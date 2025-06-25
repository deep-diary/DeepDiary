# src/app_logic/core_manager/handler/gui_device_interface.py
# GUI设备接口处理器，负责处理GUI设备接口相关的信号连接和事件处理

from PySide6.QtCore import Slot
from src.app_logic.core_manager.base_handler import BaseHandler

class GuiDeviceInterfaceHandler(BaseHandler):
    """
    GUI设备接口处理器
    负责处理GUI设备接口相关的信号连接和事件处理
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def _validate_dependencies(self):
        """
        验证必需的依赖项是否已设置
        """
        if not self.logger:
            raise ValueError("缺少必需的依赖项: logger")
        if not self.gui_manager:
            raise ValueError("缺少必需的依赖项: gui_manager")
        if not self.device_logic_manager:
            raise ValueError("缺少必需的依赖项: device_logic_manager")
        if not self.serial_communicator:
            raise ValueError("缺少必需的依赖项: serial_communicator")
        if not self.coordinator_handler:
            raise ValueError("缺少必需的依赖项: coordinator_handler")
            
    # def _connect_signals(self):
    #     """
    #     连接GUI设备接口层相关的信号
    #     """
    #     self.logger.debug("GuiDeviceInterfaceHandler: 连接GUI设备接口层信号...")
        
    #     # 连接设备控制界面的信号
    #     self._connect_device_interface_signals()
        
    #     # 连接DeepMotor页面的信号
    #     self._connect_deep_motor_page_signals()
        
    #     # 连接测试按钮信号
    #     self._connect_test_button_signals()
        
    #     # 连接协调器输出信号到GUI
    #     self._connect_coordinator_output_signals()
        
    #     self.logger.debug("GuiDeviceInterfaceHandler: GUI设备接口层信号连接完成")
        
    # def _connect_device_interface_signals(self):
    #     """连接设备控制界面的信号"""
    #     device_interface = self.gui_manager.window.deviceInterface
        
    #     # 设备命令信号
    #     device_interface.ui_device_command.connect(self._handle_device_control_request)
        
    #     # 串口配置相关信号
    #     device_interface.serial_config.request_ports.connect(self._handle_ports_request)
    #     device_interface.serial_config.serial_connect_requested.connect(self._handle_serial_connect)
    #     device_interface.serial_config.serial_disconnect_requested.connect(self._handle_serial_disconnect)
        
    # def _connect_deep_motor_page_signals(self):
    #     """连接DeepMotor页面的信号"""
    #     deep_motor_page = self.gui_manager.window.deviceInterface.get_deep_motor_page()
    #     if deep_motor_page:
    #         self.logger.info("GuiDeviceInterfaceHandler: 找到DeepMotor页面，开始连接信号")
            
    #         # 数据请求信号
    #         deep_motor_page.request_sim_data.connect(self._handle_sim_data_request)
    #         deep_motor_page.request_history_data.connect(self._handle_request_history_data)
            
    #         # 示教相关信号
    #         deep_motor_page.start_teaching_requested.connect(self._handle_start_teaching_request)
    #         deep_motor_page.stop_teaching_requested.connect(self._handle_stop_teaching_request)
    #         deep_motor_page.execute_teaching_requested.connect(self._handle_execute_teaching_request)
            
    #         # 轨迹数据请求信号
    #         deep_motor_page.request_trajectory_data.connect(self._handle_trajectory_data_request)
    #         deep_motor_page.request_trajectory_list.connect(self._handle_trajectory_list_request)
            
    #         # 轨迹操作信号
    #         deep_motor_page.replan_requested.connect(self._handle_replan_requested)
    #         deep_motor_page.restore_default_requested.connect(self._handle_restore_default_requested)
    #         deep_motor_page.delete_trajectory_requested.connect(self._handle_delete_trajectory_requested)
            
    #         self.logger.info("GuiDeviceInterfaceHandler: DeepMotor页面信号连接完成")
    #     else:
    #         self.logger.warning("GuiDeviceInterfaceHandler: DeepMotor页面未找到，无法连接相关信号")
            
    # def _connect_test_button_signals(self):
    #     """连接测试按钮信号"""
    #     self.gui_manager.window.basicInputInterface.test_button_clicked.connect(self._handle_test_button_click)
        
    # def _connect_coordinator_output_signals(self):
    #     """连接协调器输出信号到GUI"""
    #     # 应用状态消息连接到设备接口状态栏
    #     self.app_status_message_signal.connect(
    #         self.gui_manager.window.deviceInterface.status_bar.setText
    #     )
        


    def _connect_signals(self):
        """
        连接来自 GUI 管理器中各个 UI 视图的请求信号到协调器对应的槽函数。
        这是 UI 层向应用逻辑层发起操作的主要途径。
        """
        self.logger.debug("GuiDeviceInterfaceHandler: 连接 GUI 信号...")
        # 设备控制界面 (deviceInterface.py)
        self.gui_manager.window.deviceInterface.ui_device_command.connect(self._handle_device_control_request)  # 添加设备命令信号绑定
        self.gui_manager.window.deviceInterface.serial_config.request_ports.connect(self._handle_ports_request) # 连接串口列表请求信号
        self.gui_manager.window.deviceInterface.serial_config.serial_connect_requested.connect(self._handle_serial_connect)  # 添加串口连接信号绑定
        self.gui_manager.window.deviceInterface.serial_config.serial_disconnect_requested.connect(self._handle_serial_disconnect)
        
        # 获取DeepMotor页面实例 - 使用新的架构
        deep_motor_page = self.gui_manager.window.deviceInterface.get_deep_motor_page()
        if deep_motor_page:
            self.logger.info("GuiDeviceInterfaceHandler: 找到DeepMotor页面，开始连接信号")
            # 连接DeepMotor页面的信号
            deep_motor_page.request_sim_data.connect(self._handle_sim_data_request)
            deep_motor_page.request_history_data.connect(self._handle_request_history_data)
            
            # 连接示教相关信号
            deep_motor_page.start_teaching_requested.connect(self._handle_start_teaching_request)
            deep_motor_page.stop_teaching_requested.connect(self._handle_stop_teaching_request)
            deep_motor_page.execute_teaching_requested.connect(self._handle_execute_teaching_request)
            
            # 连接轨迹数据请求信号
            deep_motor_page.request_trajectory_data.connect(self._handle_trajectory_data_request)
            
            # 连接轨迹列表请求信号
            deep_motor_page.request_trajectory_list.connect(self._handle_trajectory_list_request)
            # 新增：连接重规划请求信号
            deep_motor_page.replan_requested.connect(self._handle_replan_requested)
            # 新增：连接恢复默认请求信号
            deep_motor_page.restore_default_requested.connect(self._handle_restore_default_requested)
            # 新增：连接删除轨迹请求信号
            deep_motor_page.delete_trajectory_requested.connect(self._handle_delete_trajectory_requested)
            
            self.logger.info("GuiDeviceInterfaceHandler: DeepMotor页面信号连接完成")
        else:
            self.logger.warning("GuiDeviceInterfaceHandler: DeepMotor页面未找到，无法连接相关信号")

        # 连接测试按钮信号
        self.gui_manager.window.basicInputInterface.test_button_clicked.connect(self._handle_test_button_click)

        # 连接协调器轨迹执行信号到UI
        self._connect_coordinator_trajectory_signals()

        self.logger.debug("GuiDeviceInterfaceHandler: GUI 信号连接完成。")

    def _connect_coordinator_trajectory_signals(self):
        """连接协调器轨迹执行信号到UI"""
        try:
            # 连接轨迹执行进度信号到UI
            if hasattr(self.parent(), 'trajectory_execution_progress_detailed'):
                self.parent().trajectory_execution_progress_detailed.connect(
                    self.gui_manager.window.deviceInterface._handle_trajectory_execution_progress
                )
                self.logger.info("GuiDeviceInterfaceHandler: 已连接轨迹执行进度信号")
            
            # 连接轨迹执行完成信号到UI
            if hasattr(self.parent(), 'trajectory_execution_finished'):
                self.parent().trajectory_execution_finished.connect(
                    self.gui_manager.window.deviceInterface._handle_trajectory_execution_finished
                )
                self.logger.info("GuiDeviceInterfaceHandler: 已连接轨迹执行完成信号")
            
            # 连接轨迹执行错误信号到UI
            if hasattr(self.parent(), 'trajectory_execution_error'):
                self.parent().trajectory_execution_error.connect(
                    self.gui_manager.window.deviceInterface._handle_trajectory_execution_error
                )
                self.logger.info("GuiDeviceInterfaceHandler: 已连接轨迹执行错误信号")
                
        except Exception as e:
            self.logger.error(f"GuiDeviceInterfaceHandler: 连接协调器轨迹信号失败: {e}")

    # ==================== 信号处理槽函数 ====================
    
    @Slot(str, str)
    def _handle_device_control_request(self, device_id: str, command: str):
        """处理设备控制请求"""
        self.logger.info(f"GuiDeviceInterfaceHandler: 收到设备控制请求 - 设备: {device_id}, 命令: {command}")
        
        # 如果命令是列表格式，转换为函数调用格式
        if command.startswith('[') and command.endswith(']'):
            try:
                args = eval(command)
                if isinstance(args, list):
                    command = f"{device_id}({','.join(map(str, args))})"
            except:
                self.logger.error(f"GuiDeviceInterfaceHandler: 命令格式转换失败: {command}")
                return

        # 转发给设备逻辑管理器
        self.device_logic_manager.send_command_to_device(device_id, command)
        self.coordinator_handler.app_status_message.emit(f"命令已发送至设备逻辑管理器: {device_id} - {command}")
        
    @Slot()
    def _handle_ports_request(self):
        """处理串口列表请求"""
        ports = self.serial_communicator.list_ports()
        self.gui_manager.window.deviceInterface.serial_config.update_ports(ports)
        
    @Slot(str, int)
    def _handle_serial_connect(self, port: str, baud_rate: int):
        """处理串口连接请求"""
        self.logger.info(f"GuiDeviceInterfaceHandler: 收到串口连接请求 - 端口: {port}, 波特率: {baud_rate}")
        try:
            self.serial_communicator.open_port(port, baud_rate)
        except Exception as e:
            error_msg = f"串口连接失败: {str(e)}"
            self.logger.error(f"GuiDeviceInterfaceHandler: {error_msg}")
            self.coordinator_handler.app_status_message.emit(error_msg)
            
    @Slot(str)
    def _handle_serial_disconnect(self, port: str):
        """处理串口断开请求"""
        self.logger.info(f"GuiDeviceInterfaceHandler: 收到串口断开请求 - 端口: {port}")
        self.serial_communicator.close_port(port)
        
    @Slot(str)
    def _handle_sim_data_request(self, device_name: str):
        """处理模拟数据请求"""
        self.logger.info(f"GuiDeviceInterfaceHandler: 收到模拟数据请求，设备: {device_name}")
        if device_name == "DeepMotor":
            self.serial_communicator.sim_read_serial_data()
            
    @Slot(str, str)
    def _handle_request_history_data(self, device_name: str, param_name: str):
        """处理历史数据请求"""
        self.logger.info(f"GuiDeviceInterfaceHandler: 收到历史数据请求，设备: {device_name}, 参数: {param_name}")
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
                    history_data = self.device_logic_manager.get_historical_data(device_name, param_name, options)
                else:
                    self.logger.warning("DeepMotor页面没有_current_trajectory属性")
                    return
            else:
                history_data = self.device_logic_manager.get_historical_data(device_name, param_name, {})
            
            if history_data is not None:
                if hasattr(deep_motor_page, 'update_history_curve'):
                    deep_motor_page.update_history_curve(history_data)
                    
    @Slot(str, int)
    def _handle_start_teaching_request(self, device_name: str, motor_id: int = 1):
        """处理开始示教请求"""
        self.logger.info(f"GuiDeviceInterfaceHandler: 收到开始示教请求，设备: {device_name}, motor_id: {motor_id}")
        
        # 先发送失能命令
        self.device_logic_manager.send_command_to_device(device_name, f"disable_motor({motor_id})")
        self.coordinator_handler.app_status_message.emit(f"电机{motor_id}已失能，开始示教模式")
        
        # 启动示教模式
        self.device_logic_manager.start_teaching(device_name, motor_id)
        self.coordinator_handler.app_status_message.emit(f"已开始示教，设备: {device_name}, motor_id: {motor_id}")
        
    @Slot(str)
    def _handle_stop_teaching_request(self, device_name: str):
        """处理停止示教请求"""
        self.logger.info(f"GuiDeviceInterfaceHandler: 收到停止示教请求，设备: {device_name}")
        
        saved_trajectory_name = self.device_logic_manager.stop_teaching(device_name)
        
        if saved_trajectory_name:
            self.logger.info(f"轨迹 '{saved_trajectory_name}' 已保存")
            self.coordinator_handler.app_status_message.emit(f"轨迹 '{saved_trajectory_name}' 已保存")
            self._handle_trajectory_list_request(device_name, prefer_newest=True)
        else:
            self.logger.error(f"轨迹保存失败")
            self.coordinator_handler.app_status_message.emit(f"轨迹保存失败")
            
        self.coordinator_handler.app_status_message.emit(f"已停止示教，设备: {device_name}")
        
    @Slot(str, str, bool, int)
    def _handle_execute_teaching_request(self, device_name: str, trajectory_name: str, use_planned_trajectory: bool = True, motor_id: int = 1):
        """处理执行示教请求"""
        self.logger.info(f"GuiDeviceInterfaceHandler: 收到对设备 '{device_name}' 的示教执行请求，轨迹: '{trajectory_name}', motor_id: {motor_id}, 使用规划轨迹: {use_planned_trajectory}")
        self.device_logic_manager.execute_trajectory(device_name, trajectory_name, motor_id, use_planned_trajectory)
        
    @Slot(str, str)
    def _handle_trajectory_data_request(self, device_name: str, trajectory_name: str):
        """处理轨迹数据请求"""
        self.logger.info(f"GuiDeviceInterfaceHandler: 收到轨迹数据请求，设备: {device_name}, 轨迹: {trajectory_name}")
        
        deep_motor_page = self.gui_manager.window.deviceInterface.get_deep_motor_page()
        if not deep_motor_page:
            self.logger.warning("GuiDeviceInterfaceHandler: DeepMotor页面未找到")
            return
        
        # 获取当前选择的参数类型
        if hasattr(deep_motor_page, 'current_selected_param'):
            current_param = deep_motor_page.current_selected_param
        else:
            current_param = "trajectory_both"
            
        if not current_param.startswith('trajectory_'):
            current_param = "trajectory_both"
            
        history_data_dict = self.device_logic_manager.get_historical_data(
            device_name, 
            current_param, 
            {"trajectory_name": trajectory_name}
        )
        
        if history_data_dict:
            if hasattr(deep_motor_page, 'update_history_curve'):
                deep_motor_page.update_history_curve(history_data_dict)
                self.coordinator_handler.app_status_message.emit(f"轨迹数据已获取并更新到设备: {device_name}")
        else:
            self.logger.warning(f"GuiDeviceInterfaceHandler: 未获取到轨迹数据")
            self.coordinator_handler.app_status_message.emit(f"轨迹数据获取失败，设备: {device_name}")
            
    @Slot(str)
    def _handle_trajectory_list_request(self, device_name: str, prefer_newest: bool = False):
        """处理轨迹列表请求"""
        self.logger.info(f"GuiDeviceInterfaceHandler: 收到轨迹列表请求，设备: {device_name}, prefer_newest: {prefer_newest}")
        
        trajectory_list = self.device_logic_manager.get_trajectory_list(device_name)
        
        if trajectory_list:
            if not prefer_newest and trajectory_list:
                prefer_newest = True
                
            deep_motor_page = self.gui_manager.window.deviceInterface.get_deep_motor_page()
            if deep_motor_page and hasattr(deep_motor_page, 'update_trajectory_list'):
                deep_motor_page.update_trajectory_list(trajectory_list, prefer_newest)
                self.coordinator_handler.app_status_message.emit(f"轨迹列表已更新，共 {len(trajectory_list)} 条轨迹")
        else:
            self.coordinator_handler.app_status_message.emit("暂无轨迹数据")
            
    @Slot(str, str, float)
    def _handle_replan_requested(self, device_name: str, trajectory_name: str, duration: float):
        """处理轨迹重规划请求"""
        self.logger.info(f"GuiDeviceInterfaceHandler: 收到对轨迹 '{trajectory_name}' 的重规划请求，新时长: {duration}s")
        self.device_logic_manager.replan_trajectory(device_name, trajectory_name, duration)
        self._handle_trajectory_data_request(device_name, trajectory_name)
        
    @Slot(str, str)
    def _handle_restore_default_requested(self, device_name: str, trajectory_name: str):
        """处理恢复默认轨迹请求"""
        self.logger.info(f"GuiDeviceInterfaceHandler: 收到对轨迹 '{trajectory_name}' 的恢复默认请求")
        self.device_logic_manager.replan_with_original_time(device_name, trajectory_name)
        self._handle_trajectory_data_request(device_name, trajectory_name)
        
    @Slot(str, str)
    def _handle_delete_trajectory_requested(self, device_name: str, trajectory_name: str):
        """处理删除轨迹请求"""
        self.logger.info(f"GuiDeviceInterfaceHandler: 收到对轨迹 '{trajectory_name}' 的删除请求")
        success = self.device_logic_manager.delete_trajectory(device_name, trajectory_name)
        
        if success:
            self.coordinator_handler.app_status_message.emit(f"轨迹 '{trajectory_name}' 已删除")
            self._handle_trajectory_list_request(device_name, prefer_newest=True)
        else:
            self.coordinator_handler.app_status_message.emit(f"删除轨迹 '{trajectory_name}' 失败")
            
    @Slot(str)
    def _handle_test_button_click(self, message: str):
        """处理测试按钮点击事件"""
        self.logger.info(f"GuiDeviceInterfaceHandler: 收到测试按钮点击信号 - {message}")
        self.coordinator_handler.app_status_message.emit(f"测试按钮被点击: {message}")
   