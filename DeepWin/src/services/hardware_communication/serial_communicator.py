import time
import serial # 需要安装 pyserial 库: pip install pyserial
import serial.tools.list_ports as list_ports
import can    # 需要安装 python-can 库: pip install python-can
import json # 用于模拟 DBC 解析后的 JSON 格式输出
import re # 用于模拟简单的串口数据解析
from PySide6.QtCore import QObject, Signal, Slot, QTimer
from typing import Dict, Any, Optional, Union, List, Tuple
from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager
import random


class SerialCommunicator(QObject):
    """
    串口通信模块。
    建立、维护和管理与 DeepArm、DeepToy 等设备的串口连接。
    负责发送和接收原始串口数据。
    处理串口数据的编解码。
    """
    # 修改信号，使其直接发出解析后的 CAN 帧组件
    raw_frame_received = Signal(str, bytes) # 收到原始帧: (port_name, data_bytes)
    raw_frame_send = Signal(str, bytes) # 发送原始帧: (port_name, data_bytes)
    can_frame_components_received = Signal(str, int, bytes, bool) # 收到 CAN 帧组件: (port_name, arbitration_id, data_bytes, is_extended_id)
    connection_status_changed = Signal(str, bool) # 串口连接状态变更: (port_name, is_connected)
    serial_error = Signal(str, str) # 串口错误: (port_name, error_msg)

    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, parent: Optional[QObject] = None):
        """
        初始化 SerialCommunicator。
        :param log_manager: 全局日志管理器实例。
        :param config_manager: 全局配置管理器实例。
        :param parent: QObject 父对象。
        """
        super().__init__(parent)
        self.logger = log_manager.get_logger(__name__)
        self.config_manager = config_manager
        self.logger.info("SerialCommunicator: 初始化中...")
        self._serial_ports: Dict[str, serial.Serial] = {} # {port_name: serial.Serial_instance}
        # 查看可用设备列表
        self.available_ports = self.list_ports()
        self.active_port = ''
        self._read_timers: Dict[str, QTimer] = {} # {port_name: QTimer_instance}
        self.logger.info("SerialCommunicator: 初始化完成。")


    def list_ports(self):
        """
        列出所有可用串口。
        """
        ports = list_ports.comports()
        all_ports = []
        bt_ports = []
        usb_ports = []
        other_ports = []
        for port in ports:
            all_ports.append(port.device)
            self.logger.debug(f"SerialCommunicator: 发现串口: {port.device} - {port.description}")

            if "bluetooth" in port.description or "bth" in port.hwid or "蓝牙" in port.description:
                bt_ports.append(port.device)
            elif "usb" in port.description.lower() or "ch340" in port.description.lower() or "串行设备" in port.description:
                usb_ports.append(port.device)
            else:
                other_ports.append(port.device)

        # self.logger.info("SerialCommunicator: 蓝牙设备列表: %s", bt_ports)
        self.logger.info("SerialCommunicator: USB设备列表: %s", usb_ports)
        # self.logger.info("SerialCommunicator: 其他设备列表: %s", other_ports)
        # self.logger.info(f"SerialCommunicator: 所有串口列表: {all_ports}")

        return usb_ports

    @Slot(str, int)
    def open_port(self, port_name: str, baud_rate: Optional[int] = 921600):
        """
        打开指定的串口。
        如果未指定波特率，将尝试从配置管理器中获取。
        :param port_name: 串口名称 (如 'COM1' 或 '/dev/ttyUSB0')。
        :param baud_rate: 可选的波特率。
        """
        if port_name in self._serial_ports and self._serial_ports[port_name].is_open:
            self.logger.warning(f"SerialCommunicator: 串口 '{port_name}' 已打开。")
            return


        self.logger.info(f"SerialCommunicator: 尝试打开串口 '{port_name}'，波特率 {baud_rate}...")
        try:
            ser = serial.Serial(port=port_name, baudrate=baud_rate, timeout=0.5)
            self._serial_ports[port_name] = ser
            self.connection_status_changed.emit(port_name, True)
            self.logger.info(f"SerialCommunicator: 串口 '{port_name}' 打开成功。")
            self.active_port = port_name
            self.start_reading(port_name)
        except serial.SerialException as e:
            error_msg = f"打开串口 '{port_name}' 失败: {e}"
            self.logger.error(f"SerialCommunicator: {error_msg}")
            self.serial_error.emit(port_name, error_msg)
        except Exception as e:
            error_msg = f"打开串口 '{port_name}' 遇到未知错误: {e}"
            self.logger.error(f"SerialCommunicator: {error_msg}")
            self.serial_error.emit(port_name, error_msg)


    @Slot(str)
    def close_port(self, port_name: str):
        """
        关闭指定的串口。
        :param port_name: 串口名称。
        """
        if port_name in self._serial_ports:
            self.stop_reading(port_name) # 停止读取计时器
            try:
                self._serial_ports[port_name].close()
                self.connection_status_changed.emit(port_name, False)
                self.active_port = ''
                self.logger.info(f"SerialCommunicator: 串口 '{port_name}' 已关闭。")
                del self._serial_ports[port_name]
            except Exception as e:
                error_msg = f"关闭串口 '{port_name}' 失败: {e}"
                self.logger.error(f"SerialCommunicator: {error_msg}")
                self.serial_error.emit(port_name, error_msg)
        else:
            self.logger.warning(f"SerialCommunicator: 尝试关闭不存在的串口 '{port_name}'。")

    @Slot(str, bytes)
    def send_bytes(self, port_name: str, data: bytes):
        """
        向指定串口发送原始字节数据。
        :param port_name: 串口名称。
        :param data: 要发送的字节数据。
        """
        if port_name not in self._serial_ports or not self._serial_ports[port_name].is_open:
            self.logger.warning(f"SerialCommunicator: 串口 '{port_name}' 未打开或不存在，无法发送数据。")
            return
        try:
            self.logger.debug(f"SerialCommunicator: 向串口 '{port_name}' 发送数据: {data.hex()}")
            self._serial_ports[port_name].write(data)
            self.raw_frame_send.emit(port_name, data)
        except Exception as e:
            error_msg = f"向串口 '{port_name}' 发送数据失败: {e}"
            self.logger.error(f"SerialCommunicator: {error_msg}")
            self.serial_error.emit(port_name, error_msg)

    def start_reading(self, port_name: str):
        """
        开始从指定串口周期性读取数据。
        :param port_name: 串口名称。
        """
        if port_name not in self._serial_ports:
            self.logger.warning(f"SerialCommunicator: 串口 '{port_name}' 未打开，无法开始读取。")
            return
        if port_name in self._read_timers and self._read_timers[port_name].isActive():
            self.logger.warning(f"SerialCommunicator: 串口 '{port_name}' 已经在读取中。")
            return

        timer = QTimer(self)
        timer.timeout.connect(lambda: self._read_serial_data(port_name))
        timer.start(10) # 每 10ms 尝试读取一次，适应 readline 的阻塞
        self._read_timers[port_name] = timer
        self.logger.info(f"SerialCommunicator: 开始从串口 '{port_name}' 读取数据。")

    def stop_reading(self, port_name: str):
        """
        停止从指定串口读取数据。
        :param port_name: 串口名称。
        """
        if port_name in self._read_timers:
            self._read_timers[port_name].stop()
            self._read_timers[port_name].deleteLater() # 确保 QTimer 对象被正确销毁
            del self._read_timers[port_name]
            self.logger.info(f"SerialCommunicator: 已停止从串口 '{port_name}' 读取数据。")

    @Slot(str)
    def _read_serial_data(self, port_name: str):
        """
        内部方法：从串口读取数据，并解析为 CAN 帧组件。
        数据格式: AT(2字节) + CANID(4字节) + Len(1字节) + Data(N字节) + \r\n(2字节)
        例如: 41 54 14 00 37 EC 08 FF FF 82 0F 81 51 01 36 0D 0A 
        """
        if port_name not in self._serial_ports or not self._serial_ports[port_name].is_open:
            self.logger.warning(f"SerialCommunicator: 尝试从已关闭或不存在的串口 '{port_name}' 读取数据。")
            self.stop_reading(port_name) # 确保停止计时器
            return
        try:
            # 读取一行数据直到 '\n' 或超时
            line = self._serial_ports[port_name].readline()
            if not line: # 没有读到数据
                return

            # 检查数据长度是否足够（至少需要9字节：2字节AT + 4字节CANID + 1字节长度 + 2字节\r\n）
            if len(line) < 9:
                self.logger.warning(f"SerialCommunicator: 串口 '{port_name}' 收到数据长度不足: {len(line)} 字节")
                return

            # 检查数据头是否为 "AT"
            if line[0:2] != b'AT':
                self.logger.warning(f"SerialCommunicator: 串口 '{port_name}' 收到无效的数据头: {line[0:2].hex()}")
                return
            # 检查数据尾是否为 \r\n
            if line[-2:] != b'\r\n':
                self.logger.warning(f"SerialCommunicator: 串口 '{port_name}' 数据尾无效: {line[-2:].hex()}")
                return
            
            # 去掉头尾后发送
            processed_line = line[2:-2]
            self.raw_frame_received.emit(port_name, processed_line)

            self.ser2can(port_name,processed_line)

        except serial.SerialException as e:
            error_msg = f"从串口 '{port_name}' 读取数据失败: {e}"
            self.logger.error(f"SerialCommunicator: {error_msg}")
            self.serial_error.emit(port_name, error_msg)
            self.stop_reading(port_name) # 发生错误时停止读取
        except Exception as e:
            error_msg = f"从串口 '{port_name}' 读取或解码数据时发生未知错误: {e}"
            self.logger.error(f"SerialCommunicator: {error_msg}")
            self.serial_error.emit(port_name, error_msg)
            self.stop_reading(port_name) # 发生错误时停止读取

    def ser2can(self, port_name: str, line: bytes):
        """
        将串口数据解析为 CAN 帧组件。
        :param line: 串口数据。
        :param port_name: 串口名称。
        """
        # 解析CAN ID（4字节），先向右移3位, 具体根据协议决定
            
        arbitration_id = int.from_bytes(line[0:4], byteorder='big') >> 3
        
        # 解析数据长度（1字节）
        data_length = line[4]
        
        # 检查数据长度是否合理
        if data_length > 8:  # CAN 2.0 标准帧最大数据长度为8字节
            self.logger.warning(f"SerialCommunicator: 串口 '{port_name}' 数据长度超出范围: {data_length}")
            return

        # 检查接收到的数据长度是否足够
        expected_length = 5 + data_length  # 5 = 4(CANID) + 1(Len)
        if len(line) < expected_length:
            self.logger.warning(f"SerialCommunicator: 串口 '{port_name}' 数据不完整，期望 {expected_length} 字节，实际 {len(line)} 字节")
            return

        # 提取数据部分
        data_bytes = line[5:5+data_length]


        # 假设所有 CAN ID 都是标准 ID (非扩展 ID)，实际项目中需要根据 CANID 范围判断
        is_extended_id = True

        self.logger.info(f"SerialCommunicator: 解析到 CAN 帧: ID=0x{arbitration_id:X}, Len={data_length}, Data={data_bytes.hex()}")
        # 发射解析后的 CAN 帧组件，CanBusCommunicator 将会接收并进一步处理
        self.can_frame_components_received.emit(
            port_name, arbitration_id, data_bytes, is_extended_id
        )

    def sim_read_serial_data(self, port_name: str = None):
        """
        模拟从串口读取数据。
        :param port_name: 串口名称。
        """
        # 检查数据格式：AT开头，\r\n结尾
        # 扩展CAN ID 为 0x00000001，数据长度为 0x08，数据为 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11

        decoded_line = [0x41, 0x54, 0x14, 0x00, 0x37, 0xEC, 0x08, 0xFF, 0xFF, 0x82, 0x0F, 0x81, 0x51, 0x01, 0x36, 0x0D, 0x0A]
        # 发送原始帧数据
        frame = decoded_line[2:-2]
        # 最后一个自己增加一个随机数
        frame[6] = random.randint(0, 255)
        frame[8] = random.randint(0, 255)
        frame[10] = random.randint(0, 255)
        frame[12] = random.randint(0, 255)
        frame = bytes(frame)

        self.logger.info(f"SerialCommunicator: 模拟从串口 '{port_name}' 读取数据。")
        self.logger.info(f"SerialCommunicator: 数据: {frame.hex()}")

        arbitration_id = 0x140037ec
        data_bytes = bytes([0xFF, 0xFF, 0x82, 0x0F, 0x81, 0x51, 0x01, 0x36])
        is_extended_id = True

        if port_name is None:
            port_name = self.active_port


        self.raw_frame_received.emit('DeepMotor', frame)  # 去掉 AT 和 \r\n

        # 发送 CAN 帧组件
        self.can_frame_components_received.emit(
            port_name, arbitration_id, data_bytes, is_extended_id
        )

    def cleanup(self):
        """
        清理所有打开的串口资源。
        """
        self.logger.info("SerialCommunicator: 清理中...")
        for port_name in list(self._serial_ports.keys()):
            self.close_port(port_name)
        self.logger.info("SerialCommunicator: 清理完成。")