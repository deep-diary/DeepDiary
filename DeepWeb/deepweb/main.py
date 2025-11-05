# main.py
# DeepWeb 应用程序入口

import sys
from pathlib import Path

# 添加项目根目录到路径，支持直接运行 main.py
# 获取当前文件的父目录的父目录（DeepWeb 目录）
# 例如：/home/liyun.xu/DeepDiary/DeepWeb/deepweb/main.py -> /home/liyun.xu/DeepDiary/DeepWeb
project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 导入 DeepWeb 核心组件
from deepweb.app_logic.core_manager.coordinator import Coordinator
from deepweb.data_management.log_manager import LogManager
from deepweb.ui.ui_manager import UIManager
import logging
import signal
import sys

# 全局变量，用于Gradio热重载
demo = None
coordinator = None  # 全局变量，用于信号处理


def signal_handler(signum, frame):
    """
    信号处理器，用于优雅地关闭应用程序
    
    Args:
        signum: 信号编号
        frame: 当前堆栈帧
    """
    print("\n收到中断信号，正在关闭应用程序...")
    if coordinator:
        try:
            coordinator.cleanup()
        except Exception as e:
            print(f"清理资源时出错: {e}")
    sys.exit(0)


def main():
    """
    DeepWeb 应用程序主入口。
    
    初始化流程：
    1. 初始化日志管理器（最先初始化，确保所有后续日志都能被记录）
    2. 初始化核心协调器（负责业务逻辑的调度和模块间的通信）
    3. 初始化并启动 UI 管理器（构建并启动 Gradio 界面）
    """
    global coordinator, demo

    # 注册信号处理器（支持 Ctrl+C）
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 1. 初始化日志管理器（控制台与文件均输出 INFO 级别）
        log_manager = LogManager(console_level=logging.INFO, file_level=logging.INFO)
        logger = log_manager.get_logger(__name__)
        logger.info("DeepWeb 应用程序启动中...")

        # 2. 初始化核心协调器
        # 协调器是应用逻辑层的核心，负责业务逻辑的调度和模块间的通信
        coordinator = Coordinator(log_manager=log_manager)

        # 3. 通过协调器获取并启动 UI（协调器是最高层，统一管理 MQTT 与 UI）
        ui_manager = coordinator.ui_manager
        
        # 获取demo对象并暴露为模块级变量（用于Gradio热重载）
        demo = ui_manager.get_app()
        
        logger.info("DeepWeb 应用程序已启动，启动 UI...")
        logger.info(f"访问地址: http://localhost:{ui_manager.port}")
        logger.info("按 Ctrl+C 停止服务")
        
        # launch() 会阻塞直到服务停止
        ui_manager.launch()
        
    except KeyboardInterrupt:
        print("\n收到键盘中断信号，正在关闭应用程序...")
        if coordinator:
            try:
                coordinator.cleanup()
            except Exception as e:
                print(f"清理资源时出错: {e}")
    except Exception as e:
        print(f"应用程序运行时出错: {e}")
        import traceback
        traceback.print_exc()
        if coordinator:
            try:
                coordinator.cleanup()
            except Exception as cleanup_error:
                print(f"清理资源时出错: {cleanup_error}")
        sys.exit(1)


if __name__ == "__main__":
    main()