from PySide6.QtCore import QObject
from src.data_management.log_manager import LogManager

class CloudApiClient(QObject):
    def __init__(self, log_manager: LogManager, parent=None):
        super().__init__(parent)
        self.logger = log_manager.get_logger(__name__)
        self.logger.info("CloudApiClient: 初始化中...")
        self.logger.info("CloudApiClient: 初始化完成。")

    def cleanup(self):
        self.logger.info("CloudApiClient: 执行清理工作。")