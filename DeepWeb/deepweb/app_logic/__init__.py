#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepWeb App Logic Package
应用逻辑包

作者: DeepDiary Team
日期: 2025-01-27
"""

# 导入设备逻辑管理器
try:
    from .device_logic_manager import DeviceLogicManager, DeviceInfo, DeviceCommand, DeviceStatus, ComponentStatus
except ImportError:
    DeviceLogicManager = None
    DeviceInfo = None
    DeviceCommand = None
    DeviceStatus = None
    ComponentStatus = None

# Export main classes
__all__ = [
    'DeviceLogicManager',
    'DeviceInfo',
    'DeviceCommand',
    'DeviceStatus',
    'ComponentStatus',
]

__version__ = "1.0.0"
__author__ = "DeepDiary Team"
