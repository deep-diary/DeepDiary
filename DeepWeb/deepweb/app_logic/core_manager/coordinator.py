# deepweb/app_logic/core_manager/coordinator.py
# 核心协调器
# 
# 职责：
# - 协调 UI 请求，分派给业务逻辑模块
# - 处理异步任务和结果回调
# - 管理各模块间的通信和协调
# 
# 架构定位：
# 作为应用逻辑层的核心调度中心，负责统一管理和分发业务逻辑请求

import os
import importlib
import inspect

from deepweb.data_management.log_manager import LogManager
from deepweb.services.device_communication.mqtt_manager import MQTTManager
from deepweb.app_logic.device_logic_manager.manager import DeviceLogicManager
from deepweb.app_logic.core_manager.base_handler import BaseHandler
from deepweb.ui.ui_manager import UIManager
from deepweb.config.config_manager import ConfigManager


class Coordinator:
    """
    核心协调器类
    
    负责协调整个应用的业务逻辑流转，作为 UI 层与业务逻辑层的中间桥梁。
    """

    def __init__(self, log_manager: LogManager):
        """
        初始化协调器
        
        Args:
            log_manager: 日志管理器实例（必须传入有效的 LogManager）
        """
        self.log_manager = log_manager
        self.logger = log_manager.get_logger(__name__)
        self.logger.info("Coordinator: 初始化中...")

        # 初始化配置管理器
        self.config_manager = ConfigManager()
        
        # 初始化管理器
        self.init_managers()
        # 初始化处理器
        self.init_handlers()
        # 启动应用程序
        self.start_application()
        self.logger.info("Coordinator: 应用程序启动完成。")

    
    def init_managers(self):
        """
        初始化所有管理器
        
        该方法用于初始化应用中的各个管理器模块，
        如设备管理器、数据管理器等。
        """
        self.logger.info("Coordinator: 初始化管理器...")
        
        # 创建并持有 UI 管理器，由协调器统一管理
        self.ui_manager = UIManager(log_manager=self.log_manager, coordinator=self)

        # 创建MQTT管理器
        # 注意：client_id="deepweb" 是 MQTT 客户端的标识符（用于标识这个服务器客户端）
        # 订阅主题时使用通配符 "+" 来接收所有设备的消息，而不是固定为 "deepweb"
        # 例如：订阅 device/+/info 可以接收 device/device_001/info, device/device_002/info 等
        self.mqtt_manager = MQTTManager(
            log_manager=self.log_manager,
            server_name="default"
        )
        
        # 初始化设备逻辑管理器（如果需要，暂时不初始化，后续用到时再启用）
        self.device_logic_manager = None
        # self.device_logic_manager = DeviceLogicManager(log_manager=self.log_manager, config_manager=self.config_manager)


    def init_handlers(self):
        """
        自动发现、实例化、初始化所有 Handler 类
        
        注意：
            CoordinatorHandler 需要优先初始化，因为其他 Handler 可能依赖它。
            Handler 用于处理特定的业务逻辑请求。
        """
        self.logger.info("Coordinator: 开始自动发现和初始化处理器...")
        
        # 存储所有处理器的字典
        self.handlers = {}
        
        # 获取handler文件夹的路径
        handler_dir = os.path.join(os.path.dirname(__file__), 'handler')
        
        if not os.path.exists(handler_dir):
            self.logger.warning(f"Coordinator: Handler目录不存在: {handler_dir}")
            return
            
        # 第一步：优先初始化CoordinatorHandler（如果存在）
        self._init_coordinator_handler(handler_dir)
        
        # 第二步：初始化其他Handler
        self._init_other_handlers(handler_dir)
        
        self.logger.info(f"Coordinator: 处理器初始化完成，共初始化 {len(self.handlers)} 个处理器")
        
    def _init_coordinator_handler(self, handler_dir):
        """优先初始化CoordinatorHandler（如果存在）"""
        try:
            # 动态导入CoordinatorHandler模块
            module_path = "deepweb.app_logic.core_manager.handler.coordinator"
            module = importlib.import_module(module_path)
            
            # 查找CoordinatorHandler类
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseHandler) and 
                    obj != BaseHandler and
                    name == 'CoordinatorHandler'):
                    
                    # 创建CoordinatorHandler实例
                    handler_instance = obj(parent=self)
                    
                    # 先存储处理器实例到handlers字典
                    handler_name = name.lower()
                    self.handlers[handler_name] = handler_instance
                    
                    # 然后设置依赖项
                    handler_instance.set_coordinator_dependencies(self)
                    self.logger.info(f"Coordinator: 设置依赖项: {handler_name}")
                    # 初始化处理器
                    handler_instance.initialize()
                    
                    self.logger.info(f"Coordinator: 成功初始化CoordinatorHandler")
                    return
                    
        except ImportError:
            # CoordinatorHandler不存在，这是正常的（可选）
            pass
        except Exception as e:
            self.logger.error(f"Coordinator: 初始化CoordinatorHandler失败: {e}")
            
    def _init_other_handlers(self, handler_dir):
        """初始化其他Handler"""
        # 遍历handler文件夹中的所有.py文件
        for filename in os.listdir(handler_dir):
            if filename.endswith('.py') and not filename.startswith('__') and filename != 'coordinator.py':
                module_name = filename[:-3]  # 去掉.py后缀
                
                try:
                    # 动态导入模块
                    module_path = f"deepweb.app_logic.core_manager.handler.{module_name}"
                    module = importlib.import_module(module_path)
                    
                    # 查找模块中的Handler类
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseHandler) and 
                            obj != BaseHandler):
                            self.logger.debug(f"Coordinator: 开始初始化处理器: {name}")
                            # 创建处理器实例
                            handler_instance = obj(parent=self)
                            
                            # 设置依赖项
                            handler_instance.set_coordinator_dependencies(self)
                            
                            # 初始化处理器
                            handler_instance.initialize()
                            
                            # 存储处理器实例
                            handler_name = name.lower()
                            self.handlers[handler_name] = handler_instance
                            
                            self.logger.debug(f"Coordinator: 成功初始化处理器: {name}")
                            
                except Exception as e:
                    self.logger.error(f"Coordinator: 初始化处理器 {module_name} 失败: {e}")
                    continue
   
    def start_application(self):
        """
        启动应用程序
        
        该方法用于启动应用的业务逻辑流程，
        包括初始化各种服务和启动后台任务等。
        """
        self.logger.info("Coordinator: 启动应用程序...")
        # 可以在这里添加启动时的业务逻辑
        # 例如：启动定时任务、初始化数据等

    def cleanup(self):
        """
        协调器清理资源的方法。
        在应用程序退出时调用，确保所有子模块的资源被正确释放。
        """
        self.logger.info("Coordinator: 执行清理工作。")

        # 清理处理器
        if hasattr(self, 'handlers'):
            for handler_name, handler in self.handlers.items():
                try:
                    handler.cleanup()
                    self.logger.info(f"Coordinator: 已清理处理器: {handler_name}")
                except Exception as e:
                    self.logger.error(f"Coordinator: 清理处理器 {handler_name} 失败: {e}")

        # 关闭所有子模块可能打开的资源
        if hasattr(self, 'mqtt_manager') and self.mqtt_manager:
            # 如果MQTTManager有清理方法，可以在这里调用
            pass

        self.logger.info("Coordinator: 所有子模块清理完成。")
  