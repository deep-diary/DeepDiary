#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepWeb Services Package
简化的服务包，只包含DeepWeb需要的模块

作者: DeepDiary Team
日期: 2025-01-27
"""

# 只导入存在的模块
try:
    from .mqtt_service_adapter import MQTTServiceAdapter
except ImportError:
    MQTTServiceAdapter = None

try:
    from .simple_video_receiver import SimpleVideoReceiver, get_video_receiver, start_video_service, stop_video_service
except ImportError:
    SimpleVideoReceiver = None
    get_video_receiver = None
    start_video_service = None
    stop_video_service = None

# Export main classes for easy access
__all__ = [
    'MQTTServiceAdapter',
    'SimpleVideoReceiver',
    'get_video_receiver',
    'start_video_service',
    'stop_video_service',
]

# Version info
__version__ = "1.0.0"
__author__ = "DeepDiary Team"