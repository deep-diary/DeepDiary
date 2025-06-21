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
    """
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
        # 将轨迹点就绪信号连接到发送电机指令的方法
        self.teaching_manager._trajectory_point_ready.connect(self._on_trajectory_point_ready)
        
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
                self.logger.debug(f"DeepMotor '{self.device_id}': 处理参数 {semantic_key} = {value} (类型: {type(value)})")
                
                # 对于 mode_state，支持字符串类型；对于其他参数，只接受数值类型
                if value is not None:
                    if semantic_key == 'mode_state':
                        # mode_state 是字符串类型，直接存储
                        new_data = pd.DataFrame([{'time': relative_time, 'value': value}])
                        self.data_buffer[buffer_key] = pd.concat([self.data_buffer[buffer_key], new_data], ignore_index=True)
                        self.logger.debug(f"DeepMotor '{self.device_id}': 存储 mode_state 数据: {value}")
                    elif isinstance(value, (int, float)):
                        # 其他参数必须是数值类型
                        new_data = pd.DataFrame([{'time': relative_time, 'value': value}])
                        self.data_buffer[buffer_key] = pd.concat([self.data_buffer[buffer_key], new_data], ignore_index=True)
                        self.logger.debug(f"DeepMotor '{self.device_id}': 存储数值数据 {semantic_key}: {value}")
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
                self.logger.debug(f"DeepMotor '{self.device_id}': 缓冲区 {key} 有 {len(self.data_buffer[key])} 个数据点")

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
        self.teaching_manager.stop_playback()
        self.logger.info(f"DeepMotor '{self.device_id}': 清理完成。")
        super().cleanup()

    def get_historical_data(self, parameter: str, options: dict = {}) -> pd.DataFrame:
        """
        获取历史数据。
        - 对于 position, velocity, speed, torque, temperature, current, error_code, 
          motor_can_id, mode_state, flt_* 等参数，从环形缓冲区获取。
        - 对于轨迹相关，从 teaching_manager 获取。
        """
        # 定义所有支持的参数列表
        supported_parameters = [
            "position", "velocity", "torque", "temperature",
            "error_code", "motor_can_id", "mode_state", "flt_uninitialized",
            "flt_hall_encoding", "flt_magnetic_encoding", "flt_over_temperature",
            "flt_over_current", "flt_voltage_drop"
        ]
        
        # 如果请求 '示教轨迹'，则返回 'position' 数据
        effective_parameter = 'position' if parameter == 'teaching_trajectory' else parameter
        
        if effective_parameter in supported_parameters:
            data = self.data_buffer.get(effective_parameter, pd.DataFrame(columns=['time', 'value']))
            logging.debug(f"获取到历史数据: {parameter}, 数据点数: {len(data)}")
            return data.copy()
        
        elif parameter in ["trajectory_original", "trajectory_planned", "trajectory_comparison", "trajectory_both"]:
            trajectory_name = options.get("trajectory_name")
            if not trajectory_name:
                logging.warning("请求轨迹数据，但未提供轨迹名称。")
                return pd.DataFrame()
            
            logging.debug(f"向 teaching_manager 请求轨迹数据: {trajectory_name}, 类型: {parameter}")
            # 使用现有的方法获取轨迹数据
            trajectory_data = self.teaching_manager.get_trajectory_visualization_data(trajectory_name)
            if not trajectory_data:
                return pd.DataFrame()
            
            # 根据参数类型返回不同的数据
            if parameter == "trajectory_original":
                times = trajectory_data.get('original_times', [])
                positions = trajectory_data.get('original_positions', [])
            elif parameter == "trajectory_planned":
                times = trajectory_data.get('planned_times', [])
                positions = trajectory_data.get('planned_positions', [])
            elif parameter == "trajectory_both":  # 兼容 trajectory_both 参数
                # 返回对比数据，包含原始和规划的数据
                original_times = trajectory_data.get('original_times', [])
                original_positions = trajectory_data.get('original_positions', [])
                planned_times = trajectory_data.get('planned_times', [])
                planned_positions = trajectory_data.get('planned_positions', [])
                
                # 创建包含两种数据的DataFrame
                data_list = []
                for i, (t, p) in enumerate(zip(original_times, original_positions)):
                    data_list.append({'time': t, 'value': p, 'type': 'original'})
                for i, (t, p) in enumerate(zip(planned_times, planned_positions)):
                    data_list.append({'time': t, 'value': p, 'type': 'planned'})
                return pd.DataFrame(data_list)
            else:  # trajectory_comparison
                # 返回对比数据，包含原始和规划的数据
                original_times = trajectory_data.get('original_times', [])
                original_positions = trajectory_data.get('original_positions', [])
                planned_times = trajectory_data.get('planned_times', [])
                planned_positions = trajectory_data.get('planned_positions', [])
                
                # 创建包含两种数据的DataFrame
                data_list = []
                for i, (t, p) in enumerate(zip(original_times, original_positions)):
                    data_list.append({'time': t, 'value': p, 'type': 'original'})
                for i, (t, p) in enumerate(zip(planned_times, planned_positions)):
                    data_list.append({'time': t, 'value': p, 'type': 'planned'})
                return pd.DataFrame(data_list)
            
            # 创建DataFrame
            data_list = [{'time': t, 'value': p} for t, p in zip(times, positions)]
            return pd.DataFrame(data_list)

        logging.warning(f"未知的历史数据参数请求: {parameter}")
        return pd.DataFrame()

    def get_trajectory_list(self):
        return self.teaching_manager.get_available_trajectories()

    def start_teaching(self):
        # 清空当前的位置历史数据，以便实时显示示教轨迹
        if 'position' in self.data_buffer:
            self.data_buffer['position'] = pd.DataFrame(columns=['time', 'value'])
            self.logger.info(f"DeepMotor '{self.device_id}': 已为示教清空位置缓冲区。")
        
        # 开始示教前，确保电机失能
        self.command_to_coordinator.emit(self.device_id, "disable_motor", [1])
        return self.teaching_manager.start_teaching(self.device_id)

    def stop_teaching(self, trajectory_name: str) -> bool:
        # 先停止示教
        self.teaching_manager.stop_teaching(self.device_id)
        # 然后保存轨迹
        return self.teaching_manager.save_trajectory(self.device_id, trajectory_name)

    def execute_trajectory(self, trajectory_name: str):
        self.teaching_manager.play_trajectory(self.device_id, trajectory_name)

    @Slot(float, float)
    def _on_trajectory_point_ready(self, position: float, speed: float):
        """
        接收到轨迹播放器发出的点，并将其作为命令发送到协调器。
        """
        self.logger.debug(f"Trajectory point ready: pos={position}, speed={speed}")
        # 通过信号请求 Coordinator 发送底层命令
        # 注意：这里的 "1" 是电机ID，可能需要根据实际情况调整
        self.command_to_coordinator.emit(self.device_id, "set_motor_pos_speed", [1, position, speed])

    def reload_trajectories(self):
        """重新加载所有轨迹"""
        # 轨迹在初始化时已经加载，这里只需要返回当前列表
        return self.get_trajectory_list()