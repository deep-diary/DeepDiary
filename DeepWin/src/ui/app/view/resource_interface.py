# coding: utf-8
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QSpinBox, QTextEdit, QStackedWidget
from qfluentwidgets import (ScrollArea, FlowLayout, CardWidget, PrimaryPushButton, 
                          SearchLineEdit, ComboBox, SpinBox, TextEdit, ProgressBar,
                          TabBar, FluentIcon as FIF)
from qfluentwidgets import FluentStyleSheet

from ..common.translator import Translator


class ResourceCard(CardWidget):
    """ 资源卡片 """

    def __init__(self, name: str, resource_type: str, status: str, usage: int, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(300, 200)
        
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
        usage_layout = QHBoxLayout()
        usage_layout.setContentsMargins(0, 0, 0, 0)
        usage_layout.setSpacing(8)
        
        usage_label = QLabel(Translator().resourceUsage)
        self.usage_bar = ProgressBar()
        self.usage_bar.setValue(usage)
        
        usage_layout.addWidget(usage_label)
        usage_layout.addWidget(self.usage_bar)
        layout.addLayout(usage_layout)
        
        # 操作按钮
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

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.translator = Translator()
        self.setObjectName('resourceInterface')
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

    def setup_resource_tab(self):
        """ 设置资源列表标签页 """
        layout = QVBoxLayout(self.resource_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 搜索和筛选区域
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)

        # 搜索框
        self.resource_search = SearchLineEdit(self)
        self.resource_search.setPlaceholderText(self.translator.tr('搜索资源...'))
        search_layout.addWidget(self.resource_search)

        # 类型筛选
        self.resource_type_combo = ComboBox(self)
        self.resource_type_combo.addItems([self.translator.resourceType, '计算资源', '存储资源', '网络资源'])
        search_layout.addWidget(self.resource_type_combo)

        # 状态筛选
        self.resource_status_combo = ComboBox(self)
        self.resource_status_combo.addItems([self.translator.resourceStatus, '可用', '使用中', '维护中'])
        search_layout.addWidget(self.resource_status_combo)

        # 添加按钮
        add_button = PrimaryPushButton(self.translator.addResource)
        add_button.setIcon(FIF.ADD)
        search_layout.addWidget(add_button)

        layout.addWidget(search_widget)

        # 资源列表
        self.resource_flow_layout = FlowLayout()
        self.resource_flow_layout.setContentsMargins(0, 0, 0, 0)
        self.resource_flow_layout.setSpacing(10)

        # 添加示例资源卡片
        resources = [
            ('CPU-001', '计算资源', '可用', 30),
            ('GPU-001', '计算资源', '使用中', 80),
            ('Storage-001', '存储资源', '可用', 45),
            ('Network-001', '网络资源', '维护中', 0),
        ]
        
        for name, resource_type, status, usage in resources:
            card = ResourceCard(name, resource_type, status, usage, self)
            self.resource_flow_layout.addWidget(card)

        # 创建容器窗口部件
        container = QWidget()
        container.setLayout(self.resource_flow_layout)
        layout.addWidget(container)

    def setup_demand_tab(self):
        """ 设置需求列表标签页 """
        layout = QVBoxLayout(self.demand_tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 搜索和筛选区域
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)

        # 搜索框
        self.demand_search = SearchLineEdit(self)
        self.demand_search.setPlaceholderText(self.translator.tr('搜索需求...'))
        search_layout.addWidget(self.demand_search)

        # 类型筛选
        self.demand_type_combo = ComboBox(self)
        self.demand_type_combo.addItems([self.translator.demandType, '计算需求', '存储需求', '网络需求'])
        search_layout.addWidget(self.demand_type_combo)

        # 优先级筛选
        self.demand_priority_combo = ComboBox(self)
        self.demand_priority_combo.addItems([self.translator.demandPriority, '高', '中', '低'])
        search_layout.addWidget(self.demand_priority_combo)

        # 添加按钮
        add_button = PrimaryPushButton(self.translator.addDemand)
        add_button.setIcon(FIF.ADD)
        search_layout.addWidget(add_button)

        layout.addWidget(search_widget)

        # 需求列表
        self.demand_flow_layout = FlowLayout()
        self.demand_flow_layout.setContentsMargins(0, 0, 0, 0)
        self.demand_flow_layout.setSpacing(10)

        # 添加示例需求卡片
        demands = [
            ('训练任务-001', '计算需求', '高', '进行中'),
            ('数据备份-001', '存储需求', '中', '等待中'),
            ('模型部署-001', '网络需求', '高', '已完成'),
            ('数据同步-001', '网络需求', '低', '已取消'),
        ]
        
        for title, demand_type, priority, status in demands:
            card = DemandCard(title, demand_type, priority, status, self)
            self.demand_flow_layout.addWidget(card)

        # 创建容器窗口部件
        container = QWidget()
        container.setLayout(self.demand_flow_layout)
        layout.addWidget(container) 