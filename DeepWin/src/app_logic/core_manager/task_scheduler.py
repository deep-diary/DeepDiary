# src/app_logic/core_manager/task_scheduler.py
# 任务调度器
# 实现任务调度器（如定时任务、后台大文件处理队列）。

import time
import uuid
from PySide6.QtCore import QObject, Signal, Slot, QTimer, QThreadPool, QRunnable
from typing import Callable, Dict, Any, Optional

from src.data_management.log_manager import LogManager # 导入日志管理器
from src.app_logic.core_manager.workers import WorkerRunnable, WorkerSignals # 重用 WorkerRunnable


class TaskScheduler(QObject):
    """
    DeepWin 应用程序的任务调度器。
    负责管理定时任务和后台队列任务，确保它们在不阻塞 UI 的情况下执行。
    支持：
    1. 添加和管理周期性任务 (Periodic Tasks)。
    2. 添加和管理一次性延时任务 (Delayed Tasks)。
    3. 提交任意后台任务到 QThreadPool。
    4. 报告任务完成或失败的状态。
    """

    task_completed = Signal(str, object) # 任务完成信号：task_id, result
    task_failed = Signal(str, str)      # 任务失败信号：task_id, error_message
    task_progress = Signal(str, int)    # 任务进度信号：task_id, progress (0-100)

    def __init__(self, log_manager: LogManager, thread_pool: QThreadPool, parent: Optional[QObject] = None):
        """
        初始化任务调度器。
        :param log_manager: 全局日志管理器实例。
        :param thread_pool: 用于执行耗时任务的 QThreadPool 实例。
        :param parent: QObject 父对象。
        """
        super().__init__(parent)
        self.logger = log_manager.get_logger(__name__)
        self.thread_pool = thread_pool
        self.logger.info("TaskScheduler: 初始化中...")

        # 存储周期性任务的字典: {task_id: QTimer实例}
        self.periodic_timers: Dict[str, QTimer] = {}
        # 存储一次性延时任务的字典: {task_id: QTimer实例}
        self.delayed_timers: Dict[str, QTimer] = {}
        # 存储任务执行函数，以便 QTimer 触发时能够正确调用
        self.task_functions: Dict[str, Callable] = {}

        self.logger.info("TaskScheduler: 初始化完成。")

    def _execute_task_in_background(self, task_id: str, task_func: Callable, *args, **kwargs):
        """
        在后台线程池中执行一个任务。
        :param task_id: 任务的唯一标识符。
        :param task_func: 要执行的任务函数。
        :param args: 任务函数的参数。
        :param kwargs: 任务函数的关键字参数。
        """
        self.logger.info(f"TaskScheduler: 提交任务 '{task_id}' 到线程池。")
        worker = WorkerRunnable(task_func, *args, **kwargs)

        # 连接 WorkerRunnable 的信号到 TaskScheduler 的内部槽函数
        worker.signals.finished.connect(lambda result: self._on_worker_finished(task_id, result))
        worker.signals.error.connect(lambda error_msg: self._on_worker_error(task_id, error_msg))
        worker.signals.progress.connect(lambda progress: self._on_worker_progress(task_id, progress))

        self.thread_pool.start(worker)

    @Slot(str, object)
    def _on_worker_finished(self, task_id: str, result: Any):
        """
        内部槽函数：处理 WorkerRunnable 完成任务的信号。
        然后通过 TaskScheduler 的公开信号通知外部（Coordinator）。
        :param task_id: 完成的任务ID。
        :param result: 任务执行结果。
        """
        self.logger.info(f"TaskScheduler: 任务 '{task_id}' (Worker) 完成。结果: {result}")
        self.task_completed.emit(task_id, result)

    @Slot(str, str)
    def _on_worker_error(self, task_id: str, error_msg: str):
        """
        内部槽函数：处理 WorkerRunnable 任务出错的信号。
        然后通过 TaskScheduler 的公开信号通知外部（Coordinator）。
        :param task_id: 失败的任务ID。
        :param error_msg: 错误信息。
        """
        self.logger.error(f"TaskScheduler: 任务 '{task_id}' (Worker) 失败。错误: {error_msg}")
        self.task_failed.emit(task_id, error_msg)

    @Slot(str, int)
    def _on_worker_progress(self, task_id: str, progress: int):
        """
        内部槽函数：处理 WorkerRunnable 任务进度更新的信号。
        :param task_id: 任务ID。
        :param progress: 进度百分比 (0-100)。
        """
        self.logger.debug(f"TaskScheduler: 任务 '{task_id}' 进度: {progress}%")
        self.task_progress.emit(task_id, progress) # 转发进度信号


    def add_periodic_task(self, task_id: str, task_func: Callable, interval_ms: int,
                          initial_delay_ms: int = 0, *args, **kwargs):
        """
        添加一个周期性任务。
        任务将每隔 `interval_ms` 毫秒执行一次。
        如果 `task_id` 已存在，将替换现有任务。
        :param task_id: 任务的唯一标识符。
        :param task_func: 要周期性执行的函数。
        :param interval_ms: 任务执行的周期，单位毫秒。
        :param initial_delay_ms: 首次执行的延迟，单位毫秒 (默认为0，即立即开始周期性执行)。
        :param args: 传递给 task_func 的位置参数。
        :param kwargs: 传递给 task_func 的关键字参数。
        """
        if task_id in self.periodic_timers:
            self.remove_task(task_id) # 停止并移除旧任务

        timer = QTimer(self)
        # 使用 lambda 表达式包装任务函数和参数，并提交到后台执行
        # 确保在 QTimer 触发时，任务被安全地提交到 QThreadPool
        timer.timeout.connect(lambda: self._execute_task_in_background(task_id, task_func, *args, **kwargs))
        timer.start(interval_ms)
        self.periodic_timers[task_id] = timer
        self.task_functions[task_id] = (task_func, args, kwargs) # 存储任务函数及其参数，用于更新或调试

        self.logger.info(f"TaskScheduler: 添加周期性任务 '{task_id}'，间隔 {interval_ms} ms。")

        if initial_delay_ms > 0:
            # 首次执行时额外延迟
            QTimer.singleShot(initial_delay_ms, lambda: self._execute_task_in_background(task_id, task_func, *args, **kwargs))
            self.logger.info(f"TaskScheduler: 周期性任务 '{task_id}' 首次执行将延迟 {initial_delay_ms} ms。")
        else:
            # 如果没有初始延迟，立即执行一次
            self._execute_task_in_background(task_id, task_func, *args, **kwargs)
            self.logger.info(f"TaskScheduler: 周期性任务 '{task_id}' 首次执行已立即开始。")


    def add_delayed_task(self, task_func: Callable, delay_ms: int, *args, **kwargs) -> str:
        """
        添加一个一次性延时任务。
        任务将在 `delay_ms` 毫秒后执行一次。
        :param task_func: 要执行的函数。
        :param delay_ms: 延迟执行的时间，单位毫秒。
        :param args: 传递给 task_func 的位置参数。
        :param kwargs: 传递给 task_func 的关键字参数。
        :return: 任务的唯一标识符 (task_id)。
        """
        task_id = str(uuid.uuid4())
        self.task_functions[task_id] = (task_func, args, kwargs)
        
        timer = QTimer(self)
        timer.setSingleShot(True)
        timer.timeout.connect(lambda: self._on_delayed_task_timeout(task_id))
        timer.start(delay_ms)
        self.delayed_timers[task_id] = timer
        return task_id

    @Slot(str)
    def _on_delayed_task_timeout(self, task_id: str):
        if task_id in self.task_functions:
            task_func, args, kwargs = self.task_functions[task_id]
            self._execute_task_in_background(task_id, task_func, *args, **kwargs)
            del self.task_functions[task_id]


    def update_periodic_task(self, task_id: str, task_func: Callable, interval_ms: int, *args, **kwargs):
        """
        更新一个已存在的周期性任务的间隔和/或任务函数。
        如果任务不存在，将创建一个新任务。
        :param task_id: 要更新的任务ID。
        :param task_func: 新的任务函数。
        :param interval_ms: 新的任务间隔，单位毫秒。
        :param args: 传递给 task_func 的位置参数。
        :param kwargs: 传递给 task_func 的关键字参数。
        """
        self.logger.info(f"TaskScheduler: 更新周期性任务 '{task_id}'，新间隔 {interval_ms} ms。")
        self.add_periodic_task(task_id, task_func, interval_ms, initial_delay_ms=0, *args, **kwargs) # 重新添加会替换旧的

    def remove_task(self, task_id: str):
        """
        移除一个周期性任务或延时任务。
        :param task_id: 要移除的任务ID。
        """
        if task_id in self.periodic_timers:
            timer = self.periodic_timers.pop(task_id)
            timer.stop()
            timer.deleteLater() # 确保 QTimer 对象被正确销毁
            self.task_functions.pop(task_id, None)
            self.logger.info(f"TaskScheduler: 已移除周期性任务 '{task_id}'。")
        elif task_id in self.delayed_timers:
            timer = self.delayed_timers.pop(task_id)
            timer.stop()
            timer.deleteLater()
            self.task_functions.pop(task_id, None)
            self.logger.info(f"TaskScheduler: 已移除延时任务 '{task_id}'。")
        else:
            self.logger.warning(f"TaskScheduler: 尝试移除不存在的任务 '{task_id}'。")

    def stop_all_tasks(self):
        """
        停止并移除所有正在运行的周期性任务和延时任务。
        在应用程序关闭时调用。
        """
        self.logger.info("TaskScheduler: 停止所有任务。")
        for task_id in list(self.periodic_timers.keys()):
            self.remove_task(task_id)
        for task_id in list(self.delayed_timers.keys()):
            self.remove_task(task_id)
        self.logger.info("TaskScheduler: 所有任务已停止。")


    def cleanup(self):
        """
        清理任务调度器占用的资源。
        """
        self.stop_all_tasks()
        self.logger.info("TaskScheduler: 执行清理工作。")

