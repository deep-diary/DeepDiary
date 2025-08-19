#!/usr/bin/env python3
"""
DeepWin Database Factory
数据库工厂类，负责创建和管理不同类型的数据库实例
"""

from typing import Dict, Optional, Type
from .base_database import BaseDatabase
from .sqlite_manager import SQLiteManager
from .qdrant_manager import QdrantManager
from ..config_manager import ConfigManager
from ..log_manager import LogManager


class DatabaseFactory:
    """数据库工厂类，使用工厂模式创建数据库实例"""
    
    # 支持的数据库类型
    DATABASE_TYPES = {
        'sqlite': SQLiteManager,
        'qdrant': QdrantManager
    }
    
    def __init__(self, config_manager: ConfigManager, log_manager: LogManager):
        """
        初始化数据库工厂
        
        Args:
            config_manager: 配置管理器实例
            log_manager: 日志管理器实例
        """
        self.config_manager = config_manager
        self.log_manager = log_manager
        self._databases = {}

    def create_database(self, db_type: str, name: str, **kwargs) -> Optional[BaseDatabase]:
        """
        创建数据库实例
        
        Args:
            db_type: 数据库类型 ('sqlite' 或 'qdrant')
            name: 数据库名称
            **kwargs: 其他参数
            
        Returns:
            BaseDatabase: 数据库实例，如果创建失败返回None
        """
        if db_type not in self.DATABASE_TYPES:
            self.log_manager.get_logger(__name__).error(f"不支持的数据库类型: {db_type}")
            return None
        
        try:
            # 创建数据库实例
            database_class = self.DATABASE_TYPES[db_type]
            database = database_class(
                name=name, 
                config_manager=self.config_manager, 
                log_manager=self.log_manager, 
                **kwargs
            )
            
            # 存储到内部字典
            self._databases[name] = database
            
            self.log_manager.get_logger(__name__).info(f"成功创建数据库: {db_type} - {name}")
            return database
            
        except Exception as e:
            self.log_manager.get_logger(__name__).error(f"创建数据库失败 {db_type} - {name}: {e}")
            return None

    def get_database(self, name: str) -> Optional[BaseDatabase]:
        """
        获取已创建的数据库实例
        
        Args:
            name: 数据库名称
            
        Returns:
            BaseDatabase: 数据库实例，如果不存在返回None
        """
        return self._databases.get(name)

    def get_all_databases(self) -> Dict[str, BaseDatabase]:
        """
        获取所有已创建的数据库实例
        
        Returns:
            Dict[str, BaseDatabase]: 数据库名称到实例的映射
        """
        return self._databases.copy()

    def remove_database(self, name: str) -> bool:
        """
        移除数据库实例
        
        Args:
            name: 数据库名称
            
        Returns:
            bool: 是否成功移除
        """
        if name in self._databases:
            database = self._databases[name]
            try:
                # 断开连接
                database.run_async(database.disconnect())
                del self._databases[name]
                self.log_manager.get_logger(__name__).info(f"成功移除数据库: {name}")
                return True
            except Exception as e:
                self.log_manager.get_logger(__name__).error(f"移除数据库失败 {name}: {e}")
                return False
        return False

    def clear_all_databases(self):
        """清除所有数据库实例"""
        for name in list(self._databases.keys()):
            self.remove_database(name)

    async def connect_all_databases(self) -> bool:
        """
        连接所有数据库
        
        Returns:
            bool: 是否所有数据库都连接成功
        """
        success_count = 0
        total_count = len(self._databases)
        
        for name, database in self._databases.items():
            try:
                if await database.connect():
                    success_count += 1
                    self.log_manager.get_logger(__name__).info(f"数据库 {name} 连接成功")
                else:
                    self.log_manager.get_logger(__name__).error(f"数据库 {name} 连接失败")
            except Exception as e:
                self.log_manager.get_logger(__name__).error(f"数据库 {name} 连接异常: {e}")
        
        self.log_manager.get_logger(__name__).info(f"数据库连接完成: {success_count}/{total_count} 成功")
        return success_count == total_count

    async def disconnect_all_databases(self) -> bool:
        """
        断开所有数据库连接
        
        Returns:
            bool: 是否所有数据库都断开成功
        """
        success_count = 0
        total_count = len(self._databases)
        
        for name, database in self._databases.items():
            try:
                if await database.disconnect():
                    success_count += 1
                    self.log_manager.get_logger(__name__).info(f"数据库 {name} 断开连接成功")
                else:
                    self.log_manager.get_logger(__name__).error(f"数据库 {name} 断开连接失败")
            except Exception as e:
                self.log_manager.get_logger(__name__).error(f"数据库 {name} 连接异常: {e}")
        
        self.log_manager.get_logger(__name__).info(f"数据库断开连接完成: {success_count}/{total_count} 成功")
        return success_count == total_count

    def get_database_status(self) -> Dict[str, Dict]:
        """
        获取所有数据库的状态信息
        
        Returns:
            Dict[str, Dict]: 数据库状态信息
        """
        status = {}
        for name, database in self._databases.items():
            status[name] = {
                'type': database.__class__.__name__,
                'connected': database.is_connected,
                'name': database.name
            }
        return status

    def __len__(self) -> int:
        """返回数据库数量"""
        return len(self._databases)

    def __contains__(self, name: str) -> bool:
        """检查是否包含指定名称的数据库"""
        return name in self._databases

    def __iter__(self):
        """迭代所有数据库"""
        return iter(self._databases.values())
