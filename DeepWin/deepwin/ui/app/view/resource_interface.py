# coding: utf-8
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSpinBox, QTextEdit, QStackedWidget
from qfluentwidgets import (ScrollArea, FlowLayout, CardWidget, PrimaryPushButton, 
                          SearchLineEdit, ComboBox, SpinBox, TextEdit, ProgressBar,
                          TabBar, FluentIcon as FIF)
from qfluentwidgets import FluentStyleSheet

from ..common.translator import Translator
from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager


class ResourceCard(CardWidget):
    """ 资源卡片 """

    def __init__(self, name: str, resource_type: str, status: str, usage: int, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(300, 150)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # 资源名称
        name_label = QLabel(name)
        name_label.setObjectName('nameLabel')
        layout.addWidget(name_label)
        
        # 资源类型
        type_label = QLabel(resource_type)
        type_label.setObjectName('typeLabel')
        layout.addWidget(type_label)
        
        # 资源状态
        status_label = QLabel(status)
        status_label.setObjectName('statusLabel')
        layout.addWidget(status_label)
        
        # 使用率
        usage_label = QLabel(f'使用率: {usage}%')
        usage_label.setObjectName('usageLabel')
        layout.addWidget(usage_label)
        
        # 控制按钮
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        
        edit_button = PrimaryPushButton(Translator().editResource)
        delete_button = PrimaryPushButton(Translator().deleteResource)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        layout.addLayout(button_layout)


class DemandCard(CardWidget):
    """ 需求卡片 """

    def __init__(self, title: str, demand_type: str, priority: str, status: str, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(300, 200)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # 需求标题
        title_label = QLabel(title)
        title_label.setObjectName('titleLabel')
        layout.addWidget(title_label)
        
        # 需求类型
        type_label = QLabel(demand_type)
        type_label.setObjectName('typeLabel')
        layout.addWidget(type_label)
        
        # 优先级
        priority_label = QLabel(f"{Translator().demandPriority}: {priority}")
        priority_label.setObjectName('priorityLabel')
        layout.addWidget(priority_label)
        
        # 状态
        status_label = QLabel(f"{Translator().demandStatus}: {status}")
        status_label.setObjectName('statusLabel')
        layout.addWidget(status_label)
        
        # 操作按钮
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        
        edit_button = PrimaryPushButton(Translator().editDemand)
        delete_button = PrimaryPushButton(Translator().deleteDemand)
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        layout.addLayout(button_layout)


class ResourceInterface(ScrollArea):
    """ 资源需求界面 """

    def __init__(self, log_manager: LogManager = None, config_manager: ConfigManager = None, parent=None):
        super().__init__(parent=parent)
        self.log_manager = log_manager
        self.logger = self.log_manager.get_logger(__name__) if self.log_manager else None
        self.config_manager = config_manager
        self.translator = Translator()
        self.setObjectName('resourceInterface')
        
        if self.logger:
            self.logger.info("资源管理界面初始化开始")
        self.setup_ui()
        if self.logger:
            self.logger.info("资源管理界面初始化完成")

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

        # 创建标签栏和堆叠窗口
        self.tab_bar = TabBar(self)
        self.stacked_widget = QStackedWidget(self)
        self.vBoxLayout.addWidget(self.tab_bar)
        self.vBoxLayout.addWidget(self.stacked_widget)

        # 添加资源列表标签页
        self.resource_tab = QWidget()
        self.stacked_widget.addWidget(self.resource_tab)
        self.tab_bar.addTab(FIF.LIBRARY, self.translator.resourceList)
        self.setup_resource_tab()

        # 添加需求列表标签页
        self.demand_tab = QWidget()
        self.stacked_widget.addWidget(self.demand_tab)
        self.tab_bar.addTab(FIF.TAG, self.translator.demandList)
        self.setup_demand_tab()

        # 连接标签切换信号
        self.tab_bar.currentChanged.connect(self.on_tab_changed)

    def on_tab_changed(self, index):
        """ 标签切换处理 """
        self.stacked_widget.setCurrentIndex(index)
        if self.logger:
            tab_names = ["资源列表", "需求列表"]
            self.logger.info(f"切换到标签页: {tab_names[index] if index < len(tab_names) else f'未知标签({index})'}")

    def setup_resource_tab(self):
        """ 设置资源列表标签页 """
        layout = QVBoxLayout(self.resource_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 创建流式布局
        flow_layout = FlowLayout()
        flow_layout.setContentsMargins(0, 0, 0, 0)
        flow_layout.setSpacing(10)

        # 添加示例资源卡片
        resources = [
            ('CPU', '计算资源', '运行中', 75),
            ('内存', '存储资源', '运行中', 60),
            ('GPU', '图形资源', '空闲', 20),
            ('网络', '网络资源', '运行中', 45),
            ('磁盘', '存储资源', '运行中', 80),
        ]

        for name, resource_type, status, usage in resources:
            card = ResourceCard(name, resource_type, status, usage, self)
            flow_layout.addWidget(card)

        # 创建容器窗口部件
        container = QWidget()
        container.setLayout(flow_layout)
        layout.addWidget(container)
        
        if self.logger:
            self.logger.info(f"资源列表标签页设置完成，添加了 {len(resources)} 个资源卡片")

    def setup_demand_tab(self):
        """ 设置需求列表标签页 """
        layout = QVBoxLayout(self.demand_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 创建流式布局
        flow_layout = FlowLayout()
        flow_layout.setContentsMargins(0, 0, 0, 0)
        flow_layout.setSpacing(10)

        # 添加示例需求卡片
        demands = [
            ('深度学习训练', '计算需求', '等待中', 90),
            ('图像处理', '图形需求', '进行中', 70),
            ('数据备份', '存储需求', '完成', 100),
            ('实时监控', '网络需求', '运行中', 85),
        ]

        for name, demand_type, status, priority in demands:
            card = ResourceCard(name, demand_type, status, priority, self)
            flow_layout.addWidget(card)

        # 创建容器窗口部件
        container = QWidget()
        container.setLayout(flow_layout)
        layout.addWidget(container)
        
        if self.logger:
            self.logger.info(f"需求列表标签页设置完成，添加了 {len(demands)} 个需求卡片") 