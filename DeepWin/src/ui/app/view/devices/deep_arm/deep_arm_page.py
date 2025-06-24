from src.ui.app.view.devices.base_device_page import BaseDevicePage
from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager
from PySide6.QtWidgets import QVBoxLayout, QLabel
from PySide6.QtCore import Signal

class DeepArmPage(BaseDevicePage):
    """DeepArm 控制页面"""
    ui_device_command = Signal(str, str)  # 设备命令信号

    def __init__(self, device_name: str = "DeepArm", log_manager: LogManager = None, config_manager: ConfigManager = None, parent=None):
        # 可在此初始化自定义属性
        super().__init__(device_name, log_manager, config_manager, parent)
        self.setup_ui()
        self.setup_signals()
        self.init_device()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        label = QLabel("DeepArm 设备页面（模板）")
        layout.addWidget(label)

    def setup_signals(self):
        pass

    def init_device(self):
        pass 