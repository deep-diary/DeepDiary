#!/usr/bin/env python3
"""
DeepWeb Data Management Package

This package contains all data management components for the DeepWeb system:
- Log management
"""

# Core data management classes
from .log_manager import LogManager

# Export main classes for easy access
__all__ = [
    'LogManager',
]

# Version info
__version__ = "0.1.0"
__author__ = "DeepWeb Team"

