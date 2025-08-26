#!/usr/bin/env python3
"""
DeepWin Utils Package

This package contains utility modules and helper functions for the DeepWin system:
- Configuration utilities
- Constants and exceptions
- Common helper functions
"""

# Core utility classes
# from .config import Config  # 暂时注释掉，因为config.py是空的
# from .constants import *    # 暂时注释掉，因为constants.py是空的
# from .exceptions import *   # 暂时注释掉，因为exceptions.py是空的
from .test import TestBase, ConfigTestBase
from .path_manager import PathManager, get_path_manager, get_output_path, get_models_path, get_data_path

# Export main classes for easy access
__all__ = [
    # 'Config',  # 暂时注释掉
    # 'constants',  # 暂时注释掉
    # 'exceptions',  # 暂时注释掉
    'TestBase',
    'ConfigTestBase',
    'PathManager',
    'get_path_manager',
    'get_output_path',
    'get_models_path',
    'get_data_path'
]

# Version info
__version__ = "0.1.0"
__author__ = "DeepWin Team"
