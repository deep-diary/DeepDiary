from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel
from qfluentwidgets import CardWidget

from deepwin.data_management.log_manager import LogManager
from deepwin.data_management.config_manager import ConfigManager

# 导入自定义小部件
from .joint_control_widget import JointControlWidget
from .basic_control_widget import BasicControlWidget

class DeepArmControlCard(CardWidget):
    """DeepArm 控制卡片 - 包含关节控制和基础控制功能"""
    
    # 信号定义
    joint_control_requested = Signal(int, float)  # 关节控制信号 (关节ID, 角度)
    emergency_stop_requested = Signal()  # 急停信号
    reset_arm_requested = Signal()  # 复位信号

    def __init__(self, logger: LogManager = None, config_manager: ConfigManager = None, parent=None):
        super().__init__(parent)
        self.logger = logger
        self.config_manager = config_manager
        
        # 初始化小部件
        self.joint_control_widget = None
        self.basic_control_widget = None
        
        self.setup_ui()
        self.setup_signals()

    def setup_ui(self):
        """初始化控制卡片界面"""
        if self.logger:
            self.logger.info("开始设置DeepArm控制卡片UI")
            
        # 设置卡片标题
        self.setObjectName('控制卡片')
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 添加标题
        title_label = QLabel('机械臂控制')
        title_label.setObjectName('cardTitle')
        main_layout.addWidget(title_label)
        
        # 创建关节控制区域
        joint_title = QLabel('关节角度控制')
        joint_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        main_layout.addWidget(joint_title)
        
        self.joint_control_widget = JointControlWidget(self)
        main_layout.addWidget(self.joint_control_widget)
        
        # 创建基础控制区域
        basic_title = QLabel('基础控制')
        basic_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        main_layout.addWidget(basic_title)
        
        self.basic_control_widget = BasicControlWidget(self)
        main_layout.addWidget(self.basic_control_widget)
        
        if self.logger:
            self.logger.info("DeepArm控制卡片UI设置完成")



    def setup_signals(self):
        """设置信号连接"""
        # 连接关节控制信号
        if self.joint_control_widget:
            self.joint_control_widget.joint_control_requested.connect(self.joint_control_requested.emit)
        
        # 连接基础控制信号
        if self.basic_control_widget:
            self.basic_control_widget.emergency_stop_requested.connect(self.emergency_stop_requested.emit)
            self.basic_control_widget.reset_arm_requested.connect(self.reset_arm_requested.emit)

    # ==================== 信号处理槽函数 ====================
    # 信号处理已移至各个小部件中

    # ==================== 公共接口方法 ====================
    
    def update_joint_angle(self, joint_id: int, angle: float):
        """更新关节角度显示"""
        if self.joint_control_widget:
            self.joint_control_widget.update_joint_angle(joint_id, angle)
    
    def get_joint_angle(self, joint_id: int) -> float:
        """获取关节角度值"""
        if self.joint_control_widget:
            return self.joint_control_widget.get_joint_angle(joint_id)
        return 0.0
    
    def set_emergency_stop_state(self, is_active: bool):
        """设置急停状态"""
        if self.basic_control_widget:
            self.basic_control_widget.set_emergency_stop_state(is_active) 