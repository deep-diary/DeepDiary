#!/usr/bin/env python3
"""
DeepWin Database Models
使用SQLAlchemy ORM的数据模型包
"""

from .base_model import BaseModel, Base

# 延迟导入模型以避免循环依赖
# 这些模型会在需要时动态导入

__all__ = [
    'Base',  # SQLAlchemy基类，用于创建表
    'BaseModel',
    # 模型类将在需要时动态导入
]

__version__ = "0.2.0"
__author__ = "DeepWin Team"

# 导入模型初始化器
from .model_initializer import (
    load_all_models, get_all_models, 
    get_model_by_name, ensure_models_loaded
)

# 提供延迟导入函数
def get_user_model():
    """延迟导入UserModel"""
    ensure_models_loaded()
    return get_model_by_name('UserModel')

def get_need_model():
    """延迟导入NeedModel"""
    ensure_models_loaded()
    return get_model_by_name('NeedModel')

def get_resource_model():
    """延迟导入ResourceModel"""
    ensure_models_loaded()
    return get_model_by_name('ResourceModel')

def get_photo_model():
    """延迟导入PhotoModel"""
    ensure_models_loaded()
    return get_model_by_name('PhotoModel')
