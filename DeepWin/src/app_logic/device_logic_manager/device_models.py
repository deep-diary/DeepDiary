# src/app_logic/device_logic_manager/device_models.py
# 定义设备状态数据模型

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
import time
from enum import Enum

class DeviceStatus(Enum):
    """设备连接和运行状态的枚举。"""
    DISCONNECTED = "Disconnected"
    CONNECTED = "Connected"
    IDLE = "Idle"
    WORKING = "Working"
    ERROR = "Error"
    WARNING = "Warning"
    TEACHING = "Teaching"
    PLAYING = "Playing"

@dataclass
class BaseDeviceState:
    """所有设备状态的基类。"""
    device_id: str
    connection_status: DeviceStatus = DeviceStatus.DISCONNECTED
    last_active_time: float = field(default_factory=time.time)
    firmware_version: str = "Unknown"
    is_online: bool = False # 简化判断，实际可基于 connection_status

    def to_dict(self) -> Dict[str, Any]:
        """将设备状态转换为字典，便于传输或日志记录。"""
        # 注意：枚举类型需要转换为其值，否则无法序列化
        return {
            "device_id": self.device_id,
            "connection_status": self.connection_status.value,
            "last_active_time": self.last_active_time,
            "firmware_version": self.firmware_version,
            "is_online": self.is_online
        }

    def update_from_dict(self, data: Dict[str, Any]):
        """从字典更新设备状态。"""
        for key, value in data.items():
            if hasattr(self, key):
                # 尝试转换枚举
                if key == "connection_status" and isinstance(value, str):
                    try:
                        self.connection_status = DeviceStatus(value)
                    except ValueError:
                        pass # 保持原值或记录错误
                else:
                    setattr(self, key, value)
        self.last_active_time = time.time() # 任何更新都视为活跃


@dataclass
class DeepMotorState(BaseDeviceState):
    """DeepMotor 无刷电机状态模型。"""
    motor_rpm: int = 0
    motor_current: float = 0.0
    motor_temperature: float = 0.0
    error_code: int = 0
    # 可以添加更多电机特定的状态，如 PWM 值，编码器读数等

    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "motor_rpm": self.motor_rpm,
            "motor_current": self.motor_current,
            "motor_temperature": self.motor_temperature,
            "error_code": self.error_code
        })
        return base_dict

@dataclass
class DeepArmState(BaseDeviceState):
    """DeepArm 机械臂状态模型。"""
    # 假设 DeepArm 有 6 个关节，可以存储它们的角度
    joint1_angle: float = 0.0
    joint2_angle: float = 0.0
    joint3_angle: float = 0.0
    joint4_angle: float = 0.0
    joint5_angle: float = 0.0
    joint6_angle: float = 0.0
    # 末端执行器坐标
    end_effector_x: float = 0.0
    end_effector_y: float = 0.0
    end_effector_z: float = 0.0
    # 机械臂温度 (可以从某个DeepMotor汇总)
    temperature: float = 0.0
    current_status: int = 0 # 示例：0=OK, 1=Warning, 2=Error

    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "joint1_angle": self.joint1_angle,
            "joint2_angle": self.joint2_angle,
            "joint3_angle": self.joint3_angle,
            "joint4_angle": self.joint4_angle,
            "joint5_angle": self.joint5_angle,
            "joint6_angle": self.joint6_angle,
            "end_effector_x": self.end_effector_x,
            "end_effector_y": self.end_effector_y,
            "end_effector_z": self.end_effector_z,
            "temperature": self.temperature,
            "current_status": self.current_status
        })
        return base_dict

    def get_current_joint_angles(self) -> List[float]:
        """获取当前所有关节的角度列表。"""
        return [
            self.joint1_angle, self.joint2_angle, self.joint3_angle,
            self.joint4_angle, self.joint5_angle, self.joint6_angle
        ]

@dataclass
class DeepToyState(BaseDeviceState):
    """DeepToy 玩具控制器状态模型。"""
    digital_inputs: Dict[int, bool] = field(default_factory=dict) # 数字输入状态，如 {0: True, 1: False}
    analog_inputs: Dict[int, float] = field(default_factory=dict) # 模拟输入值
    battery_level: float = 0.0 # 电池电量百分比
    # 可以添加更多玩具控制器特定的状态，如按键状态，PWM 输出状态等

    def to_dict(self) -> Dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            "digital_inputs": self.digital_inputs,
            "analog_inputs": self.analog_inputs,
            "battery_level": self.battery_level
        })
        return base_dict