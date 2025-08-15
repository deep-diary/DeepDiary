#!/usr/bin/env python3
"""
DeepWin DeepToy Package

This package contains the DeepToy device implementation including:
- Core toy control
- State management
- Interactive features
"""

# Core toy classes
from .deep_toy import DeepToy
from .state_model import DeepToyState

# Export main classes for easy access
__all__ = [
    # Core classes
    'DeepToy',
    'DeepToyState',
]

# Version info
__version__ = "0.1.0"
__author__ = "DeepWin Team"
