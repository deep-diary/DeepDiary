from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QDoubleSpinBox
from qfluentwidgets import ComboBox, SwitchButton, PrimaryPushButton

class TrajectoryManagementWidget(QWidget):
    """轨迹管理小部件 - 包含轨迹选择、时长控制、规划开关等"""
    
    # 信号定义
    trajectory_selection_changed = Signal(str)  # 轨迹选择改变信号
    duration_changed = Signal(float)  # 时长改变信号
    planning_switch_changed = Signal(bool)  # 规划开关改变信号
    refresh_requested = Signal()  # 刷新请求信号
    restore_default_requested = Signal()  # 恢复默认请求信号
    delete_trajectory_requested = Signal()  # 删除轨迹请求信号

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 初始化属性
        self._current_trajectory = None
        self._original_total_time = None
        
        self.setup_ui()
        self.setup_signals()

    def setup_ui(self):
        """初始化轨迹管理界面"""
        # 创建轨迹管理布局
        trajectory_layout = QHBoxLayout(self)
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

    def setup_signals(self):
        """设置信号连接"""
        # 连接轨迹管理信号
        self.trajectory_combo.currentTextChanged.connect(self._on_trajectory_selection_changed)
        self.duration_spin.valueChanged.connect(self._on_duration_changed)
        self.planning_switch.checkedChanged.connect(self._on_planning_switch_changed)
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        self.restore_time_button.clicked.connect(self._on_restore_time_clicked)
        self.delete_trajectory_button.clicked.connect(self._on_delete_trajectory_clicked)

    # ==================== 信号处理槽函数 ====================
    
    def _on_trajectory_selection_changed(self, text: str):
        """轨迹选择改变时的处理"""
        if not text:
            return
        
        self._current_trajectory = text
        # 更新删除按钮状态
        self.delete_trajectory_button.setEnabled(True)
        self.trajectory_selection_changed.emit(text)
    
    def _on_duration_changed(self, value: float):
        """执行时长改变时的处理"""
        if not self._current_trajectory:
            return
        
        # 启用刷新按钮，让用户确认重规划
        self.refresh_button.setEnabled(True)
        # 同时启用恢复按钮
        self.restore_time_button.setEnabled(True)
        self.duration_changed.emit(value)
    
    def _on_planning_switch_changed(self, checked: bool):
        """轨迹规划开关改变时的处理"""
        # 更新开关文本
        self.planning_switch.setText('开启' if checked else '关闭')
        self.planning_switch_changed.emit(checked)
    
    def _on_refresh_clicked(self):
        """刷新轨迹按钮点击处理"""
        if not self._current_trajectory:
            return
        
        self.refresh_requested.emit()
        # 点击后禁用，等待新数据
        self.refresh_button.setEnabled(False)
    
    def _on_restore_time_clicked(self):
        """恢复默认时长按钮点击处理"""
        if not self._current_trajectory:
            return
        
        # 立即在UI上恢复时长输入框的值
        self.duration_spin.blockSignals(True)
        self.duration_spin.setValue(self._original_total_time)
        self.duration_spin.blockSignals(False)
        
        # 发射信号，请求后端按原始时间戳进行重规划
        self.restore_default_requested.emit()
        
        # 点击后，禁用刷新和恢复按钮
        self.refresh_button.setEnabled(False)
        self.restore_time_button.setEnabled(False)
    
    def _on_delete_trajectory_clicked(self):
        """删除轨迹按钮点击处理"""
        trajectory_name = self.trajectory_combo.currentText()
        if not trajectory_name:
            return
        
        self.delete_trajectory_requested.emit()

    # ==================== 公共接口方法 ====================
    
    def update_trajectory_list(self, trajectory_names: list, prefer_newest: bool = False):
        """更新轨迹列表"""
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
    
    def get_current_trajectory(self) -> str:
        """获取当前选中的轨迹"""
        return self.trajectory_combo.currentText()
    
    def get_duration(self) -> float:
        """获取当前设置的时长"""
        return self.duration_spin.value()
    
    def is_planning_enabled(self) -> bool:
        """获取规划开关状态"""
        return self.planning_switch.isChecked()
    
    def set_buttons_enabled(self, enabled: bool):
        """设置所有按钮是否可用"""
        self.refresh_button.setEnabled(enabled)
        self.restore_time_button.setEnabled(enabled)
        self.delete_trajectory_button.setEnabled(enabled)
        self.trajectory_combo.setEnabled(enabled)
        self.duration_spin.setEnabled(enabled)
        self.planning_switch.setEnabled(enabled) 