from PySide6.QtCore import Slot
from src.app_logic.core_manager.base_handler import BaseHandler

class AiCoordinatorHandler(BaseHandler):
    """
    AI协调器处理器
    负责处理AI协调器相关的信号连接和事件处理
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def _validate_dependencies(self):
        """
        验证必需的依赖项是否已设置
        """
        self.logger.info(f"AiCoordinatorHandler: 验证依赖项开始--------------------------------")
        if not self.logger:
            raise ValueError("缺少必需的依赖项: logger")
        if not self.ai_coordinator:
            raise ValueError("缺少必需的依赖项: ai_coordinator")
        if not self.coordinator_handler:
            raise ValueError("缺少必需的依赖项: coordinator_handler")
        # coordinator_handler.app_status_message是类属性，在实例化时总是存在的，不需要检查
        self.logger.info(f"AiCoordinatorHandler: 验证依赖项结束--------------------------------")
        

    def _connect_signals(self):
        """
        连接AI协调器层相关的信号
        """
        # AI 协调器
        self.logger.debug("AiCoordinatorHandler: 连接AI协调器层信号...")
        self.ai_coordinator.ai_service_response.connect(lambda result: self.coordinator_handler.app_status_message.emit(f"AI 服务响应: {result}"))
        self.ai_coordinator.ai_service_error.connect(lambda error_msg: self.coordinator_handler.app_status_message.emit(f"AI 服务错误: {error_msg}"))  
        self.logger.debug("AiCoordinatorHandler: AI协调器层信号连接完成")
        
 