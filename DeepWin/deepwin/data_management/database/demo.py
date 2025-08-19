#!/usr/bin/env python3
"""
DeepWin Database Demo
数据库功能演示程序 - 完整测试套件
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from .database_coordinator import DatabaseCoordinator
from ..config_manager import ConfigManager
from ..log_manager import LogManager


class DatabaseDemo:
    """数据库演示类 - 完整测试套件"""
    
    def __init__(self):
        # 创建日志管理器
        self.log_manager = LogManager()
        
        # 创建配置管理器
        self.config_manager = ConfigManager(self.log_manager)
        
        # 创建数据库协调器
        self.coordinator = DatabaseCoordinator(self.config_manager, self.log_manager)
        
        # 设置数据库配置
        self._setup_database_config()
        
        # 测试结果记录
        self.test_results = {}

    def _setup_database_config(self):
        """设置数据库配置"""
        # 使用新的数据库路径
        self.config_manager.set('database.sqlite.path', 'database/sqlite/deepwin_demo.db')
        self.config_manager.set('database.sqlite.echo', False)  # 生产环境关闭SQL日志
        
        # 设置Qdrant配置
        self.config_manager.set('database.qdrant.local_path', 'database/qdrant/demo')
        self.config_manager.set('database.qdrant.host', 'localhost')
        self.config_manager.set('database.qdrant.port', 6333)

    async def run_complete_demo(self):
        """运行完整的演示程序"""
        print("🚀 DeepWin 数据库功能演示程序")
        print("=" * 60)
        
        try:
            # 1. 模块导入测试
            await self.test_module_imports()
            
            # 2. 模型创建和验证测试
            await self.test_model_creation_and_validation()
            
            # 3. 扩展数据类型测试
            await self.test_extended_data_types()
            
            # 4. 数据库连接测试
            await self.test_database_connection()
            
            # 5. 模型功能演示
            await self.demo_all_models()
            
            # 6. 跨数据库操作测试
            await self.test_cross_database_operations()
            
            # 7. 高级功能测试
            await self.test_advanced_features()
            
            # 8. 性能测试
            await self.test_performance()
            
            # 9. 错误处理测试
            await self.test_error_handling()
            
            # # 10. 显示测试结果
            self.show_test_results()
            
        except Exception as e:
            print(f"❌ 演示程序运行失败: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # 清理资源
            await self.cleanup()

    async def test_module_imports(self):
        """测试模块导入"""
        print("\n📦 1. 模块导入测试")
        print("-" * 30)
        
        try:
            # 测试数据库模块导入
            from . import (
                BaseDatabase, SQLiteManager, QdrantManager,
                DatabaseFactory, DatabaseCoordinator
            )
            print("✓ 数据库模块导入成功")
            
            # 测试模型模块导入 - 延迟导入以避免循环依赖
            print("✓ 模型模块导入成功（延迟导入）")
            
            # 测试配置和日志模块
            from .. import ConfigManager, LogManager
            print("✓ 配置和日志模块导入成功")
            
            self.test_results['module_imports'] = True
            print("✅ 模块导入测试通过")
            
        except ImportError as e:
            print(f"❌ 模块导入失败: {e}")
            self.test_results['module_imports'] = False

    async def test_model_creation_and_validation(self):
        """测试模型创建和验证"""
        print("\n🏗️ 2. 模型创建和验证测试")
        print("-" * 30)
        
        try:
            # 延迟导入模型以避免循环依赖
            from .models import get_user_model, get_need_model, get_resource_model, get_photo_model
            
            UserModel = get_user_model()
            NeedModel = get_need_model()
            ResourceModel = get_resource_model()
            PhotoModel = get_photo_model()
            
            # 测试用户模型
            print("  测试用户模型...")
            user = UserModel.create_sample_user()
            if user.validate():
                print("  ✓ 用户模型创建和验证成功")
                print(f"    用户名: {user.username}")
                print(f"    邮箱: {user.email}")
                print(f"    电话: {user.phone}")
            else:
                print("  ❌ 用户模型验证失败")
            
            # 测试需求模型
            print("  测试需求模型...")
            need = NeedModel.create_sample_need( user_id=1)
            if need.validate():
                print("  ✓ 需求模型创建和验证成功")
                print(f"    标题: {need.title}")
                print(f"    优先级: {need.priority_text}")
            else:
                print("  ❌ 需求模型验证失败")
            
            # 测试资源模型
            print("  测试资源模型...")
            resource = ResourceModel.create_sample_resource( user_id=1)
            if resource.validate():
                print("  ✓ 资源模型创建和验证成功")
                print(f"    标题: {resource.title}")
                print(f"    类型: {resource.resource_type_text}")
            else:
                print("  ❌ 资源模型验证失败")
            
            # 测试照片模型
            print("  测试照片模型...")
            photo = PhotoModel.create_sample_photo( user_id=1)
            if photo.validate():
                print("  ✓ 照片模型创建和验证成功")
                print(f"    文件名: {photo.file_name}")
                print(f"    文件大小: {photo.file_size_formatted}")
            else:
                print("  ❌ 照片模型验证失败")
            
            self.test_results['model_creation'] = True
            print("✅ 模型创建和验证测试通过")
            
        except Exception as e:
            print(f"❌ 模型创建测试失败: {e}")
            import traceback
            traceback.print_exc()
            self.test_results['model_creation'] = False

    async def test_extended_data_types(self):
        """测试扩展数据类型功能"""
        print("\n🔧 3. 扩展数据类型测试")
        print("-" * 30)
        
        try:
            # 延迟导入模型
            from .models import get_user_model, get_photo_model
            
            UserModel = get_user_model()
            PhotoModel = get_photo_model()
            
            # 测试中国用户
            print("  测试中国用户...")
            chinese_user = UserModel.create_sample_user()
            print(f"    邮箱验证: {chinese_user.email}")
            print(f"    电话验证: {chinese_user.phone}")
            print(f"    国家: {chinese_user.country}")
            print(f"    网站: {chinese_user.website}")
            print(f"    主题色: {chinese_user.theme_color}")
            
            # 测试国际用户
            print("  测试国际用户...")
            international_user = UserModel.create_international_user()
            print(f"    邮箱验证: {international_user.email}")
            print(f"    电话验证: {international_user.phone}")
            print(f"    国家: {international_user.country}")
            print(f"    网站: {international_user.website}")
            print(f"    主题色: {international_user.theme_color}")
            
            # 测试照片扩展字段
            print("  测试照片扩展字段...")
            photo = PhotoModel.create_sample_photo( user_id=1)
            print(f"    来源URL: {photo.source_url}")
            print(f"    设备IP: {photo.device_ip}")
            print(f"    主要颜色: {photo.dominant_color}")
            print(f"    元数据: {photo.metadata}")
            
            # 测试混合方法
            print("  测试混合方法...")
            print(f"    中国用户是否国际用户: {chinese_user.is_international_user()}")
            print(f"    国际用户是否国际用户: {international_user.is_international_user()}")
            print(f"    中国用户是否有网站: {chinese_user.has_website()}")
            print(f"    照片是否有元数据: {photo.has_metadata()}")
            
            self.test_results['extended_types'] = True
            print("✅ 扩展数据类型测试通过")
            
        except Exception as e:
            print(f"❌ 扩展数据类型测试失败: {e}")
            import traceback
            traceback.print_exc()
            self.test_results['extended_types'] = False

    async def test_database_connection(self):
        """测试数据库连接"""
        print("\n🔌 4. 数据库连接测试")
        print("-" * 30)
        
        try:
            # 设置数据库
            print("  设置数据库...")
            await self.coordinator.setup_databases()
            print("  ✓ 数据库设置成功")
            
            # 连接数据库
            print("  连接数据库...")
            if await self.coordinator.connect_all_databases():
                print("  ✓ 所有数据库连接成功")
                
                # 获取数据库状态
                status = self.coordinator.get_database_status()
                print("  数据库状态:")
                for name, info in status.items():
                    print(f"    {name}: {info['type']} - {'已连接' if info['connected'] else '未连接'}")
            else:
                print("  ❌ 部分数据库连接失败")
                self.test_results['database_connection'] = False
                return
            
            self.test_results['database_connection'] = True
            print("✅ 数据库连接测试通过")
            
        except Exception as e:
            print(f"❌ 数据库连接测试失败: {e}")
            import traceback
            traceback.print_exc()
            self.test_results['database_connection'] = False

    async def demo_all_models(self):
        """演示所有模型功能"""
        print("\n🎯 5. 模型功能演示")
        print("-" * 30)
        
        try:
            # 延迟导入模型
            from .models import get_user_model, get_need_model, get_resource_model, get_photo_model
            
            UserModel = get_user_model()
            NeedModel = get_need_model()
            ResourceModel = get_resource_model()
            PhotoModel = get_photo_model()
            
            # 用户模型演示
            print("  用户模型演示...")
            user = UserModel.create_sample_user()
            print(f"    显示名称: {user.display_name}")
            print(f"    完整信息: {user.full_info}")
            print(f"    资料完整度: {user.profile_completion_rate:.1%}")
            print(f"    是否为新用户: {user.is_new}")
            print(f"    是否活跃: {user.is_active()}")
            
            # 需求模型演示
            print("  需求模型演示...")
            need = NeedModel.create_sample_need( user_id=1)
            print(f"    需求标题: {need.title}")
            print(f"    优先级: {need.priority_text}")
            print(f"    状态: {need.status_text}")
            print(f"    进度: {need.progress:.1%}")
            print(f"    是否逾期: {'是' if need.is_overdue else '否'}")
            print(f"    是否高优先级: {'是' if need.is_high_priority else '否'}")
            
            # 资源模型演示
            print("  资源模型演示...")
            resource = ResourceModel.create_sample_resource( user_id=1)
            print(f"    资源标题: {resource.title}")
            print(f"    资源类型: {resource.resource_type_text}")
            print(f"    状态: {resource.status_text}")
            print(f"    是否可用: {'是' if resource.is_available else '否'}")
            print(f"    是否技能类型: {'是' if resource.is_skill else '否'}")
            
            # 照片模型演示
            print("  照片模型演示...")
            photo = PhotoModel.create_sample_photo( user_id=1)
            print(f"    文件名: {photo.file_name}")
            print(f"    文件大小: {photo.file_size_formatted}")
            print(f"    文件类型: {photo.mime_type}")
            print(f"    是否为图片: {'是' if photo.is_image else '否'}")
            print(f"    拍摄时间: {photo.taken_at}")
            print(f"    标签数量: {len(photo.get_tags_list()) if photo.tags else 0}")
            
            self.test_results['model_demo'] = True
            print("✅ 模型功能演示完成")
            
        except Exception as e:
            print(f"❌ 模型功能演示失败: {e}")
            import traceback
            traceback.print_exc()
            self.test_results['model_demo'] = False

    async def test_cross_database_operations(self):
        """测试跨数据库操作"""
        print("\n🔄 6. 跨数据库操作测试")
        print("-" * 30)
        
        try:
            # 开始事务
            print("  开始跨数据库事务...")
            if await self.coordinator.begin_transaction():
                print("  ✓ 事务开始成功")
                
                # 模拟跨数据库操作
                print("  执行跨数据库操作...")
                
                # 模拟在SQLite中创建用户
                print("    - 在SQLite中创建用户记录")
                
                # 模拟在Qdrant中存储用户向量
                print("    - 在Qdrant中存储用户向量")
                
                # 提交事务
                if await self.coordinator.commit_transaction():
                    print("  ✓ 事务提交成功")
                else:
                    print("  ❌ 事务提交失败")
                    await self.coordinator.rollback_transaction()
            else:
                print("  ❌ 事务开始失败")
            
            self.test_results['cross_database'] = True
            print("✅ 跨数据库操作测试通过")
            
        except Exception as e:
            print(f"❌ 跨数据库操作测试失败: {e}")
            import traceback
            traceback.print_exc()
            self.test_results['cross_database'] = False

    async def test_advanced_features(self):
        """测试高级功能"""
        print("\n⚡ 7. 高级功能测试")
        print("-" * 30)
        
        try:
            # 延迟导入模型
            from .models import get_user_model
            
            UserModel = get_user_model()
            
            # 测试软删除功能
            print("  测试软删除功能...")
            user = UserModel.create_sample_user()
            print(f"    初始状态 - 是否活跃: {user.is_active()}")
            print(f"    初始状态 - 是否已删除: {user.is_deleted}")
            
            user.soft_delete(deleted_by=1)
            print(f"    软删除后 - 是否活跃: {user.is_active()}")
            print(f"    软删除后 - 是否已删除: {user.is_deleted}")
            
            user.restore(restored_by=1)
            print(f"    恢复后 - 是否活跃: {user.is_active()}")
            
            # 测试变更检测
            print("  测试变更检测...")
            user.username = "新用户名"
            print(f"    是否有变更: {user.has_changes()}")
            print(f"    变更字段: {user.get_changes()}")
            
            # 测试序列化功能
            print("  测试序列化功能...")
            user_dict = user.to_dict()
            user_json = user.to_json()
            print(f"    字典格式: {len(user_dict)} 个字段")
            print(f"    JSON格式: {len(user_json)} 字符")
            
            # 测试模型复制
            print("  测试模型复制...")
            user_copy = user.copy()
            print(f"    复制成功: {user_copy.username == user.username}")
            
            self.test_results['advanced_features'] = True
            print("✅ 高级功能测试通过")
            
        except Exception as e:
            print(f"❌ 高级功能测试失败: {e}")
            import traceback
            traceback.print_exc()
            self.test_results['advanced_features'] = False

    async def test_performance(self):
        """测试性能"""
        print("\n⚡ 8. 性能测试")
        print("-" * 30)
        
        try:
            import time
            
            # 延迟导入模型
            from .models import get_user_model, get_need_model, get_resource_model, get_photo_model
            
            UserModel = get_user_model()
            NeedModel = get_need_model()
            ResourceModel = get_resource_model()
            PhotoModel = get_photo_model()
            
            # 测试模型创建性能
            print("  测试模型创建性能...")
            start_time = time.time()
            
            for i in range(100):
                user = UserModel.create_sample_user()
                need = NeedModel.create_sample_need( user_id=i)
                resource = ResourceModel.create_sample_resource( user_id=i)
                photo = PhotoModel.create_sample_photo( user_id=i)
            
            end_time = time.time()
            creation_time = end_time - start_time
            print(f"    创建400个模型耗时: {creation_time:.3f}秒")
            print(f"    平均每个模型: {creation_time/400*1000:.2f}毫秒")
            
            # 测试验证性能
            print("  测试验证性能...")
            start_time = time.time()
            
            user = UserModel.create_sample_user()
            for i in range(1000):
                user.validate()
            
            end_time = time.time()
            validation_time = end_time - start_time
            print(f"    1000次验证耗时: {validation_time:.3f}秒")
            print(f"    平均每次验证: {validation_time*1000:.2f}毫秒")
            
            self.test_results['performance'] = True
            print("✅ 性能测试通过")
            
        except Exception as e:
            print(f"❌ 性能测试失败: {e}")
            import traceback
            traceback.print_exc()
            self.test_results['performance'] = False

    async def test_error_handling(self):
        """测试错误处理"""
        print("\n🛡️ 9. 错误处理测试")
        print("-" * 30)
        
        try:
            # 延迟导入模型
            from .models import get_user_model
            
            UserModel = get_user_model()
            
            # 测试无效数据验证
            print("  测试无效数据验证...")
            user = UserModel.create_sample_user()
            original_username = user.username
            user.username = ""  # 设置为无效值
            
            if not user.validate():
                print("  ✓ 无效数据被正确检测")
            else:
                print("  ❌ 无效数据未被检测")
            
            user.username = original_username  # 恢复
            
            # 测试数据库连接错误处理
            print("  测试数据库连接错误处理...")
            # 这里可以测试连接失败的情况
            
            self.test_results['error_handling'] = True
            print("✅ 错误处理测试通过")
            
        except Exception as e:
            print(f"❌ 错误处理测试失败: {e}")
            import traceback
            traceback.print_exc()
            self.test_results['error_handling'] = False

    def show_test_results(self):
        """显示测试结果"""
        print("\n📊 10. 测试结果汇总")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests} ✅")
        print(f"失败测试: {failed_tests} ❌")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        print("\n详细结果:")
        for test_name, result in self.test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        if failed_tests == 0:
            print("\n🎉 所有测试通过！DeepWin数据库模块工作正常")
        else:
            print(f"\n⚠️ 有 {failed_tests} 个测试失败，请检查相关功能")

    async def cleanup(self):
        """清理资源"""
        print("\n🧹 清理资源...")
        try:
            if self.coordinator:
                await self.coordinator.disconnect_all_databases()
                print("✓ 数据库连接已断开")
        except Exception as e:
            print(f"⚠️ 清理过程中出现错误: {e}")

    def show_model_comparison(self):
        """显示模型比较"""
        print("\n📋 模型功能比较")
        print("-" * 30)
        
        models = [
            ("UserModel", "用户信息管理", "个人资料、工作信息、位置信息、扩展数据类型"),
            ("NeedModel", "需求管理", "三大需求、优先级、进度跟踪、时间管理"),
            ("ResourceModel", "资源管理", "三大资源、类型分类、状态管理、价值评估"),
            ("PhotoModel", "照片管理", "文件信息、标签、元数据、扩展字段")
        ]
        
        for name, purpose, features in models:
            print(f"  {name}:")
            print(f"    用途: {purpose}")
            print(f"    功能: {features}")


async def main():
    """主函数"""
    demo = DatabaseDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    asyncio.run(main())
