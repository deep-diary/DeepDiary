#!/usr/bin/env python3
"""
DeepWin Configuration Package

This package contains all configuration files and management utilities for the DeepWin system.
Supports multiple configuration formats and environment-specific configurations.
"""

from .config_manager import ConfigManager
from .config_validator import ConfigValidator

__all__ = [
    'ConfigManager',
    'ConfigValidator'
]

__version__ = "0.1.0"
__author__ = "DeepWin Team"
