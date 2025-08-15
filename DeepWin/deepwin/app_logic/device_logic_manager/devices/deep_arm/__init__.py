#!/usr/bin/env python3
"""
DeepWin DeepArm Package

This package contains the DeepArm device implementation including:
- Core arm control
- State management
- Teaching trajectory management
"""

# Core arm classes
from .deep_arm import DeepArm
from .state_model import DeepArmState

# Trajectory management
from .teaching_trajectory_manager import TeachingTrajectoryManager

# Export main classes for easy access
__all__ = [
    # Core classes
    'DeepArm',
    'DeepArmState',
    
    # Trajectory management
    'TeachingTrajectoryManager',
]

# Version info
__version__ = "0.1.0"
__author__ = "DeepWin Team"
