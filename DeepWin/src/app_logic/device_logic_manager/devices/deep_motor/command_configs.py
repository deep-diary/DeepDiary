# src/app_logic/device_logic_manager/devices/deep_motor/command_configs.py
# DeepMotor 命令配置管理

from typing import Dict, Any, List

class DeepMotorCommandConfigs:
    """DeepMotor 命令配置管理类"""
    
    @staticmethod
    def get_command_configs() -> List[Dict[str, Any]]:
        """获取所有命令配置"""
        return [
            # 基础控制命令
            {
                "name": "set_rpm",
                "param_count": 1,
                "param_names": ["rpm"],
                "param_types": [int, float],
                "default_values": [1000],
                "description": "设置电机转速",
                "example": "set_rpm(1500)",
                "validation": lambda args: isinstance(args[0], (int, float)) and args[0] >= 0,
                "error_message": "设置 RPM 命令需要一个非负数字参数。",
                "category": "basic_control"
            },
            {
                "name": "jog_motor",
                "param_count": 2,
                "param_names": ["motor_id", "speed"],
                "param_types": [int, (int, float)],
                "default_values": [1, 0],
                "description": "点动电机",
                "example": "jog_motor(1, 500)",
                "validation": lambda args: isinstance(args[0], int) and isinstance(args[1], (int, float)),
                "error_message": "点动电机命令需要电机ID(整数)和速度(数字)参数。",
                "category": "basic_control"
            },
            {
                "name": "stop_jog_motor",
                "param_count": 1,
                "param_names": ["motor_id"],
                "param_types": [int],
                "default_values": [1],
                "description": "停止点动电机",
                "example": "stop_jog_motor(1)",
                "validation": lambda args: isinstance(args[0], int),
                "error_message": "停止点动电机命令需要电机ID(整数)参数。",
                "category": "basic_control"
            },
            
            # 电机状态控制命令
            {
                "name": "enable_motor",
                "param_count": 1,
                "param_names": ["motor_id"],
                "param_types": [int],
                "default_values": [1],
                "description": "使能电机",
                "example": "enable_motor(1)",
                "validation": lambda args: isinstance(args[0], int),
                "error_message": "使能电机命令需要电机ID(整数)参数。",
                "category": "status_control"
            },
            {
                "name": "disable_motor",
                "param_count": 1,
                "param_names": ["motor_id"],
                "param_types": [int],
                "default_values": [1],
                "description": "失能电机",
                "example": "disable_motor(1)",
                "validation": lambda args: isinstance(args[0], int),
                "error_message": "失能电机命令需要电机ID(整数)参数。",
                "category": "status_control"
            },
            {
                "name": "init_motor",
                "param_count": 1,
                "param_names": ["motor_id"],
                "param_types": [int],
                "default_values": [1],
                "description": "初始化电机",
                "example": "init_motor(1)",
                "validation": lambda args: isinstance(args[0], int),
                "error_message": "初始化电机命令需要电机ID(整数)参数。",
                "category": "status_control"
            },
            {
                "name": "reset_motor",
                "param_count": 1,
                "param_names": ["motor_id"],
                "param_types": [int],
                "default_values": [1],
                "description": "重置电机",
                "example": "reset_motor(1)",
                "validation": lambda args: isinstance(args[0], int),
                "error_message": "重置电机命令需要电机ID(整数)参数。",
                "category": "status_control"
            },
            {
                "name": "zero_motor",
                "param_count": 1,
                "param_names": ["motor_id"],
                "param_types": [int],
                "default_values": [1],
                "description": "零点标定电机",
                "example": "zero_motor(1)",
                "validation": lambda args: isinstance(args[0], int),
                "error_message": "零点标定电机命令需要电机ID(整数)参数。",
                "category": "status_control"
            },
            
            # 位置控制命令
            {
                "name": "set_motor_mode",
                "param_count": 2,
                "param_names": ["motor_id", "mode"],
                "param_types": [int, str],
                "default_values": [1, "position"],
                "description": "设置电机模式",
                "example": "set_motor_mode(1, 'position')",
                "validation": lambda args: isinstance(args[0], int) and isinstance(args[1], str),
                "error_message": "设置电机模式命令需要电机ID(整数)和模式(字符串)参数。",
                "category": "position_control"
            },
            {
                "name": "set_motor_position",
                "param_count": 2,
                "param_names": ["motor_id", "position"],
                "param_types": [int, (int, float)],
                "default_values": [1, 0.0],
                "description": "设置电机位置",
                "example": "set_motor_position(1, 90.0)",
                "validation": lambda args: isinstance(args[0], int) and isinstance(args[1], (int, float)),
                "error_message": "设置电机位置命令需要电机ID(整数)和位置(数字)参数。",
                "category": "position_control"
            },
            {
                "name": "set_motor_pos_speed",
                "param_count": 3,
                "param_names": ["motor_id", "position", "speed"],
                "param_types": [int, (int, float), (int, float)],
                "default_values": [1, 0.0, 100.0],
                "description": "设置电机位置和速度",
                "example": "set_motor_pos_speed(1, 90.0, 200.0)",
                "validation": lambda args: (isinstance(args[0], int) and 
                                          isinstance(args[1], (int, float)) and 
                                          isinstance(args[2], (int, float))),
                "error_message": "设置电机位置和速度命令需要电机ID(整数)、位置(数字)和速度(数字)参数。",
                "category": "position_control"
            }
        ]
    
    @staticmethod
    def get_commands_by_category() -> Dict[str, List[Dict[str, Any]]]:
        """按类别获取命令配置"""
        configs = DeepMotorCommandConfigs.get_command_configs()
        categorized = {}
        for config in configs:
            category = config.get("category", "other")
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(config)
        return categorized
    
    @staticmethod
    def get_command_names() -> List[str]:
        """获取所有命令名称"""
        configs = DeepMotorCommandConfigs.get_command_configs()
        return [config["name"] for config in configs]
    
    @staticmethod
    def get_command_help_by_category() -> Dict[str, Dict[str, Any]]:
        """按类别获取命令帮助信息"""
        categorized = DeepMotorCommandConfigs.get_commands_by_category()
        help_info = {}
        
        for category, configs in categorized.items():
            help_info[category] = {}
            for config in configs:
                help_info[category][config["name"]] = {
                    "description": config["description"],
                    "example": config["example"],
                    "param_names": config["param_names"],
                    "param_count": config["param_count"]
                }
        
        return help_info 