from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox
from qfluentwidgets import (CardWidget, PrimaryPushButton, ComboBox, 
                           FluentIcon as FIF, FlowLayout, SwitchButton)

from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager

class DeepArmTeachingCard(CardWidget):
    """DeepArm 示教卡片 - 包含示教控制和轨迹管理功能"""
    
    # 信号定义
    start_teaching_requested = Signal()  # 开始示教信号
    stop_teaching_requested = Signal()   # 停止示教信号
    execute_teaching_requested = Signal(str, bool)  # 执行示教信号 (轨迹名, 是否使用规划轨迹)
    
    # 轨迹管理信号
    request_trajectory_data = Signal(str)  # 请求轨迹数据信号 (轨迹名)
    request_trajectory_list = Signal()  # 请求轨迹列表信号
    replan_requested = Signal(str, float)  # 重规划信号 (轨迹名, 新时长)
    restore_default_requested = Signal(str) # 恢复默认信号 (轨迹名)
    delete_trajectory_requested = Signal(str) # 删除轨迹信号 (轨迹名)

    def __init__(self, logger: LogManager = None, config_manager: ConfigManager = None, parent=None):
        super().__init__(parent)
        self.logger = logger
        self.config_manager = config_manager
        
        # 初始化属性
        self._current_trajectory = None
        self._is_executing_trajectory = False
        self._original_total_time = None
        
        self.setup_ui()
        self.setup_signals()
        self.init_trajectory_list()

    def setup_ui(self):
        """初始化示教卡片界面"""
        if self.logger:
            self.logger.info("开始设置DeepArm示教卡片UI")
            
        # 设置卡片标题
        self.setObjectName('示教卡片')
        
        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # 添加标题
        title_label = QLabel('示教控制')
        title_label.setObjectName('cardTitle')
        main_layout.addWidget(title_label)
        
        # 创建示教控制区域
        self._create_teaching_control_area(main_layout)
        
        # 创建轨迹管理区域
        self._create_trajectory_management_area(main_layout)
        
        # 创建状态显示区域
        self._create_status_area(main_layout)
        
        if self.logger:
            self.logger.info("DeepArm示教卡片UI设置完成")

    def _create_teaching_control_area(self, parent_layout):
        """创建示教控制区域"""
        # 示教控制标题
        teaching_title = QLabel('示教操作')
        teaching_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        parent_layout.addWidget(teaching_title)
        
        # 创建示教控制布局
        teaching_layout = QHBoxLayout()
        teaching_layout.setSpacing(10)
        
        # 示教控制按钮
        self.start_teaching_button = PrimaryPushButton('开始示教', self)
        self.start_teaching_button.setIcon(FIF.EDIT)
        
        self.stop_teaching_button = PrimaryPushButton('结束示教', self)
        self.stop_teaching_button.setIcon(FIF.PAUSE)
        self.stop_teaching_button.setEnabled(False)
        
        self.execute_teaching_button = PrimaryPushButton('执行示教', self)
        self.execute_teaching_button.setIcon(FIF.PLAY)
        
        # 添加按钮到布局
        teaching_layout.addWidget(self.start_teaching_button)
        teaching_layout.addWidget(self.stop_teaching_button)
        teaching_layout.addWidget(self.execute_teaching_button)
        teaching_layout.addStretch()
        
        parent_layout.addLayout(teaching_layout)

    def _create_trajectory_management_area(self, parent_layout):
        """创建轨迹管理区域"""
        # 轨迹管理标题
        trajectory_title = QLabel('轨迹管理')
        trajectory_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        parent_layout.addWidget(trajectory_title)
        
        # 创建轨迹管理布局
        trajectory_layout = QHBoxLayout()
        trajectory_layout.setSpacing(10)
        
        # 轨迹选择
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
        self.duration_spin.setEnabled(False)
        
        # 轨迹规划开关
        planning_label = QLabel('轨迹规划:')
        self.planning_switch = SwitchButton('关闭')
        self.planning_switch.setChecked(False)  # 默认关闭
        
        # 轨迹操作按钮
        self.refresh_button = PrimaryPushButton('刷新轨迹')
        self.refresh_button.setEnabled(False)
        
        self.restore_time_button = PrimaryPushButton('恢复默认')
        self.restore_time_button.setEnabled(False)
        
        self.delete_trajectory_button = PrimaryPushButton('删除轨迹')
        self.delete_trajectory_button.setEnabled(False)
        
        # 添加组件到布局
        trajectory_layout.addWidget(trajectory_label)
        trajectory_layout.addWidget(self.trajectory_combo)
        trajectory_layout.addWidget(duration_label)
        trajectory_layout.addWidget(self.duration_spin)
        trajectory_layout.addWidget(planning_label)
        trajectory_layout.addWidget(self.planning_switch)
        trajectory_layout.addWidget(self.refresh_button)
        trajectory_layout.addWidget(self.restore_time_button)
        trajectory_layout.addWidget(self.delete_trajectory_button)
        trajectory_layout.addStretch()
        
        parent_layout.addLayout(trajectory_layout)

    def _create_status_area(self, parent_layout):
        """创建状态显示区域"""
        # 状态显示标题
        status_title = QLabel('示教状态')
        status_title.setStyleSheet("font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        parent_layout.addWidget(status_title)
        
        # 状态标签
        self.teaching_status_label = QLabel('示教状态: 未开始')
        self.teaching_status_label.setStyleSheet("color: gray; padding: 5px; background-color: #f5f5f5; border-radius: 3px;")
        parent_layout.addWidget(self.teaching_status_label)

    def setup_signals(self):
        """设置信号连接"""
        # 连接示教控制按钮信号
        self.start_teaching_button.clicked.connect(self._on_start_teaching_clicked)
        self.stop_teaching_button.clicked.connect(self._on_stop_teaching_clicked)
        self.execute_teaching_button.clicked.connect(self._on_execute_teaching_clicked)
        
        # 连接轨迹管理信号
        self.trajectory_combo.currentTextChanged.connect(self._on_trajectory_selection_changed)
        self.duration_spin.valueChanged.connect(self._on_duration_changed)
        self.planning_switch.checkedChanged.connect(self._on_planning_switch_changed)
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        self.restore_time_button.clicked.connect(self._on_restore_time_clicked)
        self.delete_trajectory_button.clicked.connect(self._on_delete_trajectory_clicked)

    def init_trajectory_list(self):
        """初始化轨迹列表"""
        if self.logger:
            self.logger.info("准备请求轨迹列表")
        # 使用QTimer延迟发送请求信号，确保所有组件都已初始化
        QTimer.singleShot(100, lambda: self.request_trajectory_list.emit())

    # ==================== 信号处理槽函数 ====================
    
    def _on_start_teaching_clicked(self):
        """开始示教按钮点击处理"""
        if self.logger:
            self.logger.info("开始示教按钮被点击")
        self._is_executing_trajectory = True
        self.update_teaching_buttons_state()
        self.start_teaching_requested.emit()
    
    def _on_stop_teaching_clicked(self):
        """结束示教按钮点击处理"""
        if self.logger:
            self.logger.info("结束示教按钮被点击")
        self._is_executing_trajectory = False
        self.update_teaching_buttons_state()
        self.stop_teaching_requested.emit()
    
    def _on_execute_teaching_clicked(self):
        """执行示教按钮点击处理"""
        trajectory_name = self.trajectory_combo.currentText()
        if not trajectory_name:
            if self.logger:
                self.logger.warning("请先选择要执行的轨迹")
            return
        
        use_planned = self.planning_switch.isChecked()
        if self.logger:
            self.logger.info(f"执行示教按钮被点击，轨迹: {trajectory_name}, 使用规划轨迹: {use_planned}")
        
        self._is_executing_trajectory = True
        self.update_execution_buttons_state()
        self.execute_teaching_requested.emit(trajectory_name, use_planned)
    
    def _on_trajectory_selection_changed(self, text: str):
        """轨迹选择改变时的处理"""
        if not text:
            return
        
        self._current_trajectory = text
        if self.logger:
            self.logger.info(f"轨迹选择已更改为: {text}")
        
        # 更新删除按钮状态
        self.delete_trajectory_button.setEnabled(True)
        
        # 自动请求轨迹数据
        self.request_trajectory_data.emit(text)
    
    def _on_duration_changed(self, value: float):
        """执行时长改变时的处理"""
        if not self._current_trajectory:
            return
        
        if self.logger:
            self.logger.info(f"执行时长已更改为: {value}秒")
        
        # 启用刷新按钮，让用户确认重规划
        self.refresh_button.setEnabled(True)
        # 同时启用恢复按钮
        self.restore_time_button.setEnabled(True)
    
    def _on_planning_switch_changed(self, checked: bool):
        """轨迹规划开关改变时的处理"""
        # 更新开关文本
        self.planning_switch.setText('开启' if checked else '关闭')
        if self.logger:
            self.logger.info(f"轨迹规划开关已更改为: {'开启' if checked else '关闭'}")
    
    def _on_refresh_clicked(self):
        """刷新轨迹按钮点击处理"""
        if not self._current_trajectory:
            return
        
        duration = self.duration_spin.value()
        if self.logger:
            self.logger.info(f"刷新轨迹，重规划时长: {duration}秒")
        self.replan_requested.emit(self._current_trajectory, duration)
        # 点击后禁用，等待新数据
        self.refresh_button.setEnabled(False)
    
    def _on_restore_time_clicked(self):
        """恢复默认时长按钮点击处理"""
        if not self._current_trajectory:
            return
        
        if self.logger:
            self.logger.info("恢复默认时长按钮被点击")
        
        # 立即在UI上恢复时长输入框的值
        self.duration_spin.blockSignals(True)
        self.duration_spin.setValue(self._original_total_time)
        self.duration_spin.blockSignals(False)
        
        # 发射信号，请求后端按原始时间戳进行重规划
        self.restore_default_requested.emit(self._current_trajectory)
        
        # 点击后，禁用刷新和恢复按钮
        self.refresh_button.setEnabled(False)
        self.restore_time_button.setEnabled(False)
    
    def _on_delete_trajectory_clicked(self):
        """删除轨迹按钮点击处理"""
        trajectory_name = self.trajectory_combo.currentText()
        if not trajectory_name:
            if self.logger:
                self.logger.warning("请先选择要删除的轨迹")
            return
        
        if self.logger:
            self.logger.info(f"删除轨迹按钮被点击，轨迹: {trajectory_name}")
        
        self.delete_trajectory_requested.emit(trajectory_name)

    # ==================== 公共接口方法 ====================
    
    def update_trajectory_list(self, trajectory_names: list, prefer_newest: bool = False):
        """更新轨迹列表"""
        if self.logger:
            self.logger.info(f"收到轨迹列表更新，轨迹数量: {len(trajectory_names)}")
        
        # 保存当前选中的轨迹名称
        current_selection = self.trajectory_combo.currentText()
        
        # 清空并重新添加轨迹
        self.trajectory_combo.clear()
        self.trajectory_combo.addItems(trajectory_names)
        
        if prefer_newest and trajectory_names:
            # 优先选择最新的轨迹
            newest_trajectory = trajectory_names[-1]
            self.trajectory_combo.setCurrentText(newest_trajectory)
            self._current_trajectory = newest_trajectory
        elif current_selection and current_selection in trajectory_names:
            # 尝试恢复之前选中的轨迹
            self.trajectory_combo.setCurrentText(current_selection)
            self._current_trajectory = current_selection
        else:
            # 如果没有之前选中的轨迹或轨迹不存在，清空选择
            self._current_trajectory = None
        
        # 更新删除按钮状态
        self.delete_trajectory_button.setEnabled(bool(self.trajectory_combo.currentText()))
    
    def update_trajectory_data(self, trajectory_data: dict):
        """更新轨迹数据"""
        total_time = trajectory_data.get('total_time')
        if total_time is not None:
            self._original_total_time = total_time  # 保存原始时长
            self.duration_spin.blockSignals(True)
            self.duration_spin.setValue(total_time)
            self.duration_spin.blockSignals(False)
            self.duration_spin.setEnabled(True)
            # 刚加载完，禁用刷新按钮，启用恢复按钮
            self.refresh_button.setEnabled(False)
            self.restore_time_button.setEnabled(True)
    
    def update_teaching_buttons_state(self):
        """更新示教按钮状态"""
        if self._is_executing_trajectory:
            self.start_teaching_button.setEnabled(False)
            self.stop_teaching_button.setEnabled(True)
            self.execute_teaching_button.setEnabled(False)
            self.delete_trajectory_button.setEnabled(False)
            self.teaching_status_label.setText('示教状态: 执行中')
            self.teaching_status_label.setStyleSheet("color: blue; padding: 5px; background-color: #e3f2fd; border-radius: 3px;")
        else:
            self.start_teaching_button.setEnabled(True)
            self.stop_teaching_button.setEnabled(False)
            self.execute_teaching_button.setEnabled(True)
            # 删除按钮只有在有选中轨迹时才启用
            self.delete_trajectory_button.setEnabled(bool(self.trajectory_combo.currentText()))
            self.teaching_status_label.setText('示教状态: 未开始')
            self.teaching_status_label.setStyleSheet("color: gray; padding: 5px; background-color: #f5f5f5; border-radius: 3px;")
    
    def update_execution_buttons_state(self):
        """更新执行按钮状态"""
        if self._is_executing_trajectory:
            self.execute_teaching_button.setEnabled(False)
            self.delete_trajectory_button.setEnabled(False)
            self.teaching_status_label.setText('示教状态: 执行中')
            self.teaching_status_label.setStyleSheet("color: blue; padding: 5px; background-color: #e3f2fd; border-radius: 3px;")
        else:
            self.execute_teaching_button.setEnabled(True)
            # 删除按钮只有在有选中轨迹时才启用
            self.delete_trajectory_button.setEnabled(bool(self.trajectory_combo.currentText()))
            self.teaching_status_label.setText('示教状态: 未开始')
            self.teaching_status_label.setStyleSheet("color: gray; padding: 5px; background-color: #f5f5f5; border-radius: 3px;")
    
    def on_trajectory_execution_finished(self):
        """轨迹执行完成时的处理"""
        if self.logger:
            self.logger.info("收到轨迹执行完成信号")
        self._is_executing_trajectory = False
        self.update_execution_buttons_state()
        self.teaching_status_label.setText('示教状态: 执行完成')
        self.teaching_status_label.setStyleSheet("color: green; padding: 5px; background-color: #e8f5e8; border-radius: 3px;")
        # 3秒后恢复默认状态
        QTimer.singleShot(3000, lambda: self.teaching_status_label.setText('示教状态: 未开始'))
        QTimer.singleShot(3000, lambda: self.teaching_status_label.setStyleSheet("color: gray; padding: 5px; background-color: #f5f5f5; border-radius: 3px;"))
    
    def on_trajectory_execution_error(self, error_message: str):
        """轨迹执行错误时的处理"""
        if self.logger:
            self.logger.error(f"轨迹执行错误: {error_message}")
        
        # 恢复执行状态和按钮
        self._is_executing_trajectory = False
        self.update_execution_buttons_state()
        
        # 更新状态标签
        self.teaching_status_label.setText(f'示教状态: 执行失败')
        self.teaching_status_label.setStyleSheet("color: red; padding: 5px; background-color: #ffebee; border-radius: 3px;")
        
        # 3秒后恢复默认状态
        QTimer.singleShot(3000, lambda: self.teaching_status_label.setText('示教状态: 未开始'))
        QTimer.singleShot(3000, lambda: self.teaching_status_label.setStyleSheet("color: gray; padding: 5px; background-color: #f5f5f5; border-radius: 3px;")) 