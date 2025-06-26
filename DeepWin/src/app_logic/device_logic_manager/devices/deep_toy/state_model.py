# src/app_logic/device_logic_manager/devices/deep_toy/state_model.py
# DeepToy 状态模型定义

from dataclasses import dataclass, field
from typing import Dict, Any
from src.app_logic.device_logic_manager.devices.base_device import BaseDeviceState

@dataclass
class DeepToyState(BaseDeviceState):
    """DeepToy 玩具控制器状态模型。"""
    # 输入状态
    digital_inputs: Dict[int, bool] = field(default_factory=dict)  # 数字输入状态，如 {0: True, 1: False}
    analog_inputs: Dict[int, float] = field(default_factory=dict)  # 模拟输入值
    
    # 输出状态
    digital_outputs: Dict[int, bool] = field(default_factory=dict)  # 数字输出状态
    pwm_outputs: Dict[int, float] = field(default_factory=dict)     # PWM输出值 (0.0-1.0)
    
    # 系统状态
    battery_level: float = 0.0  # 电池电量百分比
    battery_voltage: float = 0.0  # 电池电压
    system_temperature: float = 0.0  # 系统温度
    
    # 按键状态
    button_states: Dict[str, bool] = field(default_factory=dict)  # 按键状态，如 {"A": True, "B": False}
    
    # 通信状态
    wireless_connected: bool = False
    signal_strength: int = 0  # 信号强度 (0-100)

    def to_dict(self) -> Dict[str, Any]:
        """将设备状态转换为字典，便于传输或日志记录。"""
        base_dict = super().to_dict()
        base_dict.update({
            "digital_inputs": self.digital_inputs,
            "analog_inputs": self.analog_inputs,
            "digital_outputs": self.digital_outputs,
            "pwm_outputs": self.pwm_outputs,
            "battery_level": self.battery_level,
            "battery_voltage": self.battery_voltage,
            "system_temperature": self.system_temperature,
            "button_states": self.button_states,
            "wireless_connected": self.wireless_connected,
            "signal_strength": self.signal_strength
        })
        return base_dict
    
    def get_input_states(self) -> Dict[str, Any]:
        """获取输入状态"""
        return {
            "digital_inputs": self.digital_inputs,
            "analog_inputs": self.analog_inputs,
            "button_states": self.button_states
        }
    
    def get_output_states(self) -> Dict[str, Any]:
        """获取输出状态"""
        return {
            "digital_outputs": self.digital_outputs,
            "pwm_outputs": self.pwm_outputs
        }
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        return {
            "battery_level": self.battery_level,
            "battery_voltage": self.battery_voltage,
            "system_temperature": self.system_temperature,
            "wireless_connected": self.wireless_connected,
            "signal_strength": self.signal_strength
        }
    
    def is_low_battery(self) -> bool:
        """检查是否低电量"""
        return self.battery_level < 20.0
    
    def is_overheating(self) -> bool:
        """检查是否过热"""
        return self.system_temperature > 60.0
    
    def get_status_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        return {
            "device_id": self.device_id,
            "connection_status": self.connection_status.value,
            "is_online": self.is_online,
            "battery_level": self.battery_level,
            "wireless_connected": self.wireless_connected,
            "signal_strength": self.signal_strength,
            "is_low_battery": self.is_low_battery(),
            "is_overheating": self.is_overheating(),
            "input_count": len(self.digital_inputs) + len(self.analog_inputs),
            "output_count": len(self.digital_outputs) + len(self.pwm_outputs)
        } 