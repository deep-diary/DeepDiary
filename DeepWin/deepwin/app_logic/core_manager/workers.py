# src/app_logic/core_manager/workers.py
# 后台工作者模块
# 包含 WorkerRunnable 和 WorkerSignals 类，用于在 QThreadPool 中执行耗时操作。
# 这是为了解决 Coordinator 和 TaskScheduler 之间的循环导入问题而提取出来的公共模块。

from PySide6.QtCore import QObject, Signal, Slot, QRunnable
from typing import Any


class WorkerRunnable(QRunnable):
    """
    一个可运行的任务封装类，用于在 QThreadPool 中执行耗时操作。
    它接受一个函数和其参数，并在执行完成后发射一个信号。
    """
    def __init__(self, func, *args, **kwargs):
        """
        初始化 WorkerRunnable 实例。
        :param func: 要在后台执行的函数。
        :param args: 传递给 func 的位置参数。
        :param kwargs: 传递给 func 的关键字参数。
        """
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals() # 用于报告结果、错误和进度

    @Slot()
    def run(self):
        """
        在后台线程中执行任务。
        执行 self.func，并将结果或错误通过 signals 发射。
        """
        try:
            self.signals.progress.emit(0) # 任务开始时发出进度信号
            result = self.func(*self.args, **self.kwargs)
            self.signals.progress.emit(100) # 任务完成时发出进度信号
            self.signals.finished.emit(result)
        except Exception as e:
            self.signals.error.emit(str(e))


class WorkerSignals(QObject):
    """
    定义 WorkerRunnable 发射的信号。
    这些信号用于跨线程安全地报告任务状态。
    """
    finished = Signal(object) # 任务完成，传递结果 (object 类型可传递任何Python对象)
    error = Signal(str)      # 任务出错，传递错误信息字符串
    progress = Signal(int)   # 任务进度更新 (0-100 的整数)

