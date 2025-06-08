# src/app_logic/core_manager/coordinator.py
# 核心协调器 (T类)
# 负责协调 UI 请求，分派给业务逻辑模块，并处理异步任务和结果回调。

from PySide6.QtCore import QObject, Signal, Slot, QThreadPool, QRunnable
from typing import Dict, Any

# 导入应用逻辑层的各个管理器/处理器
# 注意：这里我们假设这些模块都存在，实际开发中需要逐步实现
from src.app_logic.memory_processing.image_video_processing.processor import ImageVideoProcessor
from src.app_logic.resource_demand_manager.manager import ResourceDemandManager # 假设的资源需求管理器
from src.app_logic.device_logic_manager.manager import DeviceLogicManager     # 假设的设备逻辑管理器
from src.app_logic.ai_coordinator.coordinator import AICoordinator         # 假设的AI协调器
from src.app_logic.agents.agent_manager import AgentManager               # 智能体管理器
from src.services.cloud_communication.api_client import CloudApiClient      # 云端API客户端示例
from src.data_management.local_database import LocalDatabaseManager       # 本地数据库管理器
from src.data_management.log_manager import LogManager # 日志管理器


class WorkerRunnable(QRunnable):
    """
    一个可运行的任务封装类，用于在 QThreadPool 中执行耗时操作。
    它接受一个函数和其参数，并在执行完成后发射一个信号。
    """
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals() # 用于报告结果和错误

    @Slot()
    def run(self):
        """
        在后台线程中执行任务。
        """
        try:
            result = self.func(*self.args, **self.kwargs)
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))


class WorkerSignals(QObject):
    """
    定义 WorkerRunnable 发射的信号。
    """
    finished = Signal(object) # 任务完成，传递结果
    error = Signal(str)      # 任务出错，传递错误信息
    progress = Signal(int)   # 任务进度更新 (可选)


class Coordinator(QObject):
    """
    DeepWin 应用程序的核心协调器。
    它负责：
    1. 管理和初始化应用逻辑层的各个模块。
    2. 接收来自 UI 的请求，并分派给对应的业务逻辑模块。
    3. 管理后台任务的执行（通过 QThreadPool），确保 UI 保持响应。
    4. 将业务逻辑执行结果或状态更新回调给 UI 或其他相关模块。
    5. 协调智能体层的行为。
    """

    # 定义协调器可以向 UI 发射的信号，用于更新界面
    # 例如：
    image_processing_started = Signal(str) # 图像处理开始，传递文件路径
    image_processing_finished = Signal(str, str) # 图像处理完成，传递文件路径和结果
    image_processing_error = Signal(str, str) # 图像处理出错，传递文件路径和错误信息
    device_status_updated = Signal(dict) # 设备状态更新
    resource_matched = Signal(dict) # 资源匹配结果
    app_status_message = Signal(str) # 应用状态消息（显示在状态栏）

    def __init__(self, log_manager: LogManager, parent=None):
        super().__init__(parent)
        self.logger = log_manager.get_logger(__name__)
        self.logger.info("Coordinator: 初始化中...")

        self.thread_pool = QThreadPool.globalInstance()

        # 初始化应用逻辑层的各个管理器/处理器
        # 这些是我们的 'I类'，它们不直接与 UI 交互
        self.image_video_processor = ImageVideoProcessor(log_manager=log_manager)
        self.resource_demand_manager = ResourceDemandManager(log_manager=log_manager)
        self.device_logic_manager = DeviceLogicManager(log_manager=log_manager)
        self.ai_coordinator = AICoordinator(log_manager=log_manager)
        self.agent_manager = AgentManager(log_manager=log_manager) # 智能体管理器也需要协调器引用
        self.agent_manager.set_coordinator(self)

        # 初始化服务层和数据管理层
        self.cloud_api_client = CloudApiClient(log_manager=log_manager)
        self.local_database_manager = LocalDatabaseManager(log_manager=log_manager)

        self._connect_internal_signals() # 连接内部模块的信号

        self.logger.info("Coordinator: 初始化完成。")

    def _connect_internal_signals(self):
        """
        连接内部模块发出的信号到协调器的方法，
        或将协调器的方法连接到其他模块。
        """
        # 示例：连接图像处理器完成信号到协调器的方法
        self.image_video_processor.processing_finished.connect(self._on_image_processing_done)
        self.image_video_processor.processing_error.connect(self._on_image_processing_error)
        # 可以有更多内部信号连接，例如设备状态变化由 device_logic_manager 发出，由协调器接收并转发
        # self.device_logic_manager.status_changed.connect(self.device_status_updated.emit)

        # 示例：连接智能体层需要获取数据的信号
        self.agent_manager.request_memory_data.connect(self.local_database_manager.get_memories)
        self.agent_manager.trigger_device_action.connect(self.device_logic_manager.send_command_to_device)
        self.agent_manager.request_cloud_ai.connect(self.ai_coordinator.request_cloud_ai_service)


    @Slot(str)
    def handle_process_image_request(self, image_path: str):
        """
        槽函数：处理来自 UI 的图像处理请求。
        将耗时的图像处理任务提交到线程池执行，不阻塞 UI。
        """
        self.logger.info(f"Coordinator: 收到图像处理请求：{image_path}")
        self.app_status_message.emit(f"正在处理图片：{image_path}...")
        self.image_processing_started.emit(image_path)

        # 创建一个 QRunnable 实例来执行实际的图像处理逻辑
        worker = WorkerRunnable(self.image_video_processor.process_image, image_path)
        # 连接 worker 信号到协调器的方法
        worker.signals.finished.connect(lambda result: self.image_processing_finished.emit(image_path, result))
        worker.signals.error.connect(lambda error_msg: self.image_processing_error.emit(image_path, error_msg))

        # 将 worker 提交到线程池执行
        self.thread_pool.start(worker)

    @Slot(float, float)
    def handle_match_resource_request(self, latitude: float, longitude: float):
        """
        槽函数：处理来自 UI 的资源匹配请求。
        这个可能涉及云端调用，也需要异步处理。
        """
        self.logger.info(f"Coordinator: 收到资源匹配请求，位置：{latitude}, {longitude}")
        self.app_status_message.emit("正在匹配资源...")

        # 同样，可以将资源匹配任务提交到线程池或使用异步网络库
        # 这里仅作示例，假设资源匹配逻辑在 resource_demand_manager 中
        worker = WorkerRunnable(self.resource_demand_manager.find_matching_resources, latitude, longitude)
        worker.signals.finished.connect(lambda result: self.resource_matched.emit(result))
        worker.signals.error.connect(lambda error_msg: self.app_status_message.emit(f"资源匹配失败: {error_msg}"))
        self.thread_pool.start(worker)

    @Slot(str, str)
    def handle_device_control_request(self, device_id: str, command: str):
        """
        槽函数：处理来自 UI 的设备控制请求。
        """
        self.logger.info(f"Coordinator: 收到设备控制请求：{device_id} - {command}")
        self.app_status_message.emit(f"正在发送命令到设备 {device_id}...")
        # 设备控制可能涉及串口或网络通信，也需要异步处理
        worker = WorkerRunnable(self.device_logic_manager.send_command_to_device, device_id, command)
        worker.signals.finished.connect(lambda res: self.app_status_message.emit(f"命令发送成功: {res}"))
        worker.signals.error.connect(lambda err: self.app_status_message.emit(f"命令发送失败: {err}"))
        self.thread_pool.start(worker)


    def _on_image_processing_done(self, result: str):
        """
        内部槽函数：处理图像处理任务完成的信号。
        由 ImageVideoProcessor 发出。
        """
        self.logger.info(f"Coordinator: 图像处理任务完成：{result}")
        self.app_status_message.emit(f"图像处理完成！结果：{result}")
        # 这里可以触发 UI 更新，但因为 signal 已经连接到 self.image_processing_finished.emit，所以实际在主窗口处理

    def _on_image_processing_error(self, error_msg: str):
        """
        内部槽函数：处理图像处理任务出错的信号。
        由 ImageVideoProcessor 发出。
        """
        self.logger.error(f"Coordinator: 图像处理任务出错：{error_msg}")
        self.app_status_message.emit(f"图像处理出错：{error_msg}")
        # 这里可以触发 UI 更新，但因为 signal 已经连接到 self.image_processing_error.emit，所以实际在主窗口处理


    def cleanup(self):
        """
        协调器清理资源的方法。
        """
        self.logger.info("Coordinator: 执行清理工作。")
        # 关闭所有子模块可能打开的资源
        self.image_video_processor.cleanup()
        self.resource_demand_manager.cleanup()
        self.device_logic_manager.cleanup()
        self.ai_coordinator.cleanup()
        self.agent_manager.cleanup()
        self.cloud_api_client.cleanup()
        self.local_database_manager.cleanup()