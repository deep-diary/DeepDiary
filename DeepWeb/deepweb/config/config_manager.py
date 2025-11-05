#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepWeb 配置管理器
简化的配置管理，专门为DeepWeb项目设计

作者: DeepDiary Team
日期: 2025-01-27
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """DeepWeb配置管理器"""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent
        self.config_file = self.config_dir / "config.json"
        self._config = {}
        
        # 加载配置
        self._load_config()
    
    def _load_config(self):
        """加载配置文件"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                # 配置加载成功，不输出日志（避免干扰主程序日志）
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                self._config = self._get_default_config()
        else:
            print("配置文件不存在，使用默认配置")
            self._config = self._get_default_config()
            self.save_config(self._config)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "mqtt": {
                "host": "localhost",
                "port": 1883,
                "username": None,
                "password": None,
                "client_id": "deepweb-client",
                "keepalive": 60,
                "auto_reconnect": True,
                "reconnect_interval": 5
            },
            "tcp_server": {
                "host": "0.0.0.0",
                "port": 8080,
                "web_host": "0.0.0.0",
                "web_port": 8000
            },
            "ui": {
                "theme": "浅色",
                "language": "中文",
                "auto_refresh": True,
                "refresh_interval": 5,
                "show_debug": False
            },
            "devices": {
                "default_device": {
                    "device_id": "ATK-DNESP32S3-ESP32-S3-12345678",
                    "device_type": "ATK-DNESP32S3",
                    "firmware_version": "1.0.0",
                    "ip_address": "192.168.1.100"
                }
            }
        }
    
    def get_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """获取配置值，支持点分路径"""
        keys = key_path.split('.')
        current = self._config
        
        try:
            for key in keys:
                current = current[key]
            return current
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """设置配置值，支持点分路径"""
        keys = key_path.split('.')
        current = self._config
        
        # 遍历到最后一个键的父级
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # 设置最后一个键的值
        current[keys[-1]] = value
        
        # 保存配置
        self.save_config(self._config)
    
    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """保存配置到文件"""
        if config is None:
            config = self._config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            print(f"配置已保存: {self.config_file}")
        except Exception as e:
            print(f"保存配置文件失败: {e}")
    
    def reload_config(self):
        """重新加载配置文件"""
        self._load_config()