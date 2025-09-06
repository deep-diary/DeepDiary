"""
优化版绘图组件
针对性能问题进行了优化，减少不必要的重绘和计算
"""

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from qfluentwidgets import ComboBox, PrimaryPushButton, CardWidget
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime
import pandas as pd
import hashlib
from typing import Dict, List, Any, Optional, Union
from deepwin.data_management.log_manager import LogManager


class OptimizedPlotWidget(QWidget):
    """优化版绘图组件"""
    
    # 信号定义
    param_changed = Signal(str)  # 参数改变信号
    refresh_requested = Signal()  # 刷新请求信号
    
    def __init__(self, title: str = "数据曲线", log_manager: LogManager = None, parent=None):
        super().__init__(parent)
        self.logger = log_manager
        self.title = title
        
        # 绘图相关属性
        self.figure = None
        self.canvas = None
        self.ax = None
        
        # 数据缓存
        self.latest_data = None
        self._last_data_hash = None
        self._is_updating = False
        
        # 性能优化相关 - 降低更新频率
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(500)  # 500ms更新间隔（2 FPS），大幅降低频率
        self.update_timer.timeout.connect(self._throttled_update)
        
        # 坐标轴范围缓存
        self._last_xlim = None
        self._last_ylim = None
        
        # 数据变化检测阈值
        self._data_change_threshold = 0.01  # 数据变化阈值，避免微小变化触发重绘
        
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
        
        # 控制面板
        control_layout = QHBoxLayout()
        
        # 参数选择
        param_label = QLabel('选择参数:')
        self.param_combo = ComboBox()
        self.param_combo.addItems([
            'position (位置)', 'velocity (速度)', 'torque (扭矩)', 'temperature (温度)',
            'error_code (错误码)', 'motor_can_id (CAN ID)', 'mode_state (模式状态)',
            'flt_uninitialized (未初始化故障)', 'flt_hall_encoding (霍尔编码故障)',
            'flt_magnetic_encoding (磁编码故障)', 'flt_over_temperature (过温故障)',
            'flt_over_current (过流故障)', 'flt_voltage_drop (电压跌落故障)',
            '--- 示教与轨迹 ---', 'trajectory_teaching (示教轨迹)', 
            'trajectory_original (原始轨迹)', 'trajectory_planned (规划轨迹)', 
            'trajectory_both (原始+规划)', 'trajectory_executed (执行轨迹)'
        ])
        self.param_combo.setCurrentText('position (位置)')
        
        # 刷新按钮
        self.refresh_button = PrimaryPushButton('刷新曲线')
        self.refresh_button.setEnabled(False)
        
        # 恢复默认按钮
        self.restore_button = PrimaryPushButton('恢复默认')
        self.restore_button.setEnabled(False)
        
        control_layout.addWidget(param_label)
        control_layout.addWidget(self.param_combo)
        control_layout.addWidget(self.refresh_button)
        control_layout.addWidget(self.restore_button)
        control_layout.addStretch()
        
        card_layout.addLayout(control_layout)
        
        # 创建matplotlib图形 - 使用更小的图形尺寸
        self.figure = Figure(figsize=(6, 3))  # 减小图形尺寸
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(200)  # 减小最小高度
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('时间')
        self.ax.set_ylabel('数值')
        self.ax.grid(True, alpha=0.3)  # 降低网格透明度
        self.figure.tight_layout()
        
        card_layout.addWidget(self.canvas)
        
        layout.addWidget(self.card)
        
        # 连接信号
        self.param_combo.currentTextChanged.connect(self._on_param_changed)
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        self.restore_button.clicked.connect(self._on_restore_clicked)
        
    def _on_param_changed(self, param_text: str):
        """参数改变处理"""
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
            'flt_over_temperature (过温故障)': 'flt_over_temperature',
            'flt_over_current (过流故障)': 'flt_over_current',
            'flt_voltage_drop (电压跌落故障)': 'flt_voltage_drop',
            'trajectory_teaching (示教轨迹)': 'trajectory_teaching',
            'trajectory_original (原始轨迹)': 'trajectory_original',
            'trajectory_planned (规划轨迹)': 'trajectory_planned',
            'trajectory_both (原始+规划)': 'trajectory_both',
            'trajectory_executed (执行轨迹)': 'trajectory_executed'
        }
        
        param_name = param_map.get(param_text, 'position')
        
        if self.logger:
            self.logger.info(f"优化绘图组件参数改变: {param_text} -> {param_name}")
        
        # 简化的参数切换处理
        self.ax.clear()
        self.ax.set_xlabel('时间 (s)')
        self.ax.set_ylabel('数值')
        self.ax.grid(True, alpha=0.3)
        self.ax.text(0.5, 0.5, '加载中...', ha='center', va='center', transform=self.ax.transAxes)
        self.canvas.draw()
        
        # 发射信号
        self.param_changed.emit(param_name)
        
    def _on_refresh_clicked(self):
        """刷新按钮点击处理"""
        if self.logger:
            self.logger.info("优化绘图组件刷新请求")
        self.refresh_requested.emit()
        
    def _on_restore_clicked(self):
        """恢复默认按钮点击处理"""
        if self.logger:
            self.logger.info("优化绘图组件恢复默认请求")
        self.restore_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        
    def update_data(self, data_dict: Dict[str, Any]):
        """
        更新绘图数据 - 优化版本
        :param data_dict: 包含绘图数据的字典
        """
        if self._is_updating:
            return
            
        # 缓存数据
        self.latest_data = data_dict
        
        # 启动定时更新 - 降低频率
        if not self.update_timer.isActive():
            self.update_timer.start()
            
    def _throttled_update(self):
        """节流更新方法 - 优化版本"""
        if not self.latest_data or self._is_updating:
            return
            
        # 计算数据hash，避免重复绘制
        current_hash = self._calculate_data_hash(self.latest_data)
        if current_hash == self._last_data_hash:
            return
            
        # 检查数据变化是否足够大
        if not self._is_data_significantly_changed():
            return
            
        self._is_updating = True
        try:
            self._update_plot_optimized(self.latest_data)
            self._last_data_hash = current_hash
        finally:
            self._is_updating = False
            
    def _is_data_significantly_changed(self) -> bool:
        """检查数据是否有显著变化"""
        if not self.latest_data or not self._last_data_hash:
            return True
            
        # 简化的变化检测
        plot_data = self.latest_data.get('data')
        if plot_data is None:
            return False
            
        # 对于数值数据，检查是否有显著变化
        if hasattr(plot_data, 'values'):
            values = plot_data.values
            if len(values) > 0:
                # 检查最大值和最小值的变化
                current_max = max(values)
                current_min = min(values)
                # 这里可以添加更复杂的阈值检测
                return True
                
        return True
            
    def _calculate_data_hash(self, data_dict: Dict[str, Any]) -> Optional[str]:
        """计算数据hash值 - 优化版本"""
        try:
            plot_data = data_dict.get('data')
            if plot_data is None:
                return None
                
            # 简化hash计算，只使用数据的基本信息
            if hasattr(plot_data, 'shape'):
                data_str = f"{plot_data.shape}_{plot_data.iloc[-1] if len(plot_data) > 0 else 'empty'}"
            elif isinstance(plot_data, (list, dict)):
                data_str = f"{len(plot_data)}_{str(plot_data)[:100]}"  # 只取前100个字符
            else:
                data_str = str(plot_data)[:100]
                
            return hashlib.md5(data_str.encode()).hexdigest()
        except Exception:
            return None
            
    def _update_plot_optimized(self, data_dict: Dict[str, Any]):
        """优化版绘图更新"""
        plot_data = data_dict.get('data')
        total_time = data_dict.get('total_time')
        
        # 清空当前图形
        self.ax.clear()
        
        # 检查数据是否为空
        if plot_data is None or (hasattr(plot_data, 'empty') and plot_data.empty):
            self.ax.set_xlabel('时间')
            self.ax.set_ylabel('数值')
            self.ax.grid(True, alpha=0.3)
            self.ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            return
            
        # 根据数据类型进行绘制 - 简化版本
        if hasattr(plot_data, 'columns') and 'time' in plot_data.columns and 'value' in plot_data.columns:
            # DataFrame格式的历史数据
            self._plot_dataframe_history_optimized(plot_data)
        else:
            # 其他格式数据
            self.ax.text(0.5, 0.5, '不支持的数据格式', ha='center', va='center', transform=self.ax.transAxes)
            
        # 设置标签和网格
        self._set_labels_and_grid()
        
        # 自动调整布局
        self.figure.tight_layout()
        
        # 刷新画布 - 使用更轻量的绘制
        self.canvas.draw_idle()  # 使用draw_idle而不是draw，更轻量
        
        # 更新控制按钮状态
        if total_time is not None:
            self.refresh_button.setEnabled(True)
            self.restore_button.setEnabled(True)
            
    def _plot_dataframe_history_optimized(self, df: pd.DataFrame):
        """绘制DataFrame格式的历史数据 - 优化版本"""
        times = df['time'].tolist()
        values = df['value'].tolist()
        
        # 简化绘制，减少样式设置
        if self.param_combo.currentText().startswith('mode_state'):
            # 对于 mode_state，使用简化的散点图
            self.ax.scatter(times, values, c='red', s=30, alpha=0.7)
        else:
            # 对于数值类型参数，使用简化的线图
            self.ax.plot(times, values, 'b-', linewidth=1.5, alpha=0.8)
            
        # 设置坐标轴范围
        if times and values:
            self._set_axis_limits_from_lists(times, values)
            
    def _set_labels_and_grid(self):
        """设置标签和网格 - 简化版本"""
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
        
        # 获取当前参数名
        current_text = self.param_combo.currentText()
        param_name = current_text.split(' (')[0] if ' (' in current_text else current_text
        
        self.ax.set_xlabel('时间 (s)')
        self.ax.set_ylabel(param_labels.get(param_name, '数值'))
        self.ax.grid(True, alpha=0.3)
        
    def _set_axis_limits_from_lists(self, times: List, values: List):
        """从列表设置坐标轴范围 - 简化版本"""
        if not times or not values:
            return
            
        # 设置X轴范围
        x_min, x_max = min(times), max(times)
        x_margin = (x_max - x_min) * 0.05 if x_max > x_min else 0.1
        self.ax.set_xlim(x_min - x_margin, x_max + x_margin)
        
        # 设置Y轴范围
        y_min, y_max = min(values), max(values)
        if y_min == y_max:
            y_margin = 1.0
        else:
            y_margin = (y_max - y_min) * 0.1
        self.ax.set_ylim(y_min - y_margin, y_max + y_margin)
        
    def clear_plot(self):
        """清空绘图"""
        self.ax.clear()
        self.ax.set_xlabel('时间')
        self.ax.set_ylabel('数值')
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
        
    def set_title(self, title: str):
        """设置标题"""
        self.title = title
        self.card.setObjectName(title)
        
    def get_current_param(self) -> str:
        """获取当前选中的参数"""
        current_text = self.param_combo.currentText()
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
            'flt_over_temperature (过温故障)': 'flt_over_temperature',
            'flt_over_current (过流故障)': 'flt_over_current',
            'flt_voltage_drop (电压跌落故障)': 'flt_voltage_drop',
            'trajectory_teaching (示教轨迹)': 'trajectory_teaching',
            'trajectory_original (原始轨迹)': 'trajectory_original',
            'trajectory_planned (规划轨迹)': 'trajectory_planned',
            'trajectory_both (原始+规划)': 'trajectory_both',
            'trajectory_executed (执行轨迹)': 'trajectory_executed'
        }
        return param_map.get(current_text, 'position')
        
    def stop_updates(self):
        """停止更新"""
        self.update_timer.stop()
        
    def start_updates(self):
        """开始更新"""
        if self.latest_data:
            self.update_timer.start()
            
    def reset_to_defaults(self):
        """重置为默认状态"""
        self.ax.clear()
        self.ax.set_xlabel('时间')
        self.ax.set_ylabel('数值')
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
        self.refresh_button.setEnabled(False)
        self.restore_button.setEnabled(False)
