#!/usr/bin/env python3
"""
DeepWin Database Base Class
提供数据库操作的抽象基类
"""

import asyncio
import logging
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Union
from PySide6.QtCore import QObject, Signal

from ..config_manager import ConfigManager
from ..log_manager import LogManager


class BaseDatabase(QObject):
    """数据库基类，定义所有数据库必须实现的方法"""
    
    # 信号定义
    connected = Signal(str)  # 数据库连接成功
    disconnected = Signal(str)  # 数据库断开连接
    error_occurred = Signal(str, str)  # 错误发生 (数据库名, 错误信息)
    operation_completed = Signal(str, str)  # 操作完成 (数据库名, 操作类型)

    def __init__(self, name: str, config_manager: ConfigManager, log_manager: LogManager, parent=None):
        """
        初始化数据库基类
        
        Args:
            name: 数据库名称
            config_manager: 配置管理器实例
            log_manager: 日志管理器实例
            parent: 父对象
        """
        super().__init__(parent)
        self.name = name
        self.config_manager = config_manager
        self.log_manager = log_manager
        self.logger = log_manager.get_logger(__name__)
        self._is_connected = False
        self.executor = ThreadPoolExecutor(max_workers=4)

    @property
    def is_connected(self) -> bool:
        """检查数据库是否已连接"""
        return self._is_connected

    @is_connected.setter
    def is_connected(self, value: bool):
        """设置连接状态"""
        self._is_connected = value

    @abstractmethod
    async def connect(self) -> bool:
        """连接到数据库"""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """断开数据库连接"""
        pass

    @abstractmethod
    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行查询操作"""
        pass

    @abstractmethod
    async def execute_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """执行命令操作"""
        pass

    @abstractmethod
    async def begin_transaction(self) -> bool:
        """开始事务"""
        pass

    @abstractmethod
    async def commit_transaction(self) -> bool:
        """提交事务"""
        pass

    @abstractmethod
    async def rollback_transaction(self) -> bool:
        """回滚事务"""
        pass

    def run_async(self, coro):
        """运行异步协程"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，使用线程执行器
                future = asyncio.run_coroutine_threadsafe(coro, loop)
                return future.result()
            else:
                return asyncio.run(coro)
        except RuntimeError:
            # 如果没有事件循环，创建一个新的
            return asyncio.run(coro)

    def run_in_thread(self, func, *args, **kwargs):
        """在线程中运行函数"""
        future = self.executor.submit(func, *args, **kwargs)
        return future.result()

    def __del__(self):
        """析构函数，确保资源被正确释放"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
