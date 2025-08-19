#!/usr/bin/env python3
"""
DeepWin Data Management Package

This package contains all data management components for the DeepWin system:
- Log management
- Local database management
- Configuration management
"""

# Core data management classes
from .log_manager import LogManager
from .local_database import LocalDatabaseManager
from .config_manager import ConfigManager

# Database management classes
from .database import (
    BaseDatabase, SQLiteManager, QdrantManager, 
    DatabaseFactory, DatabaseCoordinator
)

# Export main classes for easy access
__all__ = [
    'LogManager',
    'LocalDatabaseManager',
    'ConfigManager',
    'BaseDatabase',
    'SQLiteManager',
    'QdrantManager',
    'DatabaseFactory',
    'DatabaseCoordinator',
]

# Version info
__version__ = "0.1.0"
__author__ = "DeepWin Team"

