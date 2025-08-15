from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from qfluentwidgets import PrimaryPushButton, FluentIcon as FIF

class TeachingControlWidget(QWidget):
    """示教控制小部件 - 包含开始示教、结束示教、执行示教等按钮"""
    
    # 信号定义
    start_teaching_requested = Signal()  # 开始示教信号
    stop_teaching_requested = Signal()   # 停止示教信号
    execute_teaching_requested = Signal()  # 执行示教信号

    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._is_teaching = False
        
        self.setup_ui()
        self.setup_signals()

    def setup_ui(self):
        """初始化示教控制界面"""
        # 创建示教控制布局
        teaching_layout = QHBoxLayout(self)
        teaching_layout.setSpacing(10)
        
        # 示教控制按钮
        self.start_teaching_button = PrimaryPushButton('开始示教', self)
        self.start_teaching_button.setIcon(FIF.EDIT)
        
        self.stop_teaching_button = PrimaryPushButton('结束示教', self)
        self.stop_teaching_button.setIcon(FIF.POWER)
        self.stop_teaching_button.setEnabled(False)
        
        self.execute_teaching_button = PrimaryPushButton('执行示教', self)
        self.execute_teaching_button.setIcon(FIF.PLAY)
        
        # 添加按钮到布局
        teaching_layout.addWidget(self.start_teaching_button)
        teaching_layout.addWidget(self.stop_teaching_button)
        teaching_layout.addWidget(self.execute_teaching_button)
        teaching_layout.addStretch()

    def setup_signals(self):
        """设置信号连接"""
        # 连接示教控制按钮信号
        self.start_teaching_button.clicked.connect(self._on_start_teaching_clicked)
        self.stop_teaching_button.clicked.connect(self._on_stop_teaching_clicked)
        self.execute_teaching_button.clicked.connect(self._on_execute_teaching_clicked)

    # ==================== 信号处理槽函数 ====================
    
    def _on_start_teaching_clicked(self):
        """开始示教按钮点击处理"""
        self._is_teaching = True
        self.update_teaching_buttons_state()
        self.start_teaching_requested.emit()
    
    def _on_stop_teaching_clicked(self):
        """结束示教按钮点击处理"""
        self._is_teaching = False
        self.update_teaching_buttons_state()
        self.stop_teaching_requested.emit()
    
    def _on_execute_teaching_clicked(self):
        """执行示教按钮点击处理"""
        self.execute_teaching_requested.emit()

    # ==================== 公共接口方法 ====================
    
    def update_teaching_buttons_state(self):
        """更新示教按钮状态"""
        if self._is_teaching:
            self.start_teaching_button.setEnabled(False)
            self.stop_teaching_button.setEnabled(True)
            self.execute_teaching_button.setEnabled(False)
        else:
            self.start_teaching_button.setEnabled(True)
            self.stop_teaching_button.setEnabled(False)
            self.execute_teaching_button.setEnabled(True)
    
    def set_execution_state(self, is_executing: bool):
        """设置执行状态"""
        if is_executing:
            self.execute_teaching_button.setEnabled(False)
            self.start_teaching_button.setEnabled(False)
            self.stop_teaching_button.setEnabled(False)
        else:
            self.update_teaching_buttons_state()
    
    def reset_teaching_state(self):
        """重置示教状态"""
        self._is_teaching = False
        self.update_teaching_buttons_state() 