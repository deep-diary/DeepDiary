from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
from qfluentwidgets import (PrimaryPushButton, ComboBox, SpinBox, FluentIcon as FIF, CardWidget)

class SerialConfigWidget(QWidget):
    """串口配置组件"""
    serial_connect_requested = Signal(str, int)  # 串口名, 波特率
    serial_disconnect_requested = Signal(str)  # 串口名
    request_ports = Signal()  # 请求获取可用端口列表的信号

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setup_ui()
        # 使用QTimer延迟发送刷新信号，确保信号连接已经建立
        QTimer.singleShot(100, self.request_ports.emit)
        self.is_connected = False  # 添加连接状态标志
        self.current_port = ""  # 当前连接的串口

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 串口选择
        port_layout = QHBoxLayout()
        port_label = QLabel('串口:')
        self.port_combo = ComboBox()
        port_layout.addWidget(port_label)
        port_layout.addWidget(self.port_combo)
        port_layout.addStretch()

        # 波特率选择
        baud_layout = QHBoxLayout()
        baud_label = QLabel('波特率:')
        self.baud_combo = ComboBox()
        self.baud_combo.addItems(['9600', '115200', '230400', '460800', '921600', '1500000'])
        self.baud_combo.setCurrentText('921600')
        baud_layout.addWidget(baud_label)
        baud_layout.addWidget(self.baud_combo)
        baud_layout.addStretch()

        # 连接按钮
        self.connect_button = PrimaryPushButton('连接')
        self.connect_button.setStyleSheet("""
            PrimaryPushButton {
                background-color: #0078d4;
                color: white;
            }
            PrimaryPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        layout.addLayout(port_layout)
        layout.addLayout(baud_layout)
        layout.addWidget(self.connect_button)
        layout.addStretch()

        # 连接信号
        self.connect_button.clicked.connect(self.toggle_connection)

    def update_ports(self, ports: list):
        """更新串口列表"""
        current_port = self.port_combo.currentText()
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        # 尝试恢复之前选择的端口
        index = self.port_combo.findText(current_port)
        if index >= 0:
            self.port_combo.setCurrentIndex(index)

    def toggle_connection(self):
        """切换连接状态"""
        if self.is_connected:
            # 如果已连接，发送断开请求
            self.serial_disconnect_requested.emit(self.current_port)
        else:
            # 如果未连接，发送连接请求
            port = self.port_combo.currentText()
            baud = int(self.baud_combo.currentText())
            self.current_port = port  # 保存当前连接的串口
            self.serial_connect_requested.emit(port, baud)

    def update_connection_status(self, is_connected: bool):
        """更新连接状态UI"""
        self.is_connected = is_connected
        if is_connected:
            self.connect_button.setText('关闭')
            self.connect_button.setStyleSheet("""
                PrimaryPushButton {
                    background-color: #d83b01;
                    color: white;
                }
                PrimaryPushButton:disabled {
                    background-color: #cccccc;
                }
            """)
            # 禁用串口和波特率选择
            self.port_combo.setEnabled(False)
            self.baud_combo.setEnabled(False)
        else:
            self.connect_button.setText('连接')
            self.connect_button.setStyleSheet("""
                PrimaryPushButton {
                    background-color: #0078d4;
                    color: white;
                }
                PrimaryPushButton:disabled {
                    background-color: #cccccc;
                }
            """)
            # 启用串口和波特率选择
            self.port_combo.setEnabled(True)
            self.baud_combo.setEnabled(True)
            self.current_port = ""  # 清除当前连接的串口

class DeepMotorPage(QWidget):
    """DeepMotor 控制页面"""
    ui_deepmotor_command = Signal(str, str)  # 设备命令信号
    request_sim_data = Signal(str)  # 请求模拟数据的信号

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.DeviceName = "DeepMotor"
        self.current_motor_id = 1  # 当前选中的电机ID
        self._is_jogging = False  # 添加点动状态标志
        self.setup_ui()

    def setup_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 电机控制部分
        control_group = CardWidget(parent=self)
        control_group.setObjectName('电机控制')
        control_layout = QVBoxLayout(control_group)
        
        # 标题标签
        title_label = QLabel('电机控制')
        title_label.setObjectName('cardTitle')
        control_layout.addWidget(title_label)
        
        # 电机ID选择
        id_layout = QHBoxLayout()
        id_label = QLabel('电机ID:')
        self.id_spin = SpinBox()
        self.id_spin.setRange(1, 10)
        self.id_spin.valueChanged.connect(self.on_motor_id_changed)
        id_layout.addWidget(id_label)
        id_layout.addWidget(self.id_spin)
        id_layout.addStretch()
        
        # 位置控制
        pos_layout = QHBoxLayout()
        pos_label = QLabel('位置:')
        self.pos_spin = SpinBox()
        self.pos_spin.setRange(-360, 360)
        pos_layout.addWidget(pos_label)
        pos_layout.addWidget(self.pos_spin)
        pos_layout.addStretch()
        
        # 速度控制
        speed_layout = QHBoxLayout()
        speed_label = QLabel('速度:')
        self.speed_spin = SpinBox()
        self.speed_spin.setRange(-20, 20)
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_spin)
        speed_layout.addStretch()

        # 添加数据显示部分
        data_group = CardWidget(parent=self)
        data_group.setObjectName('电机数据')
        data_layout = QVBoxLayout(data_group)
        
        # 数据显示标题
        data_title = QLabel('电机数据')
        data_title.setObjectName('cardTitle')
        data_layout.addWidget(data_title)
        
        # 创建数据显示网格
        data_grid = QGridLayout()
        
        # 位置显示
        pos_display_label = QLabel('当前位置:')
        self.pos_display = QLabel('0.0°')
        data_grid.addWidget(pos_display_label, 0, 0)
        data_grid.addWidget(self.pos_display, 0, 1)
        
        # 速度显示
        speed_display_label = QLabel('当前速度:')
        self.speed_display = QLabel('0.0°/s')
        data_grid.addWidget(speed_display_label, 0, 2)
        data_grid.addWidget(self.speed_display, 0, 3)
        
        # 扭矩显示
        torque_display_label = QLabel('当前扭矩:')
        self.torque_display = QLabel('0.0 N·m')
        data_grid.addWidget(torque_display_label, 1, 0)
        data_grid.addWidget(self.torque_display, 1, 1)
        
        # 温度显示
        temp_display_label = QLabel('当前温度:')
        self.temp_display = QLabel('0.0°C')
        data_grid.addWidget(temp_display_label, 1, 2)
        data_grid.addWidget(self.temp_display, 1, 3)
        
        data_layout.addLayout(data_grid)
        
        # 模拟数据按钮
        sim_button_layout = QHBoxLayout()
        self.sim_button = PrimaryPushButton('发送模拟数据')
        self.sim_button.clicked.connect(self.on_sim_data_clicked)
        sim_button_layout.addWidget(self.sim_button)
        sim_button_layout.addStretch()
        data_layout.addLayout(sim_button_layout)
        
        # 点动控制
        jog_layout = QHBoxLayout()
        self.jog_button = PrimaryPushButton('点动')
        self.jog_button.setCheckable(True)  # 使按钮可切换状态
        self.jog_button.pressed.connect(self.on_jog_pressed)
        self.jog_button.released.connect(self.on_jog_released)
        jog_layout.addWidget(self.jog_button)
        jog_layout.addStretch()
        
        # 控制按钮
        button_layout = QHBoxLayout()
        self.init_button = PrimaryPushButton('初始化')
        self.enable_button = PrimaryPushButton('使能')
        self.disable_button = PrimaryPushButton('失能')
        self.set_pos_button = PrimaryPushButton('设置位置')
        self.set_pos_speed_button = PrimaryPushButton('设置位置和速度')
        
        button_layout.addWidget(self.init_button)
        button_layout.addWidget(self.enable_button)
        button_layout.addWidget(self.disable_button)
        button_layout.addWidget(self.set_pos_button)
        button_layout.addWidget(self.set_pos_speed_button)
        
        # 添加所有控件到布局
        control_layout.addLayout(id_layout)
        control_layout.addLayout(pos_layout)
        control_layout.addLayout(speed_layout)
        control_layout.addLayout(jog_layout)  # 添加点动控制布局
        control_layout.addLayout(button_layout)
        
        layout.addWidget(control_group)
        layout.addWidget(data_group)  # 添加数据显示组
        layout.addStretch()
        
        # 连接信号
        self.init_button.clicked.connect(self.on_init_clicked)
        self.enable_button.clicked.connect(self.on_enable_clicked)
        self.disable_button.clicked.connect(self.on_disable_clicked)
        self.set_pos_button.clicked.connect(self.on_set_pos_clicked)
        self.set_pos_speed_button.clicked.connect(self.on_set_pos_speed_clicked)

    def on_motor_id_changed(self, value):
        """电机ID改变时的处理函数"""
        self.current_motor_id = value

    def on_jog_pressed(self):
        """点动按钮按下时的处理函数"""
        print(f"--------------------------------------------------on_jog_pressed")
        self.send_command('jog_motor', [self.current_motor_id, self.speed_spin.value()])
        

    def on_jog_released(self):
        """点动按钮释放时的处理函数"""
        print(f"--------------------------------------------------on_jog_released")
        self.send_command('stop_jog_motor', [self.current_motor_id])

    def on_init_clicked(self):
        """初始化按钮点击处理函数"""
        self.send_command('init_motor', [self.id_spin.value()])

    def on_enable_clicked(self):
        """使能按钮点击处理函数"""
        self.send_command('enable_motor', [self.id_spin.value()])

    def on_disable_clicked(self):
        """失能按钮点击处理函数"""
        self.send_command('disable_motor', [self.id_spin.value()])

    def on_set_pos_clicked(self):
        """设置位置按钮点击处理函数"""
        self.send_command('set_motor_position', [self.id_spin.value(), self.pos_spin.value()])

    def on_set_pos_speed_clicked(self):
        """设置位置和速度按钮点击处理函数"""
        self.send_command('set_motor_pos_speed', [self.id_spin.value(), self.pos_spin.value(), self.speed_spin.value()])

    def on_sim_data_clicked(self):
        """模拟数据按钮点击处理函数"""
        self.request_sim_data.emit(self.DeviceName)

    def update_motor_data(self, state_dict: dict):
        print(f"--------------------------------------------------update_motor_data")
        print(f"state_dict: {state_dict}")
        status = state_dict.get('status', {})
        position = status.get('position', 0.0)
        speed = status.get('velocity', 0.0)
        torque = status.get('torque', 0.0)
        temperature = status.get('temperature', 0.0)
        """更新电机数据显示"""
        self.pos_display.setText(f"{position:.1f}°")
        self.speed_display.setText(f"{speed:.1f}°/s")
        self.torque_display.setText(f"{torque:.1f} N·m")
        self.temp_display.setText(f"{temperature:.1f}°C")

    def send_command(self, command: str, args: list):
        """发送设备命令"""
        print(f"--------------------------------------------------send_command")
        command_str = command + "(" + ",".join(str(arg) for arg in args) + ")"
        print(f"DeepMotorPage: 发送命令: {command_str}")
        self.ui_deepmotor_command.emit(self.DeviceName, command_str)

class DeepArmPage(QWidget):
    """DeepArm 控制页面"""
    ui_device_command = Signal(str, str)  # 设备命令信号

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setup_ui()

    def setup_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 机械臂控制部分
        control_group = CardWidget(parent=self)
        control_group.setObjectName('机械臂控制')
        control_layout = QVBoxLayout(control_group)
        
        # 标题标签
        title_label = QLabel('机械臂控制')
        title_label.setObjectName('cardTitle')
        control_layout.addWidget(title_label)
        
        # 添加机械臂控制相关的控件
        # TODO: 实现机械臂控制界面
        
        layout.addWidget(control_group)
        layout.addStretch()

class DeepToyPage(QWidget):
    """DeepToy 控制页面"""
    ui_device_command = Signal(str, str)  # 设备命令信号

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setup_ui()

    def setup_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 玩具控制部分
        control_group = CardWidget(parent=self)
        control_group.setObjectName('玩具控制')
        control_layout = QVBoxLayout(control_group)
        
        # 标题标签
        title_label = QLabel('玩具控制')
        title_label.setObjectName('cardTitle')
        control_layout.addWidget(title_label)
        
        # 添加玩具控制相关的控件
        # TODO: 实现玩具控制界面
        
        layout.addWidget(control_group)
        layout.addStretch() 