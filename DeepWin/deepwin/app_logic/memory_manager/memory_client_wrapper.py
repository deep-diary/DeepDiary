#!/usr/bin/env python3
"""
基于 MemoryClient 的记忆管理包装器

解决 Memory.from_config() 配置问题，直接使用 MemoryClient 进行记忆管理
"""

import os
import sys
from typing import List, Dict, Any, Optional
import json

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from deepwin.data_management.log_manager import LogManager
from mem0 import MemoryClient

# 设置日志记录器
log_manager = LogManager()
logger = log_manager.get_logger(__name__)


class MemoryManager:
    """基于 MemoryClient 的记忆管理器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化记忆管理器
        
        Args:
            api_key: mem0 API 密钥，如果不提供则从环境变量获取
        """
        self.api_key = api_key or os.getenv("MEM0_API_KEY")
        if not self.api_key:
            raise ValueError("MEM0_API_KEY 环境变量未设置")
        
        # 设置环境变量
        os.environ["MEM0_API_KEY"] = self.api_key
        
        # 创建 MemoryClient 实例
        self.client = MemoryClient()
        logger.info("MemoryManager 初始化成功")
    
    def add_memory(self, messages: List[Dict[str, str]], 
                   user_id: str, 
                   metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        添加记忆
        
        Args:
            messages: 消息列表，格式为 [{"role": "user", "content": "..."}, ...]
            user_id: 用户ID
            metadata: 元数据
            
        Returns:
            添加结果
        """
        try:
            logger.info(f"为用户 {user_id} 添加记忆")
            
            result = self.client.add(
                messages=messages,
                user_id=user_id,
                metadata=metadata or {}
            )
            
            logger.info(f"记忆添加成功: {result}")
            return result
            
        except Exception as e:
            logger.error(f"添加记忆失败: {e}")
            raise
    
    def search_memory(self, query: str, 
                     user_id: str,
                     metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        搜索记忆
        
        Args:
            query: 搜索查询
            user_id: 用户ID
            metadata: 元数据过滤条件
            
        Returns:
            搜索结果列表
        """
        try:
            logger.info(f"搜索用户 {user_id} 的记忆，查询: {query}")
            
            results = self.client.search(
                query=query,
                user_id=user_id,
                metadata=metadata
            )
            
            logger.info(f"记忆搜索完成，找到 {len(results)} 条结果")
            return results
            
        except Exception as e:
            logger.error(f"搜索记忆失败: {e}")
            raise
    
    def get_all_memories(self, user_id: str) -> List[Dict[str, Any]]:
        """
        获取用户的所有记忆
        
        Args:
            user_id: 用户ID
            
        Returns:
            记忆列表
        """
        try:
            logger.info(f"获取用户 {user_id} 的所有记忆")
            
            memories = self.client.get_all(user_id=user_id)
            
            logger.info(f"获取到 {len(memories)} 条记忆")
            return memories
            
        except Exception as e:
            logger.error(f"获取记忆失败: {e}")
            raise
    
    def delete_memory(self, memory_id: str) -> bool:
        """
        删除记忆
        
        Args:
            memory_id: 记忆ID
            
        Returns:
            是否删除成功
        """
        try:
            logger.info(f"删除记忆: {memory_id}")
            
            result = self.client.delete(memory_id=memory_id)
            
            logger.info(f"记忆删除成功: {result}")
            return result
            
        except Exception as e:
            logger.error(f"删除记忆失败: {e}")
            raise
    
    def delete_all_memories(self, user_id: str) -> bool:
        """
        删除用户的所有记忆
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否删除成功
        """
        try:
            logger.info(f"删除用户 {user_id} 的所有记忆")
            
            result = self.client.delete_all(user_id=user_id)
            
            logger.info(f"所有记忆删除成功: {result}")
            return result
            
        except Exception as e:
            logger.error(f"删除所有记忆失败: {e}")
            raise


def create_sample_messages() -> List[Dict[str, str]]:
    """创建示例消息"""
    return [
        {"role": "user", "content": "I'm planning to watch a movie tonight. Any recommendations?"},
        {"role": "assistant", "content": "How about a thriller movies? They can be quite engaging."},
        {"role": "user", "content": "I'm not a big fan of thriller movies but I love sci-fi movies."},
        {"role": "assistant", "content": "Got it! I'll avoid thriller recommendations and suggest sci-fi movies in the future."}
    ]


def test_memory_manager():
    """测试记忆管理器"""
    print("🧪 测试 MemoryManager")
    print("=" * 50)
    
    try:
        # 创建记忆管理器
        memory_manager = MemoryManager()
        print("✅ MemoryManager 创建成功")
        
        # 准备测试消息
        messages = create_sample_messages()
        print(f"📝 准备添加 {len(messages)} 条消息")
        
        # 添加记忆
        result = memory_manager.add_memory(
            messages=messages,
            user_id="test_user",
            metadata={"category": "movies", "test": True}
        )
        
        print(f"✅ 记忆添加结果: {json.dumps(result, indent=2, default=str)}")
        
        # 搜索记忆
        search_results = memory_manager.search_memory(
            query="movie recommendations",
            user_id="test_user"
        )
        
        print(f"🔍 搜索结果: {json.dumps(search_results, indent=2, default=str)}")
        print(f"找到 {len(search_results)} 条结果")
        
        # 获取所有记忆
        all_memories = memory_manager.get_all_memories(user_id="test_user")
        print(f"📋 用户共有 {len(all_memories)} 条记忆")
        
        return True
        
    except Exception as e:
        logger.error(f"MemoryManager 测试失败: {e}")
        print(f"❌ 测试失败: {e}")
        return False


def main():
    """主函数"""
    print("🔧 MemoryClient 包装器测试")
    print("=" * 60)
    
    # 加载环境变量
    from deepwin.config.config_manager import ConfigManager
    config_manager = ConfigManager()
    config_manager.load_env()
    
    # 检查环境变量
    mem0_api_key = os.getenv("MEM0_API_KEY")
    if not mem0_api_key:
        print("❌ MEM0_API_KEY 环境变量未设置")
        return False
    
    print(f"✅ 环境变量检查通过: MEM0_API_KEY = {mem0_api_key[:10]}...")
    
    # 测试记忆管理器
    success = test_memory_manager()
    
    # 总结
    print("\n" + "=" * 60)
    if success:
        print("🎉 MemoryManager 测试成功！")
        print("现在可以使用 MemoryManager 进行记忆管理了。")
    else:
        print("❌ MemoryManager 测试失败")
    
    print("=" * 60)
    return success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 测试过程中发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
