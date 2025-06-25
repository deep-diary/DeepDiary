# src/app_logic/core_manager/handler/hardware_communication.py
# 硬件通信处理器，负责处理所有硬件通信相关的信号连接和事件处理

from PySide6.QtCore import Slot
from src.app_logic.core_manager.base_handler import BaseHandler

class HardwareCommunicationHandler(BaseHandler):
    """
    硬件通信处理器
    负责处理串口通信、CAN总线通信、设备协议解析等硬件通信相关的信号连接和事件处理
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def _validate_dependencies(self):
        """
        验证必需的依赖项是否已设置
        """
        # 检查基础依赖项
        if not self.logger:
            raise ValueError("缺少必需的依赖项: logger")
        if not self.serial_communicator:
            raise ValueError("缺少必需的依赖项: serial_communicator")
        if not self.device_protocol_parser:
            raise ValueError("缺少必需的依赖项: device_protocol_parser")
        if not self.device_logic_manager:
            raise ValueError("缺少必需的依赖项: device_logic_manager")
        if not self.gui_manager:
            raise ValueError("缺少必需的依赖项: gui_manager")
        if not self.coordinator_handler:
            raise ValueError("缺少必需的依赖项: coordinator_handler")

    def _connect_signals(self):
        """
        连接硬件通信层相关的信号
        """
        self.logger.debug("HardwareCommunicationHandler: 连接硬件通信层信号...")
        
        # 1. 连接串口通信器信号
        self.serial_communicator.serial_error.connect(
            lambda p, msg: self.coordinator_handler.app_status_message.emit(f"串口错误 [{p}]: {msg}")
        )
        self.serial_communicator.connection_status_changed.connect(
            self._on_serial_connection_status_changed
        )
        self.serial_communicator.raw_frame_received.connect(
            self._on_raw_serial_frame_received
        )
        
        # 2. 连接设备协议解析器信号
        self.device_protocol_parser.device_semantic_data_ready.connect(
            self.device_logic_manager.handle_device_semantic_data
        )
        self.device_protocol_parser.protocol_conversion_error.connect(
            lambda dev_id, msg: self.coordinator_handler.app_status_message.emit(f"协议转换错误 [{dev_id}]: {msg}")
        )
        
        self.logger.debug("HardwareCommunicationHandler: 硬件通信层信号连接完成")
        
    @Slot(str, bool)
    def _on_serial_connection_status_changed(self, port: str, is_connected: bool):
        """
        处理串口连接状态变化
        """
        device_instance_id = 'DeepMotor'
        
        if is_connected:
            self.logger.info(f"HardwareCommunicationHandler: 串口 {port} 连接成功")
            self.coordinator_handler.app_status_message.emit(f"串口 {port} 连接成功")
            # 使用SerialCommunicator的映射功能
            self.serial_communicator.add_port_device_mapping(port, device_instance_id)
        else:
            self.logger.info(f"HardwareCommunicationHandler: 串口 {port} 已断开")
            self.coordinator_handler.app_status_message.emit(f"串口 {port} 已断开")
            # 使用SerialCommunicator的映射功能
            self.serial_communicator.remove_port_device_mapping(port)
            
        # 更新GUI连接状态
        if self.gui_manager and self.gui_manager.window:
            self.gui_manager.window.deviceInterface.serial_config.update_connection_status(is_connected)
            
    @Slot(str, bytes)
    def _on_raw_serial_frame_received(self, port_name: str, raw_frame_data: bytes):
        """
        处理从串口接收到的原始帧数据
        """
        # 使用SerialCommunicator的映射功能获取设备ID
        device_id = self.serial_communicator.get_device_id_from_port(port_name)
        
        if not device_id:
            self.logger.warning(f"HardwareCommunicationHandler: 收到来自未知串口 '{port_name}' 的数据，无法映射到设备ID。数据: {raw_frame_data.hex()}")
            device_id = "DeepMotor"  # 调试时使用默认值
        
        self.logger.debug(f"HardwareCommunicationHandler: 收到来自串口 '{port_name}' (设备 '{device_id}') 的原始帧数据: {raw_frame_data.hex()}")
        
        # 转发给设备协议解析器
        self.device_protocol_parser.parse_low_level_data(device_id, raw_frame_data)