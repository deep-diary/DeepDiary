# src/ui/main_window.py
# 主窗口 (U类)
# 负责界面展示和用户交互，通过信号与协调器通信。


# 导入协调器（T类）以建立通信连接
from src.app_logic.core_manager.coordinator import Coordinator
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
from qfluentwidgets import InfoBar


# enable dpi scale
if cfg.get(cfg.dpiScale) != "Auto":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))


class MainWindowManager(): 
    """
    DeepWin 应用程序的主窗口界面。
    负责 UI 的展示和用户输入，通过信号与 Coordinator 交互。
    """

    # 定义可以向 Coordinator 发射的信号
    process_image_request = Signal(str) # 请求处理图像，传递文件路径
    match_resource_request = Signal(float, float) # 请求匹配资源，传递经纬度
    device_control_request = Signal(str, str) # 请求控制设备，传递设备ID和命令


    def __init__(self, coordinator: Coordinator, log_manager: LogManager):
        self.coordinator = coordinator
        self.logger = log_manager.get_logger(__name__)
        self.logger.info("MainWindow: 初始化中...")

        self.app = QApplication(sys.argv)
        self.app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
        self.window = self.init_ui()

        self._connect_signals()

        self.logger.info("MainWindow: 初始化完成。")

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


    def _connect_signals(self):
        """
        连接 UI 信号到协调器 (T类) 的槽函数，以及连接协调器信号到 UI 槽函数。
        """
        # UI -> Coordinator 信号
        # self.window.process_image_button.clicked.connect(
        #     lambda: self.process_image_request.emit(self.image_path_input.text())
        # )
        # self.window.send_command_button.clicked.connect(
        #     lambda: self.device_control_request.emit(self.device_id_input.text(), self.command_input.text())
        # )
        # 可以连接更多 UI 信号，例如资源匹配界面的按钮点击


        # Coordinator -> UI 信号 (用于更新 UI)
        self.coordinator.image_processing_started.connect(self._on_image_processing_started)
        self.coordinator.image_processing_finished.connect(self._on_image_processing_finished)
        self.coordinator.image_processing_error.connect(self._on_image_processing_error)
        self.coordinator.device_status_updated.connect(self._on_device_status_updated) # 假设设备状态由Coordinator转发
        self.coordinator.resource_matched.connect(self._on_resource_matched) # 假设资源匹配结果由Coordinator转发


    @Slot(str)
    def _on_image_processing_started(self, image_path: str):
        """
        槽函数：当图像处理任务开始时，更新 UI 状态。
        """
        # self.image_result_label.setText(f"正在处理图片: {image_path}...")
        # self.process_image_button.setEnabled(False) # 禁用按钮避免重复点击
        InfoBar.info(
            title="通知",
            content=f"已开始处理图片: {image_path}",
            parent=self
        )


    @Slot(str, str)
    def _on_image_processing_finished(self, image_path: str, result: str):
        """
        槽函数：当图像处理任务完成时，更新 UI 结果。
        """
        # self.image_result_label.setText(f"图片处理完成！路径：{image_path}，结果：{result}")
        # self.process_image_button.setEnabled(True) # 重新启用按钮
        InfoBar.success(
            title="成功",
            content=f"图片处理完成: {image_path}",
            parent=self
        )


    @Slot(str, str)
    def _on_image_processing_error(self, image_path: str, error_msg: str):
        """
        槽函数：当图像处理任务出错时，更新 UI 错误信息。
        """
        # self.image_result_label.setText(f"图片处理失败！路径：{image_path}，错误：{error_msg}")
        # self.process_image_button.setEnabled(True) # 重新启用按钮
        InfoBar.error(
            title="错误",
            content=f"图片处理失败: {image_path}，错误：{error_msg}",
            parent=self
        )


    @Slot(dict)
    def _on_device_status_updated(self, status_data: dict):
        """
        槽函数：更新设备状态信息到 UI (简化示例，实际会更新设备控制界面的特定区域)。
        """
        self.logger.info(f"UI收到设备状态更新：{status_data}")
        # 实际代码会更新设备控制界面上的 QLabel, ProgressBar, Chart 等
        # self.statusBar.showMessage(f"设备 {status_data.get('device_id', '未知')} 状态：{status_data.get('status', '未知')}")


    @Slot(dict)
    def _on_resource_matched(self, match_result: dict):
        """
        槽函数：显示资源匹配结果 (简化示例，实际会更新资源/需求界面的匹配建议区)。
        """
        self.logger.info(f"UI收到资源匹配结果：{match_result}")
        matched_item = match_result.get('matched_item', '未知')
        score = match_result.get('score', 0)
        InfoBar.success(
            title="资源匹配",
            content=f"找到匹配资源: {matched_item}，匹配度: {score:.2f}",
            parent=self
        )

    def closeEvent(self, event):
        """
        重写 closeEvent，确保应用程序退出前进行清理。
        """
        self.logger.info("MainWindow: 窗口关闭事件。")
        # 这里可以放置额外的确认逻辑或直接允许关闭
        event.accept()