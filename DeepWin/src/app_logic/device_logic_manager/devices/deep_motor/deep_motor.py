# src/app_logic/device_logic_manager/devices/deep_motor/deep_motor.py
# DeepMotor 无刷电机相关实现

from typing import Dict, Any, List, Callable, Optional
import copy
import time
import pandas as pd
import logging
import os

from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager
from src.app_logic.device_logic_manager.devices.base_device import BaseDevice
from src.app_logic.device_logic_manager.device_models import DeepMotorState, DeviceStatus
from .teaching_trajectory_manager import TeachingTrajectoryManager
from PySide6.QtCore import QObject, Signal, Slot

class DeepMotor(BaseDevice):
    """
    DeepMotor 无刷电机的逻辑实现。
    管理单个电机的状态和响应特定命令。
    轨迹相关功能委托给 TeachingTrajectoryManager 处理。
    """
    # 新增：轨迹执行相关信号
    send_command_request = Signal(str, str, list)  # (device_id, command_name, args)
    
    def __init__(self, device_id: str, log_manager: LogManager, config_manager: ConfigManager, parent: Optional[QObject] = None):
        super().__init__(device_id, log_manager, parent)
        self._state: DeepMotorState = DeepMotorState(device_id=device_id)
        self.config_manager = config_manager
        
        # 初始化数据缓冲区 - 扩展支持所有相关参数
        self.data_buffer = {
            "position": pd.DataFrame(columns=['time', 'value']),
            "velocity": pd.DataFrame(columns=['time', 'value']),
            "torque": pd.DataFrame(columns=['time', 'value']),
            "temperature": pd.DataFrame(columns=['time', 'value']),
            "error_code": pd.DataFrame(columns=['time', 'value']),
            "motor_can_id": pd.DataFrame(columns=['time', 'value']),
            "mode_state": pd.DataFrame(columns=['time', 'value']),
            "flt_uninitialized": pd.DataFrame(columns=['time', 'value']),
            "flt_hall_encoding": pd.DataFrame(columns=['time', 'value']),
            "flt_magnetic_encoding": pd.DataFrame(columns=['time', 'value']),
            "flt_over_temperature": pd.DataFrame(columns=['time', 'value']),
            "flt_over_current": pd.DataFrame(columns=['time', 'value']),
            "flt_voltage_drop": pd.DataFrame(columns=['time', 'value'])
        }
        self.buffer_size = self.config_manager.get("device_settings.deepmotor_history_length", 1000)
        
        # 添加相对时间起始点
        self._start_time = time.time()

        # 初始化示教管理器
        # 使用设备目录下的 trajectories 文件夹
        current_dir = os.path.dirname(os.path.abspath(__file__))
        trajectory_folder = os.path.join(current_dir, 'trajectories')
        self.teaching_manager = TeachingTrajectoryManager(log_manager=log_manager, trajectory_folder=trajectory_folder)
        
        # 连接 TeachingTrajectoryManager 的命令发送信号到 DeepMotor 的信号
        self.teaching_manager._send_command_request.connect(self.send_command_request.emit)
        
        self.logger.info(f"DeepMotor '{device_id}': 初始化完成，历史记录长度设置为 {self.buffer_size}。")

    def get_current_state(self) -> DeepMotorState:
        """重写以返回 DeepMotorState。"""
        return self._state

    def update_state_from_semantic_data(self, semantic_data: Dict[str, Any]):
        """
        从业务语义数据更新 DeepMotor 的状态模型。
        """
        self.logger.debug(f"DeepMotor '{self.device_id}': 收到语义数据更新: {semantic_data}")
        super().update_state_from_semantic_data(semantic_data)

        for key, value in semantic_data.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)
        
        current_state_dict = self._state.to_dict()

        # 更新数据缓冲区 - 使用相对时间
        relative_time = time.time() - self._start_time
        
        # 定义需要存储历史数据的参数映射
        parameter_mapping = {
            'position': 'position',
            'velocity': 'velocity', 
            'torque': 'torque',
            'temperature': 'temperature',
            'error_code': 'error_code',
            'motor_can_id': 'motor_can_id',
            'mode_state': 'mode_state',
            'flt_uninitialized': 'flt_uninitialized',
            'flt_hall_encoding': 'flt_hall_encoding',
            'flt_magnetic_encoding': 'flt_magnetic_encoding',
            'flt_over_temperature': 'flt_over_temperature',
            'flt_over_current': 'flt_over_current',
            'flt_voltage_drop': 'flt_voltage_drop'
        }
        
        # 遍历所有参数，如果语义数据中包含该参数，则存储到对应的缓冲区
        for semantic_key, buffer_key in parameter_mapping.items():
            if semantic_key in semantic_data:
                value = semantic_data[semantic_key]
                # self.logger.debug(f"DeepMotor '{self.device_id}': 处理参数 {semantic_key} = {value} (类型: {type(value)})")
                
                # 对于 mode_state，支持字符串类型；对于其他参数，只接受数值类型
                if value is not None:
                    if semantic_key == 'mode_state':
                        # mode_state 是字符串类型，直接存储
                        new_data = pd.DataFrame([{'time': relative_time, 'value': value}])
                        self.data_buffer[buffer_key] = pd.concat([self.data_buffer[buffer_key], new_data], ignore_index=True)
                        # self.logger.debug(f"DeepMotor '{self.device_id}': 存储 mode_state 数据: {value}")
                    elif isinstance(value, (int, float)):
                        # 其他参数必须是数值类型
                        new_data = pd.DataFrame([{'time': relative_time, 'value': value}])
                        self.data_buffer[buffer_key] = pd.concat([self.data_buffer[buffer_key], new_data], ignore_index=True)
                        # self.logger.debug(f"DeepMotor '{self.device_id}': 存储数值数据 {semantic_key}: {value}")
                    else:
                        self.logger.warning(f"DeepMotor '{self.device_id}': 参数 {semantic_key} 的值 {value} 不是支持的格式")
                else:
                    self.logger.debug(f"DeepMotor '{self.device_id}': 参数 {semantic_key} 的值为 None，跳过存储")
        
        # 限制缓冲区大小
        for key in self.data_buffer:
            if len(self.data_buffer[key]) > self.buffer_size:
                self.data_buffer[key] = self.data_buffer[key].iloc[-self.buffer_size:]
        
        # 添加调试日志，显示每个缓冲区中的数据点数
        for key in self.data_buffer:
            if len(self.data_buffer[key]) > 0:
                # self.logger.debug(f"DeepMotor '{self.device_id}': 缓冲区 {key} 有 {len(self.data_buffer[key])} 个数据点")
                pass

        # 如果正在示教，则记录状态
        if self.teaching_manager.is_teaching(self.device_id):
            self.teaching_manager.record_trajectory_point(
                device_id=self.device_id,
                position=semantic_data.get('position'),
                velocity=semantic_data.get('velocity')
            )

        self.logger.debug(f"DeepMotor '{self.device_id}': 特定状态更新完成。")
        self.device_states_updated.emit(self.device_id, current_state_dict)

    def execute_abstract_command(self,
                                 command_name: str,
                                 args: List[Any],
                                 send_request_signal: Signal):
        """
        执行 DeepMotor 特定的抽象命令。
        :param command_name: 抽象命令的名称 (如 "set_rpm", "get_status")。
        :param args: 命令的参数列表。
        :param send_request_signal: 用于请求 Coordinator 发送底层命令的信号。
        """
        self.logger.info(f"DeepMotor '{self.device_id}': 收到命令 '{command_name}' with args {args}")
        if command_name == "set_rpm":
            if args and isinstance(args[0], (int, float)):
                rpm = int(args[0])
                self.logger.debug(f"DeepMotor '{self.device_id}': 请求设置 RPM 到 {rpm}")
                # 请求 Coordinator 通过服务层发送底层命令
                send_request_signal.emit(self.device_id, "set_motor_rpm", [rpm])
                self.logger.info(f"DeepMotor '{self.device_id}': 已请求设置 RPM 为 {rpm}")
            else:
                self.device_error.emit(self.device_id, "设置 RPM 命令需要一个数字参数。")
        # jog
        elif command_name == "jog_motor":
            motor_id = args[0] if args else 1
            speed = args[1] if len(args) > 1 else 0
            self.logger.debug(f"DeepMotor '{self.device_id}': 请求点动电机 {motor_id} 速度为 {speed}")
            send_request_signal.emit(self.device_id, "jog_motor", [motor_id, speed])
            self.logger.info(f"DeepMotor '{self.device_id}': 已请求点动电机 {motor_id} 速度为 {speed}")
        # stop_jog_motor
        elif command_name == "stop_jog_motor":
            motor_id = args[0] if args else 1
            self.logger.debug(f"DeepMotor '{self.device_id}': 请求停止点动电机 {motor_id}")
            send_request_signal.emit(self.device_id, "stop_jog_motor", [motor_id])
            self.logger.info(f"DeepMotor '{self.device_id}': 已请求停止点动电机 {motor_id}")
        elif command_name == "enable_motor":
            motor_id = args[0] if args else 1
            self.logger.debug(f"DeepMotor '{self.device_id}': 请求使能电机 {motor_id}")
            send_request_signal.emit(self.device_id, "enable_motor", [motor_id])
            self.logger.info(f"DeepMotor '{self.device_id}': 已请求使能电机 {motor_id}")
        elif command_name == "disable_motor":
            motor_id = args[0] if args else 1
            self.logger.debug(f"DeepMotor '{self.device_id}': 请求失能电机 {motor_id}")
            send_request_signal.emit(self.device_id, "disable_motor", [motor_id])
            self.logger.info(f"DeepMotor '{self.device_id}': 已请求失能电机 {motor_id}")
        elif command_name == "init_motor":
            motor_id = args[0] if args else 1
            self.logger.debug(f"DeepMotor '{self.device_id}': 请求初始化电机 {motor_id}")
            send_request_signal.emit(self.device_id, "init_motor", [motor_id])
            self.logger.info(f"DeepMotor '{self.device_id}': 已请求初始化电机 {motor_id}")
        elif command_name == "reset_motor":
            motor_id = args[0] if args else 1
            self.logger.debug(f"DeepMotor '{self.device_id}': 请求重置电机 {motor_id}")
            send_request_signal.emit(self.device_id, "reset_motor", [motor_id])
            self.logger.info(f"DeepMotor '{self.device_id}': 已请求重置电机 {motor_id}")
        elif command_name == "zero_motor":
            motor_id = args[0] if args else 1
            self.logger.debug(f"DeepMotor '{self.device_id}': 请求零点标定电机 {motor_id}")
            send_request_signal.emit(self.device_id, "zero_motor", [motor_id])
            self.logger.info(f"DeepMotor '{self.device_id}': 已请求零点标定电机 {motor_id}")
        elif command_name == "set_motor_mode":
            motor_id = args[0] if args else 1
            mode = args[1] if len(args) > 1 else None
            self.logger.debug(f"DeepMotor '{self.device_id}': 请求设置电机 {motor_id} 模式为 {mode}")
            send_request_signal.emit(self.device_id, "set_motor_mode", [motor_id, mode])
            self.logger.info(f"DeepMotor '{self.device_id}': 已请求设置电机 {motor_id} 模式为 {mode}")
        elif command_name == "set_motor_position":
            motor_id = args[0] if args else 1
            position = args[1] if len(args) > 1 else None
            self.logger.debug(f"DeepMotor '{self.device_id}': 请求设置电机 {motor_id} 位置为 {position}")
            send_request_signal.emit(self.device_id, "set_motor_position", [motor_id, position])
            self.logger.info(f"DeepMotor '{self.device_id}': 已请求设置电机 {motor_id} 位置为 {position}")
        elif command_name == "set_motor_pos_speed":
            motor_id = args[0] if args else 1
            position = args[1] if len(args) > 1 else None
            speed = args[2] if len(args) > 2 else None
            self.logger.debug(f"DeepMotor '{self.device_id}': 请求设置电机 {motor_id} 位置为 {position}，速度为 {speed}")
            send_request_signal.emit(self.device_id, "set_motor_pos_speed", [motor_id, position, speed])
            self.logger.info(f"DeepMotor '{self.device_id}': 已请求设置电机 {motor_id} 位置为 {position}，速度为 {speed}")
        elif command_name == "get_status":
            self.logger.info(f"DeepMotor '{self.device_id}': 返回当前状态: {self._state.to_dict()}")
            # 状态已经通过 device_states_updated 信号发出，这里只是日志
        else:
            super().execute_abstract_command(command_name, args, send_request_signal) # 转发到基类处理未知命令

    def get_supported_commands(self) -> List[str]:
        """
        获取 DeepMotor 支持的抽象命令列表。
        """
        return super().get_supported_commands() + [
            "set_rpm", 
            "enable_motor",
            "init_motor",
            "reset_motor",
            "zero_motor",
            "set_motor_mode",
            "set_motor_position",
            "set_motor_pos_speed"
        ]

    def check_anomaly(self):
        """
        执行 DeepMotor 特定的异常检测。
        """
        super().check_anomaly() # 先执行通用检测
        if self._state.temperature > 90:
            self.device_error.emit(self.device_id, f"DeepMotor '{self.device_id}' 温度过高 ({self._state.temperature}°C)！")
            self._state.connection_status = DeviceStatus.WARNING # 更新状态为警告
        if self._state.error_code != 0:
            self.device_error.emit(self.device_id, f"DeepMotor '{self.device_id}' 报告错误码: {self._state.error_code}！")
            self._state.connection_status = DeviceStatus.ERROR # 更新状态为错误

    def cleanup(self):
        """
        清理资源，例如停止正在执行的轨迹。
        """
        # 停止轨迹执行
        if self.teaching_manager:
            self.teaching_manager.stop_trajectory_execution(self.device_id)
            self.teaching_manager.cleanup()
        
        self.logger.info(f"DeepMotor '{self.device_id}': 清理完成。")
        super().cleanup()

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
            
            # 从 teaching_manager 获取轨迹可视化数据
            vis_data = self.get_trajectory_visualization_data(trajectory_name)
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
            if 'position' in self.data_buffer:
                self.logger.debug(f"DeepMotor '{self.device_id}': 正在获取示教轨迹数据，当前有 {len(self.data_buffer['position'])} 条记录。")
                return {'data': self.data_buffer['position'].copy()}
            else:
                return {'data': pd.DataFrame(columns=['time', 'value'])}
        
        # 处理普通的历史数据参数
        elif parameter in self.data_buffer:
            self.logger.debug(f"DeepMotor '{self.device_id}': 正在获取参数 '{parameter}' 的历史数据，当前有 {len(self.data_buffer[parameter])} 条记录。")
            return {'data': self.data_buffer[parameter].copy()}
        else:
            self.logger.warning(f"DeepMotor '{self.device_id}': 请求了未知的历史数据参数 '{parameter}'")
            return {'data': pd.DataFrame(columns=['time', 'value'])}

    def start_teaching(self, device_id: str, motor_id: int = 1):
        """
        开始示教
        :param device_id: 开始示教的设备ID
        :param motor_id: 要示教的电机ID
        """
        self.logger.info(f"正在为设备 '{self.device_id}' 清空历史位置数据并开始示教，motor_id: {motor_id}")
        # 清空当前的位置历史数据，以便实时显示示教轨迹
        if 'position' in self.data_buffer:
            self.data_buffer['position'] = pd.DataFrame(columns=['time', 'value'])
        
        if self.teaching_manager:
            return self.teaching_manager.start_teaching(device_id, motor_id)

    def stop_teaching(self, device_id: str) -> Optional[str]:
        """
        停止示教
        :param device_id: 停止示教的设备ID
        :return: 保存的轨迹文件名，如果未保存则返回None
        """
        self.logger.info(f"正在停止对设备 '{self.device_id}' 的示教。")
        if self.teaching_manager:
            trajectory_name = self.teaching_manager.stop_teaching(device_id)
            return trajectory_name
        return None

    def replan_trajectory(self, trajectory_name: str, duration: float):
        """
        使用新的时长重新规划轨迹
        :param trajectory_name: 轨迹名称
        :param duration: 新的执行时长
        """
        if self.teaching_manager:
            self.teaching_manager.replan_trajectory_with_duration(trajectory_name, duration)

    def replan_with_original_time(self, trajectory_name: str):
        """
        使用原始时间戳重新规划轨迹
        """
        if self.teaching_manager:
            self.teaching_manager.replan_trajectory_with_original_time(trajectory_name)

    def get_trajectory_list(self) -> list:
        """
        获取示教轨迹列表
        """
        if self.teaching_manager:
            return self.teaching_manager.get_trajectory_names_for_device(self.device_id)
        return []

    def get_trajectory_visualization_data(self, trajectory_name: str) -> dict:
        """
        获取轨迹可视化数据
        """
        if self.teaching_manager:
            return self.teaching_manager.get_trajectory_visualization_data(trajectory_name)
        return {}

    def execute_trajectory(self, trajectory_name: str, motor_id: int, use_planned_trajectory: bool = True):
        """
        执行指定的示教轨迹
        :param trajectory_name: 轨迹名称
        :param motor_id: 电机ID
        :param use_planned_trajectory: 是否使用规划轨迹，True使用规划轨迹（平滑控制），False使用原始轨迹（便于调试）
        """
        self.logger.info(f"DeepMotor '{self.device_id}': 委托 TeachingTrajectoryManager 执行轨迹 '{trajectory_name}', motor_id: {motor_id}, 使用规划轨迹: {use_planned_trajectory}")
        if self.teaching_manager:
            self.teaching_manager.execute_trajectory(self.device_id, trajectory_name, motor_id, use_planned_trajectory)

    def stop_trajectory_execution(self):
        """
        停止轨迹执行
        """
        self.logger.info(f"DeepMotor '{self.device_id}': 委托 TeachingTrajectoryManager 停止轨迹执行")
        if self.teaching_manager:
            self.teaching_manager.stop_trajectory_execution(self.device_id)

    def reload_trajectories(self):
        """
        重新从文件加载所有轨迹。
        """
        if self.teaching_manager:
            self.teaching_manager.load_all_trajectories()
            self.logger.info(f"设备 '{self.device_id}' 的轨迹已重新加载。")