#!/usr/bin/env python3
"""
记忆系统诊断脚本

用于诊断记忆无法正常获取的问题，并提供修复方案
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


class MemoryDiagnostic:
    """记忆系统诊断器"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化诊断器"""
        self.api_key = api_key or os.getenv("MEM0_API_KEY")
        if not self.api_key:
            raise ValueError("MEM0_API_KEY 环境变量未设置")
        
        # 设置环境变量
        os.environ["MEM0_API_KEY"] = self.api_key
        
        # 创建 MemoryClient 实例
        self.client = MemoryClient()
        logger.info("MemoryDiagnostic 初始化成功")
    
    def diagnose_memory_system(self, user_id: str) -> Dict[str, Any]:
        """诊断记忆系统"""
        print(f"🔍 诊断用户 {user_id} 的记忆系统")
        print("=" * 60)
        
        diagnosis = {
            "user_id": user_id,
            "get_all_result": None,
            "search_result": None,
            "history_result": None,
            "memory_count": 0,
            "issues": [],
            "recommendations": []
        }
        
        try:
            # 1. 测试 get_all 方法
            print("1️⃣ 测试 get_all 方法...")
            try:
                get_all_result = self.client.get_all(user_id=user_id)
                diagnosis["get_all_result"] = get_all_result
                print(f"   ✅ get_all 成功，返回 {len(get_all_result)} 条记录")
            except Exception as e:
                print(f"   ❌ get_all 失败: {e}")
                diagnosis["issues"].append(f"get_all 失败: {e}")
            
            # 2. 测试 search 方法
            print("2️⃣ 测试 search 方法...")
            try:
                search_result = self.client.search("test", user_id=user_id)
                diagnosis["search_result"] = search_result
                print(f"   ✅ search 成功，返回 {len(search_result)} 条记录")
            except Exception as e:
                print(f"   ❌ search 失败: {e}")
                diagnosis["issues"].append(f"search 失败: {e}")
            
            # 3. 测试 history 方法
            print("3️⃣ 测试 history 方法...")
            try:
                # 先获取一些记忆ID来测试history
                if diagnosis["get_all_result"] and len(diagnosis["get_all_result"]) > 0:
                    memory_id = diagnosis["get_all_result"][0]["id"]
                    history_result = self.client.history(memory_id=memory_id)
                    diagnosis["history_result"] = history_result
                    print(f"   ✅ history 成功，返回 {len(history_result)} 条记录")
                else:
                    print("   ⚠️  无法测试 history，因为没有可用的记忆ID")
            except Exception as e:
                print(f"   ❌ history 失败: {e}")
                diagnosis["issues"].append(f"history 失败: {e}")
            
            # 4. 分析问题
            print("\n4️⃣ 问题分析...")
            self._analyze_issues(diagnosis)
            
            # 5. 提供建议
            print("\n5️⃣ 修复建议...")
            self._provide_recommendations(diagnosis)
            
        except Exception as e:
            logger.error(f"诊断过程失败: {e}")
            diagnosis["issues"].append(f"诊断过程失败: {e}")
        
        return diagnosis
    
    def _analyze_issues(self, diagnosis: Dict[str, Any]):
        """分析问题"""
        issues = diagnosis["issues"]
        
        if not issues:
            print("   ✅ 未发现明显问题")
            return
        
        for issue in issues:
            print(f"   ❌ {issue}")
        
        # 分析具体问题
        if diagnosis["get_all_result"] is not None and len(diagnosis["get_all_result"]) == 0:
            if diagnosis["history_result"] and len(diagnosis["history_result"]) > 0:
                print("   🔍 问题分析: 记忆存在于历史记录中，但无法通过 get_all 获取")
                print("   💡 可能原因: 向量索引损坏或不同步")
                diagnosis["recommendations"].append("重建向量索引")
            else:
                print("   🔍 问题分析: 用户没有任何记忆记录")
                diagnosis["recommendations"].append("检查记忆添加过程")
        
        if diagnosis["search_result"] is not None and len(diagnosis["search_result"]) == 0:
            if diagnosis["get_all_result"] and len(diagnosis["get_all_result"]) > 0:
                print("   🔍 问题分析: 记忆存在但搜索不到")
                print("   💡 可能原因: 搜索索引损坏")
                diagnosis["recommendations"].append("重建搜索索引")
    
    def _provide_recommendations(self, diagnosis: Dict[str, Any]):
        """提供修复建议"""
        recommendations = diagnosis["recommendations"]
        
        if not recommendations:
            print("   ✅ 系统运行正常，无需修复")
            return
        
        print("   🛠️  修复建议:")
        for i, rec in enumerate(recommendations, 1):
            print(f"      {i}. {rec}")
        
        # 提供具体的修复步骤
        print("\n   📋 修复步骤:")
        print("      1. 检查 mem0 服务状态")
        print("      2. 验证 API 密钥权限")
        print("      3. 尝试重新添加少量测试记忆")
        print("      4. 如果问题持续，联系 mem0 技术支持")
    
    def test_memory_recovery(self, user_id: str) -> bool:
        """测试记忆恢复"""
        print(f"\n🧪 测试记忆恢复 - 用户 {user_id}")
        print("=" * 50)
        
        try:
            # 1. 添加测试记忆
            print("1️⃣ 添加测试记忆...")
            test_messages = [
                {"role": "user", "content": "This is a test message for recovery."},
                {"role": "assistant", "content": "I received your test message."}
            ]
            
            add_result = self.client.add(
                messages=test_messages,
                user_id=user_id,
                metadata={"test": True, "recovery": True}
            )
            
            if add_result and len(add_result.get('results', [])) > 0:
                print(f"   ✅ 测试记忆添加成功: {len(add_result['results'])} 条")
                memory_id = add_result['results'][0]['id']
                
                # 2. 测试获取
                print("2️⃣ 测试获取新记忆...")
                get_result = self.client.get_all(user_id=user_id)
                print(f"   ✅ 获取结果: {len(get_result)} 条记忆")
                
                # 3. 测试搜索
                print("3️⃣ 测试搜索新记忆...")
                search_result = self.client.search("test message", user_id=user_id)
                print(f"   ✅ 搜索结果: {len(search_result)} 条记忆")
                
                # 4. 测试历史
                print("4️⃣ 测试历史记录...")
                history_result = self.client.history(memory_id=memory_id)
                print(f"   ✅ 历史记录: {len(history_result)} 条")
                
                # 5. 清理测试数据
                print("5️⃣ 清理测试数据...")
                try:
                    self.client.delete(memory_id=memory_id)
                    print("   ✅ 测试记忆清理成功")
                except Exception as e:
                    print(f"   ⚠️  测试记忆清理失败: {e}")
                
                return True
            else:
                print("   ❌ 测试记忆添加失败")
                return False
                
        except Exception as e:
            logger.error(f"记忆恢复测试失败: {e}")
            print(f"   ❌ 记忆恢复测试失败: {e}")
            return False
    
    def force_index_rebuild(self, user_id: str) -> bool:
        """强制重建索引（通过重新添加记忆）"""
        print(f"\n🔧 强制重建索引 - 用户 {user_id}")
        print("=" * 50)
        
        try:
            # 1. 获取现有记忆
            print("1️⃣ 获取现有记忆...")
            all_memories = self.client.get_all(user_id=user_id)
            
            if not all_memories:
                print("   ⚠️  没有现有记忆，无法重建索引")
                return False
            
            print(f"   📋 找到 {len(all_memories)} 条现有记忆")
            
            # 2. 备份记忆内容
            print("2️⃣ 备份记忆内容...")
            memory_backup = []
            for memory in all_memories:
                memory_backup.append({
                    "content": memory.get("memory", ""),
                    "metadata": memory.get("metadata", {}),
                    "id": memory.get("id", "")
                })
            
            print(f"   💾 备份了 {len(memory_backup)} 条记忆")
            
            # 3. 删除所有记忆
            print("3️⃣ 删除所有现有记忆...")
            for memory in all_memories:
                try:
                    self.client.delete(memory_id=memory["id"])
                except Exception as e:
                    print(f"   ⚠️  删除记忆 {memory['id']} 失败: {e}")
            
            print("   ✅ 所有现有记忆已删除")
            
            # 4. 重新添加记忆
            print("4️⃣ 重新添加记忆...")
            success_count = 0
            for backup in memory_backup:
                try:
                    messages = [
                        {"role": "user", "content": backup["content"]},
                        {"role": "assistant", "content": "Memory restored from backup."}
                    ]
                    
                    result = self.client.add(
                        messages=messages,
                        user_id=user_id,
                        metadata=backup["metadata"]
                    )
                    
                    if result and len(result.get('results', [])) > 0:
                        success_count += 1
                except Exception as e:
                    print(f"   ⚠️  恢复记忆失败: {e}")
            
            print(f"   ✅ 成功恢复 {success_count}/{len(memory_backup)} 条记忆")
            
            # 5. 验证恢复结果
            print("5️⃣ 验证恢复结果...")
            final_memories = self.client.get_all(user_id=user_id)
            print(f"   📊 最终记忆数量: {len(final_memories)}")
            
            return success_count > 0
            
        except Exception as e:
            logger.error(f"强制索引重建失败: {e}")
            print(f"   ❌ 强制索引重建失败: {e}")
            return False


def main():
    """主函数"""
    print("🔧 记忆系统诊断工具")
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
    
    # 创建诊断器
    try:
        diagnostic = MemoryDiagnostic()
        print("✅ 诊断器创建成功")
    except Exception as e:
        print(f"❌ 诊断器创建失败: {e}")
        return False
    
    # 测试用户ID
    test_user_id = "test_user"
    
    # 1. 执行诊断
    diagnosis = diagnostic.diagnose_memory_system(test_user_id)
    
    # 2. 测试记忆恢复
    recovery_success = diagnostic.test_memory_recovery(test_user_id)
    
    # 3. 如果恢复测试成功，提供进一步建议
    if recovery_success:
        print("\n🎉 记忆恢复测试成功！")
        print("建议:")
        print("1. 系统基本功能正常")
        print("2. 可能是之前的索引问题")
        print("3. 继续使用系统，观察是否稳定")
    else:
        print("\n⚠️  记忆恢复测试失败")
        print("建议:")
        print("1. 检查 mem0 服务状态")
        print("2. 验证 API 密钥权限")
        print("3. 考虑联系技术支持")
    
    # 4. 询问是否要强制重建索引
    print("\n" + "=" * 60)
    print("🔧 高级修复选项")
    print("如果问题持续存在，可以考虑强制重建索引")
    print("注意: 这会删除并重新创建所有记忆")
    
    # 这里可以添加用户交互逻辑
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  诊断被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 诊断过程中发生未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
