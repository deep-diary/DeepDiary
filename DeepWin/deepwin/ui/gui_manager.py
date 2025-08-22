# src/ui/main_window.py
# 主窗口 (U类)
# 负责界面展示和用户交互，通过信号与协调器通信。


# 导入协调器（T类）以建立通信连接
from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager

import os
import sys

from PySide6.QtCore import Qt, QTranslator, QObject, Signal, Slot, QTimer, QCoreApplication
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from deepwin.ui.app.common.config import cfg
from deepwin.ui.app.view.main_window import MainWindow
from deepwin.ui.app.common.style_sheet import StyleSheet





class GuiManager(): 
    """
    DeepWin 应用程序的主窗口界面。
    负责 UI 的展示和用户输入，通过信号与 Coordinator 交互。
    """

    # # 定义可以向 Coordinator 发射的信号
    # process_image_request = Signal(str) # 请求处理图像，传递文件路径
    # match_resource_request = Signal(float, float) # 请求匹配资源，传递经纬度
    # device_control_request = Signal(str, str) # 请求控制设备，传递设备ID和命令


    def __init__(self, log_manager: LogManager, config_manager: ConfigManager):
        self.logger = log_manager.get_logger(__name__)
        self.log_manager = log_manager
        self.config_manager = config_manager
        self.logger.info("GuiManager: 初始化中...")


        # enable dpi scale
        if cfg.get(cfg.dpiScale) != "Auto":
            os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
            os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))
        
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication(sys.argv)

        # 初始化UI
        self.window = self.init_ui()

        self.logger.info("GuiManager: 初始化完成。")

    def init_ui(self) -> MainWindow:
        """
        初始化用户界面元素和布局。
        """

        # internationalization
        locale = cfg.get(cfg.language).value
        translator = FluentTranslator(locale)
        galleryTranslator = QTranslator()
        galleryTranslator.load(locale, "gallery", ".", ":/gallery/i18n")

        self.app.installTranslator(translator)
        self.app.installTranslator(galleryTranslator)

        # create main window
        window = MainWindow(log_manager=self.log_manager, config_manager=self.config_manager)
        
        # 启用无边框窗口模式
        # window.setWindowFlags(window.windowFlags() | Qt.FramelessWindowHint)
        # 启用亚克力背景
        # window.setMicaEffectEnabled(True)

        return window


    def exec(self):
        """
        启动应用程序事件循环
        """
        return self.app.exec() 

    def closeEvent(self, event):
        """
        重写 closeEvent，确保应用程序退出前进行清理。
        """
        self.logger.info("MainWindow: 窗口关闭事件。")
        # 这里可以放置额外的确认逻辑或直接允许关闭
        event.accept()


    def cleanup(self):
        """
        清理资源。
        """
        self.logger.info("GuiManager: 清理中...")
        # self.window.close()
        # self.app.quit()
        self.logger.info("GuiManager: 清理完成。")


    def select_deepmotor_trajectory(self, trajectory_name: str):
        """
        在 DeepMotor 页面的下拉框中选中指定的轨迹。
        """
        # 检查UI是否完全初始化
        if not hasattr(self.window, 'deviceInterface'):
            self.logger.warning("GuiManager: deviceInterface 尚未初始化")
            return False
        
        deep_motor_page = self.window.deviceInterface.get_deep_motor_page() if hasattr(self.window.deviceInterface, 'get_deep_motor_page') else None
        if not deep_motor_page:
            self.logger.warning("GuiManager: deep_motor_page 尚未初始化")
            return False
        
        # 检查轨迹下拉框是否存在
        if not hasattr(deep_motor_page, 'trajectory_combo'):
            self.logger.warning("GuiManager: trajectory_combo 尚未初始化")
            return False
        
        # 执行轨迹选择
        deep_motor_page.select_trajectory(trajectory_name)
        self.logger.info(f"GuiManager: 请求UI选中轨迹 '{trajectory_name}'")
        return True