# src/app_logic/device_logic_manager/devices/deep_motor/deep_motor.py
# DeepMotor 无刷电机相关实现

from typing import Dict, Any, List, Callable, Optional
import time
import pandas as pd
import logging
import os

from deepweb.data_management.log_manager import LogManager
from deepweb.config.config_manager import ConfigManager
from deepweb.app_logic.device_logic_manager.devices.base_device import BaseDevice
from deepweb.app_logic.device_logic_manager.devices.base_device import DeviceStatus
from .state_model import DeepMotorState
from .teaching_capability import TeachingCapability

from .data_buffer_manager import DeepMotorDataBufferManager
from .command_parser import CommandParser
from PySide6.QtCore import QObject, Signal, Slot

class DeepMotor(BaseDevice):
    """
    DeepMotor 无刷电机的逻辑实现。
    管理单个电机的状态和响应特定命令。
    示教相关功能通过TeachingCapability能力提供。
    """
    # 轨迹执行相关信号（转发自TeachingCapability）
    send_command_request = Signal(str, str, dict)  # (device_id, command_name, args)
    trajectory_execution_progress_updated = Signal(str, dict)  # (device_id, progress_data)
    trajectory_execution_finished = Signal(str, str)  # (device_id, trajectory_name)
    trajectory_execution_error = Signal(str, str)  # (device_id, error_message)
    
    # 示教轨迹实时更新信号（转发自TeachingCapability）
    teaching_trajectory_updated = Signal(str, list, list)  # 示教轨迹实时更新
    
    def __init__(self, device_id: str, log_manager: LogManager, config_manager: ConfigManager, parent: Optional[QObject] = None):
        super().__init__(device_id, log_manager, parent)
        self._state: DeepMotorState = DeepMotorState(device_id=device_id)
        self.config_manager = config_manager
        self.command_parser = CommandParser()
        
        # 初始化数据缓冲区管理器
        self.data_buffer_manager = DeepMotorDataBufferManager(config_manager, log_manager)
        
        # 添加示教能力
        self.teaching_capability = TeachingCapability(device_id, log_manager, config_manager, self)
        self.add_capability(self.teaching_capability)
        
        # 连接TeachingCapability的信号到DeepMotor的信号（用于转发）
        self.teaching_capability.send_command_request.connect(self.send_command_request.emit)
        self.teaching_capability.trajectory_execution_progress_updated.connect(self.trajectory_execution_progress_updated.emit)
        self.teaching_capability.trajectory_execution_finished.connect(self.trajectory_execution_finished.emit)
        self.teaching_capability.trajectory_execution_error.connect(self.trajectory_execution_error.emit)
        self.teaching_capability.teaching_trajectory_updated.connect(self.teaching_trajectory_updated.emit)
        
        self.logger.info(f"DeepMotor '{device_id}': 初始化完成，历史记录长度设置为 {self.data_buffer_manager.buffer_size}。")

    def get_current_state(self) -> DeepMotorState:
        """重写以返回 DeepMotorState。"""
        return self._state
    
    def get_command_parser(self) -> CommandParser:
        """获取命令解析器"""
        return self.command_parser

    def update_state_from_semantic_data(self, semantic_data: Dict[str, Any]):
        """
        从业务语义数据更新 DeepMotor 的状态模型。
        """
        self.logger.debug(f"DeepMotor '{self.device_id}': 收到语义数据更新: {semantic_data}")
        super().update_state_from_semantic_data(semantic_data)

        # 更新状态模型
        for key, value in semantic_data.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)
        
        current_state_dict = self._state.to_dict()

        # 使用数据缓冲区管理器处理数据 - 优化版本，减少日志记录
        stored_count = 0
        for param_name, value in semantic_data.items():
            if value is not None:
                success = self.data_buffer_manager.add_data_point(param_name, value)
                if success:
                    stored_count += 1
        
        # 减少日志记录频率，只在存储多个参数时记录
        if stored_count > 0 and stored_count % 10 == 0:
            self.logger.debug(f"DeepMotor '{self.device_id}': 成功存储 {stored_count} 个参数到数据缓冲区")

        # 如果正在示教，则记录状态
        if self.teaching_capability.is_teaching(self.device_id):
            self.teaching_capability.record_trajectory_point(
                device_id=self.device_id,
                position=semantic_data.get('position'),
                velocity=semantic_data.get('velocity')
            )

        # 如果正在执行轨迹，记录反馈数据
        if self.teaching_capability.is_executing(self.device_id):
            self.teaching_capability.record_feedback_data(
                device_id=self.device_id,
                position=semantic_data.get('position', 0.0)
            )

        self.logger.debug(f"DeepMotor '{self.device_id}': 特定状态更新完成。")
        self.device_states_updated.emit(self.device_id, current_state_dict)

    def _convert_params_to_args(self, command_name: str, params: Dict[str, Any], command_config: Dict[str, Any]) -> List[Any]:
        """
        将参数字典转换为位置参数列表。
        :param command_name: 命令名称。
        :param params: 参数字典。
        :param command_config: 命令配置。
        :return: 位置参数列表。
        """
        param_names = command_config.get('param_names', [])
        default_values = command_config.get('default_values', [])
        
        args = []
        for i, param_name in enumerate(param_names):
            if param_name in params:
                args.append(params[param_name])
            elif i < len(default_values):
                args.append(default_values[i])
            else:
                # 如果没有默认值，使用None
                args.append(None)
        
        return args

    def get_supported_commands(self) -> List[str]:
        """
        获取 DeepMotor 支持的抽象命令列表。
        """
        base_commands = super().get_supported_commands()
        # 从 CommandParser 获取命令名称，而不是从 DeepMotorCommandConfigs
        config_commands = self.command_parser.get_all_command_names()
        return base_commands + config_commands

    def get_command_help(self, command_name: str = None) -> Dict[str, Any]:
        """
        获取命令帮助信息
        :param command_name: 特定命令名称，如果为None则返回所有命令的帮助
        :return: 命令帮助信息字典
        """
        if command_name:
            # 从 CommandParser 获取特定命令的帮助
            return self.command_parser.get_command_help().get(command_name, {})
        else:
            # 从 CommandParser 获取所有命令的帮助
            return self.command_parser.get_command_help()

    def check_anomaly(self):
        """
        执行 DeepMotor 特定的异常检测。
        """
        super().check_anomaly() # 先执行通用检测
        
        # 温度异常检测
        if self._state.temperature > 90:
            self.device_error.emit(self.device_id, f"DeepMotor '{self.device_id}' 温度过高 ({self._state.temperature}°C)！")
            self._state.connection_status = DeviceStatus.WARNING
            
        # 错误码检测
        if self._state.error_code != 0:
            self.device_error.emit(self.device_id, f"DeepMotor '{self.device_id}' 报告错误码: {self._state.error_code}！")
            self._state.connection_status = DeviceStatus.ERROR
            
        # 故障标志检测
        if self._state.has_faults():
            fault_flags = self._state.get_fault_flags()
            active_faults = [name for name, active in fault_flags.items() if active]
            self.device_error.emit(self.device_id, f"DeepMotor '{self.device_id}' 检测到故障: {', '.join(active_faults)}")
            self._state.connection_status = DeviceStatus.ERROR

    def cleanup(self):
        """
        清理资源，例如停止正在执行的轨迹。
        """
        # 基类会清理所有能力（包括teaching_capability）
        super().cleanup()
        self.logger.info(f"DeepMotor '{self.device_id}': 清理完成。")

    def get_historical_data(self, parameter: str, options: dict = {}) -> Dict[str, Any]:
        """
        获取指定参数的历史数据。
        :param parameter: 参数名称 (e.g., 'position', 'velocity', 'trajectory_both')
        :param options: 其他选项 (e.g., a time range, trajectory_name)
        :return: 包含绘图数据和元数据（如总时长）的字典
        """
        # 处理轨迹相关参数
        if parameter.startswith('trajectory_'):
            trajectory_name = options.get('trajectory_name')
            if not trajectory_name:
                self.logger.warning(f"DeepMotor '{self.device_id}': 请求轨迹数据但未提供轨迹名称")
                return {'data': pd.DataFrame(columns=['time', 'value', 'type'])}
            
            # 从 teaching_capability 获取轨迹可视化数据
            vis_data = self.teaching_capability.get_trajectory_visualization_data(trajectory_name)
            if not vis_data:
                return {'data': pd.DataFrame(columns=['time', 'value', 'type'])}
            
            # 准备DataFrame
            data_list = []
            df = pd.DataFrame()

            if parameter == 'trajectory_original':
                times = vis_data.get('original_times', [])
                positions = vis_data.get('original_positions', [])
                data_list = [{'time': t, 'value': p, 'type': 'original'} for t, p in zip(times, positions)]
                df = pd.DataFrame(data_list)
            
            elif parameter == 'trajectory_planned':
                times = vis_data.get('planned_times', [])
                positions = vis_data.get('planned_positions', [])
                data_list = [{'time': t, 'value': p, 'type': 'planned'} for t, p in zip(times, positions)]
                df = pd.DataFrame(data_list)
            
            elif parameter == 'trajectory_both':
                original_times = vis_data.get('original_times', [])
                original_positions = vis_data.get('original_positions', [])
                planned_times = vis_data.get('planned_times', [])
                planned_positions = vis_data.get('planned_positions', [])
                
                for t, p in zip(original_times, original_positions):
                    data_list.append({'time': t, 'value': p, 'type': 'original'})
                for t, p in zip(planned_times, planned_positions):
                    data_list.append({'time': t, 'value': p, 'type': 'planned'})
                df = pd.DataFrame(data_list)
            
            return {
                'data': df,
                'total_time': vis_data.get('total_time')
            }
        
        # 处理示教轨迹参数
        elif parameter == 'teaching_trajectory':
            # 示教轨迹使用 position 数据
            history_data = self.data_buffer_manager.get_historical_data('position')
            if history_data:
                self.logger.debug(f"DeepMotor '{self.device_id}': 正在获取示教轨迹数据，当前有 {history_data['total_points']} 条记录。")
                return {'data': history_data['data']}
            else:
                return {'data': pd.DataFrame(columns=['time', 'value'])}
        
        # 处理普通的历史数据参数
        else:
            history_data = self.data_buffer_manager.get_historical_data(parameter, options)
            if history_data:
                self.logger.debug(f"DeepMotor '{self.device_id}': 正在获取参数 '{parameter}' 的历史数据，当前有 {history_data['total_points']} 条记录。")
                return {'data': history_data['data']}
            else:
                self.logger.warning(f"DeepMotor '{self.device_id}': 请求了未知的历史数据参数 '{parameter}'")
                return {'data': pd.DataFrame(columns=['time', 'value'])}

    # === 新增：数据缓冲区管理接口 ===
    def get_buffer_info(self) -> Dict[str, Any]:
        """获取缓冲区信息"""
        return self.data_buffer_manager.get_buffer_info()
    
    def get_parameter_statistics(self, parameter: str) -> Optional[Dict[str, Any]]:
        """获取参数统计信息"""
        return self.data_buffer_manager.get_statistics(parameter)
    
    def clear_data_buffer(self, parameter: Optional[str] = None):
        """清空数据缓冲区"""
        self.data_buffer_manager.clear_buffer(parameter)
        self.logger.info(f"DeepMotor '{self.device_id}': 已清空数据缓冲区" + (f"参数 '{parameter}'" if parameter else ""))
    
    def resize_data_buffer(self, new_size: int):
        """调整数据缓冲区大小"""
        self.data_buffer_manager.resize_buffer(new_size)
        self.logger.info(f"DeepMotor '{self.device_id}': 数据缓冲区大小已调整为 {new_size}")
    
    # === 新增：状态管理接口 ===
    def get_motion_state(self) -> Dict[str, float]:
        """获取运动状态"""
        return self._state.get_motion_state()
    
    def get_fault_flags(self) -> Dict[str, bool]:
        """获取故障标志"""
        return self._state.get_fault_flags()
    
    def has_faults(self) -> bool:
        """检查是否有故障"""
        return self._state.has_faults()
    
    def get_status_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        return self._state.get_status_summary()