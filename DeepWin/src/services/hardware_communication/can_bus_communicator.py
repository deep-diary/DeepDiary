from typing import Dict, Any, Optional
from PySide6.QtCore import QObject, Signal, Slot
from src.data_management.log_manager import LogManager
import can
from PySide6.QtCore import QTimer

class CanBusCommunicator(QObject):
    """
    CAN 总线通信模块。
    负责 CAN 报文的发送和接收，并根据 DBC 文件进行解析和编码。
    """
    can_raw_frame_received = Signal(str, bytes) # 收到原始 CAN 帧: (channel, raw_frame_bytes)
    can_parsed_data_received = Signal(str, dict) # 收到解析后的 CAN 信号数据: (channel, parsed_signals_dict)
    connection_status_changed = Signal(str, bool) # CAN 总线连接状态变更: (channel, is_connected)
    can_error = Signal(str, str) # CAN 总线错误: (channel, error_msg)

    def __init__(self, log_manager: LogManager, parent: Optional[QObject] = None):
        """
        初始化 CanBusCommunicator。
        :param log_manager: 全局日志管理器实例。
        :param parent: QObject 父对象。
        """
        super().__init__(parent)
        self.logger = log_manager.get_logger(__name__)
        self.logger.info("CanBusCommunicator: 初始化中...")
        self._can_buses: Dict[str, can.Bus] = {} # {channel: can.Bus_instance}
        self._dbcs: Dict[str, Any] = {} # {channel: cantools.db.Database_instance}
        self._notifier: Dict[str, can.Notifier] = {} # {channel: can.Notifier_instance}
        self.logger.info("CanBusCommunicator: 初始化完成。")

    @Slot(str, str, str)
    def connect_can_interface(self, channel: str, bustype: str, dbc_file_path: Optional[str] = None):
        """
        连接到 CAN 总线接口，并加载 DBC 文件。
        :param channel: CAN 接口通道 (如 'can0', 'COM1', 'Pcan_usb@USB0')。
        :param bustype: CAN 接口类型 (如 'socketcan', 'pcan', 'kvaser', 'virtual')。
        :param dbc_file_path: 可选的 DBC 文件路径，用于解析 CAN 报文。
        """
        if channel in self._can_buses:
            self.logger.warning(f"CanBusCommunicator: CAN 通道 '{channel}' 已连接。")
            return

        self.logger.info(f"CanBusCommunicator: 尝试连接 CAN 接口 '{channel}' ({bustype})...")
        try:
            # 连接 CAN 总线
            # 这里使用 'virtual' 类型来模拟，实际需要根据您的 CAN 硬件适配
            bus = can.Bus(channel=channel, bustype=bustype)
            self._can_buses[channel] = bus

            # 如果提供 DBC 文件路径，加载 DBC 文件
            if dbc_file_path:
                try:
                    import cantools # 需要安装 cantools 库: pip install cantools
                    db = cantools.database.load_file(dbc_file_path)
                    self._dbcs[channel] = db
                    self.logger.info(f"CanBusCommunicator: 已为通道 '{channel}' 加载 DBC 文件: {dbc_file_path}")
                except ImportError:
                    self.logger.warning("CanBusCommunicator: cantools 库未安装，无法解析 DBC 文件。请安装：pip install cantools")
                except Exception as e:
                    self.logger.error(f"CanBusCommunicator: 加载 DBC 文件 '{dbc_file_path}' 失败: {e}")

            # 启动 CAN 消息监听器
            # 注意：在真实环境中，notifier 和 listener 会在后台线程中运行，
            # 并通过回调或信号通知主线程。这里简化为一个直接的 lambda 
            # 并假设 bus.recv() 会在另一个线程被调用。
            # 对于 PySide6，更好的方法是使用 QThread 封装 can.Notifier 或 bus.recv() 循环。
            # 为了演示信号流，这里直接在回调中处理。
            listener = can.BufferedReader() # 使用 BufferedReader 来缓冲消息
            notifier = can.Notifier(bus, [listener], timeout=0.1) # timeout 应该匹配 QTimer 的周期
            self._notifier[channel] = notifier
            # 这里通过一个定时器来模拟从 BufferedReader 获取消息，并在主线程中处理
            timer = QTimer(self)
            timer.timeout.connect(lambda: self._check_for_can_messages(channel, listener))
            timer.start(50) # 每 50ms 检查一次缓冲区
            self._read_timers[channel] = timer # 存储计时器，以便清理

            self.connection_status_changed.emit(channel, True)
            self.logger.info(f"CanBusCommunicator: CAN 接口 '{channel}' 连接成功。")
        except Exception as e:
            error_msg = f"连接 CAN 接口 '{channel}' 失败: {e}"
            self.logger.error(f"CanBusCommunicator: {error_msg}")
            self.can_error.emit(channel, error_msg)

    @Slot(str)
    def disconnect_can_interface(self, channel: str):
        """
        断开指定的 CAN 总线接口。
        :param channel: CAN 接口通道。
        """
        if channel in self._can_buses:
            if channel in self._notifier:
                self._notifier[channel].stop()
                del self._notifier[channel]
            if channel in self._read_timers: # 停止并清理读取计时器
                self._read_timers[channel].stop()
                self._read_timers[channel].deleteLater()
                del self._read_timers[channel]
            try:
                self._can_buses[channel].shutdown()
                self.connection_status_changed.emit(channel, False)
                self.logger.info(f"CanBusCommunicator: CAN 接口 '{channel}' 已断开。")
                del self._can_buses[channel]
                self._dbcs.pop(channel, None) # 移除 DBC 引用
            except Exception as e:
                error_msg = f"断开 CAN 接口 '{channel}' 失败: {e}"
                self.logger.error(f"CanBusCommunicator: {error_msg}")
                self.can_error.emit(channel, error_msg)
        else:
            self.logger.warning(f"CanBusCommunicator: 尝试断开不存在的 CAN 接口 '{channel}'。")

    @Slot(str, int, bytes)
    def send_can_frame(self, channel: str, arbitration_id: int, data: bytes):
        """
        向指定 CAN 总线发送原始 CAN 帧。
        :param channel: CAN 接口通道。
        :param arbitration_id: 仲裁ID (CAN ID)。
        :param data: 要发送的字节数据 (DLC 长度，最大 8 字节)。
        """
        if channel not in self._can_buses or not self._can_buses[channel].is_filtered: # is_filtered 检查总线是否活跃
            self.logger.warning(f"CanBusCommunicator: CAN 通道 '{channel}' 未连接或不活跃，无法发送帧。")
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
        :param channel: CAN 接口通道。
        :param message_id: CAN 报文ID (用于在 DBC 中查找报文)。
        :param signals: 信号名称-值字典，如 {"EngineRPM": 1500, "Temperature": 80.5}。
        """
        if channel not in self._dbcs:
            error_msg = f"CAN 通道 '{channel}' 未加载 DBC 文件，无法编码信号。"
            self.logger.error(f"CanBusCommunicator: {error_msg}")
            self.can_error.emit(channel, error_msg)
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
        self.logger.info(f"CanBusCommunicator: 收到来自串口 '{port_name}' 的 CAN 帧组件: ID=0x{arbitration_id:X}, Data={data.hex()}")
        # 创建一个 can.Message 对象，以便复用现有的 DBC 解析逻辑
        msg = can.Message(
            arbitration_id=arbitration_id,
            data=data,
            is_extended_id=is_extended_id,
            dlc=len(data) # 确保 DLC 正确
        )
        self._on_can_message_received(port_name, msg) # 调用内部处理函数

    def _check_for_can_messages(self, channel: str, reader: can.BufferedReader):
        """
        内部方法：周期性检查 BufferedReader 中是否有新的 CAN 消息。
        """
        while True:
            msg = reader.get_message()
            if msg is None:
                break
            self._on_can_message_received(channel, msg)

    def _on_can_message_received(self, channel: str, msg: can.Message):
        """
        内部方法：处理接收到的 CAN 消息。
        如果加载了 DBC 文件，将进行解析。
        :param channel: 接收消息的 CAN 通道。
        :param msg: can.Message 对象。
        """
        self.logger.debug(f"CanBusCommunicator: 收到原始 CAN 帧 (通道 '{channel}'): {msg}")
        self.can_raw_frame_received.emit(channel, msg.data) # 发送原始帧数据

        if channel in self._dbcs:
            db = self._dbcs[channel]
            try:
                # 尝试通过 frame_id 获取 message 定义并解码
                message_definition = db.get_message_by_frame_id(msg.arbitration_id)
                decoded_signals = message_definition.decode(msg.data)
                self.logger.info(f"CanBusCommunicator: 解码后的 CAN 信号 (通道 '{channel}', ID 0x{msg.arbitration_id:X}): {decoded_signals}")
                self.can_parsed_data_received.emit(channel, decoded_signals) # 发送解析后的信号数据
            except KeyError:
                self.logger.debug(f"CanBusCommunicator: CAN ID 0x{msg.arbitration_id:X} 在 DBC 中未定义 (通道 '{channel}')。")
            except Exception as e:
                self.logger.warning(f"CanBusCommunicator: 解码 CAN 消息 (ID 0x{msg.arbitration_id:X}) 失败: {e}")
                self.can_error.emit(channel, f"解码CAN消息失败: {e}")

    def cleanup(self):
        """
        清理所有打开的 CAN 总线资源。
        """
        self.logger.info("CanBusCommunicator: 清理中...")
        for channel in list(self._can_buses.keys()):
            self.disconnect_can_interface(channel)
        # 清理 _read_timers
        for channel in list(self._read_timers.keys()):
            if self._read_timers[channel].isActive():
                self._read_timers[channel].stop()
                self._read_timers[channel].deleteLater()
        self.logger.info("CanBusCommunicator: 清理完成。")
