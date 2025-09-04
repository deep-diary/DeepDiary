# src/app_logic/core_manager/handler/device_logic_manager.py
# 设备逻辑管理器处理器，负责处理设备逻辑管理相关的信号连接和事件处理

from PySide6.QtCore import Slot, Signal
from deepwin.app_logic.core_manager.base_handler import BaseHandler
from typing import Dict, Any, List, Union, Optional
import time

class DeviceLogicManagerHandler(BaseHandler):
    """
    DeviceLogicManager处理器
    负责处理设备逻辑管理相关的信号连接和事件处理
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        
    def _validate_dependencies(self):
        """
        验证必需的依赖项是否已设置
        """
        if not self.logger:
            raise ValueError("缺少必需的依赖项: logger")
        if not self.device_logic_manager:
            raise ValueError("缺少必需的依赖项: device_logic_manager")
        if not self.device_protocol_parser:
            raise ValueError("缺少必需的依赖项: device_protocol_parser")
        if not self.serial_communicator:
            raise ValueError("缺少必需的依赖项: serial_communicator")
        if not self.can_bus_communicator:
            raise ValueError("缺少必需的依赖项: can_bus_communicator")
        if not self.gui_manager:
            raise ValueError("缺少必需的依赖项: gui_manager")
        if not self.ai_coordinator:
            raise ValueError("缺少必需的依赖项: ai_coordinator")
        if not self.coordinator_handler:
            raise ValueError("缺少必需的依赖项: coordinator_handler")
            
    def _connect_signals(self):
        """
        连接设备逻辑管理器发出的信号到协调器的方法。
        这些信号通常表示设备状态更新、命令响应或错误。
        """
        self.logger.debug("DeviceLogicManagerHandler: 连接设备逻辑管理器信号...")
        
        # 设备逻辑管理器 -> Coordinator 的信号
        self.device_logic_manager.device_status_updated.connect(self.handle_device_states_updated)
        self.device_logic_manager.device_command_response.connect(
            lambda msg: self.coordinator_handler.app_status_message.emit(f"设备命令响应: {msg}")
        )
        self.device_logic_manager.device_error.connect(
            lambda msg: self.coordinator_handler.app_status_message.emit(f"设备错误: {msg}")
        )
        self.device_logic_manager.send_device_abstract_command_requested.connect(self._on_device_abstract_command_requested)
        
        # 连接DeviceLogicManager的轨迹执行相关信号
        self.device_logic_manager.trajectory_execution_progress_updated.connect(self.handle_trajectory_execution_progress)
        self.device_logic_manager.trajectory_execution_finished.connect(self.handle_trajectory_execution_finished)
        self.device_logic_manager.trajectory_execution_error.connect(self.handle_trajectory_execution_error)
        
        # 连接DeviceLogicManager的示教轨迹实时更新信号
        self.device_logic_manager.teaching_trajectory_updated.connect(self.handle_teaching_trajectory_updated)
        
        self.logger.debug("DeviceLogicManagerHandler: 设备逻辑管理器信号连接完成。")
        
    @Slot(str, dict)
    def handle_device_states_updated(self, device_id: str, data: dict):
        """
        处理来自 DeviceLogicManager 的设备状态更新。
        将数据转发到 UI 和 AI 协调器。
        """
        # 转发到 UI
        if self.gui_manager and self.gui_manager.window:
            if device_id == "DeepMotor":
                deep_motor_page = self.gui_manager.window.deviceInterface.get_deep_motor_page()
                if deep_motor_page and hasattr(deep_motor_page, 'update_motor_data'):
                    deep_motor_page.update_motor_data(data)
                
                # 如果当前显示的是历史曲线参数，自动触发历史数据请求以刷新曲线
                if deep_motor_page and hasattr(deep_motor_page, 'current_selected_param'):
                    current_param = deep_motor_page.current_selected_param
                    if not current_param.startswith('trajectory_'):
                        # 非轨迹参数，自动请求历史数据刷新曲线
                        self.handle_request_history_data(device_id, current_param)

        # 转发到 AI 协调器
        if self.ai_coordinator:
            self.ai_coordinator.perceive_device_state(device_id, data)

    @Slot(str, str, list)
    def _on_device_abstract_command_requested(self, device_id: str, command_name: str, params: dict = None):
        """
        槽函数：处理 DeviceLogicManager 发出的抽象命令发送请求。
        采用分层架构方式2：逐层传递数据
        命令 → 协议层 → CAN帧 → CAN层 → 串口帧 → 串口层
        """
        self.logger.info(f"DeviceLogicManagerHandler: 收到抽象命令发送请求 - 设备: {device_id}, 命令: {command_name}, 参数: {params}")
        try:
            # ==================== 第1层：协议层 - 命令 → CAN帧 ====================
            self.logger.debug(f"DeviceLogicManagerHandler: 第1层 - 协议层转换命令为CAN帧")
            can_frame_data = self.device_protocol_parser.convert_command_to_can_frame(device_id, command_name, params)
            
            if not can_frame_data:
                error_msg = f"协议层转换失败：无法将命令 '{command_name}' 转换为CAN帧"
                self.logger.error(f"DeviceLogicManagerHandler: {error_msg}")
                self.coordinator_handler.app_status_message.emit(error_msg)
                return
            
            # 检查是否为多帧命令
            if isinstance(can_frame_data, list):
                # 多帧命令处理
                self.logger.info(f"DeviceLogicManagerHandler: 协议层转换成功 - 多帧命令，共 {len(can_frame_data)} 帧")
                self._process_multiframe_command(can_frame_data, device_id, command_name, params)
            else:
                # 单帧命令处理
                self.logger.info(f"DeviceLogicManagerHandler: 协议层转换成功 - 单帧命令，CAN帧ID: 0x{can_frame_data['arbitration_id']:X}")
                self._process_singleframe_command(can_frame_data, device_id, command_name, params)
                
        except Exception as e:
            error_msg = f"处理设备抽象命令 '{command_name}' 失败: {e}"
            self.logger.error(f"DeviceLogicManagerHandler: {error_msg}")
            self.coordinator_handler.app_status_message.emit(f"命令发送失败: {error_msg}")
            self.device_logic_manager.device_error.emit(error_msg)
    
    def _process_singleframe_command(self, can_frame: Dict[str, Any], device_id: str, command_name: str, params: Dict[str, Any]):
        """
        处理单帧命令
        """
        try:
            # ==================== 第2层：CAN层 - CAN帧 → 串口帧 ====================
            self.logger.debug(f"DeviceLogicManagerHandler: 第2层 - CAN层转换CAN帧为串口帧")
            serial_frame = self.can_bus_communicator.send_can_frame(
                can_frame['arbitration_id'], 
                can_frame['data'], 
                can_frame.get('is_extended_id', True)
            )
            
            if not serial_frame:
                error_msg = f"CAN层转换失败：无法将CAN帧转换为串口帧"
                self.logger.error(f"DeviceLogicManagerHandler: {error_msg}")
                self.coordinator_handler.app_status_message.emit(error_msg)
                return
            
            self.logger.info(f"DeviceLogicManagerHandler: CAN层转换成功 - 串口帧: {serial_frame.hex()}")
            
            # ==================== 第3层：串口层 - 串口帧 → 实际发送 ====================
            self._send_serial_data(serial_frame, device_id, command_name, params)
            
        except Exception as e:
            error_msg = f"处理单帧命令失败: {e}"
            self.logger.error(f"DeviceLogicManagerHandler: {error_msg}")
            self.coordinator_handler.app_status_message.emit(error_msg)
    
    def _process_multiframe_command(self, can_frames: List[Dict[str, Any]], device_id: str, command_name: str, params: Dict[str, Any]):
        """
        处理多帧命令
        """
        try:
            self.logger.info(f"DeviceLogicManagerHandler: 开始处理多帧命令，共 {len(can_frames)} 帧")
            
            # 获取目标端口
            target_port_name = self._get_device_port(device_id)
            if not target_port_name:
                self.logger.warning(f"DeviceLogicManagerHandler: 无法确定设备 '{device_id}' 对应的串口")
                self.coordinator_handler.app_status_message.emit(f"无法确定设备 '{device_id}' 对应的串口")
                # 反馈模拟数据
                position = params.get('pos', 0.0) if params else 0.0
                self.serial_communicator.sim_read_serial_data(position=position)
                return
            
            # 逐帧处理
            for i, can_frame in enumerate(can_frames):
                self.logger.debug(f"DeviceLogicManagerHandler: 处理第 {i+1}/{len(can_frames)} 帧")
                
                # ==================== 第2层：CAN层 - CAN帧 → 串口帧 ====================
                serial_frame = self.can_bus_communicator.send_can_frame(
                    can_frame['arbitration_id'], 
                    can_frame['data'], 
                    can_frame.get('is_extended_id', True)
                )
                
                if not serial_frame:
                    error_msg = f"CAN层转换失败：第 {i+1} 帧无法转换为串口帧"
                    self.logger.error(f"DeviceLogicManagerHandler: {error_msg}")
                    self.coordinator_handler.app_status_message.emit(error_msg)
                    return
                
                self.logger.debug(f"DeviceLogicManagerHandler: 第 {i+1} 帧转换成功 - 串口帧: {serial_frame.hex()}")
                
                # ==================== 第3层：串口层 - 串口帧 → 实际发送 ====================
                send_success = self.serial_communicator.send_bytes(target_port_name, serial_frame)
                
                if send_success is None:
                    # 串口不存在或发送失败，触发模拟数据反馈
                    self.logger.warning(f"DeviceLogicManagerHandler: 多帧命令第 {i+1} 帧串口发送失败，触发模拟数据反馈")
                    position = params.get('pos', 0.0) if params else 0.0
                    self.serial_communicator.sim_read_serial_data(position=position)
                    self.coordinator_handler.app_status_message.emit(f"串口不存在，多帧命令 '{command_name}' 已触发模拟数据反馈")
                    return
                
                # 帧间延迟，避免连续发送过快
                if i < len(can_frames) - 1:  # 不是最后一帧
                    time.sleep(0.01)
            
            self.logger.info(f"DeviceLogicManagerHandler: 多帧命令发送成功 - 端口: {target_port_name}")
            self.coordinator_handler.app_status_message.emit(f"多帧命令已成功发送到设备 {device_id} (端口: {target_port_name})")
            
        except Exception as e:
            error_msg = f"处理多帧命令失败: {e}"
            self.logger.error(f"DeviceLogicManagerHandler: {error_msg}")
            self.coordinator_handler.app_status_message.emit(error_msg)
    
    def _send_serial_data(self, serial_frame: bytes, device_id: str, command_name: str, params: Dict[str, Any]):
        """
        发送串口数据的通用方法
        """
        try:
            # 获取目标端口
            target_port_name = self._get_device_port(device_id)
            if not target_port_name:
                self.logger.warning(f"DeviceLogicManagerHandler: 无法确定设备 '{device_id}' 对应的串口")
                self.coordinator_handler.app_status_message.emit(f"无法确定设备 '{device_id}' 对应的串口")
                # 反馈模拟数据
                position = params.get('pos', 0.0) if params else 0.0
                self.serial_communicator.sim_read_serial_data(position=position)
                return
            
            # 发送串口数据
            send_success = self.serial_communicator.send_bytes(target_port_name, serial_frame)
            
            if send_success is not None:
                self.logger.info(f"DeviceLogicManagerHandler: 串口层发送成功 - 端口: {target_port_name}")
                self.coordinator_handler.app_status_message.emit(f"命令已成功发送到设备 {device_id} (端口: {target_port_name})")
            else:
                # 串口不存在或发送失败，触发模拟数据反馈
                self.logger.warning(f"DeviceLogicManagerHandler: 单帧命令串口 '{target_port_name}' 不存在或发送失败，触发模拟数据反馈")
                position = params.get('pos', 0.0) if params else 0.0
                self.serial_communicator.sim_read_serial_data(position=position)
                self.coordinator_handler.app_status_message.emit(f"串口不存在，单帧命令 '{command_name}' 已触发模拟数据反馈")
                
        except Exception as e:
            error_msg = f"发送串口数据失败: {e}"
            self.logger.error(f"DeviceLogicManagerHandler: {error_msg}")
            self.coordinator_handler.app_status_message.emit(error_msg)
    
    def _get_device_port(self, device_id: str) -> str:
        """
        获取设备对应的串口端口
        :param device_id: 设备ID
        :return: 端口名称，如果未找到则返回None
        """
        try:
            port_mapping = self.serial_communicator.get_port_device_mapping()
            for port, dev_id in port_mapping.items():
                if dev_id == device_id:
                    return port
            return None
        except Exception as e:
            self.logger.error(f"DeviceLogicManagerHandler: 获取设备端口失败: {e}")
            return None

    @Slot(str, dict)
    def handle_trajectory_execution_progress(self, device_id: str, progress_data: dict):
        """
        处理来自 DeviceLogicManager 的轨迹执行进度信号。
        通过CoordinatorHandler转发到UI。
        """
        self.logger.debug(f"DeviceLogicManagerHandler: 收到轨迹执行进度 for '{device_id}', data keys: {progress_data.keys()}")
        
        # 通过CoordinatorHandler转发信号
        try:
            self.coordinator_handler.emit_trajectory_execution_progress(device_id, progress_data)
        except Exception as e:
            self.logger.error(f"DeviceLogicManagerHandler: 转发轨迹执行进度信号失败: {e}")

    @Slot(str, str)
    def handle_trajectory_execution_finished(self, device_id: str, trajectory_name: str):
        self.logger.info(f"DeviceLogicManagerHandler: 轨迹执行完成，设备: {device_id}, 轨迹: {trajectory_name}")
        
        # 通过CoordinatorHandler转发信号
        try:
            self.coordinator_handler.emit_trajectory_execution_finished(device_id)
            self.logger.info(f"DeviceLogicManagerHandler: 已通过CoordinatorHandler发射轨迹执行完成信号，参数: {device_id}")
        except Exception as e:
            self.logger.error(f"DeviceLogicManagerHandler: 转发轨迹执行完成信号失败: {e}")

    @Slot(str, str)
    def handle_trajectory_execution_error(self, device_id: str, error_message: str):
        self.logger.error(f"DeviceLogicManagerHandler: 轨迹执行错误，设备: {device_id}, 错误: {error_message}")
        
        # 通过CoordinatorHandler转发信号
        try:
            self.coordinator_handler.emit_trajectory_execution_error(device_id, error_message)
            self.logger.info(f"DeviceLogicManagerHandler: 已通过CoordinatorHandler发射轨迹执行错误信号，参数: {device_id}, {error_message}")
        except Exception as e:
            self.logger.error(f"DeviceLogicManagerHandler: 转发轨迹执行错误信号失败: {e}")

    @Slot(str, list, list)
    def handle_teaching_trajectory_updated(self, device_id: str, times: list, positions: list):
        """处理示教轨迹实时更新信号"""
        # 转发给UI
        deep_motor_page = self.gui_manager.window.deviceInterface.get_deep_motor_page()
        if deep_motor_page and hasattr(deep_motor_page, 'update_teaching_trajectory'):
            deep_motor_page.update_teaching_trajectory(times, positions)
        else:
            self.logger.warning("DeviceLogicManagerHandler: GUI管理器不可用，无法转发示教轨迹更新信号")
            
    def handle_request_history_data(self, device_name: str, param_name: str):
        """处理历史数据请求"""
        self.logger.info(f"DeviceLogicManagerHandler: 收到历史数据请求，设备: {device_name}, 参数: {param_name}")
        if device_name == "DeepMotor":
            deep_motor_page = self.gui_manager.window.deviceInterface.get_deep_motor_page()
            if not deep_motor_page:
                self.logger.warning("DeepMotor页面未找到")
                return
                
            # 检查是否是轨迹相关参数
            if param_name.startswith('trajectory_'):
                if hasattr(deep_motor_page, '_current_trajectory'):
                    current_trajectory = deep_motor_page._current_trajectory
                    if not current_trajectory:
                        self.logger.warning("请求轨迹数据但未选择轨迹")
                        self.coordinator_handler.app_status_message.emit("请先选择一条轨迹")
                        return
                    
                    options = {"trajectory_name": current_trajectory}
                    # 使用新的架构：直接访问设备实例
                    motor = self.device_logic_manager.deep_motor
                    if motor:
                        history_data = motor.get_historical_data(param_name, options)
                    else:
                        self.logger.error("DeepMotor设备未找到")
                        return
                else:
                    self.logger.warning("DeepMotor页面没有_current_trajectory属性")
                    return
            else:
                # 使用新的架构：直接访问设备实例
                motor = self.device_logic_manager.deep_motor
                if motor:
                    history_data = motor.get_historical_data(param_name, {})
                else:
                    self.logger.error("DeepMotor设备未找到")
                    return
            
            if history_data is not None:
                if hasattr(deep_motor_page, 'update_history_curve'):
                    deep_motor_page.update_history_curve(history_data)