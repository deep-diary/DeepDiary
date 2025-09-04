#!/usr/bin/env python3
"""
记忆存储调试脚本

用于诊断记忆无法正确存储到数据库的问题
"""

import os
import sys
from typing import List, Dict, Any
import json

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from deepwin.app_logic.memory_manager.config import create_memory_config
from deepwin.data_management.log_manager import LogManager
from mem0 import Memory

# 设置日志记录器
log_manager = LogManager()
logger = log_manager.get_logger(__name__)


def debug_memory_config():
    """调试记忆配置"""
    print("🔧 调试记忆配置")
    print("=" * 50)
    
    try:
        # 创建配置
        config = create_memory_config()
        print(f"✅ 配置创建成功")
        print(f"配置内容: {json.dumps(config, indent=2, default=str)}")
        
        # 检查环境变量
        required_vars = ["DASHSCOPE_API_KEY", "DEEPSEEK_API_KEY", "MEM0_API_KEY"]
        for var in required_vars:
            value = os.getenv(var)
            if value:
                print(f"✅ {var}: {'*' * 10}{value[-4:]}")
            else:
                print(f"❌ {var}: 未设置")
        
        return config
        
    except Exception as e:
        print(f"❌ 配置创建失败: {e}")
        return None


def debug_memory_initialization(config):
    """调试记忆初始化"""
    print("\n🚀 调试记忆初始化")
    print("=" * 50)
    
    try:
        # 创建记忆实例
        memory = Memory.from_config(config)
        print("✅ Memory 实例创建成功")
        
        # 检查实例属性
        print(f"Memory 实例类型: {type(memory)}")
        print(f"Memory 实例属性: {dir(memory)}")
        
        return memory
        
    except Exception as e:
        print(f"❌ Memory 实例创建失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def debug_memory_add(memory):
    """调试记忆添加"""
    print("\n📝 调试记忆添加")
    print("=" * 50)
    
    try:
        # 准备测试消息
        test_messages = [
            {"role": "user", "content": "Hello, this is a test message."},
            {"role": "assistant", "content": "I received your test message."}
        ]
        
        print(f"测试消息: {json.dumps(test_messages, indent=2)}")
        
        # 尝试添加记忆
        result = memory.add(
            messages=test_messages,
            user_id="debug_user",
            metadata={"test": True, "debug": True}
        )
        
        print(f"✅ 记忆添加结果: {json.dumps(result, indent=2, default=str)}")
        
        # 检查结果
        if result and isinstance(result, dict):
            results = result.get('results', [])
            print(f"返回的结果数量: {len(results)}")
            if results:
                print(f"第一个结果: {json.dumps(results[0], indent=2, default=str)}")
        
        return result
        
    except Exception as e:
        print(f"❌ 记忆添加失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def debug_memory_search(memory):
    """调试记忆搜索"""
    print("\n🔍 调试记忆搜索")
    print("=" * 50)
    
    try:
        # 尝试搜索记忆
        search_result = memory.search(
            "test message",
            user_id="debug_user"
        )
        
        print(f"✅ 搜索结果: {json.dumps(search_result, indent=2, default=str)}")
        
        # 检查搜索结果
        if search_result and isinstance(search_result, dict):
            results = search_result.get('results', [])
            print(f"搜索结果数量: {len(results)}")
            if results:
                print(f"第一个搜索结果: {json.dumps(results[0], indent=2, default=str)}")
        
        return search_result
        
    except Exception as e:
        print(f"❌ 记忆搜索失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def debug_database_files():
    """调试数据库文件"""
    print("\n💾 调试数据库文件")
    print("=" * 50)
    
    try:
        # 检查 FAISS 数据库文件
        faiss_dir = "./faiss_db"
        if os.path.exists(faiss_dir):
            print(f"✅ FAISS 目录存在: {faiss_dir}")
            files = os.listdir(faiss_dir)
            for file in files:
                file_path = os.path.join(faiss_dir, file)
                size = os.path.getsize(file_path)
                print(f"  - {file}: {size} bytes")
        else:
            print(f"❌ FAISS 目录不存在: {faiss_dir}")
        
        # 检查历史数据库文件
        history_db = "./history.db"
        if os.path.exists(history_db):
            size = os.path.getsize(history_db)
            print(f"✅ 历史数据库存在: {history_db} ({size} bytes)")
        else:
            print(f"❌ 历史数据库不存在: {history_db}")
        
        # 检查 mem0 缓存目录
        mem0_cache = os.path.expanduser("~/.mem0")
        if os.path.exists(mem0_cache):
            print(f"✅ mem0 缓存目录存在: {mem0_cache}")
            files = os.listdir(mem0_cache)
            for file in files:
                file_path = os.path.join(mem0_cache, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    print(f"  - {file}: {size} bytes")
        else:
            print(f"❌ mem0 缓存目录不存在: {mem0_cache}")
        
    except Exception as e:
        print(f"❌ 数据库文件检查失败: {e}")


def test_alternative_approaches():
    """测试替代方法"""
    print("\n🧪 测试替代方法")
    print("=" * 50)
    
    try:
        # 方法1: 使用不同的消息格式
        print("方法1: 使用字符串格式的消息")
        config = create_memory_config()
        memory = Memory.from_config(config)
        
        # 尝试使用字符串格式
        string_message = "Hello, this is a test message from the assistant."
        result1 = memory.add(
            messages=string_message,
            user_id="test_user_1",
            metadata={"format": "string"}
        )
        print(f"字符串格式结果: {result1}")
        
        # 方法2: 使用单个消息字典
        print("\n方法2: 使用单个消息字典")
        single_message = {"role": "user", "content": "Single test message"}
        result2 = memory.add(
            messages=single_message,
            user_id="test_user_2",
            metadata={"format": "single_dict"}
        )
        print(f"单个字典结果: {result2}")
        
        # 方法3: 使用不同的用户ID
        print("\n方法3: 使用不同的用户ID")
        messages = [
            {"role": "user", "content": "Test with different user ID"},
            {"role": "assistant", "content": "Response to different user"}
        ]
        result3 = memory.add(
            messages=messages,
            user_id="different_user",
            metadata={"format": "different_user"}
        )
        print(f"不同用户ID结果: {result3}")
        
    except Exception as e:
        print(f"❌ 替代方法测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主调试函数"""
    print("🐛 DeepWin 记忆存储调试")
    print("=" * 60)
    
    # 1. 调试配置
    config = debug_memory_config()
    if not config:
        return False
    
    # 2. 调试初始化
    memory = debug_memory_initialization(config)
    if not memory:
        return False
    
    # 3. 调试数据库文件
    debug_database_files()
    
    # 4. 调试记忆添加
    add_result = debug_memory_add(memory)
    
    # 5. 调试记忆搜索
    search_result = debug_memory_search(memory)
    
    # 6. 测试替代方法
    test_alternative_approaches()
    
    # 总结
    print("\n" + "=" * 60)
    print("🎯 调试总结")
    print(f"配置: {'✅' if config else '❌'}")
    print(f"初始化: {'✅' if memory else '❌'}")
    print(f"添加: {'✅' if add_result else '❌'}")
    print(f"搜索: {'✅' if search_result else '❌'}")
    
    if add_result and search_result:
        add_results = add_result.get('results', [])
        search_results = search_result.get('results', [])
        print(f"添加结果数量: {len(add_results)}")
        print(f"搜索结果数量: {len(search_results)}")
        
        if len(add_results) > 0 and len(search_results) == 0:
            print("⚠️  记忆添加成功但搜索不到，可能存在存储或索引问题")
        elif len(add_results) == 0:
            print("⚠️  记忆添加失败，返回空结果")
        else:
            print("✅ 记忆系统工作正常")
    
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  调试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 调试过程中发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
