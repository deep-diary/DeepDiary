# DeepToy 玩具控制器相关实现

from typing import Dict, Any, List, Callable, Optional

from src.data_management.log_manager import LogManager
from src.app_logic.device_logic_manager.devices.base_device import BaseDevice
from src.app_logic.device_logic_manager.devices.base_device import DeviceStatus
from .state_model import DeepToyState
from PySide6.QtCore import QObject, Signal, Slot


class DeepToy(BaseDevice):
    """
    DeepToy 玩具控制器的逻辑实现。
    管理玩具控制器的输入输出状态和系统状态。
    """
    def __init__(self, device_id: str, log_manager: LogManager, parent: Optional[QObject] = None):
        super().__init__(device_id, log_manager, parent)
        self._state: DeepToyState = DeepToyState(device_id=device_id)
        self.logger.info(f"DeepToy '{device_id}': 初始化完成。")

    def get_current_state(self) -> DeepToyState:
        """重写以返回 DeepToyState。"""
        return self._state

    def update_state_from_semantic_data(self, semantic_data: Dict[str, Any]):
        """
        从业务语义数据更新 DeepToy 的状态模型。
        :param semantic_data: 语义数据字典，例如包含 digital_inputs, analog_inputs 等。
        """
        self.logger.debug(f"DeepToy '{self.device_id}': 收到语义数据更新: {semantic_data}")
        # 调用基类更新通用状态
        super().update_state_from_semantic_data(semantic_data)

        # 更新 DeepToy 独有的状态
        if 'digital_inputs' in semantic_data:
            self._state.digital_inputs.update(semantic_data['digital_inputs'])
        
        if 'analog_inputs' in semantic_data:
            self._state.analog_inputs.update(semantic_data['analog_inputs'])
        
        if 'digital_outputs' in semantic_data:
            self._state.digital_outputs.update(semantic_data['digital_outputs'])
        
        if 'pwm_outputs' in semantic_data:
            self._state.pwm_outputs.update(semantic_data['pwm_outputs'])
        
        if 'battery_level' in semantic_data:
            self._state.battery_level = float(semantic_data['battery_level'])
        
        if 'battery_voltage' in semantic_data:
            self._state.battery_voltage = float(semantic_data['battery_voltage'])
        
        if 'system_temperature' in semantic_data:
            self._state.system_temperature = float(semantic_data['system_temperature'])
        
        if 'button_states' in semantic_data:
            self._state.button_states.update(semantic_data['button_states'])
        
        if 'wireless_connected' in semantic_data:
            self._state.wireless_connected = bool(semantic_data['wireless_connected'])
        
        if 'signal_strength' in semantic_data:
            self._state.signal_strength = int(semantic_data['signal_strength'])

        self.logger.debug(f"DeepToy '{self.device_id}': 特定状态更新完成。")
        self.device_states_updated.emit(self.device_id, self._state.to_dict())

    def execute_abstract_command(self,
                                 command_name: str,
                                 args: List[Any],
                                 send_request_signal: Callable[[str, str, List[Any]], Any]):
        """
        执行 DeepToy 特定的抽象命令。
        :param command_name: 抽象命令的名称 (如 "set_digital_output", "set_pwm_output")。
        :param args: 命令的参数列表。
        :param send_request_signal: 用于请求 Coordinator 发送底层命令的信号发射器。
        """
        self.logger.info(f"DeepToy '{self.device_id}': 收到命令 '{command_name}' with args {args}")
        
        if command_name == "set_digital_output":
            if len(args) == 2 and isinstance(args[0], int) and isinstance(args[1], bool):
                channel, value = args
                self.logger.debug(f"DeepToy '{self.device_id}': 设置数字输出 {channel} = {value}")
                send_request_signal(self.device_id, "set_digital_output", args)
                self.logger.info(f"DeepToy '{self.device_id}': 已请求设置数字输出。")
            else:
                self.device_error.emit(self.device_id, "set_digital_output 命令需要 (channel: int, value: bool) 参数。")
        
        elif command_name == "set_pwm_output":
            if len(args) == 2 and isinstance(args[0], int) and isinstance(args[1], (int, float)):
                channel, value = args
                if 0.0 <= float(value) <= 1.0:
                    self.logger.debug(f"DeepToy '{self.device_id}': 设置PWM输出 {channel} = {value}")
                    send_request_signal(self.device_id, "set_pwm_output", args)
                    self.logger.info(f"DeepToy '{self.device_id}': 已请求设置PWM输出。")
                else:
                    self.device_error.emit(self.device_id, "PWM值必须在0.0到1.0之间。")
            else:
                self.device_error.emit(self.device_id, "set_pwm_output 命令需要 (channel: int, value: float) 参数。")
        
        elif command_name == "get_toy_status":
            self.logger.info(f"DeepToy '{self.device_id}': 返回当前状态: {self._state.to_dict()}")
        
        elif command_name == "reset_toy":
            self.logger.info(f"DeepToy '{self.device_id}': 请求复位玩具控制器。")
            send_request_signal(self.device_id, "reset_toy", [])
        
        else:
            super().execute_abstract_command(command_name, args, send_request_signal) # 转发到基类处理未知命令

    def get_supported_commands(self) -> List[str]:
        """
        获取 DeepToy 支持的抽象命令列表。
        """
        return super().get_supported_commands() + ["set_digital_output", "set_pwm_output", "get_toy_status", "reset_toy"]

    def check_anomaly(self):
        """
        执行 DeepToy 特定的异常检测。
        """
        super().check_anomaly() # 先执行通用检测

        # 检查电池状态
        if self._state.is_low_battery():
            self.device_error.emit(self.device_id, f"DeepToy '{self.device_id}' 电池电量低 ({self._state.battery_level}%)！")
            self._state.connection_status = DeviceStatus.WARNING

        # 检查温度状态
        if self._state.is_overheating():
            self.device_error.emit(self.device_id, f"DeepToy '{self.device_id}' 系统过热 ({self._state.system_temperature}°C)！")
            self._state.connection_status = DeviceStatus.ERROR

        # 检查无线连接状态
        if not self._state.wireless_connected:
            self.device_error.emit(self.device_id, f"DeepToy '{self.device_id}' 无线连接断开！")
            self._state.connection_status = DeviceStatus.WARNING

        # 检查信号强度
        if self._state.signal_strength < 20:
            self.device_error.emit(self.device_id, f"DeepToy '{self.device_id}' 信号强度弱 ({self._state.signal_strength}%)！")
            self._state.connection_status = DeviceStatus.WARNING

    def cleanup(self):
        """
        清理 DeepToy 实例资源。
        """
        self.logger.info(f"DeepToy '{self.device_id}': 清理完成。")
        super().cleanup()
    
    # === 新增：状态管理接口 ===
    def get_input_states(self) -> Dict[str, Any]:
        """获取输入状态"""
        return self._state.get_input_states()
    
    def get_output_states(self) -> Dict[str, Any]:
        """获取输出状态"""
        return self._state.get_output_states()
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return self._state.get_system_info()
    
    def is_low_battery(self) -> bool:
        """检查是否低电量"""
        return self._state.is_low_battery()
    
    def is_overheating(self) -> bool:
        """检查是否过热"""
        return self._state.is_overheating()
    
    def get_status_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        return self._state.get_status_summary() 