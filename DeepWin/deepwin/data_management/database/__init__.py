#!/usr/bin/env python3
"""
DeepWin Database Package
使用SQLAlchemy ORM和langchain-qdrant的数据库管理包
"""

from .base_database import BaseDatabase
from .sqlite_manager import SQLiteManager
from .qdrant_manager import QdrantManager
from .database_factory import DatabaseFactory
from .database_coordinator import DatabaseCoordinator
from .models import Base  # SQLAlchemy基类

__all__ = [
    'BaseDatabase',
    'SQLiteManager', 
    'QdrantManager',
    'DatabaseFactory',
    'DatabaseCoordinator',
    'Base',  # 导出Base类，方便外部使用
]

__version__ = "0.2.0"
__author__ = "DeepWin Team"
