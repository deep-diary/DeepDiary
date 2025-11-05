# src/app_logic/core_manager/base_handler.py
# 基础处理器类，提供通用的依赖注入和资源管理功能
# Web端版本，不依赖PySide6

from typing import Optional, Dict, Any, TYPE_CHECKING
from abc import ABC, abstractmethod
import logging

# 导入应用逻辑层的各个管理器/处理器
from deepweb.app_logic.device_logic_manager.manager import DeviceLogicManager

from deepweb.config.config_manager import ConfigManager

from deepweb.ui.ui_manager import UIManager

from deepweb.services.device_communication.mqtt_manager import MQTTManager


# 避免循环导入
if TYPE_CHECKING:
    from deepweb.app_logic.core_manager.handler.coordinator import CoordinatorHandler

class BaseHandler:
    """
    基础处理器类，提供：
    1. 统一的依赖注入机制
    2. 通用的资源管理
    3. 事件连接的基础框架（web端不使用信号槽）
    4. 避免循环依赖的解决方案
    5. 通用管理器的统一访问
    """
    
    def __init__(self, parent=None):
        self.parent = parent
        self._dependencies: Dict[str, Any] = {}
        self._is_initialized = False
        
        # 通用管理器属性，子类可以直接访问
        self.logger: Optional[logging.Logger] = None
        self.config_manager: Optional[ConfigManager] = None
        self.ui_manager: Optional[UIManager] = None

        # 服务层管理器
        self.mqtt_manager: Optional[MQTTManager] = None
        
        # 应用逻辑层管理器
        self.device_logic_manager: Optional[DeviceLogicManager] = None
        
        # 协调器信号处理器（可选依赖）
        self.coordinator_handler: Optional['CoordinatorHandler'] = None
        
        # 注意：处理器间通信应该通过协调器进行，避免直接引用
        
    def set_coordinator_dependencies(self, coordinator):
        """
        从协调器设置所有通用依赖项
        这是推荐的初始化方式，简化了依赖注入过程
        :param coordinator: 协调器实例
        """
        # 设置基础管理器
        self.logger = coordinator.log_manager.get_logger(self.__class__.__module__)
        self.config_manager = coordinator.config_manager
        self.ui_manager = coordinator.ui_manager
        
        # 设置服务层管理器
        self.mqtt_manager = coordinator.mqtt_manager
        
        # 设置应用逻辑层管理器
        self.device_logic_manager = coordinator.device_logic_manager
        
        # 设置协调器信号处理器（可选依赖）
        if hasattr(coordinator, 'handlers') and 'coordinatorhandler' in coordinator.handlers:
            self.coordinator_handler = coordinator.handlers['coordinatorhandler']
            self.logger.debug(f"{self.__class__.__name__}: 成功从CoordinatorHandler获取coordinator_handler")
        else:
            self.coordinator_handler = None
            if self.logger:
                self.logger.warning(f"{self.__class__.__name__}: 无法获取CoordinatorHandler，这是可选的依赖项")
        
        # 注意：处理器间通信应该通过协调器进行，避免直接引用
        
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
            
        # 注意：处理器间通信应该通过协调器进行，避免直接引用
        
        self._validate_dependencies()
        self._connect_events()
        self._is_initialized = True
    
    def _validate_dependencies(self):
        """
        验证必需的依赖项是否已设置
        子类可以重写此方法
        """
        pass
        
    def _connect_events(self):
        """
        连接事件处理器（web端不使用信号槽）
        子类可以重写此方法
        """
        pass
        
    def cleanup(self):
        """
        清理资源
        """
        self._is_initialized = False
        self._dependencies.clear()
        
        # 先清理可能触发事件的管理器（保持logger最后清理）
        self.mqtt_manager = None
        self.device_logic_manager = None
        self.ui_manager = None
        
        # 清理协调器处理器
        self.coordinator_handler = None
        
        # 最后清理logger和配置管理器
        self.logger = None
        self.config_manager = None
        
        # 注意：处理器间通信应该通过协调器进行，避免直接引用
        
    @property
    def is_initialized(self) -> bool:
        """是否已初始化"""
        return self._is_initialized 