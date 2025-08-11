from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout
from qfluentwidgets import PrimaryPushButton, FluentIcon as FIF, FlowLayout

class BasicControlWidget(QWidget):
    """基础控制小部件 - 包含急停、复位、使能、失能等按钮"""
    
    # 信号定义
    emergency_stop_requested = Signal()  # 急停信号
    reset_arm_requested = Signal()  # 复位信号
    enable_arm_requested = Signal()  # 使能信号
    disable_arm_requested = Signal()  # 失能信号

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setup_ui()
        self.setup_signals()

    def setup_ui(self):
        """初始化基础控制界面"""
        # 创建按钮容器
        button_container = QWidget()
        button_flow_layout = FlowLayout(button_container, needAni=True)
        button_flow_layout.setContentsMargins(0, 10, 0, 0)
        button_flow_layout.setVerticalSpacing(10)
        button_flow_layout.setHorizontalSpacing(10)
        
        # 创建基础控制按钮
        self.emergency_stop_button = PrimaryPushButton('急停', self)
        self.emergency_stop_button.setIcon(FIF.PLAY)
        self.emergency_stop_button.setStyleSheet("background-color: #d32f2f; color: white;")
        
        self.reset_button = PrimaryPushButton('复位', self)
        self.reset_button.setIcon(FIF.RETURN)
        
        self.enable_button = PrimaryPushButton('使能', self)
        self.enable_button.setIcon(FIF.PLAY)
        
        self.disable_button = PrimaryPushButton('失能', self)
        self.disable_button.setIcon(FIF.PAUSE)
        
        # 添加按钮到布局
        button_flow_layout.addWidget(self.emergency_stop_button)
        button_flow_layout.addWidget(self.reset_button)
        button_flow_layout.addWidget(self.enable_button)
        button_flow_layout.addWidget(self.disable_button)
        
        # 创建主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(button_container)

    def setup_signals(self):
        """设置信号连接"""
        # 连接基础控制按钮信号
        self.emergency_stop_button.clicked.connect(self._on_emergency_stop_clicked)
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.enable_button.clicked.connect(self._on_enable_clicked)
        self.disable_button.clicked.connect(self._on_disable_clicked)

    # ==================== 信号处理槽函数 ====================
    
    def _on_emergency_stop_clicked(self):
        """急停按钮点击处理"""
        self.emergency_stop_requested.emit()
    
    def _on_reset_clicked(self):
        """复位按钮点击处理"""
        self.reset_arm_requested.emit()
    
    def _on_enable_clicked(self):
        """使能按钮点击处理"""
        self.enable_arm_requested.emit()
    
    def _on_disable_clicked(self):
        """失能按钮点击处理"""
        self.disable_arm_requested.emit()

    # ==================== 公共接口方法 ====================
    
    def set_emergency_stop_state(self, is_active: bool):
        """设置急停状态"""
        if is_active:
            self.emergency_stop_button.setStyleSheet("background-color: #d32f2f; color: white;")
            self.emergency_stop_button.setText('急停激活')
        else:
            self.emergency_stop_button.setStyleSheet("")
            self.emergency_stop_button.setText('急停')
    
    def set_enable_state(self, is_enabled: bool):
        """设置使能状态"""
        if is_enabled:
            self.enable_button.setEnabled(False)
            self.disable_button.setEnabled(True)
            self.enable_button.setText('已使能')
        else:
            self.enable_button.setEnabled(True)
            self.disable_button.setEnabled(False)
            self.enable_button.setText('使能')
    
    def set_all_buttons_enabled(self, enabled: bool):
        """设置所有按钮是否可用"""
        self.emergency_stop_button.setEnabled(enabled)
        self.reset_button.setEnabled(enabled)
        self.enable_button.setEnabled(enabled)
        self.disable_button.setEnabled(enabled) 