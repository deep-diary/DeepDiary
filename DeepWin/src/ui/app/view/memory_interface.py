# coding: utf-8
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QDateEdit, QLineEdit
from qfluentwidgets import (ScrollArea, FlowLayout, CardWidget, PrimaryPushButton, 
                          SearchLineEdit, ComboBox, DateEdit, FluentIcon as FIF)
from qfluentwidgets import FluentStyleSheet
from PySide6.QtCore import Signal
from ..common.translator import Translator
import os
from PySide6.QtCore import Slot
from src.data_management.log_manager import LogManager


class MemoryCard(CardWidget):
    """ 记忆卡片 """

    def __init__(self, title: str, content: str, parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(300, 200)
        
        # 创建布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)
        
        # 标题
        title_label = QLabel(title)
        title_label.setObjectName('titleLabel')
        layout.addWidget(title_label)
        
        # 内容
        content_label = QLabel(content)
        content_label.setObjectName('contentLabel')
        content_label.setWordWrap(True)
        layout.addWidget(content_label)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(8)
        
        edit_button = PrimaryPushButton(Translator().tr('编辑'))
        delete_button = PrimaryPushButton(Translator().tr('删除'))
        button_layout.addWidget(edit_button)
        button_layout.addWidget(delete_button)
        layout.addLayout(button_layout)


class MemoryInterface(ScrollArea):
    """ 记忆管理界面 """

    process_image_request = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.log_manager = LogManager(log_file_name="memory_interface")
        self.logger = self.log_manager.get_logger(__name__)
        self.translator = Translator()
        self.setObjectName('memoryInterface')
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

        # 创建搜索和筛选区域
        self.create_search_widget()
        
        # 创建记忆列表
        self.create_memory_list()

    def create_search_widget(self):
        """ 创建搜索和筛选区域 """
        search_widget = QWidget()
        search_layout = QHBoxLayout(search_widget)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(10)

        # 搜索框
        self.search_edit = SearchLineEdit(self)
        self.search_edit.setPlaceholderText(self.translator.memorySearch)
        search_layout.addWidget(self.search_edit)

        # 类型筛选
        self.type_combo = ComboBox(self)
        self.type_combo.addItems([self.translator.memoryType, '视觉记忆', '听觉记忆', '触觉记忆'])
        search_layout.addWidget(self.type_combo)

        # 日期筛选
        self.date_edit = DateEdit(self)
        self.date_edit.setDisplayFormat('yyyy-MM-dd')
        search_layout.addWidget(self.date_edit)

        # 添加按钮
        add_button = PrimaryPushButton(self.translator.tr('添加记忆'))
        add_button.setIcon(FIF.ADD)
        search_layout.addWidget(add_button)

        self.vBoxLayout.addWidget(search_widget)

        # 绑定信号
        add_button.clicked.connect(self.add_memory)


    def add_memory(self):
        """ 添加记忆 """
        project_root = 'd:/BlueDoc/DeepDiary'
        image_path = os.path.join(project_root, 'DeepWin', 'media', 'images', 'IMG_20210905_163757.jpg')
        print(f"MemoryInterface: 添加记忆，路径：{image_path}")
        self.process_image_request.emit(image_path)


        

    def create_memory_list(self):
        """ 创建记忆列表 """
        # 创建流式布局
        self.flow_layout = FlowLayout()
        self.flow_layout.setContentsMargins(0, 0, 0, 0)
        self.flow_layout.setSpacing(10)

        # 添加示例记忆卡片
        for i in range(10):
            card = MemoryCard(
                f'记忆 {i+1}',
                '这是一段示例记忆内容，描述了某个具体的场景或事件。',
                self
            )
            self.flow_layout.addWidget(card)

        # 创建容器窗口部件
        container = QWidget()
        container.setLayout(self.flow_layout)
        self.vBoxLayout.addWidget(container) 


    @Slot(str)
    def _on_image_processing_started(self, image_path: str):
        """
        槽函数：当图像处理任务开始时，更新 UI 状态。
        """
        self.logger.info(f"UI收到图像处理开始：{image_path}")


    @Slot(str, str)
    def _on_image_processing_finished(self, image_path: str, result: str):
        """
        槽函数：当图像处理任务完成时，更新 UI 结果。
        """
        self.logger.info(f"UI收到图像处理完成：{image_path}，结果：{result}")


    @Slot(str, str)
    def _on_image_processing_error(self, image_path: str, error_msg: str):
        """
        槽函数：当图像处理任务出错时，更新 UI 错误信息。
        """
        self.logger.error(f"UI收到图像处理失败：{image_path}，错误：{error_msg}")