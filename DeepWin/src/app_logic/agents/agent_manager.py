from PySide6.QtCore import QObject, Signal
from src.data_management.log_manager import LogManager

class AgentManager(QObject):
    request_memory_data = Signal(str)
    trigger_device_action = Signal(str, str)
    request_cloud_ai = Signal(str)
    send_app_message = Signal(str)

    def __init__(self, log_manager: LogManager, parent=None):
        super().__init__(parent)
        self.logger = log_manager.get_logger(__name__)
        self.coordinator = None  # 初始化为 None，稍后设置
        self.logger.info("AgentManager: 初始化中...")
        self.logger.info("AgentManager: 初始化完成。")
        self._init_agents()

    def set_coordinator(self, coordinator):
        """设置Coordinator实例"""
        self.coordinator = coordinator
        self.logger.info("AgentManager: Coordinator已设置")

    def _init_agents(self):
        # 智能体可以在这里被实例化和管理
        # 例如：self.memory_curator_agent = MemoryCuratorAgent(self.coordinator)
        self.logger.info("AgentManager: 示例智能体已初始化。")

    def cleanup(self):
        self.logger.info("AgentManager: 执行清理工作。")