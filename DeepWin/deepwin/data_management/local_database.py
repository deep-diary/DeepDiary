#!/usr/bin/env python3
"""
DeepWin Local Database Manager
本地数据库管理器，作为新数据库架构的入口
"""

from PySide6.QtCore import QObject, Signal
from typing import Dict, Any, Optional
from .log_manager import LogManager
from .config_manager import ConfigManager
from .database.database_coordinator import DatabaseCoordinator
# 延迟导入模型以避免循环依赖
# from .database.models import UserModel, NeedModel, ResourceModel, PhotoModel


class LocalDatabaseManager(QObject):
    """本地数据库管理器，整合SQLite和Qdrant数据库"""
    
    # 信号定义
    database_ready = Signal()  # 数据库准备就绪
    data_operation_completed = Signal(str, str)  # 数据操作完成（增删改查、同步等）
    connection_status_changed = Signal(str, str)  # 连接状态变化（连接、断开、重连等）
    error_occurred = Signal(str, str)  # 错误发生

    def __init__(self, config_manager: ConfigManager, log_manager: LogManager, parent=None):
        """
        初始化本地数据库管理器
        
        Args:
            config_manager: 配置管理器实例
            log_manager: 日志管理器实例
            parent: 父对象
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.log_manager = log_manager
        self.logger = log_manager.get_logger(__name__)
        
        self.logger.info("LocalDatabaseManager: 初始化中...")
        
        # 创建数据库协调器
        self.coordinator = DatabaseCoordinator(config_manager, log_manager)
        
        # 连接协调器信号到本地信号（统一信号出口）
        self._connect_coordinator_signals()
        
        # 数据库状态
        self.is_ready = False
        
        # 自动同步初始化数据库（启动时同步初始化即可）
        self._init_databases_sync()
        
        self.logger.info("LocalDatabaseManager: 初始化完成。")
    
    def _connect_coordinator_signals(self):
        """
        连接协调器信号到本地信号，实现统一信号出口
        """
        try:
            # 连接协调器的数据库连接信号
            self.coordinator.databases_connected.connect(self._on_coordinator_databases_connected)
            self.coordinator.databases_disconnected.connect(self._on_coordinator_databases_disconnected)
            self.coordinator.error_occurred.connect(self._on_coordinator_error_occurred)
            
            # 连接数据操作信号（转发协调器的数据操作完成信号）
            self.coordinator.data_operation_completed.connect(self._on_coordinator_data_operation_completed)
            
            self.logger.info("LocalDatabaseManager: 协调器信号连接成功")
            
        except Exception as e:
            self.logger.error(f"LocalDatabaseManager: 连接协调器信号失败: {e}")
    
    def _on_coordinator_databases_connected(self, database_names: list):
        """
        处理协调器的数据库连接成功信号
        """
        self.logger.info(f"LocalDatabaseManager: 协调器报告数据库连接成功: {database_names}")
        # 转发连接状态变化信号
        self.connection_status_changed.emit("databases_connected", f"数据库连接成功: {', '.join(database_names)}")
    
    def _on_coordinator_databases_disconnected(self, database_names: list):
        """
        处理协调器的数据库断开连接信号
        """
        self.logger.info(f"LocalDatabaseManager: 协调器报告数据库断开连接: {database_names}")
        # 转发连接状态变化信号
        self.connection_status_changed.emit("databases_disconnected", f"数据库断开连接: {', '.join(database_names)}")
    
    def _on_coordinator_data_operation_completed(self, operation: str, result: str):
        """
        处理协调器的数据操作完成信号
        """
        self.logger.info(f"LocalDatabaseManager: 协调器数据操作完成: {operation} - {result}")
        # 转发数据操作完成信号
        self.data_operation_completed.emit(operation, result)
    
    def _on_coordinator_error_occurred(self, operation: str, error: str):
        """
        处理协调器的错误发生信号
        """
        self.logger.error(f"LocalDatabaseManager: 协调器操作错误: {operation} - {error}")
        # 转发信号，保持参数一致
        self.error_occurred.emit(operation, error)

    def _init_databases_sync(self):
        """
        同步初始化数据库系统
        在启动时同步初始化即可，避免过度复杂化
        """
        try:
            self.logger.info("LocalDatabaseManager: 开始同步初始化数据库...")
            
            # 使用asyncio.run在同步环境中运行异步代码
            import asyncio
            
            # 设置数据库
            asyncio.run(self.coordinator.setup_databases())
            
            # 连接数据库
            if asyncio.run(self.coordinator.connect_all_databases()):
                self.is_ready = True
                self.database_ready.emit()
                self.data_operation_completed.emit("initialize", "数据库系统初始化成功")
                self.logger.info("LocalDatabaseManager: 数据库系统初始化成功")
            else:
                self.logger.error("LocalDatabaseManager: 数据库连接失败")
                self.error_occurred.emit("initialize", "数据库连接失败")
                
        except Exception as e:
            self.logger.error(f"LocalDatabaseManager: 同步初始化失败: {e}")
            self.error_occurred.emit("initialize", str(e))

    async def initialize(self) -> bool:
        """初始化数据库系统"""
        try:
            self.logger.info("LocalDatabaseManager: 开始初始化数据库系统...")
            
            # 设置数据库
            await self.coordinator.setup_databases()
            
            # 连接数据库
            if await self.coordinator.connect_all_databases():
                self.is_ready = True
                self.database_ready.emit()
                self.data_operation_completed.emit("initialize", "数据库系统初始化成功")
                self.logger.info("LocalDatabaseManager: 数据库系统初始化成功")
                return True
            else:
                self.logger.error("LocalDatabaseManager: 数据库连接失败")
                self.error_occurred.emit("initialize", "数据库连接失败")
                return False
                
        except Exception as e:
            self.logger.error(f"LocalDatabaseManager: 初始化失败: {e}")
            self.error_occurred.emit("initialize", str(e))
            return False

    async def shutdown(self):
        """关闭数据库系统"""
        try:
            self.logger.info("LocalDatabaseManager: 开始关闭数据库系统...")
            
            if self.coordinator:
                await self.coordinator.disconnect_all_databases()
            
            self.is_ready = False
            self.data_operation_completed.emit("shutdown", "数据库系统关闭完成")
            self.logger.info("LocalDatabaseManager: 数据库系统关闭完成")
            
        except Exception as e:
            self.logger.error(f"LocalDatabaseManager: 关闭失败: {e}")
            self.error_occurred.emit("shutdown", str(e))

    def get_memories(self, query: str) -> Dict[str, Any]:
        """查询本地记忆（从向量数据库）"""
        if not self.is_ready:
            return {"error": "数据库未准备就绪"}
        
        try:
            # 这里应该调用Qdrant进行向量搜索
            # 暂时返回模拟结果
            self.logger.info(f"LocalDatabaseManager: 模拟查询本地记忆：{query}")
            result = {"result": f"本地找到关于'{query}'的记忆"}
            self.data_operation_completed.emit("query_memories", "记忆查询完成")
            return result
            
        except Exception as e:
            self.logger.error(f"查询记忆失败: {e}")
            self.error_occurred.emit("query_memories", str(e))
            return {"error": str(e)}

    def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """获取用户信息"""
        if not self.is_ready:
            return None
        
        try:
            # 这里应该从SQLite查询用户信息
            # 暂时返回模拟结果
            self.logger.info(f"LocalDatabaseManager: 查询用户信息：{user_id}")
            result = {
                "id": user_id,
                "username": "示例用户",
                "email": "user@example.com"
            }
            self.data_operation_completed.emit("query_user_info", f"用户信息查询完成: {user_id}")
            return result
            
        except Exception as e:
            self.logger.error(f"查询用户信息失败: {e}")
            self.error_occurred.emit("query_user_info", str(e))
            return None

    def create_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建用户"""
        if not self.is_ready:
            return None
        
        try:
            # 这里应该创建用户并保存到SQLite
            self.logger.info(f"LocalDatabaseManager: 创建用户：{user_data}")
            result = {
                "id": 1,
                "username": user_data.get("username"),
                "email": user_data.get("email"),
                "status": "created"
            }
            self.data_operation_completed.emit("create_user", f"用户创建成功: {user_data.get('username')}")
            return result
            
        except Exception as e:
            self.logger.error(f"创建用户失败: {e}")
            self.error_occurred.emit("create_user", str(e))
            return None

    def get_database_status(self) -> Dict[str, Any]:
        """获取数据库状态"""
        if not self.coordinator:
            return {"error": "数据库协调器未初始化"}
        
        try:
            if not self.is_ready:
                return {
                    "status": "initializing",
                    "message": "数据库系统正在初始化中",
                    "coordinator": "available"
                }
            
            status = self.coordinator.get_database_status()
            if not status:
                return {
                    "status": "no_databases",
                    "message": "没有可用的数据库",
                    "coordinator": "ready"
                }
            
            return {
                "status": "ready",
                "databases": status,
                "coordinator": "ready"
            }
            
        except Exception as e:
            self.logger.error(f"获取数据库状态失败: {e}")
            return {"error": str(e)}

    def is_database_ready(self) -> bool:
        """检查数据库是否准备就绪"""
        return self.is_ready

    def get_coordinator(self) -> DatabaseCoordinator:
        """获取数据库协调器实例"""
        return self.coordinator

    def cleanup(self):
        """清理资源"""
        self.logger.info("LocalDatabaseManager: 执行清理工作。")
        
        # 这里可以添加其他清理逻辑
        # 比如清理临时文件、关闭连接等