#!/usr/bin/env python3
"""
DeepWin Resource Model
使用SQLAlchemy ORM的资源数据模型，支持混合方法和关系
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, Integer, ForeignKey, Text, Index, Boolean
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base_model import BaseModel


class ResourceModel(BaseModel):
    """资源模型类，使用SQLAlchemy ORM，支持混合方法和关系"""
    
    __tablename__ = 'resources'
    
    # 表级配置
    __table_args__ = (
        Index('idx_resource_user_id', 'user_id'),
        Index('idx_resource_title', 'title'),
        Index('idx_resource_category', 'category'),
        Index('idx_resource_type', 'resource_type'),
        Index('idx_resource_status', 'status'),
    )
    
    # 资源类型常量
    TYPE_SKILL = 'skill'
    TYPE_MATERIAL = 'material'
    TYPE_NETWORK = 'network'
    TYPE_FINANCIAL = 'financial'
    TYPE_TIME = 'time'
    
    # 状态常量
    STATUS_AVAILABLE = 'available'
    STATUS_IN_USE = 'in_use'
    STATUS_MAINTENANCE = 'maintenance'
    STATUS_RETIRED = 'retired'
    
    # 基本信息
    user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        comment='用户ID'
    )
    
    title = Column(
        String(200),
        nullable=False,
        comment='资源标题'
    )
    
    description = Column(
        Text,
        nullable=True,
        comment='资源描述'
    )
    
    category = Column(
        String(100),
        nullable=True,
        comment='资源分类'
    )
    
    # 资源类型和状态
    resource_type = Column(
        String(100),
        nullable=False,
        default=TYPE_SKILL,
        comment='资源类型：skill-技能，material-物质，network-人脉，financial-财务，time-时间'
    )
    
    status = Column(
        String(50),
        nullable=False,
        default=STATUS_AVAILABLE,
        comment='状态：available-可用，in_use-使用中，maintenance-维护中，retired-已退役'
    )
    
    # 标签和备注
    tags = Column(
        String(500),
        nullable=True,
        comment='标签，逗号分隔'
    )
    
    notes = Column(
        Text,
        nullable=True,
        comment='备注信息'
    )
    
    # 关系定义
    user = relationship("UserModel", back_populates="resources")

    def __init__(self, config_manager, **kwargs):
        super().__init__(config_manager, **kwargs)

    def validate(self) -> bool:
        """验证模型数据"""
        if not self.title:
            self.validation_error.emit('title', '资源标题不能为空')
            return False
        
        if not self.user_id:
            self.validation_error.emit('user_id', '用户ID不能为空')
            return False
        
        if self.resource_type not in [self.TYPE_SKILL, self.TYPE_MATERIAL, 
                                    self.TYPE_NETWORK, self.TYPE_FINANCIAL, self.TYPE_TIME]:
            self.validation_error.emit('resource_type', '资源类型无效')
            return False
        
        if self.status not in [self.STATUS_AVAILABLE, self.STATUS_IN_USE, 
                             self.STATUS_MAINTENANCE, self.STATUS_RETIRED]:
            self.validation_error.emit('status', '状态值无效')
            return False
        
        return True

    @hybrid_property
    def resource_type_text(self) -> str:
        """获取资源类型文本"""
        type_map = {
            self.TYPE_SKILL: '技能',
            self.TYPE_MATERIAL: '物质',
            self.TYPE_NETWORK: '人脉',
            self.TYPE_FINANCIAL: '财务',
            self.TYPE_TIME: '时间'
        }
        return type_map.get(self.resource_type, '未知类型')

    @hybrid_property
    def status_text(self) -> str:
        """获取状态文本"""
        status_map = {
            self.STATUS_AVAILABLE: '可用',
            self.STATUS_IN_USE: '使用中',
            self.STATUS_MAINTENANCE: '维护中',
            self.STATUS_RETIRED: '已退役'
        }
        return status_map.get(self.status, '未知状态')

    @hybrid_property
    def is_available(self) -> bool:
        """检查是否可用"""
        return self.status == self.STATUS_AVAILABLE

    @hybrid_property
    def is_in_use(self) -> bool:
        """检查是否正在使用"""
        return self.status == self.STATUS_IN_USE

    @hybrid_property
    def is_skill(self) -> bool:
        """检查是否为技能类型"""
        return self.resource_type == self.TYPE_SKILL

    @hybrid_method
    def is_type(self, resource_type: str) -> bool:
        """检查是否为指定类型"""
        return self.resource_type == resource_type

    @is_type.expression
    def is_type(cls, resource_type: str):
        """数据库表达式版本"""
        return cls.resource_type == resource_type

    @hybrid_method
    def is_status(self, status: str) -> bool:
        """检查是否为指定状态"""
        return self.status == status

    @is_status.expression
    def is_status(cls, status: str):
        """数据库表达式版本"""
        return cls.status == status

    @hybrid_method
    def has_tag(self, tag: str) -> bool:
        """检查是否包含指定标签"""
        if not self.tags:
            return False
        return tag in self.get_tags_list()

    @has_tag.expression
    def has_tag(cls, tag: str):
        """数据库表达式版本"""
        return func.instr(func.coalesce(cls.tags, ''), tag) > 0

    @hybrid_method
    def is_recently_created(self, days: int = 30) -> bool:
        """检查是否为最近创建的资源"""
        if self.created_at is None:
            return False
        return (datetime.now() - self.created_at).days <= days

    @is_recently_created.expression
    def is_recently_created(cls, days: int = 30):
        """数据库表达式版本"""
        return func.julianday('now') - func.julianday(cls.created_at) <= days

    def mark_as_in_use(self):
        """标记为使用中"""
        if self.status == self.STATUS_AVAILABLE:
            self.status = self.STATUS_IN_USE
            self.update_timestamps()

    def mark_as_available(self):
        """标记为可用"""
        if self.status in [self.STATUS_IN_USE, self.STATUS_MAINTENANCE]:
            self.status = self.STATUS_AVAILABLE
            self.update_timestamps()

    def mark_as_maintenance(self):
        """标记为维护中"""
        if self.status in [self.STATUS_AVAILABLE, self.STATUS_IN_USE]:
            self.status = self.STATUS_MAINTENANCE
            self.update_timestamps()

    def retire(self):
        """退役资源"""
        self.status = self.STATUS_RETIRED
        self.update_timestamps()

    def add_tag(self, tag: str):
        """添加标签"""
        if tag and tag not in self.get_tags_list():
            current_tags = self.get_tags_list()
            current_tags.append(tag)
            self.tags = ','.join(current_tags)

    def remove_tag(self, tag: str):
        """移除标签"""
        current_tags = self.get_tags_list()
        if tag in current_tags:
            current_tags.remove(tag)
            self.tags = ','.join(current_tags)

    def get_tags_list(self) -> List[str]:
        """获取标签列表"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []

    def get_tags_text(self) -> str:
        """获取标签文本"""
        tags_list = self.get_tags_list()
        return ', '.join(tags_list) if tags_list else '无标签'

    @classmethod
    def create_sample_resource(cls, config_manager, user_id: int):
        """创建示例资源"""
        return cls(
            config_manager=config_manager,
            user_id=user_id,
            title="Python编程技能",
            description="熟练掌握Python语言及其常用库",
            category="编程",
            resource_type=cls.TYPE_SKILL,
            status=cls.STATUS_AVAILABLE,
            tags="编程,Python,技术",
            notes="通过自学和项目实践获得"
        )
