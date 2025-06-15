# src/services/hardware_communication/can_bus_communicator.py
# CAN 总线通信模块

import time
import can
import json
import os # Import os for path handling with DBC files
import struct # 添加 struct 模块导入
from can.listener import BufferedReader
from can.message import Message
from PySide6.QtCore import QObject, Signal, Slot, QTimer
from typing import Dict, Any, Optional, Union, List, Tuple
import cantools

from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager


class CanBusCommunicator(QObject):
    """
    CAN 总线通信模块。
    负责 CAN 报文的 DBC 解析和编码。
    """
    can_parsed_data_received = Signal(str, dict)
    connection_status_changed = Signal(str, bool)
    can_error = Signal(str, str)

    # 定义一个特殊的 bustype，用于指示 CAN 数据是通过串口桥接进来的
    SERIAL_BRIDGE_BUSTYPE = "serial_can_bridge"

    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, parent: Optional[QObject] = None):
        """
        初始化 CanBusCommunicator。
        :param log_manager: 全局日志管理器实例。
        :param config_manager: 全局配置管理器实例。
        :param parent: QObject 父对象。
        """
        super().__init__(parent)
        self.logger = log_manager.get_logger(__name__)
        self.config_manager = config_manager # 保存配置管理器实例
        self.logger.info("CanBusCommunicator: 初始化中...")
        self._can_buses: Dict[str, can.Bus] = {} # 存储实际的 can.Bus 实例 (非串口桥接模式)
        self._dbcs: Dict[str, Any] = {} # 存储加载的 DBC 数据库
        self._notifier: Dict[str, can.Notifier] = {} # 存储 can.Notifier 实例
        self._read_timers: Dict[str, QTimer] = {} # For polling BufferedReader (only for direct CAN bus)
        # NEW: 存储通道名到具体设备实例 ID 的映射
        self._channel_to_device_id_map: Dict[str, str] = {} # 存储通道名到具体设备实例 ID 的映射
        self.logger.info("CanBusCommunicator: 初始化完成。")

    def _get_dbc_path(self, device_type: str) -> str:
        """
        获取DBC文件的路径。
        :param device_type: 设备类型（如 'deepmotor'）
        :return: DBC文件的完整路径
        """
        # 获取项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        # 构建DBC文件路径
        protocol_dir = f"{device_type}_protocol"  # 修正目录名格式
        dbc_path = os.path.join(project_root, 'src', 'services', 'hardware_communication', 
                               'device_protocols', protocol_dir, f'{device_type}.dbc')
        return dbc_path
    
    def get_port_name(self, device_id: str) -> str:
        """
        根据设备ID获取对应的串口名。
        :param device_id: 设备ID（如 'DeepArm1' 或 'DeepMotor1'）
        :return: 对应的串口名（如 'COM1' 或 'COM2'）
        """
        for channel, id in self._channel_to_device_id_map.items():
            if device_id in id:
                self.logger.info(f"CanBusCommunicator: 设备ID '{device_id}' 映射到通道 '{channel}'。")
                return channel
            else:
                self.logger.warning(f"CanBusCommunicator: 设备ID '{device_id}' 未映射到通道 '{channel}'。")
        return device_id
    
    def remove_channel_mapping(self, channel: str):
        """
        移除通道到设备ID的映射关系。
        :param channel: CAN通道名称。
        """
        if channel in self._channel_to_device_id_map:
            self.logger.info(f"CanBusCommunicator: 移除通道 '{channel}' 到设备ID的映射关系。")
            del self._channel_to_device_id_map[channel]
            # 打印_channel_to_device_id_map
            self.logger.info(f"CanBusCommunicator: _channel_to_device_id_map: {self._channel_to_device_id_map}")
        else:
            self.logger.warning(f"CanBusCommunicator: 通道 '{channel}' 未映射到设备ID。")
        

    @Slot(str, str)
    def configure_channel(self, channel: str, device_type: str):
        """
        配置CAN通道。
        :param channel: CAN通道名称（如 'COM1' 或 'can0'）
        :param device_type: 设备类型（如 'deepmotor'）
        """
        if channel in self._can_buses:
            self.logger.warning(f"CanBusCommunicator: CAN通道 '{channel}' 已配置。")
            return

        try:
            # 加载DBC文件
            dbc_path = self._get_dbc_path(device_type)
            self.logger.info(f"CanBusCommunicator: 尝试配置 CAN 通道 '{channel}' (类型: {device_type}), 加载 DBC: {dbc_path}...")
            
            if not os.path.exists(dbc_path):
                raise FileNotFoundError(f"DBC文件不存在: {dbc_path}")

            self._dbcs[channel] = cantools.database.load_file(dbc_path)
            
            # 配置CAN总线
            bus = can.Bus(channel=channel, bustype='serial_can_bridge')
            self._can_buses[channel] = bus
            self.connection_status_changed.emit(channel, True)
            self.logger.info(f"CanBusCommunicator: CAN通道 '{channel}' 配置成功。")
            
        except Exception as e:
            error_msg = f"配置CAN通道 '{channel}' 失败: {e}"
            self.logger.error(f"CanBusCommunicator: {error_msg}")
            self.can_error.emit(channel, error_msg)

    

    @Slot(str, str, str, str) # NEW: Added device_instance_id parameter
    def connect_can_interface(self, channel: Optional[str] = None, bustype: Optional[str] = None, dbc_name: Optional[str] = None, device_instance_id: Optional[str] = None):
        """
        连接到 CAN 总线接口，并加载 DBC 文件。
        如果未指定 channel, bustype 或 dbc_file_path，将尝试从配置管理器中获取。
        :param channel: CAN 接口通道 (如 'can0', 'COM1', 'Pcan_usb@USB0')。
                        对于串口桥接模式，此参数应为串口名（如 'COM1'）。
        :param bustype: CAN 接口类型 (如 'socketcan', 'pcan', 'kvaser', 'virtual' 或 'serial_can_bridge')。
        :param dbc_file_path: 可选的 DBC 文件路径，用于解析 CAN 报文。
        :param device_instance_id: 可选参数，指定此 CAN 通道所对应的具体设备实例 ID (例如 "DeepArm1")。
        """
        # 从配置中获取默认值
        if channel is None:
            channel = self.config_manager.get('device_settings.deeparm_serial_port', 'COM1') # 默认用串口名作为CAN通道名
        if bustype is None:
            bustype = self.config_manager.get('device_settings.deeparm_can_bustype', self.SERIAL_BRIDGE_BUSTYPE) # 默认使用串口桥接
        if dbc_name is None:
            dbc_name = self.config_manager.get('device_settings.deeparm_dbc_name', 'deeparm')

        # NEW: 存储通道到设备实例ID的映射
        if device_instance_id:
            self._channel_to_device_id_map[channel] = device_instance_id
            self.logger.info(f"CanBusCommunicator: 映射通道 '{channel}' 到设备实例 ID '{device_instance_id}'。")
        elif channel not in self._channel_to_device_id_map:
            # 如果没有明确的 device_instance_id 且之前未映射，则默认使用通道名作为设备ID（fallback）
            # 在Coordinator中应该总是显式传入device_instance_id以避免模糊性
            self._channel_to_device_id_map[channel] = channel 
            self.logger.warning(f"CanBusCommunicator: 未为通道 '{channel}' 提供明确的设备实例 ID。将使用通道名作为设备 ID。")

        if channel in self._dbcs: # 检查 DBC 是否已加载，以此判断是否已配置该通道
            self.logger.warning(f"CanBusCommunicator: CAN 通道 '{channel}' 的 DBC 已加载或已配置。")
            # 如果是实际的 CAN Bus，可以进一步检查是否已连接
            if bustype != self.SERIAL_BRIDGE_BUSTYPE and channel in self._can_buses:
                 self.logger.warning(f"CanBusCommunicator: 实际 CAN Bus '{channel}' 已连接。")
            return

        self.logger.info(f"CanBusCommunicator: 尝试配置 CAN 通道 '{channel}' (类型: {bustype}), 加载 DBC: {dbc_name}...")

        # 1. 加载 DBC 文件 (无论是否是实际 CAN Bus，都需要 DBC 来解析)
        dbc_file_path = self._get_dbc_path(dbc_name)
        if dbc_file_path:
            try:
                import cantools
                db = cantools.database.load_file(dbc_file_path)
                self._dbcs[channel] = db
                self.logger.info(f"CanBusCommunicator: 已为通道 '{channel}' 加载 DBC 文件: {dbc_file_path}")
            except ImportError:
                self.logger.warning("CanBusCommunicator: cantools 库未安装，无法解析 DBC 文件。请安装：pip install cantools")
            except Exception as e:
                self.logger.error(f"CanBusCommunicator: 加载 DBC 文件 '{dbc_file_path}' 失败: {e}")
                self.can_error.emit(channel, f"加载 DBC 失败: {e}")
                return # DBC 加载失败，后续操作无意义

        # 2. 根据 bustype 判断是否需要创建实际的 can.Bus 实例
        if bustype != self.SERIAL_BRIDGE_BUSTYPE:
            self.logger.info(f"CanBusCommunicator: 尝试连接实际 CAN 接口 '{channel}' ({bustype})...")
            try:
                bus = can.Bus(channel=channel, bustype=bustype)
                self._can_buses[channel] = bus

                # 为实际 CAN Bus 设置 Listener 和 Notifier
                listener = can.BufferedReader()
                notifier = can.Notifier(bus, [listener], timeout=0.1)
                self._notifier[channel] = notifier
                
                timer = QTimer(self)
                timer.timeout.connect(lambda: self._check_for_can_messages(channel, listener))
                timer.start(50) # 每 50ms 检查一次缓冲区是否有新消息
                self._read_timers[channel] = timer

                self.connection_status_changed.emit(channel, True)
                self.logger.info(f"CanBusCommunicator: CAN 接口 '{channel}' 连接成功。")
            except Exception as e:
                error_msg = f"连接 CAN 接口 '{channel}' 失败: {e}"
                self.logger.error(f"CanBusCommunicator: {error_msg}")
                self.can_error.emit(channel, error_msg)
        else:
            self.logger.info(f"CanBusCommunicator: 通道 '{channel}' 使用串口桥接模式，不创建实际 CAN Bus。DBC 已加载。")
            # 在这种模式下，连接状态视为已就绪，因为 DBC 已加载
            self.connection_status_changed.emit(channel, True)

    @Slot(str)
    def disconnect_can_interface(self, channel: str):
        """
        断开指定的 CAN 总线接口。
        :param channel: CAN 接口通道。
        """
        # 清理 Notifier 和 Timer
        if channel in self._notifier:
            self._notifier[channel].stop()
            del self._notifier[channel]
        if channel in self._read_timers:
            self._read_timers[channel].stop()
            self._read_timers[channel].deleteLater()
            del self._read_timers[channel]

        # 如果存在实际的 can.Bus 实例，则关闭
        if channel in self._can_buses:
            try:
                self._can_buses[channel].shutdown()
                self.connection_status_changed.emit(channel, False)
                self.logger.info(f"CanBusCommunicator: CAN 接口 '{channel}' 已断开。")
                del self._can_buses[channel]
            except Exception as e:
                error_msg = f"断开 CAN 接口 '{channel}' 失败: {e}"
                self.logger.error(f"CanBusCommunicator: {error_msg}")
                self.can_error.emit(channel, error_msg)
        else:
            # 如果没有实际的 can.Bus，但 DBC 已加载，也视为"断开配置"
            if channel in self._dbcs:
                self._dbcs.pop(channel, None)
                self.connection_status_changed.emit(channel, False)
                self.logger.info(f"CanBusCommunicator: CAN 通道 '{channel}' 的配置（包括 DBC）已清除。")
            else:
                self.logger.warning(f"CanBusCommunicator: 尝试断开不存在或未配置的 CAN 接口 '{channel}'。")


    @Slot(str, int, bytes)
    def send_can_frame(self, channel: str, arbitration_id: int, data: bytes):
        """
        向指定 CAN 总线发送原始 CAN 帧。
        注意：此方法仅适用于通过 can.Bus 实际连接的 CAN 接口。
        对于串口桥接模式，命令的发送逻辑通常会通过 DeviceProtocolParser 最终回到 SerialCommunicator。
        :param channel: CAN 接口通道。
        :param arbitration_id: 仲裁ID (CAN ID)。
        :param data: 要发送的字节数据 (DLC 长度，最大 8 字节)。
        """
        if channel not in self._can_buses or not self._can_buses[channel].is_filtered:
            self.logger.warning(f"CanBusCommunicator: CAN 通道 '{channel}' 未连接或不活跃，无法发送帧。如果是串口桥接模式，请通过 DeviceProtocolParser->SerialCommunicator发送命令。")
            return
        try:
            msg = can.Message(arbitration_id=arbitration_id, data=data)
            self.logger.debug(f"CanBusCommunicator: 向 CAN 通道 '{channel}' 发送帧: {msg}")
            self._can_buses[channel].send(msg)
        except Exception as e:
            error_msg = f"向 CAN 通道 '{channel}' 发送帧失败: {e}"
            self.logger.error(f"CanBusCommunicator: {error_msg}")
            self.can_error.emit(channel, error_msg)

    @Slot(str, int, dict)
    def send_can_signals(self, channel: str, message_id: int, signals: Dict[str, Any]):
        """
        根据 DBC 文件编码并发送 CAN 信号数据。
        注意：此方法仅适用于通过 can.Bus 实际连接的 CAN 接口。
        对于串口桥接模式，命令的发送逻辑通常会通过 DeviceProtocolParser 最终回到 SerialCommunicator。
        :param channel: CAN 接口通道。
        :param message_id: CAN 报文ID (用于在 DBC 中查找报文)。
        :param signals: 信号名称-值字典，如 {"EngineRPM": 1500, "Temperature": 80.5}。
        """
        if channel not in self._dbcs:
            error_msg = f"CAN 通道 '{channel}' 未加载 DBC 文件，无法编码信号。"
            self.logger.error(f"CanBusCommunicator: {error_msg}")
            self.can_error.emit(channel, error_msg)
            return
        if channel not in self._can_buses or not self._can_buses[channel].is_filtered:
            self.logger.warning(f"CanBusCommunicator: CAN 通道 '{channel}' 未连接或不活跃，无法编码并发送信号。如果是串口桥接模式，请通过 DeviceProtocolParser->SerialCommunicator发送命令。")
            return
        try:
            db = self._dbcs[channel]
            message_definition = db.get_message_by_frame_id(message_id)
            encoded_data = message_definition.encode(signals)
            self.send_can_frame(channel, message_id, encoded_data)
            self.logger.debug(f"CanBusCommunicator: 已编码并发送 CAN 信号到通道 '{channel}', ID: {message_id}, 信号: {signals}")
        except Exception as e:
            error_msg = f"编码或发送 CAN 信号到通道 '{channel}' (ID: {message_id}) 失败: {e}"
            self.logger.error(f"CanBusCommunicator: {error_msg}")
            self.can_error.emit(channel, error_msg)

    @Slot(str, int, bytes, bool)
    def process_serial_can_frame(self, port_name: str, arbitration_id: int, data: bytes, is_extended_id: bool):
        """
        接收从 SerialCommunicator 发送的解析后的 CAN 帧组件，并进行进一步处理（如 DBC 解析）。
        这里将 port_name 作为 channel 来处理，以便复用 DBC 逻辑。
        :param port_name: 串口名称 (作为 CAN channel)。
        :param arbitration_id: 仲裁ID。
        :param data: 字节数据。
        :param is_extended_id: 是否为扩展ID。
        """
        self.logger.debug(f"CanBusCommunicator: 收到来自串口 '{port_name}' 的 CAN 帧组件: ID=0x{arbitration_id:X}, Data={bytes(data).hex()}")
        # 对于串口桥接模式，我们期望 _dbcs 中已经加载了该 port_name 对应的 DBC 文件
        if port_name not in self._dbcs:
            self.logger.warning(f"CanBusCommunicator: 通道 '{port_name}' 未加载 DBC 文件，无法解析接收到的 CAN 帧。")
            return

        msg = can.Message(
            arbitration_id=arbitration_id,
            data=data,
            is_extended_id=is_extended_id,
            dlc=len(data)
        )
        # 需要将端口号转换成设备名

        # port_name="DeepMotor"  # 临时测试
        self._on_can_message_received(port_name, msg)

    def _check_for_can_messages(self, channel: str, reader: BufferedReader):
        """
        内部方法：周期性检查 BufferedReader 中是否有新的 CAN 消息。
        此方法仅用于连接了实际 can.Bus 实例的通道。
        """
        while True:
            msg = reader.get_message()
            if msg is None:
                break
            self._on_can_message_received(channel, msg)

    def _on_can_message_received(self, channel: str, msg: Message):
        """
        内部方法：处理接收到的 CAN 消息。
        使用 DBC 文件进行解析。
        :param channel: 接收消息的 CAN 通道。
        :param msg: can.Message 对象。
        """
        self.logger.debug(f"CanBusCommunicator: 收到 CAN 帧 (通道 '{channel}'): {msg}")
        
        # 获取与该通道关联的设备实例ID
        actual_device_id = self._channel_to_device_id_map.get(channel, channel)
        if actual_device_id == channel:
            self.logger.warning(f"CanBusCommunicator: 通道 '{channel}' 未映射到具体的设备实例ID。将使用通道名作为设备ID。")

        # 使用 DBC 解析
        if channel in self._dbcs:
            try:
                db = self._dbcs[channel]
                message_definition = db.get_message_by_frame_id(msg.arbitration_id)
                decoded_signals = message_definition.decode(msg.data)
                self.logger.info(f"CanBusCommunicator: DBC解析后的 CAN 信号 (通道 '{channel}', 映射设备 '{actual_device_id}', ID 0x{msg.arbitration_id:X}): {decoded_signals}")
                self.can_parsed_data_received.emit(actual_device_id, decoded_signals)
            except KeyError:
                self.logger.debug(f"CanBusCommunicator: CAN ID 0x{msg.arbitration_id:X} 在 DBC 中未定义 (通道 '{channel}')。")
            except Exception as e:
                self.logger.warning(f"CanBusCommunicator: DBC解析 CAN 消息 (ID 0x{msg.arbitration_id:X}) 失败: {e}")
                self.can_error.emit(channel, f"DBC解析CAN消息失败: {e}")
        else:
            self.logger.warning(f"CanBusCommunicator: 通道 '{channel}' 未加载 DBC 文件，无法解析 CAN 消息。")

    def cleanup(self):
        """
        清理所有打开的 CAN 总线资源。
        """
        self.logger.info("CanBusCommunicator: 清理中...")
        for channel in list(self._can_buses.keys()):
            self.disconnect_can_interface(channel)
        
        # 停止所有可能遗留的定时器
        for channel in list(self._read_timers.keys()):
            if self._read_timers[channel].isActive():
                self._read_timers[channel].stop()
                self._read_timers[channel].deleteLater()
            del self._read_timers[channel] # Ensure removed from dict

        self._dbcs.clear() # 清除所有加载的DBCs
        self.logger.info("CanBusCommunicator: 清理完成。")
