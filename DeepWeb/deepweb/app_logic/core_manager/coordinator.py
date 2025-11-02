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

from deepweb.data_management.log_manager import LogManager
from deepweb.services.device_communication.mqtt_manager import MQTTManager
from deepweb.app_logic.handlers.mqtt_handlers import DeviceMessageHandler
from deepweb.ui.ui_manager import UIManager
import threading


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
        self.mqtt_manager = MQTTManager(
            log_manager=self.log_manager,
            server_name="default",
            client_id="deepweb"
        )


    def init_handlers(self):
        """
        自动发现、实例化、初始化所有 Handler 类
        
        注意：
            CoordinatorHandler 需要优先初始化，因为其他 Handler 可能依赖它。
            Handler 用于处理特定的业务逻辑请求。
        """
        self.logger.info("Coordinator: 开始自动发现和初始化处理器...")
        # TODO: 实现自动发现和初始化 Handler 的逻辑
                # 初始化设备消息处理器（UI 稍后注入）
        self.device_handler = DeviceMessageHandler(
            logger=self.logger,
            mqtt_manager=None,
            ui_manager=None,
        )
        # 将实际的 mqtt_manager 和 UI 注入 handler
        self.device_handler.mqtt = self.mqtt_manager
        self.device_handler.ui = self.ui_manager
        
        # 设置统一的消息回调（在handler层根据topic分发）
        self.mqtt_manager.set_message_callback(self.device_handler.handle_message)
        
        self.logger.info("Coordinator: 处理器初始化完成。")
   
    def start_application(self):
        """
        启动应用程序
        
        该方法用于启动应用的业务逻辑流程，
        包括初始化各种服务和启动后台任务等。
        """
        self.logger.info("Coordinator: 启动应用程序...")
        # 开启新线程，循环发送测试主题
        self.test_thread = threading.Thread(target=self.device_handler.send_test_topic,daemon=True)
        self.test_thread.start()

        self.logger.info("Coordinator: 应用程序启动完成。")
  