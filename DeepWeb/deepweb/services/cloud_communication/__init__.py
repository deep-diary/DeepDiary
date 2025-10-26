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

# Export main classes
__all__ = [
    'MQTTManager',
]

__version__ = "1.0.0"
__author__ = "DeepDiary Team"
