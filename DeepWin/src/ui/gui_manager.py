# src/ui/main_window.py
# 主窗口 (U类)
# 负责界面展示和用户交互，通过信号与协调器通信。


# 导入协调器（T类）以建立通信连接
from src.data_management.log_manager import LogManager

import os
import sys

from PySide6.QtCore import Qt, QTranslator
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from src.ui.app.common.config import cfg
from src.ui.app.view.main_window import MainWindow

from PySide6.QtCore import QObject, Signal, Slot



# enable dpi scale
if cfg.get(cfg.dpiScale) != "Auto":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))


class GuiManager(): 
    """
    DeepWin 应用程序的主窗口界面。
    负责 UI 的展示和用户输入，通过信号与 Coordinator 交互。
    """

    # # 定义可以向 Coordinator 发射的信号
    # process_image_request = Signal(str) # 请求处理图像，传递文件路径
    # match_resource_request = Signal(float, float) # 请求匹配资源，传递经纬度
    # device_control_request = Signal(str, str) # 请求控制设备，传递设备ID和命令


    def __init__(self, log_manager: LogManager):
        self.logger = log_manager.get_logger(__name__)
        self.logger.info("GuiManager: 初始化中...")

        self.app = QApplication(sys.argv)
        self.app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
        self.window = self.init_ui()

        self.logger.info("GuiManager: 初始化完成。")

    def init_ui(self):
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
        window = MainWindow()
        return window


    # def _connect_signals(self):
    #     """
    #     连接 UI 信号到协调器 (T类) 的槽函数，以及连接协调器信号到 UI 槽函数。
    #     """
    #     # UI -> Coordinator 信号
    #     # self.window.process_image_button.clicked.connect(
    #     #     lambda: self.process_image_request.emit(self.image_path_input.text())
    #     # )
    #     # self.window.send_command_button.clicked.connect(
    #     #     lambda: self.device_control_request.emit(self.device_id_input.text(), self.command_input.text())
    #     # )
    #     # 可以连接更多 UI 信号，例如资源匹配界面的按钮点击


    #     # Coordinator -> UI 信号 (用于更新 UI)
    #     self.coordinator.image_processing_started.connect(self._on_image_processing_started)
    #     self.coordinator.image_processing_finished.connect(self._on_image_processing_finished)
    #     self.coordinator.image_processing_error.connect(self._on_image_processing_error)
    #     self.coordinator.device_status_updated.connect(self._on_device_status_updated) # 假设设备状态由Coordinator转发
    #     self.coordinator.resource_matched.connect(self._on_resource_matched) # 假设资源匹配结果由Coordinator转发



    def closeEvent(self, event):
        """
        重写 closeEvent，确保应用程序退出前进行清理。
        """
        self.logger.info("MainWindow: 窗口关闭事件。")
        # 这里可以放置额外的确认逻辑或直接允许关闭
        event.accept()