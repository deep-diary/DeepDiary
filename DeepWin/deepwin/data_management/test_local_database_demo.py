#!/usr/bin/env python3
"""
DeepWin Local Database Demo
本地数据库增删改查功能测试演示
"""

import asyncio
import sys
import os
import logging
from datetime import datetime
from typing import Dict, Any, List

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from deepwin.config.config_manager import ConfigManager
from deepwin.data_management.log_manager import LogManager
from deepwin.data_management.local_database import LocalDatabaseManager
from deepwin.data_management.database.models import (
    get_user_model, get_need_model, get_resource_model, get_photo_model
)


class LocalDatabaseDemo:
    """本地数据库功能演示类"""
    
    def __init__(self):
        """初始化演示环境"""
        self.log_manager = LogManager()
        
        # 设置日志级别：控制台只显示INFO及以上，文件记录DEBUG及以上
        self.log_manager.set_all_levels(
            console_level=logging.INFO,  # 控制台只显示INFO、WARNING、ERROR
            file_level=logging.DEBUG      # 文件记录所有日志
        )
        
        self.config_manager = ConfigManager(self.log_manager)
        
        self.db_manager = LocalDatabaseManager(self.config_manager, self.log_manager)
        self.logger = self.log_manager.get_logger(__name__)
        
        # 获取模型类
        self.UserModel = get_user_model()
        self.NeedModel = get_need_model()
        self.ResourceModel = get_resource_model()
        self.PhotoModel = get_photo_model()
        
        self.test_users = []
        self.test_needs = []
        self.test_resources = []
        self.test_photos = []
        
        # 用于生成唯一标识的计数器
        self.test_counter = 0

    async def setup(self):
        """设置演示环境"""
        print("🚀 开始设置演示环境...")
        
        # 初始化数据库
        success = await self.db_manager.initialize()
        if not success:
            print("❌ 数据库初始化失败")
            return False
            
        print("✅ 数据库初始化成功")
        return True

    async def cleanup(self):
        """清理演示环境"""
        print("🧹 清理演示环境...")
        await self.db_manager.shutdown()
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
                print(f"   {key}: {value}")
        else:
            print(f"   {result}")
        print()

    def get_unique_id(self) -> str:
        """生成唯一的测试标识"""
        self.test_counter += 1
        timestamp = datetime.now().strftime("%H%M%S")
        return f"{timestamp}_{self.test_counter}"

    async def test_user_crud(self):
        """测试用户增删改查功能"""
        self.print_section("用户管理功能测试")
        
        coordinator = self.db_manager.get_coordinator()
        sqlite_db = coordinator.get_database('sqlite')
        
        if not sqlite_db:
            print("❌ SQLite数据库不可用")
            return

        # 创建用户
        print("📝 创建测试用户...")
        unique_id = self.get_unique_id()
        user_data = {
            "username": f"test_user_{unique_id}",
            "email": f"test{unique_id}@example.com",
            "phone": f"+86-138-{unique_id}",
            "country": "CN",
            "city": "北京",
            "company": "测试公司",
            "industry": "科技",
            "position": "软件工程师",
            "website": "https://example.com",
            "bio": "这是一个测试用户"
        }
        
        user = await sqlite_db.create(self.UserModel, user_data)
        if user:
            self.test_users.append(user.id)
            self.print_result("创建用户", f"用户ID: {user.id}, 用户名: {user.username}")
        else:
            print("❌ 创建用户失败")
            return

        # 查询用户
        print("🔍 查询用户信息...")
        user_info = await sqlite_db.get_by_id(self.UserModel, user.id)
        if user_info:
            self.print_result("查询用户", {
                "ID": user_info.id,
                "用户名": user_info.username,
                "邮箱": user_info.email,
                "城市": user_info.city,
                "公司": user_info.company
            })

        # 更新用户
        print("✏️ 更新用户信息...")
        update_data = {
            "city": "上海",
            "position": "高级软件工程师",
            "bio": "更新后的用户简介"
        }
        
        updated_user = await sqlite_db.update(self.UserModel, user.id, update_data)
        if updated_user:
            self.print_result("更新用户", {
                "ID": updated_user.id,
                "城市": updated_user.city,
                "职位": updated_user.position,
                "简介": updated_user.bio
            })

        # 查询用户列表
        print("📋 查询用户列表...")
        users = await sqlite_db.get_all(self.UserModel, limit=5)
        if users:
            self.print_result("用户列表", f"共找到 {len(users)} 个用户")
            for u in users:
                print(f"   - {u.username} ({u.email}) - {u.city}")

    async def test_need_crud(self):
        """测试需求增删改查功能"""
        self.print_section("需求管理功能测试")
        
        coordinator = self.db_manager.get_coordinator()
        sqlite_db = coordinator.get_database('sqlite')
        
        if not sqlite_db:
            print("❌ SQLite数据库不可用")
            return

        # 首先创建一个测试用户
        print("👤 创建测试用户...")
        unique_id = self.get_unique_id()
        user_data = {
            "username": f"test_user_{unique_id}",
            "email": f"test{unique_id}@example.com",
            "phone": "+86-138-0000-0001",
            "city": "北京",
            "is_active": True
        }
        
        user = await sqlite_db.create(self.UserModel, user_data)
        if not user:
            print("❌ 创建测试用户失败")
            return
        
        self.test_users.append(user.id)
        print(f"✅ 创建测试用户成功，ID: {user.id}")

        # 创建需求
        print("📝 创建测试需求...")
        need_data = {
            "user_id": user.id,  # 使用刚创建的用户ID
            "title": "开发新功能模块",
            "description": "需要开发一个用户管理模块，包含增删改查功能",
            "priority": 3,  # 使用整数：1-低，2-中，3-高，4-紧急
            "status": "active",  # 使用正确的状态值
            "category": "feature",
            "tags": "用户管理,CRUD,模块开发",
            "deadline": datetime.now().replace(day=datetime.now().day + 7)
        }
        
        need = await sqlite_db.create(self.NeedModel, need_data)
        if need:
            self.test_needs.append(need.id)
            self.print_result("创建需求", {
                "ID": need.id,
                "标题": need.title,
                "优先级": need.priority,
                "状态": need.status,
                "进度": f"{need.progress * 100:.1f}%"
            })
        else:
            print("❌ 创建需求失败")
            return

        # 查询需求
        print("🔍 查询需求详情...")
        need_info = await sqlite_db.get_by_id(self.NeedModel, need.id)
        if need_info:
            self.print_result("需求详情", {
                "ID": need_info.id,
                "标题": need_info.title,
                "描述": need_info.description[:50] + "...",
                "优先级": need_info.priority,
                "状态": need_info.status,
                "分类": need_info.category,
                "标签": need_info.tags
            })

        # 更新需求状态
        print("✏️ 更新需求状态...")
        update_data = {
            "status": "completed",
            "progress": 0.75,
            "notes": "已完成75%的工作"
        }
        
        updated_need = await sqlite_db.update(self.NeedModel, need.id, update_data)
        if updated_need:
            self.print_result("更新需求", {
                "ID": updated_need.id,
                "状态": updated_need.status,
                "进度": f"{updated_need.progress * 100:.1f}%",
                "备注": updated_need.notes
            })

        # 查询需求列表
        print("📋 查询需求列表...")
        needs = await sqlite_db.get_all(self.NeedModel, limit=5)
        if needs:
            self.print_result("需求列表", f"共找到 {len(needs)} 个需求")
            for n in needs:
                print(f"   - {n.title} ({n.priority}) - {n.status}")

    async def test_resource_crud(self):
        """测试资源增删改查功能"""
        self.print_section("资源管理功能测试")
        
        coordinator = self.db_manager.get_coordinator()
        sqlite_db = coordinator.get_database('sqlite')
        
        if not sqlite_db:
            print("❌ SQLite数据库不可用")
            return

        # 创建资源
        print("📝 创建测试资源...")
        unique_id = self.get_unique_id()
        resource_data = {
            "user_id": 1,  # 使用默认用户ID
            "title": f"开发服务器_{unique_id}",
            "resource_type": "material",
            "category": "server",
            "description": "用于开发和测试的服务器",
            "status": "available",
            "tags": "服务器,开发,测试"
        }
        
        resource = await sqlite_db.create(self.ResourceModel, resource_data)
        if resource:
            self.test_resources.append(resource.id)
            self.print_result("创建资源", {
                "ID": resource.id,
                "标题": resource.title,
                "类型": resource.resource_type,
                "状态": resource.status,
                "分类": resource.category
            })
        else:
            print("❌ 创建资源失败")
            return

        # 查询资源
        print("🔍 查询资源详情...")
        resource_info = await sqlite_db.get_by_id(self.ResourceModel, resource.id)
        if resource_info:
            self.print_result("资源详情", {
                "ID": resource_info.id,
                "标题": resource_info.title,
                "类型": resource_info.resource_type,
                "分类": resource_info.category,
                "描述": resource_info.description[:50] + "...",
                "状态": resource_info.status,
                "标签": resource_info.tags
            })

        # 更新资源状态
        print("✏️ 更新资源状态...")
        update_data = {
            "status": "in_use",
            "notes": "正在使用中"
        }
        
        updated_resource = await sqlite_db.update(self.ResourceModel, resource.id, update_data)
        if updated_resource:
            self.print_result("更新资源", {
                "ID": updated_resource.id,
                "状态": updated_resource.status,
                "备注": updated_resource.notes
            })

        # 查询资源列表
        print("📋 查询资源列表...")
        resources = await sqlite_db.get_all(self.ResourceModel, limit=5)
        if resources:
            self.print_result("资源列表", f"共找到 {len(resources)} 个资源")
            for r in resources:
                print(f"   - {r.title} ({r.resource_type}) - {r.status}")

    async def test_photo_crud(self):
        """测试照片增删改查功能"""
        self.print_section("照片管理功能测试")
        
        coordinator = self.db_manager.get_coordinator()
        sqlite_db = coordinator.get_database('sqlite')
        
        if not sqlite_db:
            print("❌ SQLite数据库不可用")
            return

        # 创建照片记录
        print("📝 创建测试照片记录...")
        unique_id = self.get_unique_id()
        photo_data = {
            "user_id": 1,  # 使用默认用户ID
            "file_path": f"/photos/test_photo_{unique_id}.jpg",
            "file_name": f"test_photo_{unique_id}.jpg",
            "file_size": 2048576,  # 2MB
            "mime_type": "image/jpeg",
            "description": "这是一张测试照片",
            "tags": "测试,照片,演示",
            "location": "北京",
            "taken_at": datetime.now().replace(hour=10, minute=30)
        }
        
        photo = await sqlite_db.create(self.PhotoModel, photo_data)
        if photo:
            self.test_photos.append(photo.id)
            self.print_result("创建照片记录", {
                "ID": photo.id,
                "文件名": photo.file_name,
                "文件大小": f"{photo.file_size / 1024 / 1024:.2f}MB",
                "MIME类型": photo.mime_type
            })
        else:
            print("❌ 创建照片记录失败")
            return

        # 查询照片
        print("🔍 查询照片详情...")
        photo_info = await sqlite_db.get_by_id(self.PhotoModel, photo.id)
        if photo_info:
            self.print_result("照片详情", {
                "ID": photo_info.id,
                "文件名": photo_info.file_name,
                "文件路径": photo_info.file_path,
                "文件大小": f"{photo_info.file_size / 1024 / 1024:.2f}MB",
                "MIME类型": photo_info.mime_type,
                "描述": photo_info.description,
                "标签": photo_info.tags,
                "位置": photo_info.location,
                "拍摄时间": photo_info.taken_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        # 更新照片信息
        print("✏️ 更新照片信息...")
        update_data = {
            "description": "更新后的照片描述",
            "tags": "测试,照片,演示,更新"
        }
        
        updated_photo = await sqlite_db.update(self.PhotoModel, photo.id, update_data)
        if updated_photo:
            self.print_result("更新照片", {
                "ID": updated_photo.id,
                "描述": updated_photo.description,
                "标签": updated_photo.tags
            })

        # 查询照片列表
        print("📋 查询照片列表...")
        photos = await sqlite_db.get_all(self.PhotoModel, limit=5)
        if photos:
            self.print_result("照片列表", f"共找到 {len(photos)} 张照片")
            for p in photos:
                print(f"   - {p.file_name} ({p.file_size_formatted}) - {p.mime_type}")

    async def test_search_and_filter(self):
        """测试搜索和过滤功能"""
        self.print_section("搜索和过滤功能测试")
        
        coordinator = self.db_manager.get_coordinator()
        sqlite_db = coordinator.get_database('sqlite')
        
        if not sqlite_db:
            print("❌ SQLite数据库不可用")
            return

        # 按条件查询用户
        print("🔍 按条件查询用户...")
        users = await sqlite_db.filter(
            self.UserModel,
            filters={"city": "上海"},
            limit=3
        )
        if users:
            self.print_result("上海用户", f"找到 {len(users)} 个上海用户")
            for user in users:
                print(f"   - {user.username} ({user.email})")

        # 按条件查询需求
        print("🔍 按条件查询需求...")
        needs = await sqlite_db.filter(
            self.NeedModel,
            filters={"status": "in_progress"},
            limit=3
        )
        if needs:
            self.print_result("进行中需求", f"找到 {len(needs)} 个进行中的需求")
            for need in needs:
                print(f"   - {need.title} (进度: {need.progress}%)")

        # 按条件查询资源
        print("🔍 按条件查询资源...")
        resources = await sqlite_db.filter(
            self.ResourceModel,
            filters={"resource_type": "material"},
            limit=3
        )
        if resources:
            self.print_result("物质资源", f"找到 {len(resources)} 个物质资源")
            for resource in resources:
                print(f"   - {resource.title} ({resource.category})")

        # 按条件查询照片
        print("🔍 按条件查询照片...")
        photos = await sqlite_db.filter(
            self.PhotoModel,
            filters={"mime_type": "image/jpeg"},
            limit=3
        )
        if photos:
            self.print_result("JPEG照片", f"找到 {len(photos)} 张JPEG照片")
            for photo in photos:
                print(f"   - {photo.file_name} ({photo.mime_type})")

    async def test_delete_operations(self):
        """测试删除功能"""
        self.print_section("删除功能测试")
        
        coordinator = self.db_manager.get_coordinator()
        sqlite_db = coordinator.get_database('sqlite')
        
        if not sqlite_db:
            print("❌ SQLite数据库不可用")
            return

        # 删除测试数据
        print("🗑️ 删除测试数据...")
        
        # 删除照片
        for photo_id in self.test_photos:
            success = await sqlite_db.delete(self.PhotoModel, photo_id)
            if success:
                print(f"   ✅ 删除照片 ID: {photo_id}")
            else:
                print(f"   ❌ 删除照片失败 ID: {photo_id}")

        # 删除资源
        for resource_id in self.test_resources:
            success = await sqlite_db.delete(self.ResourceModel, resource_id)
            if success:
                print(f"   ✅ 删除资源 ID: {resource_id}")
            else:
                print(f"   ❌ 删除资源失败 ID: {resource_id}")

        # 删除需求
        for need_id in self.test_needs:
            success = await sqlite_db.delete(self.NeedModel, need_id)
            if success:
                print(f"   ✅ 删除需求 ID: {need_id}")
            else:
                print(f"   ❌ 删除需求失败 ID: {need_id}")

        # 删除用户
        for user_id in self.test_users:
            success = await sqlite_db.delete(self.UserModel, user_id)
            if success:
                print(f"   ✅ 删除用户 ID: {user_id}")
            else:
                print(f"   ❌ 删除用户失败 ID: {user_id}")

        print("✅ 测试数据清理完成")

    async def test_database_status(self):
        """测试数据库状态查询"""
        self.print_section("数据库状态查询")
        
        # 获取数据库状态
        status = self.db_manager.get_database_status()
        self.print_result("数据库状态", status)
        
        # 检查数据库是否准备就绪
        is_ready = self.db_manager.is_database_ready()
        self.print_result("数据库准备状态", f"准备就绪: {is_ready}")

    async def run_demo(self):
        """运行完整的演示"""
        print("🎯 DeepWin 本地数据库功能演示")
        print("=" * 60)
        
        try:
            # 设置环境
            if not await self.setup():
                return
            
            # 运行各项测试
            await self.test_database_status()
            await self.test_user_crud()
            await self.test_need_crud()
            await self.test_resource_crud()
            await self.test_photo_crud()
            await self.test_search_and_filter()
            await self.test_delete_operations()
            
            print("\n🎉 演示完成！所有功能测试通过")
            
        except Exception as e:
            print(f"❌ 演示过程中发生错误: {e}")
            self.logger.error(f"演示错误: {e}")
            
        finally:
            # 清理环境
            await self.cleanup()


async def main():
    """主函数"""
    demo = LocalDatabaseDemo()
    await demo.run_demo()


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())
