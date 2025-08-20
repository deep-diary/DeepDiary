# main.py
# DeepWin 应用程序入口

import sys
import threading
import time
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QThreadPool # 用于管理后台任务

# 配置matplotlib（必须在导入其他模块之前）
from deepwin.app_logic.device_logic_manager.devices.deep_motor.matplotlib_config import configure_matplotlib_globally
configure_matplotlib_globally()

# 导入 DeepWin 核心组件
from deepwin.app_logic.core_manager.coordinator import Coordinator
from deepwin.data_management.log_manager import LogManager # 导入日志管理器

def cleanup_threads():
    """清理所有非主线程"""
    logger = LogManager().get_logger(__name__)
    
    # 获取所有活跃线程
    active_threads = threading.enumerate()
    main_thread = threading.main_thread()
    
    logger.info(f"清理前活跃线程数量: {len(active_threads)}")
    
    # 等待非主线程完成
    for thread in active_threads:
        if thread != main_thread and thread.is_alive():
            logger.info(f"等待线程完成: {thread.name} (ID: {thread.ident})")
            thread.join(timeout=3)
            if thread.is_alive():
                logger.warning(f"线程 {thread.name} 未能在3秒内完成")
    
    # 再次检查线程状态
    remaining_threads = [t for t in threading.enumerate() if t != main_thread and t.is_alive()]
    if remaining_threads:
        logger.warning(f"仍有 {len(remaining_threads)} 个线程未完成")
        for thread in remaining_threads:
            logger.warning(f"  - {thread.name} (ID: {thread.ident})")
    else:
        logger.info("所有非主线程已清理完成")

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
    coordinator.start_application() # 新增：自动启动应用相关服务

    # 4. 启动后台任务线程池（PySide6 自动管理）
    # QThreadPool 默认在 QApplication 启动时自动启动，这里只是明确指出其存在
    # 可以在 Coordinator 中使用 QThreadPool 来运行耗时任务
    QThreadPool.globalInstance().setMaxThreadCount(QThreadPool.globalInstance().maxThreadCount() - 1) # 留一个主线程给UI
    logger.info(f"QThreadPool 已启动，最大线程数: {QThreadPool.globalInstance().maxThreadCount()}")

    # 5. 启动应用程序事件循环
    # 应用程序会在此处等待用户交互，直到窗口关闭
    coordinator.gui_manager.window.show()
    exit_code = coordinator.gui_manager.exec()

    # 6. 应用程序退出前的清理工作
    logger.info("开始应用程序清理...")
    
    # 清理协调器
    coordinator.cleanup()
    
    # 等待QThreadPool任务完成
    logger.info("等待QThreadPool任务完成...")
    try:
        # PySide6的waitForDone()不支持timeout参数，使用无参数版本
        QThreadPool.globalInstance().waitForDone()
        logger.info("QThreadPool任务已完成")
    except Exception as e:
        logger.warning(f"等待QThreadPool任务完成时出现异常: {e}")
    
    # 清理线程
    cleanup_threads()
    
    logger.info("DeepWin 应用程序已退出。")
    sys.exit(exit_code)

if __name__ == "__main__":
    # 不再需要手动添加路径，包安装后会自动处理
    main()