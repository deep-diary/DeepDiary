"""
示教控制组件
提供示教录制和执行相关功能
"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox
from qfluentwidgets import (PrimaryPushButton, ComboBox, SwitchButton, CardWidget)
from typing import List, Optional
from deepwin.data_management.log_manager import LogManager


class TeachingControlWidget(QWidget):
    """示教控制组件"""
    
    # 信号定义
    start_teaching_requested = Signal(int)  # 开始示教信号 (motor_id)
    stop_teaching_requested = Signal()      # 停止示教信号
    execute_teaching_requested = Signal(str, bool, int)  # 执行示教信号 (轨迹名, 是否使用规划轨迹, motor_id)
    delete_trajectory_requested = Signal(str)  # 删除轨迹信号 (轨迹名)
    trajectory_selected = Signal(str)       # 轨迹选择信号 (轨迹名)
    duration_changed = Signal(float)        # 执行时长改变信号 (时长)
    replan_requested = Signal(str, float)   # 重规划信号 (轨迹名, 新时长)
    restore_default_requested = Signal(str) # 恢复默认信号 (轨迹名)
    switch_to_execution_view = Signal()     # 切换到执行轨迹视图信号
    switch_to_teaching_view = Signal()      # 切换到示教轨迹视图信号
    
    def __init__(self, title: str = "示教控制", log_manager: LogManager = None, parent=None):
        super().__init__(parent)
        self.logger = log_manager
        self.title = title
        
        # 示教状态
        self._is_teaching = False
        self._is_executing = False
        self._current_trajectory = None
        self._original_total_time = None
        self.current_motor_id = 6
        
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
        
        # 示教控制区域
        teaching_controls_layout = QHBoxLayout()
        
        # 开始示教按钮
        self.start_teaching_button = PrimaryPushButton('开始示教')
        self.start_teaching_button.clicked.connect(self._on_start_teaching_clicked)
        
        # 结束示教按钮
        self.stop_teaching_button = PrimaryPushButton('结束示教')
        self.stop_teaching_button.clicked.connect(self._on_stop_teaching_clicked)
        
        # 执行示教按钮
        self.execute_teaching_button = PrimaryPushButton('执行示教')
        self.execute_teaching_button.clicked.connect(self._on_execute_teaching_clicked)
        
        # 删除轨迹按钮
        self.delete_trajectory_button = PrimaryPushButton('删除轨迹')
        self.delete_trajectory_button.clicked.connect(self._on_delete_trajectory_clicked)
        
        teaching_controls_layout.addWidget(self.start_teaching_button)
        teaching_controls_layout.addWidget(self.stop_teaching_button)
        teaching_controls_layout.addWidget(self.execute_teaching_button)
        teaching_controls_layout.addWidget(self.delete_trajectory_button)
        teaching_controls_layout.addStretch()
        
        card_layout.addLayout(teaching_controls_layout)
        
        # 轨迹选择和控制区域
        trajectory_controls_layout = QHBoxLayout()
        
        # 轨迹选择
        trajectory_label = QLabel('轨迹:')
        self.trajectory_combo = ComboBox()
        self.trajectory_combo.setMinimumWidth(150)
        self.trajectory_combo.currentTextChanged.connect(self._on_trajectory_selection_changed)
        
        # 执行时间控制
        duration_label = QLabel('执行时间:')
        self.duration_spin = QDoubleSpinBox(self)
        self.duration_spin.setRange(1.0, 30.0)
        self.duration_spin.setSingleStep(0.5)
        self.duration_spin.setSuffix(" s")
        self.duration_spin.setValue(5.0)
        self.duration_spin.valueChanged.connect(self._on_duration_changed)
        
        # 轨迹规划开关
        planning_label = QLabel('轨迹规划:')
        self.planning_switch = SwitchButton('关闭')
        self.planning_switch.setChecked(False)  # 默认关闭
        self.planning_switch.checkedChanged.connect(self._on_planning_switch_changed)
        
        trajectory_controls_layout.addWidget(trajectory_label)
        trajectory_controls_layout.addWidget(self.trajectory_combo)
        trajectory_controls_layout.addWidget(duration_label)
        trajectory_controls_layout.addWidget(self.duration_spin)
        trajectory_controls_layout.addWidget(planning_label)
        trajectory_controls_layout.addWidget(self.planning_switch)
        trajectory_controls_layout.addStretch()
        
        card_layout.addLayout(trajectory_controls_layout)
        
        # 状态显示区域
        self.teaching_status_label = QLabel('示教状态: 未开始')
        self.teaching_status_label.setStyleSheet("color: gray;")
        card_layout.addWidget(self.teaching_status_label)
        
        layout.addWidget(self.card)
        
        # 初始化按钮状态
        self.update_teaching_buttons_state()
        
    def _on_start_teaching_clicked(self):
        """开始示教按钮点击处理"""
        if self.logger:
            self.logger.info("开始示教按钮被点击")
        self._is_teaching = True
        self.update_teaching_buttons_state()
        self.teaching_status_label.setText('示教状态: 录制中')
        self.teaching_status_label.setStyleSheet("color: blue;")
        
        # 自动切换到示教轨迹视图
        self.switch_to_teaching_view.emit()
        
        self.start_teaching_requested.emit(self.current_motor_id)
        
    def _on_stop_teaching_clicked(self):
        """结束示教按钮点击处理"""
        if self.logger:
            self.logger.info("结束示教按钮被点击")
        self._is_teaching = False
        self.update_teaching_buttons_state()
        self.teaching_status_label.setText('示教状态: 录制完成')
        self.teaching_status_label.setStyleSheet("color: green;")
        self.stop_teaching_requested.emit()
        
    def _on_execute_teaching_clicked(self):
        """执行示教按钮点击处理"""
        trajectory_name = self.trajectory_combo.currentText()
        if not trajectory_name:
            if self.logger:
                self.logger.warning("请先选择要执行的轨迹")
            return
            
        if self.logger:
            self.logger.info(f"执行示教按钮被点击，轨迹: {trajectory_name}, 使用规划轨迹: {self.planning_switch.isChecked()}")
            
        self._is_executing = True
        self.update_execution_buttons_state()
        self.teaching_status_label.setText('示教状态: 执行中')
        self.teaching_status_label.setStyleSheet("color: blue;")
        
        # 自动切换到执行轨迹视图
        self.switch_to_execution_view.emit()
        
        self.execute_teaching_requested.emit(trajectory_name, self.planning_switch.isChecked(), self.current_motor_id)
        
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
        
    def _on_trajectory_selection_changed(self, text: str):
        """轨迹选择改变处理"""
        if not text:
            self._current_trajectory = None
            return
            
        self._current_trajectory = text
        if self.logger:
            self.logger.info(f"轨迹选择已更改为: {text}")
            
        # 更新删除按钮状态
        self.delete_trajectory_button.setEnabled(True)
        
        # 发射信号
        self.trajectory_selected.emit(text)
        
    def _on_duration_changed(self, value: float):
        """执行时长改变处理"""
        if not self._current_trajectory:
            return
            
        if self.logger:
            self.logger.info(f"执行时长已更改为: {value}秒")
        self.duration_changed.emit(value)
        
    def _on_planning_switch_changed(self, checked: bool):
        """轨迹规划开关改变处理"""
        # 更新开关文本
        self.planning_switch.setText('开启' if checked else '关闭')
        if self.logger:
            self.logger.info(f"轨迹规划开关已更改为: {'开启' if checked else '关闭'}")
            
    def update_trajectory_list(self, trajectory_names: List[str], prefer_newest: bool = False):
        """
        更新轨迹列表
        :param trajectory_names: 轨迹名称列表
        :param prefer_newest: 是否优先选择最新轨迹
        """
        if self.logger:
            self.logger.info(f"示教控制组件: 收到轨迹列表更新，轨迹数量: {len(trajectory_names)}")
            
        # 保存当前选中的轨迹名称
        current_selection = self.trajectory_combo.currentText()
        
        # 清空并重新添加轨迹
        self.trajectory_combo.clear()
        self.trajectory_combo.addItems(trajectory_names)
        
        if prefer_newest and trajectory_names:
            # 优先选择最新的轨迹（列表中的最后一个）
            newest_trajectory = trajectory_names[-1]
            self.trajectory_combo.setCurrentText(newest_trajectory)
            self._current_trajectory = newest_trajectory
            if self.logger:
                self.logger.info(f"示教控制组件: 优先选中最新轨迹 '{newest_trajectory}'")
        elif current_selection and current_selection in trajectory_names:
            # 尝试恢复之前选中的轨迹
            self.trajectory_combo.setCurrentText(current_selection)
            self._current_trajectory = current_selection
            if self.logger:
                self.logger.info(f"示教控制组件: 保持选中轨迹 '{current_selection}'")
        else:
            # 如果没有之前选中的轨迹或轨迹不存在，清空选择
            self._current_trajectory = None
            if self.logger:
                self.logger.info("示教控制组件: 清空轨迹选择")
                
        # 更新删除按钮状态
        self.delete_trajectory_button.setEnabled(bool(self.trajectory_combo.currentText()))
        
    def update_teaching_buttons_state(self):
        """更新示教按钮状态"""
        if self._is_teaching:
            self.start_teaching_button.setEnabled(False)
            self.stop_teaching_button.setEnabled(True)
            self.execute_teaching_button.setEnabled(False)
            self.delete_trajectory_button.setEnabled(False)
        else:
            self.start_teaching_button.setEnabled(True)
            self.stop_teaching_button.setEnabled(False)
            self.execute_teaching_button.setEnabled(True)
            # 删除按钮只有在有选中轨迹时才启用
            self.delete_trajectory_button.setEnabled(bool(self.trajectory_combo.currentText()))
            
    def update_execution_buttons_state(self):
        """更新执行按钮状态"""
        if self._is_executing:
            self.execute_teaching_button.setEnabled(False)
            self.delete_trajectory_button.setEnabled(False)
            self.start_teaching_button.setEnabled(False)
            self.stop_teaching_button.setEnabled(False)
        else:
            self.execute_teaching_button.setEnabled(True)
            # 删除按钮只有在有选中轨迹时才启用
            self.delete_trajectory_button.setEnabled(bool(self.trajectory_combo.currentText()))
            self.start_teaching_button.setEnabled(True)
            self.stop_teaching_button.setEnabled(False)
            
    def on_trajectory_execution_finished(self):
        """轨迹执行完成处理"""
        if self.logger:
            self.logger.info("示教控制组件: 收到轨迹执行完成信号")
        self._is_executing = False
        self.update_execution_buttons_state()
        self.teaching_status_label.setText('示教状态: 执行完成')
        self.teaching_status_label.setStyleSheet("color: green;")
        
        # 3秒后恢复默认状态
        QTimer.singleShot(3000, lambda: self.teaching_status_label.setText('示教状态: 未开始'))
        QTimer.singleShot(3000, lambda: self.teaching_status_label.setStyleSheet("color: gray;"))
        
    def on_trajectory_execution_error(self, error_message: str):
        """轨迹执行错误处理"""
        if self.logger:
            self.logger.error(f"轨迹执行错误: {error_message}")
            
        self._is_executing = False
        self.update_execution_buttons_state()
        self.teaching_status_label.setText(f'示教状态: 执行失败')
        self.teaching_status_label.setStyleSheet("color: red;")
        
        # 3秒后恢复默认状态
        QTimer.singleShot(3000, lambda: self.teaching_status_label.setText('示教状态: 未开始'))
        QTimer.singleShot(3000, lambda: self.teaching_status_label.setStyleSheet("color: gray;"))
        
    def update_execution_progress(self, progress_percent: int):
        """更新执行进度"""
        if self._is_executing:
            self.teaching_status_label.setText(f'示教状态: 执行中 ({progress_percent}%)')
            
    def set_motor_id(self, motor_id: int):
        """设置电机ID"""
        self.current_motor_id = motor_id
        
    def get_current_trajectory(self) -> Optional[str]:
        """获取当前选中的轨迹"""
        return self._current_trajectory
        
    def get_duration(self) -> float:
        """获取执行时长"""
        return self.duration_spin.value()
        
    def set_duration(self, duration: float):
        """设置执行时长"""
        self.duration_spin.blockSignals(True)
        self.duration_spin.setValue(duration)
        self.duration_spin.blockSignals(False)
        
    def get_use_planned_trajectory(self) -> bool:
        """获取是否使用规划轨迹"""
        return self.planning_switch.isChecked()
        
    def set_use_planned_trajectory(self, use_planned: bool):
        """设置是否使用规划轨迹"""
        self.planning_switch.blockSignals(True)
        self.planning_switch.setChecked(use_planned)
        self.planning_switch.setText('开启' if use_planned else '关闭')
        self.planning_switch.blockSignals(False)
        
    def set_original_total_time(self, total_time: float):
        """设置原始总时长"""
        self._original_total_time = total_time
        
    def get_original_total_time(self) -> Optional[float]:
        """获取原始总时长"""
        return self._original_total_time
        
    def is_teaching(self) -> bool:
        """获取示教状态"""
        return self._is_teaching
        
    def is_executing(self) -> bool:
        """获取执行状态"""
        return self._is_executing
        
    def reset_to_defaults(self):
        """重置为默认状态"""
        self._is_teaching = False
        self._is_executing = False
        self._current_trajectory = None
        self._original_total_time = None
        
        self.trajectory_combo.clear()
        self.duration_spin.setValue(5.0)
        self.planning_switch.setChecked(False)
        self.planning_switch.setText('关闭')
        
        self.teaching_status_label.setText('示教状态: 未开始')
        self.teaching_status_label.setStyleSheet("color: gray;")
        
        self.update_teaching_buttons_state()
