# src/app_logic/device_logic_manager/devices/deep_motor/teaching_capability.py
# 示教能力实现

from typing import Dict, Any, List, Callable, Optional
import pandas as pd

from deepweb.app_logic.device_logic_manager.devices.base_device import DeviceCapability
from deepweb.data_management.log_manager import LogManager
from deepweb.config.config_manager import ConfigManager
from .teaching_trajectory_manager import TeachingTrajectoryManager


class TeachingCapability(DeviceCapability):
    """
    示教能力实现
    将TeachingTrajectoryManager包装为DeviceCapability
    使用回调机制替代 PySide6 信号槽
    """
    
    def __init__(self, device_id: str, log_manager: LogManager, config_manager: ConfigManager, parent=None):
        self.device_id = device_id
        self.logger = log_manager.get_logger(f"{self.__class__.__name__}.{device_id}")
        
        # 回调函数列表（替代信号）
        self._trajectory_execution_progress_updated_callbacks: List[Callable[[str, dict], None]] = []
        self._trajectory_execution_finished_callbacks: List[Callable[[str, str], None]] = []
        self._trajectory_execution_error_callbacks: List[Callable[[str, str], None]] = []
        self._teaching_trajectory_updated_callbacks: List[Callable[[str, list, list], None]] = []
        self._send_command_request_callbacks: List[Callable[[str, str, dict], None]] = []
        
        # 初始化示教管理器
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        trajectory_folder = os.path.join(current_dir, 'trajectories')
        self.teaching_manager = TeachingTrajectoryManager(
            log_manager=log_manager, 
            config_manager=config_manager, 
            trajectory_folder=trajectory_folder
        )
        
        # 注册回调（替代信号连接）
        self.teaching_manager.register_callback('trajectory_execution_progress_detailed', self._on_trajectory_execution_progress_updated)
        self.teaching_manager.register_callback('trajectory_execution_finished', self._on_trajectory_execution_finished)
        self.teaching_manager.register_callback('trajectory_execution_error', self._on_trajectory_execution_error)
        self.teaching_manager.register_callback('teaching_trajectory_updated', self._on_teaching_trajectory_updated)
        self.teaching_manager.register_callback('send_command_request', self._on_send_command_request)
        
        self.logger.info(f"TeachingCapability '{device_id}': 初始化完成")
    
    def register_callback(self, event_name: str, callback: Callable):
        """注册回调函数（替代信号连接）"""
        if event_name == 'trajectory_execution_progress_updated':
            self._trajectory_execution_progress_updated_callbacks.append(callback)
        elif event_name == 'trajectory_execution_finished':
            self._trajectory_execution_finished_callbacks.append(callback)
        elif event_name == 'trajectory_execution_error':
            self._trajectory_execution_error_callbacks.append(callback)
        elif event_name == 'teaching_trajectory_updated':
            self._teaching_trajectory_updated_callbacks.append(callback)
        elif event_name == 'send_command_request':
            self._send_command_request_callbacks.append(callback)
        else:
            self.logger.warning(f"未知的事件名称: {event_name}")
    
    def _on_trajectory_execution_progress_updated(self, device_id: str, progress_data: dict):
        """内部回调：轨迹执行进度更新"""
        for callback in self._trajectory_execution_progress_updated_callbacks:
            try:
                callback(device_id, progress_data)
            except Exception as e:
                self.logger.error(f"回调执行错误: {e}")
    
    def _on_trajectory_execution_finished(self, device_id: str, trajectory_name: str):
        """内部回调：轨迹执行完成"""
        for callback in self._trajectory_execution_finished_callbacks:
            try:
                callback(device_id, trajectory_name)
            except Exception as e:
                self.logger.error(f"回调执行错误: {e}")
    
    def _on_trajectory_execution_error(self, device_id: str, error_message: str):
        """内部回调：轨迹执行错误"""
        for callback in self._trajectory_execution_error_callbacks:
            try:
                callback(device_id, error_message)
            except Exception as e:
                self.logger.error(f"回调执行错误: {e}")
    
    def _on_teaching_trajectory_updated(self, device_id: str, times: list, positions: list):
        """内部回调：示教轨迹更新"""
        for callback in self._teaching_trajectory_updated_callbacks:
            try:
                callback(device_id, times, positions)
            except Exception as e:
                self.logger.error(f"回调执行错误: {e}")
    
    def _on_send_command_request(self, device_id: str, command_name: str, args: dict):
        """内部回调：发送命令请求"""
        for callback in self._send_command_request_callbacks:
            try:
                callback(device_id, command_name, args)
            except Exception as e:
                self.logger.error(f"回调执行错误: {e}")

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