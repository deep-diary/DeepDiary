# coding: utf-8
from PySide6.QtCore import Qt, QSize, Signal, QTimer
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QPushButton, QComboBox, QSpinBox, QTextEdit, QStackedWidget)
from qfluentwidgets import (ScrollArea, FlowLayout, CardWidget, PrimaryPushButton, 
                          SearchLineEdit, ComboBox, SpinBox, TextEdit, FluentIcon as FIF,
                          Pivot, NavigationItemPosition, InfoBar)
from qfluentwidgets import FluentStyleSheet

from deepwin.ui.app.common.translator import Translator
from deepwin.ui.app.view.gallery_interface import GalleryInterface
from .base_device_page import SerialConfigWidget
from .device_page_manager import DevicePageManager
from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager
from deepwin.ui.app.view.devices.deep_motor.deep_motor_page import DeepMotorPage
from deepwin.ui.app.view.devices.deep_arm.deep_arm_page import DeepArmPage
from deepwin.ui.app.view.devices.deep_toy.deep_toy_page import DeepToyPage

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

class DeviceInterface(GalleryInterface):
    """ 设备控制界面 """
    ui_device_start_button = Signal(str, str)
    ui_device_stop_button = Signal(str, str)
    ui_device_reset_button = Signal(str, str)
    ui_device_command = Signal(str, str)  # 设备命令信号
    ui_request_history_data = Signal(str, str)  # 请求历史数据信号 (设备名, 参数名)

    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, parent=None):
        self.translator = Translator()
        self.log_manager = log_manager
        self.logger = self.log_manager.get_logger(__name__)
        self.config_manager = config_manager

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
        
        self.logger.info("设备界面初始化开始")
        self.setup_ui()
        self.logger.info("设备界面初始化完成")

    def setup_ui(self):
        """ 初始化界面 """
        self.logger.info("开始设置设备界面UI")
        
        # 创建主窗口部件
        self.view = QWidget(self)
        self.setWidget(self.view)
        self.setWidgetResizable(True)

        # 创建主布局
        self.vBoxLayout = QVBoxLayout(self.view)
        self.vBoxLayout.setContentsMargins(36, 20, 36, 20)
        self.vBoxLayout.setSpacing(10)

        # 创建串口配置组件
        self.serial_config = SerialConfigWidget(self.log_manager, self.config_manager)
        self.vBoxLayout.addWidget(self.serial_config)

        # 创建顶部导航
        self.pivot = Pivot(self)
        self.pivot.setFixedWidth(600)

        # 创建堆叠窗口部件
        self.stackWidget = QStackedWidget(self)

        # 自动创建并添加设备页面
        self._create_pages()

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

        # 设置默认页面（如果有设备页面的话）
        if self.deep_motor_page:
            self.stackWidget.setCurrentWidget(self.deep_motor_page)
            self.pivot.setCurrentItem(self.deep_motor_page.objectName())
        
        self.logger.info("设备界面UI设置完成")

    def _create_pages(self):
        """创建并初始化所有页面"""
        self.logger.info("开始创建设备页面")

        # 创建新的页面实例
        self.deep_motor_page = DeepMotorPage(log_manager=self.log_manager, config_manager=self.config_manager)
        self.deep_arm_page = DeepArmPage(log_manager=self.log_manager, config_manager=self.config_manager)
        self.deep_toy_page = DeepToyPage(log_manager=self.log_manager, config_manager=self.config_manager)

        # 连接信号
        self.deep_motor_page.ui_deepmotor_command.connect(self.ui_device_command)
        self.deep_motor_page.ui_device_command.connect(self.ui_device_command)
        self.deep_motor_page.request_history_data.connect(self.ui_request_history_data)
        self.deep_arm_page.ui_device_command.connect(self.ui_device_command)
        self.deep_toy_page.ui_device_command.connect(self.ui_device_command)

        # 添加页面到堆叠窗口
        self.stackWidget.addWidget(self.deep_motor_page)
        self.stackWidget.addWidget(self.deep_arm_page)
        self.stackWidget.addWidget(self.deep_toy_page)
        
        # 添加导航项
        self.addSubInterface(self.deep_motor_page, 'deep_motor', 'DeepMotor')
        self.addSubInterface(self.deep_arm_page, 'deep_arm', 'DeepArm')
        self.addSubInterface(self.deep_toy_page, 'deep_toy', 'DeepToy')
        
        self.logger.info("设备页面创建完成")

    def addSubInterface(self, widget: QWidget, objectName: str, text: str):
        """添加子界面"""
        widget.setObjectName(objectName)
        self.pivot.addItem(
            routeKey=objectName,
            text=text,
            onClick=lambda: self.stackWidget.setCurrentWidget(widget)
        )
        self.logger.info(f"添加子界面: {text} (对象名: {objectName})")

    def onCurrentIndexChanged(self, index):
        """当前页面改变处理"""
        widget = self.stackWidget.widget(index)
        if widget:
            self.pivot.setCurrentItem(widget.objectName())
            self.logger.info(f"页面切换: 当前页面索引 {index}, 对象名: {widget.objectName()}")

    def update_motor_history_data(self, history_data):
        """更新电机历史数据（保持向后兼容）"""
        # 查找DeepMotor页面
        if self.deep_motor_page and hasattr(self.deep_motor_page, 'update_history_curve'):
            self.deep_motor_page.update_history_curve(history_data)
            self.logger.info("电机历史数据更新完成")
        else:
            self.logger.warning("DeepMotor页面未初始化，无法更新历史数据")

    def get_device_page(self, device_id: str):
        """根据设备ID获取对应的设备页面"""
        device_map = {
            'DeepMotor': self.deep_motor_page,
            'DeepArm': self.deep_arm_page,
            'DeepToy': self.deep_toy_page
        }
        return device_map.get(device_id)

    def get_deep_motor_page(self):
        """获取DeepMotor页面实例"""
        return self.deep_motor_page

    def _handle_trajectory_execution_progress(self, device_id: str, progress_data: dict):
        """处理轨迹执行进度信号"""
        self.logger.info(f"设备界面: 收到轨迹执行进度，设备: {device_id}")
        device_page = self.get_device_page(device_id)
        if device_page and hasattr(device_page, 'update_trajectory_execution_progress'):
            device_page.update_trajectory_execution_progress(device_id, progress_data)

    def _handle_trajectory_execution_finished(self, device_id: str):
        """处理轨迹执行完成信号"""
        self.logger.info(f"设备界面: 收到轨迹执行完成，设备: {device_id}")
        device_page = self.get_device_page(device_id)
        if device_page and hasattr(device_page, 'on_trajectory_execution_finished'):
            device_page.on_trajectory_execution_finished()

    def _handle_trajectory_execution_error(self, device_id: str, error_message: str):
        """处理轨迹执行错误信号"""
        self.logger.error(f"设备界面: 收到轨迹执行错误，设备: {device_id}, 错误: {error_message}")
        device_page = self.get_device_page(device_id)
        if device_page and hasattr(device_page, 'on_trajectory_execution_error'):
            device_page.on_trajectory_execution_error(error_message)
    
    def _handle_device_status_updated(self, device_id: str, status: dict):
        """处理设备状态更新信号"""
        self.logger.debug(f"设备界面: 收到设备状态更新，设备: {device_id}, 状态: {status}")
        device_page = self.get_device_page(device_id)
        if device_page and hasattr(device_page, 'on_device_status_updated'):
            device_page.on_device_status_updated(status)
    
    def _handle_device_control_response(self, device_id: str, response: dict):
        """处理设备控制响应信号"""
        self.logger.debug(f"设备界面: 收到设备控制响应，设备: {device_id}, 响应: {response}")
        device_page = self.get_device_page(device_id)
        if device_page and hasattr(device_page, 'on_device_control_response'):
            device_page.on_device_control_response(response)
    
    def _handle_device_control_error(self, device_id: str, error: str):
        """处理设备控制错误信号"""
        self.logger.error(f"设备界面: 收到设备控制错误，设备: {device_id}, 错误: {error}")
        device_page = self.get_device_page(device_id)
        if device_page and hasattr(device_page, 'on_device_control_error'):
            device_page.on_device_control_error(error)
    
    def _handle_image_processing_started(self, task_id: str, image_path: str):
        """处理图像处理开始信号"""
        self.logger.debug(f"设备界面: 收到图像处理开始，任务: {task_id}, 图像: {image_path}")
        # 可以在这里添加图像处理开始的UI更新逻辑
    
    def _handle_image_processing_finished(self, task_id: str, result: str):
        """处理图像处理完成信号"""
        self.logger.debug(f"设备界面: 收到图像处理完成，任务: {task_id}, 结果: {result}")
        # 可以在这里添加图像处理完成的UI更新逻辑
    
    def _handle_image_processing_error(self, task_id: str, error: str):
        """处理图像处理错误信号"""
        self.logger.error(f"设备界面: 收到图像处理错误，任务: {task_id}, 错误: {error}")
        # 可以在这里添加图像处理错误的UI更新逻辑
    
    def _handle_resource_matched(self, resource_id: str, match_result: dict):
        """处理资源匹配信号"""
        self.logger.debug(f"设备界面: 收到资源匹配，资源: {resource_id}, 结果: {match_result}")
        # 可以在这里添加资源匹配的UI更新逻辑
    
    def _handle_resource_match_error(self, resource_id: str, error: str):
        """处理资源匹配错误信号"""
        self.logger.error(f"设备界面: 收到资源匹配错误，资源: {resource_id}, 错误: {error}")
        # 可以在这里添加资源匹配错误的UI更新逻辑
        