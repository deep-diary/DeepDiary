# src/app_logic/device_logic_manager/devices/deep_motor/command_model.py
# DeepMotor 命令模型定义 - 使用 Pydantic

from pydantic import BaseModel, Field, validator
from typing import Optional, Union, List
from enum import Enum

DEFAULT_MOTOR_ID = 255

class MotorMode(str, Enum):
    """电机模式枚举"""
    POSITION = "position"
    VELOCITY = "velocity"
    TORQUE = "torque"
    MIT = "mit"

# 基础电机命令类
class MotorSetSpeedCommand(BaseModel):
    """设置电机转速命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID，默认为1",
        example=1
    )
    spd: float = Field(
        default=1.5, 
        ge=0, 
        le=50, 
        description="电机转速，单位：rad/s",
        example=1.5
    )
    
    @validator('spd')
    def validate_spd(cls, v):
        if v > 50:
            raise ValueError('转速过高，可能损坏电机')
        return v

class MotorJogCommand(BaseModel):
    """点动电机命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )
    spd: float = Field(
        default=1.5, 
        description="点动速度，单位：rad/s",
        example=1.5
    )

class MotorJogStopCommand(BaseModel):
    """停止点动电机命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )

class MotorEnableCommand(BaseModel):
    """使能电机命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )

class MotorDisableCommand(BaseModel):
    """失能电机命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )

class MotorInitCommand(BaseModel):
    """初始化电机命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )

class MotorResetCommand(BaseModel):
    """重置电机命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )

class MotorZeroCommand(BaseModel):
    """零点标定电机命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )

class MotorSetModeCommand(BaseModel):
    """设置电机模式命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )
    mode: MotorMode = Field(
        default=MotorMode.POSITION, 
        description="电机运行模式",
        example="position"
    )

class MotorSetPosSpeedCommand(BaseModel):
    """设置电机位置和速度命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )
    position: float = Field(
        default=1.0, 
        description="目标位置，单位：弧度",
        example=1.0
    )
    speed: float = Field(
        default=2.0, 
        gt=0, 
        le=20,
        description="运动速度，单位：弧度/秒",
        example=2.0
    )

class MotorSetPosCommand(BaseModel):
    """设置电机位置命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )
    position: float = Field(
        default=1.0, 
        description="目标位置，单位：弧度",
        example=1.0
    )

class MotorDecreasePosDefaultCommand(BaseModel):
    """电机位置减小默认值命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )

class MotorIncreasePosDefaultCommand(BaseModel):
    """电机位置增大默认值命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )

class MotorIncreasePosCommand(BaseModel):
    """电机位置增大命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )
    pos: float = Field(
        default=1.5, 
        description="位置增量，单位：弧度",
        example=1.5
    )

class MotorDecreasePosCommand(BaseModel):
    """电机位置减小命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )
    pos: float = Field(
        default=1.5, 
        description="位置减量，单位：弧度",
        example=1.5
    )

class MotorWriteCommand(BaseModel):
    """电机写入命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )
    param_id: int = Field(
        default=7016, 
        ge=0, 
        description="位置参数ID",
        example=7016
    )
    data: float = Field(
        default=0.0, 
        description="写入数据",
        example=0.0
    )

class MotorReadCommand(BaseModel):
    """电机读取命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )
    param_id: int = Field(
        default=7016, 
        ge=0, 
        description="位置参数ID",
        example=7016
    )

class MotorReadAllCommand(BaseModel):
    """电机读取所有命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )

class MotorReadSigDispCommand(BaseModel):
    """电机读取信号示波器模式显示命令"""
    motor_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="电机ID",
        example=1
    )
    sig_id: int = Field(
        default=DEFAULT_MOTOR_ID, 
        ge=1, 
        description="信号ID",
        example=1
    )
    freq: int = Field(
        default=50, 
        ge=1, 
        le=100,
        description="频率，单位：Hz",
        example=50
    )


   