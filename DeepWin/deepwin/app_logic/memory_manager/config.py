# Pass the initialized model to the config
import os
import logging
from typing import List, Dict, Any, Optional
# 直接初始化 DashScope 嵌入模型
from langchain_community.embeddings import DashScopeEmbeddings
from langchain.chat_models import init_chat_model

from deepwin.config.config_manager import ConfigManager
from deepwin.data_management.log_manager import LogManager
from memory_client_wrapper import MemoryManager

# 设置日志记录器
log_manager = LogManager()
logger = log_manager.get_logger(__name__)

config_manager = ConfigManager()
config_manager.load_env()

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DeepSeek_API_KEY = os.getenv("DEEPSEEK_API_KEY")
logger.info(f"DASHSCOPE_API_KEY: {DASHSCOPE_API_KEY}")
logger.info(f"DeepSeek_API_KEY: {DeepSeek_API_KEY}")


def create_memory_manager() -> MemoryManager:
    """创建记忆管理器实例"""
    try:
        logger.info("创建 MemoryManager 实例")
        memory_manager = MemoryManager()
        logger.info("MemoryManager 实例创建成功")
        return memory_manager
    except Exception as e:
        logger.error(f"创建 MemoryManager 失败: {e}")
        raise


def create_sample_messages() -> List[Dict[str, str]]:
    """创建示例消息"""
    return [
        {"role": "user", "content": "I'm planning to watch a movie tonight. Any recommendations?"},
        {"role": "assistant", "content": "How about a thriller movies? They can be quite engaging."},
        {"role": "user", "content": "I'm not a big fan of thriller movies but I love sci-fi movies."},
        {"role": "assistant", "content": "Got it! I'll avoid thriller recommendations and suggest sci-fi movies in the future."}
    ]


def add_memory_to_system(memory_manager: MemoryManager, messages: List[Dict[str, str]], 
                         user_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """向系统添加记忆"""
    try:
        logger.info(f"开始为用户 {user_id} 添加记忆")
        
        result = memory_manager.add_memory(
            messages=messages, 
            user_id=user_id, 
            metadata=metadata or {}
        )
        
        logger.info(f"记忆添加成功: {result}")
        return result
        
    except Exception as e:
        logger.error(f"添加记忆失败: {e}")
        raise


def search_memories(memory_manager: MemoryManager, query: str, user_id: str) -> List[Dict[str, Any]]:
    """搜索记忆"""
    try:
        logger.info(f"开始搜索用户 {user_id} 的记忆，查询: {query}")
        
        results = memory_manager.search_memory(query, user_id=user_id)
        logger.info(f"记忆搜索完成，找到 {len(results)} 条结果")
        return results
        
    except Exception as e:
        logger.error(f"搜索记忆失败: {e}")
        raise


def get_all_memories(memory_manager: MemoryManager, user_id: str) -> List[Dict[str, Any]]:
    """获取用户的所有记忆"""
    try:
        logger.info(f"获取用户 {user_id} 的所有记忆")
        
        memories = memory_manager.get_all_memories(user_id=user_id)
        logger.info(f"获取到 {len(memories)} 条记忆")
        return memories
        
    except Exception as e:
        logger.error(f"获取记忆失败: {e}")
        raise


def main():
    """主函数"""
    try:
        logger.info("开始初始化记忆管理系统")
        
        # 创建记忆管理器
        memory_manager = create_memory_manager()
        
        # 准备示例消息
        messages = create_sample_messages()
        
        # 添加记忆
        result = add_memory_to_system(
            memory_manager=memory_manager,
            messages=messages,
            user_id="alice",
            metadata={"category": "movies", "source": "conversation"}
        )
        
        # 搜索记忆
        search_results = search_memories(
            memory_manager=memory_manager,
            query="movie recommendations",
            user_id="alice"
        )
        
        # 获取所有记忆
        all_memories = get_all_memories(
            memory_manager=memory_manager,
            user_id="alice"
        )
        
        logger.info("记忆管理系统测试完成")
        return {
            "add_result": result,
            "search_result": search_results,
            "all_memories": all_memories
        }
        
    except Exception as e:
        logger.error(f"记忆管理系统测试失败: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    try:
        results = main()
        print("✅ 记忆管理系统测试成功")
        print(f"添加结果: {len(results['add_result'].get('results', []))} 条记忆")
        print(f"搜索结果: {len(results['search_result'])} 条记忆")
        print(f"总记忆数: {len(results['all_memories'])} 条")
    except Exception as e:
        print(f"❌ 记忆管理系统测试失败: {e}")
        import traceback
        traceback.print_exc()