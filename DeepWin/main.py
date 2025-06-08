# main.py
# DeepWin 应用程序入口

import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThreadPool # 用于管理后台任务

# 导入 DeepWin 核心组件
from src.app_logic.core_manager.coordinator import Coordinator
from src.ui.main_window import MainWindowManager
from src.data_management.log_manager import LogManager # 导入日志管理器


def main():
    """
    DeepWin 应用程序主入口。
    初始化应用，协调器，UI，并启动事件循环。
    """


    # 1. 初始化日志管理器
    # 这是最先初始化的组件之一，确保所有后续日志都能被记录
    log_manager = LogManager()
    logger = log_manager.get_logger(__name__)
    logger.info("DeepWin 应用程序启动中...")

    # 2. 初始化核心协调器 (T类)
    # 协调器是应用逻辑层的核心，负责业务逻辑的调度和模块间的通信
    coordinator = Coordinator(log_manager=log_manager)

    # 3. 初始化主窗口 (U类)，并将协调器传递给它
    # UI 不直接处理复杂业务逻辑，而是通过协调器来触发
    main_window = MainWindowManager(coordinator=coordinator, log_manager=log_manager)
    main_window.window.show()

    # 4. 启动后台任务线程池（PySide6 自动管理）
    # QThreadPool 默认在 QApplication 启动时自动启动，这里只是明确指出其存在
    # 可以在 Coordinator 中使用 QThreadPool 来运行耗时任务
    QThreadPool.globalInstance().setMaxThreadCount(QThreadPool.globalInstance().maxThreadCount() - 1) # 留一个主线程给UI
    logger.info(f"QThreadPool 已启动，最大线程数: {QThreadPool.globalInstance().maxThreadCount()}")


    # 5. 启动应用程序事件循环
    # 应用程序会在此处等待用户交互，直到窗口关闭
    exit_code = main_window.app.exec()

    # 6. 应用程序退出前的清理工作
    coordinator.cleanup()
    QThreadPool.globalInstance().waitForDone() # 等待所有后台任务完成
    logger.info("DeepWin 应用程序已退出。")
    sys.exit(exit_code)

if __name__ == "__main__":
    # 确保 src 目录在 Python 路径中，以便正确导入模块
    # 在实际项目中，这通常通过构建系统或 IDE 配置来处理
    # 这里为了演示方便，手动添加
    if 'src' not in sys.path:
        sys.path.insert(0, 'src')
    main()