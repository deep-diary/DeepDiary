from .command_model import *
from typing import List

class CommandDescription:
    """DeepMotor 命令描述"""
    commands = [
        {
            "name": "motor_set_speed",
            "model": MotorSetSpeedCommand,
            "description": "设置电机转速",
            "example": "motor_set_speed(1, 1.5)",
            "category": "DeepMotor",
            "voice_prompt": [
                "设置电机转速为1.5",
                "设置电机转速为1.5弧度每秒"
            ]
        },
        {
            "name": "motor_jog",
            "model": MotorJogCommand,
            "description": "点动电机",
            "example": "motor_jog(1, 1.5)",
            "category": "DeepMotor",
            "voice_prompt": [
                "电机正转",
                "电机正转1.5弧度每秒"
            ]
        },
        {
            "name": "motor_jog_stop",
            "model": MotorJogStopCommand,
            "description": "停止点动电机",
            "example": "motor_jog_stop(1)",
            "category": "DeepMotor",
            "voice_prompt": [
                "电机停止"
            ]
        },
        {
            "name": "motor_enable",
            "model": MotorEnableCommand,
            "description": "使能电机",
            "example": "motor_enable(1)",
            "category": "DeepMotor",
            "voice_prompt": [
                "使能电机",
                "激活电机"
            ]
        },
        {
            "name": "motor_disable",
            "model": MotorDisableCommand,
            "description": "失能电机",
            "example": "motor_disable(1)",
            "category": "DeepMotor",
            "voice_prompt": [
                "失能电机",
                "关闭电机"
            ]
        },
        {
            "name": "motor_init",
            "model": MotorInitCommand,
            "description": "初始化电机",
            "example": "motor_init(1)",
            "category": "DeepMotor",
            "voice_prompt": [
                "初始化电机"
            ]
        },
        {
            "name": "motor_reset",
            "model": MotorResetCommand,
            "description": "重置电机",
            "example": "motor_reset(1)",
            "category": "DeepMotor",
            "voice_prompt": [
                "重置电机"
            ]
        },
        {
            "name": "motor_zero",
            "model": MotorZeroCommand,
            "description": "零点标定电机",
            "example": "motor_zero(1)",
            "category": "DeepMotor",
            "voice_prompt": [
                "零点标定电机",
                "设置零位"
            ]
        },
        {
            "name": "motor_set_mode",
            "model": MotorSetModeCommand,
            "description": "设置电机模式",
            "example": "motor_set_mode(1, 'position')",
            "category": "DeepMotor",
            "voice_prompt": [
                "设置电机模式为位置",
                "将电机设置为位置模式"
            ]
        },
        {
            "name": "motor_set_pos_speed",
            "model": MotorSetPosSpeedCommand,   
            "description": "设置电机位置和速度",
            "example": "motor_set_pos_speed(1, 1.0, 1.5)",
            "category": "DeepMotor",
            "voice_prompt": [
                "以1.5弧度每秒的速度移动电机到1.0弧度",
                "以1.5的速度移动电机到1.0度"
            ]
        },
        {
            "name": "motor_set_pos",
            "model": MotorSetPosCommand,
            "description": "设置电机位置",
            "example": "motor_set_pos(1, 1.0)",
            "category": "DeepMotor",
            "voice_prompt": [
                "设置电机位置为1.0弧度",
                "设置电机位调1.0度"
            ]
        },
        {
            "name": "motor_decrease_pos_default",
            "model": MotorDecreasePosDefaultCommand,
            "description": "电机位置减小默认值",
            "example": "motor_decrease_pos_default(1)",
            "category": "DeepMotor",
            "voice_prompt": [
                "电机位置减小默认值",
                "电机位置调小些"
            ]
        },
        {
            "name": "motor_increase_pos_default",   
            "model": MotorIncreasePosDefaultCommand,
            "description": "电机位置增大默认值",
            "example": "motor_increase_pos_default(1)",
            "category": "DeepMotor",
            "voice_prompt": [
                "电机位置增大默认值",
                "电机位置调大些"
            ]
        },
        {
            "name": "motor_increase_pos",
            "model": MotorIncreasePosCommand,
            "description": "电机位置增大",
            "example": "motor_increase_pos(1, 1.5)",
            "category": "DeepMotor",
            "voice_prompt": [
                "电机位置调大1.0度",
                "电机位置增大1.5弧度"
            ]
        },
        {
            "name": "motor_decrease_pos",
            "model": MotorDecreasePosCommand,
            "description": "电机位置减小",
            "example": "motor_decrease_pos(1, 1.5)",
            "category": "DeepMotor",
            "voice_prompt": [
                "电机位置调小1.0度",
                "电机位置减小1.5弧度"
            ]
        },
        {
            "name": "motor_write",
            "model": MotorWriteCommand,
            "description": "电机写入",
            "example": "motor_write(1, 0x7016, 0.0)",
            "category": "DeepMotor",
            "voice_prompt": [
                "将电机位置写入0.0度",
                "将电机位置写入0.0弧度"
            ]
        },
        {
            "name": "motor_read",
            "model": MotorReadCommand,
            "description": "电机读取",
            "example": "motor_read(1, 0x7016)",
            "category": "DeepMotor",
            "voice_prompt": [
                "读取电机位置",
                "读取电机位置0.0度"
            ]
        },
        {
            "name": "motor_read_all",
            "model": MotorReadAllCommand,
            "description": "电机读取所有",
            "example": "motor_read_all(1)",
            "category": "DeepMotor",
            "voice_prompt": [
                "读取电机所有参数"
            ]
        },
        {
            "name": "motor_read_sig_disp",
            "model": MotorReadSigDispCommand,
            "description": "电机读取信号示波器模式显示",
            "example": "motor_read_sig_disp(1, 0x7016, 50)",
            "category": "DeepMotor",
            "voice_prompt": [
                "电机电流波形按50HZ返回"
            ]
        }
    ]
