import time
import serial # 需要安装 pyserial 库: pip install pyserial
import serial.tools.list_ports as list_ports
import can    # 需要安装 python-can 库: pip install python-can
import json # 用于模拟 DBC 解析后的 JSON 格式输出
import re # 用于模拟简单的串口数据解析
from PySide6.QtCore import QObject, Signal, Slot, QTimer
from typing import Dict, Any, Optional, Union, List, Tuple
from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager
import random
from collections import deque


class SerialCommunicator(QObject):
    """
    串口通信模块。
    建立、维护和管理与 DeepArm、DeepToy 等设备的串口连接。
    负责发送和接收原始串口数据。
    处理串口数据的编解码。
    
    新增功能：
    - 发送和接收帧的列表管理，支持先进先出机制
    - 可配置的最大列表长度（默认1000）
    - 清空帧列表功能
    - 帧列表更新信号，用于UI同步更新
    - 获取帧列表信息的接口
    """
    # 串口通信信号
    raw_frame_received = Signal(str, bytes) # 收到原始帧: (port_name, data_bytes)
    raw_frame_send = Signal(str, bytes, str) # 发送原始帧: (port_name, data_bytes, send_status)
    connection_status_changed = Signal(str, bool) # 串口连接状态变更: (port_name, is_connected)
    serial_error = Signal(str, str) # 串口错误: (port_name, error_msg)
    
    # 新增信号：用于UI更新发送和接收帧列表
    frame_lists_updated = Signal() # 发送和接收帧列表更新信号

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
        # self.available_ports = self.list_ports()
        self.active_port = ''
        self._read_timers: Dict[str, QTimer] = {} # {port_name: QTimer_instance}
        
        # 新增：端口到设备ID的映射管理
        self._port_to_device_id_map: Dict[str, str] = {} # {port_name: device_id}
        
        # 新增：发送和接收帧列表管理
        self._max_frame_list_size = 1000  # 默认最大帧列表长度
        self._sent_frames: deque = deque(maxlen=self._max_frame_list_size)  # 发送帧列表
        self._received_frames: deque = deque(maxlen=self._max_frame_list_size)  # 接收帧列表


        
        # 清理可能存在的空端口映射
        self._cleanup_empty_port_mappings()
        
        self.logger.info("SerialCommunicator: 初始化完成。")

    def _cleanup_empty_port_mappings(self):
        """
        清理空端口映射，确保端口和设备ID的一对一关系
        """
        empty_ports = [port for port in self._port_to_device_id_map.keys() if not port or not port.strip()]
        for port in empty_ports:
            device_id = self._port_to_device_id_map.pop(port)
            self.logger.warning(f"SerialCommunicator: 清理空端口映射 '{port}' -> '{device_id}'")
        
        if empty_ports:
            self.logger.info(f"SerialCommunicator: 已清理 {len(empty_ports)} 个空端口映射")

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
    def open_port(self, port_name: str, baud_rate: Optional[int] = 921600, device_id: Optional[str] = None):
        """
        打开指定的串口。
        如果未指定波特率，将尝试从配置管理器中获取。
        :param port_name: 串口名称 (如 'COM1' 或 '/dev/ttyUSB0')。
        :param baud_rate: 可选的波特率。
        :param device_id: 可选的设备ID，用于建立端口到设备的映射关系。
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
            
            # 新增：建立端口到设备的映射关系
            if device_id:
                self._port_to_device_id_map[port_name] = device_id
                self.logger.info(f"SerialCommunicator: 建立端口映射 '{port_name}' -> '{device_id}'")
                
            # 发送AT指令，激活USB转CAN模块
            at_frame = self.create_AT_frame()
            if isinstance(at_frame, list):
                at_frame = bytes(at_frame)
            self.send_bytes(self.active_port, at_frame)
            
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
                
                # 新增：清理端口到设备的映射关系
                if port_name in self._port_to_device_id_map:
                    device_id = self._port_to_device_id_map.pop(port_name)
                    self.logger.info(f"SerialCommunicator: 清理端口映射 '{port_name}' -> '{device_id}'")
                
                self.logger.info(f"SerialCommunicator: 串口 '{port_name}' 已关闭。")
                del self._serial_ports[port_name]
            except Exception as e:
                error_msg = f"关闭串口 '{port_name}' 失败: {e}"
                self.logger.error(f"SerialCommunicator: {error_msg}")
                self.serial_error.emit(port_name, error_msg)
        else:
            self.logger.warning(f"SerialCommunicator: 尝试关闭不存在的串口 '{port_name}'。")

    @Slot(str, bytes)
    def send_bytes(self, port_name: str, data: bytes, command_info: Optional[Dict] = None):
        """
        向指定串口发送原始字节数据。
        无论串口是否存在，都会发送信号给UI进行显示更新。
        如果串口不存在或发送失败，会自动触发模拟数据反馈。
        :param port_name: 串口名称。
        :param data: 要发送的字节数据。
        :param command_info: 命令信息字典，包含命令名称等。
        :return: 发送结果，True表示成功，False表示失败，None表示串口不存在
        """
        # 检查串口连接状态
        is_port_available = port_name in self._serial_ports 
        self.logger.info(f"SerialCommunicator: 串口 '{port_name}' 连接状态: {is_port_available}, _serial_ports: {self._serial_ports}")


        send_status = "OK" if is_port_available else "X"
        
        # 记录发送的帧（无论串口是否连接）
        frame_info = {
            'timestamp': time.time(),
            'port_name': port_name,
            'data': data,
            'data_hex': data.hex(),
            'send_status': send_status
        }
        
        # 添加命令信息
        if command_info:
            frame_info.update(command_info)
            
        self._sent_frames.append(frame_info)
        
        # 先发送原始信号（用于UI显示），无论串口是否存在都要发送
        self.raw_frame_send.emit(port_name, data, send_status)
        # 发送帧列表更新信号
        self.frame_lists_updated.emit()
        
        if not is_port_available:
            self.logger.warning(f"SerialCommunicator: 串口 '{port_name}' 未打开或不存在，触发模拟数据反馈")
            # 触发模拟数据反馈
            self._trigger_simulation_feedback(port_name, command_info)
            return None
            
        try:
            self.logger.debug(f"SerialCommunicator: 向串口 '{port_name}' 发送数据: {data.hex()}")
            self._serial_ports[port_name].write(data)
            self.logger.info(f"SerialCommunicator: 串口层发送成功 - 端口: {port_name}")
            return True
            
        except Exception as e:
            error_msg = f"向串口 '{port_name}' 发送数据失败: {e}"
            self.logger.error(f"SerialCommunicator: {error_msg}")
            self.serial_error.emit(port_name, error_msg)
            # 发送失败时也触发模拟数据反馈
            self._trigger_simulation_feedback(port_name, command_info)
            return False

    def _trigger_simulation_feedback(self, port_name: str, command_info: Optional[Dict] = None):
        """
        触发模拟数据反馈
        :param port_name: 端口名称
        :param command_info: 命令信息，用于提取位置参数
        """
        try:
            # 从命令信息中提取位置参数
            position = 0.0
            if command_info and 'params' in command_info:
                position = command_info['params'].get('pos', 0.0)
            
            # 触发模拟数据反馈
            self.sim_read_serial_data(port_name=port_name, position=position)
            self.logger.info(f"SerialCommunicator: 已触发模拟数据反馈 - 端口: {port_name}, 位置: {position}")
            
        except Exception as e:
            self.logger.error(f"SerialCommunicator: 触发模拟数据反馈失败: {e}")

    def send_bytes_by_device_id(self, device_id: str, data: bytes, command_info: Optional[Dict] = None):
        """
        通过设备ID发送串口数据
        :param device_id: 设备ID
        :param data: 要发送的字节数据
        :param command_info: 命令信息字典
        :return: 发送结果，True表示成功，False表示失败，None表示设备端口不存在
        """
        try:
            # 获取设备对应的端口，如果不存在则使用设备ID作为端口名
            target_port = self._get_device_port_by_id(device_id)
            self.logger.info(f"SerialCommunicator: 通过设备ID发送数据 - 设备ID: {device_id}, 查找到的端口: {target_port}, 端口映射: {self._port_to_device_id_map}")
            
            target_port = self.active_port
            
            # 调用send_bytes方法，统一处理端口检查和模拟数据反馈
            return self.send_bytes(target_port, data, command_info)
            
        except Exception as e:
            self.logger.error(f"SerialCommunicator: 通过设备ID发送数据失败: {e}")
            return False

    def _get_device_port_by_id(self, device_id: str) -> Optional[str]:
        """
        根据设备ID获取对应的端口名称
        :param device_id: 设备ID
        :return: 端口名称，如果未找到则返回None
        """
        try:
            self.logger.debug(f"SerialCommunicator: 查找设备 '{device_id}' 对应的端口，当前映射: {self._port_to_device_id_map}")
            for port, dev_id in self._port_to_device_id_map.items():
                if dev_id == device_id:
                    self.logger.debug(f"SerialCommunicator: 找到设备 '{device_id}' 对应的端口: '{port}'")
                    return port
            self.logger.warning(f"SerialCommunicator: 未找到设备 '{device_id}' 对应的端口")
            return None
        except Exception as e:
            self.logger.error(f"SerialCommunicator: 获取设备端口失败: {e}")
            return None

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
            
            # 记录接收的帧
            frame_info = {
                'timestamp': time.time(),
                'port_name': port_name,
                'data': processed_line,
                'data_hex': processed_line.hex()
            }
            self._received_frames.append(frame_info)
            
            # 发送原始信号
            self.raw_frame_received.emit(port_name, processed_line)
            # 发送帧列表更新信号
            self.frame_lists_updated.emit()

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


    def sim_read_serial_data(self, port_name: str = None, position: float = None):
        """
        模拟从串口读取数据。
        :param port_name: 串口名称。
        :param position: 位置。
        """
        # 检查数据格式：AT开头，\r\n结尾
        # 扩展CAN ID 为 0x00000001，数据长度为 0x08，数据为 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x11

        decoded_line = [0x41, 0x54, 0x14, 0x00, 0x37, 0xEC, 0x08, 0x80, 0xFF, 0x82, 0x0F, 0x81, 0x51, 0x01, 0x36, 0x0D, 0x0A]
        # 发送原始帧数据
        frame = decoded_line[2:-2]
        # 最后一个自己增加一个随机数
        if not position:
            frame[6] = random.randint(0, 255)
        else:
            # 根据_decode_can_data方法的解码逻辑进行逆运算
            # 1. 首先将位置限制在POSITION_RANGE范围内
            POSITION_RANGE = (-4 * 3.14159, 4 * 3.14159)  # -4π ~ 4π
            position = min(max(position, POSITION_RANGE[0]), POSITION_RANGE[1])
            
            # 2. 使用_scale_value的逆运算，将位置映射到-32768到32767范围
            # _scale_value: (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min
            # 逆运算: (position - out_min) * (in_max - in_min) / (out_max - out_min) + in_min
            position_raw = (position - POSITION_RANGE[0]) * (32767 - (-32768)) / (POSITION_RANGE[1] - POSITION_RANGE[0]) + (-32768)
            position_raw = int(position_raw)
            
            # 3. 加上32767得到无符号值（对应_decode_can_data中的减法逆运算）
            position_uint = position_raw + 32767
            
            self.logger.info(f"SerialCommunicator: 位置 '{position}' 转换为原始值: {position_raw}, 无符号值: {position_uint}")

            # 4. 将无符号值写入frame[5:6]（大端序，对应_decode_can_data中的struct.unpack('>H', data_bytes[0:2])）
            frame[5] = (position_uint >> 8) & 0xFF  # 高字节
            frame[6] = position_uint & 0xFF         # 低字节

        frame[8] = random.randint(0, 255)
        frame[10] = random.randint(0, 255)
        frame[12] = random.randint(0, 255)
        frame = bytes(frame)

        self.logger.info(f"SerialCommunicator: 模拟从串口 '{port_name}' 读取数据。")
        self.logger.info(f"SerialCommunicator: 数据: {frame.hex()}")

        arbitration_id = 0x140037ec
        # 使用修改后的frame中的数据，而不是硬编码的值
        data_bytes = frame[5:13]  # 从frame中提取8字节的数据部分
        is_extended_id = True

        if port_name is None or not port_name.strip():
            port_name = 'DeepMotor'  # 模拟数据使用DeepMotor作为端口名

        # 确保端口映射存在（模拟数据场景）
        if port_name not in self._port_to_device_id_map:
            # 使用add_port_device_mapping方法确保一对一映射
            self.add_port_device_mapping(port_name, 'DeepMotor')
            self.logger.debug(f"SerialCommunicator: 为模拟数据建立端口映射 '{port_name}' -> 'DeepMotor'")

        # 记录接收的帧（模拟数据）
        frame_info = {
            'timestamp': time.time(),
            'port_name': port_name,
            'data': frame,
            'data_hex': frame.hex()
        }
        self._received_frames.append(frame_info)
        
        self.raw_frame_received.emit(port_name, frame)  # 去掉 AT 和 \r\n
        # 发送帧列表更新信号
        self.frame_lists_updated.emit()
    
    def process_received_data(self, port_name: str, data: bytes) -> Optional[Dict[str, Any]]:
        """
        处理接收到的串口数据，返回处理结果
        :param port_name: 端口名称
        :param data: 接收到的数据
        :return: 处理结果字典，包含端口信息和数据
        """
        try:
            self.logger.debug(f"SerialCommunicator: 处理接收数据 - 端口: {port_name}, 数据: {data.hex()}")
            
            # 构建处理结果
            result = {
                'port_name': port_name,
                'data': data,
                'data_hex': data.hex(),
                'timestamp': time.time(),
                'frame_type': 'serial'
            }
            
            # 添加到接收帧列表
            frame_info = {
                'timestamp': result['timestamp'],
                'port_name': port_name,
                'data': data,
                'data_hex': data.hex()
            }
            self._received_frames.append(frame_info)
            
            # 发送帧列表更新信号
            self.frame_lists_updated.emit()
            
            self.logger.debug(f"SerialCommunicator: 数据处理完成 - 端口: {port_name}")
            return result
            
        except Exception as e:
            self.logger.error(f"SerialCommunicator: 处理接收数据失败: {e}")
            return None

    def cleanup(self):
        """
        清理所有打开的串口资源。
        """
        self.logger.info("SerialCommunicator: 清理中...")
        for port_name in list(self._serial_ports.keys()):
            self.close_port(port_name)
        self.logger.info("SerialCommunicator: 清理完成。")

    # 新增：端口映射管理方法
    def get_device_id_from_port(self, port_name: str) -> Optional[str]:
        """
        根据端口名获取设备ID
        :param port_name: 端口名称
        :return: 设备ID，如果不存在则返回None
        """
        return self._port_to_device_id_map.get(port_name)
        
    def get_port_device_mapping(self) -> Dict[str, str]:
        """
        获取端口到设备ID的映射
        :return: 端口到设备ID的映射字典
        """
        return self._port_to_device_id_map.copy()
        
    def set_port_device_mapping(self, mapping: Dict[str, str]):
        """
        设置端口到设备ID的映射
        :param mapping: 端口到设备ID的映射字典
        """
        self._port_to_device_id_map = mapping.copy()
        self.logger.info(f"SerialCommunicator: 设置端口映射: {mapping}")
        
    def add_port_device_mapping(self, port_name: str, device_id: str):
        """
        添加单个端口到设备的映射
        :param port_name: 端口名称
        :param device_id: 设备ID
        """
        # 确保端口名不为空
        if not port_name or not port_name.strip():
            self.logger.warning(f"SerialCommunicator: 端口名不能为空，跳过映射建立")
            return
            
        # 确保一对一映射：先清除该设备ID的所有现有映射
        existing_ports = [port for port, dev_id in self._port_to_device_id_map.items() if dev_id == device_id]
        for port in existing_ports:
            if port != port_name:
                self.logger.info(f"SerialCommunicator: 清除旧映射 '{port}' -> '{device_id}'")
                del self._port_to_device_id_map[port]
        
        # 建立新映射
        self._port_to_device_id_map[port_name] = device_id
        self.logger.info(f"SerialCommunicator: 添加端口映射 '{port_name}' -> '{device_id}'")
        
    def remove_port_device_mapping(self, port_name: str):
        """
        移除端口到设备的映射
        :param port_name: 端口名称
        """
        if port_name in self._port_to_device_id_map:
            device_id = self._port_to_device_id_map.pop(port_name)
            self.logger.info(f"SerialCommunicator: 移除端口映射 '{port_name}' -> '{device_id}'")
    
    # 新增：帧列表管理方法
    def clear_frame_lists(self):
        """
        清空发送和接收帧列表
        """
        self._sent_frames.clear()
        self._received_frames.clear()
        self.logger.info("SerialCommunicator: 已清空发送和接收帧列表")
        # 发送帧列表更新信号
        self.frame_lists_updated.emit()
    
    def get_sent_frames(self) -> List[Dict[str, Any]]:
        """
        获取发送帧列表
        :return: 发送帧列表的副本
        """
        return list(self._sent_frames)
    
    def get_received_frames(self) -> List[Dict[str, Any]]:
        """
        获取接收帧列表
        :return: 接收帧列表的副本
        """
        return list(self._received_frames)
    
    def get_frame_lists_info(self) -> Dict[str, Any]:
        """
        获取帧列表信息
        :return: 包含帧列表统计信息的字典
        """
        return {
            'sent_frames_count': len(self._sent_frames),
            'received_frames_count': len(self._received_frames),
            'max_list_size': self._max_frame_list_size,
            'sent_frames': list(self._sent_frames),
            'received_frames': list(self._received_frames)
        }
    
    def set_max_frame_list_size(self, size: int):
        """
        设置帧列表的最大长度
        :param size: 新的最大长度
        """
        if size <= 0:
            self.logger.warning(f"SerialCommunicator: 无效的帧列表大小: {size}")
            return
        
        self._max_frame_list_size = size
        # 重新创建deque以应用新的maxlen
        old_sent = list(self._sent_frames)
        old_received = list(self._received_frames)
        
        self._sent_frames = deque(old_sent, maxlen=size)
        self._received_frames = deque(old_received, maxlen=size)
        
        self.logger.info(f"SerialCommunicator: 帧列表最大长度已设置为: {size}")
        # 发送帧列表更新信号
        self.frame_lists_updated.emit()

    def get_sent_frame_info(self, port_name: str, data: bytes) -> Optional[Dict]:
        """
        获取发送帧的详细信息
        :param port_name: 端口名称
        :param data: 发送的数据
        :return: 帧信息字典，如果未找到则返回None
        """
        # 在发送帧列表中查找匹配的帧
        for frame_info in reversed(self._sent_frames):  # 从最新的开始查找
            if (frame_info.get('port_name') == port_name and 
                frame_info.get('data') == data):
                return frame_info
        return None
        
    def create_AT_frame(self):
        # Send 'AT+AT' command
        frame = [0x41, 0x54, 0x2B, 0x41, 0x54, 0x0D, 0x0A]
        return frame