from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QProgressBar
from qfluentwidgets import CardWidget, PrimaryPushButton, FluentIcon as FIF

from deepwin.data_management.log_manager import LogManager
from deepwin.data_management.config_manager import ConfigManager

class DeepArmFeedbackCard(CardWidget):
    """DeepArm 反馈卡片 - 包含状态显示和反馈信息"""
    
    # 信号定义
    clear_log_requested = Signal()  # 清除日志信号
    export_log_requested = Signal()  # 导出日志信号

    def __init__(self, logger: LogManager = None, config_manager: ConfigManager = None, parent=None):
        super().__init__(parent)
        self.logger = logger
        self.config_manager = config_manager
        
        # 初始化状态变量
        self._current_status = "未连接"
        self._is_connected = False
        self._is_moving = False
        self._error_message = ""
        
        self.setup_ui()
        self.setup_signals()

    def setup_ui(self):
        """初始化反馈卡片界面"""
        if self.logger:
            self.logger.info("开始设置DeepArm反馈卡片UI")
            
        # 设置卡片标题
        self.setObjectName('反馈卡片')
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 添加标题
        title_label = QLabel('设备状态')
        title_label.setObjectName('cardTitle')
        main_layout.addWidget(title_label)
        
        # 创建状态显示区域
        self._create_status_area(main_layout)
        
        # 创建进度显示区域
        self._create_progress_area(main_layout)
        
        # 创建日志显示区域
        self._create_log_area(main_layout)
        
        if self.logger:
            self.logger.info("DeepArm反馈卡片UI设置完成")

    def _create_status_area(self, parent_layout):
        """创建状态显示区域"""
        # 状态显示标题
        status_title = QLabel('连接状态')
        status_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        parent_layout.addWidget(status_title)
        
        # 创建状态布局
        status_layout = QHBoxLayout()
        status_layout.setSpacing(10)
        
        # 连接状态标签
        self.connection_status_label = QLabel('连接状态: 未连接')
        self.connection_status_label.setStyleSheet("color: red; padding: 5px; background-color: #ffebee; border-radius: 3px;")
        
        # 运动状态标签
        self.motion_status_label = QLabel('运动状态: 静止')
        self.motion_status_label.setStyleSheet("color: gray; padding: 5px; background-color: #f5f5f5; border-radius: 3px;")
        
        # 错误状态标签
        self.error_status_label = QLabel('错误状态: 正常')
        self.error_status_label.setStyleSheet("color: green; padding: 5px; background-color: #e8f5e8; border-radius: 3px;")
        
        # 添加到布局
        status_layout.addWidget(self.connection_status_label)
        status_layout.addWidget(self.motion_status_label)
        status_layout.addWidget(self.error_status_label)
        status_layout.addStretch()
        
        parent_layout.addLayout(status_layout)

    def _create_progress_area(self, parent_layout):
        """创建进度显示区域"""
        # 进度显示标题
        progress_title = QLabel('执行进度')
        progress_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        parent_layout.addWidget(progress_title)
        
        # 创建进度布局
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(5)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)  # 默认隐藏
        
        # 进度文本
        self.progress_label = QLabel('准备就绪')
        self.progress_label.setStyleSheet("color: gray; padding: 5px;")
        
        # 添加到布局
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(self.progress_label)
        
        parent_layout.addLayout(progress_layout)

    def _create_log_area(self, parent_layout):
        """创建日志显示区域"""
        # 日志显示标题
        log_title = QLabel('操作日志')
        log_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        parent_layout.addWidget(log_title)
        
        # 创建日志布局
        log_layout = QVBoxLayout()
        log_layout.setSpacing(10)
        
        # 日志文本区域
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setMaximumHeight(150)
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 3px;")
        
        # 日志操作按钮
        log_button_layout = QHBoxLayout()
        log_button_layout.setSpacing(10)
        
        self.clear_log_button = PrimaryPushButton('清除日志', self)
        self.clear_log_button.setIcon(FIF.DELETE)
        
        self.export_log_button = PrimaryPushButton('导出日志', self)
        self.export_log_button.setIcon(FIF.DOWNLOAD)
        
        # 添加按钮到布局
        log_button_layout.addWidget(self.clear_log_button)
        log_button_layout.addWidget(self.export_log_button)
        log_button_layout.addStretch()
        
        # 添加到主日志布局
        log_layout.addWidget(self.log_text_edit)
        log_layout.addLayout(log_button_layout)
        
        parent_layout.addLayout(log_layout)

    def setup_signals(self):
        """设置信号连接"""
        # 连接日志操作按钮信号
        self.clear_log_button.clicked.connect(self._on_clear_log_clicked)
        self.export_log_button.clicked.connect(self._on_export_log_clicked)

    # ==================== 信号处理槽函数 ====================
    
    def _on_clear_log_clicked(self):
        """清除日志按钮点击处理"""
        if self.logger:
            self.logger.info("清除日志按钮被点击")
        self.clear_log_requested.emit()
        self.log_text_edit.clear()
    
    def _on_export_log_clicked(self):
        """导出日志按钮点击处理"""
        if self.logger:
            self.logger.info("导出日志按钮被点击")
        self.export_log_requested.emit()

    # ==================== 公共接口方法 ====================
    
    def update_connection_status(self, is_connected: bool, status_text: str = None):
        """更新连接状态"""
        self._is_connected = is_connected
        
        if status_text is None:
            status_text = "已连接" if is_connected else "未连接"
        
        self.connection_status_label.setText(f'连接状态: {status_text}')
        
        if is_connected:
            self.connection_status_label.setStyleSheet("color: green; padding: 5px; background-color: #e8f5e8; border-radius: 3px;")
        else:
            self.connection_status_label.setStyleSheet("color: red; padding: 5px; background-color: #ffebee; border-radius: 3px;")
        
        if self.logger:
            self.logger.info(f"连接状态更新: {status_text}")
    
    def update_motion_status(self, is_moving: bool, status_text: str = None):
        """更新运动状态"""
        self._is_moving = is_moving
        
        if status_text is None:
            status_text = "运动中" if is_moving else "静止"
        
        self.motion_status_label.setText(f'运动状态: {status_text}')
        
        if is_moving:
            self.motion_status_label.setStyleSheet("color: blue; padding: 5px; background-color: #e3f2fd; border-radius: 3px;")
        else:
            self.motion_status_label.setStyleSheet("color: gray; padding: 5px; background-color: #f5f5f5; border-radius: 3px;")
        
        if self.logger:
            self.logger.info(f"运动状态更新: {status_text}")
    
    def update_error_status(self, has_error: bool, error_message: str = ""):
        """更新错误状态"""
        self._error_message = error_message
        
        if has_error:
            self.error_status_label.setText(f'错误状态: {error_message}')
            self.error_status_label.setStyleSheet("color: red; padding: 5px; background-color: #ffebee; border-radius: 3px;")
        else:
            self.error_status_label.setText('错误状态: 正常')
            self.error_status_label.setStyleSheet("color: green; padding: 5px; background-color: #e8f5e8; border-radius: 3px;")
        
        if self.logger:
            if has_error:
                self.logger.error(f"错误状态更新: {error_message}")
            else:
                self.logger.info("错误状态更新: 正常")
    
    def update_progress(self, progress: int, status_text: str = None):
        """更新执行进度"""
        if progress < 0:
            # 隐藏进度条
            self.progress_bar.setVisible(False)
            self.progress_label.setText('准备就绪')
            return
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(progress)
        
        if status_text:
            self.progress_label.setText(status_text)
        else:
            self.progress_label.setText(f'执行进度: {progress}%')
        
        if self.logger:
            self.logger.info(f"进度更新: {progress}% - {status_text}")
    
    def add_log_message(self, message: str, level: str = "INFO"):
        """添加日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # 根据级别设置颜色
        if level == "ERROR":
            color = "red"
        elif level == "WARNING":
            color = "orange"
        elif level == "SUCCESS":
            color = "green"
        else:
            color = "black"
        
        # 格式化日志消息
        formatted_message = f'<span style="color: gray;">[{timestamp}]</span> <span style="color: {color};">[{level}]</span> {message}'
        
        # 添加到文本区域
        self.log_text_edit.append(formatted_message)
        
        # 滚动到底部
        scrollbar = self.log_text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        if self.logger:
            if level == "ERROR":
                self.logger.error(message)
            elif level == "WARNING":
                self.logger.warning(message)
            else:
                self.logger.info(message)
    
    def clear_log(self):
        """清除日志"""
        self.log_text_edit.clear()
        if self.logger:
            self.logger.info("日志已清除")
    
    def get_log_content(self) -> str:
        """获取日志内容"""
        return self.log_text_edit.toPlainText()
    
    def set_log_content(self, content: str):
        """设置日志内容"""
        self.log_text_edit.setPlainText(content) 