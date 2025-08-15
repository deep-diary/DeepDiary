#!/usr/bin/env python3
"""
DeepWin Services Package

This package contains all service layer components for the DeepWin system:
- Cloud communication services
- Hardware communication services
- Voice communication services
"""

# Cloud communication services
from .cloud_communication.api_client import CloudApiClient

# Hardware communication services
from .hardware_communication.device_protocol_parser import DeviceProtocolParser
from .hardware_communication.serial_communicator import SerialCommunicator

# Voice communication services
from .voice_communication.voice_manager import VoiceManager

# Export main classes for easy access
__all__ = [
    # Cloud communication
    'CloudApiClient',
    
    # Hardware communication
    'DeviceProtocolParser',
    'SerialCommunicator',
    
    # Voice communication
    'VoiceManager',
]

# Version info
__version__ = "0.1.0"
__author__ = "DeepWin Team"
