#!/usr/bin/env python3
"""
DeepWin Device Logic Manager Package

This package manages the logic for all devices in the DeepWin system.
Provides a unified interface for device management, state monitoring, and control.
"""

# Core manager
from .manager import DeviceLogicManager

# Base device classes
from .devices.base_device import BaseDevice, BaseDeviceState, DeviceStatus

# Device implementations
from .devices.deep_motor.deep_motor import DeepMotor
from .devices.deep_motor.state_model import DeepMotorState
from .devices.deep_arm.deep_arm import DeepArm
from .devices.deep_arm.state_model import DeepArmState
from .devices.deep_toy.deep_toy import DeepToy
from .devices.deep_toy.state_model import DeepToyState

# Export main classes for easy access
__all__ = [
    # Core manager
    'DeviceLogicManager',
    
    # Base classes
    'BaseDevice',
    'BaseDeviceState', 
    'DeviceStatus',
    
    # Device implementations
    'DeepMotor',
    'DeepMotorState',
    'DeepArm',
    'DeepArmState',
    'DeepToy',
    'DeepToyState',
]

# Version info
__version__ = "0.1.0"
__author__ = "DeepWin Team"