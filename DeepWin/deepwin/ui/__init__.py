#!/usr/bin/env python3
"""
DeepWin UI Package

This package contains all user interface components for the DeepWin system:
- Main window management
- GUI manager
- Various interface components
"""

# Core UI management
from .gui_manager import GuiManager
from .app.view.main_window import MainWindow

# Interface components
from .app.view.home_interface import HomeInterface
from .app.view.device_interface import DeviceInterface
from .app.view.gallery_interface import GalleryInterface
from .app.view.setting_interface import SettingInterface

# Export main classes for easy access
__all__ = [
    # Core UI management
    'GuiManager',
    'MainWindow',
    
    # Interface components
    'HomeInterface',
    'DeviceInterface',
    'GalleryInterface',
    'SettingInterface',
]

# Version info
__version__ = "0.1.0"
__author__ = "DeepWin Team"
