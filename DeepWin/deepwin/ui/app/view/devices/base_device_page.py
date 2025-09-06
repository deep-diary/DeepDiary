# coding: utf-8
"""
设备页面基类
定义所有设备页面的通用接口和基础功能
"""
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from qfluentwidgets import CardWidget, PrimaryPushButton, ComboBox

from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager


class BaseDevicePage(QWidget):
    """设备页面基类"""
    
    # 通用信号定义
    ui_device_command = Signal(str, str)  # 设备命令信号 (设备名, 命令)
    request_history_data = Signal(str, str)  # 请求历史数据信号 (设备名, 参数名)
    
    def __init__(self, device_name: str, log_manager: LogManager = None, 
                 config_manager: ConfigManager = None, parent=None):
        super().__init__(parent=parent)
        self.device_name = device_name
        self.log_manager = log_manager
        self.logger = self.log_manager.get_logger(__name__) if self.log_manager else None
        self.config_manager = config_manager
        self.is_connected = False
        self.is_running = False
        if self.logger:
            self.logger.debug(f"{self.device_name}页面初始化开始")
        # 不自动调用setup_ui、setup_signals、init_device，由子类手动调用
        if self.logger:
            self.logger.debug(f"{self.device_name}页面初始化完成")
    
    def _check_required_methods(self):
        """检查子类是否实现了必要的方法"""
        required_methods = ['setup_ui', 'setup_signals', 'init_device']
        missing_methods = []
        
        for method_name in required_methods:
            method = getattr(self.__class__, method_name, None)
            if method is None or method.__qualname__.startswith('BaseDevicePage'):
                missing_methods.append(method_name)
        
        if missing_methods:
            raise NotImplementedError(
                f"设备页面类 {self.__class__.__name__} 必须实现以下方法: {', '.join(missing_methods)}"
            )
    
    def setup_ui(self):
        """设置UI界面 - 子类必须实现"""
        raise NotImplementedError("子类必须实现 setup_ui 方法")
    
    def setup_signals(self):
        """设置信号连接 - 子类必须实现"""
        raise NotImplementedError("子类必须实现 setup_signals 方法")
    
    def init_device(self):
        """初始化设备 - 子类必须实现"""
        raise NotImplementedError("子类必须实现 init_device 方法")
    
    def send_command(self, command: str, args: list = None):
        """发送设备命令的通用方法"""
        if args is None:
            args = []
        command_str = command + "(" + ",".join(str(arg) for arg in args) + ")"
        if self.logger:
            self.logger.info(f"{self.device_name}: 发送命令: {command_str}")
        self.ui_device_command.emit(self.device_name, command_str)
    
    def update_connection_status(self, is_connected: bool):
        """更新连接状态"""
        self.is_connected = is_connected
        if self.logger:
            status = "已连接" if is_connected else "未连接"
            self.logger.info(f"{self.device_name}连接状态: {status}")
    
    def update_running_status(self, is_running: bool):
        """更新运行状态"""
        self.is_running = is_running
        if self.logger:
            status = "运行中" if is_running else "已停止"
            self.logger.info(f"{self.device_name}运行状态: {status}")
    
    def show_status_message(self, message: str, message_type: str = "info"):
        """显示状态消息"""
        if self.logger:
            if message_type == "error":
                self.logger.error(f"{self.device_name}: {message}")
            elif message_type == "warning":
                self.logger.warning(f"{self.device_name}: {message}")
            else:
                self.logger.info(f"{self.device_name}: {message}")
    
    def create_control_card(self, title: str) -> CardWidget:
        """创建控制卡片的通用方法"""
        card = CardWidget(self)
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setObjectName('cardTitle')
        layout.addWidget(title_label)
        
        return card, layout
    
    def create_status_card(self, title: str) -> CardWidget:
        """创建状态显示卡片的通用方法"""
        card = CardWidget(self)
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setObjectName('cardTitle')
        layout.addWidget(title_label)
        
        return card, layout


class SerialConfigWidget(CardWidget):
    """串口配置组件"""
    serial_connect_requested = Signal(str, int)  # 串口名, 波特率
    serial_disconnect_requested = Signal(str)  # 串口名
    request_ports = Signal()  # 请求获取可用端口列表的信号

    def __init__(self, log_manager: LogManager = None, config_manager: ConfigManager = None, parent=None):
        super().__init__(parent=parent)
        self.log_manager = log_manager
        self.logger = self.log_manager.get_logger(__name__) if self.log_manager else None
        self.config_manager = config_manager
        
        self.setup_ui()
        # 使用QTimer延迟发送刷新信号，确保信号连接已经建立
        QTimer.singleShot(100, self.request_ports.emit)
        self.is_connected = False  # 添加连接状态标志
        self.current_port = ""  # 当前连接的串口
        
        if self.logger:
            self.logger.info("串口配置组件初始化完成")

    def setup_ui(self):
        self.v_layout = QVBoxLayout(self)
        self.h_layout = QHBoxLayout()

        title_label = QLabel('串口连接')
        title_label.setObjectName('cardTitle')
        self.v_layout.addWidget(title_label)
        self.v_layout.addLayout(self.h_layout)

        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.h_layout.setSpacing(10)

        # 串口选择
        port_layout = QHBoxLayout()
        port_label = QLabel('串口:')
        self.port_combo = ComboBox()
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_combo)
        port_layout.addStretch()

        # 波特率选择
        baud_layout = QHBoxLayout()
        baud_label = QLabel('波特率:')
        self.baud_combo = ComboBox()
        self.baud_combo.addItems(['9600', '115200', '230400', '460800', '921600', '1500000'])
        self.baud_combo.setCurrentText('921600')
        baud_layout.addWidget(baud_label)
        baud_layout.addWidget(self.baud_combo)
        baud_layout.addStretch()

        # 连接按钮
        self.connect_button = PrimaryPushButton('连接')
        self.connect_button.setStyleSheet("""
            PrimaryPushButton {
                background-color: #0078d4;
                color: white;
            }
            PrimaryPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        self.h_layout.addLayout(port_layout)
        self.h_layout.addLayout(baud_layout)
        self.h_layout.addWidget(self.connect_button)
        self.h_layout.addStretch()

        # 连接信号
        self.connect_button.clicked.connect(self.toggle_connection)

    def update_ports(self, ports: list):
        """更新串口列表"""
        current_port = self.port_combo.currentText()
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        # 尝试恢复之前选择的端口
        index = self.port_combo.findText(current_port)
        if index >= 0:
            self.port_combo.setCurrentIndex(index)
        
        if self.logger:
            self.logger.info(f"串口列表更新完成，可用端口: {ports}")

    def toggle_connection(self):
        """切换连接状态"""
        if self.is_connected:
            # 如果已连接，发送断开请求
            if self.logger:
                self.logger.info(f"请求断开串口连接: {self.current_port}")
            self.serial_disconnect_requested.emit(self.current_port)
        else:
            # 如果未连接，发送连接请求
            port = self.port_combo.currentText()
            baud = int(self.baud_combo.currentText())
            self.current_port = port  # 保存当前连接的串口
            if self.logger:
                self.logger.info(f"请求连接串口: {port}, 波特率: {baud}")
            self.serial_connect_requested.emit(port, baud)

    def update_connection_status(self, is_connected: bool):
        """更新连接状态UI"""
        self.is_connected = is_connected
        if is_connected:
            self.connect_button.setText('关闭')
            self.connect_button.setStyleSheet("""
                PrimaryPushButton {
                    background-color: #d83b01;
                    color: white;
                }
                PrimaryPushButton:disabled {
                    background-color: #cccccc;
                }
            """)
            # 禁用串口和波特率选择
            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)
            if self.logger:
                self.logger.info(f"串口连接成功: {self.current_port}")
        else:
            self.connect_button.setText('连接')
            self.connect_button.setStyleSheet("""
                PrimaryPushButton {
                    background-color: #0078d4;
                    color: white;
                }
                PrimaryPushButton:disabled {
                    background-color: #cccccc;
                }
            """)
            # 启用串口和波特率选择
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)
            self.current_port = ""  # 清除当前连接的串口
            if self.logger:
                self.logger.info("串口连接已断开") 