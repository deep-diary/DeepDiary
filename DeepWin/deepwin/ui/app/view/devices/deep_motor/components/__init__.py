"""
DeepMotor 页面组件包
包含电机控制页面的各个功能组件
"""

from .universal_plot_widget import UniversalPlotWidget
from .communication_widget import CommunicationWidget
from .motor_control_widget import MotorControlWidget
from .teaching_control_widget import TeachingControlWidget
from .history_curve_widget import HistoryCurveWidget

__all__ = [
    'UniversalPlotWidget',
    'CommunicationWidget', 
    'MotorControlWidget',
    'TeachingControlWidget',
    'HistoryCurveWidget'
]
