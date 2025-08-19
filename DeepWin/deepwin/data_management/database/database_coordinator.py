#!/usr/bin/env python3
"""
DeepWin Database Coordinator
数据库协调器，管理多个数据库的协同工作
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional
from PySide6.QtCore import QObject, Signal

from .database_factory import DatabaseFactory
from .base_database import BaseDatabase
from ..config_manager import ConfigManager
from ..log_manager import LogManager
from ..log_manager import LogManager


class DatabaseCoordinator(QObject):
    """数据库协调器，管理多个数据库的协同工作"""
    
    # 信号定义
    databases_connected = Signal(list)  # 数据库连接成功
    databases_disconnected = Signal(list)  # 数据库断开连接
    transaction_started = Signal(list)  # 事务开始
    transaction_committed = Signal(list)  # 事务提交
    transaction_rollback = Signal(list)  # 事务回滚
    operation_completed = Signal(str, str)  # 操作完成
    error_occurred = Signal(str, str)  # 错误发生

    def __init__(self, config_manager: ConfigManager, log_manager: LogManager, parent=None):
        """
        初始化数据库协调器
        
        Args:
            config_manager: 配置管理器实例
            log_manager: 日志管理器实例
            parent: 父对象
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.log_manager = log_manager
        self.logger = log_manager.get_logger(__name__)
        
        # 创建数据库工厂
        self.factory = DatabaseFactory(config_manager, log_manager)
        
        # 数据库实例管理
        self.databases = {}
        
        # 事务管理
        self.transaction_databases = set()
        self.in_transaction = False

    async def setup_databases(self):
        """设置和初始化数据库"""
        try:
            # 从配置获取数据库配置
            db_configs = self.config_manager.get('database', {})
            
            # 创建SQLite数据库
            if 'sqlite' in db_configs:
                sqlite_db = self.factory.create_database(
                    'sqlite', 
                    'sqlite_main',
                    **db_configs.get('sqlite', {})
                )
                if sqlite_db:
                    self.databases['sqlite'] = sqlite_db
                    self.logger.info("SQLite数据库创建成功")
            
            # 创建Qdrant数据库
            if 'qdrant' in db_configs:
                qdrant_db = self.factory.create_database(
                    'qdrant', 
                    'qdrant_main',
                    **db_configs.get('qdrant', {})
                )
                if qdrant_db:
                    self.databases['qdrant'] = qdrant_db
                    self.logger.info("Qdrant数据库创建成功")
            
            self.logger.info(f"数据库设置完成，共创建 {len(self.databases)} 个数据库")
            
        except Exception as e:
            self.logger.error(f"数据库设置失败: {e}")
            self.error_occurred.emit("setup", str(e))

    async def connect_all_databases(self) -> bool:
        """连接所有数据库"""
        try:
            success_count = 0
            total_count = len(self.databases)
            
            for name, database in self.databases.items():
                try:
                    if await database.connect():
                        success_count += 1
                        self.logger.info(f"数据库 {name} 连接成功")
                    else:
                        self.logger.error(f"数据库 {name} 连接失败")
                except Exception as e:
                    self.logger.error(f"数据库 {name} 连接异常: {e}")
            
            if success_count == total_count:
                self.databases_connected.emit(list(self.databases.keys()))
                self.logger.info(f"所有数据库连接成功: {success_count}/{total_count}")
                return True
            else:
                self.logger.warning(f"部分数据库连接失败: {success_count}/{total_count}")
                return False
                
        except Exception as e:
            self.logger.error(f"连接数据库失败: {e}")
            self.error_occurred.emit("connect", str(e))
            return False

    async def disconnect_all_databases(self) -> bool:
        """断开所有数据库连接"""
        try:
            success_count = 0
            total_count = len(self.databases)
            
            for name, database in self.databases.items():
                try:
                    if await database.disconnect():
                        success_count += 1
                        self.logger.info(f"数据库 {name} 断开连接成功")
                    else:
                        self.logger.error(f"数据库 {name} 断开连接失败")
                except Exception as e:
                    self.logger.error(f"数据库 {name} 断开连接异常: {e}")
            
            if success_count == total_count:
                self.databases_disconnected.emit(list(self.databases.keys()))
                self.logger.info(f"所有数据库断开连接成功: {success_count}/{total_count}")
                return True
            else:
                self.logger.warning(f"部分数据库断开连接失败: {success_count}/{total_count}")
                return False
                
        except Exception as e:
            self.logger.error(f"断开数据库连接失败: {e}")
            self.error_occurred.emit("disconnect", str(e))
            return False

    async def begin_transaction(self, database_names: Optional[List[str]] = None) -> bool:
        """
        开始事务
        
        Args:
            database_names: 要开始事务的数据库名称列表，如果为None则对所有数据库开始事务
            
        Returns:
            bool: 是否成功开始事务
        """
        try:
            if self.in_transaction:
                self.logger.warning("事务已在进行中")
                return False
            
            # 确定要开始事务的数据库
            target_databases = database_names or list(self.databases.keys())
            self.transaction_databases = set(target_databases)
            
            # 对所有目标数据库开始事务
            success_count = 0
            for name in target_databases:
                if name in self.databases:
                    database = self.databases[name]
                    if await database.begin_transaction():
                        success_count += 1
                    else:
                        self.logger.error(f"数据库 {name} 开始事务失败")
            
            if success_count == len(target_databases):
                self.in_transaction = True
                self.transaction_started.emit(target_databases)
                self.logger.info(f"事务开始成功: {success_count}/{len(target_databases)} 个数据库")
                return True
            else:
                self.logger.error(f"部分数据库开始事务失败: {success_count}/{len(target_databases)}")
                # 回滚已开始的事务
                await self.rollback_transaction()
                return False
                
        except Exception as e:
            self.logger.error(f"开始事务失败: {e}")
            self.error_occurred.emit("begin_transaction", str(e))
            return False

    async def commit_transaction(self) -> bool:
        """提交事务"""
        try:
            if not self.in_transaction:
                self.logger.warning("没有进行中的事务")
                return False
            
            # 对所有事务数据库提交事务
            success_count = 0
            for name in self.transaction_databases:
                if name in self.databases:
                    database = self.databases[name]
                    if await database.commit_transaction():
                        success_count += 1
                    else:
                        self.logger.error(f"数据库 {name} 提交事务失败")
            
            if success_count == len(self.transaction_databases):
                self.in_transaction = False
                self.transaction_databases.clear()
                self.transaction_committed.emit(list(self.transaction_databases))
                self.logger.info("事务提交成功")
                return True
            else:
                self.logger.error(f"部分数据库提交事务失败: {success_count}/{len(self.transaction_databases)}")
                return False
                
        except Exception as e:
            self.logger.error(f"提交事务失败: {e}")
            self.error_occurred.emit("commit_transaction", str(e))
            return False

    async def rollback_transaction(self) -> bool:
        """回滚事务"""
        try:
            if not self.in_transaction:
                self.logger.warning("没有进行中的事务")
                return False
            
            # 对所有事务数据库回滚事务
            success_count = 0
            for name in self.transaction_databases:
                if name in self.databases:
                    database = self.databases[name]
                    if await database.rollback_transaction():
                        success_count += 1
                    else:
                        self.logger.error(f"数据库 {name} 回滚事务失败")
            
            self.in_transaction = False
            self.transaction_databases.clear()
            self.transaction_rollback.emit(list(self.transaction_databases))
            self.logger.info(f"事务回滚完成: {success_count}/{len(self.transaction_databases)} 个数据库")
            return True
                
        except Exception as e:
            self.logger.error(f"回滚事务失败: {e}")
            self.error_occurred.emit("rollback_transaction", str(e))
            return False

    async def execute_cross_database_operation(self, operations: List[Callable], *args, **kwargs) -> List[Any]:
        """
        执行跨数据库操作
        
        Args:
            operations: 操作函数列表
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            List[Any]: 操作结果列表
        """
        try:
            if not self.in_transaction:
                # 如果没有事务，自动开始一个
                if not await self.begin_transaction():
                    raise RuntimeError("无法开始事务")
                auto_transaction = True
            else:
                auto_transaction = False
            
            results = []
            try:
                # 执行所有操作
                for operation in operations:
                    result = await operation(*args, **kwargs)
                    results.append(result)
                
                # 如果自动开始的事务，自动提交
                if auto_transaction:
                    if not await self.commit_transaction():
                        raise RuntimeError("事务提交失败")
                
                self.operation_completed.emit("cross_database", f"成功执行 {len(operations)} 个操作")
                return results
                
            except Exception as e:
                # 如果自动开始的事务，自动回滚
                if auto_transaction:
                    await self.rollback_transaction()
                raise e
                
        except Exception as e:
            self.logger.error(f"跨数据库操作失败: {e}")
            self.error_occurred.emit("cross_database", str(e))
            raise

    def get_database(self, name: str) -> Optional[BaseDatabase]:
        """获取指定名称的数据库实例"""
        return self.databases.get(name)

    def get_all_databases(self) -> Dict[str, BaseDatabase]:
        """获取所有数据库实例"""
        return self.databases.copy()

    def get_database_status(self) -> Dict[str, Dict]:
        """获取所有数据库的状态信息"""
        status = {}
        for name, database in self.databases.items():
            status[name] = {
                'type': database.__class__.__name__,
                'connected': database.is_connected,
                'name': database.name,
                'in_transaction': name in self.transaction_databases
            }
        return status

    def is_transaction_active(self) -> bool:
        """检查是否有活跃的事务"""
        return self.in_transaction

    def get_transaction_databases(self) -> List[str]:
        """获取参与当前事务的数据库列表"""
        return list(self.transaction_databases)

    def __len__(self) -> int:
        """返回数据库数量"""
        return len(self.databases)

    def __contains__(self, name: str) -> bool:
        """检查是否包含指定名称的数据库"""
        return name in self.databases

    def __iter__(self):
        """迭代所有数据库"""
        return iter(self.databases.values())
