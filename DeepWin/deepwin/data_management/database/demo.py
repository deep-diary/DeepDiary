#!/usr/bin/env python3
"""
DeepWin Database Demo
数据库功能演示程序
"""

import asyncio
from datetime import datetime

from .database_coordinator import DatabaseCoordinator
from .models.user_model import UserModel
from .models.need_model import NeedModel
from .models.resource_model import ResourceModel
from .models.photo_model import PhotoModel
from ..config_manager import ConfigManager
from ..log_manager import LogManager


class DatabaseDemo:
    """数据库演示类"""
    
    def __init__(self):
        # 创建日志管理器
        self.log_manager = LogManager()
        
        # 创建配置管理器
        self.config_manager = ConfigManager(self.log_manager)
        
        # 创建数据库协调器
        self.coordinator = DatabaseCoordinator(self.config_manager)
        
        # 设置数据库配置
        self._setup_database_config()

    def _setup_database_config(self):
        """设置数据库配置"""
        # 设置SQLite配置
        self.config_manager.set('database.sqlite.path', 'deepwin_demo.db')
        self.config_manager.set('database.sqlite.echo', True)
        
        # 设置Qdrant配置
        self.config_manager.set('database.qdrant.local_path', './qdrant_data')
        self.config_manager.set('database.qdrant.host', 'localhost')
        self.config_manager.set('database.qdrant.port', 6333)

    async def run_demo(self):
        """运行演示程序"""
        print("=== DeepWin 数据库演示程序 ===")
        
        try:
            # 设置数据库
            print("\n1. 设置数据库...")
            await self.coordinator.setup_databases()
            
            # 连接数据库
            print("\n2. 连接数据库...")
            if await self.coordinator.connect_all_databases():
                print("✓ 所有数据库连接成功")
            else:
                print("❌ 部分数据库连接失败")
                return
            
            # 演示用户模型
            print("\n3. 演示用户模型...")
            await self.demo_user_model()
            
            # 演示需求模型
            print("\n4. 演示需求模型...")
            await self.demo_need_model()
            
            # 演示资源模型
            print("\n5. 演示资源模型...")
            await self.demo_resource_model()
            
            # 演示照片模型
            print("\n6. 演示照片模型...")
            await self.demo_photo_model()
            
            # 演示跨数据库操作
            print("\n7. 演示跨数据库操作...")
            await self.demo_cross_database_operations()
            
            # 显示模型比较
            print("\n8. 模型比较...")
            self.show_model_comparison()
            
            # 断开数据库连接
            print("\n9. 断开数据库连接...")
            await self.coordinator.disconnect_all_databases()
            print("✓ 所有数据库断开连接成功")
            
        except Exception as e:
            print(f"❌ 演示程序运行失败: {e}")
            import traceback
            traceback.print_exc()

    async def demo_user_model(self):
        """演示用户模型"""
        print("  创建示例用户...")
        user = UserModel.create_sample_user(self.config_manager)
        
        print("  验证用户数据...")
        if user.validate():
            print("  ✓ 用户数据验证通过")
        else:
            print("  ❌ 用户数据验证失败")
        
        print(f"  用户信息: {user.display_name}")
        print(f"  完整信息: {user.full_info}")
        print(f"  资料完整度: {user.profile_completion_rate:.1%}")

    async def demo_need_model(self):
        """演示需求模型"""
        print("  创建示例需求...")
        need = NeedModel.create_sample_need(self.config_manager, user_id=1)
        
        print("  验证需求数据...")
        if need.validate():
            print("  ✓ 需求数据验证通过")
        else:
            print("  ❌ 需求数据验证失败")
        
        print(f"  需求标题: {need.title}")
        print(f"  优先级: {need.priority_text}")
        print(f"  状态: {need.status_text}")
        print(f"  进度: {need.progress:.1%}")
        print(f"  是否逾期: {'是' if need.is_overdue else '否'}")

    async def demo_resource_model(self):
        """演示资源模型"""
        print("  创建示例资源...")
        resource = ResourceModel.create_sample_resource(self.config_manager, user_id=1)
        
        print("  验证资源数据...")
        if resource.validate():
            print("  ✓ 资源数据验证通过")
        else:
            print("  ❌ 资源数据验证失败")
        
        print(f"  资源标题: {resource.title}")
        print(f"  资源类型: {resource.resource_type_text}")
        print(f"  状态: {resource.status_text}")
        print(f"  是否可用: {'是' if resource.is_available else '否'}")

    async def demo_photo_model(self):
        """演示照片模型"""
        print("  创建示例照片...")
        photo = PhotoModel.create_sample_photo(self.config_manager, user_id=1)
        
        print("  验证照片数据...")
        if photo.validate():
            print("  ✓ 照片数据验证通过")
        else:
            print("  ❌ 照片数据验证失败")
        
        print(f"  文件名: {photo.file_name}")
        print(f"  文件大小: {photo.file_size_formatted}")
        print(f"  文件类型: {photo.mime_type}")
        print(f"  是否为图片: {'是' if photo.is_image else '否'}")

    async def demo_cross_database_operations(self):
        """演示跨数据库操作"""
        print("  开始跨数据库事务...")
        if await self.coordinator.begin_transaction():
            print("  ✓ 事务开始成功")
            
            # 模拟一些操作
            print("  执行跨数据库操作...")
            
            # 提交事务
            if await self.coordinator.commit_transaction():
                print("  ✓ 事务提交成功")
            else:
                print("  ❌ 事务提交失败")
        else:
            print("  ❌ 事务开始失败")

    def show_model_comparison(self):
        """显示模型比较"""
        print("  模型功能比较:")
        
        models = [
            ("UserModel", "用户信息管理", "个人资料、工作信息、位置信息"),
            ("NeedModel", "需求管理", "三大需求、优先级、进度跟踪"),
            ("ResourceModel", "资源管理", "三大资源、类型分类、状态管理"),
            ("PhotoModel", "照片管理", "文件信息、标签、元数据")
        ]
        
        for name, purpose, features in models:
            print(f"    {name}: {purpose}")
            print(f"      功能: {features}")


async def main():
    """主函数"""
    demo = DatabaseDemo()
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
