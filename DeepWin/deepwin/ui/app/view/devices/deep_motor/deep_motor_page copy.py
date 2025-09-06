"""
DeepMotor 控制页面 - 重构版本
整合所有功能组件，统一信号管理
"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter
from qfluentwidgets import CardWidget

# 导入组件
from .components import (
    UniversalPlotWidget, CommunicationWidget, MotorControlWidget, 
    TeachingControlWidget, HistoryCurveWidget
)

# 导入基础页面和日志管理
from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager
from ..base_device_page import BaseDevicePage


class DeepMotorPage(BaseDevicePage):
    """DeepMotor 控制页面 - 重构版本"""
    
    # 对外统一信号定义
    ui_deepmotor_command = Signal(str, str)  # 设备命令信号
    request_sim_data = Signal(str)  # 请求模拟数据的信号
    request_history_data = Signal(str, str)  # 请求历史数据信号 (设备名, 参数名)
    
    # 示教相关信号
    start_teaching_requested = Signal(str, int)  # 开始示教信号 (设备名, motor_id)
    stop_teaching_requested = Signal(str)   # 停止示教信号
    execute_teaching_requested = Signal(str, str, bool, int)  # 执行示教信号 (设备名, 轨迹名, 是否使用规划轨迹, motor_id)
    
    # 轨迹可视化相关信号
    request_trajectory_data = Signal(str, str)  # 请求轨迹数据信号 (设备名, 轨迹名)
    request_trajectory_list = Signal(str)  # 请求轨迹列表信号
    replan_requested = Signal(str, str, float)  # 重规划信号 (设备名, 轨迹名, 新时长)
    restore_default_requested = Signal(str, str) # 恢复默认信号 (设备名, 轨迹名)
    delete_trajectory_requested = Signal(str, str) # 删除轨迹信号 (设备名, 轨迹名)
    
    # 通信相关信号
    communication_data_sent = Signal(str, bytes, str)  # 通信数据发送信号 (协议类型, 数据, 描述)
    communication_data_received = Signal(str, bytes, str)  # 通信数据接收信号 (协议类型, 数据, 描述)
    can_data_sent = Signal(int, bytes, str)  # CAN数据发送信号 (CAN ID, 数据, 描述)
    can_data_received = Signal(int, bytes, str)  # CAN数据接收信号 (CAN ID, 数据, 描述)

    def __init__(self, device_name: str = "DeepMotor", log_manager: LogManager = None, 
                 config_manager: ConfigManager = None, parent=None):
        # 1. 先调用父类构造，必须最前面
        super().__init__(device_name, log_manager, config_manager, parent)
        
        # 2. 初始化组件
        self._init_components()
        
        # 2.5. 执行状态管理
        self._is_executing_trajectory = False
        
        # 3. 设置UI布局
        self.setup_ui()
        
        # 4. 连接信号
        self.setup_signals()
        
        # 5. 初始化设备
        self.init_device()
        
    def _init_components(self):
        """初始化所有组件"""
        # 创建各个功能组件
        self.motor_control_widget = MotorControlWidget("电机控制", self.logger, self)
        self.teaching_control_widget = TeachingControlWidget("示教控制", self.logger, self)
        self.communication_widget = CommunicationWidget("通信监控", self.logger, self.config_manager, self)
        
        # 临时屏蔽历史曲线组件以测试性能
        # self.history_curve_widget = HistoryCurveWidget("历史曲线", self.logger, self)
        self.history_curve_widget = None  # 屏蔽曲线组件
        
        if self.logger:
            self.logger.info("DeepMotor页面组件初始化完成（曲线组件已屏蔽）")
            
    def setup_ui(self):
        """设置UI布局"""
        if self.logger:
            self.logger.info("开始设置DeepMotor页面UI布局")
            
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)
        
        # 创建主分割器（垂直分割）
        main_splitter = QSplitter(Qt.Vertical)
        
        # 上部：串口连接 + 通信监控
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # 串口连接组件（从BaseDevicePage继承）
        if hasattr(self, 'serial_config'):
            top_layout.addWidget(self.serial_config)
        
        # 通信监控组件
        top_layout.addWidget(self.communication_widget)
        top_layout.setStretch(0, 1)  # 串口连接占1份
        top_layout.setStretch(1, 2)  # 通信监控占2份
        
        # 中部：电机控制 + 示教控制（水平分布）
        middle_widget = QWidget()
        middle_layout = QHBoxLayout(middle_widget)
        middle_layout.setContentsMargins(0, 0, 0, 0)
        
        middle_layout.addWidget(self.motor_control_widget)
        middle_layout.addWidget(self.teaching_control_widget)
        middle_layout.setStretch(0, 1)  # 电机控制占1份
        middle_layout.setStretch(1, 1)  # 示教控制占1份
        
        # 下部：历史曲线（已屏蔽）
        main_splitter.addWidget(top_widget)
        main_splitter.addWidget(middle_widget)
        # main_splitter.addWidget(self.history_curve_widget)  # 屏蔽曲线组件
        
        main_splitter.setSizes([400, 400])  # 设置初始大小比例：上部400，中部400（移除下部）
        
        main_layout.addWidget(main_splitter)
        
        if self.logger:
            self.logger.info("DeepMotor页面UI布局设置完成")
            
    def setup_signals(self):
        """设置信号连接"""
        if self.logger:
            self.logger.info("开始设置DeepMotor页面信号连接")
            
        # 电机控制组件信号连接
        self.motor_control_widget.motor_id_changed.connect(self._on_motor_id_changed)
        self.motor_control_widget.command_requested.connect(self._on_motor_command_requested)
        self.motor_control_widget.sim_data_requested.connect(self._on_sim_data_requested)
        
        # 示教控制组件信号连接
        self.teaching_control_widget.start_teaching_requested.connect(self._on_start_teaching_requested)
        self.teaching_control_widget.stop_teaching_requested.connect(self._on_stop_teaching_requested)
        self.teaching_control_widget.execute_teaching_requested.connect(self._on_execute_teaching_requested)
        self.teaching_control_widget.delete_trajectory_requested.connect(self._on_delete_trajectory_requested)
        self.teaching_control_widget.trajectory_selected.connect(self._on_trajectory_selected)
        self.teaching_control_widget.duration_changed.connect(self._on_duration_changed)
        self.teaching_control_widget.switch_to_execution_view.connect(self._on_switch_to_execution_view)
        self.teaching_control_widget.switch_to_teaching_view.connect(self._on_switch_to_teaching_view)
        
        # 通信组件信号连接
        self.communication_widget.protocol_changed.connect(self._on_protocol_changed)
        self.communication_widget.clear_requested.connect(self._on_communication_clear_requested)
        
        # 历史曲线组件信号连接（已屏蔽）
        # self.history_curve_widget.param_changed.connect(self._on_history_param_changed)
        # self.history_curve_widget.refresh_requested.connect(self._on_history_refresh_requested)
        
        if self.logger:
            self.logger.info("DeepMotor页面信号连接设置完成")
            
    def init_device(self):
        """初始化设备"""
        if self.logger:
            self.logger.info("初始化DeepMotor设备")
            
        # 初始化轨迹列表
        self.init_trajectory_list()
        
    def init_trajectory_list(self):
        """初始化轨迹列表"""
        if self.logger:
            self.logger.info("DeepMotor页面: 准备发射轨迹列表请求信号")
        QTimer.singleShot(100, lambda: self._emit_trajectory_list_request())
        
    def _emit_trajectory_list_request(self):
        """发射轨迹列表请求信号"""
        if self.logger:
            self.logger.info(f"DeepMotor页面: 发射 request_trajectory_list 信号，设备名: {self.device_name}")
        self.request_trajectory_list.emit(self.device_name)
        
    # ==================== 信号处理方法 ====================
    
    def _on_motor_id_changed(self, motor_id: int):
        """电机ID改变处理"""
        self.teaching_control_widget.set_motor_id(motor_id)
        
    def _on_motor_command_requested(self, command: str, params: list):
        """电机命令请求处理"""
        if self.logger:
            self.logger.info(f"电机命令请求: {command}, 参数: {params}")
        
        # 发送命令 - 实际的串口数据会通过HardwareCommunicationHandler显示
        self.send_command(command, params)
        
    def _on_sim_data_requested(self):
        """模拟数据请求处理"""
        if self.logger:
            self.logger.info("模拟数据请求")
        self.request_sim_data.emit(self.device_name)
        
    def _on_start_teaching_requested(self, motor_id: int):
        """开始示教请求处理"""
        if self.logger:
            self.logger.info(f"开始示教请求，电机ID: {motor_id}")
        self.start_teaching_requested.emit(self.device_name, motor_id)
        
    def _on_stop_teaching_requested(self):
        """停止示教请求处理"""
        if self.logger:
            self.logger.info("停止示教请求")
        self.stop_teaching_requested.emit(self.device_name)
        
    def _on_execute_teaching_requested(self, trajectory_name: str, use_planned: bool, motor_id: int):
        """执行示教请求处理"""
        if self.logger:
            self.logger.info(f"执行示教请求，轨迹: {trajectory_name}, 使用规划: {use_planned}, 电机ID: {motor_id}")
        self.execute_teaching_requested.emit(self.device_name, trajectory_name, use_planned, motor_id)
        
    def _on_delete_trajectory_requested(self, trajectory_name: str):
        """删除轨迹请求处理"""
        if self.logger:
            self.logger.info(f"删除轨迹请求，轨迹: {trajectory_name}")
        self.delete_trajectory_requested.emit(self.device_name, trajectory_name)
        
    def _on_trajectory_selected(self, trajectory_name: str):
        """轨迹选择处理"""
        if self.logger:
            self.logger.info(f"轨迹选择: {trajectory_name}")
        # 自动切换到轨迹视图（已屏蔽）
        # self.history_curve_widget.set_current_param('trajectory_both')
        # 请求轨迹数据
        self.request_trajectory_data.emit(self.device_name, trajectory_name)
        
    def _on_duration_changed(self, duration: float):
        """执行时长改变处理"""
        if self.logger:
            self.logger.info(f"执行时长改变: {duration}秒")
        # 启用刷新按钮（已屏蔽）
        # self.history_curve_widget.enable_refresh_button(True)
        
    def _on_switch_to_execution_view(self):
        """切换到执行轨迹视图处理"""
        if self.logger:
            self.logger.info("切换到执行轨迹视图")
        # 切换到执行轨迹视图（已屏蔽）
        # self.history_curve_widget.set_current_param('trajectory_executed')
        # 设置执行状态
        self._is_executing_trajectory = True
        # 清空画布并设置执行监控界面（已屏蔽）
        # self.history_curve_widget.clear_plot()
        # self.history_curve_widget.set_execution_mode(True)
        
    def _on_switch_to_teaching_view(self):
        """切换到示教轨迹视图处理"""
        if self.logger:
            self.logger.info("切换到示教轨迹视图")
        # 切换到示教轨迹视图（已屏蔽）
        # self.history_curve_widget.set_current_param('trajectory_teaching')
        # 清空画布，确保没有残留的图形（已屏蔽）
        # self.history_curve_widget.clear_plot()
        
    def update_teaching_trajectory(self, times: list, positions: list):
        """
        更新示教轨迹实时显示
        :param times: 时间列表
        :param positions: 位置列表
        """
        if self.logger:
            self.logger.debug(f"DeepMotor页面: 收到示教轨迹更新，点数: {len(times) if times else 0}")
        # 屏蔽曲线更新（已屏蔽）
        # self.history_curve_widget.update_teaching_trajectory(times, positions)
        
    def update_trajectory_execution_progress(self, device_id: str, progress_data: dict):
        """
        更新轨迹执行进度显示
        :param device_id: 设备ID
        :param progress_data: 包含执行进度信息的字典
        """
        if self.logger:
            self.logger.debug(f"DeepMotor页面: 收到轨迹执行进度数据，设备: {device_id}")
        # 屏蔽曲线更新（已屏蔽）
        # self.history_curve_widget.update_execution_trajectory(progress_data)
        
    def on_trajectory_execution_finished(self):
        """轨迹执行完成处理"""
        if self.logger:
            self.logger.info("DeepMotor页面: 收到轨迹执行完成信号")
        self._is_executing_trajectory = False
        # 屏蔽曲线更新（已屏蔽）
        # self.history_curve_widget.set_execution_mode(False)
        
    def _on_protocol_changed(self, protocol: str):
        """通信协议改变处理"""
        if self.logger:
            self.logger.info(f"通信协议改变: {protocol}")
            
    def _on_communication_clear_requested(self):
        """通信清空请求处理"""
        if self.logger:
            self.logger.info("通信显示清空请求")
            
    def _on_history_param_changed(self, param_name: str):
        """历史参数改变处理"""
        if self.logger:
            self.logger.info(f"历史参数改变: {param_name}")
            
        # 屏蔽历史曲线相关处理（已屏蔽）
        # if param_name.startswith('trajectory_'):
        #     # 轨迹数据不需要定时请求
        #     self.history_curve_widget.stop_history_requests()
        # else:
        #     # 普通历史数据需要定时请求
        #     self.history_curve_widget.start_history_requests()
        #     # 立即请求一次数据
        #     self.request_history_data.emit(self.device_name, param_name)
            
    def _on_history_refresh_requested(self):
        """历史刷新请求处理"""
        # 屏蔽历史曲线相关处理（已屏蔽）
        # current_param = self.history_curve_widget.get_current_param()
        if self.logger:
            self.logger.info(f"历史刷新请求（已屏蔽）")
            
        # if current_param.startswith('trajectory_'):
        #     # 轨迹数据重规划
        #     current_trajectory = self.teaching_control_widget.get_current_trajectory()
        #     if current_trajectory:
        #         duration = self.teaching_control_widget.get_duration()
        #         self.replan_requested.emit(self.device_name, current_trajectory, duration)
        # else:
        #     # 普通历史数据刷新
        #     self.request_history_data.emit(self.device_name, current_param)
            
    # ==================== 对外接口方法 ====================
    
    def update_trajectory_list(self, trajectory_names: list, prefer_newest: bool = False):
        """更新轨迹列表"""
        self.teaching_control_widget.update_trajectory_list(trajectory_names, prefer_newest)
        
    def update_motor_status(self, status_data: dict):
        """更新电机状态"""
        self.motor_control_widget.update_motor_status(status_data)
        
    def update_motor_data(self, data: dict):
        """更新电机数据（兼容旧接口）"""
        self.update_motor_status(data)
        
    def update_history_curve(self, history_data_dict: dict):
        """更新历史曲线（已屏蔽）"""
        # self.history_curve_widget.update_history_data(history_data_dict)
        pass
        
    def update_trajectory_curve(self, trajectory_data):
        """更新轨迹曲线（已屏蔽）"""
        # self.history_curve_widget.update_trajectory_data(trajectory_data)
        pass
        
    def update_trajectory_execution_progress(self, device_id: str, progress_data: dict):
        """更新轨迹执行进度"""
        # 屏蔽曲线更新（已屏蔽）
        # self.history_curve_widget.update_execution_progress(progress_data)
        
        # 更新示教控制组件的进度显示
        current_point = progress_data.get('current_point', 0)
        total_points = progress_data.get('total_points', 1)
        progress_percent = int((current_point / total_points) * 100) if total_points > 0 else 0
        self.teaching_control_widget.update_execution_progress(progress_percent)
        
    def update_teaching_trajectory(self, times: list, positions: list):
        """更新示教轨迹（已屏蔽）"""
        # self.history_curve_widget.update_teaching_trajectory(times, positions)
        pass
        
    def on_trajectory_execution_finished(self):
        """轨迹执行完成处理"""
        if self.logger:
            self.logger.info("DeepMotor页面: 收到轨迹执行完成信号")
        self._is_executing_trajectory = False
        # 屏蔽曲线更新（已屏蔽）
        # self.history_curve_widget.set_execution_mode(False)
        self.teaching_control_widget.on_trajectory_execution_finished()
        
    def on_trajectory_execution_error(self, error_message: str):
        """轨迹执行错误处理"""
        self.teaching_control_widget.on_trajectory_execution_error(error_message)
        
    def add_communication_data(self, direction: str, protocol: str, data: bytes, description: str = "", can_id: int = None):
        """
        添加通信数据
        :param direction: 方向 ('send' 或 'receive')
        :param protocol: 协议类型 ('serial' 或 'can')
        :param data: 数据字节
        :param description: 描述信息
        :param can_id: CAN ID（仅CAN协议需要）
        """
        if self.logger:
            self.logger.info(f"DeepMotorPage: add_communication_data被调用 - direction={direction}, protocol={protocol}, can_id={can_id}, description={description}")
        
        if protocol == "serial":
            self.communication_widget.add_serial_data(direction, data, description)
        elif protocol == "can" and can_id is not None:
            self.communication_widget.add_can_data(direction, can_id, data, description)
        else:
            if self.logger:
                self.logger.warning(f"DeepMotorPage: 无法添加通信数据 - protocol={protocol}, can_id={can_id}")
            
    def get_current_motor_id(self) -> int:
        """获取当前电机ID"""
        return self.motor_control_widget.get_current_motor_id()
        
    def get_current_trajectory(self) -> str:
        """获取当前轨迹"""
        return self.teaching_control_widget.get_current_trajectory()
        
    def get_current_protocol(self) -> str:
        """获取当前通信协议"""
        return self.communication_widget.get_current_protocol()
        
    @property
    def current_selected_param(self) -> str:
        """获取当前选中的参数（兼容旧接口，已屏蔽）"""
        # return self.history_curve_widget.get_current_param()
        return 'position'  # 返回默认值
        
    def reset_to_defaults(self):
        """重置为默认状态"""
        self.motor_control_widget.reset_to_defaults()
        self.teaching_control_widget.reset_to_defaults()
        self.communication_widget.clear_all_data()
        # 屏蔽曲线组件重置（已屏蔽）
        # self.history_curve_widget.reset_to_defaults()
        
        if self.logger:
            self.logger.info("DeepMotor页面已重置为默认状态（曲线组件已屏蔽）")
            
