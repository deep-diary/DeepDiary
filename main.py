def main():
    """
    DeepWin 应用程序主入口。
    初始化应用，协调器，UI，并启动事件循环。
    """

    # 1. 初始化日志管理器
    log_manager = LogManager()
    logger = log_manager.get_logger(__name__)
    logger.info("DeepWin 应用程序启动中...")

    # 2. 初始化核心协调器 (T类)
    coordinator = Coordinator(log_manager=log_manager)

    # 3. 启动后台任务线程池
    QThreadPool.globalInstance().setMaxThreadCount(QThreadPool.globalInstance().maxThreadCount() - 1)
    logger.info(f"QThreadPool 已启动，最大线程数: {QThreadPool.globalInstance().maxThreadCount()}")

    # 4. 显示主窗口并启动应用程序事件循环
    coordinator.gui_manager.window.show()
    exit_code = coordinator.gui_manager.exec()

    # 5. 应用程序退出前的清理工作
    coordinator.cleanup()
    QThreadPool.globalInstance().waitForDone()
    logger.info("DeepWin 应用程序已退出。")
    sys.exit(exit_code)

if __name__ == "__main__":
    if 'src' not in sys.path:
        sys.path.insert(0, 'src')
    main() 