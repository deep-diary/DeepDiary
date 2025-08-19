#!/usr/bin/env python3
"""
DeepWin Model Initializer
模型初始化器 - 确保所有模型正确加载和配置
"""

import sys
from typing import List, Type
from sqlalchemy.orm import DeclarativeBase


class ModelInitializer:
    """模型初始化器，确保所有模型正确加载"""
    
    def __init__(self):
        self._models_loaded = False
        self._models: List[Type[DeclarativeBase]] = []
    
    def load_all_models(self):
        """加载所有模型"""
        if self._models_loaded:
            return self._models
        
        try:
            # 按依赖顺序导入模型
            from .user_model import UserModel
            from .need_model import NeedModel
            from .resource_model import ResourceModel
            from .photo_model import PhotoModel
            
            # 按顺序添加到列表
            self._models = [
                UserModel,
                NeedModel,
                ResourceModel,
                PhotoModel
            ]
            
            self._models_loaded = True
            print("✓ 所有模型加载完成")
            return self._models
            
        except Exception as e:
            print(f"❌ 模型加载失败: {e}")
            raise
    
    def get_all_models(self) -> List[Type[DeclarativeBase]]:
        """获取所有模型"""
        if not self._models_loaded:
            return self.load_all_models()
        return self._models
    
    def get_model_by_name(self, name: str) -> Type[DeclarativeBase]:
        """根据名称获取模型"""
        models = self.get_all_models()
        for model in models:
            if model.__name__ == name:
                return model
        raise ValueError(f"模型 '{name}' 未找到")
    
    def ensure_models_loaded(self):
        """确保模型已加载"""
        if not self._models_loaded:
            self.load_all_models()


# 全局初始化器实例
initializer = ModelInitializer()

# 便捷函数
def load_all_models():
    """加载所有模型"""
    return initializer.load_all_models()

def get_all_models():
    """获取所有模型"""
    return initializer.get_all_models()

def get_model_by_name(name: str):
    """根据名称获取模型"""
    return initializer.get_model_by_name(name)

def ensure_models_loaded():
    """确保模型已加载"""
    initializer.ensure_models_loaded()

# 自动加载模型
try:
    load_all_models()
except Exception as e:
    print(f"警告：模型自动加载失败: {e}")
    print("将在需要时手动加载")
