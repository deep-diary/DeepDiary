#!/usr/bin/env python3
"""
DeepWin DeepMotor Package

This package contains the DeepMotor device implementation including:
- Core motor control
- State management
- Command parsing and execution
- Trajectory management
- Teaching capabilities
"""

# Core motor classes
from .deep_motor import DeepMotor
from .state_model import DeepMotorState

# Command system
from .command_parser import CommandParser
from .command_description import CommandDescription

# Data management
from .data_buffer_manager import DeepMotorDataBufferManager

# Trajectory management
from .teaching_trajectory_manager import TeachingTrajectoryManager
from .teaching_capability import TeachingCapability

# Configuration and utilities
from .matplotlib_config import configure_matplotlib_globally

# Export main classes for easy access
__all__ = [
    # Core classes
    'DeepMotor',
    'DeepMotorState',
    
    # Command system
    'CommandParser', 
    'CommandDescription',
    
    # Data management
    'DeepMotorDataBufferManager',
    
    # Trajectory management
    'TeachingTrajectoryManager',
    'TeachingCapability',
    
    # Configuration
    'configure_matplotlib_globally',
]

# Version info
__version__ = "0.1.0"
__author__ = "DeepWin Team"
