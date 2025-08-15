#!/usr/bin/env python3
"""
DeepWin Devices Package

This package contains all device implementations for the DeepWin system.
Each device type has its own module with specific functionality.
"""

# Base device classes
from .base_device import BaseDevice, BaseDeviceState, DeviceStatus

# Device implementations
from .deep_motor.deep_motor import DeepMotor
from .deep_motor.state_model import DeepMotorState
from .deep_arm.deep_arm import DeepArm
from .deep_arm.state_model import DeepArmState
from .deep_toy.deep_toy import DeepToy
from .deep_toy.state_model import DeepToyState

# Export all device classes
__all__ = [
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
