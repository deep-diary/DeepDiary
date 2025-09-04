#!/usr/bin/env python3
"""
修复版本的记忆管理配置

尝试解决记忆无法正确存储到数据库的问题
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


def create_fixed_memory_config() -> Dict[str, Any]:
    """创建修复版本的记忆配置"""
    try:
        # 方法1: 使用简化的配置
        logger.info("尝试方法1: 简化配置")
        
        config = {
            "vector_store": {
                "provider": "faiss",
                "config": {
                    "collection_name": "test_fixed",
                    "path": "./faiss_db_fixed"
                }
            },
            "llm": {
                "provider": "deepseek",
                "config": {
                    "model": "deepseek-chat",
                    "temperature": 0.2,
                    "max_tokens": 2000,
                    "top_p": 1.0
                }
            },
            "embedder": {
                "provider": "dashscope",
                "config": {
                    "model": "text-embedding-v1",
                    "dashscope_api_key": DASHSCOPE_API_KEY
                }
            },
            "history_db_path": "./history_fixed.db",
            "version": "v1.1"
        }
        
        logger.info("简化配置创建成功")
        return config
        
    except Exception as e:
        logger.error(f"简化配置创建失败: {e}")
        raise


def create_alternative_config() -> Dict[str, Any]:
    """创建替代配置"""
    try:
        # 方法2: 使用不同的嵌入模型配置
        logger.info("尝试方法2: 替代配置")
        
        config = {
            "vector_store": {
                "provider": "faiss",
                "config": {
                    "collection_name": "test_alt",
                    "path": "./faiss_db_alt"
                }
            },
            "llm": {
                "provider": "deepseek",
                "config": {
                    "model": "deepseek-chat",
                    "temperature": 0.2,
                    "max_tokens": 2000
                }
            },
            "embedder": {
                "provider": "openai",  # 尝试使用 OpenAI 嵌入模型
                "config": {
                    "model": "text-embedding-ada-002",
                    "openai_api_key": os.getenv("OPENAI_API_KEY")
                }
            },
            "history_db_path": "./history_alt.db",
            "version": "v1.1"
        }
        
        logger.info("替代配置创建成功")
        return config
        
    except Exception as e:
        logger.error(f"替代配置创建失败: {e}")
        raise


def test_memory_with_config(config: Dict[str, Any], config_name: str):
    """使用指定配置测试记忆功能"""
    print(f"\n🧪 测试配置: {config_name}")
    print("=" * 50)
    
    try:
        # 创建记忆实例
        logger.info(f"使用 {config_name} 创建 Memory 实例")
        memory = Memory.from_config(config)
        print(f"✅ Memory 实例创建成功")
        
        # 测试添加记忆
        test_messages = [
            {"role": "user", "content": f"Test message from {config_name}"},
            {"role": "assistant", "content": f"Response from {config_name}"}
        ]
        
        logger.info(f"使用 {config_name} 添加记忆")
        result = memory.add(
            messages=test_messages,
            user_id=f"test_user_{config_name}",
            metadata={"config": config_name, "test": True}
        )
        
        print(f"添加结果: {json.dumps(result, indent=2, default=str)}")
        
        # 检查结果
        if result and isinstance(result, dict):
            results = result.get('results', [])
            print(f"结果数量: {len(results)}")
            
            if len(results) > 0:
                print(f"✅ {config_name} 配置成功！")
                return True
            else:
                print(f"❌ {config_name} 配置失败，返回空结果")
                return False
        
        return False
        
    except Exception as e:
        logger.error(f"{config_name} 配置测试失败: {e}")
        print(f"❌ {config_name} 配置测试失败: {e}")
        return False


def test_direct_mem0_usage():
    """直接测试 mem0 库的使用"""
    print(f"\n🔧 直接测试 mem0 库")
    print("=" * 50)
    
    try:
        # 设置环境变量
        os.environ["MEM0_API_KEY"] = MEM0_API_KEY
        
        # 尝试直接使用 mem0
        from mem0 import MemoryClient
        
        client = MemoryClient()
        print(f"✅ MemoryClient 创建成功")
        
        # 测试添加记忆
        messages = [
            {"role": "user", "content": "Direct test message"},
            {"role": "assistant", "content": "Direct test response"}
        ]
        
        result = client.add(messages, user_id="direct_test_user")
        print(f"直接添加结果: {json.dumps(result, indent=2, default=str)}")
        
        # 测试搜索
        search_result = client.search("test message", user_id="direct_test_user")
        print(f"直接搜索结果: {json.dumps(search_result, indent=2, default=str)}")
        
        return True
        
    except Exception as e:
        logger.error(f"直接 mem0 测试失败: {e}")
        print(f"❌ 直接 mem0 测试失败: {e}")
        return False


def main():
    """主测试函数"""
    print("🔧 记忆存储问题修复测试")
    print("=" * 60)
    
    # 检查环境变量
    required_vars = ["DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MEM0_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 缺少必需的环境变量: {', '.join(missing_vars)}")
        return False
    
    print("✅ 环境变量检查通过")
    
    success_count = 0
    total_tests = 3
    
    # 测试1: 简化配置
    try:
        config1 = create_fixed_memory_config()
        if test_memory_with_config(config1, "简化配置"):
            success_count += 1
    except Exception as e:
        print(f"❌ 简化配置测试失败: {e}")
    
    # 测试2: 替代配置
    try:
        config2 = create_alternative_config()
        if test_memory_with_config(config2, "替代配置"):
            success_count += 1
    except Exception as e:
        print(f"❌ 替代配置测试失败: {e}")
    
    # 测试3: 直接 mem0 使用
    if test_direct_mem0_usage():
        success_count += 1
    
    # 总结
    print("\n" + "=" * 60)
    print(f"🎯 修复测试完成: {success_count}/{total_tests} 个测试成功")
    
    if success_count > 0:
        print("✅ 找到可用的配置方法！")
    else:
        print("❌ 所有配置方法都失败")
        print("建议:")
        print("1. 检查 mem0 库版本是否兼容")
        print("2. 检查 API 密钥是否有效")
        print("3. 检查网络连接")
        print("4. 考虑使用其他记忆管理库")
    
    print("=" * 60)
    return success_count > 0


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
