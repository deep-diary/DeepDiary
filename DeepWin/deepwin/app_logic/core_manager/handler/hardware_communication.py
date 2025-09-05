# src/app_logic/core_manager/handler/hardware_communication.py
# 硬件通信处理器，负责处理所有硬件通信相关的信号连接和事件处理

from PySide6.QtCore import Slot
from deepwin.app_logic.core_manager.base_handler import BaseHandler

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
        if not self.can_bus_communicator:
            raise ValueError("缺少必需的依赖项: can_bus_communicator")
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
        
        # 连接串口数据发送信号到UI
        self.serial_communicator.raw_frame_send.connect(
            self._on_serial_data_sent
        )
        
        # 2. 连接CAN通信器信号
        self.can_bus_communicator.can_frame_received.connect(
            self._on_can_data_received
        )
        self.can_bus_communicator.can_frame_sent.connect(
            self._on_can_data_sent
        )
        
        # 3. 连接设备协议解析器信号
        # 注意：device_semantic_data_ready 信号仍然需要，因为协议层会发送信号
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
        处理从串口接收到的原始帧数据 - 逐层向上传递
        串口层 → CAN层 → 协议层 → 信号字典 → 信号发出
        """
        self.logger.debug(f"HardwareCommunicationHandler: 收到串口数据 - 端口: {port_name}, 数据: {raw_frame_data.hex()}")
        
        try:
            # ==================== 第1层：串口层 - 处理串口数据 ====================
            self.logger.debug(f"HardwareCommunicationHandler: 第1层 - 串口层处理数据")
            serial_result = self.serial_communicator.process_received_data(port_name, raw_frame_data)
            
            if not serial_result:
                self.logger.warning(f"HardwareCommunicationHandler: 串口层处理失败")
                return
            
            self.logger.debug(f"HardwareCommunicationHandler: 串口层处理成功")
            
            # ==================== 第2层：CAN层 - 串口数据 → CAN帧 ====================
            self.logger.debug(f"HardwareCommunicationHandler: 第2层 - CAN层转换串口数据为CAN帧")
            can_result = self.can_bus_communicator.process_serial_data(raw_frame_data)
            
            if not can_result:
                self.logger.warning(f"HardwareCommunicationHandler: CAN层转换失败")
                return
            
            self.logger.debug(f"HardwareCommunicationHandler: CAN层转换成功 - CAN ID: 0x{can_result['arbitration_id']:X}")
            
            # ==================== 第3层：协议层 - CAN帧 → 信号字典 ====================
            self.logger.debug(f"HardwareCommunicationHandler: 第3层 - 协议层解析CAN帧为信号字典")
            
            # 获取设备ID
            device_id = self.serial_communicator.get_device_id_from_port(port_name)
            if not device_id:
                self.logger.warning(f"HardwareCommunicationHandler: 收到来自未知串口 '{port_name}' 的数据，无法映射到设备ID")
                device_id = "DeepMotor"  # 调试时使用默认值
            
            semantic_result = self.device_protocol_parser.parse_serial_frame_to_signals(device_id, raw_frame_data)
            
            if semantic_result:
                self.logger.info(f"HardwareCommunicationHandler: 协议层解析成功 - 设备: {device_id}")
                self.logger.debug(f"HardwareCommunicationHandler: 信号字典: {semantic_result}")
                
                # 转发串口接收数据到UI
                if self.gui_manager and self.gui_manager.window:
                    deep_motor_page = self.gui_manager.window.deviceInterface.get_deep_motor_page()
                    if deep_motor_page:
                        deep_motor_page.add_communication_data(
                            direction="receive",
                            protocol="serial",
                            data=raw_frame_data,
                            description=f"串口接收 - {port_name}"
                        )
            else:
                self.logger.warning(f"HardwareCommunicationHandler: 协议层解析失败")
                
        except Exception as e:
            self.logger.error(f"HardwareCommunicationHandler: 处理串口数据失败: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            
    @Slot(str, bytes, str)
    def _on_serial_data_sent(self, port_name: str, data: bytes, send_status: str):
        """处理串口数据发送信号，转发到UI"""
        self.logger.debug(f"HardwareCommunicationHandler: 串口数据发送 - 端口: {port_name}, 数据: {data.hex()}, 状态: {send_status}")
        
        # 转发到UI通信显示组件
        if self.gui_manager and self.gui_manager.window:
            deep_motor_page = self.gui_manager.window.deviceInterface.get_deep_motor_page()
            if deep_motor_page:
                # 尝试从串口通信器获取更多信息
                frame_info = self.serial_communicator.get_sent_frame_info(port_name, data)
                if frame_info:
                    command = frame_info.get('command', 'unknown')
                    frame_index = frame_info.get('frame_index', 1)
                    total_frames = frame_info.get('total_frames', 1)
                    params = frame_info.get('params', {})
                    
                    # 构建参数字符串
                    param_str = ""
                    if params:
                        param_parts = []
                        for key, value in params.items():
                            param_parts.append(f"{key}={value}")
                        param_str = f"({', '.join(param_parts)})"
                    
                    # 添加发送状态指示器
                    status_indicator = "✓" if send_status == "OK" else "✗"
                    
                    if total_frames > 1:
                        description = f"电机命令 - {command}{param_str} [帧 {frame_index}/{total_frames}] {status_indicator}"
                    else:
                        description = f"电机命令 - {command}{param_str} {status_indicator}"
                else:
                    # 添加发送状态指示器
                    status_indicator = "✓" if send_status == "OK" else "✗"
                    description = f"串口发送 - {port_name} {status_indicator}"
                    
                deep_motor_page.add_communication_data(
                    direction="send",
                    protocol="serial", 
                    data=data,
                    description=description
                )
                
    @Slot(int, bytes)
    def _on_can_data_received(self, can_id: int, data: bytes):
        """处理CAN数据接收信号，转发到UI"""
        self.logger.debug(f"HardwareCommunicationHandler: CAN数据接收 - ID: 0x{can_id:X}, 数据: {data.hex()}")
        
        # 转发到UI通信显示组件
        if self.gui_manager and self.gui_manager.window:
            deep_motor_page = self.gui_manager.window.deviceInterface.get_deep_motor_page()
            if deep_motor_page:
                deep_motor_page.add_communication_data(
                    direction="receive",
                    protocol="can",
                    data=data,
                    description=f"CAN接收 - ID: 0x{can_id:X}",
                    can_id=can_id
                )
                
    @Slot(int, bytes, bool)
    def _on_can_data_sent(self, can_id: int, data: bytes, is_extended_id: bool = True):
        """处理CAN数据发送信号，转发到UI"""
        self.logger.debug(f"HardwareCommunicationHandler: CAN数据发送 - ID: 0x{can_id:X}, 数据: {data.hex()}")
        
        # 转发到UI通信显示组件
        if self.gui_manager and self.gui_manager.window:
            deep_motor_page = self.gui_manager.window.deviceInterface.get_deep_motor_page()
            if deep_motor_page:
                # 尝试从设备逻辑管理器处理器获取命令信息
                device_logic_handler = getattr(self, 'device_logic_manager_handler', None)
                if device_logic_handler:
                    command_info = device_logic_handler.get_last_command_info()
                    self.logger.info(f"HardwareCommunicationHandler: 获取到命令信息: {command_info}")
                else:
                    # 如果直接访问失败，尝试通过coordinator_handler访问
                    if hasattr(self, 'coordinator_handler') and self.coordinator_handler:
                        device_logic_handler = getattr(self.coordinator_handler, 'device_logic_manager_handler', None)
                        if device_logic_handler:
                            command_info = device_logic_handler.get_last_command_info()
                            self.logger.info(f"HardwareCommunicationHandler: 通过coordinator_handler获取到命令信息: {command_info}")
                        else:
                            command_info = None
                            self.logger.info(f"HardwareCommunicationHandler: 无法通过coordinator_handler获取命令信息")
                    else:
                        command_info = None
                        self.logger.info(f"HardwareCommunicationHandler: 无法获取device_logic_manager_handler")
                
                if command_info:
                    command = command_info.get('command', 'unknown')
                    frame_index = command_info.get('frame_index', 1)
                    total_frames = command_info.get('total_frames', 1)
                    params = command_info.get('params', {})
                    
                    # 构建参数字符串
                    param_str = ""
                    if params:
                        param_parts = []
                        for key, value in params.items():
                            param_parts.append(f"{key}={value}")
                        param_str = f"({', '.join(param_parts)})"
                    
                    if total_frames > 1:
                        description = f"电机命令 - {command}{param_str} [帧 {frame_index}/{total_frames}]"
                    else:
                        description = f"电机命令 - {command}{param_str}"
                else:
                    description = f"CAN发送 - ID: 0x{can_id:X}"
                    
                deep_motor_page.add_communication_data(
                    direction="send",
                    protocol="can",
                    data=data,
                    description=description,
                    can_id=can_id
                )