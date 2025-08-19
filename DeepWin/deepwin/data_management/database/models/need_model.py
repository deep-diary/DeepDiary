#!/usr/bin/env python3
"""
DeepWin Need Model
使用SQLAlchemy ORM的需求数据模型，支持混合方法和关系
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Index, Boolean
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base_model import BaseModel
from ...config_manager import ConfigManager
from ...log_manager import LogManager

class NeedModel(BaseModel):
    """需求模型类，使用SQLAlchemy ORM，支持混合方法和关系"""
    
    __tablename__ = 'needs'
    
    # 表级配置
    __table_args__ = (
        Index('idx_need_user_id', 'user_id'),
        Index('idx_need_title', 'title'),
        Index('idx_need_category', 'category'),
        Index('idx_need_priority', 'priority'),
        Index('idx_need_status', 'status'),
        Index('idx_need_deadline', 'deadline'),
    )
    
    # 状态常量
    STATUS_ACTIVE = 'active'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_ON_HOLD = 'on_hold'
    
    # 优先级常量
    PRIORITY_LOW = 1
    PRIORITY_MEDIUM = 2
    PRIORITY_HIGH = 3
    PRIORITY_URGENT = 4
    
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
        comment='需求标题'
    )
    
    description = Column(
        Text,
        nullable=True,
        comment='需求描述'
    )
    
    category = Column(
        String(100),
        nullable=True,
        comment='需求分类'
    )
    
    # 优先级和状态
    priority = Column(
        Integer,
        nullable=False,
        default=PRIORITY_MEDIUM,
        comment='优先级：1-低，2-中，3-高，4-紧急'
    )
    
    status = Column(
        String(50),
        nullable=False,
        default=STATUS_ACTIVE,
        comment='状态：active-进行中，completed-已完成，cancelled-已取消，on_hold-暂停中'
    )
    
    # 时间相关
    deadline = Column(
        DateTime,
        nullable=True,
        comment='截止日期'
    )
    
    completion_time = Column(
        DateTime,
        nullable=True,
        comment='完成时间'
    )
    
    # 其他信息
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
    
    progress = Column(
        Float,
        nullable=False,
        default=0.0,
        comment='进度：0.0-1.0'
    )
    
    # 关系定义
    user = relationship("UserModel", back_populates="needs")

    def __init__(self, config_manager: ConfigManager = None, log_manager: LogManager = None, **kwargs):
        super().__init__(config_manager, log_manager, **kwargs)

    def validate(self) -> bool:
        """验证模型数据"""
        if not self.title:
            self.validation_error.emit('title', '需求标题不能为空')
            return False
        
        if not self.user_id:
            self.validation_error.emit('user_id', '用户ID不能为空')
            return False
        
        if self.priority not in [self.PRIORITY_LOW, self.PRIORITY_MEDIUM, 
                               self.PRIORITY_HIGH, self.PRIORITY_URGENT]:
            self.validation_error.emit('priority', '优先级值无效')
            return False
        
        if self.status not in [self.STATUS_ACTIVE, self.STATUS_COMPLETED, 
                             self.STATUS_CANCELLED, self.STATUS_ON_HOLD]:
            self.validation_error.emit('status', '状态值无效')
            return False
        
        if self.progress < 0.0 or self.progress > 1.0:
            self.validation_error.emit('progress', '进度值必须在0.0到1.0之间')
            return False
        
        return True

    @hybrid_property
    def status_text(self) -> str:
        """获取状态文本"""
        status_map = {
            self.STATUS_ACTIVE: '进行中',
            self.STATUS_COMPLETED: '已完成',
            self.STATUS_CANCELLED: '已取消',
            self.STATUS_ON_HOLD: '暂停中'
        }
        return status_map.get(self.status, '未知状态')

    @hybrid_property
    def priority_text(self) -> str:
        """获取优先级文本"""
        priority_map = {
            self.PRIORITY_LOW: '低',
            self.PRIORITY_MEDIUM: '中',
            self.PRIORITY_HIGH: '高',
            self.PRIORITY_URGENT: '紧急'
        }
        return priority_map.get(self.priority, '未知优先级')

    @hybrid_property
    def is_overdue(self) -> bool:
        """检查是否逾期"""
        if not self.deadline or self.status == self.STATUS_COMPLETED:
            return False
        return datetime.now() > self.deadline

    @hybrid_property
    def is_completed(self) -> bool:
        """检查是否已完成"""
        return self.status == self.STATUS_COMPLETED

    @hybrid_property
    def is_high_priority(self) -> bool:
        """检查是否为高优先级"""
        return self.priority >= self.PRIORITY_HIGH

    @hybrid_method
    def is_urgent(self) -> bool:
        """检查是否为紧急需求"""
        return self.priority == self.PRIORITY_URGENT

    @is_urgent.expression
    def is_urgent(cls):
        """数据库表达式版本"""
        return cls.priority == cls.PRIORITY_URGENT

    @hybrid_method
    def is_due_soon(self, days: int = 7) -> bool:
        """检查是否即将到期"""
        if not self.deadline or self.status == self.STATUS_COMPLETED:
            return False
        days_until_deadline = (self.deadline - datetime.now()).days
        return 0 <= days_until_deadline <= days

    @is_due_soon.expression
    def is_due_soon(cls, days: int = 7):
        """数据库表达式版本"""
        return func.julianday(cls.deadline) - func.julianday('now') <= days

    @hybrid_method
    def has_progress(self, min_progress: float = 0.1) -> bool:
        """检查是否有进展"""
        return self.progress >= min_progress

    @has_progress.expression
    def has_progress(cls, min_progress: float = 0.1):
        """数据库表达式版本"""
        return cls.progress >= min_progress

    def complete(self, completion_time: Optional[datetime] = None):
        """标记为已完成"""
        self.status = self.STATUS_COMPLETED
        self.progress = 1.0
        self.completion_time = completion_time or datetime.now()
        self.update_timestamps()

    def update_progress(self, progress: float):
        """更新进度"""
        if 0.0 <= progress <= 1.0:
            self.progress = progress
            if progress >= 1.0:
                self.status = self.STATUS_COMPLETED
            self.update_timestamps()
        else:
            raise ValueError("进度值必须在0.0到1.0之间")

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
    def create_sample_need(cls, config_manager=None, log_manager=None, user_id: int = 1):
        """创建示例需求"""
        return cls(
            config_manager=config_manager,
            log_manager=log_manager,
            user_id=user_id,
            title="提升专业技能",
            description="学习新的编程语言和框架，提升技术能力",
            category="技能提升",
            priority=cls.PRIORITY_HIGH,
            status=cls.STATUS_ACTIVE,
            deadline=datetime.now().replace(year=datetime.now().year + 1),
            tags="学习,技术,成长",
            notes="计划参加在线课程和项目实践",
            progress=0.3
        )
