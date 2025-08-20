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

    @property
    def session(self):
        """获取同步会话"""
        if not self.is_connected:
            raise ConnectionError("数据库未连接")
        return self.SessionLocal()

    @property
    def async_session(self):
        """获取异步会话"""
        if not self.is_connected:
            raise ConnectionError("数据库未连接")
        return self.AsyncSessionLocal()

    async def insert_model(self, model_instance) -> bool:
        """插入模型实例"""
        if not self.is_connected:
            return False
        
        try:
            async with self.AsyncSessionLocal() as session:
                session.add(model_instance)
                await session.commit()
                self.logger.info(f"模型实例插入成功: {type(model_instance).__name__}")
                return True
        except Exception as e:
            self.logger.error(f"模型实例插入失败: {e}")
            return False

    async def insert_models(self, model_instances: List) -> bool:
        """批量插入模型实例"""
        if not self.is_connected:
            return False
        
        try:
            async with self.AsyncSessionLocal() as session:
                session.add_all(model_instances)
                await session.commit()
                self.logger.info(f"批量插入成功: {len(model_instances)} 个实例")
                return True
        except Exception as e:
            self.logger.error(f"批量插入失败: {e}")
            return False

    async def query_models(self, model_class, filters: Optional[Dict] = None) -> List:
        """查询模型实例"""
        if not self.is_connected:
            return []
        
        try:
            async with self.AsyncSessionLocal() as session:
                query = session.query(model_class)
                
                # 应用过滤器
                if filters:
                    for key, value in filters.items():
                        if hasattr(model_class, key):
                            query = query.filter(getattr(model_class, key) == value)
                
                result = await session.execute(query)
                return result.scalars().all()
        except Exception as e:
            self.logger.error(f"查询模型失败: {e}")
            return []

    async def get_table_info(self) -> Dict[str, Any]:
        """获取表信息"""
        if not self.is_connected:
            return {}
        
        try:
            async with self.AsyncSessionLocal() as session:
                # 获取所有表名
                result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
                tables = [row[0] for row in result.fetchall()]
                
                table_info = {}
                for table in tables:
                    # 获取表结构
                    result = await session.execute(text(f"PRAGMA table_info({table})"))
                    columns = result.fetchall()
                    table_info[table] = {
                        'columns': [col[1] for col in columns],
                        'column_count': len(columns)
                    }
                
                return table_info
        except Exception as e:
            self.logger.error(f"获取表信息失败: {e}")
            return {}

    async def get_record_count(self, table_name: str) -> int:
        """获取表的记录数"""
        if not self.is_connected:
            return 0
        
        try:
            async with self.AsyncSessionLocal() as session:
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                count = result.scalar()
                return count or 0
        except Exception as e:
            self.logger.error(f"获取记录数失败: {e}")
            return 0

    def insert_model_sync(self, model_instance) -> bool:
        """同步插入模型实例"""
        if not self.is_connected:
            return False
        try:
            with self.session as session:
                session.add(model_instance)
                session.commit()
                self.logger.info(f"模型实例同步插入成功: {type(model_instance).__name__}")
                # 发送操作完成信号
                self.operation_completed.emit(self.name, f"插入成功: {type(model_instance).__name__}")
                return True
        except Exception as e:
            self.logger.error(f"模型实例同步插入失败: {e}")
            # 发送错误信号
            self.error_occurred.emit(self.name, f"插入失败: {e}")
            return False

    def insert_models_sync(self, model_instances: List) -> bool:
        """同步插入多个模型实例"""
        if not self.is_connected:
            return False
        try:
            with self.session as session:
                session.add_all(model_instances)
                session.commit()
                self.logger.info(f"批量模型实例同步插入成功: {len(model_instances)} 个")
                # 发送操作完成信号
                self.operation_completed.emit(self.name, f"批量插入成功: {len(model_instances)} 个")
                return True
        except Exception as e:
            self.logger.error(f"批量模型实例同步插入失败: {e}")
            # 发送错误信号
            self.error_occurred.emit(self.name, f"批量插入失败: {e}")
            return False