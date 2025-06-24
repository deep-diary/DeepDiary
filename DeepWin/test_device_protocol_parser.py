#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试优化后的设备协议解析器
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager
from src.services.hardware_communication.device_protocol_parser import DeviceProtocolParser


def test_device_protocol_parser():
    """测试设备协议解析器的自动发现和注册功能"""
    
    # 初始化日志和配置管理器
    log_manager = LogManager()
    config_manager = ConfigManager()
    
    print("=== 测试设备协议解析器自动发现功能 ===")
    
    # 创建设备协议解析器实例
    device_parser = DeviceProtocolParser(log_manager, config_manager)
    
    # 获取已注册的设备列表
    registered_devices = device_parser.get_registered_devices()
    print(f"已注册的设备类型: {registered_devices}")
    
    # 测试设备类型提取功能
    print("\n=== 测试设备类型提取功能 ===")
    test_cases = [
        "deep_motor_protocol",
        "deep_arm_protocol", 
        "my_device_protocol",
        "test_sensor_protocol"
    ]
    
    for folder_name in test_cases:
        device_type = device_parser._extract_device_type_from_folder_name(folder_name)
        print(f"文件夹: {folder_name} -> 设备类型: {device_type}")
    
    # 测试设备ID匹配功能
    print("\n=== 测试设备ID匹配功能 ===")
    test_device_ids = [
        "DeepMotor001",
        "DeepArm002", 
        "UnknownDevice003",
        "DeepMotor_Test"
    ]
    
    for device_id in test_device_ids:
        device_type = device_parser._get_device_type_from_id(device_id)
        print(f"设备ID: {device_id} -> 匹配的设备类型: {device_type}")
    
    # 清理资源
    device_parser.cleanup()
    
    print("\n=== 测试完成 ===")


if __name__ == "__main__":
    test_device_protocol_parser() 