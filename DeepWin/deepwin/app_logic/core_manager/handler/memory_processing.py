from PySide6.QtCore import Slot
from deepwin.app_logic.core_manager.base_handler import BaseHandler
from deepwin.app_logic.core_manager.workers import WorkerRunnable

class MemoryProcessingHandler(BaseHandler):
    """
    记忆处理处理器
    负责处理记忆处理相关的信号连接和事件处理
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def _validate_dependencies(self):
        """
        验证必需的依赖项是否已设置
        """
        if not self.logger:
            raise ValueError("缺少必需的依赖项: logger")
        if not self.image_processor:
            raise ValueError("缺少必需的依赖项: image_processor")
        if not self.thread_pool:
            raise ValueError("缺少必需的依赖项: thread_pool")
        if not self.coordinator_handler:
            raise ValueError("缺少必需的依赖项: coordinator_handler")

    def _connect_signals(self):
        """
        连接记忆处理层相关的信号
        """
        if not self.logger:
            return
            
        self.logger.debug("MemoryProcessingHandler: 连接记忆处理层信号...")

        # 图像视频处理器 - 添加信号存在性检查
        if self.image_processor:
            try:
                if hasattr(self.image_processor, 'processing_finished'):
                    self.image_processor.processing_finished.connect(self._on_image_processing_done)
                if hasattr(self.image_processor, 'processing_error'):
                    self.image_processor.processing_error.connect(self._on_image_processing_error)
                if hasattr(self.image_processor, 'processing_progress'):
                    self.image_processor.processing_progress.connect(self._on_image_processing_progress)
                self.logger.debug("MemoryProcessingHandler: 图像处理器信号连接成功")
            except Exception as e:
                self.logger.error(f"MemoryProcessingHandler: 连接图像处理器信号失败: {e}")
                import traceback
                self.logger.error(f"MemoryProcessingHandler: 信号连接异常详情: {traceback.format_exc()}")
        else:
            self.logger.warning("MemoryProcessingHandler: image_processor 为 None，跳过信号连接")
        
        self.logger.debug("MemoryProcessingHandler: 记忆处理层信号连接完成")
        
    @Slot(str)
    def _on_image_processing_done(self, result: str):
        """
        处理图像处理任务完成的信号。
        由 ImageProcessor 发出 (通过 WorkerRunnable 转发)。
        然后 Coordinator 通过自己的信号通知 UI。
        :param result: 图像处理的结果字符串。
        """
        self.logger.info(f"MemoryProcessingHandler: 图像处理任务完成：{result}")
        if hasattr(self.parent(), 'image_processing_finished'):
            self.parent().image_processing_finished.emit(result, "成功")
        self.coordinator_handler.app_status_message.emit(f"图像处理完成！结果：{result}")

    @Slot(str)
    def _on_image_processing_error(self, error_msg: str):
        """
        处理图像处理任务出错的信号。
        由 ImageProcessor 发出 (通过 WorkerRunnable 转发)。
        然后 Coordinator 通过自己的信号通知 UI。
        :param error_msg: 错误信息字符串。
        """
        self.logger.error(f"MemoryProcessingHandler: 图像处理任务出错：{error_msg}")
        if hasattr(self.parent(), 'image_processing_error'):
            self.parent().image_processing_error.emit("", error_msg)
        self.coordinator_handler.app_status_message.emit(f"图像处理出错：{error_msg}")

    @Slot(int)
    def _on_image_processing_progress(self, progress: int):
        """
        处理图像处理任务进度更新的信号。
        由 ImageProcessor 发出 (通过 WorkerRunnable 转发)。
        可以考虑转发给 UI 更新进度条。
        :param progress: 进度百分比 (0-100)。
        """
        self.logger.debug(f"MemoryProcessingHandler: 图像处理进度: {progress}%")
        # TODO: 可以在这里发出一个通用的进度信号给 UI，或者让 UI 直接监听 Processor 的 progress 信号

    @Slot(str)
    def handle_process_image_request(self, image_path: str):
        """
        处理来自 UI 的图像处理请求。
        将耗时的图像处理任务提交到线程池执行，不阻塞 UI。
        """
        self.logger.info(f"MemoryProcessingHandler: 收到图像处理请求：{image_path}")
        self.coordinator_handler.app_status_message.emit(f"正在处理图片：{image_path}...")
        if hasattr(self.parent(), 'image_processing_started'):
            self.parent().image_processing_started.emit(image_path)
        worker = WorkerRunnable(self.image_processor.process_image, image_path)
        worker.signals.finished.connect(self._on_image_processing_done)
        worker.signals.error.connect(self._on_image_processing_error)
        worker.signals.progress.connect(self._on_image_processing_progress)
        self.thread_pool.start(worker)
