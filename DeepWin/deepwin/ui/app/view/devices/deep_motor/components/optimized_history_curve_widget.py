"""
优化版历史曲线组件
使用优化版绘图组件，大幅降低刷新频率
"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from qfluentwidgets import (PrimaryPushButton, ComboBox, CardWidget)
from typing import Dict, List, Any, Optional
from deepwin.data_management.log_manager import LogManager
from .optimized_plot_widget import OptimizedPlotWidget


class OptimizedHistoryCurveWidget(QWidget):
    """优化版历史曲线组件"""
    
    # 信号定义
    param_changed = Signal(str)  # 参数改变信号
    refresh_requested = Signal()  # 刷新请求信号
    restore_default_requested = Signal()  # 恢复默认请求信号
    
    def __init__(self, title: str = "历史曲线", log_manager: LogManager = None, parent=None):
        super().__init__(parent)
        self.logger = log_manager
        self.title = title
        
        # 历史数据请求定时器 - 大幅降低频率
        self.history_request_timer = QTimer(self)
        self.history_request_timer.setInterval(1000)  # 每1000ms请求一次历史数据（1 FPS），大幅降低频率
        self.history_request_timer.timeout.connect(self._request_history_data)
        self._should_request_history = False
        
        # 当前选中的参数
        self.current_selected_param = 'position'
        
        self.setup_ui()
        
    def setup_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 创建优化版绘图组件
        self.plot_widget = OptimizedPlotWidget(self.title, self.logger, self)
        
        # 连接绘图组件的信号
        self.plot_widget.param_changed.connect(self._on_param_changed)
        self.plot_widget.refresh_requested.connect(self._on_refresh_requested)
        
        layout.addWidget(self.plot_widget)
        
    def _on_param_changed(self, param_name: str):
        """参数改变处理"""
        self.current_selected_param = param_name
        
        if self.logger:
            self.logger.info(f"优化历史曲线组件参数改变: {param_name}")
            
        # 检查是否是轨迹数据参数
        if param_name.startswith('trajectory_'):
            # 轨迹数据不需要定时请求
            if self.history_request_timer.isActive():
                self.history_request_timer.stop()
        else:
            # 普通历史数据需要定时请求
            if not self.history_request_timer.isActive():
                self.history_request_timer.start()
                
        # 发射信号
        self.param_changed.emit(param_name)
        
    def _on_refresh_requested(self):
        """刷新请求处理"""
        if self.logger:
            self.logger.info("优化历史曲线组件刷新请求")
        self.refresh_requested.emit()
        
    def _request_history_data(self):
        """历史数据请求定时器处理"""
        if self._should_request_history:
            self._should_request_history = False
            # 这里可以发射历史数据请求信号
            if self.logger:
                self.logger.debug(f"请求历史数据: {self.current_selected_param}")
                
    def update_history_data(self, history_data_dict: Dict[str, Any]):
        """
        更新历史数据
        :param history_data_dict: 包含历史数据的字典
        """
        if self.logger:
            self.logger.debug(f"优化历史曲线组件收到数据更新: {self.current_selected_param}")
            
        # 传递给绘图组件
        self.plot_widget.update_data(history_data_dict)
        
    def update_trajectory_data(self, trajectory_data: Dict[str, Any]):
        """
        更新轨迹数据
        :param trajectory_data: 包含轨迹数据的字典
        """
        if self.logger:
            self.logger.debug(f"优化历史曲线组件收到轨迹数据更新")
            
        # 传递给绘图组件
        self.plot_widget.update_data(trajectory_data)
        
    def update_execution_progress(self, progress_data: Dict[str, Any]):
        """
        更新执行进度数据
        :param progress_data: 包含执行进度数据的字典
        """
        if self.logger:
            self.logger.debug(f"优化历史曲线组件收到执行进度数据")
            
        # 传递给绘图组件的执行轨迹更新方法
        self.plot_widget.update_execution_trajectory(progress_data)
        
    def update_teaching_trajectory(self, times: List[float], positions: List[float]):
        """
        更新示教轨迹数据
        :param times: 时间列表
        :param positions: 位置列表
        """
        if self.logger:
            self.logger.debug(f"优化历史曲线组件收到示教轨迹数据，点数: {len(times) if times else 0}")
            
        # 构建数据字典
        teaching_data = {
            'data': {
                'time': times,
                'value': positions
            },
            'type': 'teaching_trajectory'
        }
        
        # 传递给绘图组件
        self.plot_widget.update_data(teaching_data)
        
    def set_current_param(self, param_name: str):
        """设置当前参数"""
        self.current_selected_param = param_name
        
        # 更新绘图组件的参数选择
        param_map = {
            'position': 'position (位置)',
            'velocity': 'velocity (速度)',
            'torque': 'torque (扭矩)', 
            'temperature': 'temperature (温度)',
            'error_code': 'error_code (错误码)',
            'motor_can_id': 'motor_can_id (CAN ID)',
            'mode_state': 'mode_state (模式状态)',
            'flt_uninitialized': 'flt_uninitialized (未初始化故障)',
            'flt_hall_encoding': 'flt_hall_encoding (霍尔编码故障)',
            'flt_magnetic_encoding': 'flt_magnetic_encoding (磁编码故障)',
            'flt_over_temperature': 'flt_over_temperature (过温故障)',
            'flt_over_current': 'flt_over_current (过流故障)',
            'flt_voltage_drop': 'flt_voltage_drop (电压跌落故障)',
            'trajectory_teaching': 'trajectory_teaching (示教轨迹)',
            'trajectory_original': 'trajectory_original (原始轨迹)',
            'trajectory_planned': 'trajectory_planned (规划轨迹)',
            'trajectory_both': 'trajectory_both (原始+规划)',
            'trajectory_executed': 'trajectory_executed (执行轨迹)'
        }
        
        display_text = param_map.get(param_name, 'position (位置)')
        self.plot_widget.param_combo.blockSignals(True)
        self.plot_widget.param_combo.setCurrentText(display_text)
        self.plot_widget.param_combo.blockSignals(False)
        
    def get_current_param(self) -> str:
        """获取当前参数"""
        return self.current_selected_param
        
    def start_history_requests(self):
        """开始历史数据请求"""
        if not self.current_selected_param.startswith('trajectory_'):
            self._should_request_history = True
            if not self.history_request_timer.isActive():
                self.history_request_timer.start()
                
    def stop_history_requests(self):
        """停止历史数据请求"""
        self._should_request_history = False
        if self.history_request_timer.isActive():
            self.history_request_timer.stop()
            
    def clear_plot(self):
        """清空绘图"""
        self.plot_widget.clear_plot()
        
    def stop_updates(self):
        """停止更新"""
        self.plot_widget.stop_updates()
        self.stop_history_requests()
        
    def start_updates(self):
        """开始更新"""
        self.plot_widget.start_updates()
        self.start_history_requests()
        
    def set_title(self, title: str):
        """设置标题"""
        self.title = title
        self.plot_widget.set_title(title)
        
    def enable_refresh_button(self, enabled: bool = True):
        """启用/禁用刷新按钮"""
        self.plot_widget.refresh_button.setEnabled(enabled)
        
    def enable_restore_button(self, enabled: bool = True):
        """启用/禁用恢复按钮"""
        self.plot_widget.restore_button.setEnabled(enabled)
        
    def reset_to_defaults(self):
        """重置为默认状态"""
        self.current_selected_param = 'position'
        self._should_request_history = False
        self.stop_history_requests()
        self.plot_widget.reset_to_defaults()
        self.clear_plot()
        
    def update_teaching_trajectory(self, times: list, positions: list):
        """
        更新示教轨迹实时显示
        :param times: 时间列表
        :param positions: 位置列表
        """
        if self.logger:
            self.logger.debug(f"优化历史曲线组件: 收到示教轨迹更新，点数: {len(times) if times else 0}")
        self.plot_widget.update_teaching_trajectory(times, positions)
        
    def update_execution_trajectory(self, progress_data: dict):
        """
        更新执行轨迹实时显示
        :param progress_data: 包含执行进度信息的字典
        """
        if self.logger:
            self.logger.debug(f"优化历史曲线组件: 收到执行轨迹更新")
        self.plot_widget.update_execution_trajectory(progress_data)
        
    def set_execution_mode(self, enabled: bool):
        """
        设置执行模式
        :param enabled: 是否启用执行模式
        """
        if self.logger:
            self.logger.debug(f"优化历史曲线组件: 设置执行模式: {enabled}")
        self.plot_widget.set_execution_mode(enabled)
