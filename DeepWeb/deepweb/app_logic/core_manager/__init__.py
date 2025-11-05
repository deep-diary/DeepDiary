#!/usr/bin/env python3
"""
DeepWeb Core Manager Package

This package contains the core management components for the DeepWeb system:
- Application coordination
- Handler management
"""

# Core coordination
from .coordinator import Coordinator

# Handler management
from .base_handler import BaseHandler

# Export main classes for easy access
__all__ = [
    # Core coordination
    'Coordinator',
    
    # Handler management
    'BaseHandler',
]

# Version info
__version__ = "0.1.0"
__author__ = "DeepWeb Team"

