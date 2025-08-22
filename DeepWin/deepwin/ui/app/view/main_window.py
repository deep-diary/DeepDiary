# coding: utf-8
from typing import List
from PySide6.QtCore import Qt, Signal, QEasingCurve, QUrl, QSize, QTimer
from PySide6.QtGui import QIcon, QDesktopServices, QColor
from PySide6.QtWidgets import QApplication, QHBoxLayout, QFrame, QWidget, QLabel, QVBoxLayout, QMainWindow

from qfluentwidgets import (NavigationAvatarWidget, NavigationItemPosition, MessageBox, FluentWindow,
                            SplashScreen, SystemThemeListener, isDarkTheme)
from qfluentwidgets import FluentIcon as FIF

from .gallery_interface import GalleryInterface
from .home_interface import HomeInterface
from .memory_interface import MemoryInterface
from .devices.device_interface import DeviceInterface
from .resource_interface import ResourceInterface
from .basic_input_interface import BasicInputInterface
from .date_time_interface import DateTimeInterface
from .dialog_interface import DialogInterface
from .layout_interface import LayoutInterface
from .icon_interface import IconInterface
from .material_interface import MaterialInterface
from .menu_interface import MenuInterface
from .navigation_view_interface import NavigationViewInterface
from .scroll_interface import ScrollInterface
from .status_info_interface import StatusInfoInterface
from .setting_interface import SettingInterface
from .text_interface import TextInterface
from .view_interface import ViewInterface
from ..common.config import ZH_SUPPORT_URL, EN_SUPPORT_URL, cfg
from ..common.icon import Icon
from ..common.signal_bus import signalBus
from ..common.translator import Translator
from ..common import resource
from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager


class MainWindow(FluentWindow):

    def __init__(self, log_manager: LogManager, config_manager: ConfigManager):
        super().__init__()
        self.log_manager = log_manager
        self.logger = self.log_manager.get_logger(__name__)
        self.config_manager = config_manager
        
        self.logger.info("主窗口初始化开始")
        self.initWindow()

        # create system theme listener
        self.themeListener = SystemThemeListener(self)

        # create sub interface
        self.homeInterface = HomeInterface(self)
        self.memoryInterface = MemoryInterface(log_manager=self.log_manager, config_manager=self.config_manager, parent=self)
        self.deviceInterface = DeviceInterface(log_manager=self.log_manager, config_manager=self.config_manager, parent=self)
        self.resourceInterface = ResourceInterface(log_manager=self.log_manager, config_manager=self.config_manager, parent=self)
        self.iconInterface = IconInterface(self)
        self.basicInputInterface = BasicInputInterface(self)
        self.dateTimeInterface = DateTimeInterface(self)
        self.dialogInterface = DialogInterface(self)
        self.layoutInterface = LayoutInterface(self)
        self.menuInterface = MenuInterface(self)
        self.materialInterface = MaterialInterface(self)
        self.navigationViewInterface = NavigationViewInterface(self)
        self.scrollInterface = ScrollInterface(self)
        self.statusInfoInterface = StatusInfoInterface(self)
        self.settingInterface = SettingInterface(self)
        self.textInterface = TextInterface(self)
        self.viewInterface = ViewInterface(self)

        # enable acrylic effect
        self.navigationInterface.setAcrylicEnabled(True)

        self.connectSignalToSlot()

        # add items to navigation interface
        self.initNavigation()

        # add status bar
        self.create_status_bar()

        self.splashScreen.finish()

        # start theme listener
        self.themeListener.start()
        
        self.logger.info("主窗口初始化完成")

    def connectSignalToSlot(self):
        signalBus.micaEnableChanged.connect(self.setMicaEffectEnabled)
        signalBus.switchToSampleCard.connect(self.switchToSample)
        signalBus.supportSignal.connect(self.onSupport)

    def initNavigation(self):
        # add navigation items
        t = Translator()
        self.addSubInterface(self.homeInterface, FIF.HOME, self.tr('Home'))
        self.addSubInterface(self.memoryInterface, FIF.PHOTO, t.memory)
        self.addSubInterface(self.deviceInterface, FIF.ROBOT, t.device)
        self.addSubInterface(self.resourceInterface, FIF.LIBRARY, t.resource)
        self.addSubInterface(self.iconInterface, Icon.EMOJI_TAB_SYMBOLS, t.icons)
        self.navigationInterface.addSeparator()

        pos = NavigationItemPosition.SCROLL
        self.addSubInterface(self.basicInputInterface, FIF.CHECKBOX,t.basicInput, pos)
        self.addSubInterface(self.dateTimeInterface, FIF.DATE_TIME, t.dateTime, pos)
        self.addSubInterface(self.dialogInterface, FIF.MESSAGE, t.dialogs, pos)
        self.addSubInterface(self.layoutInterface, FIF.LAYOUT, t.layout, pos)
        self.addSubInterface(self.materialInterface, FIF.PALETTE, t.material, pos)
        self.addSubInterface(self.menuInterface, Icon.MENU, t.menus, pos)
        self.addSubInterface(self.navigationViewInterface, FIF.MENU, t.navigation, pos)
        self.addSubInterface(self.scrollInterface, FIF.SCROLL, t.scroll, pos)
        self.addSubInterface(self.statusInfoInterface, FIF.CHAT, t.statusInfo, pos)
        self.addSubInterface(self.textInterface, Icon.TEXT, t.text, pos)
        self.addSubInterface(self.viewInterface, Icon.GRID, t.view, pos)

        # add custom widget to bottom
        self.navigationInterface.addItem(
            routeKey='price',
            icon=Icon.PRICE,
            text=t.price,
            onClick=self.onSupport,
            selectable=False,
            tooltip=t.price,
            position=NavigationItemPosition.BOTTOM
        )
        self.addSubInterface(
            self.settingInterface, FIF.SETTING, self.tr('Settings'), NavigationItemPosition.BOTTOM)
            
        # 设置设备页面为默认页面
        self.stackedWidget.setCurrentWidget(self.deviceInterface)
        self.navigationInterface.setCurrentItem(self.deviceInterface.objectName())
        
        self.logger.info("导航界面初始化完成，默认页面设置为设备界面")

    def initWindow(self):
        self.resize(1280, 1080)
        self.setMinimumWidth(1280)
        self.setWindowIcon(QIcon(':/gallery/images/logo.png'))
        self.setWindowTitle('DeepWin')

        self.setMicaEffectEnabled(cfg.get(cfg.micaEnabled))

        # create splash screen
        self.splashScreen = SplashScreen(self.windowIcon(), self)
        self.splashScreen.setIconSize(QSize(106, 106))
        self.splashScreen.raise_()

        desktop = QApplication.screens()[0].availableGeometry()
        w, h = desktop.width(), desktop.height()
        self.move(w//2 - self.width()//2, h//2 - self.height()//2)
        self.show()
        QApplication.processEvents()
        
        self.logger.info("主窗口UI初始化完成")

    def create_status_bar(self):
        """创建状态栏"""
        # 创建状态栏容器
        self.status_bar_container = QWidget()
        self.status_bar_container.setObjectName('statusBarContainer')
        self.status_bar_container.setFixedHeight(30)
        self.status_bar_container.setStyleSheet("""
            QWidget#statusBarContainer {
                background-color: #f5f5f5;
                border-top: 1px solid #e0e0e0;
            }
        """)
        
        # 创建状态栏布局
        status_layout = QHBoxLayout(self.status_bar_container)
        status_layout.setContentsMargins(10, 5, 10, 5)
        status_layout.setSpacing(10)
        
        # 创建状态栏标签
        self.status_bar = QLabel('就绪')
        self.status_bar.setObjectName('statusBar')
        self.status_bar.setStyleSheet("""
            QLabel#statusBar {
                color: #666666;
                font-size: 12px;
            }
        """)
        
        status_layout.addWidget(self.status_bar)
        status_layout.addStretch()
        
        # 将状态栏添加到主窗口底部
        # self.layout().addWidget(self.status_bar_container)
        self.status_bar_container.setVisible(False)
        
        self.logger.info("状态栏创建完成")

    def show_status_message(self, message: str):
        """显示状态消息"""
        if hasattr(self, 'status_bar'):
            self.status_bar.setText(message)
            if hasattr(self, 'logger'):
                self.logger.info(f"状态消息: {message}")

    def onSupport(self):
        language = cfg.get(cfg.language).value
        if language.name() == "zh_CN":
            QDesktopServices.openUrl(QUrl(ZH_SUPPORT_URL))
        else:
            QDesktopServices.openUrl(QUrl(EN_SUPPORT_URL))
        self.logger.info("打开支持页面")

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, 'splashScreen'):
            self.splashScreen.resize(self.size())

    def closeEvent(self, e):
        self.logger.info("主窗口关闭事件触发")
        self.themeListener.terminate()
        self.themeListener.deleteLater()
        super().closeEvent(e)

    def _onThemeChangedFinished(self):
        super()._onThemeChangedFinished()

        # retry
        if self.isMicaEffectEnabled():
            QTimer.singleShot(100, lambda: self.windowEffect.setMicaEffect(self.winId(), isDarkTheme()))

    def switchToSample(self, routeKey, index):
        """ switch to sample """
        interfaces = self.findChildren(GalleryInterface)
        for w in interfaces:
            if w.objectName() == routeKey:
                self.stackedWidget.setCurrentWidget(w, False)
                w.scrollToCard(index)
                self.logger.info(f"切换到示例页面: {routeKey}, 索引: {index}")
                break
