#!/usr/bin/env python3
"""
DeepWin Qdrant Database Manager
使用langchain-qdrant管理向量数据库，支持本地文件存储
"""

import asyncio
import os
from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter
from langchain_community.vectorstores import Qdrant as LangchainQdrant

from .base_database import BaseDatabase
from ..config_manager import ConfigManager
from ..log_manager import LogManager


class QdrantManager(BaseDatabase):
    """Qdrant向量数据库管理器，使用langchain-qdrant"""
    
    def __init__(self, name: str, config_manager: ConfigManager, log_manager: LogManager, parent=None, **kwargs):
        super().__init__(name, config_manager, log_manager, parent)
        
        # 从参数或配置管理器获取配置
        self.host = kwargs.get('host', config_manager.get('database.qdrant.host', 'localhost'))
        self.port = kwargs.get('port', config_manager.get('database.qdrant.port', 6333))
        self.local_path = kwargs.get('local_path', config_manager.get('database.qdrant.local_path', None))
        self.api_key = kwargs.get('api_key', config_manager.get('database.qdrant.api_key', None))
        
        # 客户端和集合
        self.client = None
        self.collections = {}
        self.langchain_stores = {}
        
        # 向量维度配置
        self.vector_sizes = {
            'user_embeddings': 1536,
            'photo_embeddings': 512,
            'memory_embeddings': 1536,
        }

    async def connect(self) -> bool:
        """连接到Qdrant数据库"""
        try:
            if self.local_path:
                self.client = QdrantClient(path=self.local_path)
                self.logger.info(f"连接到本地Qdrant数据库: {self.local_path}")
            else:
                self.client = QdrantClient(
                    host=self.host,
                    port=self.port,
                    api_key=self.api_key
                )
                self.logger.info(f"连接到远程Qdrant数据库: {self.host}:{self.port}")
            
            await self._init_collections()
            
            self.is_connected = True
            self.connected.emit(self.name)
            return True
            
        except Exception as e:
            self.logger.error(f"Qdrant数据库连接失败: {e}")
            self.error_occurred.emit(self.name, str(e))
            return False

    async def disconnect(self) -> bool:
        """断开Qdrant数据库连接"""
        try:
            if self.client:
                self.client.close()
                self.client = None
            
            self.collections.clear()
            self.langchain_stores.clear()
            self.is_connected = False
            
            self.disconnected.emit(self.name)
            return True
            
        except Exception as e:
            self.logger.error(f"Qdrant数据库断开连接失败: {e}")
            self.error_occurred.emit(self.name, str(e))
            return False

    async def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """执行向量查询操作"""
        if not self.is_connected:
            raise ConnectionError("数据库未连接")
        
        try:
            collection_name = params.get('collection', 'user_embeddings')
            query_vector = params.get('vector')
            limit = params.get('limit', 10)
            
            if query_vector:
                results = self.client.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=limit
                )
                return [point.dict() for point in results]
            else:
                results = self.client.scroll(
                    collection_name=collection_name,
                    limit=limit
                )
                return [point.dict() for point in results[0]]
                
        except Exception as e:
            self.logger.error(f"向量查询执行失败: {e}")
            self.error_occurred.emit(self.name, f"查询失败: {e}")
            raise

    async def execute_command(self, command: str, params: Optional[Dict[str, Any]] = None) -> bool:
        """执行命令操作"""
        if not self.is_connected:
            raise ConnectionError("数据库未连接")
        
        try:
            if command == 'insert':
                await self._insert_points(params)
            elif command == 'update':
                await self._update_points(params)
            elif command == 'delete':
                await self._delete_points(params)
            else:
                raise ValueError(f"未知命令: {command}")
            
            self.operation_completed.emit(self.name, f"命令执行成功: {command}")
            return True
            
        except Exception as e:
            self.logger.error(f"命令执行失败: {e}")
            self.error_occurred.emit(self.name, f"命令失败: {e}")
            return False

    async def begin_transaction(self) -> bool:
        """开始事务（Qdrant不支持传统事务）"""
        self.logger.info("Qdrant不支持传统事务，使用批量操作")
        return True

    async def commit_transaction(self) -> bool:
        """提交事务（Qdrant不支持传统事务）"""
        self.logger.info("Qdrant事务模拟提交")
        return True

    async def rollback_transaction(self) -> bool:
        """回滚事务（Qdrant不支持传统事务）"""
        self.logger.info("Qdrant事务模拟回滚")
        return True

    async def _init_collections(self):
        """初始化集合"""
        try:
            for collection_name, vector_size in self.vector_sizes.items():
                await self._create_collection_if_not_exists(collection_name, vector_size)
                
                # 暂时跳过LangChain存储的创建，避免embeddings错误
                # 在实际使用时，应该传入真实的embeddings模型
                # self.langchain_stores[collection_name] = LangchainQdrant(
                #     client=self.client,
                #     collection_name=collection_name,
                #     embeddings=None,  # 暂时为None，实际使用时需要传入
                #     vector_name="vector"
                # )
                
            self.logger.info(f"Qdrant集合初始化完成: {list(self.vector_sizes.keys())}")
            
        except Exception as e:
            self.logger.error(f"集合初始化失败: {e}")
            raise

    async def _create_collection_if_not_exists(self, collection_name: str, vector_size: int):
        """创建集合（如果不存在）"""
        try:
            collections = self.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            
            if collection_name not in collection_names:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=vector_size,
                        distance=Distance.COSINE
                    )
                )
                self.logger.info(f"创建集合: {collection_name}")
            else:
                self.logger.info(f"集合已存在: {collection_name}")
                
        except Exception as e:
            self.logger.error(f"创建集合失败 {collection_name}: {e}")
            raise

    async def _insert_points(self, params: Dict[str, Any]):
        """插入向量点"""
        collection_name = params.get('collection')
        points = params.get('points', [])
        
        if not collection_name or not points:
            raise ValueError("缺少必要参数")
        
        point_structs = []
        for point_data in points:
            point = PointStruct(
                id=point_data.get('id'),
                vector=point_data.get('vector'),
                payload=point_data.get('payload', {})
            )
            point_structs.append(point)
        
        self.client.upsert(
            collection_name=collection_name,
            points=point_structs
        )

    async def _update_points(self, params: Dict[str, Any]):
        """更新向量点"""
        collection_name = params.get('collection')
        points = params.get('points', [])
        
        if not collection_name or not points:
            raise ValueError("缺少必要参数")
        
        for point_data in points:
            self.client.set_payload(
                collection_name=collection_name,
                payload=point_data.get('payload', {}),
                points=[point_data.get('id')]
            )

    async def _delete_points(self, params: Dict[str, Any]):
        """删除向量点"""
        collection_name = params.get('collection')
        point_ids = params.get('point_ids', [])
        
        if not collection_name or not point_ids:
            raise ValueError("缺少必要参数")
        
        self.client.delete(
            collection_name=collection_name,
            points=point_ids
        )

    def get_langchain_store(self, collection_name: str):
        """获取langchain-qdrant存储实例"""
        return self.langchain_stores.get(collection_name)

    def set_embeddings(self, collection_name: str, embeddings):
        """为指定集合设置embeddings"""
        if collection_name in self.langchain_stores:
            self.langchain_stores[collection_name].embeddings = embeddings
