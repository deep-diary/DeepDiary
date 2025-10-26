"""
MQTT配置文件
定义常用的MQTT连接配置和主题配置
"""

from typing import Dict, Any

# MQTT服务器配置
MQTT_SERVERS = {
    "default": {
        "host": "34.172.161.212",
        "port": 1883,
        "username": None,
        "password": None,
        "keepalive": 60,
        "auto_reconnect": True,
        "reconnect_interval": 5
    },
    "local": {
        "host": "localhost",
        "port": 1883,
        "username": None,
        "password": None,
        "keepalive": 60,
        "auto_reconnect": True,
        "reconnect_interval": 5
    },
    "secure": {
        "host": "your-secure-mqtt-server.com",
        "port": 8883,
        "username": "your_username",
        "password": "your_password",
        "keepalive": 60,
        "auto_reconnect": True,
        "reconnect_interval": 5
    }
}

# 主题配置模板
TOPIC_TEMPLATES = {
    "device": {
        "status": "device/{device_id}/status",
        "control": "device/{device_id}/control",
        "commands": "device/{device_id}/commands",
        "logs": "device/{device_id}/logs"
    },
    "sensor": {
        "data": "sensor/{sensor_id}/data",
        "config": "sensor/{sensor_id}/config",
        "status": "sensor/{sensor_id}/status"
    },
    "system": {
        "logs": "system/logs",
        "status": "system/status",
        "config": "system/config",
        "alerts": "system/alerts"
    },
    "user": {
        "profile": "user/{user_id}/profile",
        "settings": "user/{user_id}/settings",
        "notifications": "user/{user_id}/notifications"
    }
}

# 消息类型定义
MESSAGE_TYPES = {
    "device_status": {
        "topic_template": "device/{device_id}/status",
        "schema": {
            "device_id": "string",
            "status": "string",
            "timestamp": "float",
            "battery": "int",
            "temperature": "float",
            "location": {
                "lat": "float",
                "lng": "float"
            }
        }
    },
    "device_command": {
        "topic_template": "device/{device_id}/commands",
        "schema": {
            "command": "string",
            "parameters": "dict",
            "timestamp": "float",
            "priority": "int"
        }
    },
    "sensor_data": {
        "topic_template": "sensor/{sensor_id}/data",
        "schema": {
            "sensor_id": "string",
            "data_type": "string",
            "value": "float",
            "unit": "string",
            "timestamp": "float",
            "quality": "float"
        }
    },
    "system_log": {
        "topic_template": "system/logs",
        "schema": {
            "level": "string",
            "message": "string",
            "module": "string",
            "timestamp": "float",
            "details": "dict"
        }
    }
}

# QoS级别定义
QOS_LEVELS = {
    "AT_MOST_ONCE": 0,      # 最多一次
    "AT_LEAST_ONCE": 1,     # 至少一次
    "EXACTLY_ONCE": 2       # 恰好一次
}

# 常用主题模式
COMMON_PATTERNS = {
    "all_devices": "device/+/status",
    "all_sensors": "sensor/+/data",
    "all_logs": "system/logs",
    "device_commands": "device/+/commands",
    "user_notifications": "user/+/notifications"
}


def get_server_config(server_name: str = "default") -> Dict[str, Any]:
    """
    获取MQTT服务器配置
    
    Args:
        server_name: 服务器配置名称
        
    Returns:
        Dict: 服务器配置字典
    """
    return MQTT_SERVERS.get(server_name, MQTT_SERVERS["default"]).copy()


def get_topic_template(category: str, topic_type: str) -> str:
    """
    获取主题模板
    
    Args:
        category: 主题分类 (device, sensor, system, user)
        topic_type: 主题类型 (status, control, data, etc.)
        
    Returns:
        str: 主题模板字符串
    """
    return TOPIC_TEMPLATES.get(category, {}).get(topic_type, "")


def format_topic(template: str, **kwargs) -> str:
    """
    格式化主题字符串
    
    Args:
        template: 主题模板
        **kwargs: 模板参数
        
    Returns:
        str: 格式化后的主题字符串
    """
    return template.format(**kwargs)


def get_message_schema(message_type: str) -> Dict[str, Any]:
    """
    获取消息类型的数据结构定义
    
    Args:
        message_type: 消息类型名称
        
    Returns:
        Dict: 消息结构定义
    """
    return MESSAGE_TYPES.get(message_type, {}).get("schema", {})


# 使用示例
if __name__ == "__main__":
    # 获取服务器配置
    config = get_server_config("default")
    print("默认服务器配置:", config)
    
    # 获取主题模板
    device_status_template = get_topic_template("device", "status")
    print("设备状态主题模板:", device_status_template)
    
    # 格式化主题
    device_status_topic = format_topic(device_status_template, device_id="device_001")
    print("格式化后的主题:", device_status_topic)
    
    # 获取消息结构
    schema = get_message_schema("device_status")
    print("设备状态消息结构:", schema)
