#!/usr/bin/env python3
"""
DeepWin Utils Package

This package contains utility modules and helper functions for the DeepWin system:
- Configuration utilities
- Constants and exceptions
- Common helper functions
"""

# Core utility classes
from .config import Config
from .constants import *
from .exceptions import *

# Export main classes for easy access
__all__ = [
    'Config',
]

# Version info
__version__ = "0.1.0"
__author__ = "DeepWin Team"
