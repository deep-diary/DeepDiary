"""
GUI 管理器
负责管理应用程序的 GUI 相关功能
"""

import os
import sys
from typing import Tuple
from PySide6.QtCore import Qt, QTranslator
from PySide6.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from app.common.config import cfg
from app.view.main_window import MainWindow

class GUIManager:
    """GUI 管理器类"""
    
    def __init__(self):
        self._app = None
        self._deepwin_app = None
        self._main_window = None
    
    def initialize(self) -> Tuple[QApplication, MainWindow]:
        """初始化 GUI 环境
        
        Returns:
            tuple: (QApplication, MainWindow)
        """
        # 创建 Qt 应用程序
        self._app = QApplication(sys.argv)
        self._app.setAttribute(Qt.AA_DontCreateNativeWidgetSiblings)
        
        # 配置 DPI 缩放
        if cfg.get(cfg.dpiScale) != "Auto":
            os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
            os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))
        
        
        # 配置国际化
        locale = cfg.get(cfg.language).value
        translator = FluentTranslator(locale)
        galleryTranslator = QTranslator()
        galleryTranslator.load(locale, "gallery", ".", ":/gallery/i18n")
        
        self._app.installTranslator(translator)
        self._app.installTranslator(galleryTranslator)
        
        # 创建主窗口
        self._main_window = MainWindow()
        
        return self._app, self._main_window
    
    def show_main_window(self):
        """显示主窗口"""
        if self._main_window:
            self._main_window.show()
    
    def run(self):
        """运行 GUI 应用程序
        
        Returns:
            int: 应用程序退出码
        """
        self.show_main_window()
        self._app.exec() 
    

gui_manager = GUIManager()
gui_manager.initialize()
gui_manager.run()
print("GUI 应用程序已启动")