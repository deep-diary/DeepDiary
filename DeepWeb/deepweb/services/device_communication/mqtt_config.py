"""
MQTT配置文件
定义常用的MQTT连接配置和主题配置
根据 mqtt_protocol.json 协议定义生成
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

# MQTT服务器配置
MQTT_SERVERS = {
    "default": {
        "host": "34.172.161.212",
        "port": 1883,
        "username": None,
        "password": None,
        "keepalive": 60,
        "auto_reconnect": True,
        "reconnect_interval": 5,
        # 注意：自动订阅的主题现在直接从 TOPIC_CONFIGS 列表读取，不需要在这里配置
    },
}

# 协议版本
PROTOCOL_VERSION = "1.0.0"

# 主题配置模板（根据 mqtt_protocol.json）
TOPIC_TEMPLATES = {
    "device": {
        "info": "device/{client_id}/info",      # 设备固定配置信息
        "status": "device/{client_id}/status",  # 设备动态状态信息
        "control": "device/{client_id}/control" # 远程控制命令
    }
}

# 主题详细配置（根据 mqtt_protocol.json）- 列表格式，可直接遍历使用
TOPIC_CONFIGS = [
    {
        "key": "test",
        "name": "test/hello",
        "description": "测试主题",
        "period_ms": 0,
        "qos": 0,
        "retained": False,
        "direction": "pub"
    },
    {
        "key": "device_info",
        "name": "device/{client_id}/info",
        "description": "设备固定配置信息",
        "period_ms": 60000,
        "qos": 1,
        "retained": False,
        "direction": "pub"  # 设备发布
    },
    {
        "key": "device_status",
        "name": "device/{client_id}/status",
        "description": "设备动态状态信息",
        "period_ms": 10000,
        "qos": 0,
        "retained": False,
        "direction": "pub"  # 设备发布
    },
    # 平铺的二级状态主题（便于直接订阅具体类别）
    {
        "key": "device_status_system",
        "name": "device/{client_id}/status/system",
        "description": "系统动态信息",
        "period_ms": 10000,
        "qos": 0,
        "retained": False,
        "direction": "pub"
    },
    {
        "key": "device_status_sensor",
        "name": "device/{client_id}/status/sensor",
        "description": "传感器数据",
        "period_ms": 1000,
        "qos": 0,
        "retained": False,
        "direction": "pub"
    },
    {
        "key": "device_status_actuator",
        "name": "device/{client_id}/status/actuator",
        "description": "执行器状态",
        "period_ms": 5000,
        "qos": 0,
        "retained": False,
        "direction": "pub"
    },
    {
        "key": "control",
        "name": "device/{client_id}/control",
        "description": "远程控制命令",
        "period_ms": 0,  # 事件驱动，无周期性
        "qos": 1,
        "retained": False,
        "direction": "sub"  # 设备订阅
    }
]

# 消息类型定义（按主题平铺）
MESSAGE_TYPES = {
    "test": {
        "topic_template": "test/hello",
        "fields": {
            "message": {"type": "string", "description": "消息"}
        }
    },
    "device_info": {
        "topic_template": "device/{client_id}/info",
        "fields": {
            "device_id": {"type": "string", "required": True, "description": "设备唯一ID"},
            "device_type": {"type": "string", "required": True, "description": "设备类型"},
            "firmware_version": {"type": "string", "required": True, "description": "固件版本"},
            "mac_address": {"type": "string", "required": True, "description": "MAC地址"},
            "chip_model": {"type": "string", "required": True, "description": "芯片型号"},
            "chip_revision": {"type": "string", "required": True, "description": "芯片版本"},
            "hardware_capabilities": {
                "type": "object",
                "required": True,
                "description": "硬件能力",
                "fields": {
                    "camera": {"type": "boolean", "description": "摄像头"},
                    "can_bus": {"type": "boolean", "description": "CAN总线"},
                    "led_strip": {"type": "boolean", "description": "LED灯带"},
                    "gimbal": {"type": "boolean", "description": "云台"},
                    "arm": {"type": "boolean", "description": "机械臂"},
                    "motor": {"type": "boolean", "description": "电机"},
                    "sensor": {"type": "boolean", "description": "传感器"}
                }
            }
        }
    },
    "device_status": {
        "topic_template": "device/{client_id}/status",
        "fields": {}
    },
    "device_status_system": {
        "topic_template": "device/{client_id}/status/system",
        "fields": {
            "wifi_ssid": {"type": "string", "description": "WiFi名称"},
            "ip_address": {"type": "string", "description": "IP地址"},
            "free_heap": {"type": "integer", "description": "可用堆内存(字节)"},
            "uptime_seconds": {"type": "integer", "description": "运行时间(秒)"},
            "cpu_temperature": {"type": "float", "description": "CPU温度"},
            "network_status": {"type": "string", "description": "网络状态"}
        }
    },
    "device_status_sensor": {
        "topic_template": "device/{client_id}/status/sensor",
        "fields": {
            "acc_x": {"type": "float", "description": "X轴加速度(m/s²)"},
            "acc_y": {"type": "float", "description": "Y轴加速度(m/s²)"},
            "acc_z": {"type": "float", "description": "Z轴加速度(m/s²)"},
            "acc_g": {"type": "float", "description": "总加速度(m/s²)"},
            "pitch": {"type": "float", "description": "俯仰角(度)"},
            "roll": {"type": "float", "description": "翻滚角(度)"},
            "sensor_status": {"type": "string", "description": "传感器状态"}
        }
    },
    "device_status_actuator": {
        "topic_template": "device/{client_id}/status/actuator",
        "fields": {
            "arm": {
                "type": "object",
                "fields": {
                    "connected": {"type": "boolean", "description": "是否连接"},
                    "motor_count": {"type": "integer", "description": "电机数量"},
                    "status": {"type": "string", "description": "状态"}
                }
            },
            "motor": {
                "type": "object",
                "fields": {
                    "connected": {"type": "boolean", "description": "是否连接"},
                    "motor_count": {"type": "integer", "description": "电机数量"},
                    "status": {"type": "string", "description": "状态"}
                }
            }
        }
    },
    "control": {
        "topic_template": "device/{client_id}/control",
        "fields": {
            "type": {"type": "string", "description": "命令类型"},
            "target": {"type": "string", "description": "目标设备"},
            "action": {"type": "string", "description": "动作"},
            "parameters": {"type": "object", "description": "参数"}
        }
    }
}
# 命令类型枚举
CONTROL_TYPES = {
    "ping": "ping",
    "echo": "echo",
    "control": "control"
}
# 动作类型枚举
ACTION_TYPES = {
    "start": "start",
    "stop": "stop",
    "restart": "restart",
    "reboot": "reboot",
    "factory_reset": "factory_reset",
    "update": "update",
    "config": "config"
}
#目标设备枚举
TARGET_DEVICES = {
    "deepTumbler": "deepTumbler",
    "deepMotor": "deepMotor",
    "deepArm": "deepArm",
}

# QoS级别定义
QOS_LEVELS = {
    "AT_MOST_ONCE": 0,      # 最多一次
    "AT_LEAST_ONCE": 1,     # 至少一次
    "EXACTLY_ONCE": 2       # 恰好一次
}

# 常用主题模式（基于协议定义）
COMMON_PATTERNS = {
    "all_device_info": "device/+/info",        # 订阅所有设备信息
    "all_device_status": "device/+/status",    # 订阅所有设备状态（汇总）
    "all_device_status_system": "device/+/status/system",   # 订阅所有设备系统状态
    "all_device_status_sensor": "device/+/status/sensor",   # 订阅所有设备传感器状态
    "all_device_status_actuator": "device/+/status/actuator", # 订阅所有设备执行器状态
    "all_device_control": "device/+/control", # 订阅所有设备控制（通常用于监控）
    "specific_device_info": "device/{client_id}/info",
    "specific_device_status": "device/{client_id}/status",
    "specific_device_status_system": "device/{client_id}/status/system",
    "specific_device_status_sensor": "device/{client_id}/status/sensor",
    "specific_device_status_actuator": "device/{client_id}/status/actuator",
    "specific_device_control": "device/{client_id}/control"
}


# def get_server_config(server_name: str = "default") -> Dict[str, Any]:
#     """
#     获取MQTT服务器配置
    
#     Args:
#         server_name: 服务器配置名称
        
#     Returns:
#         Dict: 服务器配置字典
#     """
#     return MQTT_SERVERS.get(server_name, MQTT_SERVERS["default"]).copy()


# def get_topic_template(category: str, topic_type: str) -> str:
#     """
#     获取主题模板
    
#     Args:
#         category: 主题分类 (device)
#         topic_type: 主题类型 (info, status, control)
        
#     Returns:
#         str: 主题模板字符串
#     """
#     return TOPIC_TEMPLATES.get(category, {}).get(topic_type, "")


# def get_topic_config(topic_key: str) -> Dict[str, Any]:
#     """
#     获取主题详细配置（包含 QoS、周期等信息）
    
#     Args:
#         topic_key: 主题键名 (device_info, device_status, control)
        
#     Returns:
#         Dict: 主题配置字典
#     """
#     return TOPIC_CONFIGS.get(topic_key, {}).copy()


# def format_topic_from_config(topic_key: str, client_id: str) -> str:
#     """
#     根据主题配置键名和 client_id 格式化主题
    
#     Args:
#         topic_key: 主题配置键名 (device_info, device_status, control)
#         client_id: 客户端ID（设备ID）
        
#     Returns:
#         str: 格式化后的主题字符串
#     """
#     config = get_topic_config(topic_key)
#     template = config.get("name", "")
#     return template.format(client_id=client_id) if template else ""


# def format_topic(template: str, **kwargs) -> str:
#     """
#     格式化主题字符串
    
#     Args:
#         template: 主题模板
#         **kwargs: 模板参数
        
#     Returns:
#         str: 格式化后的主题字符串
#     """
#     return template.format(**kwargs)


# def get_message_schema(message_type: str) -> Dict[str, Any]:
#     """
#     获取消息类型的数据结构定义
    
#     Args:
#         message_type: 消息类型名称 (device_info, device_status, control)
        
#     Returns:
#         Dict: 消息结构定义（包含 fields 或 categories）
#     """
#     return MESSAGE_TYPES.get(message_type, {}).copy()


# def get_status_category_schema(message_type: str, category: str) -> Dict[str, Any]:
#     """
#     获取 device_status 消息中特定分类的字段定义
    
#     Args:
#         message_type: 消息类型（通常是 "device_status"）
#         category: 分类名称 (system, sensor, actuator)
        
#     Returns:
#         Dict: 分类的字段定义
#     """
#     if message_type != "device_status":
#         return {}
#     schema = MESSAGE_TYPES.get(message_type, {})
#     return schema.get("categories", {}).get(category, {})


# def load_protocol_json() -> Optional[Dict[str, Any]]:
#     """
#     加载 mqtt_protocol.json 文件
    
#     Returns:
#         Dict: 协议定义字典，如果文件不存在返回 None
#     """
#     protocol_file = Path(__file__).parent / "mqtt_protocol.json"
#     if not protocol_file.exists():
#         return None
#     try:
#         with open(protocol_file, 'r', encoding='utf-8') as f:
#             return json.load(f)
#     except Exception as e:
#         print(f"加载协议文件失败: {e}")
#         return None


# # 使用示例
# if __name__ == "__main__":
#     # 获取服务器配置
#     config = get_server_config("default")
#     print("默认服务器配置:", config)
    
#     # 获取主题模板
#     device_status_template = get_topic_template("device", "status")
#     print("设备状态主题模板:", device_status_template)
    
#     # 获取主题详细配置
#     device_status_config = get_topic_config("device_status")
#     print("设备状态主题配置:", device_status_config)
    
#     # 格式化主题（使用模板）
#     device_status_topic = format_topic(device_status_template, client_id="device_001")
#     print("格式化后的主题（模板）:", device_status_topic)
    
#     # 格式化主题（使用配置）
#     device_status_topic2 = format_topic_from_config("device_status", "device_001")
#     print("格式化后的主题（配置）:", device_status_topic2)
    
#     # 获取消息结构
#     schema = get_message_schema("device_status")
#     print("设备状态消息结构（包含分类）:", list(schema.get("categories", {}).keys()))
    
#     # 获取特定分类的字段定义
#     system_schema = get_status_category_schema("device_status", "system")
#     print("系统分类字段:", list(system_schema.get("fields", {}).keys()))
    
#     sensor_schema = get_status_category_schema("device_status", "sensor")
#     print("传感器分类字段:", list(sensor_schema.get("fields", {}).keys()))
