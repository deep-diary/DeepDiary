#!/usr/bin/env python3
"""
DeepWin Core Manager Package

This package contains the core management components for the DeepWin system:
- Application coordination
- Task scheduling
- Worker management
- Handler management
"""

# Core coordination
from .coordinator import Coordinator

# Task management
from .task_scheduler import TaskScheduler

# Worker management
from .workers import WorkerRunnable, WorkerSignals

# Handler management
from .handler.agents import AgentsHandler
from .handler.ai_coordinator import AiCoordinatorHandler
from .handler.cloud_communication import CloudCommunicationHandler
from .handler.coordinator import CoordinatorHandler
from .handler.demo import DemoHandler
from .handler.device_logic_manager import DeviceLogicManagerHandler
from .handler.gui_device_interface import GuiDeviceInterfaceHandler
from .handler.hardware_communication import HardwareCommunicationHandler
from .handler.memory_processing import MemoryProcessingHandler
from .handler.voice_communication import VoiceCommunicationHandler

# Export main classes for easy access
__all__ = [
    # Core coordination
    'Coordinator',
    
    # Task management
    'TaskScheduler',
    
    # Worker management
    'WorkerRunnable',
    'WorkerSignals',
    
    # Handler management
    'AgentsHandler',
    'AiCoordinatorHandler',
    'CloudCommunicationHandler',
    'CoordinatorHandler',
    'DemoHandler',
    'DeviceLogicManagerHandler',
    'GuiDeviceInterfaceHandler',
    'HardwareCommunicationHandler',
    'MemoryProcessingHandler',
    'VoiceCommunicationHandler',
]

# Version info
__version__ = "0.1.0"
__author__ = "DeepWin Team"
