#!/usr/bin/env python3
"""
DeepWin Photo Model
使用SQLAlchemy ORM的照片数据模型，支持混合方法和关系
"""

from datetime import datetime
from typing import List, Optional, Any
from sqlalchemy import Column, String, Integer, ForeignKey, Text, Index, DateTime
from sqlalchemy.ext.hybrid import hybrid_method, hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy_utils import URLType, IPAddressType, ColorType, JSONType

from .base_model import BaseModel, CommonFieldsMixin, Base
from ...config_manager import ConfigManager
from ...log_manager import LogManager


class PhotoModel(CommonFieldsMixin, Base, BaseModel):
    """照片模型类，使用SQLAlchemy ORM，支持混合方法和关系"""
    
    __tablename__ = 'photos'
    
    # 表级配置
    __table_args__ = (
        Index('idx_photo_user_id', 'user_id'),
        Index('idx_photo_file_name', 'file_name'),
        Index('idx_photo_location', 'location'),
        Index('idx_photo_taken_at', 'taken_at'),
        Index('idx_photo_mime_type', 'mime_type'),
        Index('idx_photo_deleted_at', 'deleted_at'),  # 软删除索引
    )
    
    # 基本信息
    user_id = Column(
        Integer,
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        comment='用户ID'
    )
    
    file_path = Column(
        String(500),
        nullable=False,
        comment='文件路径'
    )
    
    file_name = Column(
        String(200),
        nullable=False,
        comment='文件名'
    )
    
    file_size = Column(
        Integer,
        nullable=True,
        comment='文件大小（字节）'
    )
    
    mime_type = Column(
        String(100),
        nullable=True,
        comment='MIME类型'
    )
    
    # 描述信息
    description = Column(
        Text,
        nullable=True,
        comment='照片描述'
    )
    
    tags = Column(
        String(500),
        nullable=True,
        comment='标签，逗号分隔'
    )
    
    location = Column(
        String(200),
        nullable=True,
        comment='拍摄位置'
    )
    
    taken_at = Column(
        DateTime,
        nullable=True,
        comment='拍摄时间'
    )
    
    # 扩展信息
    source_url = Column(
        URLType,
        nullable=True,
        comment='图片来源URL（自动验证URL格式）'
    )
    
    device_ip = Column(
        IPAddressType,
        nullable=True,
        comment='拍摄设备IP地址（自动验证IP格式）'
    )
    
    dominant_color = Column(
        ColorType,
        nullable=True,
        comment='主要颜色（自动验证颜色格式）'
    )
    
    photo_metadata = Column(
        JSONType,
        nullable=True,
        comment='照片元数据（JSON格式）'
    )
    
    # 关系定义
    user = relationship("UserModel")

    def __init__(self, **kwargs):
        # 初始化BaseModel的属性
        self._changed_fields = set()
        self._original_values = {}
        
        # 直接设置属性，避免构造函数冲突
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        # 记录原始值用于变更检测
        if hasattr(self, '__table__'):
            self._original_values = self._get_current_values()

    def validate(self) -> bool:
        """验证模型数据"""
        if not self.file_path:
            self.validation_error.emit('file_path', '文件路径不能为空')
            return False
        
        if not self.file_name:
            self.validation_error.emit('file_name', '文件名不能为空')
            return False
        
        if not self.user_id:
            self.validation_error.emit('user_id', '用户ID不能为空')
            return False
        
        if self.file_size is not None and self.file_size < 0:
            self.validation_error.emit('file_size', '文件大小不能为负数')
            return False
        
        # URLType, IPAddressType, ColorType, JSONType 会自动验证格式
        
        return True

    @hybrid_property
    def file_size_formatted(self) -> str:
        """获取格式化的文件大小"""
        if self.file_size is None:
            return "未知"
        
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"

    @hybrid_property
    def file_extension(self) -> str:
        """获取文件扩展名"""
        if '.' in self.file_name:
            return self.file_name.split('.')[-1].lower()
        return ''

    @hybrid_property
    def is_image(self) -> bool:
        """检查是否为图片文件"""
        image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
        return self.file_extension in image_extensions

    @hybrid_property
    def is_video(self) -> bool:
        """检查是否为视频文件"""
        video_extensions = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv']
        return self.file_extension in video_extensions

    @hybrid_property
    def is_large_file(self) -> bool:
        """检查是否为大文件（>10MB）"""
        if self.file_size is None:
            return False
        return self.file_size > 10 * 1024 * 1024

    @hybrid_method
    def is_recent_photo(self, days: int = 30) -> bool:
        """检查是否为最近拍摄的照片"""
        if not self.taken_at:
            return False
        return (datetime.now() - self.taken_at).days <= days

    @is_recent_photo.expression
    def is_recent_photo(cls, days: int = 30):
        """数据库表达式版本"""
        return func.julianday('now') - func.julianday(cls.taken_at) <= days

    @hybrid_method
    def is_location(self, location: str) -> bool:
        """检查是否为指定位置拍摄"""
        if not self.location:
            return False
        return location.lower() in self.location.lower()

    @is_location.expression
    def is_location(cls, location: str):
        """数据库表达式版本"""
        return func.instr(func.lower(func.coalesce(cls.location, '')), location.lower()) > 0

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
    def is_mime_type(self, mime_type: str) -> bool:
        """检查是否为指定MIME类型"""
        if not self.mime_type:
            return False
        return mime_type.lower() in self.mime_type.lower()

    @is_mime_type.expression
    def is_mime_type(cls, mime_type: str):
        """数据库表达式版本"""
        return func.instr(func.lower(func.coalesce(cls.mime_type, '')), mime_type.lower()) > 0

    @hybrid_method
    def is_size_range(self, min_size: int, max_size: int) -> bool:
        """检查文件大小是否在指定范围内"""
        if self.file_size is None:
            return False
        return min_size <= self.file_size <= max_size

    @is_size_range.expression
    def is_size_range(cls, min_size: int, max_size: int):
        """数据库表达式版本"""
        return (cls.file_size >= min_size) & (cls.file_size <= max_size)

    @hybrid_method
    def has_source_url(self) -> bool:
        """检查是否有来源URL"""
        return bool(self.source_url)

    @has_source_url.expression
    def has_source_url(cls):
        """数据库表达式版本"""
        return func.coalesce(cls.source_url, '') != ''

    @hybrid_method
    def has_device_ip(self) -> bool:
        """检查是否有设备IP地址"""
        return bool(self.device_ip)

    @has_device_ip.expression
    def has_device_ip(cls):
        """数据库表达式版本"""
        return func.coalesce(cls.device_ip, '') != ''

    @hybrid_method
    def has_dominant_color(self) -> bool:
        """检查是否设置了主要颜色"""
        return bool(self.dominant_color)

    @has_dominant_color.expression
    def has_dominant_color(cls):
        """数据库表达式版本"""
        return func.coalesce(cls.dominant_color, '') != ''

    @hybrid_method
    def has_metadata(self) -> bool:
        """检查是否有元数据"""
        return bool(self.photo_metadata)

    @has_metadata.expression
    def has_metadata(cls):
        """数据库表达式版本"""
        return func.coalesce(cls.photo_metadata, '') != ''

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

    def set_metadata(self, key: str, value: Any):
        """设置元数据"""
        if self.photo_metadata is None:
            self.photo_metadata = {}
        self.photo_metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据"""
        if self.photo_metadata and key in self.photo_metadata:
            return self.photo_metadata[key]
        return default

    @classmethod
    def create_sample_photo(cls, user_id: int):
        """创建示例照片"""
        return cls(
            user_id=user_id,
            file_path="/photos/sample.jpg",
            file_name="sample.jpg",
            file_size=2048576,
            mime_type="image/jpeg",
            description="示例照片",
            tags="示例,测试",
            location="北京",
            taken_at=datetime.now(),
            source_url="https://example.com/photo",
            device_ip="192.168.1.100",
            dominant_color="#FF6B6B",
            photo_metadata={
                "camera": "iPhone 13",
                "iso": 100,
                "shutter_speed": "1/60",
                "aperture": "f/2.8"
            }
        )
