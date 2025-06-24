from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QDoubleSpinBox
from qfluentwidgets import (PrimaryPushButton, ComboBox, SpinBox, FluentIcon as FIF, CardWidget, FlowLayout, SwitchButton)

# 添加matplotlib支持
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime
import time
import hashlib
import pandas as pd

# 添加日志管理
from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager

class SerialConfigWidget(CardWidget):
    """串口配置组件"""
    serial_connect_requested = Signal(str, int)  # 串口名, 波特率
    serial_disconnect_requested = Signal(str)  # 串口名
    request_ports = Signal()  # 请求获取可用端口列表的信号

    def __init__(self, log_manager: LogManager = None, config_manager: ConfigManager = None, parent=None):
        super().__init__(parent=parent)
        self.log_manager = log_manager
        self.logger = self.log_manager.get_logger(__name__) if self.log_manager else None
        self.config_manager = config_manager
        
        self.setup_ui()
        # 使用QTimer延迟发送刷新信号，确保信号连接已经建立
        QTimer.singleShot(100, self.request_ports.emit)
        self.is_connected = False  # 添加连接状态标志
        self.current_port = ""  # 当前连接的串口
        
        if self.logger:
            self.logger.info("串口配置组件初始化完成")

    def setup_ui(self):
        self.v_layout = QVBoxLayout(self)
        self.h_layout = QHBoxLayout()

        title_label = QLabel('串口连接')
        title_label.setObjectName('cardTitle')
        self.v_layout.addWidget(title_label)
        self.v_layout.addLayout(self.h_layout)

        self.h_layout.setContentsMargins(0, 0, 0, 0)
        self.h_layout.setSpacing(10)

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
        
        self.h_layout.addLayout(port_layout)
        self.h_layout.addLayout(baud_layout)
        self.h_layout.addWidget(self.connect_button)
        self.h_layout.addStretch()

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
        
        if self.logger:
            self.logger.info(f"串口列表更新完成，可用端口: {ports}")

    def toggle_connection(self):
        """切换连接状态"""
        if self.is_connected:
            # 如果已连接，发送断开请求
            if self.logger:
                self.logger.info(f"请求断开串口连接: {self.current_port}")
            self.serial_disconnect_requested.emit(self.current_port)
        else:
            # 如果未连接，发送连接请求
            port = self.port_combo.currentText()
            baud = int(self.baud_combo.currentText())
            self.current_port = port  # 保存当前连接的串口
            if self.logger:
                self.logger.info(f"请求连接串口: {port}, 波特率: {baud}")
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
            if self.logger:
                self.logger.info(f"串口连接成功: {self.current_port}")
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
            if self.logger:
                self.logger.info("串口连接已断开")

class DeepMotorPage(QWidget):
    """DeepMotor 控制页面"""
    ui_deepmotor_command = Signal(str, str)  # 设备命令信号
    request_sim_data = Signal(str)  # 请求模拟数据的信号
    request_history_data = Signal(str, str)  # 请求历史数据信号 (设备名, 参数名)
    # 示教相关信号
    start_teaching_requested = Signal(str, int)  # 开始示教信号 (设备名, motor_id)
    stop_teaching_requested = Signal(str)   # 停止示教信号
    execute_teaching_requested = Signal(str, str, bool, int)  # 执行示教信号 (设备名, 轨迹名, 是否使用规划轨迹, motor_id)
    # 新增：轨迹可视化相关信号
    request_trajectory_data = Signal(str, str)  # 请求轨迹数据信号 (设备名, 轨迹名)
    request_trajectory_list = Signal(str)  # 请求轨迹列表信号
    replan_requested = Signal(str, str, float)  # 重规划信号 (设备名, 轨迹名, 新时长)
    restore_default_requested = Signal(str, str) # 恢复默认信号 (设备名, 轨迹名)
    delete_trajectory_requested = Signal(str, str) # 删除轨迹信号 (设备名, 轨迹名)

    def __init__(self, log_manager: LogManager = None, config_manager: ConfigManager = None, parent=None):
        super().__init__(parent=parent)
        self.log_manager = log_manager
        self.logger = self.log_manager.get_logger(__name__) if self.log_manager else None
        self.config_manager = config_manager
        
        # 设备名称
        self.DeviceName = "DeepMotor"
        
        # 当前选中的参数
        self.current_selected_param = 'position'
        
        # 轨迹相关变量
        self._current_trajectory = None
        self._show_trajectory = False
        self._original_total_time = None
        
        # 示教相关变量
        self._is_executing_trajectory = False
        self._last_execution_data = None  # 保存最后一次执行的数据
        
        # 电机控制相关变量
        self.current_motor_id = 6  # 当前选中的电机ID
        self._is_jogging = False  # 点动状态标志
        
        # 轨迹规划相关变量
        self.use_planned_trajectory = False  # 是否使用规划轨迹
        
        # 新增：动画和绘图优化相关变量
        self.planned_line = None  # 规划轨迹的Line2D对象
        self.feedback_line = None # 反馈轨迹的Line2D对象
        self.background = None    # 绘图背景缓存，用于blitting
        self._last_xlim = None    # 上一次的X轴范围
        self._last_ylim = None    # 上一次的Y轴范围
        
        # 新增：用于节流更新的定时器和数据
        self.plot_update_timer = QTimer(self)
        self.plot_update_timer.setInterval(50)  # 每50ms更新一次图表（20 FPS）
        self.plot_update_timer.timeout.connect(self._throttled_plot_update)
        self.latest_progress_data = None
        
        # 新增：历史曲线定时更新相关变量
        self.history_update_timer = QTimer(self)
        self.history_update_timer.setInterval(100)  # 每100ms更新一次历史曲线（10 FPS）
        self.history_update_timer.timeout.connect(self._throttled_history_update)
        self.latest_history_data = None  # 缓存最新的历史数据
        self._is_history_updating = False  # 历史曲线更新状态标志
        self._last_drawn_history_data_hash = None  # 上一次绘制的数据hash
        
        # 新增：历史数据请求定时器
        self.history_request_timer = QTimer(self)
        self.history_request_timer.setInterval(200)  # 每200ms请求一次历史数据（5 FPS）
        self.history_request_timer.timeout.connect(self._request_history_data)
        self._should_request_history = False  # 是否需要请求历史数据的标志
        
        if self.logger:
            self.logger.info("DeepMotor页面初始化开始")
        self.setup_ui()
        
        # 初始化轨迹列表
        self.init_trajectory_list()
        
        if self.logger:
            self.logger.info("DeepMotor页面初始化完成")

    def setup_ui(self):
        """初始化界面"""
        if self.logger:
            self.logger.info("开始设置DeepMotor页面UI")
            
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        # --- 电机控制卡片 ---
        motor_control_card = CardWidget(self)
        motor_control_layout = QVBoxLayout(motor_control_card)
        motor_title = QLabel('电机控制')
        motor_title.setObjectName('cardTitle')
        motor_control_layout.addWidget(motor_title)

        # 参数行
        param_layout = QHBoxLayout()
        id_label = QLabel('电机ID:')
        self.id_spin = SpinBox()
        self.id_spin.setRange(1, 10)
        self.id_spin.setValue(6)
        self.id_spin.valueChanged.connect(self.on_motor_id_changed)
        pos_label = QLabel('位置:')
        self.pos_spin = SpinBox()
        self.pos_spin.setRange(-360, 360)
        speed_label = QLabel('速度:')
        self.speed_spin = SpinBox()
        self.speed_spin.setRange(-20, 20)
        param_layout.addWidget(id_label)
        param_layout.addWidget(self.id_spin)
        param_layout.addWidget(pos_label)
        param_layout.addWidget(self.pos_spin)
        param_layout.addWidget(speed_label)
        param_layout.addWidget(self.speed_spin)
        param_layout.addStretch()
        motor_control_layout.addLayout(param_layout)

        # 按钮行 (使用 FlowLayout)
        button_container = QWidget()
        button_flow_layout = FlowLayout(button_container, needAni=True)
        button_flow_layout.setContentsMargins(0, 10, 0, 0)
        button_flow_layout.setVerticalSpacing(10)
        button_flow_layout.setHorizontalSpacing(10)

        self.jog_button = PrimaryPushButton('点动')
        self.jog_button.setCheckable(True)
        self.jog_button.pressed.connect(self.on_jog_pressed)
        self.jog_button.released.connect(self.on_jog_released)
        self.init_button = PrimaryPushButton('初始化')
        self.enable_button = PrimaryPushButton('使能')
        self.disable_button = PrimaryPushButton('失能')
        self.set_pos_button = PrimaryPushButton('设置位置')
        self.set_pos_speed_button = PrimaryPushButton('设置位置和速度')
        self.sim_button = PrimaryPushButton('发送模拟数据')
        self.sim_button.clicked.connect(self.on_sim_data_clicked)
        
        button_flow_layout.addWidget(self.jog_button)
        button_flow_layout.addWidget(self.init_button)
        button_flow_layout.addWidget(self.enable_button)
        button_flow_layout.addWidget(self.disable_button)
        button_flow_layout.addWidget(self.set_pos_button)
        button_flow_layout.addWidget(self.set_pos_speed_button)
        button_flow_layout.addWidget(self.sim_button)
        motor_control_layout.addWidget(button_container)
        
        main_layout.addWidget(motor_control_card)

        # --- 示教控制卡片 ---
        teaching_card = CardWidget(self)
        teaching_layout_v = QVBoxLayout(teaching_card)
        teaching_title = QLabel('示教控制')
        teaching_title.setObjectName('cardTitle')
        teaching_layout_v.addWidget(teaching_title)

        teaching_controls_layout = QHBoxLayout()
        self.start_teaching_button = PrimaryPushButton('开始示教')
        self.stop_teaching_button = PrimaryPushButton('结束示教')
        self.execute_teaching_button = PrimaryPushButton('执行示教')
        self.delete_trajectory_button = PrimaryPushButton('删除轨迹')
        trajectory_label = QLabel('轨迹:')
        self.trajectory_combo = ComboBox()
        self.trajectory_combo.setMinimumWidth(150)
        
        # 执行时间控制
        duration_label = QLabel('执行时间:')
        self.duration_spin = QDoubleSpinBox(self)
        self.duration_spin.setRange(1.0, 30.0)
        self.duration_spin.setSingleStep(0.5)
        self.duration_spin.setSuffix(" s")
        self.duration_spin.setValue(5.0)
        
        # 轨迹规划开关
        planning_label = QLabel('轨迹规划:')
        self.planning_switch = SwitchButton('关闭')
        self.planning_switch.setChecked(False)  # 默认关闭
        self.planning_switch.checkedChanged.connect(self.on_planning_switch_changed)
        
        teaching_controls_layout.addWidget(self.start_teaching_button)
        teaching_controls_layout.addWidget(self.stop_teaching_button)
        teaching_controls_layout.addWidget(self.execute_teaching_button)
        teaching_controls_layout.addWidget(trajectory_label)
        teaching_controls_layout.addWidget(self.trajectory_combo)
        teaching_controls_layout.addWidget(duration_label)
        teaching_controls_layout.addWidget(self.duration_spin)
        teaching_controls_layout.addWidget(planning_label)
        teaching_controls_layout.addWidget(self.planning_switch)
        teaching_controls_layout.addWidget(self.delete_trajectory_button)
        teaching_controls_layout.addStretch()
        teaching_layout_v.addLayout(teaching_controls_layout)

        self.teaching_status_label = QLabel('示教状态: 未开始')
        self.teaching_status_label.setStyleSheet("color: gray;")
        teaching_layout_v.addWidget(self.teaching_status_label)
        
        main_layout.addWidget(teaching_card)

        # 添加数据显示部分（隐藏）
        data_group = CardWidget(parent=self)
        data_group.setObjectName('电机数据')
        data_layout = QVBoxLayout(data_group)
        data_title = QLabel('电机数据')
        data_title.setObjectName('cardTitle')
        data_layout.addWidget(data_title)
        data_grid = QGridLayout()
        pos_display_label = QLabel('当前位置:')
        self.pos_display = QLabel('0.0°')
        data_grid.addWidget(pos_display_label, 0, 0)
        data_grid.addWidget(self.pos_display, 0, 1)
        speed_display_label = QLabel('当前速度:')
        self.speed_display = QLabel('0.0°/s')
        data_grid.addWidget(speed_display_label, 0, 2)
        data_grid.addWidget(self.speed_display, 0, 3)
        torque_display_label = QLabel('当前扭矩:')
        self.torque_display = QLabel('0.0 N·m')
        data_grid.addWidget(torque_display_label, 1, 0)
        data_grid.addWidget(self.torque_display, 1, 1)
        temp_display_label = QLabel('当前温度:')
        self.temp_display = QLabel('0.0°C')
        data_grid.addWidget(temp_display_label, 1, 2)
        data_grid.addWidget(self.temp_display, 1, 3)
        data_layout.addLayout(data_grid)
        data_group.setVisible(False)
        
        main_layout.addWidget(data_group)
        
        # 添加历史曲线显示部分
        history_group = CardWidget(parent=self)
        history_group.setObjectName('历史曲线')
        history_group.setMinimumHeight(350)
        history_layout = QVBoxLayout(history_group)
        
        # 历史曲线标题
        history_title = QLabel('历史曲线')
        history_title.setObjectName('cardTitle')
        history_layout.addWidget(history_title)
        
        # 参数选择和控制
        param_control_layout = QHBoxLayout()
        param_label = QLabel('选择参数:')
        self.param_combo = ComboBox()
        self.param_combo.addItems([
            'position (位置)', 'velocity (速度)', 'torque (扭矩)', 'temperature (温度)', 'error_code (错误码)',
            'motor_can_id (CAN ID)', 'mode_state (模式状态)', 'flt_uninitialized (未初始化故障)',
            'flt_hall_encoding (霍尔编码故障)', 'flt_magnetic_encoding (磁编码故障)', 'flt_over_temperature (过温故障)',
            'flt_over_current (过流故障)', 'flt_voltage_drop (电压跌落故障)',
            '--- 示教与轨迹 ---', 'trajectory_teaching (示教轨迹)', 'trajectory_original (原始轨迹)', 'trajectory_planned (规划轨迹)', 'trajectory_both (原始+规划)', 'trajectory_executed (执行轨迹)'
        ])
        self.param_combo.setCurrentText('position (位置)')
        
        # 统一的刷新按钮
        self.refresh_button = PrimaryPushButton('刷新曲线')
        
        # 恢复默认时间按钮
        self.restore_time_button = PrimaryPushButton('恢复默认')
        self.restore_time_button.setEnabled(False)
        
        param_control_layout.addWidget(param_label)
        param_control_layout.addWidget(self.param_combo)
        param_control_layout.addWidget(self.refresh_button)
        param_control_layout.addWidget(self.restore_time_button)
        param_control_layout.addStretch()
        
        history_layout.addLayout(param_control_layout)
        
        # 创建matplotlib图形
        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(300)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('时间')
        self.ax.set_ylabel('数值')
        self.ax.grid(True)
        self.figure.tight_layout()
        
        history_layout.addWidget(self.canvas)
        
        main_layout.addWidget(history_group)
        main_layout.addStretch()
        
        # 连接信号
        self.init_button.clicked.connect(self.on_init_clicked)
        self.enable_button.clicked.connect(self.on_enable_clicked)
        self.disable_button.clicked.connect(self.on_disable_clicked)
        self.set_pos_button.clicked.connect(self.on_set_pos_clicked)
        self.set_pos_speed_button.clicked.connect(self.on_set_pos_speed_clicked)
        self.param_combo.currentTextChanged.connect(self.on_param_changed)
        self.refresh_button.clicked.connect(self.on_refresh_clicked)
        
        # 连接示教相关信号
        self.start_teaching_button.clicked.connect(self.on_start_teaching_clicked)
        self.stop_teaching_button.clicked.connect(self.on_stop_teaching_clicked)
        self.execute_teaching_button.clicked.connect(self.on_execute_teaching_clicked)
        self.delete_trajectory_button.clicked.connect(self.on_delete_trajectory_clicked)
        
        # 连接轨迹选择信号
        self.trajectory_combo.currentTextChanged.connect(self.on_trajectory_selection_changed)
        
        # 连接执行时间变化信号
        self.duration_spin.valueChanged.connect(self.on_duration_changed)
        
        # 连接恢复默认时间按钮
        self.restore_time_button.clicked.connect(self.on_restore_time_clicked)

        # 初始化示教按钮状态
        self.update_teaching_buttons_state()
        
        if self.logger:
            self.logger.info("DeepMotor页面UI设置完成")

    def select_trajectory(self, trajectory_name: str):
        """在下拉框中选中指定的轨迹"""
        # findText 会查找匹配的文本并返回其索引
        index = self.trajectory_combo.findText(trajectory_name)
        if index >= 0:
            self.trajectory_combo.setCurrentIndex(index)
            if self.logger:
                self.logger.info(f"UI: 已自动选中新轨迹 '{trajectory_name}'")
        else:
            if self.logger:
                self.logger.warning(f"UI: 尝试选中轨迹 '{trajectory_name}' 但在下拉框中未找到。")

    def update_teaching_buttons_state(self):
        """更新示教按钮状态"""
        if self._is_executing_trajectory:
            self.start_teaching_button.setEnabled(False)
            self.stop_teaching_button.setEnabled(True)
            self.execute_teaching_button.setEnabled(False)
            self.delete_trajectory_button.setEnabled(False)
            self.teaching_status_label.setText('示教状态: 执行中')
            self.teaching_status_label.setStyleSheet("color: blue;")
        else:
            self.start_teaching_button.setEnabled(True)
            self.stop_teaching_button.setEnabled(False)
            self.execute_teaching_button.setEnabled(True)
            # 删除按钮只有在有选中轨迹时才启用
            self.delete_trajectory_button.setEnabled(bool(self.trajectory_combo.currentText()))
            self.teaching_status_label.setText('示教状态: 未开始')
            self.teaching_status_label.setStyleSheet("color: gray;")

    def update_execution_buttons_state(self):
        """更新执行按钮状态"""
        if self._is_executing_trajectory:
            self.execute_teaching_button.setEnabled(False)
            self.delete_trajectory_button.setEnabled(False)
            self.teaching_status_label.setText('示教状态: 执行中')
            self.teaching_status_label.setStyleSheet("color: blue;")
        else:
            self.execute_teaching_button.setEnabled(True)
            # 删除按钮只有在有选中轨迹时才启用
            self.delete_trajectory_button.setEnabled(bool(self.trajectory_combo.currentText()))
            self.teaching_status_label.setText('示教状态: 未开始')
            self.teaching_status_label.setStyleSheet("color: gray;")

    def update_trajectory_list(self, trajectory_names: list, prefer_newest: bool = False):
        """更新轨迹列表"""
        # 保存当前选中的轨迹名称
        current_selection = self.trajectory_combo.currentText()
        
        # 清空并重新添加轨迹
        self.trajectory_combo.clear()
        self.trajectory_combo.addItems(trajectory_names)
        
        if prefer_newest and trajectory_names:
            # 优先选择最新的轨迹（列表中的最后一个）
            newest_trajectory = trajectory_names[-1]
            self.trajectory_combo.setCurrentText(newest_trajectory)
            if self.logger:
                self.logger.info(f"UI: 优先选中最新轨迹 '{newest_trajectory}'")
        elif current_selection and current_selection in trajectory_names:
            # 尝试恢复之前选中的轨迹
            self.trajectory_combo.setCurrentText(current_selection)
            if self.logger:
                self.logger.info(f"UI: 保持选中轨迹 '{current_selection}'")
        else:
            # 如果没有之前选中的轨迹或轨迹不存在，清空选择
            self._current_trajectory = None
            if self.logger:
                self.logger.info("UI: 清空轨迹选择")
        
        # 更新删除按钮状态
        self.delete_trajectory_button.setEnabled(bool(self.trajectory_combo.currentText()))

    def on_start_teaching_clicked(self):
        """开始示教按钮点击处理函数"""
        if self.logger:
            self.logger.info("开始示教按钮被点击")
        self._is_executing_trajectory = True
        self.update_teaching_buttons_state()
        
        # 先清空画布，确保没有残留的图形
        self.ax.clear()
        self.ax.set_xlabel('时间 (s)')
        self.ax.set_ylabel('位置 (°)')
        self.ax.set_title('示教轨迹实时记录')
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
        
        # 然后切换到示教轨迹视图（使用blockSignals避免触发on_param_changed）
        self.param_combo.blockSignals(True)
        self.param_combo.setCurrentText('trajectory_teaching (示教轨迹)')
        self.current_selected_param = 'trajectory_teaching'  # 立即更新内部状态
        self.param_combo.blockSignals(False)
        
        # 发送开始示教信号
        self.start_teaching_requested.emit(self.DeviceName, self.current_motor_id)

    def on_stop_teaching_clicked(self):
        """结束示教按钮点击处理函数"""
        if self.logger:
            self.logger.info("结束示教按钮被点击")
        self._is_executing_trajectory = False
        self.update_teaching_buttons_state()
        
        # 更新状态标签
        self.teaching_status_label.setText('示教状态: 录制完成')
        self.teaching_status_label.setStyleSheet("color: green;")
        
        # 发送结束示教信号
        self.stop_teaching_requested.emit(self.DeviceName)

    def on_execute_teaching_clicked(self):
        """执行示教按钮点击处理函数"""
        trajectory_name = self.trajectory_combo.currentText()
        if not trajectory_name:
            if self.logger:
                self.logger.warning("请先选择要执行的轨迹")
            return
        if self.logger:
            self.logger.info(f"执行示教按钮被点击，轨迹: {trajectory_name}, 使用规划轨迹: {self.planning_switch.isChecked()}")
        # 设置执行状态
        self._is_executing_trajectory = True
        self.update_execution_buttons_state()
        # 自动切换到执行轨迹视图
        self.param_combo.setCurrentText('trajectory_executed (执行轨迹)')
        
        # 显示当前坐标轴范围信息
        current_xlim = self.ax.get_xlim()
        current_ylim = self.ax.get_ylim()
        if self.logger:
            self.logger.info(f"执行轨迹时当前X轴范围: {current_xlim}")
            self.logger.info(f"执行轨迹时当前Y轴范围: {current_ylim}")
            if hasattr(self, '_last_xlim') and self._last_xlim:
                self.logger.info(f"保存的X轴范围: {self._last_xlim}")
            if hasattr(self, '_last_ylim') and self._last_ylim:
                self.logger.info(f"保存的Y轴范围: {self._last_ylim}")
        
        # 不清空画布，只清除现有的线条，保持坐标轴范围不变
        for line in self.ax.lines:
            line.remove()
        for text in self.ax.texts:
            text.remove()
        if self.ax.legend_:
            self.ax.legend_.remove()
        
        self.ax.set_xlabel('时间 (s)')
        self.ax.set_ylabel('位置 (°)')
        self.ax.set_title('轨迹执行实时监控')
        self.ax.grid(True, alpha=0.3)
        
        # 使用保存的坐标轴范围，如果没有保存的范围则使用当前范围
        if hasattr(self, '_last_xlim') and self._last_xlim:
            self.ax.set_xlim(self._last_xlim)
            if self.logger:
                self.logger.info(f"使用保存的X轴范围: {self._last_xlim}")
        if hasattr(self, '_last_ylim') and self._last_ylim:
            self.ax.set_ylim(self._last_ylim)
            if self.logger:
                self.logger.info(f"使用保存的Y轴范围: {self._last_ylim}")
        
        self.planned_line, = self.ax.plot([], [], 'b-', animated=True, label='规划轨迹')
        self.feedback_line, = self.ax.plot([], [], 'r-', animated=True, label='实际反馈')
        self.ax.legend()
        self.canvas.draw()
        self.background = self.canvas.copy_from_bbox(self.ax.bbox)
        self.latest_progress_data = None # 清空旧数据
        # --- 启动高频定时器（如50ms/20Hz）---
        self.plot_update_timer.setInterval(50)
        self.plot_update_timer.start()
        self.execute_teaching_requested.emit(self.DeviceName, trajectory_name, self.planning_switch.isChecked(), self.current_motor_id)

    def on_motor_id_changed(self, value):
        """电机ID改变时的处理函数"""
        self.current_motor_id = value
        if self.logger:
            self.logger.info(f"电机ID已更改为: {value}")

    def on_trajectory_selection_changed(self, text: str):
        """轨迹选择改变时的处理函数"""
        if not text:
            return

        self._current_trajectory = text
        
        if self.logger:
            self.logger.info(f"轨迹选择已更改为: {text}")
        
        # 更新删除按钮状态
        self.delete_trajectory_button.setEnabled(True)
        
        # 自动切换到轨迹视图并刷新
        # 1. 确保视图在正确的参数模式
        if not self.current_selected_param.startswith('trajectory_'):
            # 使用 blockSignals 避免触发 on_param_changed
            self.param_combo.blockSignals(True)
            self.param_combo.setCurrentText('trajectory_both (原始+规划)')
            self.current_selected_param = 'trajectory_both' # 立即更新内部状态
            self.param_combo.blockSignals(False)
        elif self.current_selected_param != 'trajectory_both':
            # 如果当前已经是轨迹参数但不是trajectory_both，也切换到trajectory_both
            self.param_combo.blockSignals(True)
            self.param_combo.setCurrentText('trajectory_both (原始+规划)')
            self.current_selected_param = 'trajectory_both'
            self.param_combo.blockSignals(False)

        # 2. 直接发送请求，自动刷新曲线
        self.request_trajectory_data.emit(self.DeviceName, self._current_trajectory)

    def on_duration_changed(self, value: float):
        """执行时长改变时的处理函数"""
        if not self._current_trajectory:
            return
        
        if self.logger:
            self.logger.info(f"执行时长已更改为: {value}秒")
        
        # 启用刷新按钮，让用户确认重规划
        self.refresh_button.setEnabled(True)
        # 同时启用恢复按钮
        self.restore_time_button.setEnabled(True)

    def on_restore_time_clicked(self):
        """恢复默认时长按钮点击处理函数"""
        if not self._current_trajectory:
            return
        
        if self.logger:
            self.logger.info("恢复默认时长按钮被点击")
        
        # 1. 立即在UI上恢复时长输入框的值
        self.duration_spin.blockSignals(True)
        self.duration_spin.setValue(self._original_total_time)
        self.duration_spin.blockSignals(False)
        
        # 2. 发射信号，请求后端按原始时间戳进行重规划
        self.restore_default_requested.emit(self.DeviceName, self._current_trajectory)
        
        # 3. 点击后，禁用刷新和恢复按钮，因为UI即将更新到最新状态
        self.refresh_button.setEnabled(False)
        self.restore_time_button.setEnabled(False)

    def on_param_changed(self, param_text: str):
        """参数选择改变时的处理函数"""
        # 停止历史曲线定时更新
        if self.history_update_timer.isActive():
            self.history_update_timer.stop()
        
        # 停止历史数据请求定时器
        if self.history_request_timer.isActive():
            self.history_request_timer.stop()
        
        # 从显示文本中提取参数名
        param_map = {
            'position (位置)': 'position',
            'velocity (速度)': 'velocity',
            'torque (扭矩)': 'torque', 
            'temperature (温度)': 'temperature',
            'error_code (错误码)': 'error_code',
            'motor_can_id (CAN ID)': 'motor_can_id',
            'mode_state (模式状态)': 'mode_state',
            'flt_uninitialized (未初始化故障)': 'flt_uninitialized',
            'flt_hall_encoding (霍尔编码故障)': 'flt_hall_encoding',
            'flt_magnetic_encoding (磁编码故障)': 'flt_magnetic_encoding',
            'flt_over_temperature (过温故障)': 'flt_over_current',
            'flt_voltage_drop (电压跌落故障)': 'flt_voltage_drop',
            'trajectory_teaching (示教轨迹)': 'trajectory_teaching',
            'trajectory_original (原始轨迹)': 'trajectory_original',
            'trajectory_planned (规划轨迹)': 'trajectory_planned',
            'trajectory_both (原始+规划)': 'trajectory_both',
            'trajectory_executed (执行轨迹)': 'trajectory_executed'
        }
        
        self.current_selected_param = param_map.get(param_text, 'position')
        
        if self.logger:
            self.logger.info(f"参数选择已更改为: {param_text} -> {self.current_selected_param}")
        
        # 检查是否是轨迹数据参数
        if self.current_selected_param.startswith('trajectory_'):
            self._show_trajectory = True
            
            # 特殊处理trajectory_executed参数
            if self.current_selected_param == 'trajectory_executed':
                if self._last_execution_data:
                    # 显示保存的执行数据
                    self._display_execution_data(self._last_execution_data)
                else:
                    # 没有执行数据，显示提示
                    self.ax.clear()
                    self.ax.text(0.5, 0.5, '暂无执行轨迹数据\n请先执行一次示教轨迹',
                                 horizontalalignment='center',
                                 verticalalignment='center',
                                 transform=self.ax.transAxes)
                    self.canvas.draw()
                # 禁用时长相关控件
                self.duration_spin.setEnabled(False)
                self.refresh_button.setEnabled(False)
                self.restore_time_button.setEnabled(False)
            elif self.current_selected_param == 'trajectory_teaching':
                # 示教轨迹参数的特殊处理 - 不需要选择轨迹，直接准备记录
                # 注意：如果已经在示教状态，不要重复清空画布
                if not self._is_executing_trajectory:
                    self.ax.clear()
                    self.ax.set_xlabel('时间 (s)')
                    self.ax.set_ylabel('位置 (°)')
                    self.ax.set_title('示教轨迹实时记录')
                    self.ax.grid(True, alpha=0.3)
                    self.canvas.draw()
                # 禁用时长相关控件
                self.duration_spin.setEnabled(False)
                self.refresh_button.setEnabled(False)
                self.restore_time_button.setEnabled(False)
            else:
                # 其他轨迹参数的处理
                if self._current_trajectory:
                    self.request_trajectory_data.emit(self.DeviceName, self._current_trajectory)
                else:
                    # 如果没有选择轨迹，提示用户选择并禁用时长控件
                    self.ax.clear()
                    self.ax.text(0.5, 0.5, '请先从上方选择一条轨迹',
                                 horizontalalignment='center',
                                 verticalalignment='center',
                                 transform=self.ax.transAxes)
                    self.canvas.draw()
                    # 禁用时长相关控件
                    self.duration_spin.setEnabled(False)
                    self.refresh_button.setEnabled(False)
                    self.restore_time_button.setEnabled(False)
        else:
            self._show_trajectory = False
            # 禁用时长相关控件（非轨迹模式）
            self.duration_spin.setEnabled(False)
            self.refresh_button.setEnabled(False)
            self.restore_time_button.setEnabled(False)
            
            # 启动历史数据请求定时器
            if not self.history_request_timer.isActive():
                self.history_request_timer.start()
            
            # 立即清空画布，防止残留上一个参数的曲线
            self.ax.clear()
            self.ax.set_xlabel('时间')
            self.ax.set_ylabel('数值')
            self.ax.grid(True)
            self.ax.text(0.5, 0.5, '加载中...', ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            
            # 如果有历史曲线数据，立即显示
            if self.latest_history_data:
                self._update_history_curve_direct(self.latest_history_data)
            
            # 立即请求一次数据并刷新
            self._should_request_history = True
            self.request_history_data.emit(self.DeviceName, self.current_selected_param)

    def on_refresh_clicked(self):
        """刷新曲线按钮点击处理函数. 根据当前模式决定行为."""
        if self.current_selected_param.startswith('trajectory_') and self._current_trajectory:
            # 轨迹模式：发送重规划请求
            duration = self.duration_spin.value()
            if self.logger:
                self.logger.info(f"刷新轨迹曲线，重规划时长: {duration}秒")
            self.replan_requested.emit(self.DeviceName, self._current_trajectory, duration)
            # 点击后禁用，等待新数据
            self.refresh_button.setEnabled(False)
        else:
            # 普通模式：发送普通刷新请求
            if self.logger:
                self.logger.info(f"刷新历史曲线，参数: {self.current_selected_param}")
            self.request_history_data.emit(self.DeviceName, self.current_selected_param)

    def update_history_curve(self, history_data_dict: dict):
        """更新历史曲线显示"""
        # 从字典中提取绘图数据和元数据
        plot_data = history_data_dict.get('data')
        total_time = history_data_dict.get('total_time')
        
        # 如果是轨迹数据，更新时长控件
        if total_time is not None:
            self._original_total_time = total_time  # 保存原始时长
            self.duration_spin.blockSignals(True)
            self.duration_spin.setValue(total_time)
            self.duration_spin.blockSignals(False)
            self.duration_spin.setEnabled(True)
            # 刚加载完，禁用刷新按钮，启用恢复按钮
            self.refresh_button.setEnabled(False)
            self.restore_time_button.setEnabled(True)
            
        # 检查数据是否为空
        if plot_data is None or (hasattr(plot_data, 'empty') and plot_data.empty):
            # 如果没有数据，清空图形
            self.ax.clear()
            self.ax.set_xlabel('时间')
            self.ax.set_ylabel('数值')
            self.ax.grid(True)
            self.ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            if self.logger:
                self.logger.warning("历史曲线数据为空")
            return
        
        # 检查是否是轨迹数据（DataFrame格式）
        if hasattr(plot_data, 'columns') and 'type' in plot_data.columns:
            # 这是轨迹对比数据，直接更新
            self._update_history_curve_direct(history_data_dict)
        elif hasattr(plot_data, 'columns') and 'time' in plot_data.columns and 'value' in plot_data.columns:
            # 这是DataFrame格式的历史数据，也直接更新
            self._update_history_curve_direct(history_data_dict)
        else:
            # 这是旧的列表格式数据，使用定时更新
            self._update_history_curve_throttled(history_data_dict)

    def _update_history_curve_direct(self, history_data_dict: dict):
        """
        直接更新历史曲线（用于轨迹数据等静态数据）
        """
        # 从字典中提取绘图数据和元数据
        plot_data = history_data_dict.get('data')
        
        # 清空当前图形
        self.ax.clear()
        
        # 检查是否是轨迹数据（DataFrame格式）
        if hasattr(plot_data, 'columns') and 'type' in plot_data.columns:
            # 这是轨迹对比数据
            self._plot_trajectory_comparison(plot_data)
        elif hasattr(plot_data, 'columns') and 'time' in plot_data.columns and 'value' in plot_data.columns:
            # 这是DataFrame格式的历史数据
            self._plot_dataframe_history(plot_data)
        else:
            # 这是旧的列表格式数据
            self._plot_list_history(plot_data)
        
        # 设置标签和网格
        param_labels = {
            'position': '位置 (°)',
            'velocity': '速度 (°/s)',
            'torque': '扭矩 (N·m)',
            'temperature': '温度 (°C)',
            'error_code': '错误码',
            'motor_can_id': 'CAN ID',
            'mode_state': '模式状态',
            'teaching_trajectory': '位置 (°)',
            'flt_uninitialized': '未初始化故障',
            'flt_hall_encoding': '霍尔编码故障',
            'flt_magnetic_encoding': '磁编码故障',
            'flt_over_temperature': '过温故障',
            'flt_over_current': '过流故障',
            'flt_voltage_drop': '电压跌落故障'
        }
        
        self.ax.set_xlabel('时间 (s)')
        self.ax.set_ylabel(param_labels.get(self.current_selected_param, '数值'))
        self.ax.grid(True, alpha=0.3)
        
        # 自动调整布局
        self.figure.tight_layout()
        
        # 刷新画布
        self.canvas.draw()
        
        if self.logger:
            self.logger.info(f"历史曲线直接更新完成，参数: {self.current_selected_param}")

    def _update_history_curve_throttled(self, history_data_dict: dict):
        """
        节流更新历史曲线（用于实时数据）
        """
        # 缓存最新数据
        self.latest_history_data = history_data_dict
        
        # 启动定时器（如果还没启动）
        if not self.history_update_timer.isActive():
            self.history_update_timer.start()
        
        # 如果画布是"加载中..."，立即刷新一次
        if self.ax.texts and any('加载中' in t.get_text() for t in self.ax.texts):
            self._update_history_curve_direct(history_data_dict)

    def _plot_trajectory_comparison(self, df):
        """绘制轨迹对比数据"""
        # 分离原始轨迹和规划轨迹
        original_data = df[df['type'] == 'original']
        planned_data = df[df['type'] == 'planned']
        
        # 绘制原始轨迹
        if not original_data.empty:
            self.ax.plot(original_data['time'], original_data['value'], 'ro-', 
                        linewidth=2, markersize=6, label='原始轨迹')
        
        # 绘制规划轨迹
        if not planned_data.empty:
            self.ax.plot(planned_data['time'], planned_data['value'], 'b-', 
                        linewidth=2, label='规划轨迹')
        
        # 添加图例
        if not original_data.empty or not planned_data.empty:
            self.ax.legend()
        
        # 设置标题
        self.ax.set_title('轨迹对比')
        
        # 正确设置和保存坐标轴范围
        all_times = []
        all_values = []
        
        # 收集所有时间点和位置点
        if not original_data.empty:
            all_times.extend(original_data['time'].tolist())
            all_values.extend(original_data['value'].tolist())
        if not planned_data.empty:
            all_times.extend(planned_data['time'].tolist())
            all_values.extend(planned_data['value'].tolist())
        
        # 设置X轴范围
        if all_times:
            x_min, x_max = min(all_times), max(all_times)
            x_margin = (x_max - x_min) * 0.05 if x_max > x_min else 0.1
            self.ax.set_xlim(x_min - x_margin, x_max + x_margin)
            self._last_xlim = (x_min - x_margin, x_max + x_margin)
            
            # 设置Y轴范围
            if all_values:
                y_min, y_max = min(all_values), max(all_values)
                if y_min == y_max:
                    y_margin = 1.0
                else:
                    y_margin = (y_max - y_min) * 0.1
                self.ax.set_ylim(y_min - y_margin, y_max + y_margin)
                self._last_ylim = (y_min - y_margin, y_max + y_margin)
                
                if self.logger:
                    self.logger.info(f"轨迹对比设置X轴范围: {self._last_xlim}")
                    self.logger.info(f"轨迹对比设置Y轴范围: {self._last_ylim}")

    def _plot_dataframe_history(self, df):
        """绘制DataFrame格式的历史数据"""
        times = df['time'].tolist()
        values = df['value'].tolist()

        if self.current_selected_param == 'teaching_trajectory':
            self.ax.set_title('示教轨迹实时记录')
        
        # 检查是否是 mode_state 参数（字符串类型）
        if self.current_selected_param == 'mode_state':
            # 对于 mode_state，使用散点图显示状态变化
            self.ax.scatter(times, values, c='red', s=50, alpha=0.7)
            
            # 为不同的状态值添加标签
            unique_values = list(set(values))
            for i, value in enumerate(unique_values):
                # 找到该状态值对应的所有时间点
                value_times = [t for t, v in zip(times, values) if v == value]
                if value_times:
                    # 在第一个时间点添加标签
                    self.ax.annotate(str(value), 
                                   xy=(value_times[0], value), 
                                   xytext=(5, 5), 
                                   textcoords='offset points',
                                   fontsize=10,
                                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
            
            # 设置Y轴为分类轴
            self.ax.set_yticks(unique_values)
            self.ax.set_yticklabels([str(v) for v in unique_values])
            
        else:
            # 对于数值类型参数，使用线图
            self.ax.plot(times, values, 'b-', linewidth=2, marker='o', markersize=3)
            
            # 设置Y轴范围
            if values:
                min_val = min(values)
                max_val = max(values)
                if min_val == max_val:
                    self.ax.set_ylim(min_val - 1, max_val + 1)
                else:
                    margin = (max_val - min_val) * 0.1
                    self.ax.set_ylim(min_val - margin, max_val + margin)

        # 正确设置和保存坐标轴范围
        if times and values:
            # 设置X轴范围
            x_min, x_max = min(times), max(times)
            x_margin = (x_max - x_min) * 0.05 if x_max > x_min else 0.1
            self.ax.set_xlim(x_min - x_margin, x_max + x_margin)
            self._last_xlim = (x_min - x_margin, x_max + x_margin)
            
            # 设置Y轴范围
            y_min, y_max = min(values), max(values)
            if y_min == y_max:
                y_margin = 1.0
            else:
                y_margin = (y_max - y_min) * 0.1
            self.ax.set_ylim(y_min - y_margin, y_max + y_margin)
            self._last_ylim = (y_min - y_margin, y_max + y_margin)
            
            if self.logger:
                self.logger.info(f"DataFrame历史数据设置X轴范围: {self._last_xlim}")
                self.logger.info(f"DataFrame历史数据设置Y轴范围: {self._last_ylim}")

    def _plot_list_history(self, history_data):
        """绘制列表格式的历史数据"""
        # 提取时间和数值数据
        timestamps = []
        values = []
        
        for timestamp, value in history_data:
            # 转换时间戳为datetime对象
            dt = datetime.fromtimestamp(timestamp)
            timestamps.append(dt)
            values.append(value)
        
        # 绘制曲线
        self.ax.plot(timestamps, values, 'b-', linewidth=2, marker='o', markersize=3)
        
        # 设置Y轴范围
        if values:
            min_val = min(values)
            max_val = max(values)
            if min_val == max_val:
                self.ax.set_ylim(min_val - 1, max_val + 1)
            else:
                margin = (max_val - min_val) * 0.1
                self.ax.set_ylim(min_val - margin, max_val + margin)
        
        # 格式化x轴时间显示（仅对列表格式的历史数据）
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())

    def update_trajectory_curve(self, trajectory_data):
        """更新轨迹曲线显示"""
        if not trajectory_data:
            # 如果没有数据，清空图形
            self.ax.clear()
            self.ax.set_xlabel('时间')
            self.ax.set_ylabel('位置 (°)')
            self.ax.grid(True)
            self.ax.text(0.5, 0.5, '暂无轨迹数据', ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            if self.logger:
                self.logger.warning("轨迹数据为空")
            return
        
        # 清空当前图形
        self.ax.clear()
        
        original_times = trajectory_data.get('original_times', [])
        original_positions = trajectory_data.get('original_positions', [])
        planned_times = trajectory_data.get('planned_times', [])
        planned_positions = trajectory_data.get('planned_positions', [])
        trajectory_name = trajectory_data.get('trajectory_name', '')
        total_time = trajectory_data.get('total_time')

        # 更新并启用时长控制器
        if total_time is not None:
            self.duration_spin.blockSignals(True)
            self.duration_spin.setValue(total_time)
            self.duration_spin.blockSignals(False)
            self.duration_spin.setEnabled(True)
            # 禁用刷新按钮（因为当前显示的是原始规划结果）
            self.refresh_button.setEnabled(False)
        
        # 根据选择的参数类型绘制不同的曲线
        if self.current_selected_param == 'trajectory_original' and original_times:
            # 绘制原始轨迹
            self.ax.plot(original_times, original_positions, 'ro-', linewidth=2, markersize=6, label='原始轨迹')
            self.ax.set_title(f'原始轨迹: {trajectory_name}')
            
        elif self.current_selected_param == 'trajectory_planned' and planned_times:
            # 绘制规划轨迹
            self.ax.plot(planned_times, planned_positions, 'b-', linewidth=2, label='规划轨迹')
            self.ax.set_title(f'规划轨迹: {trajectory_name}')
            
        elif self.current_selected_param == 'trajectory_both' and (original_times or planned_times):
            # 绘制原始轨迹和规划轨迹
            if original_times:
                self.ax.plot(original_times, original_positions, 'ro-', linewidth=2, markersize=6, label='原始轨迹')
            if planned_times:
                self.ax.plot(planned_times, planned_positions, 'b-', linewidth=2, label='规划轨迹')
            self.ax.set_title(f'轨迹对比: {trajectory_name}')
            self.ax.legend()
        
        # 设置标签和网格
        self.ax.set_xlabel('时间 (s)')
        self.ax.set_ylabel('位置 (°)')
        self.ax.grid(True, alpha=0.3)
        
        # --- 设置坐标轴范围，确保曲线完整可见 ---
        all_times = []
        all_positions = []
        
        # 收集所有时间点和位置点
        if original_times and original_positions:
            all_times.extend(original_times)
            all_positions.extend(original_positions)
        if planned_times and planned_positions:
            all_times.extend(planned_times)
            all_positions.extend(planned_positions)
        
        # 设置X轴范围
        if all_times:
            x_min, x_max = min(all_times), max(all_times)
            x_margin = (x_max - x_min) * 0.05 if x_max > x_min else 0.1
            self.ax.set_xlim(x_min - x_margin, x_max + x_margin)
            self._last_xlim = (x_min - x_margin, x_max + x_margin)
            if self.logger:
                self.logger.info(f"设置X轴范围: {self._last_xlim}")
        
        # 设置Y轴范围
        if all_positions:
            y_min, y_max = min(all_positions), max(all_positions)
            if y_min == y_max:
                y_margin = 1.0
            else:
                y_margin = (y_max - y_min) * 0.1
            self.ax.set_ylim(y_min - y_margin, y_max + y_margin)
            self._last_ylim = (y_min - y_margin, y_max + y_margin)
            if self.logger:
                self.logger.info(f"设置Y轴范围: {self._last_ylim}")
        
        # 自动调整布局
        self.figure.tight_layout()
        
        # 刷新画布
        self.canvas.draw()
        
        if self.logger:
            self.logger.info(f"轨迹曲线更新完成，轨迹名: {trajectory_name}")

    def on_jog_pressed(self):
        """点动按钮按下时的处理函数"""
        if self.logger:
            self.logger.info(f"点动按钮按下，电机ID: {self.current_motor_id}, 速度: {self.speed_spin.value()}")
        self.send_command('jog_motor', [self.current_motor_id, self.speed_spin.value()])
        

    def on_jog_released(self):
        """点动按钮释放时的处理函数"""
        if self.logger:
            self.logger.info(f"点动按钮释放，电机ID: {self.current_motor_id}")
        self.send_command('stop_jog_motor', [self.current_motor_id])

    def on_init_clicked(self):
        """初始化按钮点击处理函数"""
        if self.logger:
            self.logger.info(f"初始化按钮被点击，电机ID: {self.id_spin.value()}")
        self.send_command('init_motor', [self.id_spin.value()])

    def on_enable_clicked(self):
        """使能按钮点击处理函数"""
        if self.logger:
            self.logger.info(f"使能按钮被点击，电机ID: {self.id_spin.value()}")
        self.send_command('enable_motor', [self.id_spin.value()])   

    def on_disable_clicked(self):
        """失能按钮点击处理函数"""
        if self.logger:
            self.logger.info(f"失能按钮被点击，电机ID: {self.id_spin.value()}")
        self.send_command('disable_motor', [self.id_spin.value()])

    def on_set_pos_clicked(self):
        """设置位置按钮点击处理函数"""
        if self.logger:
            self.logger.info(f"设置位置按钮被点击，电机ID: {self.id_spin.value()}, 位置: {self.pos_spin.value()}")
        self.send_command('set_motor_position', [self.id_spin.value(), self.pos_spin.value()])

    def on_set_pos_speed_clicked(self):
        """设置位置和速度按钮点击处理函数"""
        if self.logger:
            self.logger.info(f"设置位置和速度按钮被点击，电机ID: {self.id_spin.value()}, 位置: {self.pos_spin.value()}, 速度: {self.speed_spin.value()}")
        self.send_command('set_motor_pos_speed', [self.id_spin.value(), self.pos_spin.value(), self.speed_spin.value()])

    def on_sim_data_clicked(self):
        """模拟数据按钮点击处理函数"""
        if self.logger:
            self.logger.info(f"模拟数据按钮被点击，电机ID: {self.id_spin.value()}")
        self.request_sim_data.emit(self.DeviceName)

    def update_motor_data(self, state_dict: dict):
        if self.logger:
            self.logger.info(f"更新电机数据: {state_dict}")
        position = state_dict.get('position', 0.0)
        speed = state_dict.get('velocity', 0.0)
        torque = state_dict.get('torque', 0.0)
        temperature = state_dict.get('temperature', 0.0)
        self.pos_display.setText(f"{position:.1f}°")
        self.speed_display.setText(f"{speed:.1f}°/s")
        self.torque_display.setText(f"{torque:.1f} N·m")
        self.temp_display.setText(f"{temperature:.1f}°C")

    def send_command(self, command: str, args: list):
        """发送设备命令"""
        command_str = command + "(" + ",".join(str(arg) for arg in args) + ")"
        if self.logger:
            self.logger.info(f"DeepMotorPage: 发送命令: {command_str}")
        self.ui_deepmotor_command.emit(self.DeviceName, command_str)

    def init_trajectory_list(self):
        """初始化轨迹列表"""
        # 使用QTimer延迟发送请求信号，确保所有组件都已初始化
        QTimer.singleShot(100, lambda: self.request_trajectory_list.emit(self.DeviceName))

    def on_planning_switch_changed(self, checked: bool):
        """轨迹规划开关改变时的处理函数"""
        self.use_planned_trajectory = checked
        # 更新开关文本
        self.planning_switch.setText('开启' if checked else '关闭')
        if self.logger:
            self.logger.info(f"轨迹规划开关已更改为: {'开启' if checked else '关闭'}")

    def update_trajectory_execution_progress(self, device_id: str, progress_data: dict):
        """
        更新轨迹执行进度显示 - 此方法被高频调用
        :param device_id: 设备ID (从信号接收，当前未使用)
        :param progress_data: 包含执行进度信息的字典
        """
        # 只保存最新数据，不主动刷新UI，彻底解耦
        self._last_execution_data = progress_data.copy()
        self.latest_progress_data = progress_data

        if not self._is_executing_trajectory:
            # 如果不在执行状态，但当前显示的是trajectory_executed参数，则立即更新显示
            if self.current_selected_param == 'trajectory_executed':
                self._display_execution_data(progress_data)
            return

        # 只更新轻量级的状态标签，避免UI阻塞
        current_point = progress_data.get('current_point', 0)
        total_points = progress_data.get('total_points', 1)
        progress_percent = int((current_point / total_points) * 100) if total_points > 0 else 0
        self.teaching_status_label.setText(f'示教状态: 执行中 ({progress_percent}%)')

    def _throttled_plot_update(self):
        """
        节流的绘图更新方法，由QTimer定时调用 - 使用Blitting技术优化性能
        """
        if self.latest_progress_data and self._is_executing_trajectory and self.background:
            data = self.latest_progress_data
            
            # 恢复背景
            # self.canvas.restore_region(self.background)

            # 更新曲线数据
            self.planned_line.set_data(data.get('executed_times', []), data.get('executed_positions', []))
            self.feedback_line.set_data(data.get('feedback_times', []), data.get('feedback_positions', []))

            # 只重绘更新过的艺术家
            self.ax.draw_artist(self.planned_line)
            self.ax.draw_artist(self.feedback_line)

            # 将更新后的区域"贴"到画布上
            self.canvas.blit(self.ax.bbox)
            self.canvas.flush_events()

    def _throttled_history_update(self):
        """
        节流的历史曲线更新方法，由QTimer定时调用
        """
        if self.latest_history_data and not self._is_history_updating:
            # 计算当前数据的hash值
            current_hash = self._calculate_history_data_hash(self.latest_history_data)
            
            # 如果数据没有变化，跳过更新
            if current_hash == self._last_drawn_history_data_hash:
                return
            
            self._is_history_updating = True
            try:
                self.update_history_curve(self.latest_history_data)
                # 更新hash值
                self._last_drawn_history_data_hash = current_hash
            finally:
                self._is_history_updating = False

    def _calculate_history_data_hash(self, history_data_dict: dict):
        """计算历史数据的hash值，用于判断数据是否发生变化"""
        try:
            plot_data = history_data_dict.get('data')
            if plot_data is None:
                return None
            
            # 对于DataFrame，使用其内容的hash
            if hasattr(plot_data, 'to_string'):
                data_str = plot_data.to_string()
            elif isinstance(plot_data, list):
                data_str = str(plot_data)
            else:
                data_str = str(plot_data)
            
            return hashlib.md5(data_str.encode()).hexdigest()
        except Exception:
            return None

    def on_trajectory_execution_finished(self):
        """轨迹执行完成时的处理函数"""
        if self.logger:
            self.logger.info("轨迹执行完成")
        # 恢复定时器为默认频率（如50ms/20Hz）
        self.plot_update_timer.setInterval(50)
        self.plot_update_timer.stop()
        
        # 停止历史曲线定时更新
        if self.history_update_timer.isActive():
            self.history_update_timer.stop()
        
        self._is_executing_trajectory = False
        self.update_execution_buttons_state()
        if self.planned_line:
            self.planned_line.set_animated(False)
        if self.feedback_line:
            self.feedback_line.set_animated(False)
        self.background = None
        self.teaching_status_label.setText('示教状态: 执行完成')
        self.teaching_status_label.setStyleSheet("color: green;")
        # --- 强制全量刷新一次，确保所有反馈点都显示 ---
        if self._last_execution_data:
            self._display_execution_data(self._last_execution_data)
        QTimer.singleShot(3000, lambda: self.teaching_status_label.setText('示教状态: 未开始'))
        QTimer.singleShot(3000, lambda: self.teaching_status_label.setStyleSheet("color: gray;"))

    def on_trajectory_execution_error(self, error_message: str):
        """轨迹执行错误时的处理函数"""
        if self.logger:
            self.logger.error(f"轨迹执行错误: {error_message}")
            
        # 停止UI更新定时器
        self.plot_update_timer.stop()
        
        # 停止历史曲线定时更新
        if self.history_update_timer.isActive():
            self.history_update_timer.stop()
        
        # 停止历史数据请求定时器
        if self.history_request_timer.isActive():
            self.history_request_timer.stop()
        
        # 恢复执行状态和按钮
        self._is_executing_trajectory = False
        self.update_execution_buttons_state()
        
        # 恢复Line2D为非动画模式，并清除背景缓存
        if self.planned_line:
            self.planned_line.set_animated(False)
        if self.feedback_line:
            self.feedback_line.set_animated(False)
        self.background = None
        
        # 更新状态标签
        self.teaching_status_label.setText(f'示教状态: 执行失败')
        self.teaching_status_label.setStyleSheet("color: red;")
        
        # 3秒后恢复默认状态
        QTimer.singleShot(3000, lambda: self.teaching_status_label.setText('示教状态: 未开始'))
        QTimer.singleShot(3000, lambda: self.teaching_status_label.setStyleSheet("color: gray;"))

    def update_teaching_trajectory(self, times: list, positions: list):
        """
        更新示教轨迹实时显示
        :param times: 时间列表
        :param positions: 位置列表
        """
        if not self._is_executing_trajectory or self.current_selected_param != 'trajectory_teaching':
            return
            
        # 检查是否有新的数据点
        if not times or not positions:
            return
            
        # 如果是第一次更新，清空画布并设置基本属性
        if len(times) == 1:
            self.ax.clear()
            self.ax.set_xlabel('时间 (s)')
            self.ax.set_ylabel('位置 (°)')
            self.ax.set_title('示教轨迹实时记录')
            self.ax.grid(True, alpha=0.3)
            # 绘制第一个点
            self.ax.plot(times, positions, 'go', markersize=6, label='示教轨迹')
            self.ax.legend()
        else:
            # 增量更新：只绘制最新的点
            # 获取最新的两个点用于绘制线段
            if len(times) >= 2:
                # 绘制从倒数第二个点到最新点的线段
                self.ax.plot(times[-2:], positions[-2:], 'g-', linewidth=2)
                # 更新最新点的标记
                self.ax.plot(times[-1], positions[-1], 'go', markersize=4)
            else:
                # 只有一个点时，只绘制点
                self.ax.plot(times[-1], positions[-1], 'go', markersize=4)
        
        # 自动调整布局
        self.figure.tight_layout()
        
        # 刷新画布
        self.canvas.draw()

    def _display_execution_data(self, progress_data: dict):
        """
        显示执行数据（用于非执行状态下的显示）
        """
        executed_times = progress_data.get('executed_times', [])
        executed_positions = progress_data.get('executed_positions', [])
        feedback_times = progress_data.get('feedback_times', [])
        feedback_positions = progress_data.get('feedback_positions', [])
        
        # 清空当前图形
        self.ax.clear()
        
        # 绘制已执行的规划轨迹（蓝色实线）
        if executed_times and executed_positions:
            self.ax.plot(executed_times, executed_positions, 'b-', linewidth=2, label='规划轨迹')
        
        # 绘制实时反馈轨迹（红色实线）
        if feedback_times and feedback_positions:
            self.ax.plot(feedback_times, feedback_positions, 'r-', linewidth=2, label='实际反馈')
        
        # 设置标签和网格
        self.ax.set_xlabel('时间 (s)')
        self.ax.set_ylabel('位置 (°)')
        self.ax.set_title('轨迹执行结果')
        self.ax.grid(True, alpha=0.3)
        
        # 添加图例
        if (executed_times and executed_positions) or (feedback_times and feedback_positions):
            self.ax.legend()
        
        # 自动调整布局
        self.figure.tight_layout()
        
        # 刷新画布
        self.canvas.draw()

    def on_delete_trajectory_clicked(self):
        """删除轨迹按钮点击处理函数"""
        trajectory_name = self.trajectory_combo.currentText()
        if not trajectory_name:
            if self.logger:
                self.logger.warning("请先选择要删除的轨迹")
            return
        
        if self.logger:
            self.logger.info(f"删除轨迹按钮被点击，轨迹: {trajectory_name}")
        
        # 发送删除轨迹信号
        self.delete_trajectory_requested.emit(self.DeviceName, trajectory_name)

    def _request_history_data(self):
        """
        历史数据请求定时器处理函数
        """
        if self._should_request_history:
            self.request_history_data.emit(self.DeviceName, self.current_selected_param)
            self._should_request_history = False

class DeepArmPage(QWidget):
    """DeepArm 控制页面"""
    ui_device_command = Signal(str, str)  # 设备命令信号

    def __init__(self, log_manager: LogManager = None, config_manager: ConfigManager = None, parent=None):
        super().__init__(parent=parent)
        self.log_manager = log_manager
        self.logger = self.log_manager.get_logger(__name__) if self.log_manager else None
        self.config_manager = config_manager
        
        if self.logger:
            self.logger.info("DeepArm页面初始化开始")
        self.setup_ui()
        if self.logger:
            self.logger.info("DeepArm页面初始化完成")

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
        
        if self.logger:
            self.logger.info("DeepArm页面UI设置完成")

class DeepToyPage(QWidget):
    """DeepToy 控制页面"""
    ui_device_command = Signal(str, str)  # 设备命令信号

    def __init__(self, log_manager: LogManager = None, config_manager: ConfigManager = None, parent=None):
        super().__init__(parent=parent)
        self.log_manager = log_manager
        self.logger = self.log_manager.get_logger(__name__) if self.log_manager else None
        self.config_manager = config_manager
        
        if self.logger:
            self.logger.info("DeepToy页面初始化开始")
        self.setup_ui()
        if self.logger:
            self.logger.info("DeepToy页面初始化完成")

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
        
        if self.logger:
            self.logger.info("DeepToy页面UI设置完成") 