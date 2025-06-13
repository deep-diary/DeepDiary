# coding: utf-8
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSpinBox, QTextEdit
from qfluentwidgets import (ScrollArea, FlowLayout, CardWidget, PrimaryPushButton, 
                          SearchLineEdit, ComboBox, SpinBox, TextEdit, FluentIcon as FIF)
from qfluentwidgets import FluentStyleSheet

from ..common.translator import Translator


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


class DeviceInterface(ScrollArea):
    """ 设备控制界面 """
    ui_device_start_button = Signal(str, str)
    ui_device_stop_button = Signal(str, str)
    ui_device_reset_button = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.translator = Translator()
        self.setObjectName('deviceInterface')
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

        # 创建设备列表
        self.create_device_list()
        
        # 创建控制面板
        self.create_control_panel()

        # 创建状态栏
        self.status_bar = QLabel()
        self.status_bar.setObjectName('statusBar')
        self.vBoxLayout.addWidget(self.status_bar)

    def create_device_list(self):
        """ 创建设备列表 """
        # 创建流式布局
        self.flow_layout = FlowLayout()
        self.flow_layout.setContentsMargins(0, 0, 0, 0)
        self.flow_layout.setSpacing(10)

        # 添加示例设备卡片
        devices = [
            ('机械臂 A', '机械臂', '在线'),
            ('机械臂 B', '机械臂', '离线'),
            ('摄像头 A', '摄像头', '在线'),
            ('传感器 A', '传感器', '在线'),
        ]
        
        for name, device_type, status in devices:
            card = DeviceCard(name, device_type, status, self)
            self.flow_layout.addWidget(card)

        # 创建容器窗口部件
        container = QWidget()
        container.setLayout(self.flow_layout)
        self.vBoxLayout.addWidget(container)

    def create_control_panel(self):
        """ 创建控制面板 """
        control_widget = QWidget()
        control_layout = QVBoxLayout(control_widget)
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)

        # 关节控制
        joint_group = QWidget()
        joint_layout = QHBoxLayout(joint_group)
        joint_layout.setContentsMargins(0, 0, 0, 0)
        joint_layout.setSpacing(10)

        for i in range(6):
            joint_widget = QWidget()
            joint_widget_layout = QVBoxLayout(joint_widget)
            joint_widget_layout.setContentsMargins(0, 0, 0, 0)
            joint_widget_layout.setSpacing(5)

            label = QLabel(f'关节 {i+1}')
            spin_box = SpinBox()
            spin_box.setRange(-180, 180)
            spin_box.setValue(0)

            joint_widget_layout.addWidget(label)
            joint_widget_layout.addWidget(spin_box)
            joint_layout.addWidget(joint_widget)

        control_layout.addWidget(joint_group)

        # 操作按钮
        button_group = QWidget()
        button_layout = QHBoxLayout(button_group)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(10)

        start_button = PrimaryPushButton(self.translator.tr('开始'))
        stop_button = PrimaryPushButton(self.translator.tr('停止'))
        reset_button = PrimaryPushButton(self.translator.tr('重置'))

        button_layout.addWidget(start_button)
        button_layout.addWidget(stop_button)
        button_layout.addWidget(reset_button)
        button_layout.addStretch()

        control_layout.addWidget(button_group)

        # 指令控制台
        console_group = QWidget()
        console_layout = QVBoxLayout(console_group)
        console_layout.setContentsMargins(0, 0, 0, 0)
        console_layout.setSpacing(5)

        console_label = QLabel(self.translator.commandConsole)
        self.console_edit = TextEdit()
        self.console_edit.setPlaceholderText(self.translator.tr('输入指令...'))
        self.console_edit.setMaximumHeight(100)

        console_layout.addWidget(console_label)
        console_layout.addWidget(self.console_edit)

        control_layout.addWidget(console_group)

        self.vBoxLayout.addWidget(control_widget) 


        start_button.clicked.connect(self.start_button_clicked)

    def start_button_clicked(self):
        # self.logger.info("DeviceInterface: 开始按钮被点击")
        self.ui_device_start_button.emit("DeepMotor", "set_rpm(100)")