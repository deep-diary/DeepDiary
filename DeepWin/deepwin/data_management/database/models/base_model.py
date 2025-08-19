#!/usr/bin/env python3
"""
DeepWin Database Models Base Class
使用SQLAlchemy ORM的数据模型基类，支持混合方法和事件监听
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import Column, Integer, DateTime, text, event, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.sql import func
from sqlalchemy_utils import Timestamp # 自动添加created_at/updated_at
from sqlalchemy_utils import generic_repr, force_auto_coercion
from sqlalchemy_utils.types import ScalarListType
from ...config_manager import ConfigManager
from ...log_manager import LogManager

# 创建SQLAlchemy基类
Base = declarative_base()


class BaseModel:
    """数据模型基类，使用组合模式，避免SQLAlchemy继承问题"""
    
    def __init__(self, config_manager: ConfigManager = None, log_manager: LogManager = None, **kwargs):
        # 首先初始化变更检测相关的属性
        self._changed_fields = set()
        self._original_values = {}
        
        # 设置配置管理器
        self.config_manager = config_manager
        self.logger = log_manager.get_logger(__name__) if log_manager else None
        
        # 设置属性值
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # 记录原始值用于变更检测
        self._original_values = self._get_current_values()

    def has_changes(self) -> bool:
        """检查模型是否有变更"""
        return len(self._changed_fields) > 0

    def get_changes(self) -> Dict[str, Any]:
        """获取变更的字段和值"""
        changes = {}
        current_values = self._get_current_values()
        for field in self._changed_fields:
            if field in current_values:
                changes[field] = current_values[field]
        return changes

    def _get_current_values(self) -> Dict[str, Any]:
        """获取当前所有字段的值"""
        values = {}
        if hasattr(self, '__table__'):
            for column in self.__table__.columns:
                values[column.name] = getattr(self, column.name, None)
        return values

    def _mark_field_changed(self, field_name: str):
        """标记字段为已变更"""
        self._changed_fields.add(field_name)

    def __setattr__(self, name, value):
        """重写属性设置，自动标记变更"""
        if not name.startswith('_') and hasattr(self, '__table__'):
            # 检查是否为表字段
            if name in [col.name for col in self.__table__.columns]:
                old_value = getattr(self, name, None)
                if old_value != value:
                    self._mark_field_changed(name)
        super().__setattr__(name, value)

    def to_dict(self) -> Dict[str, Any]:
        """将模型转换为字典"""
        result = {}
        if hasattr(self, '__table__'):
            for column in self.__table__.columns:
                value = getattr(self, column.name, None)
                if value is not None:
                    if isinstance(value, datetime):
                        result[column.name] = value.isoformat()
                    else:
                        result[column.name] = value
        return result

    def from_dict(self, data: Dict[str, Any]) -> 'BaseModel':
        """从字典更新模型数据"""
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        return self

    def to_json(self) -> str:
        """将模型转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def from_json(self, json_str: str) -> 'BaseModel':
        """从JSON字符串更新模型数据"""
        data = json.loads(json_str)
        return self.from_dict(data)

    def copy(self) -> 'BaseModel':
        """创建模型的副本"""
        data = self.to_dict()
        data.pop('id', None)  # 移除ID，避免重复
        return self.__class__(**data)

    def validate(self) -> bool:
        """验证模型数据（子类需要实现）"""
        return True

    def __str__(self):
        """字符串表示"""
        return f"{self.__class__.__name__}(id={getattr(self, 'id', 'N/A')})"

    def __repr__(self):
        """详细字符串表示"""
        return f"{self.__class__.__name__}({self.to_dict()})"


# 创建基础字段的Mixin类
class CommonFieldsMixin(Timestamp):
    """通用字段Mixin，提供基础字段定义"""
    
    id = Column(
        Integer, 
        primary_key=True,
        autoincrement='auto',
        comment='主键ID'
    )
    
    # created_at = Column(
    #     DateTime,
    #     server_default=func.now(),
    #     comment='创建时间'
    # )
    
    # updated_at = Column(
    #     DateTime,
    #     server_default=func.now(),
    #     onupdate=func.current_timestamp(),
    #     comment='更新时间'
    # )
    
    # 软删除字段
    deleted_at = Column(
        DateTime,
        nullable=True,
        comment='删除时间（软删除）'
    )
    
    # 审计字段
    created_by = Column(
        Integer,
        nullable=True,
        comment='创建者ID'
    )
    
    updated_by = Column(
        Integer,
        nullable=True,
        comment='更新者ID'
    )

    @hybrid_property
    def is_new(self) -> bool:
        """检查模型是否为新创建的（未保存到数据库）"""
        return self.id is None

    @hybrid_method
    def is_recent(self, days: int) -> bool:
        """检查是否为最近创建/更新的记录"""
        if self.created_at is None:
            return False
        return (datetime.now() - self.created_at).days <= days

    @is_recent.expression
    def is_recent(cls, days: int):
        """数据库表达式版本"""
        return func.julianday('now') - func.julianday(cls.created_at) <= days

    @hybrid_property
    def is_deleted(self) -> bool:
        """检查是否已软删除"""
        return self.deleted_at is not None

    @hybrid_method
    def is_active(self) -> bool:
        """检查是否为活跃状态（未删除）"""
        return self.deleted_at is None

    @is_active.expression
    def is_active(cls):
        """数据库表达式版本"""
        return cls.deleted_at.is_(None)

    def update_timestamps(self):
        """更新时间戳"""
        now = datetime.now()
        if self.created_at is None:
            self.created_at = now
        self.updated_at = now

    def soft_delete(self, deleted_by: Optional[int] = None):
        """软删除记录"""
        self.deleted_at = datetime.now()
        if deleted_by:
            self.updated_by = deleted_by

    def restore(self, restored_by: Optional[int] = None):
        """恢复软删除的记录"""
        self.deleted_at = None
        if restored_by:
            self.updated_by = restored_by
