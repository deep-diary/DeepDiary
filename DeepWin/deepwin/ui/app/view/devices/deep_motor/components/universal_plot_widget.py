"""
通用绘图组件
提供统一的matplotlib绘图接口，支持多种数据类型的高性能绘制
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


class UniversalPlotWidget(QWidget):
    """通用绘图组件"""
    
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
        
        # 性能优化相关
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(1000)  # 1000ms更新间隔，大幅降低频率以提升性能
        self.update_timer.timeout.connect(self._throttled_update)
        
        # 坐标轴范围缓存
        self._last_xlim = None
        self._last_ylim = None
        
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
        
        # 创建matplotlib图形
        self.figure = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setMinimumHeight(300)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_xlabel('时间')
        self.ax.set_ylabel('数值')
        self.ax.grid(True)
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
            self.logger.info(f"绘图组件参数改变: {param_text} -> {param_name}")
        
        # 检查是否是示教轨迹参数
        if param_name == 'trajectory_teaching':
            # 示教轨迹参数的特殊处理
            self.ax.clear()
            self.ax.set_xlabel('时间 (s)')
            self.ax.set_ylabel('位置 (°)')
            self.ax.set_title('示教轨迹实时记录')
            self.ax.grid(True, alpha=0.3)
            self.canvas.draw()
        else:
            # 其他参数的通用处理
            self.ax.clear()
            self.ax.set_xlabel('时间')
            self.ax.set_ylabel('数值')
            self.ax.grid(True)
            self.ax.text(0.5, 0.5, '加载中...', ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
        
        # 发射信号
        self.param_changed.emit(param_name)
        
    def _on_refresh_clicked(self):
        """刷新按钮点击处理"""
        if self.logger:
            self.logger.info("绘图组件刷新请求")
        self.refresh_requested.emit()
        
    def _on_restore_clicked(self):
        """恢复默认按钮点击处理"""
        if self.logger:
            self.logger.info("绘图组件恢复默认请求")
        # 这里可以发射恢复默认信号
        self.restore_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        
    def update_data(self, data_dict: Dict[str, Any]):
        """
        更新绘图数据
        :param data_dict: 包含绘图数据的字典
        """
        if self._is_updating:
            return
            
        # 缓存数据
        self.latest_data = data_dict
        
        # 启动定时更新
        if not self.update_timer.isActive():
            self.update_timer.start()
            
    def _throttled_update(self):
        """节流更新方法"""
        if not self.latest_data or self._is_updating:
            return
            
        # 计算数据hash，避免重复绘制
        current_hash = self._calculate_data_hash(self.latest_data)
        if current_hash == self._last_data_hash:
            return
            
        self._is_updating = True
        try:
            self._update_plot_direct(self.latest_data)
            self._last_data_hash = current_hash
        finally:
            self._is_updating = False
            
    def _calculate_data_hash(self, data_dict: Dict[str, Any]) -> Optional[str]:
        """计算数据hash值"""
        try:
            plot_data = data_dict.get('data')
            if plot_data is None:
                return None
                
            if hasattr(plot_data, 'to_string'):
                data_str = plot_data.to_string()
            elif isinstance(plot_data, (list, dict)):
                data_str = str(plot_data)
            else:
                data_str = str(plot_data)
                
            return hashlib.md5(data_str.encode()).hexdigest()
        except Exception:
            return None
            
    def _update_plot_direct(self, data_dict: Dict[str, Any]):
        """直接更新绘图"""
        plot_data = data_dict.get('data')
        total_time = data_dict.get('total_time')
        
        # 清空当前图形
        self.ax.clear()
        
        # 检查数据是否为空
        if plot_data is None or (hasattr(plot_data, 'empty') and plot_data.empty):
            self.ax.set_xlabel('时间')
            self.ax.set_ylabel('数值')
            self.ax.grid(True)
            self.ax.text(0.5, 0.5, '暂无数据', ha='center', va='center', transform=self.ax.transAxes)
            self.canvas.draw()
            return
            
        # 根据数据类型进行绘制
        if hasattr(plot_data, 'columns') and 'type' in plot_data.columns:
            # 轨迹对比数据
            self._plot_trajectory_comparison(plot_data)
        elif hasattr(plot_data, 'columns') and 'time' in plot_data.columns and 'value' in plot_data.columns:
            # DataFrame格式的历史数据
            self._plot_dataframe_history(plot_data)
        elif isinstance(plot_data, list) and plot_data and isinstance(plot_data[0], (list, tuple)):
            # 列表格式的历史数据
            self._plot_list_history(plot_data)
        else:
            # 其他格式数据
            self.ax.text(0.5, 0.5, '不支持的数据格式', ha='center', va='center', transform=self.ax.transAxes)
            
        # 设置标签和网格
        self._set_labels_and_grid()
        
        # 自动调整布局
        self.figure.tight_layout()
        
        # 刷新画布
        self.canvas.draw()
        
        # 更新控制按钮状态
        if total_time is not None:
            self.refresh_button.setEnabled(True)
            self.restore_button.setEnabled(True)
            
    def _plot_trajectory_comparison(self, df: pd.DataFrame):
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
        
        # 设置坐标轴范围
        self._set_axis_limits(original_data, planned_data)
        
    def _plot_dataframe_history(self, df: pd.DataFrame):
        """绘制DataFrame格式的历史数据"""
        times = df['time'].tolist()
        values = df['value'].tolist()
        
        # 检查是否是 mode_state 参数（字符串类型）
        if self.param_combo.currentText().startswith('mode_state'):
            # 对于 mode_state，使用散点图显示状态变化
            self.ax.scatter(times, values, c='red', s=50, alpha=0.7)
            
            # 为不同的状态值添加标签
            unique_values = list(set(values))
            for value in unique_values:
                value_times = [t for t, v in zip(times, values) if v == value]
                if value_times:
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
            
        # 设置坐标轴范围
        if times and values:
            self._set_axis_limits_from_lists(times, values)
            
    def _plot_list_history(self, history_data: List):
        """绘制列表格式的历史数据"""
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
        
        # 格式化x轴时间显示
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
    def _set_labels_and_grid(self):
        """设置标签和网格"""
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
        
    def _set_axis_limits(self, original_data: pd.DataFrame, planned_data: pd.DataFrame):
        """设置坐标轴范围（轨迹对比）"""
        all_times = []
        all_values = []
        
        if not original_data.empty:
            all_times.extend(original_data['time'].tolist())
            all_values.extend(original_data['value'].tolist())
        if not planned_data.empty:
            all_times.extend(planned_data['time'].tolist())
            all_values.extend(planned_data['value'].tolist())
            
        self._set_axis_limits_from_lists(all_times, all_values)
        
    def _set_axis_limits_from_lists(self, times: List, values: List):
        """从列表设置坐标轴范围"""
        if not times or not values:
            return
            
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
        
    def clear_plot(self):
        """清空绘图"""
        self.ax.clear()
        self.ax.set_xlabel('时间')
        self.ax.set_ylabel('数值')
        self.ax.grid(True)
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
        
    def update_teaching_trajectory(self, times: list, positions: list):
        """
        更新示教轨迹实时显示
        :param times: 时间列表
        :param positions: 位置列表
        """
        if self.logger:
            self.logger.debug(f"绘图组件: 收到示教轨迹更新，点数: {len(times) if times else 0}")
        
        # 检查是否有新的数据点
        if not times or not positions:
            if self.logger:
                self.logger.debug("绘图组件: 示教轨迹数据为空")
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
        
    def update_execution_trajectory(self, progress_data: dict):
        """
        更新执行轨迹实时显示
        :param progress_data: 包含执行进度信息的字典
        """
        if self.logger:
            self.logger.debug(f"绘图组件: 收到执行轨迹更新")
        
        executed_times = progress_data.get('executed_times', [])
        executed_positions = progress_data.get('executed_positions', [])
        feedback_times = progress_data.get('feedback_times', [])
        feedback_positions = progress_data.get('feedback_positions', [])
        
        # 检查是否有动画线条
        if hasattr(self, 'planned_line') and hasattr(self, 'feedback_line'):
            # 使用动画线条更新
            self.planned_line.set_data(executed_times, executed_positions)
            self.feedback_line.set_data(feedback_times, feedback_positions)
            
            # 只重绘更新过的艺术家
            self.ax.draw_artist(self.planned_line)
            self.ax.draw_artist(self.feedback_line)
            
            # 将更新后的区域"贴"到画布上
            self.canvas.blit(self.ax.bbox)
            self.canvas.flush_events()
        else:
            # 没有动画线条，使用普通绘制
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
            self.ax.set_title('轨迹执行实时监控')
            self.ax.grid(True, alpha=0.3)
            
            # 添加图例
            if (executed_times and executed_positions) or (feedback_times and feedback_positions):
                self.ax.legend()
            
            # 自动调整布局
            self.figure.tight_layout()
            
            # 刷新画布
            self.canvas.draw()
        
    def set_execution_mode(self, enabled: bool):
        """
        设置执行模式
        :param enabled: 是否启用执行模式
        """
        if self.logger:
            self.logger.debug(f"绘图组件: 设置执行模式: {enabled}")
        
        if enabled:
            # 清空画布并设置执行监控界面
            self.ax.clear()
            self.ax.set_xlabel('时间 (s)')
            self.ax.set_ylabel('位置 (°)')
            self.ax.set_title('轨迹执行实时监控')
            self.ax.grid(True, alpha=0.3)
            
            # 创建空的线条用于动画
            self.planned_line, = self.ax.plot([], [], 'b-', animated=True, label='规划轨迹')
            self.feedback_line, = self.ax.plot([], [], 'r-', animated=True, label='实际反馈')
            self.ax.legend()
            
            # 刷新画布
            self.canvas.draw()
            
            # 启动高频更新定时器
            self.update_timer.setInterval(200)  # 200ms = 5 FPS，降低频率以提升性能
            self.update_timer.start()
        else:
            # 停止执行模式
            self.update_timer.stop()
            if hasattr(self, 'planned_line'):
                self.planned_line.set_animated(False)
            if hasattr(self, 'feedback_line'):
                self.feedback_line.set_animated(False)
        
    def start_updates(self):
        """开始更新"""
        if self.latest_data:
            self.update_timer.start()
