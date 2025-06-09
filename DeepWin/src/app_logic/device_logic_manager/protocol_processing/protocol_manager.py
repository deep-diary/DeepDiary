#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
协议管理器
用于管理和获取不同设备的协议实现
"""

from typing import Dict, Type
from app_logic.device_logic_manager.protocol_processing.base import ProtocolProcessor

class ProtocolManager:
    """协议管理器类"""
    
    _instance = None
    _protocols: Dict[str, Type[ProtocolProcessor]] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProtocolManager, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def register_protocol(cls, device_type: str, protocol_class: Type[ProtocolProcessor]):
        """
        注册设备协议
        
        Args:
            device_type: 设备类型
            protocol_class: 协议实现类
        """
        cls._protocols[device_type] = protocol_class
    
    @classmethod
    def get_protocol(cls, device_type: str, **kwargs) -> ProtocolProcessor:
        """
        获取设备协议实例
        
        Args:
            device_type: 设备类型
            **kwargs: 协议初始化参数
            
        Returns:
            ProtocolProcessor: 协议实例
            
        Raises:
            KeyError: 设备类型未注册
        """
        if device_type not in cls._protocols:
            raise KeyError(f"未找到设备类型 '{device_type}' 的协议实现")
        
        return cls._protocols[device_type](**kwargs)
    
    @classmethod
    def list_protocols(cls) -> list:
        """
        列出所有已注册的设备类型
        
        Returns:
            list: 设备类型列表
        """
        return list(cls._protocols.keys()) 