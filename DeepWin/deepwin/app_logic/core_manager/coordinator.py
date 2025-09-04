# src/app_logic/core_manager/coordinator.py
# 核心协调器 (T类)
# 负责协调 UI 请求，分派给业务逻辑模块，并处理异步任务和结果回调。
# 完善模块协调和事件分发逻辑。

from PySide6.QtCore import QObject, Signal, Slot, QThreadPool, QTimer
from typing import Dict, Any, Optional, List
import time
import os
import importlib
import inspect
import asyncio
import concurrent.futures
from datetime import datetime


from deepwin.app_logic.core_manager.base_handler import BaseHandler

# 导入公共的 WorkerRunnable 和 WorkerSignals，以解决循环导入问题
from deepwin.app_logic.core_manager.workers import WorkerRunnable, WorkerSignals

# 导入应用逻辑层的各个管理器/处理器
from deepwin.app_logic.memory_processing.image_processing.manager import ImageManager
from deepwin.app_logic.resource_demand_manager.manager import ResourceDemandManager
from deepwin.app_logic.device_logic_manager.manager import DeviceLogicManager
from deepwin.app_logic.ai_coordinator.coordinator import AICoordinator
from deepwin.app_logic.agents.agent_manager import AgentManager
from deepwin.app_logic.core_manager.task_scheduler import TaskScheduler # 导入新任务调度器

# 导入处理器
from deepwin.app_logic.core_manager.handler.hardware_communication import HardwareCommunicationHandler

from deepwin.data_management.local_database import LocalDatabaseManager
from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager
from deepwin.services.hardware_communication.serial_communicator import SerialCommunicator
from deepwin.services.hardware_communication.can_bus_communicator import CanBusCommunicator
from deepwin.services.hardware_communication.device_protocol_parser import DeviceProtocolParser
from deepwin.services.cloud_communication.api_client import CloudApiClient
from deepwin.services.voice_communication.voice_manager import VoiceManager
from deepwin.app_logic.mcp_client_manager.mcp_client_manager import MCPClientManager
from deepwin.app_logic.weather_manager import WeatherManager
from deepwin.services.web_crawler.crawler_manager import CrawlerManager

from deepwin.data_management.database.sqlite_manager import SQLiteManager
from deepwin.data_management.database.qdrant_manager import QdrantManager
from deepwin.ui.gui_manager import GuiManager

from deepwin.utils.path_manager import PathManager

class Coordinator(QObject):
    """
    DeepWin 应用程序的核心协调器。
    它负责：
    1. 管理和初始化应用逻辑层的各个模块。
    2. 接收来自 UI 或其他模块的请求，并分派给对应的业务逻辑模块。
    3. 管理后台任务的执行（通过 QThreadPool 和 TaskScheduler），确保 UI 保持响应。
    4. 将业务逻辑执行结果或状态更新回调给 UI 或其他相关模块。
    5. 协调智能体层的行为，作为智能体感知和行动的桥梁。
    6. 实现模块间的事件分发和统一协调。
    """


    def __init__(self, log_manager: LogManager, parent=None):
        """
        初始化协调器及其所有子模块。
        :param log_manager: 全局日志管理器实例。
        :param parent: QObject 父对象。
        """
        super().__init__(parent)
        self.logger = log_manager.get_logger(__name__)
        self.log_manager = log_manager  # 添加log_manager属性
        self.logger.info("Coordinator: 初始化中...")

        self.thread_pool = QThreadPool.globalInstance()
        # Ensure the thread pool is ready, and we manage its maximum threads
        # self.thread_pool.setMaxThreadCount(QThreadPool.globalInstance().maxThreadCount() - 1) # Moved to main.py
        self.logger.info(f"Coordinator: QThreadPool max thread count: {self.thread_pool.maxThreadCount()}")

        # 1. 初始化配置管理器
        self.config_manager = ConfigManager(log_manager=log_manager)
        self.config_manager.load_env() # 加载环境变量

        # 2. 初始化管理器（包括数据库管理器，会自动初始化数据库）
        self.init_managers()

        # 3. 初始化处理器
        self.init_handlers()

        # 4. 启动定时任务 (例如：数据同步) TODO: 暂时不启动, 目前代码启动后会异常退出
        # self.setup_initial_tasks()

        # 5. 启动应用程序
        self.start_application()

        self.logger.info("Coordinator: 初始化完成。")
    
    def init_managers(self):
        """
        初始化管理器
        """
        self.logger.info("Coordinator: 初始化管理器...")
        # ----------------------------------------------------------------------
        # 1. 初始化应用逻辑层的各个管理器/处理器
        # 这些模块专注于各自的业务逻辑，不直接与 UI 交互
        # ----------------------------------------------------------------------
        self.image_manager = ImageManager(log_manager=self.log_manager, config_manager=self.config_manager)
        self.resource_demand_manager = ResourceDemandManager(log_manager=self.log_manager)
        self.device_logic_manager = DeviceLogicManager(log_manager=self.log_manager, config_manager=self.config_manager)
        self.ai_coordinator = AICoordinator(log_manager=self.log_manager) # 避免与 Coordinator 类名冲突
        self.agent_manager = AgentManager(log_manager=self.log_manager) # 智能体管理器需要协调器引用
        self.agent_manager.set_coordinator(self)
        self.path_manager = PathManager(log_manager=self.log_manager, config_manager=self.config_manager)

        # ----------------------------------------------------------------------
        # 2. 初始化核心服务模块
        # ----------------------------------------------------------------------
        self.task_scheduler = TaskScheduler(log_manager=self.log_manager, thread_pool=self.thread_pool)
        self.cloud_api_client = CloudApiClient(log_manager=self.log_manager)
        self.local_database_manager = LocalDatabaseManager(log_manager=self.log_manager, config_manager=self.config_manager)
        self.gui_manager = GuiManager(log_manager=self.log_manager, config_manager=self.config_manager) # GUI 管理器用于管理 UI 视图


        # 实例化服务层组件 (真正的服务层实现)
        self.serial_communicator = SerialCommunicator(log_manager=self.log_manager, config_manager=self.config_manager)
        self.can_bus_communicator = CanBusCommunicator(log_manager=self.log_manager, config_manager=self.config_manager)
        self.device_protocol_parser = DeviceProtocolParser(log_manager=self.log_manager, config_manager=self.config_manager)
        self.cloud_api_client = CloudApiClient(log_manager=self.log_manager) # 云端 API 客户端
        self.voice_manager = VoiceManager(log_manager=self.log_manager, config_manager=self.config_manager)

        # 实例化 MCPClientManager
        self.mcp_client_manager = MCPClientManager(log_manager=self.log_manager, config_manager=self.config_manager) # NEW
        # 实例化 WeatherManager，并传入 mcp_client_manager
        self.weather_manager = WeatherManager(mcp_client_manager=self.mcp_client_manager, log_manager=self.log_manager) # NEW

        # 实例化爬虫管理器
        self.crawler_manager = CrawlerManager(log_manager=self.log_manager, config_manager=self.config_manager)

        # 连接任务调度器信号（只连接一次，避免重复执行）
        self.task_scheduler.task_completed.connect(self._on_crawler_task_completed)
        self.task_scheduler.task_failed.connect(self._on_crawler_task_failed)
        self.logger.info("Coordinator: 任务调度器信号连接完成")

        # 实例化数据库管理器
        # 注意：LocalDatabaseManager在创建时会自动初始化数据库
        # 这里只需要获取数据库实例即可
        self.sqlite_db: Optional[SQLiteManager] = None
        self.qdrant_db: Optional[QdrantManager] = None
        self.local_database_manager = LocalDatabaseManager(log_manager=self.log_manager, config_manager=self.config_manager)
        
        # 获取数据库实例（数据库已经初始化完成）
        if self.local_database_manager.is_ready:
            self.sqlite_db = self.local_database_manager.coordinator.get_database('sqlite')
            self.qdrant_db = self.local_database_manager.coordinator.get_database('qdrant')
            self.logger.info(f"Coordinator: 数据库实例获取成功: {self.sqlite_db} {self.qdrant_db}")
        else:
            self.logger.warning("Coordinator: 数据库未就绪，实例获取失败")

    def init_handlers(self):
        """
        自动发现、实例化、初始化所有Handler类
        注意：CoordinatorHandler需要优先初始化，因为其他Handler依赖它
        """
        self.logger.info("Coordinator: 开始自动发现和初始化处理器...")
        
        # 存储所有处理器的字典
        self.handlers = {}
        
        # 获取handler文件夹的路径
        handler_dir = os.path.join(os.path.dirname(__file__), 'handler')
        
        if not os.path.exists(handler_dir):
            self.logger.warning(f"Coordinator: Handler目录不存在: {handler_dir}")
            return
            
        # 第一步：优先初始化CoordinatorHandler
        self._init_coordinator_handler(handler_dir)
        
        # 第二步：初始化其他Handler
        self._init_other_handlers(handler_dir)
        
        self.logger.info(f"Coordinator: 处理器初始化完成，共初始化 {len(self.handlers)} 个处理器")
        
    def _init_coordinator_handler(self, handler_dir):
        """优先初始化CoordinatorHandler"""
        try:
            # 动态导入CoordinatorHandler模块
            module_path = "deepwin.app_logic.core_manager.handler.coordinator"
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
                    
        except Exception as e:
            self.logger.error(f"Coordinator: 初始化CoordinatorHandler失败: {e}")
            # 如果CoordinatorHandler初始化失败，记录错误但不覆盖handlers字典
            # 这样其他Handler仍然可以尝试初始化
            
    def _init_other_handlers(self, handler_dir):
        """初始化其他Handler"""
        # 遍历handler文件夹中的所有.py文件
        for filename in os.listdir(handler_dir):
            if filename.endswith('.py') and not filename.startswith('__') and filename != 'coordinator.py':
                module_name = filename[:-3]  # 去掉.py后缀
                
                try:
                    # 动态导入模块
                    module_path = f"deepwin.app_logic.core_manager.handler.{module_name}"
                    module = importlib.import_module(module_path)
                    
                    # 查找模块中的Handler类
                    for name, obj in inspect.getmembers(module):
                        if (inspect.isclass(obj) and 
                            issubclass(obj, BaseHandler) and 
                            obj != BaseHandler):
                            self.logger.info(f"Coordinator: 开始初始化处理器--------------------------------: {name}")
                            # 创建处理器实例
                            handler_instance = obj(parent=self)
                            
                            # 设置依赖项
                            handler_instance.set_coordinator_dependencies(self)
                            
                            # 初始化处理器
                            handler_instance.initialize()
                            
                            # 存储处理器实例
                            handler_name = name.lower()
                            self.handlers[handler_name] = handler_instance
                            
                            self.logger.info(f"Coordinator: 成功初始化处理器--------------------------------: {name}")
                            
                except Exception as e:
                    self.logger.error(f"Coordinator: 初始化处理器 {module_name} 失败: {e}")
                    continue

    def test_voice_communication(self):
        self.voice_manager.add_task_to_queue('text', text='将电机位置调大些')
        self.voice_manager.add_task_to_queue('transcript', text='转录测试任务1')
        self.voice_manager.start_voice_conversation()
        # 发送数据库准备就绪信号, 让数据库handler 开始创建示例数据, 初始化的时候，由于handler 还没初始化，所以信号发不出来
        self.local_database_manager.database_ready.emit()

    def test_image_processing(self):
        # 测试图像处理
        img_path = self.path_manager.get_path('userdata', 'img/demo.jpg')
        self.logger.info(f"Coordinator: 测试图像处理: {img_path}")
        self.image_manager.process_image(img_path, 'face_recognition')
        self.logger.info(f"Coordinator: 测试图像处理完成")

    def test_crawler(self):
        # 测试爬虫功能 - 爬取星空照片
        self.logger.info("Coordinator: Unsplash爬虫测试...")
        try:
            # # 使用 Unsplash 爬虫爬取星空照片
            # crawler_result = self.crawler_manager.download_images(
            #     crawler_type='unsplash',
            #     query='beautiful girl',
            #     pages=1
            # )
            # self.logger.info(f"Coordinator: 爬虫测试结果: {crawler_result}")
            

            # 测试百度爬虫
            crawler_result = self.crawler_manager.download_images(
                crawler_type='baidu',
                query='Smart 精灵1号',
                pages=1
            )
            self.logger.info(f"Coordinator: 百度爬虫测试结果: {crawler_result}")

            # # 测试多爬虫
            # crawler_result = self.crawler_manager.download_with_multiple_crawlers(
            #     queries=['moon', 'star'],
            #     pages=1
            # )
            # self.logger.info(f"Coordinator: 多爬虫测试结果: {crawler_result}")

            # 测试批量爬虫
            # crawler_result = self.crawler_manager.batch_download_multiple_queries(
            #     crawler_type='baidu',
            #     queries=['赛里木湖', '安徽工程大学'],
            #     pages=1
            # )
            # self.logger.info(f"Coordinator: 批量爬虫测试结果: {crawler_result}")
            
        except Exception as e:
            self.logger.error(f"Coordinator: 爬虫测试失败: {e}")
    def start_application(self):
        """启动应用程序"""
        self.logger.info("Coordinator: 启动应用程序...")
        # 测试语音通信
        # self.test_voice_communication()

        # 测试图像处理
        # self.test_image_processing()

        # 使用任务调度器异步执行爬虫任务
        # try:
        #     # 异步执行爬虫测试任务
        #     crawler_task_id = self.task_scheduler.add_delayed_task(
        #         task_func=self.test_crawler,
        #         delay_ms=1000
        #     )
        #     self.logger.info(f"Coordinator: 爬虫任务已提交到任务调度器，任务ID: {crawler_task_id}")
            
        # except Exception as e:
        #     self.logger.error(f"Coordinator: 提交爬虫任务到调度器失败: {e}")
        
        
        self.agent_manager.start_agents()
        self.logger.info("Coordinator: 应用程序启动完成。")
    
    def _on_crawler_task_completed(self, task_id: str, result: Any):
        """
        爬虫任务完成回调
        """
        self.logger.info(f"Coordinator: 爬虫任务 {task_id} 完成，结果: {result}")
        
    def _on_crawler_task_failed(self, task_id: str, error_msg: str):
        """
        爬虫任务失败回调
        """
        self.logger.error(f"Coordinator: 爬虫任务 {task_id} 失败，错误: {error_msg}")

    # ----------------------------------------------------------------------
    # 示例业务逻辑 (可能由定时任务或智能体触发)
    # ----------------------------------------------------------------------
    def setup_initial_tasks(self):
        """
        设置应用程序启动时需要执行的初始定时任务或后台任务。
        例如：定时数据同步、启动智能体等。
        """
        self.logger.info("Coordinator: 设置初始任务...")
        # 示例：添加一个每隔 30 分钟执行一次的数据同步任务
        self.task_scheduler.add_periodic_task(
            task_id="daily_data_sync",
            task_func=self._perform_daily_data_sync,
            interval_ms=1 * 60 * 1000, # 1分钟
            initial_delay_ms=1000 # 1秒后启动
        )

        # 示例：启动智能体管理器
        # self.agent_manager.start_agents()
        self.logger.info("Coordinator: 初始任务设置完成。")
        
   
    def _perform_daily_data_sync(self):
        """
        示例：执行每日数据同步的业务逻辑。
        这是一个耗时操作，通常会在后台线程中执行。
        """
        self.logger.info("Coordinator: 开始执行每日数据同步...")
        try:
            # 模拟数据同步过程，可能涉及调用 cloud_api_client 和 local_database_manager
            # 例如：
            # cloud_data = self.cloud_api_client.fetch_latest_data()
            # self.local_database_manager.sync_data(cloud_data)
            time.sleep(5) # 模拟同步 5 秒
            sync_result = "数据同步成功"
            self.logger.info("Coordinator: 每日数据同步完成。")
            return sync_result
        except Exception as e:
            self.logger.error(f"Coordinator: 每日数据同步失败: {e}")
            raise # 抛出异常，让 WorkerRunnable 捕获并报告


    def cleanup(self):
        """
        协调器清理资源的方法。
        在应用程序退出时调用，确保所有子模块的资源被正确释放。
        """
        self.logger.info("Coordinator: 执行清理工作。")
        # 停止所有正在运行的定时任务
        self.task_scheduler.stop_all_tasks()
        self.logger.info("Coordinator: 已停止所有任务调度器任务。")

        # 清理处理器
        if hasattr(self, 'handlers'):
            for handler_name, handler in self.handlers.items():
                try:
                    handler.cleanup()
                    self.logger.info(f"Coordinator: 已清理处理器: {handler_name}")
                except Exception as e:
                    self.logger.error(f"Coordinator: 清理处理器 {handler_name} 失败: {e}")

        # 关闭所有子模块可能打开的资源
        # 定义需要清理的模块列表
        modules_to_cleanup = [
            'image_video_processor',
            'resource_demand_manager', 
            'device_logic_manager',
            'ai_coordinator',
            'agent_manager',
            'cloud_api_client',
            'local_database_manager',
            'gui_manager',
            'serial_communicator',
            'can_bus_communicator',
            'device_protocol_parser',
            'voice_manager',
            'crawler_manager'
        ]

        # 循环清理每个模块
        for module_name in modules_to_cleanup:
            if hasattr(self, module_name) and getattr(self, module_name):
                getattr(self, module_name).cleanup()

        self.logger.info("Coordinator: 所有子模块清理完成。")




