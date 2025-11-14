"""
MQTT配置文件 - Thumbler 不倒翁设备专用
定义 Thumbler 设备的 MQTT 连接配置和主题配置
根据 README.md 需求文档定义
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
        "reconnect_interval": 5,
    },
    "emqx": {
        "host": "broker.emqx.io",
        "port": 1883,
        "username": None,
        "password": None,
        "keepalive": 60,
        "auto_reconnect": True,
        "reconnect_interval": 5,
    },
}

# 协议版本
PROTOCOL_VERSION = "1.0.0"

# Thumbler 主题配置模板
TOPIC_TEMPLATES = {
    "thumbler": {
        "status": "Thumbler/{device_id}/status",  # 设备状态信息（设备发布，Web订阅）
        "cmd": "Thumbler/{device_id}/cmd"         # 控制命令（Web发布，设备订阅）
    }
}

# Thumbler 主题详细配置 - 列表格式，可直接遍历使用
TOPIC_CONFIGS = [
    {
        "key": "thumbler_status",
        "name": "Thumbler/{device_id}/status",
        "description": "Thumbler 设备状态信息",
        "period_ms": 0,  # 事件驱动，由设备决定发送频率
        "qos": 0,
        "retained": False,
        "direction": "pub"  # 设备发布，Web订阅
    },
    {
        "key": "thumbler_cmd",
        "name": "Thumbler/{device_id}/cmd",
        "description": "Thumbler 控制命令",
        "period_ms": 0,  # 事件驱动，无周期性
        "qos": 1,
        "retained": False,
        "direction": "sub"  # 设备订阅，Web发布
    }
]

# Thumbler 消息类型定义
MESSAGE_TYPES = {
    "thumbler_status": {
        "topic_template": "Thumbler/{device_id}/status",
        "fields": {
            "cur_cam_switch": {"type": "boolean", "description": "摄像头开关状态", "required": False},
            "g_acc_x": {"type": "float", "description": "X轴加速度(m/s²)", "required": False},
            "g_acc_y": {"type": "float", "description": "Y轴加速度(m/s²)", "required": False},
            "g_acc_z": {"type": "float", "description": "Z轴加速度(m/s²)", "required": False},
            "g_acc_g": {"type": "float", "description": "总加速度(m/s²)", "required": False},
            "g_pitch": {"type": "float", "description": "俯仰角(度)", "required": False},
            "g_roll": {"type": "float", "description": "翻滚角(度)", "required": False},
            "cur_led_mode": {"type": "integer", "description": "当前LED工作模式(0:关闭,1:静态颜色,2:闪烁,3:呼吸灯,4:流水灯/滚动,5:系统状态)", "required": False},
            "cur_led_brightness": {"type": "integer", "description": "当前LED默认亮度(0-255)", "required": False},
            "cur_led_low_brightness": {"type": "integer", "description": "当前LED低亮度(0-255)", "required": False},
            "cur_led_color_red": {"type": "integer", "description": "当前LED颜色-红色分量(0-255)", "required": False},
            "cur_led_color_green": {"type": "integer", "description": "当前LED颜色-绿色分量(0-255)", "required": False},
            "cur_led_color_blue": {"type": "integer", "description": "当前LED颜色-蓝色分量(0-255)", "required": False},
            "cur_led_interval_ms": {"type": "integer", "description": "当前LED动画间隔时间(毫秒)", "required": False},
            "cur_led_scroll_length": {"type": "integer", "description": "当前LED滚动模式下的亮灯数量", "required": False},
            "cur_tumbler_mode": {"type": "integer", "description": "不倒翁工作模式(0:静止,1:左右循环晃动,2:来回旋转,3:充电中)", "required": False},
            "is_has_people": {"type": "boolean", "description": "当前环境是否有人", "required": False},
            "power_percent": {"type": "integer", "description": "当前系统电量(0-100)", "required": False},
            "timestamp": {"type": "integer", "description": "时间戳(Unix秒)", "required": False}
        }
    },
    "thumbler_cmd": {
        "topic_template": "Thumbler/{device_id}/cmd",
        "fields": {
            # 基础控制字段
            "tar_cam_switch": {"type": "boolean", "description": "摄像头开关控制指令", "required": False},
            "tar_pitch": {"type": "float", "description": "目标俯仰角(度)", "required": False},
            "tar_roll": {"type": "float", "description": "目标翻滚角(度)", "required": False},
            "tar_tumbler_mode": {"type": "integer", "description": "目标不倒翁工作模式(0:静止,1:左右循环晃动,2:来回旋转,3:充电中)", "required": False},
            # LED 控制字段
            "tar_led_mode": {"type": "integer", "description": "目标LED工作模式(0:关闭,1:静态颜色,2:闪烁,3:呼吸灯,4:流水灯/滚动,5:系统状态)", "required": False},
            "tar_led_brightness": {"type": "integer", "description": "目标LED默认亮度(0-255)", "required": False},
            "tar_led_low_brightness": {"type": "integer", "description": "目标LED低亮度(0-255，用于系统状态)", "required": False},
            "tar_led_color_red": {"type": "integer", "description": "LED颜色-红色分量(0-255)", "required": False},
            "tar_led_color_green": {"type": "integer", "description": "LED颜色-绿色分量(0-255)", "required": False},
            "tar_led_color_blue": {"type": "integer", "description": "LED颜色-蓝色分量(0-255)", "required": False},
            "tar_led_color_low_red": {"type": "integer", "description": "LED低颜色-红色分量(0-255，用于呼吸灯和流水灯)", "required": False},
            "tar_led_color_low_green": {"type": "integer", "description": "LED低颜色-绿色分量(0-255，用于呼吸灯和流水灯)", "required": False},
            "tar_led_color_low_blue": {"type": "integer", "description": "LED低颜色-蓝色分量(0-255，用于呼吸灯和流水灯)", "required": False},
            "tar_led_interval_ms": {"type": "integer", "description": "LED动画间隔时间(毫秒，>0，建议50-1000)", "required": False},
            "tar_led_scroll_length": {"type": "integer", "description": "LED滚动模式下的亮灯数量(1-最大LED数量，仅用于滚动模式)", "required": False},
            "timestamp": {"type": "integer", "description": "时间戳(Unix秒)", "required": False}
        }
    }
}

# Thumbler LED 模式枚举（对应设备端 CircularStrip 方法）
THUMBLER_LED_MODES = {
    "off": 0,           # 关闭
    "static": 1,        # 静态颜色 (SetAllColor)
    "blink": 2,         # 闪烁 (Blink)
    "breathe": 3,       # 呼吸灯 (Breathe)
    "scroll": 4,        # 流水灯/滚动 (Scroll)
    "system": 5         # 系统状态 (OnStateChanged)
}

# Thumbler 工作模式枚举
THUMBLER_MODES = {
    "idle": 0,          # 静止
    "swing": 1,         # 左右循环晃动
    "rotate": 2,        # 来回旋转
    "charging": 3       # 充电中
}

# QoS级别定义
QOS_LEVELS = {
    "AT_MOST_ONCE": 0,      # 最多一次
    "AT_LEAST_ONCE": 1,     # 至少一次
    "EXACTLY_ONCE": 2       # 恰好一次
}

# Thumbler 常用主题模式
COMMON_PATTERNS = {
    "all_thumbler_status": "Thumbler/+/status",    # 订阅所有 Thumbler 设备状态
    "all_thumbler_cmd": "Thumbler/+/cmd",          # 订阅所有 Thumbler 控制命令（用于监控）
    "specific_thumbler_status": "Thumbler/{device_id}/status",
    "specific_thumbler_cmd": "Thumbler/{device_id}/cmd"
}


