#!/usr/bin/env python3
"""
DeepWin User Model
使用SQLAlchemy ORM的用户数据模型，支持混合方法和关系
"""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import Column, String, Integer, Text, Index, Boolean
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy_utils import EmailType, PhoneNumberType, CountryType, URLType, ColorType

from .base_model import BaseModel, CommonFieldsMixin, Base
from ...config_manager import ConfigManager
from ...log_manager import LogManager

class UserModel(CommonFieldsMixin, Base, BaseModel):
    """用户模型类，使用SQLAlchemy ORM，支持混合方法和关系"""
    
    __tablename__ = 'users'
    
    # 表级配置 - 只包含实际存在的字段
    __table_args__ = (
        Index('idx_user_username', 'username'),
        Index('idx_user_email', 'email'),
        Index('idx_user_city', 'city'),
        Index('idx_user_company', 'company'),
        Index('idx_user_industry', 'industry'),
        Index('idx_user_country', 'country'),
        # 注意：deleted_at 字段在 CommonFieldsMixin 中定义，这里不需要重复定义
    )
    
    # 用户基本信息
    username = Column(
        String(100),
        nullable=False,
        unique=True,
        comment='用户名'
    )
    
    email = Column(
        EmailType,
        nullable=True,
        unique=True,
        comment='邮箱地址（自动验证格式）'
    )
    
    phone = Column(
        PhoneNumberType,
        nullable=True,
        comment='手机号码（自动验证格式，支持国际号码）'
    )
    
    # 位置信息
    country = Column(
        CountryType,
        nullable=True,
        comment='国家（ISO 3166-1标准）'
    )
    
    city = Column(
        String(100),
        nullable=True,
        comment='所在城市'
    )
    
    company = Column(
        String(200),
        nullable=True,
        comment='公司名称'
    )
    
    industry = Column(
        String(100),
        nullable=True,
        comment='所属行业'
    )
    
    position = Column(
        String(100),
        nullable=True,
        comment='职位'
    )
    
    # 头像信息
    avatar_path = Column(
        String(500),
        nullable=True,
        comment='头像文件路径'
    )
    
    # 扩展信息
    website = Column(
        URLType,
        nullable=True,
        comment='个人网站（自动验证URL格式）'
    )
    
    theme_color = Column(
        ColorType,
        nullable=True,
        comment='主题颜色（自动验证颜色格式）'
    )
    
    # 状态信息
    status_active = Column(
        Boolean,
        default=True,
        comment='是否激活'
    )
    
    # 关系定义 - 注释掉以避免循环依赖问题
    # 外键关系已经足够，反向关系在子模型中定义
    # needs = relationship("NeedModel", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    # resources = relationship("ResourceModel", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")
    # photos = relationship("PhotoModel", back_populates="user", cascade="all, delete-orphan", lazy="dynamic")

    def __init__(self, config_manager: ConfigManager = None, log_manager: LogManager = None, **kwargs):
        # 初始化BaseModel
        BaseModel.__init__(self, config_manager, log_manager, **kwargs)

    def validate(self) -> bool:
        """验证模型数据"""
        if not self.username:
            return False
        
        # EmailType, PhoneNumberType, URLType, ColorType 会自动验证格式
        # 这里只需要检查业务逻辑
        
        return True

    @hybrid_property
    def display_name(self) -> str:
        """获取显示名称"""
        return self.username or self.email or '未知用户'

    @hybrid_property
    def full_info(self) -> str:
        """获取完整信息"""
        info_parts = []
        if self.username:
            info_parts.append(f"用户名: {self.username}")
        if self.email:
            info_parts.append(f"邮箱: {self.email}")
        if self.phone:
            info_parts.append(f"电话: {self.phone}")
        if self.country:
            info_parts.append(f"国家: {self.country}")
        if self.city:
            info_parts.append(f"城市: {self.city}")
        if self.company:
            info_parts.append(f"公司: {self.company}")
        if self.industry:
            info_parts.append(f"行业: {self.industry}")
        if self.position:
            info_parts.append(f"职位: {self.position}")
        if self.website:
            info_parts.append(f"网站: {self.website}")
        
        return " | ".join(info_parts) if info_parts else "无信息"

    @hybrid_property
    def profile_completion_rate(self) -> float:
        """获取资料完整度"""
        required_fields = ['username', 'email', 'phone', 'country', 'city', 'company', 'industry', 'position']
        filled_fields = sum(1 for field in required_fields if getattr(self, field))
        return filled_fields / len(required_fields)

    @hybrid_method
    def is_complete_profile(self, min_rate: float = 0.7) -> bool:
        """检查资料是否完整"""
        return self.profile_completion_rate >= min_rate

    @is_complete_profile.expression
    def is_complete_profile(cls, min_rate: float = 0.7):
        """数据库表达式版本"""
        # 这里简化处理，实际可以根据需要实现更复杂的逻辑
        return func.coalesce(cls.username, '') != ''

    @hybrid_method
    def is_senior_position(self) -> bool:
        """检查是否为高级职位"""
        senior_positions = ['经理', '总监', '主管', '专家', '高级', '资深']
        if not self.position:
            return False
        return any(pos in self.position for pos in senior_positions)

    @is_senior_position.expression
    def is_senior_position(cls):
        """数据库表达式版本"""
        return func.instr(func.coalesce(cls.position, ''), '经理') > 0

    @hybrid_method
    def has_avatar(self) -> bool:
        """检查是否有头像"""
        return bool(self.avatar_path)

    @has_avatar.expression
    def has_avatar(cls):
        """数据库表达式版本"""
        return func.coalesce(cls.avatar_path, '') != ''

    @hybrid_method
    def is_international_user(self) -> bool:
        """检查是否为国际用户（非中国）"""
        if not self.country:
            return False
        # 处理 CountryType 和字符串两种情况
        country_code = self.country.code if hasattr(self.country, 'code') else str(self.country)
        return country_code != 'CN'

    @is_international_user.expression
    def is_international_user(cls):
        """数据库表达式版本"""
        return func.coalesce(cls.country, '') != 'CN'

    @hybrid_method
    def has_valid_contact(self) -> bool:
        """检查是否有有效的联系方式"""
        return bool(self.email or self.phone)

    @has_valid_contact.expression
    def has_valid_contact(cls):
        """数据库表达式版本"""
        return (func.coalesce(cls.email, '') != '') | (func.coalesce(cls.phone, '') != '')

    @hybrid_method
    def has_website(self) -> bool:
        """检查是否有个人网站"""
        return bool(self.website)

    @has_website.expression
    def has_website(cls):
        """数据库表达式版本"""
        return func.coalesce(cls.website, '') != ''

    @hybrid_method
    def has_theme_color(self) -> bool:
        """检查是否设置了主题颜色"""
        return bool(self.theme_color)

    @has_theme_color.expression
    def has_theme_color(cls):
        """数据库表达式版本"""
        return func.coalesce(cls.theme_color, '') != ''

    @classmethod
    def create_sample_user(cls, config_manager=None, log_manager=None):
        """创建示例用户"""
        return cls(
            config_manager=config_manager,
            log_manager=log_manager,
            username="张三",
            email="zhangsan@example.com",
            phone="+86-138-0013-8000",
            country="CN",
            city="北京",
            company="科技有限公司",
            industry="互联网",
            position="软件工程师",
            avatar_path="/avatars/zhangsan.jpg",
            website="https://zhangsan.dev",
            theme_color="#3B82F6",
            status_active=True
        )

    @classmethod
    def create_international_user(cls, config_manager=None, log_manager=None):
        """创建国际用户示例"""
        return cls(
            config_manager=config_manager,
            log_manager=log_manager,
            username="John Smith",
            email="john.smith@company.com",
            phone="+1-555-123-4567",
            country="US",
            city="San Francisco",
            company="Tech Corp",
            industry="Technology",
            position="Senior Engineer",
            avatar_path="/avatars/john.jpg",
            website="https://johnsmith.dev",
            theme_color="#10B981",
            status_active=True
        )
