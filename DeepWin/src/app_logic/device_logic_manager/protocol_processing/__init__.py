#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
协议处理包，用于处理不同产品的串口协议
作为串口通信层和应用层之间的桥梁
"""

from .base import ProtocolProcessor, ProtocolCommand, ProtocolResponse
from .protocol_manager import ProtocolManager
from .devices import DeepArmProtocol, TemplateProtocol

__all__ = [
    # 基类
    'ProtocolProcessor',
    'ProtocolCommand',
    'ProtocolResponse',
    
    # 管理器
    'ProtocolManager',
    
    # 实现类
    'DeepArmProtocol',
    'TemplateProtocol',
]

# 包版本
__version__ = '0.1.0'
