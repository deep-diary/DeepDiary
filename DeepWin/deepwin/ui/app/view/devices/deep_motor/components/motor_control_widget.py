"""
电机控制组件
提供电机参数设置和基本控制功能
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QSlider
from qfluentwidgets import (PrimaryPushButton, SpinBox, CardWidget, FlowLayout)
from typing import Optional
from deepwin.data_management.log_manager import LogManager


class MotorControlWidget(QWidget):
    """电机控制组件"""
    
    # 信号定义
    motor_id_changed = Signal(int)  # 电机ID改变信号
    position_changed = Signal(int)  # 位置改变信号
    speed_changed = Signal(int)     # 速度改变信号
    command_requested = Signal(str, list)  # 命令请求信号 (命令名, 参数列表)
    sim_data_requested = Signal()   # 模拟数据请求信号
    
    def __init__(self, title: str = "电机控制", log_manager: LogManager = None, parent=None):
        super().__init__(parent)
        self.logger = log_manager
        self.title = title
        
        # 电机参数
        self.current_motor_id = 6
        self.current_position = 0
        self.current_speed = 5
        self._is_jogging = False
        
        self.setup_ui()
        
    def setup_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 创建卡片容器
        self.card = CardWidget(parent=self)
        self.card.setObjectName(self.title)
        card_layout = QVBoxLayout(self.card)
        
        # 标题
        title_label = QLabel(self.title)
        title_label.setObjectName('cardTitle')
        card_layout.addWidget(title_label)
        
        # 参数设置区域
        param_layout = QHBoxLayout()
        
        # 电机ID设置
        id_label = QLabel('电机ID:')
        self.id_spin = SpinBox()
        self.id_spin.setRange(1, 10)
        self.id_spin.setValue(self.current_motor_id)
        self.id_spin.valueChanged.connect(self._on_motor_id_changed)
        
        # 位置设置
        pos_label = QLabel('位置:')
        self.pos_slider = QSlider(Qt.Horizontal)
        self.pos_slider.setRange(-360, 360)
        self.pos_slider.setValue(self.current_position)
        self.pos_slider.setTickPosition(QSlider.TicksBelow)
        self.pos_slider.setTickInterval(60)
        self.pos_value_label = QLabel(str(self.current_position))
        self.pos_slider.valueChanged.connect(self._on_position_changed)
        
        # 速度设置
        speed_label = QLabel('速度:')
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(-20, 20)
        self.speed_slider.setValue(self.current_speed)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(5)
        self.speed_value_label = QLabel(str(self.current_speed))
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        
        # 添加到布局
        param_layout.addWidget(id_label)
        param_layout.addWidget(self.id_spin)
        param_layout.addWidget(pos_label)
        param_layout.addWidget(self.pos_slider)
        param_layout.addWidget(self.pos_value_label)
        param_layout.addWidget(speed_label)
        param_layout.addWidget(self.speed_slider)
        param_layout.addWidget(self.speed_value_label)
        param_layout.addStretch()
        
        card_layout.addLayout(param_layout)
        
        # 控制按钮区域
        button_container = QWidget()
        button_flow_layout = FlowLayout(button_container, needAni=True)
        button_flow_layout.setContentsMargins(0, 10, 0, 0)
        button_flow_layout.setVerticalSpacing(10)
        button_flow_layout.setHorizontalSpacing(10)
        
        # 创建控制按钮
        self._create_control_buttons(button_flow_layout)
        
        card_layout.addWidget(button_container)
        
        # 状态显示区域
        status_layout = QGridLayout()
        
        # 状态标签
        pos_display_label = QLabel('当前位置:')
        self.pos_display = QLabel('0.0°')
        speed_display_label = QLabel('当前速度:')
        self.speed_display = QLabel('0.0°/s')
        torque_display_label = QLabel('当前扭矩:')
        self.torque_display = QLabel('0.0 N·m')
        temp_display_label = QLabel('当前温度:')
        self.temp_display = QLabel('0.0°C')
        
        status_layout.addWidget(pos_display_label, 0, 0)
        status_layout.addWidget(self.pos_display, 0, 1)
        status_layout.addWidget(speed_display_label, 0, 2)
        status_layout.addWidget(self.speed_display, 0, 3)
        status_layout.addWidget(torque_display_label, 1, 0)
        status_layout.addWidget(self.torque_display, 1, 1)
        status_layout.addWidget(temp_display_label, 1, 2)
        status_layout.addWidget(self.temp_display, 1, 3)
        
        card_layout.addLayout(status_layout)
        
        layout.addWidget(self.card)
        
    def _create_control_buttons(self, layout: FlowLayout):
        """创建控制按钮"""
        # 点动按钮
        self.jog_button = PrimaryPushButton('点动')
        self.jog_button.setCheckable(True)
        self.jog_button.pressed.connect(self._on_jog_pressed)
        self.jog_button.released.connect(self._on_jog_released)
        
        # 初始化按钮
        self.init_button = PrimaryPushButton('初始化')
        self.init_button.clicked.connect(self._on_init_clicked)
        
        # 使能按钮
        self.enable_button = PrimaryPushButton('使能')
        self.enable_button.clicked.connect(self._on_enable_clicked)
        
        # 失能按钮
        self.disable_button = PrimaryPushButton('失能')
        self.disable_button.clicked.connect(self._on_disable_clicked)
        
        # 设置位置按钮
        self.set_pos_button = PrimaryPushButton('设置位置')
        self.set_pos_button.clicked.connect(self._on_set_pos_clicked)
        
        # 设置速度按钮
        self.set_speed_button = PrimaryPushButton('设置速度')
        self.set_speed_button.clicked.connect(self._on_set_speed_clicked)
        
        # 模拟数据按钮
        self.sim_button = PrimaryPushButton('发送模拟数据')
        self.sim_button.clicked.connect(self._on_sim_data_clicked)
        
        # 添加到布局
        layout.addWidget(self.jog_button)
        layout.addWidget(self.init_button)
        layout.addWidget(self.enable_button)
        layout.addWidget(self.disable_button)
        layout.addWidget(self.set_pos_button)
        layout.addWidget(self.set_speed_button)
        layout.addWidget(self.sim_button)
        
    def _on_motor_id_changed(self, value: int):
        """电机ID改变处理"""
        self.current_motor_id = value
        if self.logger:
            self.logger.info(f"电机ID已更改为: {value}")
        self.motor_id_changed.emit(value)
        
    def _on_position_changed(self, value: int):
        """位置改变处理"""
        self.current_position = value
        self.pos_value_label.setText(str(value))
        if self.logger:
            self.logger.debug(f"位置值已更改为: {value}")
        self.position_changed.emit(value)
        
    def _on_speed_changed(self, value: int):
        """速度改变处理"""
        self.current_speed = value
        self.speed_value_label.setText(str(value))
        if self.logger:
            self.logger.debug(f"速度值已更改为: {value}")
        self.speed_changed.emit(value)
        
    def _on_jog_pressed(self):
        """点动按钮按下处理"""
        if self.logger:
            self.logger.info(f"点动按钮按下，电机ID: {self.current_motor_id}, 速度: {self.current_speed}")
        self._is_jogging = True
        self.command_requested.emit('motor_jog', [self.current_motor_id, self.current_speed])
        
    def _on_jog_released(self):
        """点动按钮释放处理"""
        if self.logger:
            self.logger.info(f"点动按钮释放，电机ID: {self.current_motor_id}")
        self._is_jogging = False
        self.command_requested.emit('motor_jog_stop', [self.current_motor_id])
        
    def _on_init_clicked(self):
        """初始化按钮点击处理"""
        if self.logger:
            self.logger.info(f"初始化按钮被点击，电机ID: {self.current_motor_id}")
        self.command_requested.emit('motor_init', [self.current_motor_id])
        
    def _on_enable_clicked(self):
        """使能按钮点击处理"""
        if self.logger:
            self.logger.info(f"使能按钮被点击，电机ID: {self.current_motor_id}")
        self.command_requested.emit('motor_enable', [self.current_motor_id])
        
    def _on_disable_clicked(self):
        """失能按钮点击处理"""
        if self.logger:
            self.logger.info(f"失能按钮被点击，电机ID: {self.current_motor_id}")
        self.command_requested.emit('motor_disable', [self.current_motor_id])
        
    def _on_set_pos_clicked(self):
        """设置位置按钮点击处理"""
        if self.logger:
            self.logger.info(f"设置位置按钮被点击，电机ID: {self.current_motor_id}, 位置: {self.current_position}")
        self.command_requested.emit('motor_set_pos', [self.current_motor_id, self.current_position])
        
    def _on_set_speed_clicked(self):
        """设置速度按钮点击处理"""
        if self.logger:
            self.logger.info(f"设置速度按钮被点击，电机ID: {self.current_motor_id}, 速度: {self.current_speed}")
        self.command_requested.emit('motor_set_speed', [self.current_motor_id, self.current_speed])
        
    def _on_sim_data_clicked(self):
        """模拟数据按钮点击处理"""
        if self.logger:
            self.logger.info(f"模拟数据按钮被点击，电机ID: {self.current_motor_id}")
        self.sim_data_requested.emit()
        
    def update_motor_status(self, status_data: dict):
        """
        更新电机状态显示
        :param status_data: 包含电机状态数据的字典
        """
        try:
            # 更新位置显示
            if 'position' in status_data:
                self.pos_display.setText(f"{status_data['position']:.1f}°")
                
            # 更新速度显示
            if 'velocity' in status_data:
                self.speed_display.setText(f"{status_data['velocity']:.1f}°/s")
                
            # 更新扭矩显示
            if 'torque' in status_data:
                self.torque_display.setText(f"{status_data['torque']:.1f} N·m")
                
            # 更新温度显示
            if 'temperature' in status_data:
                self.temp_display.setText(f"{status_data['temperature']:.1f}°C")
                
        except Exception as e:
            if self.logger:
                self.logger.error(f"更新电机状态显示失败: {e}")
                
    def get_current_motor_id(self) -> int:
        """获取当前电机ID"""
        return self.current_motor_id
        
    def get_current_position(self) -> int:
        """获取当前位置"""
        return self.current_position
        
    def get_current_speed(self) -> int:
        """获取当前速度"""
        return self.current_speed
        
    def set_motor_id(self, motor_id: int):
        """设置电机ID"""
        self.current_motor_id = motor_id
        self.id_spin.blockSignals(True)
        self.id_spin.setValue(motor_id)
        self.id_spin.blockSignals(False)
        
    def set_position(self, position: int):
        """设置位置"""
        self.current_position = position
        self.pos_slider.blockSignals(True)
        self.pos_slider.setValue(position)
        self.pos_value_label.setText(str(position))
        self.pos_slider.blockSignals(False)
        
    def set_speed(self, speed: int):
        """设置速度"""
        self.current_speed = speed
        self.speed_slider.blockSignals(True)
        self.speed_slider.setValue(speed)
        self.speed_value_label.setText(str(speed))
        self.speed_slider.blockSignals(False)
        
    def set_jogging_state(self, is_jogging: bool):
        """设置点动状态"""
        self._is_jogging = is_jogging
        self.jog_button.setChecked(is_jogging)
        
    def is_jogging(self) -> bool:
        """获取点动状态"""
        return self._is_jogging
        
    def enable_controls(self, enabled: bool = True):
        """启用/禁用控制按钮"""
        self.jog_button.setEnabled(enabled)
        self.init_button.setEnabled(enabled)
        self.enable_button.setEnabled(enabled)
        self.disable_button.setEnabled(enabled)
        self.set_pos_button.setEnabled(enabled)
        self.set_speed_button.setEnabled(enabled)
        self.sim_button.setEnabled(enabled)
        
    def reset_to_defaults(self):
        """重置为默认值"""
        self.set_motor_id(6)
        self.set_position(0)
        self.set_speed(5)
        self.set_jogging_state(False)
        
        # 重置状态显示
        self.pos_display.setText('0.0°')
        self.speed_display.setText('0.0°/s')
        self.torque_display.setText('0.0 N·m')
        self.temp_display.setText('0.0°C')
