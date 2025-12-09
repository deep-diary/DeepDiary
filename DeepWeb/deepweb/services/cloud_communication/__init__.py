#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cloud Communication Package
云通信服务包

作者: DeepDiary Team
日期: 2025-01-27
"""

# 导入MQTT管理器
try:
    from .mqtt.mqtt_manager import MQTTManager
except ImportError:
    MQTTManager = None

# 导入Immich客户端
try:
    from .immich_client import ImmichClient
except ImportError:
    ImmichClient = None

# Export main classes
__all__ = [
    'MQTTManager',
    'ImmichClient',
]

__version__ = "1.0.0"
__author__ = "DeepDiary Team"
