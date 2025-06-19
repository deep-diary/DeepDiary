# src/app_logic/device_logic_manager/devices/deep_motor/deep_motor.py
# DeepMotor 无刷电机相关实现

from typing import Dict, Any, List, Callable, Optional
import copy
import time

from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager
from src.app_logic.device_logic_manager.devices.base_device import BaseDevice
from src.app_logic.device_logic_manager.device_models import DeepMotorState, DeviceStatus
from PySide6.QtCore import QObject, Signal, Slot

class DeepMotor(BaseDevice):
    """
    DeepMotor 无刷电机的逻辑实现。
    管理单个电机的状态和响应特定命令。
    """
    def __init__(self, device_id: str, log_manager: LogManager, config_manager: ConfigManager, parent: Optional[QObject] = None):
        super().__init__(device_id, log_manager, parent)
        self._state: DeepMotorState = DeepMotorState(device_id=device_id) # 使用 DeepMotorState
        
        # 初始化历史记录
        self._history_length = config_manager.get("device_settings.deepmotor_history_length", 100)
        self._state_history: List[Dict[str, Any]] = []
        self.logger.info(f"DeepMotor '{device_id}': 初始化完成，历史记录长度设置为 {self._history_length}。")

    def get_current_state(self) -> DeepMotorState:
        """重写以返回 DeepMotorState。"""
        return self._state

    def get_state_history(self) -> List[Dict[str, Any]]:
        """
        获取状态历史记录。
        :return: 状态历史记录列表，每个元素是一个状态字典。
        """
        return copy.deepcopy(self._state_history)

    def get_state_history_length(self) -> int:
        """
        获取当前历史记录长度。
        :return: 历史记录长度。
        """
        return len(self._state_history)

    def get_field_history(self, field_name: str) -> List[tuple]:
        """
        获取特定字段的历史数据，用于曲线绘制。
        :param field_name: 字段名称，如 'position', 'velocity', 'temperature' 等。
        :return: 包含 (timestamp, value) 元组的列表。
        """
        history_data = []
        for state in self._state_history:
            if field_name in state:
                history_data.append((state.get('timestamp', 0), state[field_name]))
        return history_data

    def get_time_range_history(self, start_time: float, end_time: float) -> List[Dict[str, Any]]:
        """
        获取指定时间范围内的历史记录。
        :param start_time: 开始时间戳。
        :param end_time: 结束时间戳。
        :return: 时间范围内的历史记录列表。
        """
        return [
            state for state in self._state_history
            if start_time <= state.get('timestamp', 0) <= end_time
        ]

    def get_recent_history(self, count: int) -> List[Dict[str, Any]]:
        """
        获取最近的历史记录。
        :param count: 要获取的记录数量。
        :return: 最近的历史记录列表。
        """
        return copy.deepcopy(self._state_history[-count:]) if self._state_history else []

    def clear_history(self):
        """
        清空历史记录。
        """
        self._state_history.clear()
        self.logger.info(f"DeepMotor '{self.device_id}': 历史记录已清空。")

    def set_history_length(self, new_length: int):
        """
        动态设置历史记录长度。
        :param new_length: 新的历史记录长度。
        """
        if new_length < 0:
            self.logger.warning(f"DeepMotor '{self.device_id}': 历史记录长度不能为负数，保持原值 {self._history_length}。")
            return
        
        self._history_length = new_length
        
        # 如果当前历史记录超过新长度，移除多余的记录
        while len(self._state_history) > self._history_length:
            self._state_history.pop(0)
        
        self.logger.info(f"DeepMotor '{self.device_id}': 历史记录长度已设置为 {new_length}。")

    def _add_to_history(self, state_dict: Dict[str, Any]):
        """
        将状态添加到历史记录中。
        :param state_dict: 要添加的状态字典。
        """
        # 添加时间戳
        state_with_timestamp = copy.deepcopy(state_dict)
        state_with_timestamp['timestamp'] = time.time()
        
        self._state_history.append(state_with_timestamp)
        
        # 保持历史记录长度不超过配置的限制
        if len(self._state_history) > self._history_length:
            self._state_history.pop(0)  # 移除最旧的记录

    def update_state_from_semantic_data(self, semantic_data: Dict[str, Any]):
        """
        从业务语义数据更新 DeepMotor 的状态模型。
        :param semantic_data: 语义数据字典，例如包含 motor_rpm, motor_current 等。
        """
        self.logger.debug(f"DeepMotor '{self.device_id}': 收到语义数据更新: {semantic_data}")
        # 调用基类更新通用状态
        super().update_state_from_semantic_data(semantic_data)

        # 更新 DeepMotor 独有的状态
        for key, value in semantic_data.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)
        
        # 将更新后的状态添加到历史记录
        current_state_dict = self._state.to_dict()
        self._add_to_history(current_state_dict)
        
        self.logger.debug(f"DeepMotor '{self.device_id}': 特定状态更新完成，历史记录长度: {len(self._state_history)}。")
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
        清理 DeepMotor 实例占用的资源。
        """
        self.logger.info(f"DeepMotor '{self.device_id}': 清理完成。")
        super().cleanup()