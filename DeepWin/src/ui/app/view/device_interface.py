# coding: utf-8
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QComboBox, QSpinBox, QTextEdit, QStackedWidget)
from qfluentwidgets import (ScrollArea, FlowLayout, CardWidget, PrimaryPushButton, 
                          SearchLineEdit, ComboBox, SpinBox, TextEdit, FluentIcon as FIF,
                          Pivot, NavigationItemPosition, InfoBar)
from qfluentwidgets import FluentStyleSheet

from ..common.translator import Translator
from .gallery_interface import GalleryInterface
from .device_pages import DeepMotorPage, DeepArmPage, DeepToyPage, SerialConfigWidget

class DeviceCard(CardWidget):
    """ 设备卡片 """

    def __init__(self, name: str, device_type: str, status: str, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(300, 150)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # 设备名称
        name_label = QLabel(name)
        name_label.setObjectName('nameLabel')
        layout.addWidget(name_label)
        
        # 设备类型
        type_label = QLabel(device_type)
        type_label.setObjectName('typeLabel')
        layout.addWidget(type_label)
        
        # 设备状态
        status_label = QLabel(status)
        status_label.setObjectName('statusLabel')
        layout.addWidget(status_label)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        
        control_button = PrimaryPushButton(Translator().tr('控制'))
        button_layout.addWidget(control_button)
        layout.addLayout(button_layout)


# class SerialConfigWidget(QWidget):
#     """串口配置组件"""
#     serial_connect_requested = Signal(str, int)  # 串口名, 波特率

#     def __init__(self, parent=None):
#         super().__init__(parent=parent)
#         self.setup_ui()

#     def setup_ui(self):
#         layout = QVBoxLayout(self)
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.setSpacing(10)

#         # 串口选择
#         port_layout = QHBoxLayout()
#         port_label = QLabel('串口:')
#         self.port_combo = ComboBox()
#         self.refresh_button = PrimaryPushButton('刷新')
#         port_layout.addWidget(port_label)
#         port_layout.addWidget(self.port_combo)
#         port_layout.addWidget(self.refresh_button)
#         port_layout.addStretch()

#         # 波特率选择
#         baud_layout = QHBoxLayout()
#         baud_label = QLabel('波特率:')
#         self.baud_combo = ComboBox()
#         self.baud_combo.addItems(['9600', '19200', '38400', '57600', '115200'])
#         self.baud_combo.setCurrentText('115200')
#         baud_layout.addWidget(baud_label)
#         baud_layout.addWidget(self.baud_combo)
#         baud_layout.addStretch()

#         # 连接按钮
#         self.connect_button = PrimaryPushButton('连接')
        
#         layout.addLayout(port_layout)
#         layout.addLayout(baud_layout)
#         layout.addWidget(self.connect_button)
#         layout.addStretch()

#         # 连接信号
#         self.refresh_button.clicked.connect(self.refresh_ports)
#         self.connect_button.clicked.connect(self.connect_serial)

#     def refresh_ports(self):
#         """刷新串口列表"""
#         # TODO: 实现串口列表刷新逻辑
#         pass

#     def connect_serial(self):
#         """连接串口"""
#         port = self.port_combo.currentText()
#         baud = int(self.baud_combo.currentText())
#         self.serial_connect_requested.emit(port, baud)

class DeviceInterface(GalleryInterface):
    """ 设备控制界面 """
    ui_device_start_button = Signal(str, str)
    ui_device_stop_button = Signal(str, str)
    ui_device_reset_button = Signal(str, str)
    ui_device_command = Signal(str, str)  # 设备命令信号
    ui_request_history_data = Signal(str, str)  # 请求历史数据信号 (设备名, 参数名)
    # ui_serial_connect = Signal(str, int)  # 串口连接信号

    def __init__(self, parent=None):
        self.translator = Translator()

        super().__init__(
            title=self.translator.device,
            subtitle='qfluentwidgets.components.device_interface',
            parent=parent
        )
   
        self.setObjectName('deviceInterface')
        
        # 创建各个页面实例
        self.deep_motor_page = None
        self.deep_arm_page = None
        self.deep_toy_page = None
        
        self.setup_ui()

    def setup_ui(self):
        """ 初始化界面 """
        # 创建主窗口部件
        self.view = QWidget(self)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

        # 创建主布局
        self.vBoxLayout = QVBoxLayout(self.view)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 20)
        self.vBoxLayout.setSpacing(10)

        # 创建串口配置组件
        self.serial_config = SerialConfigWidget()
        self.vBoxLayout.addWidget(self.serial_config)

        # 创建顶部导航
        self.pivot = Pivot(self)
        self.pivot.setFixedWidth(600)

        # 创建堆叠窗口部件
        self.stackWidget = QStackedWidget(self)

        # 创建并添加页面到堆叠窗口
        self._create_pages()

        # 添加导航项
        self.addSubInterface(self.deep_motor_page, 'deep_motor', 'DeepMotor')
        self.addSubInterface(self.deep_arm_page, 'deep_arm', 'DeepArm')
        self.addSubInterface(self.deep_toy_page, 'deep_toy', 'DeepToy')

        # 创建垂直布局
        self.vBoxLayout.addWidget(self.pivot, 0, Qt.AlignLeft)
        self.vBoxLayout.addWidget(self.stackWidget)

        # 创建状态栏
        self.status_bar = QLabel("就绪")
        self.status_bar.setObjectName('statusBar')
        self.status_bar.setAlignment(Qt.AlignCenter)
        self.status_bar.setStyleSheet("""
            QLabel#statusBar {
                background-color: #f3f3f3;
                padding: 8px;
                border-top: 1px solid #e0e0e0;
                color: #606060;
            }
        """)
        self.vBoxLayout.addWidget(self.status_bar)

        # 连接信号
        self.stackWidget.currentChanged.connect(self.onCurrentIndexChanged)
        # self.serial_config.serial_connect_requested.connect(self.ui_serial_connect)

        # 设置默认页面
        self.stackWidget.setCurrentWidget(self.deep_motor_page)
        self.pivot.setCurrentItem(self.deep_motor_page.objectName())

    def _create_pages(self):
        """创建并初始化所有页面"""

        # 创建新的页面实例
        self.deep_motor_page = DeepMotorPage()
        self.deep_arm_page = DeepArmPage()
        self.deep_toy_page = DeepToyPage()

        # 连接信号
        self.deep_motor_page.ui_deepmotor_command.connect(self.ui_device_command)
        self.deep_motor_page.request_history_data.connect(self.ui_request_history_data)
        self.deep_arm_page.ui_device_command.connect(self.ui_device_command)
        self.deep_toy_page.ui_device_command.connect(self.ui_device_command)

        # 添加页面到堆叠窗口
        self.stackWidget.addWidget(self.deep_motor_page)
        self.stackWidget.addWidget(self.deep_arm_page)
        self.stackWidget.addWidget(self.deep_toy_page)

    def addSubInterface(self, widget: QWidget, objectName: str, text: str):
        """添加子界面"""
        widget.setObjectName(objectName)
        self.stackWidget.addWidget(widget)
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackWidget.setCurrentWidget(widget)
        )

    def onCurrentIndexChanged(self, index):
        """当前页面改变处理"""
        widget = self.stackWidget.widget(index)
        self.pivot.setCurrentItem(widget.objectName())

    def update_motor_history_data(self, history_data):
        """更新电机历史数据"""
        if self.deep_motor_page:
            self.deep_motor_page.update_history_curve(history_data)
        