from PySide6.QtCore import Slot
from deepwin.app_logic.core_manager.base_handler import BaseHandler

class AgentsHandler(BaseHandler):
    """
    Agents处理器
    负责处理Agents相关的信号连接和事件处理
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def _validate_dependencies(self):
        """
        验证必需的依赖项是否已设置
        """
        # 检查基础依赖项
        self.logger.info(f"AgentsHandler: 验证依赖项开始--------------------------------")
        if not self.logger:
            raise ValueError("缺少必需的依赖项: logger")
        if not self.agent_manager:
            raise ValueError("缺少必需的依赖项: agent_manager")
        if not self.device_logic_manager:
            raise ValueError("缺少必需的依赖项: device_logic_manager")
        if not self.ai_coordinator:
            raise ValueError("缺少必需的依赖项: ai_coordinator")
        if not self.local_database_manager:
            raise ValueError("缺少必需的依赖项: local_database_manager")
        if not self.coordinator_handler:
            raise ValueError("缺少必需的依赖项: coordinator_handler")
        # coordinator_handler.app_status_message是类属性，在实例化时总是存在的，不需要检查
        self.logger.info(f"AgentsHandler: 验证依赖项结束--------------------------------")

    def _connect_signals(self):
        """
        连接Agents层相关的信号
        """
        self.logger.debug("AgentsHandler: 连接Agents层信号...")

        # 智能体管理器请求数据
        self.agent_manager.request_memory_data.connect(self.local_database_manager.get_memories)
        self.agent_manager.trigger_device_action.connect(self.device_logic_manager.send_command_to_device)
        self.agent_manager.request_cloud_ai.connect(self.ai_coordinator.request_cloud_ai_service)
        self.agent_manager.send_app_message.connect(self._on_agent_app_message)

        self.logger.info(f"AgentsHandler: 连接Agents层信号: {self.coordinator_handler.app_status_message}")

        # 智能体管理器
        self.agent_manager.agent_status_update.connect(lambda status: self.coordinator_handler.app_status_message.emit(f"智能体状态: {status}"))
        self.agent_manager.agent_action_requested.connect(self._on_agent_action_requested)
        # TODO: 连接更多智能体发出的特定动作或状态信号
        # self.agent_manager.memory_curation_suggestion.connect(self.gui_manager.window.memoryInterface.display_curation_suggestion)

        self.logger.debug("AgentsHandler: Agents层信号连接完成")
        
    @Slot(str)
    def _on_agent_app_message(self, message: str):
        """
        处理来自智能体的应用消息
        """
        self.coordinator_handler.app_status_message.emit(message)
        
    @Slot(str, str)
    def _on_agent_action_requested(self, device_id: str, command: str):
        """
        处理来自智能体层的设备控制请求。
        """
        self.logger.info(f"AgentsHandler: 收到智能体层的设备控制请求 - 设备: {device_id}, 命令: {command}")
        self.device_logic_manager.send_command_to_device(device_id, command)
        self.coordinator_handler.app_status_message.emit(f"命令已发送至设备逻辑管理器: {device_id} - {command}")
