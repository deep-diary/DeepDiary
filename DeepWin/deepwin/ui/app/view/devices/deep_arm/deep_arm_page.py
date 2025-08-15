from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import CardWidget

# 导入日志管理
from deepwin.data_management.log_manager import LogManager
from deepwin.data_management.config_manager import ConfigManager
from ..base_device_page import BaseDevicePage

# 导入自定义卡片组件
from .control_card import DeepArmControlCard
from .teaching_card import DeepArmTeachingCard
from .feedback_card import DeepArmFeedbackCard

class DeepArmPage(BaseDevicePage):
    """DeepArm 机械臂控制页面"""
    
    # 设备命令信号
    ui_device_command = Signal(str, str)  # 设备命令信号
    
    # 示教相关信号
    start_teaching_requested = Signal(str)  # 开始示教信号
    stop_teaching_requested = Signal(str)   # 停止示教信号
    execute_teaching_requested = Signal(str, str, bool)  # 执行示教信号 (设备名, 轨迹名, 是否使用规划轨迹)
    
    # 轨迹管理信号
    request_trajectory_data = Signal(str, str)  # 请求轨迹数据信号 (设备名, 轨迹名)
    request_trajectory_list = Signal(str)  # 请求轨迹列表信号
    replan_requested = Signal(str, str, float)  # 重规划信号 (设备名, 轨迹名, 新时长)
    restore_default_requested = Signal(str, str) # 恢复默认信号 (设备名, 轨迹名)
    delete_trajectory_requested = Signal(str, str) # 删除轨迹信号 (设备名, 轨迹名)

    def __init__(self, device_name: str = "DeepArm", log_manager: LogManager = None, 
                 config_manager: ConfigManager = None, parent=None):
        # 1. 先调用父类构造，必须最前面
        super().__init__(device_name, log_manager, config_manager, parent)
        
        # 2. 初始化属性
        self.current_motor_id = 1
        self._current_trajectory = None
        self._is_executing_trajectory = False
        
        # 3. 初始化卡片组件
        self.control_card = None
        self.teaching_card = None
        self.feedback_card = None
        
        # 4. 手动调用页面初始化方法
        self.setup_ui()
        self.setup_signals()
        self.init_device()

    def setup_ui(self):
        """初始化界面布局"""
        if self.logger:
            self.logger.info("开始设置DeepArm页面UI")
            
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # 创建三个主要卡片
        self.control_card = DeepArmControlCard(self.logger, self.config_manager, self)
        self.teaching_card = DeepArmTeachingCard(self.logger, self.config_manager, self)
        self.feedback_card = DeepArmFeedbackCard(self.logger, self.config_manager, self)
        
        # 添加到主布局
        main_layout.addWidget(self.control_card)
        main_layout.addWidget(self.teaching_card)
        main_layout.addWidget(self.feedback_card)
        main_layout.addStretch()
        
        if self.logger:
            self.logger.info("DeepArm页面UI设置完成")

    def setup_signals(self):
        """设置信号连接"""
        # 连接控制卡片的信号
        if self.control_card:
            self.control_card.joint_control_requested.connect(self._handle_joint_control)
            self.control_card.emergency_stop_requested.connect(self._handle_emergency_stop)
            self.control_card.reset_arm_requested.connect(self._handle_reset_arm)
        
        # 连接示教卡片的信号
        if self.teaching_card:
            self.teaching_card.start_teaching_requested.connect(self._handle_start_teaching)
            self.teaching_card.stop_teaching_requested.connect(self._handle_stop_teaching)
            self.teaching_card.execute_teaching_requested.connect(self._handle_execute_teaching)
            self.teaching_card.request_trajectory_data.connect(self._handle_trajectory_data_request)
            self.teaching_card.request_trajectory_list.connect(self._handle_trajectory_list_request)
            self.teaching_card.replan_requested.connect(self._handle_replan_requested)
            self.teaching_card.restore_default_requested.connect(self._handle_restore_default_requested)
            self.teaching_card.delete_trajectory_requested.connect(self._handle_delete_trajectory_requested)

    def init_device(self):
        """初始化设备"""
        if self.logger:
            self.logger.info("DeepArm设备初始化完成")

    # ==================== 信号处理槽函数 ====================
    
    def _handle_joint_control(self, joint_id: int, angle: float):
        """处理关节控制请求"""
        if self.logger:
            self.logger.info(f"收到关节控制请求 - 关节{joint_id}: {angle}°")
        # 发送设备命令
        self.ui_device_command.emit(self.device_name, f"move_joint_angles({joint_id}, {angle})")
    
    def _handle_emergency_stop(self):
        """处理急停请求"""
        if self.logger:
            self.logger.info("收到急停请求")
        self.ui_device_command.emit(self.device_name, "emergency_stop")
    
    def _handle_reset_arm(self):
        """处理复位请求"""
        if self.logger:
            self.logger.info("收到复位请求")
        self.ui_device_command.emit(self.device_name, "reset_arm")
    
    def _handle_start_teaching(self):
        """处理开始示教请求"""
        if self.logger:
            self.logger.info("收到开始示教请求")
        self.start_teaching_requested.emit(self.device_name)
    
    def _handle_stop_teaching(self):
        """处理停止示教请求"""
        if self.logger:
            self.logger.info("收到停止示教请求")
        self.stop_teaching_requested.emit(self.device_name)
    
    def _handle_execute_teaching(self, trajectory_name: str, use_planned: bool):
        """处理执行示教请求"""
        if self.logger:
            self.logger.info(f"收到执行示教请求 - 轨迹: {trajectory_name}, 使用规划: {use_planned}")
        self.execute_teaching_requested.emit(self.device_name, trajectory_name, use_planned)
    
    def _handle_trajectory_data_request(self, trajectory_name: str):
        """处理轨迹数据请求"""
        if self.logger:
            self.logger.info(f"收到轨迹数据请求 - 轨迹: {trajectory_name}")
        self.request_trajectory_data.emit(self.device_name, trajectory_name)
    
    def _handle_trajectory_list_request(self):
        """处理轨迹列表请求"""
        if self.logger:
            self.logger.info("收到轨迹列表请求")
        self.request_trajectory_list.emit(self.device_name)
    
    def _handle_replan_requested(self, trajectory_name: str, duration: float):
        """处理重规划请求"""
        if self.logger:
            self.logger.info(f"收到重规划请求 - 轨迹: {trajectory_name}, 时长: {duration}s")
        self.replan_requested.emit(self.device_name, trajectory_name, duration)
    
    def _handle_restore_default_requested(self, trajectory_name: str):
        """处理恢复默认请求"""
        if self.logger:
            self.logger.info(f"收到恢复默认请求 - 轨迹: {trajectory_name}")
        self.restore_default_requested.emit(self.device_name, trajectory_name)
    
    def _handle_delete_trajectory_requested(self, trajectory_name: str):
        """处理删除轨迹请求"""
        if self.logger:
            self.logger.info(f"收到删除轨迹请求 - 轨迹: {trajectory_name}")
        self.delete_trajectory_requested.emit(self.device_name, trajectory_name) 