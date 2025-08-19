#!/usr/bin/env python3
"""
DeepWin Database Models
使用SQLAlchemy ORM的数据模型包
"""

from .base_model import BaseModel, Base
from .user_model import UserModel
from .need_model import NeedModel
from .resource_model import ResourceModel
from .photo_model import PhotoModel

__all__ = [
    'Base',  # SQLAlchemy基类，用于创建表
    'BaseModel',
    'UserModel',
    'NeedModel',
    'ResourceModel',
    'PhotoModel',
]

__version__ = "0.2.0"
__author__ = "DeepWin Team"
