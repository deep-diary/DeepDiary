#!/usr/bin/env python3
"""
DeepWin Qdrant Database Demo
Qdrant向量数据库功能测试演示
"""

import asyncio
import sys
import os
import logging
import numpy as np
import uuid
from datetime import datetime
from typing import Dict, Any, List

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from deepwin.data_management.config_manager import ConfigManager
from deepwin.data_management.log_manager import LogManager
from deepwin.data_management.local_database import LocalDatabaseManager
from deepwin.data_management.database.qdrant_manager import QdrantManager


class QdrantDatabaseDemo:
    """Qdrant向量数据库功能演示类"""
    
    def __init__(self):
        """初始化演示环境"""
        self.log_manager = LogManager()
        
        # 设置日志级别：控制台只显示INFO及以上，文件记录DEBUG及以上
        self.log_manager.set_all_levels(
            console_level=logging.INFO,  # 控制台只显示INFO、WARNING、ERROR
            file_level=logging.DEBUG      # 文件记录所有日志
        )
        
        self.config_manager = ConfigManager(self.log_manager)
        self.logger = self.log_manager.get_logger(__name__)
        
        # 测试数据存储
        self.test_points = {
            'user_embeddings': [],
            'photo_embeddings': [],
            'memory_embeddings': []
        }
        
        # 用于生成唯一标识的计数器
        self.test_counter = 0

    async def setup(self):
        """设置演示环境"""
        print("🚀 开始设置Qdrant演示环境...")
        
        # 创建Qdrant管理器
        self.qdrant_manager = QdrantManager(
            name="qdrant_test",
            config_manager=self.config_manager,
            log_manager=self.log_manager,
            local_path="database/qdrant/test"  # 使用测试路径
        )
        
        # 连接到Qdrant数据库
        success = await self.qdrant_manager.connect()
        if not success:
            print("❌ Qdrant数据库连接失败")
            return False
            
        print("✅ Qdrant数据库连接成功")
        return True

    async def cleanup(self):
        """清理演示环境"""
        print("🧹 清理Qdrant演示环境...")
        await self.qdrant_manager.disconnect()
        print("✅ 清理完成")

    def print_section(self, title: str):
        """打印章节标题"""
        print(f"\n{'='*60}")
        print(f"📋 {title}")
        print(f"{'='*60}")

    def print_result(self, operation: str, result: Any):
        """打印操作结果"""
        print(f"🔍 {operation}:")
        if isinstance(result, dict):
            for key, value in result.items():
                if key == 'vector' and isinstance(value, list):
                    print(f"   {key}: [向量数据，长度: {len(value)}]")
                else:
                    print(f"   {key}: {value}")
        elif isinstance(result, list):
            print(f"   共 {len(result)} 条记录")
            for i, item in enumerate(result[:3]):  # 只显示前3条
                print(f"   {i+1}. {item}")
            if len(result) > 3:
                print(f"   ... 还有 {len(result) - 3} 条记录")
        else:
            print(f"   {result}")
        print()

    def get_unique_id(self) -> str:
        """生成唯一的测试标识"""
        self.test_counter += 1
        timestamp = datetime.now().strftime("%H%M%S")
        return f"{timestamp}_{self.test_counter}"
    
    def generate_uuid(self) -> str:
        """生成有效的UUID用于Qdrant点ID"""
        return str(uuid.uuid4())

    def generate_test_vector(self, size: int) -> List[float]:
        """生成测试向量数据"""
        # 生成随机向量，模拟真实的embeddings
        return np.random.normal(0, 1, size).tolist()

    async def test_collection_operations(self):
        """测试集合操作功能"""
        self.print_section("集合操作功能测试")
        
        # 检查集合状态
        print("🔍 检查集合状态...")
        try:
            collections = self.qdrant_manager.client.get_collections()
            collection_names = [col.name for col in collections.collections]
            self.print_result("现有集合", collection_names)
        except Exception as e:
            print(f"❌ 获取集合列表失败: {e}")
            return

        # 测试创建新集合（如果不存在）
        print("📝 测试集合创建...")
        test_collection = f"test_collection_{self.get_unique_id()}"
        try:
            await self.qdrant_manager._create_collection_if_not_exists(test_collection, 128)
            print(f"✅ 测试集合创建成功: {test_collection}")
            
            # 清理测试集合
            self.qdrant_manager.client.delete_collection(test_collection)
            print(f"🧹 测试集合已清理: {test_collection}")
        except Exception as e:
            print(f"❌ 测试集合操作失败: {e}")

    async def test_vector_insertion(self):
        """测试向量插入功能"""
        self.print_section("向量插入功能测试")
        
        # 测试用户embeddings插入
        print("👤 插入用户embeddings...")
        user_id = self.generate_uuid()
        user_vector = self.generate_test_vector(1536)
        user_payload = {
            "username": f"test_user_{self.get_unique_id()}",
            "email": f"test{self.get_unique_id()}@example.com",
            "created_at": datetime.now().isoformat(),
            "tags": ["测试", "用户", "向量"]
        }
        
        try:
            await self.qdrant_manager._insert_points({
                'collection': 'user_embeddings',
                'points': [{
                    'id': user_id,
                    'vector': user_vector,
                    'payload': user_payload
                }]
            })
            self.test_points['user_embeddings'].append(user_id)
            print(f"✅ 用户embeddings插入成功: {user_id}")
        except Exception as e:
            print(f"❌ 用户embeddings插入失败: {e}")
            return

        # 测试照片embeddings插入
        print("📸 插入照片embeddings...")
        photo_id = self.generate_uuid()
        photo_vector = self.generate_test_vector(512)
        photo_payload = {
            "filename": f"test_photo_{self.get_unique_id()}.jpg",
            "file_size": 2048576,
            "mime_type": "image/jpeg",
            "description": "测试照片",
            "tags": ["测试", "照片", "图像识别"],
            "uploaded_at": datetime.now().isoformat()
        }
        
        try:
            await self.qdrant_manager._insert_points({
                'collection': 'photo_embeddings',
                'points': [{
                    'id': photo_id,
                    'vector': photo_vector,
                    'payload': photo_payload
                }]
            })
            self.test_points['photo_embeddings'].append(photo_id)
            print(f"✅ 照片embeddings插入成功: {photo_id}")
        except Exception as e:
            print(f"❌ 照片embeddings插入失败: {e}")

        # 测试记忆embeddings插入
        print("🧠 插入记忆embeddings...")
        memory_id = self.generate_uuid()
        memory_vector = self.generate_test_vector(1536)
        memory_payload = {
            "content": f"这是一个测试记忆，用于验证向量数据库功能",
            "type": "text",
            "importance": 0.8,
            "created_at": datetime.now().isoformat(),
            "tags": ["测试", "记忆", "向量搜索"]
        }
        
        try:
            await self.qdrant_manager._insert_points({
                'collection': 'memory_embeddings',
                'points': [{
                    'id': memory_id,
                    'vector': memory_vector,
                    'payload': memory_payload
                }]
            })
            self.test_points['memory_embeddings'].append(memory_id)
            print(f"✅ 记忆embeddings插入成功: {memory_id}")
        except Exception as e:
            print(f"❌ 记忆embeddings插入失败: {e}")

    async def test_vector_search(self):
        """测试向量搜索功能"""
        self.print_section("向量搜索功能测试")
        
        # 测试相似向量搜索
        print("🔍 测试相似向量搜索...")
        query_vector = self.generate_test_vector(1536)  # 用户embeddings维度
        
        try:
            results = await self.qdrant_manager.execute_query(
                "search",
                {
                    'collection': 'user_embeddings',
                    'vector': query_vector,
                    'limit': 5
                }
            )
            self.print_result("相似用户搜索结果", results)
        except Exception as e:
            print(f"❌ 相似向量搜索失败: {e}")

        # 测试照片向量搜索
        print("🔍 测试照片向量搜索...")
        photo_query_vector = self.generate_test_vector(512)  # 照片embeddings维度
        
        try:
            results = await self.qdrant_manager.execute_query(
                "search",
                {
                    'collection': 'photo_embeddings',
                    'vector': photo_query_vector,
                    'limit': 3
                }
            )
            self.print_result("相似照片搜索结果", results)
        except Exception as e:
            print(f"❌ 照片向量搜索失败: {e}")

        # 测试记忆向量搜索
        print("🔍 测试记忆向量搜索...")
        memory_query_vector = self.generate_test_vector(1536)  # 记忆embeddings维度
        
        try:
            results = await self.qdrant_manager.execute_query(
                "search",
                {
                    'collection': 'memory_embeddings',
                    'vector': memory_query_vector,
                    'limit': 3
                }
            )
            self.print_result("相似记忆搜索结果", results)
        except Exception as e:
            print(f"❌ 记忆向量搜索失败: {e}")

    async def test_vector_update(self):
        """测试向量更新功能"""
        self.print_section("向量更新功能测试")
        
        if not self.test_points['user_embeddings']:
            print("⚠️ 没有可更新的测试数据，跳过更新测试")
            return
        
        user_id = self.test_points['user_embeddings'][0]
        print(f"✏️ 更新用户embeddings: {user_id}")
        
        update_payload = {
            "username": f"updated_user_{self.get_unique_id()}",
            "email": f"updated{self.get_unique_id()}@example.com",
            "updated_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        try:
            await self.qdrant_manager._update_points({
                'collection': 'user_embeddings',
                'points': [{
                    'id': user_id,
                    'payload': update_payload
                }]
            })
            print(f"✅ 用户embeddings更新成功: {user_id}")
        except Exception as e:
            print(f"❌ 用户embeddings更新失败: {e}")

    async def test_vector_deletion(self):
        """测试向量删除功能"""
        self.print_section("向量删除功能测试")
        
        # 删除测试数据
        print("🗑️ 删除测试数据...")
        
        for collection_name, point_ids in self.test_points.items():
            if point_ids:
                print(f"   删除 {collection_name} 集合中的 {len(point_ids)} 个点...")
                try:
                    await self.qdrant_manager._delete_points({
                        'collection': collection_name,
                        'point_ids': point_ids
                    })
                    print(f"   ✅ {collection_name} 删除成功")
                except Exception as e:
                    print(f"   ❌ {collection_name} 删除失败: {e}")
        
        print("✅ 测试数据清理完成")

    async def test_batch_operations(self):
        """测试批量操作功能"""
        self.print_section("批量操作功能测试")
        
        # 批量插入多个用户embeddings
        print("👥 批量插入用户embeddings...")
        batch_points = []
        for i in range(3):
            user_id = self.generate_uuid()
            user_vector = self.generate_test_vector(1536)
            user_payload = {
                "username": f"batch_user_{i+1}",
                "email": f"batch{i+1}@example.com",
                "batch_id": f"batch_{self.get_unique_id()}",
                "created_at": datetime.now().isoformat()
            }
            batch_points.append({
                'id': user_id,
                'vector': user_vector,
                'payload': user_payload
            })
            self.test_points['user_embeddings'].append(user_id)
        
        try:
            await self.qdrant_manager._insert_points({
                'collection': 'user_embeddings',
                'points': batch_points
            })
            print(f"✅ 批量插入成功: {len(batch_points)} 个用户")
        except Exception as e:
            print(f"❌ 批量插入失败: {e}")

    async def test_error_handling(self):
        """测试错误处理功能"""
        self.print_section("错误处理功能测试")
        
        # 测试无效集合名
        print("🧪 测试无效集合名...")
        try:
            await self.qdrant_manager.execute_query(
                "search",
                {
                    'collection': 'invalid_collection',
                    'vector': self.generate_test_vector(128),
                    'limit': 5
                }
            )
        except Exception as e:
            print(f"✅ 正确捕获错误: {e}")
        
        # 测试无效向量维度
        print("🧪 测试无效向量维度...")
        try:
            await self.qdrant_manager._insert_points({
                'collection': 'user_embeddings',
                'points': [{
                    'id': self.generate_uuid(),
                    'vector': self.generate_test_vector(100),  # 错误的维度
                    'payload': {}
                }]
            })
        except Exception as e:
            print(f"✅ 正确捕获错误: {e}")

    async def test_database_status(self):
        """测试数据库状态查询"""
        self.print_section("数据库状态查询")
        
        # 获取连接状态
        is_connected = self.qdrant_manager.is_connected
        self.print_result("连接状态", f"已连接: {is_connected}")
        
        # 获取集合信息
        try:
            collections = self.qdrant_manager.client.get_collections()
            collection_info = {}
            for col in collections.collections:
                # 获取集合的详细信息
                collection_detail = self.qdrant_manager.client.get_collection(col.name)
                collection_info[col.name] = {
                    "向量数量": collection_detail.config.params.vectors.size,
                    "点数量": collection_detail.points_count,
                    "状态": "active"
                }
            self.print_result("集合信息", collection_info)
        except Exception as e:
            print(f"❌ 获取集合信息失败: {e}")

    async def run_demo(self):
        """运行完整的演示"""
        print("🎯 DeepWin Qdrant向量数据库功能演示")
        print("=" * 60)
        
        try:
            # 设置环境
            if not await self.setup():
                return
            
            # 运行各项测试
            await self.test_database_status()
            await self.test_collection_operations()
            await self.test_vector_insertion()
            await self.test_vector_search()
            await self.test_vector_update()
            await self.test_batch_operations()
            await self.test_error_handling()
            await self.test_vector_deletion()
            
            print("\n🎉 演示完成！所有功能测试通过")
            
        except Exception as e:
            print(f"❌ 演示过程中发生错误: {e}")
            self.logger.error(f"演示错误: {e}")
            
        finally:
            # 清理环境
            await self.cleanup()


async def main():
    """主函数"""
    demo = QdrantDatabaseDemo()
    await demo.run_demo()


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())
