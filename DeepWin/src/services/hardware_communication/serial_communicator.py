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


class SerialCommunicator(QObject):
    """
    串口通信模块。
    建立、维护和管理与 DeepArm、DeepToy 等设备的串口连接。
    负责发送和接收原始串口数据。
    处理串口数据的编解码。
    """
    # 修改信号，使其直接发出解析后的 CAN 帧组件
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
        self._read_timers: Dict[str, QTimer] = {} # {port_name: QTimer_instance}
        self.logger.info("SerialCommunicator: 初始化完成。")


    def list_ports(self):
        """
        列出所有可用串口。
        """
        ports = list_ports.comports()
        bt_ports = []
        usb_ports = []
        other_ports = []
        for port in ports:
            if "bluetooth" in port.description or "bth" in port.hwid or "蓝牙" in port.description:
                bt_ports.append(port.device)
            elif "usb" in port.description or "vid" in port.hwid:
                usb_ports.append(port.device)
            else:
                other_ports.append(port.device)

        self.logger.info("SerialCommunicator: 蓝牙设备列表: %s", bt_ports)
        self.logger.info("SerialCommunicator: USB设备列表: %s", usb_ports)
        self.logger.info("SerialCommunicator: 其他设备列表: %s", other_ports)
                
        # port_names = [port.device for port in ports]
        # port_descriptions = [port.description for port in ports]
        # self.logger.info("SerialCommunicator: 可用设备列表: %s", port_names)
        # self.logger.info("SerialCommunicator: 可用设备描述: %s", port_descriptions)
        return bt_ports

    @Slot(str, int)
    def open_port(self, port_name: str, baud_rate: Optional[int] = None):
        """
        打开指定的串口。
        如果未指定波特率，将尝试从配置管理器中获取。
        :param port_name: 串口名称 (如 'COM1' 或 '/dev/ttyUSB0')。
        :param baud_rate: 可选的波特率。
        """
        if port_name in self._serial_ports and self._serial_ports[port_name].is_open:
            self.logger.warning(f"SerialCommunicator: 串口 '{port_name}' 已打开。")
            return

        # 如果未提供波特率，尝试从配置中获取
        if baud_rate is None:
            # 尝试根据端口名判断设备类型，并从配置中获取对应的波特率
            if "COM1" in port_name or "DeepArm" in port_name: # 假设COM1或包含DeepArm的是DeepArm
                baud_rate = self.config_manager.get('device_settings.deeparm_baud_rate', 9600)
            elif "COM2" in port_name or "DeepMotor" in port_name: # 假设COM2或包含DeepMotor的是DeepMotor
                baud_rate = self.config_manager.get('device_settings.deepmotor_baud_rate', 115200)
            else:
                baud_rate = self.config_manager.get('device_settings.default_baud_rate', 9600) # 通用默认值

            self.logger.info(f"SerialCommunicator: 未指定波特率，从配置中获取到波特率: {baud_rate}")

        self.logger.info(f"SerialCommunicator: 尝试打开串口 '{port_name}'，波特率 {baud_rate}...")
        try:
            ser = serial.Serial(port=port_name, baudrate=baud_rate, timeout=0.5)
            self._serial_ports[port_name] = ser
            self.connection_status_changed.emit(port_name, True)
            self.logger.info(f"SerialCommunicator: 串口 '{port_name}' 打开成功。")
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
        timer.start(50) # 每 50ms 尝试读取一次，适应 readline 的阻塞
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
        数据格式: "AT" + CANID (hex) + Len (hex) + Data (hex) + "\r\n"
        例如: "AT00000108AABBCCDDEEFF0011\r\n"
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

            decoded_line = line.decode('ascii').strip() # 假设是 ASCII 编码
            self.logger.debug(f"SerialCommunicator: 从串口 '{port_name}' 读取到行: {decoded_line}")

            # 检查并解析数据格式: "AT" + CANID (hex) + Len (hex) + Data (hex) + "\r\n"
            # 正则表达式: ^AT([0-9A-Fa-f]{1,8})([0-9A-Fa-f]{2})([0-9A-Fa-f]*)$
            # 1. 匹配 "AT" 开头
            # 2. 捕获 1-8 位十六进制作为 CANID
            # 3. 捕获 2 位十六进制作为 Len (表示数据字节数)
            # 4. 捕获剩余的十六进制作为 Data
            match = re.match(r"^AT([0-9A-Fa-f]+)([0-9A-Fa-f]{2})([0-9A-Fa-f]*)$", decoded_line)

            if match:
                can_id_hex = match.group(1)
                len_hex = match.group(2)
                data_hex = match.group(3)

                try:
                    arbitration_id = int(can_id_hex, 16)
                    data_length = int(len_hex, 16)
                    
                    # 将十六进制数据字符串转换为字节数组
                    # 确保 data_hex 是偶数长度，如果不是，则补0
                    if len(data_hex) % 2 != 0:
                        data_hex = '0' + data_hex 
                    data_bytes = bytes.fromhex(data_hex)

                    # 验证实际数据长度与声明的长度是否一致
                    if len(data_bytes) != data_length:
                        self.logger.warning(f"SerialCommunicator: 串口 '{port_name}' 数据长度不匹配。声明: {data_length}, 实际: {len(data_bytes)}。原始: {decoded_line}")
                        return # 丢弃不完整或错误的数据包

                    # 假设所有 CAN ID 都是标准 ID (非扩展 ID)，实际项目中需要根据 CANID 范围判断
                    is_extended_id = False 

                    self.logger.info(f"SerialCommunicator: 解析到 CAN 帧: ID=0x{arbitration_id:X}, Len={data_length}, Data={data_bytes.hex()}")
                    # 发射解析后的 CAN 帧组件，CanBusCommunicator 将会接收并进一步处理
                    self.can_frame_components_received.emit(
                        port_name, arbitration_id, data_bytes, is_extended_id
                    )
                except ValueError as ve:
                    self.logger.error(f"SerialCommunicator: 串口 '{port_name}' 数据格式转换错误: {ve}. 原始: {decoded_line}")
                except Exception as e:
                    self.logger.error(f"SerialCommunicator: 串口 '{port_name}' 处理解析数据时发生未知错误: {e}. 原始: {decoded_line}")
            else:
                self.logger.warning(f"SerialCommunicator: 串口 '{port_name}' 收到不符合协议格式的数据: {decoded_line}")

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

    def sim_read_serial_data(self, port_name: str = "COM3"):
        """
        模拟从串口读取数据。
        :param port_name: 串口名称。
        """
        # 检查数据格式：AT开头，\r\n结尾
        # 扩展CAN ID 为 0x00000001，数据长度为 0x08，数据为 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11
        decoded_line = [0x41, 0x54, 0x00, 0x00, 0x00, 0x01, 0x08, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0D, 0x0A]
        self.logger.info(f"SerialCommunicator: 模拟从串口 '{port_name}' 读取数据。")
        self.logger.info(f"SerialCommunicator: 数据: {decoded_line}")

        arbitration_id = 0x00000001
        data_bytes = [0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11]
        is_extended_id = True

        self.can_frame_components_received.emit(
            port_name, arbitration_id, data_bytes, is_extended_id
        )

        # 检查并解析数据格式: "AT" + CANID (hex) + Len (hex) + Data (hex) + "\r\n"
        # 正则表达式: ^AT([0-9A-Fa-f]{1,8})([0-9A-Fa-f]{2})([0-9A-Fa-f]*)$
        # 1. 匹配 "AT" 开头
        # 2. 捕获 1-8 位十六进制作为 CANID
        # 3. 捕获 2 位十六进制作为 Len (表示数据字节数)
        # 4. 捕获剩余的十六进制作为 Data
        # match = re.match(r"^AT([0-9A-Fa-f]+)([0-9A-Fa-f]{2})([0-9A-Fa-f]*)$", decoded_line)

        # if match:
        #     can_id_hex = match.group(1)
        #     len_hex = match.group(2)
        #     data_hex = match.group(3)

        #     try:
        #         arbitration_id = int(can_id_hex, 16)
        #         data_length = int(len_hex, 16)
                
        #         # 将十六进制数据字符串转换为字节数组
        #         # 确保 data_hex 是偶数长度，如果不是，则补0
        #         if len(data_hex) % 2 != 0:
        #             data_hex = '0' + data_hex 
        #         data_bytes = bytes.fromhex(data_hex)

        #         # 验证实际数据长度与声明的长度是否一致
        #         if len(data_bytes) != data_length:
        #             self.logger.warning(f"SerialCommunicator: 串口 '{port_name}' 数据长度不匹配。声明: {data_length}, 实际: {len(data_bytes)}。原始: {decoded_line}")
        #             return # 丢弃不完整或错误的数据包

        #         # 假设所有 CAN ID 都是标准 ID (非扩展 ID)，实际项目中需要根据 CANID 范围判断
        #         is_extended_id = False 

        #         self.logger.info(f"SerialCommunicator: 解析到 CAN 帧: ID=0x{arbitration_id:X}, Len={data_length}, Data={data_bytes.hex()}")
        #         # 发射解析后的 CAN 帧组件，CanBusCommunicator 将会接收并进一步处理
        #         self.can_frame_components_received.emit(
        #             port_name, arbitration_id, data_bytes, is_extended_id
        #         )
        #     except ValueError as ve:
        #         self.logger.error(f"SerialCommunicator: 串口 '{port_name}' 数据格式转换错误: {ve}. 原始: {decoded_line}")
        #     except Exception as e:
        #         self.logger.error(f"SerialCommunicator: 串口 '{port_name}' 处理解析数据时发生未知错误: {e}. 原始: {decoded_line}")
        # else:
        #     self.logger.warning(f"SerialCommunicator: 串口 '{port_name}' 收到不符合协议格式的数据: {decoded_line}")

    def cleanup(self):
        """
        清理所有打开的串口资源。
        """
        self.logger.info("SerialCommunicator: 清理中...")
        for port_name in list(self._serial_ports.keys()):
            self.close_port(port_name)
        self.logger.info("SerialCommunicator: 清理完成。")