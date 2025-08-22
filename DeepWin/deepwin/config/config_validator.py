#!/usr/bin/env python3
"""
Configuration Validator for DeepWin
"""

import json
from typing import Dict, Any, List, Tuple, Optional
import logging

class ConfigValidator:
    """配置验证器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validation_errors = []
        self.validation_warnings = []
    
    def validate_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """验证配置文件"""
        self.validation_errors = []
        self.validation_warnings = []
        
        try:
            # 基本验证
            if not isinstance(config, dict):
                self.validation_errors.append("配置文件必须是字典格式")
                return False, self.validation_errors, self.validation_warnings
            
            # 验证必需字段
            required_sections = ["general", "device_settings", "network"]
            for section in required_sections:
                if section not in config:
                    self.validation_errors.append(f"缺少必需配置段: {section}")
            
            # 验证设备配置
            if "device_settings" in config:
                self._validate_device_settings(config["device_settings"])
            
            # 验证网络配置
            if "network" in config:
                self._validate_network_settings(config["network"])
            
            is_valid = len(self.validation_errors) == 0
            return is_valid, self.validation_errors, self.validation_warnings
            
        except Exception as e:
            self.logger.error(f"配置验证异常: {e}")
            self.validation_errors.append(f"验证异常: {e}")
            return False, self.validation_errors, self.validation_warnings
    
    def _validate_device_settings(self, device_config: Dict[str, Any]):
        """验证设备配置"""
        if not isinstance(device_config, dict):
            self.validation_errors.append("设备配置必须是字典格式")
            return
        
        # 检查串口配置
        for device in ["deeparm", "deepmotor"]:
            serial_port = device_config.get(f"{device}_serial_port")
            if serial_port and not serial_port.startswith("COM"):
                self.validation_warnings.append(f"{device} 串口配置可能不正确: {serial_port}")
    
    def _validate_network_settings(self, network_config: Dict[str, Any]):
        """验证网络配置"""
        if not isinstance(network_config, dict):
            self.validation_errors.append("网络配置必须是字典格式")
            return
        
        # 检查端口范围
        port = network_config.get("mqtt_broker_port")
        if port and (port < 1 or port > 65535):
            self.validation_errors.append("MQTT端口必须在1-65535范围内")
    
    def get_validation_summary(self) -> str:
        """获取验证摘要"""
        if not self.validation_errors and not self.validation_warnings:
            return "✅ 配置验证通过"
        
        summary = []
        if self.validation_errors:
            summary.append(f"❌ 错误: {len(self.validation_errors)}")
        if self.validation_warnings:
            summary.append(f"⚠️ 警告: {len(self.validation_warnings)}")
        
        return " ".join(summary)
