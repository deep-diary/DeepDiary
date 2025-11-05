# src/app_logic/device_logic_manager/devices/deep_motor/state_model.py
# DeepMotor 状态模型定义

from dataclasses import dataclass
from typing import Dict, Any
from deepweb.app_logic.device_logic_manager.devices.base_device import BaseDeviceState

@dataclass
class DeepMotorState(BaseDeviceState):
    """DeepMotor 无刷电机状态模型。"""
    # 基础运动参数
    position: float = 0.0
    velocity: float = 0.0
    torque: float = 0.0
    
    # 状态参数
    temperature: float = 0.0
    error_code: int = 0
    error_message: str = ""
    response_mode: str = ""
    motor_can_id: int = 0
    mode_state: str = ""
    
    # 故障标志
    flt_uninitialized: bool = False
    flt_hall_encoding: bool = False
    flt_magnetic_encoding: bool = False
    flt_over_temperature: bool = False
    flt_over_current: bool = False
    flt_voltage_drop: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """将设备状态转换为字典，便于传输或日志记录。"""
        base_dict = super().to_dict()
        base_dict.update({
            "position": self.position,
            "velocity": self.velocity,
            "torque": self.torque,
            "temperature": self.temperature,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "response_mode": self.response_mode,
            "motor_can_id": self.motor_can_id,
            "mode_state": self.mode_state,
            "flt_uninitialized": self.flt_uninitialized,
            "flt_hall_encoding": self.flt_hall_encoding,
            "flt_magnetic_encoding": self.flt_magnetic_encoding,
            "flt_over_temperature": self.flt_over_temperature,
            "flt_over_current": self.flt_over_current,
            "flt_voltage_drop": self.flt_voltage_drop
        })
        return base_dict
    
    def get_motion_state(self) -> Dict[str, float]:
        """获取运动状态参数"""
        return {
            "position": self.position,
            "velocity": self.velocity,
            "torque": self.torque
        }
    
    def get_fault_flags(self) -> Dict[str, bool]:
        """获取故障标志状态"""
        return {
            "flt_uninitialized": self.flt_uninitialized,
            "flt_hall_encoding": self.flt_hall_encoding,
            "flt_magnetic_encoding": self.flt_magnetic_encoding,
            "flt_over_temperature": self.flt_over_temperature,
            "flt_over_current": self.flt_over_current,
            "flt_voltage_drop": self.flt_voltage_drop
        }
    
    def has_faults(self) -> bool:
        """检查是否有故障"""
        fault_flags = self.get_fault_flags()
        return any(fault_flags.values()) or self.error_code != 0
    
    def get_status_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        return {
            "device_id": self.device_id,
            "connection_status": self.connection_status.value,
            "is_online": self.is_online,
            "position": self.position,
            "velocity": self.velocity,
            "temperature": self.temperature,
            "error_code": self.error_code,
            "has_faults": self.has_faults(),
            "mode_state": self.mode_state
        } 