#!/usr/bin/env python3
"""
修复版本的本地记忆管理配置

确保能够正确连接到本地保存的记忆数据库
"""

import os
import sys
from typing import List, Dict, Any, Optional
import json

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from deepwin.config.config_manager import ConfigManager
from deepwin.data_management.log_manager import LogManager
from langchain_community.embeddings import DashScopeEmbeddings
from langchain.chat_models import init_chat_model
from mem0 import Memory

# 设置日志记录器
log_manager = LogManager()
logger = log_manager.get_logger(__name__)

config_manager = ConfigManager()
config_manager.load_env()

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DeepSeek_API_KEY = os.getenv("DEEPSEEK_API_KEY")
MEM0_API_KEY = os.getenv("MEM0_API_KEY")

logger.info(f"DASHSCOPE_API_KEY: {DASHSCOPE_API_KEY}")
logger.info(f"DeepSeek_API_KEY: {DeepSeek_API_KEY}")
logger.info(f"MEM0_API_KEY: {MEM0_API_KEY}")

# 获取项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def create_local_memory_config() -> Dict[str, Any]:
    """创建本地记忆配置，确保能够连接到本地数据库"""
    
    # 本地存储路径
    local_data_dir = os.path.join(PROJECT_ROOT, "data")
    local_faiss_dir = os.path.join(local_data_dir, "faiss")
    local_sqlite_dir = os.path.join(local_data_dir, "sqlite")
    
    # 确保目录存在
    os.makedirs(local_faiss_dir, exist_ok=True)
    os.makedirs(local_sqlite_dir, exist_ok=True)
    
    logger.info(f"本地数据目录: {local_data_dir}")
    logger.info(f"本地FAISS目录: {local_faiss_dir}")
    logger.info(f"本地SQLite目录: {local_sqlite_dir}")
    
    config = {
        "vector_store": {
            "provider": "faiss",
            "config": {
                "collection_name": "deepwin_memories",
                "index_path": local_faiss_dir,
                "embedding_dimension": 1536,
                "metric": "cosine"
            }
        },
        "database": {
            "provider": "sqlite",
            "config": {
                "database_path": os.path.join(local_sqlite_dir, "deepwin_memories.db"),
                "table_name": "memories"
            }
        },
        "embedding_model": {
            "provider": "dashscope",
            "model": "text-embedding-v1",
            "api_key": DASHSCOPE_API_KEY
        },
        "llm_model": {
            "provider": "deepseek",
            "model": "deepseek-chat",
            "api_key": DeepSeek_API_KEY
        },
        "memory_config": {
            "max_memories": 10000,
            "memory_decay": 0.1,
            "similarity_threshold": 0.7
        }
    }
    
    return config

def create_memory_with_local_storage() -> Memory:
    """创建连接到本地存储的Memory实例"""
    
    try:
        # 创建配置
        config = create_local_memory_config()
        logger.info("本地记忆配置创建成功")
        
        # 打印配置信息
        logger.info(f"配置内容: {json.dumps(config, indent=2, default=str)}")
        
        # 创建Memory实例
        memory = Memory.from_config(config)
        logger.info("Memory实例创建成功")
        
        return memory
        
    except Exception as e:
        logger.error(f"创建Memory实例失败: {e}")
        raise

def test_local_memory_connection(memory: Memory, user_id: str = "test_user") -> bool:
    """测试本地记忆连接"""
    
    print(f"🔍 测试本地记忆连接 - 用户 {user_id}")
    print("=" * 60)
    
    try:
        # 1. 测试获取所有记忆
        print("1️⃣ 测试获取所有记忆...")
        all_memories = memory.get_all(user_id=user_id)
        print(f"   📊 找到 {len(all_memories)} 条记忆")
        
        if all_memories:
            print("   ✅ 本地记忆连接成功！")
            for i, mem in enumerate(all_memories[:3]):  # 只显示前3条
                print(f"      {i+1}. ID: {mem.get('id', 'N/A')}")
                print(f"         内容: {mem.get('memory', 'N/A')[:50]}...")
                print(f"         元数据: {mem.get('metadata', {})}")
        else:
            print("   ⚠️  未找到任何记忆")
        
        # 2. 测试搜索功能
        print("\n2️⃣ 测试搜索功能...")
        search_results = memory.search("test", user_id=user_id)
        print(f"   🔍 搜索结果: {len(search_results)} 条")
        
        # 3. 测试添加新记忆
        print("\n3️⃣ 测试添加新记忆...")
        test_messages = [
            {"role": "user", "content": "Testing local memory connection"},
            {"role": "assistant", "content": "Local memory connection test successful"}
        ]
        
        add_result = memory.add(
            messages=test_messages,
            user_id=user_id,
            metadata={"test": True, "local": True}
        )
        
        if add_result and len(add_result.get('results', [])) > 0:
            print(f"   ✅ 新记忆添加成功: {len(add_result['results'])} 条")
            new_memory_id = add_result['results'][0]['id']
            
            # 4. 验证新记忆是否可以被检索
            print("\n4️⃣ 验证新记忆检索...")
            verify_memories = memory.get_all(user_id=user_id)
            print(f"   📊 验证后记忆总数: {len(verify_memories)} 条")
            
            # 5. 清理测试记忆
            print("\n5️⃣ 清理测试记忆...")
            try:
                memory.delete(memory_id=new_memory_id)
                print("   ✅ 测试记忆清理成功")
            except Exception as e:
                print(f"   ⚠️  测试记忆清理失败: {e}")
            
            return True
        else:
            print("   ❌ 新记忆添加失败")
            return False
            
    except Exception as e:
        logger.error(f"测试本地记忆连接失败: {e}")
        print(f"   ❌ 测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🔧 本地记忆管理测试")
    print("=" * 60)
    
    try:
        # 创建Memory实例
        print("1️⃣ 创建Memory实例...")
        memory = create_memory_with_local_storage()
        print("   ✅ Memory实例创建成功")
        
        # 测试本地记忆连接
        print("\n2️⃣ 测试本地记忆连接...")
        test_user_id = "test_user"
        success = test_local_memory_connection(memory, test_user_id)
        
        if success:
            print("\n🎉 本地记忆管理测试成功！")
            print("建议:")
            print("1. 本地存储配置正确")
            print("2. 记忆系统工作正常")
            print("3. 可以继续使用现有记忆")
        else:
            print("\n⚠️  本地记忆管理测试失败")
            print("建议:")
            print("1. 检查本地存储路径")
            print("2. 验证数据库文件权限")
            print("3. 考虑重新初始化记忆系统")
        
        return success
        
    except Exception as e:
        logger.error(f"主函数执行失败: {e}")
        print(f"❌ 主函数执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

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
