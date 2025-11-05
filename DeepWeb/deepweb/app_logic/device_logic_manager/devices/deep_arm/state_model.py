# src/app_logic/device_logic_manager/devices/deep_arm/state_model.py
# DeepArm 状态模型定义

from dataclasses import dataclass
from typing import Dict, Any, List
from deepweb.app_logic.device_logic_manager.devices.base_device import BaseDeviceState

@dataclass
class DeepArmState(BaseDeviceState):
    """DeepArm 机械臂状态模型。"""
    # 关节角度 (6个关节)
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
    
    # 状态参数
    temperature: float = 0.0
    current_status: int = 0  # 0=OK, 1=Warning, 2=Error
    
    # 关节状态
    joint_velocities: List[float] = None  # 关节速度
    joint_torques: List[float] = None     # 关节扭矩
    
    # 安全状态
    emergency_stop: bool = False
    collision_detected: bool = False
    workspace_limit_reached: bool = False

    def __post_init__(self):
        """初始化后处理"""
        if self.joint_velocities is None:
            self.joint_velocities = [0.0] * 6
        if self.joint_torques is None:
            self.joint_torques = [0.0] * 6

    def to_dict(self) -> Dict[str, Any]:
        """将设备状态转换为字典，便于传输或日志记录。"""
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
            "current_status": self.current_status,
            "joint_velocities": self.joint_velocities,
            "joint_torques": self.joint_torques,
            "emergency_stop": self.emergency_stop,
            "collision_detected": self.collision_detected,
            "workspace_limit_reached": self.workspace_limit_reached
        })
        return base_dict

    def get_current_joint_angles(self) -> List[float]:
        """获取当前所有关节的角度列表。"""
        return [
            self.joint1_angle, self.joint2_angle, self.joint3_angle,
            self.joint4_angle, self.joint5_angle, self.joint6_angle
        ]
    
    def get_end_effector_position(self) -> Dict[str, float]:
        """获取末端执行器位置"""
        return {
            "x": self.end_effector_x,
            "y": self.end_effector_y,
            "z": self.end_effector_z
        }
    
    def get_joint_states(self) -> Dict[str, List[float]]:
        """获取关节状态"""
        return {
            "angles": self.get_current_joint_angles(),
            "velocities": self.joint_velocities,
            "torques": self.joint_torques
        }
    
    def has_safety_issues(self) -> bool:
        """检查是否有安全问题"""
        return (self.emergency_stop or 
                self.collision_detected or 
                self.workspace_limit_reached)
    
    def get_status_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        return {
            "device_id": self.device_id,
            "connection_status": self.connection_status.value,
            "is_online": self.is_online,
            "current_status": self.current_status,
            "end_effector_position": self.get_end_effector_position(),
            "has_safety_issues": self.has_safety_issues(),
            "temperature": self.temperature
        } 