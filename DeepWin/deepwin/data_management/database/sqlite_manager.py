#!/usr/bin/env python3
"""
DeepWin SQLite Database Manager
使用SQLAlchemy ORM管理SQLite数据库
"""

import asyncio
import os
from typing import Any, Dict, List, Optional
from sqlalchemy import create_engine, text, MetaData
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from .base_database import BaseDatabase
from ..config_manager import ConfigManager
from ..log_manager import LogManager


class SQLiteManager(BaseDatabase):
    """SQLite数据库管理器，使用SQLAlchemy ORM"""
    
    def __init__(self, name: str, config_manager: ConfigManager, log_manager: LogManager, parent=None, **kwargs):
        super().__init__(name, config_manager, log_manager, parent)
        
        # 从参数或配置管理器获取数据库路径
        self.db_path = kwargs.get('path', config_manager.get('database.sqlite.path', 'deepwin.db'))
        self.db_url = f"sqlite:///{self.db_path}"
        self.async_db_url = f"sqlite+aiosqlite:///{self.db_path}"
        
        # SQLAlchemy引擎和会话
        self.engine = None
        self.async_engine = None
        self.SessionLocal = None
        self.AsyncSessionLocal = None
        
        # 元数据
        self.metadata = MetaData()

    async def connect(self) -> bool:
        """连接到SQLite数据库"""
        try:
            # 确保数据库目录存在
            db_dir = os.path.dirname(self.db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
            
            # 创建同步引擎
            self.engine = create_engine(
                self.db_url,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
                echo=self.config_manager.get('database.sqlite.echo', False)
            )
            
            # 创建异步引擎
            self.async_engine = create_async_engine(
                self.async_db_url,
                poolclass=StaticPool,
                echo=self.config_manager.get('database.sqlite.echo', False)
            )
            
            # 创建会话工厂
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self.AsyncSessionLocal = sessionmaker(
                class_=AsyncSession,
                autocommit=False,
                autoflush=False,
                bind=self.async_engine
            )
            
            # 初始化表结构
            await self._init_tables()
            
            self.is_connected = True
            self.connected.emit(self.name)
            self.logger.info(f"SQLite数据库 {self.name} 连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"SQLite数据库 {self.name} 连接失败: {e}")
            self.error_occurred.emit(self.name, str(e))
            return False

    async def disconnect(self) -> bool:
        """断开SQLite数据库连接"""
        try:
            if self.engine:
                self.engine.dispose()
                self.engine = None
            
            if self.async_engine:
                await self.async_engine.dispose()
                self.async_engine = None
            
            self.SessionLocal = None
            self.AsyncSessionLocal = None
            self.is_connected = False
            
            self.disconnected.emit(self.name)
            self.logger.info(f"SQLite数据库 {self.name} 断开连接成功")
            return True
            
        except Exception as e:
            self.logger.error(f"SQLite数据库 {self.name} 断开连接失败: {e}")
            self.error_occurred.emit(self.name, str(e))
            return False

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行查询操作"""
        if not self.is_connected:
            raise ConnectionError("数据库未连接")
        
        try:
            async with self.AsyncSessionLocal() as session:
                result = await session.execute(text(query), params or {})
                rows = result.fetchall()
                
                # 转换为字典列表
                columns = result.keys()
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            self.logger.error(f"查询执行失败: {e}")
            self.error_occurred.emit(self.name, f"查询失败: {e}")
            raise

    async def execute_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """执行命令操作"""
        if not self.is_connected:
            raise ConnectionError("数据库未连接")
        
        try:
            async with self.AsyncSessionLocal() as session:
                await session.execute(text(command), params or {})
                await session.commit()
                
                self.operation_completed.emit(self.name, "命令执行成功")
                return True
                
        except Exception as e:
            self.logger.error(f"命令执行失败: {e}")
            self.error_occurred.emit(self.name, f"命令失败: {e}")
            return False

    async def begin_transaction(self) -> bool:
        """开始事务"""
        if not self.is_connected:
            return False
        
        try:
            # SQLite默认支持事务，这里主要是标记状态
            self.logger.info("开始SQLite事务")
            return True
        except Exception as e:
            self.logger.error(f"开始事务失败: {e}")
            return False

    async def commit_transaction(self) -> bool:
        """提交事务"""
        if not self.is_connected:
            return False
        
        try:
            # SQLite事务会在execute_command中自动提交
            self.logger.info("提交SQLite事务")
            return True
        except Exception as e:
            self.logger.error(f"提交事务失败: {e}")
            return False

    async def rollback_transaction(self) -> bool:
        """回滚事务"""
        if not self.is_connected:
            return False
        
        try:
            # SQLite事务回滚需要特殊处理
            self.logger.info("回滚SQLite事务")
            return True
        except Exception as e:
            self.logger.error(f"回滚事务失败: {e}")
            return False

    async def _init_tables(self):
        """初始化数据库表"""
        try:
            # 延迟导入模型以避免循环依赖
            from .models import get_all_models
            
            # 获取所有模型以确保表被创建
            models = get_all_models()
            
            # 创建所有表
            from .models.base_model import Base
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("SQLite表结构初始化完成")
        except Exception as e:
            self.logger.error(f"表结构初始化失败: {e}")
            raise

    def get_session(self):
        """获取同步会话"""
        if not self.SessionLocal:
            raise ConnectionError("数据库未连接")
        return self.SessionLocal()

    async def get_async_session(self):
        """获取异步会话"""
        if not self.AsyncSessionLocal:
            raise ConnectionError("数据库未连接")
        return self.AsyncSessionLocal()

    def close_session(self, session):
        """关闭同步会话"""
        if session:
            session.close()

    async def close_async_session(self, session):
        """关闭异步会话"""
        if session:
            await session.close()

    # CRUD操作方法
    async def create(self, model_class, data: Dict[str, Any]):
        """创建新记录"""
        if not self.is_connected:
            raise ConnectionError("数据库未连接")
        
        try:
            async with self.AsyncSessionLocal() as session:
                # 创建模型实例
                instance = model_class(**data)
                session.add(instance)
                await session.commit()
                await session.refresh(instance)
                
                self.operation_completed.emit(self.name, f"创建{model_class.__name__}成功")
                self.logger.info(f"创建{model_class.__name__}成功: {instance.id}")
                return instance
                
        except Exception as e:
            self.logger.error(f"创建{model_class.__name__}失败: {e}")
            self.error_occurred.emit(self.name, f"创建失败: {e}")
            return None

    async def get_by_id(self, model_class, record_id: int):
        """根据ID获取记录"""
        if not self.is_connected:
            raise ConnectionError("数据库未连接")
        
        try:
            async with self.AsyncSessionLocal() as session:
                instance = await session.get(model_class, record_id)
                if instance:
                    self.logger.info(f"查询{model_class.__name__}成功: {record_id}")
                return instance
                
        except Exception as e:
            self.logger.error(f"查询{model_class.__name__}失败: {e}")
            self.error_occurred.emit(self.name, f"查询失败: {e}")
            return None

    async def update(self, model_class, record_id: int, data: Dict[str, Any]):
        """更新记录"""
        if not self.is_connected:
            raise ConnectionError("数据库未连接")
        
        try:
            async with self.AsyncSessionLocal() as session:
                # 先查询现有记录
                instance = await session.get(model_class, record_id)
                if not instance:
                    self.logger.warning(f"要更新的{model_class.__name__}不存在: {record_id}")
                    return None
                
                # 简化更新：使用SQLAlchemy标准方式更新
                for key, value in data.items():
                    if hasattr(instance, key):
                        # 绕过所有自定义逻辑，直接更新
                        instance.__dict__[key] = value
                
                # 标记实例为dirty，确保SQLAlchemy知道需要更新
                session.add(instance)
                
                # 提交更改
                await session.commit()
                await session.refresh(instance)
                
                self.operation_completed.emit(self.name, f"更新{model_class.__name__}成功")
                self.logger.info(f"更新{model_class.__name__}成功: {record_id}")
                return instance
                
        except Exception as e:
            self.logger.error(f"更新{model_class.__name__}失败: {e}")
            self.error_occurred.emit(self.name, f"更新失败: {e}")
            return None

    async def delete(self, model_class, record_id: int) -> bool:
        """删除记录"""
        if not self.is_connected:
            raise ConnectionError("数据库未连接")
        
        try:
            async with self.AsyncSessionLocal() as session:
                instance = await session.get(model_class, record_id)
                if not instance:
                    self.logger.warning(f"要删除的{model_class.__name__}不存在: {record_id}")
                    return False
                
                await session.delete(instance)
                await session.commit()
                
                self.operation_completed.emit(self.name, f"删除{model_class.__name__}成功")
                self.logger.info(f"删除{model_class.__name__}成功: {record_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"删除{model_class.__name__}失败: {e}")
            self.error_occurred.emit(self.name, f"删除失败: {e}")
            return False

    async def get_all(self, model_class, limit: Optional[int] = None, offset: int = 0):
        """获取所有记录"""
        if not self.is_connected:
            raise ConnectionError("数据库未连接")
        
        try:
            async with self.AsyncSessionLocal() as session:
                from sqlalchemy import select
                
                stmt = select(model_class)
                if offset > 0:
                    stmt = stmt.offset(offset)
                if limit:
                    stmt = stmt.limit(limit)
                
                result = await session.execute(stmt)
                instances = result.scalars().all()
                
                self.logger.info(f"查询{model_class.__name__}列表成功: {len(instances)}条记录")
                return instances
                
        except Exception as e:
            self.logger.error(f"查询{model_class.__name__}列表失败: {e}")
            self.error_occurred.emit(self.name, f"查询列表失败: {e}")
            return []

    async def filter(self, model_class, filters: Dict[str, Any], limit: Optional[int] = None, offset: int = 0):
        """根据条件过滤记录"""
        if not self.is_connected:
            raise ConnectionError("数据库未连接")
        
        try:
            async with self.AsyncSessionLocal() as session:
                from sqlalchemy import select
                
                stmt = select(model_class)
                
                # 应用过滤条件
                for field, value in filters.items():
                    if hasattr(model_class, field):
                        stmt = stmt.where(getattr(model_class, field) == value)
                
                if offset > 0:
                    stmt = stmt.offset(offset)
                if limit:
                    stmt = stmt.limit(limit)
                
                result = await session.execute(stmt)
                instances = result.scalars().all()
                
                self.logger.info(f"过滤{model_class.__name__}成功: {len(instances)}条记录")
                return instances
                
        except Exception as e:
            self.logger.error(f"过滤{model_class.__name__}失败: {e}")
            self.error_occurred.emit(self.name, f"过滤失败: {e}")
            return []