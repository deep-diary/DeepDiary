#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
串口通信包的配置模块
负责加载和验证配置
"""

import os
import yaml
import logging
from .serial_exceptions import ConfigError

# 默认配置
DEFAULT_CONFIG = {
    # 串口设置
    'port': '/dev/ttyUSB0',
    'baudrate': 115200,
    'bytesize': 8,
    'parity': 'N',
    'stopbits': 1,
    'timeout': 0.1,
    'write_timeout': 1.0,
    'xonxoff': False,
    'rtscts': False,
    'dsrdtr': False,
    
    # 读取设置
    'read_mode': 'line',
    'line_terminator': '\n',
    'read_length': 1024,
    
    # 处理设置
    'encoding': 'utf-8',
    'auto_reconnect': True,
    'reconnect_delay': 2.0,
    'reconnect_attempts': 5,
    
    # 高级设置
    'buffer_size': 4096,
    'read_chunk_size': 128,
    'flush_on_write': True,
    'thread_sleep': 0.01,
    'line_buffer_size': 100,
    
    # 日志设置
    'log_level': 'info',
    'log_to_file': False,
    'log_file': 'serial_comm.log'
}

# 日志级别映射
LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO, 
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}

def load_config(config_file=None):
    """
    加载配置文件
    
    Args:
        config_file (str): 配置文件路径，None则使用默认配置
        
    Returns:
        dict: 配置字典
    
    Raises:
        ConfigError: 当配置加载或验证失败时
    """
    # 使用默认配置作为基础
    config = DEFAULT_CONFIG.copy()
    
    # 如果指定了配置文件，尝试加载
    if config_file:
        try:
            # 如果是相对路径，转换为绝对路径
            if not os.path.isabs(config_file):
                # 尝试不同的可能基础路径
                base_paths = [
                    os.getcwd(),  # 当前工作目录
                    os.path.dirname(os.path.abspath(__file__)),  # serial_config.py所在目录
                    os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'),  # 上一级目录
                ]
                
                # 依次尝试各个基础路径
                for base_path in base_paths:
                    abs_path = os.path.abspath(os.path.join(base_path, config_file))
                    if os.path.exists(abs_path):
                        config_file = abs_path
                        break
            
            # 检查文件是否存在
            if not os.path.exists(config_file):
                # 尝试在默认位置查找
                default_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'serial_config.yaml')
                if os.path.exists(default_config):
                    config_file = default_config
                else:
                    raise ConfigError(f"配置文件未找到: {config_file}")
                
            with open(config_file, 'r', encoding='utf-8') as f:
                yaml_config = yaml.safe_load(f)
                
            if yaml_config:
                # 更新配置
                config.update(yaml_config)
                
            # 记录使用的配置文件路径
            config['_config_path'] = config_file
            
        except Exception as e:
            if isinstance(e, ConfigError):
                raise
            raise ConfigError(f"加载配置文件失败: {str(e)}")
    else:
        # 如果没有指定配置文件，尝试加载默认位置的配置
        default_config = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'serial_config.yaml')
        if os.path.exists(default_config):
            try:
                with open(default_config, 'r', encoding='utf-8') as f:
                    yaml_config = yaml.safe_load(f)
                    
                if yaml_config:
                    # 更新配置
                    config.update(yaml_config)
                    
                # 记录使用的配置文件路径
                config['_config_path'] = default_config
            except Exception as e:
                # 如果默认配置加载失败，只记录日志，使用内置默认配置继续
                print(f"警告: 默认配置文件加载失败: {str(e)}，将使用内置默认值")
    
    # 验证配置
    validate_config(config)
    
    return config

def validate_config(config):
    """
    验证配置项
    
    Args:
        config (dict): 配置字典
        
    Raises:
        ConfigError: 当配置验证失败时
    """
    try:
        # 检查必需字段
        required_fields = ['port', 'baudrate', 'bytesize', 'parity', 'stopbits']
        for field in required_fields:
            if field not in config:
                raise ConfigError(f"缺少必要配置项: {field}")
        
        # 验证波特率是整数且在合理范围内
        if not isinstance(config['baudrate'], int) or config['baudrate'] <= 0:
            raise ConfigError(f"波特率必须是正整数，当前值: {config['baudrate']}")
        
        # 验证数据位
        if config['bytesize'] not in [5, 6, 7, 8]:
            raise ConfigError(f"数据位必须是5、6、7或8，当前值: {config['bytesize']}")
        
        # 验证校验位
        if config['parity'] not in ['N', 'E', 'O', 'M', 'S']:
            raise ConfigError(f"校验位必须是N、E、O、M或S，当前值: {config['parity']}")
        
        # 验证停止位
        if config['stopbits'] not in [1, 1.5, 2]:
            raise ConfigError(f"停止位必须是1、1.5或2，当前值: {config['stopbits']}")
        
        # 验证读取模式
        if config['read_mode'] not in ['line', 'raw', 'length']:
            raise ConfigError(f"读取模式必须是line、raw或length，当前值: {config['read_mode']}")
        
        # 验证日志级别
        if config['log_level'].lower() not in LOG_LEVELS:
            raise ConfigError(f"日志级别无效，当前值: {config['log_level']}")
        
    except Exception as e:
        if isinstance(e, ConfigError):
            raise
        raise ConfigError(f"配置验证失败: {str(e)}")
    
    return True 