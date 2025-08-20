# src/app_logic/core_manager/handler/base_handler.py
# 基础处理器类，提供通用的依赖注入和资源管理功能

from PySide6.QtCore import QObject, Signal, QThreadPool
from typing import Optional, Dict, Any, TYPE_CHECKING
from abc import ABC, abstractmethod

# 导入应用逻辑层的各个管理器/处理器
from deepwin.app_logic.memory_processing.image_video_processing.processor import ImageVideoProcessor
from deepwin.app_logic.resource_demand_manager.manager import ResourceDemandManager
from deepwin.app_logic.device_logic_manager.manager import DeviceLogicManager
from deepwin.app_logic.ai_coordinator.coordinator import AICoordinator
from deepwin.app_logic.agents.agent_manager import AgentManager
from deepwin.app_logic.core_manager.task_scheduler import TaskScheduler # 导入新任务调度器

from deepwin.data_management.local_database import LocalDatabaseManager
from deepwin.data_management.log_manager import LogManager
from deepwin.data_management.config_manager import ConfigManager

from deepwin.ui.gui_manager import GuiManager

from deepwin.services.hardware_communication.serial_communicator import SerialCommunicator
from deepwin.services.hardware_communication.can_bus_communicator import CanBusCommunicator
from deepwin.services.hardware_communication.device_protocol_parser import DeviceProtocolParser
from deepwin.services.cloud_communication.api_client import CloudApiClient
from deepwin.services.voice_communication.voice_manager import VoiceManager

from deepwin.app_logic.mcp_client_manager.mcp_client_manager import MCPClientManager
from deepwin.app_logic.weather_manager import WeatherManager
from deepwin.data_management.database.sqlite_manager import SQLiteManager
from deepwin.data_management.database.qdrant_manager import QdrantManager

# 避免循环导入
if TYPE_CHECKING:
    from deepwin.app_logic.core_manager.handler.coordinator import CoordinatorHandler

class BaseHandler(QObject):
    """
    基础处理器类，提供：
    1. 统一的依赖注入机制
    2. 通用的资源管理
    3. 信号连接的基础框架
    4. 避免循环依赖的解决方案
    5. 通用管理器的统一访问
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._dependencies: Dict[str, Any] = {}
        self._is_initialized = False
        
        # 通用管理器属性，子类可以直接访问
        self.logger: Optional[LogManager] = None
        self.config_manager: Optional[ConfigManager] = None
        self.gui_manager: Optional[GuiManager] = None


        # 服务层管理器
        self.serial_communicator: Optional[SerialCommunicator] = None
        self.can_bus_communicator: Optional[CanBusCommunicator] = None
        self.device_protocol_parser: Optional[DeviceProtocolParser] = None
        self.cloud_api_client: Optional[CloudApiClient] = None
        self.local_database_manager: Optional[LocalDatabaseManager] = None
        self.voice_manager: Optional[VoiceManager] = None
        
        # 应用逻辑层管理器
        self.device_logic_manager: Optional[DeviceLogicManager] = None
        self.ai_coordinator: Optional[AICoordinator] = None
        self.agent_manager: Optional[AgentManager] = None
        self.image_video_processor: Optional[ImageVideoProcessor] = None
        self.resource_demand_manager: Optional[ResourceDemandManager] = None
        self.task_scheduler: Optional[TaskScheduler] = None
        self.mcp_client_manager: Optional[MCPClientManager] = None
        self.weather_manager: Optional[WeatherManager] = None

        # 数据库管理器
        self.sqlite_db: Optional[SQLiteManager] = None
        self.qdrant_db: Optional[QdrantManager] = None
        
        # 线程池
        self.thread_pool: Optional[QThreadPool] = None
        
        # 协调器信号处理器（新增）
        self.coordinator_handler: Optional['CoordinatorHandler'] = None
        
    def set_coordinator_dependencies(self, coordinator):
        """
        从协调器设置所有通用依赖项
        这是推荐的初始化方式，简化了依赖注入过程
        :param coordinator: 协调器实例
        """
        # 设置基础管理器
        self.logger = coordinator.logger
        self.config_manager = coordinator.config_manager
        self.gui_manager = coordinator.gui_manager
        
        # 设置服务层管理器
        self.serial_communicator = coordinator.serial_communicator
        self.can_bus_communicator = coordinator.can_bus_communicator
        self.device_protocol_parser = coordinator.device_protocol_parser
        self.cloud_api_client = coordinator.cloud_api_client
        self.local_database_manager = coordinator.local_database_manager
        
        # 设置应用逻辑层管理器
        self.device_logic_manager = coordinator.device_logic_manager
        self.ai_coordinator = coordinator.ai_coordinator
        self.agent_manager = coordinator.agent_manager
        self.image_video_processor = coordinator.image_video_processor
        self.resource_demand_manager = coordinator.resource_demand_manager
        self.task_scheduler = coordinator.task_scheduler
        self.mcp_client_manager = coordinator.mcp_client_manager
        self.weather_manager = coordinator.weather_manager
        
        # 设置语音管理器（新增）
        self.voice_manager = coordinator.voice_manager

        # 设置数据库管理器
        self.sqlite_db = coordinator.sqlite_db
        self.qdrant_db = coordinator.qdrant_db
        
        # 设置线程池
        self.thread_pool = coordinator.thread_pool
        
        # 设置协调器信号处理器（可选依赖）
        if hasattr(coordinator, 'handlers') and 'coordinatorhandler' in coordinator.handlers:
            self.coordinator_handler = coordinator.handlers['coordinatorhandler']
            if self.logger:
                self.logger.info("BaseHandler: 成功从CoordinatorHandler获取coordinator_handler")
        else:
            self.coordinator_handler = None
            if self.logger:
                self.logger.warning("BaseHandler: 无法获取CoordinatorHandler，这是可选的依赖项")
        
    def set_dependency(self, name: str, dependency: Any):
        """
        设置依赖项，支持动态注入（保留原有接口以兼容）
        :param name: 依赖项名称
        :param dependency: 依赖项对象
        """
        self._dependencies[name] = dependency
        
    def get_dependency(self, name: str) -> Optional[Any]:
        """
        获取依赖项（保留原有接口以兼容）
        :param name: 依赖项名称
        :return: 依赖项对象，如果不存在返回None
        """
        return self._dependencies.get(name)
        
    def has_dependency(self, name: str) -> bool:
        """
        检查是否存在指定的依赖项（保留原有接口以兼容）
        :param name: 依赖项名称
        :return: 是否存在
        """
        return name in self._dependencies
        
    def initialize(self):
        """
        初始化处理器，在设置完所有依赖项后调用
        """
        if self._is_initialized:
            return
            
        self._validate_dependencies()
        self._connect_signals()
        self._is_initialized = True
        
    def _validate_dependencies(self):
        """
        验证必需的依赖项是否已设置
        子类必须实现此方法
        """
        pass
        
    def _connect_signals(self):
        """
        连接信号和槽
        子类必须实现此方法
        """
        pass
        
    def cleanup(self):
        """
        清理资源
        """
        self._is_initialized = False
        self._dependencies.clear()
        
        # 清理通用管理器引用
        self.logger = None
        self.config_manager = None
        self.gui_manager = None
        self.app_status_message_signal = None
        self.serial_communicator = None
        self.can_bus_communicator = None
        self.device_protocol_parser = None
        self.cloud_api_client = None
        self.local_database_manager = None
        self.device_logic_manager = None
        self.ai_coordinator = None
        self.agent_manager = None
        self.image_video_processor = None
        self.resource_demand_manager = None
        self.task_scheduler = None
        self.mcp_client_manager = None
        self.weather_manager = None
        
        # 清理线程池
        self.thread_pool = None
        
        # 清理协调器信号处理器
        self.coordinator_handler = None
        
    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._is_initialized 