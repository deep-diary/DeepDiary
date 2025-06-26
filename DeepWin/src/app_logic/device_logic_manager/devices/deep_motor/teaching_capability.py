# src/app_logic/device_logic_manager/devices/deep_motor/teaching_capability.py
# 示教能力实现

from typing import Dict, Any, List, Callable, Optional
from PySide6.QtCore import QObject, Signal
import pandas as pd

from src.app_logic.device_logic_manager.devices.base_device import DeviceCapability
from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager
from .teaching_trajectory_manager import TeachingTrajectoryManager


class TeachingCapability(QObject, DeviceCapability):
    """
    示教能力实现
    将TeachingTrajectoryManager包装为DeviceCapability
    """
    
    # 示教相关信号
    trajectory_execution_progress_updated = Signal(str, dict)  # (device_id, progress_data)
    trajectory_execution_finished = Signal(str, str)  # (device_id, trajectory_name)
    trajectory_execution_error = Signal(str, str)  # (device_id, error_message)
    teaching_trajectory_updated = Signal(str, list, list)  # 示教轨迹实时更新
    send_command_request = Signal(str, str, list)  # (device_id, command_name, args)

    def __init__(self, device_id: str, log_manager: LogManager, config_manager: ConfigManager, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.device_id = device_id
        self.logger = log_manager.get_logger(f"{self.__class__.__name__}.{device_id}")
        
        # 初始化示教管理器
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        trajectory_folder = os.path.join(current_dir, 'trajectories')
        self.teaching_manager = TeachingTrajectoryManager(
            log_manager=log_manager, 
            config_manager=config_manager, 
            trajectory_folder=trajectory_folder
        )
        
        # 连接信号
        self.teaching_manager._trajectory_execution_progress_detailed.connect(self.trajectory_execution_progress_updated.emit)
        self.teaching_manager._trajectory_execution_finished.connect(self.trajectory_execution_finished.emit)
        self.teaching_manager._trajectory_execution_error.connect(self.trajectory_execution_error.emit)
        self.teaching_manager._teaching_trajectory_updated.connect(self.teaching_trajectory_updated.emit)
        self.teaching_manager._send_command_request.connect(self.send_command_request.emit)
        
        self.logger.info(f"TeachingCapability '{device_id}': 初始化完成")

    def get_capability_name(self) -> str:
        """获取能力名称"""
        return "teaching"

    def get_supported_methods(self) -> Dict[str, Callable]:
        """返回支持的方法映射"""
        return {
            'start_teaching': self.start_teaching,
            'stop_teaching': self.stop_teaching,
            'execute_trajectory': self.execute_trajectory,
            'get_trajectory_list': self.get_trajectory_list,
            'reload_trajectories': self.reload_trajectories,
            'replan_trajectory': self.replan_trajectory,
            'replan_with_original_time': self.replan_with_original_time,
            'delete_trajectory': self.delete_trajectory,
            'get_trajectory_visualization_data': self.get_trajectory_visualization_data,
            'stop_trajectory_execution': self.stop_trajectory_execution,
            'is_teaching': self.is_teaching,
            'is_executing': self.is_executing,
            'record_trajectory_point': self.record_trajectory_point,
            'record_feedback_data': self.record_feedback_data,
            'get_execution_data': self.get_execution_data
        }

    def start_teaching(self, device_id: str, motor_id: int = 1):
        """开始示教"""
        # 清空历史位置数据，以便实时显示示教轨迹
        if hasattr(self, 'parent_device') and hasattr(self.parent_device, 'data_buffer'):
            if 'position' in self.parent_device.data_buffer:
                self.parent_device.data_buffer['position'] = pd.DataFrame(columns=['time', 'value'])
                self.logger.info(f"已清空设备 '{device_id}' 的历史位置数据")
        
        return self.teaching_manager.start_teaching(device_id, motor_id)

    def stop_teaching(self, device_id: str) -> Optional[str]:
        """停止示教"""
        return self.teaching_manager.stop_teaching(device_id)

    def execute_trajectory(self, device_id: str, trajectory_name: str, motor_id: int, use_planned_trajectory: bool = True):
        """执行轨迹"""
        self.teaching_manager.execute_trajectory(device_id, trajectory_name, motor_id, use_planned_trajectory)

    def get_trajectory_list(self, device_id: str) -> List[str]:
        """获取轨迹列表"""
        return self.teaching_manager.get_trajectory_names_for_device(device_id)

    def reload_trajectories(self, device_id: str):
        """重新加载轨迹"""
        self.teaching_manager.load_all_trajectories()

    def replan_trajectory(self, trajectory_name: str, duration: float):
        """重新规划轨迹"""
        self.teaching_manager.replan_trajectory_with_duration(trajectory_name, duration)

    def replan_with_original_time(self, trajectory_name: str):
        """使用原始时间重新规划轨迹"""
        self.teaching_manager.replan_trajectory_with_original_time(trajectory_name)

    def delete_trajectory(self, trajectory_name: str) -> bool:
        """删除轨迹"""
        return self.teaching_manager.delete_trajectory(trajectory_name)

    def get_trajectory_visualization_data(self, trajectory_name: str) -> Dict[str, Any]:
        """获取轨迹可视化数据"""
        return self.teaching_manager.get_trajectory_visualization_data(trajectory_name)

    def stop_trajectory_execution(self, device_id: str = None):
        """停止轨迹执行"""
        self.teaching_manager.stop_trajectory_execution(device_id)

    def is_teaching(self, device_id: str) -> bool:
        """检查是否正在示教"""
        return self.teaching_manager.is_teaching(device_id)

    def is_executing(self, device_id: str) -> bool:
        """检查是否正在执行轨迹"""
        return self.teaching_manager.is_executing(device_id)

    def record_trajectory_point(self, device_id: str, position: float, velocity: float):
        """记录轨迹点"""
        self.teaching_manager.record_trajectory_point(device_id, position, velocity)

    def record_feedback_data(self, device_id: str, position: float):
        """记录反馈数据"""
        self.teaching_manager.record_feedback_data(device_id, position)

    def get_execution_data(self, device_id: str) -> Dict[str, Any]:
        """获取执行数据"""
        return self.teaching_manager.get_execution_data(device_id)

    def cleanup(self):
        """清理资源"""
        if self.teaching_manager:
            self.teaching_manager.cleanup()
        self.logger.info(f"TeachingCapability '{self.device_id}': 清理完成") 