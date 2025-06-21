from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
from qfluentwidgets import (PrimaryPushButton, ComboBox, SpinBox, FluentIcon as FIF, CardWidget, FlowLayout)

# 添加matplotlib支持
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime
import time

class SerialConfigWidget(CardWidget):
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
    request_history_data = Signal(str, str)  # 请求历史数据信号 (设备名, 参数名)
    # 示教相关信号
    start_teaching_requested = Signal(str)  # 开始示教信号
    stop_teaching_requested = Signal(str)   # 停止示教信号
    execute_teaching_requested = Signal(str, str)  # 执行示教信号 (设备名, 轨迹名)
    # 新增：轨迹可视化相关信号
    request_trajectory_data = Signal(str, str)  # 请求轨迹数据信号 (设备名, 轨迹名)
    request_trajectory_list = Signal(str)  # 请求轨迹列表信号

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.DeviceName = "DeepMotor"
        self.current_motor_id = 1  # 当前选中的电机ID
        self._is_jogging = False  # 添加点动状态标志
        self.current_selected_param = "position"  # 当前选中的参数
        self._is_teaching = False  # 示教状态标志
        self._current_trajectory = ""  # 当前选中的轨迹
        self._show_trajectory = False  # 是否显示轨迹模式
        self.setup_ui()
        
        # 初始化轨迹列表
        self.init_trajectory_list()

    def setup_ui(self):
        """初始化界面"""
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
        trajectory_label = QLabel('轨迹:')
        self.trajectory_combo = ComboBox()
        self.trajectory_combo.setMinimumWidth(150)
        
        teaching_controls_layout.addWidget(self.start_teaching_button)
        teaching_controls_layout.addWidget(self.stop_teaching_button)
        teaching_controls_layout.addWidget(self.execute_teaching_button)
        teaching_controls_layout.addWidget(trajectory_label)
        teaching_controls_layout.addWidget(self.trajectory_combo)
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
        history_group.setMinimumHeight(350)  # 新增：设置最小高度
        history_layout = QVBoxLayout(history_group)
        
        # 历史曲线标题
        history_title = QLabel('历史曲线')
        history_title.setObjectName('cardTitle')
        history_layout.addWidget(history_title)
        
        # 参数选择和控制
        param_control_layout = QHBoxLayout()
        param_label = QLabel('选择参数:')
        self.param_combo = ComboBox()
        # 根据DeepMotorState的属性添加选项
        self.param_combo.addItems([
            'position (位置)',
            'velocity (速度)', 
            'torque (扭矩)',
            'temperature (温度)',
            'error_code (错误码)',
            'motor_can_id (CAN ID)',
            'mode_state (模式状态)',
            'flt_uninitialized (未初始化故障)',
            'flt_hall_encoding (霍尔编码故障)',
            'flt_magnetic_encoding (磁编码故障)',
            'flt_over_temperature (过温故障)',
            'flt_over_current (过流故障)',
            'flt_voltage_drop (电压跌落故障)',
            '--- 示教与轨迹 ---',
            '示教轨迹',
            'trajectory_original (原始轨迹)',
            'trajectory_planned (规划轨迹)',
            'trajectory_both (原始+规划)'
        ])
        self.param_combo.setCurrentText('position (位置)')
        
        # 刷新按钮
        self.refresh_button = PrimaryPushButton('刷新曲线')
        
        param_control_layout.addWidget(param_label)
        param_control_layout.addWidget(self.param_combo)
        param_control_layout.addWidget(self.refresh_button)
        param_control_layout.addStretch()
        
        history_layout.addLayout(param_control_layout)
        
        # 创建matplotlib图形
        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(300)  # 新增：设置画布最小高度
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
        
        # 连接轨迹选择信号
        self.trajectory_combo.currentTextChanged.connect(self.on_trajectory_selection_changed)
        
        # 初始化示教按钮状态
        self.update_teaching_buttons_state()

    def update_teaching_buttons_state(self):
        """更新示教按钮状态"""
        if self._is_teaching:
            self.start_teaching_button.setEnabled(False)
            self.stop_teaching_button.setEnabled(True)
            self.execute_teaching_button.setEnabled(False)
            self.teaching_status_label.setText('示教状态: 录制中')
            self.teaching_status_label.setStyleSheet("color: red;")
        else:
            self.start_teaching_button.setEnabled(True)
            self.stop_teaching_button.setEnabled(False)
            self.execute_teaching_button.setEnabled(True)
            self.teaching_status_label.setText('示教状态: 未开始')
            self.teaching_status_label.setStyleSheet("color: gray;")

    def update_trajectory_list(self, trajectory_names: list):
        """更新轨迹列表"""
        self.trajectory_combo.clear()
        self.trajectory_combo.addItems(trajectory_names)

    def on_start_teaching_clicked(self):
        """开始示教按钮点击处理函数"""
        print(f"--------------------------------------------------on_start_teaching_clicked")
        self._is_teaching = True
        self.update_teaching_buttons_state()
        
        # 自动切换到示教轨迹视图并清空画布
        self.param_combo.setCurrentText('示教轨迹')
        self.ax.clear()
        self.ax.set_xlabel('时间 (s)')
        self.ax.set_ylabel('位置 (°)')
        self.ax.set_title('示教轨迹实时记录')
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
        
        # 发送开始示教信号
        self.start_teaching_requested.emit(self.DeviceName)

    def on_stop_teaching_clicked(self):
        """结束示教按钮点击处理函数"""
        print(f"--------------------------------------------------on_stop_teaching_clicked")
        self._is_teaching = False
        self.update_teaching_buttons_state()
        
        # 发送结束示教信号
        self.stop_teaching_requested.emit(self.DeviceName)

    def on_execute_teaching_clicked(self):
        """执行示教按钮点击处理函数"""
        print(f"--------------------------------------------------on_execute_teaching_clicked")
        trajectory_name = self.trajectory_combo.currentText()
        if not trajectory_name:
            print("请先选择要执行的轨迹")
            return
        
        # 发送执行示教信号
        self.execute_teaching_requested.emit(self.DeviceName, trajectory_name)

    def on_motor_id_changed(self, value):
        """电机ID改变时的处理函数"""
        self.current_motor_id = value

    def on_trajectory_selection_changed(self, text: str):
        """轨迹选择改变时的处理函数"""
        if not text:
            return

        self._current_trajectory = text
        
        # 如果当前参数是轨迹相关的，则自动请求新选择的轨迹数据
        if self.current_selected_param.startswith('trajectory_'):
            self.request_trajectory_data.emit(self.DeviceName, self._current_trajectory)

    def on_param_changed(self, param_text: str):
        """参数选择改变时的处理函数"""
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
            '示教轨迹': 'teaching_trajectory',
            'trajectory_original (原始轨迹)': 'trajectory_original',
            'trajectory_planned (规划轨迹)': 'trajectory_planned',
            'trajectory_both (原始+规划)': 'trajectory_both'
        }
        
        self.current_selected_param = param_map.get(param_text, 'position')
        
        # 检查是否是轨迹数据参数
        if self.current_selected_param.startswith('trajectory_'):
            self._show_trajectory = True
            # 如果有选中的轨迹，请求轨迹数据
            if self._current_trajectory:
                self.request_trajectory_data.emit(self.DeviceName, self._current_trajectory)
            else:
                # 如果没有选择轨迹，提示用户选择
                self.ax.clear()
                self.ax.text(0.5, 0.5, '请先从上方选择一条轨迹',
                             horizontalalignment='center',
                             verticalalignment='center',
                             transform=self.ax.transAxes)
                self.canvas.draw()
        else:
            self._show_trajectory = False
            # 自动刷新曲线
            self.on_refresh_clicked()

    def on_refresh_clicked(self):
        """刷新曲线按钮点击处理函数"""
        print('on_refresh_clicked', self.DeviceName, self.current_selected_param)
        self.request_history_data.emit(self.DeviceName, self.current_selected_param)

    def update_history_curve(self, history_data):
        """更新历史曲线显示"""
        # 检查数据是否为空
        if history_data is None or (hasattr(history_data, 'empty') and history_data.empty):
            # 如果没有数据，清空图形
            self.ax.clear()
            self.ax.set_xlabel('时间')
            self.ax.set_ylabel('数值')
            self.ax.grid(True)
            self.ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            return
        
        # 清空当前图形
        self.ax.clear()
        
        # 检查是否是轨迹数据（DataFrame格式）
        if hasattr(history_data, 'columns') and 'type' in history_data.columns:
            # 这是轨迹对比数据
            self._plot_trajectory_comparison(history_data)
        elif hasattr(history_data, 'columns') and 'time' in history_data.columns and 'value' in history_data.columns:
            # 这是DataFrame格式的历史数据
            self._plot_dataframe_history(history_data)
        else:
            # 这是旧的列表格式数据
            self._plot_list_history(history_data)
        
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
            return
        
        # 清空当前图形
        self.ax.clear()
        
        original_times = trajectory_data.get('original_times', [])
        original_positions = trajectory_data.get('original_positions', [])
        planned_times = trajectory_data.get('planned_times', [])
        planned_positions = trajectory_data.get('planned_positions', [])
        trajectory_name = trajectory_data.get('trajectory_name', '')
        
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
        
        # 自动调整布局
        self.figure.tight_layout()
        
        # 刷新画布
        self.canvas.draw()

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
        print(f"--------------------------------------------------send_command")
        command_str = command + "(" + ",".join(str(arg) for arg in args) + ")"
        print(f"DeepMotorPage: 发送命令: {command_str}")
        self.ui_deepmotor_command.emit(self.DeviceName, command_str)

    def init_trajectory_list(self):
        """初始化轨迹列表"""
        # 使用QTimer延迟发送请求信号，确保所有组件都已初始化
        QTimer.singleShot(100, lambda: self.request_trajectory_list.emit(self.DeviceName))

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