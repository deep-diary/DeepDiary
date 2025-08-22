from .base import InputListener
from .config_manager import ConfigManager

class InputManager:
    def __init__(self):
        self.config = ConfigManager()
        self.listener = InputListener()

    def register_handler(self, name: str, handler):
        """注册事件处理器"""
        self.listener.register_handler(name, handler)

    def set_active_handler(self, name: str):
        """设置活动的处理器"""
        self.listener.set_active_handler(name)

    def start(self):
        """启动输入管理器"""
        self.listener.start()

    def stop(self):
        """停止输入管理器"""
        self.listener.stop()
