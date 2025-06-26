# src/app_logic/core_manager/handler/device_logic_manager.py
# 设备逻辑管理器处理器，负责处理设备逻辑管理相关的信号连接和事件处理

from PySide6.QtCore import Slot
from src.app_logic.core_manager.base_handler import BaseHandler
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
    def _on_device_abstract_command_requested(self, device_id: str, abstract_command_name: str, args: list):
        """
        槽函数：处理 DeviceLogicManager 发出的抽象命令发送请求。
        将抽象命令转换为底层协议命令并通过硬件通信服务发送。
        """
        self.logger.info(f"DeviceLogicManagerHandler: 收到抽象命令发送请求 - 设备: {device_id}, 命令: {abstract_command_name}, 参数: {args}")
        try:
            # 使用 DeviceProtocolParser 将抽象命令转换为底层字节命令（包含 AT 头等）
            low_level_command_bytes = self.device_protocol_parser.generate_low_level_command(
                device_id, abstract_command_name, *args
            )
            
            # 根据设备类型决定通过哪个通信器发送
            # 假设 DeepArm 和 DeepMotor 的底层命令都是通过串口发送的

            target_port_name = None
            # 直接使用SerialCommunicator的映射功能获取端口
            port_mapping = self.serial_communicator.get_port_device_mapping()
            # 从映射中查找设备对应的端口
            for port, dev_id in port_mapping.items():
                if dev_id == device_id:
                    target_port_name = port
                    break

            if not target_port_name:
                self.logger.warning(f"DeviceLogicManagerHandler: 无法确定设备 '{device_id}' 对应的串口。")
                self.coordinator_handler.app_status_message.emit(f"无法确定设备 '{device_id}' 对应的串口。")
                # 反馈模拟数据 - 修复list index out of range错误
                position = args[1] if len(args) > 1 else 0.0  # 如果args只有一个元素，使用默认值
                self.serial_communicator.sim_read_serial_data(position = position)
                return

            # 处理多帧命令
            if isinstance(low_level_command_bytes, list):
                for cmd_bytes in low_level_command_bytes:
                    self.logger.debug(f"DeviceLogicManagerHandler: 目标串口 '{target_port_name}'，底层命令 (多帧): {cmd_bytes.hex()}")
                    self.serial_communicator.send_bytes(target_port_name, cmd_bytes)
                    time.sleep(0.01) # 短暂延迟，避免连续发送过快导致串口拥堵
            else:
                self.logger.debug(f"DeviceLogicManagerHandler: 目标串口 '{target_port_name}'，底层命令: {low_level_command_bytes.hex()}")
                self.serial_communicator.send_bytes(target_port_name, low_level_command_bytes)
            
            self.coordinator_handler.app_status_message.emit(f"已将底层命令发送到串口: {target_port_name}")
        except Exception as e:
            error_msg = f"处理设备抽象命令 '{abstract_command_name}' 失败: {e}"
            self.logger.error(f"DeviceLogicManagerHandler: {error_msg}")
            self.coordinator_handler.app_status_message.emit(f"命令发送失败: {error_msg}")
            self.device_logic_manager.device_error.emit(error_msg) # 通知 DeviceLogicManager 错误

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