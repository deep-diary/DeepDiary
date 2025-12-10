#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ImmichClient 完整功能测试脚本
测试 ImmichClient 类的所有主要功能
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, project_root)

from deepweb.services.cloud_communication.immich_client import ImmichClient
from deepweb.config.config_manager import ConfigManager


async def test_initialization():
    """测试客户端初始化"""
    print("="*60)
    print("测试 1: 客户端初始化")
    print("="*60)
    
    try:
        config_manager = ConfigManager()
        all_config = config_manager.get_config()
        immich_config = all_config.get("immich", {})
        
        print(f"\n配置信息:")
        print(f"  API URL: {immich_config.get('api_url')}")
        print(f"  User: {immich_config.get('user')}")
        print(f"  Email: {immich_config.get('email')}")
        print(f"  Has API Key: {bool(immich_config.get('api_key'))}")
        
        immich_client = ImmichClient(immich_config)
        
        if immich_client.enabled:
            print("\n✅ Immich 客户端初始化成功")
            return immich_client
        else:
            print("\n❌ Immich 客户端未启用")
            return None
    except Exception as e:
        print(f"\n❌ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_get_person_by_name(immich_client: ImmichClient, person_name: str):
    """测试通过名称搜索人物"""
    print("\n" + "="*60)
    print(f"测试 2: 通过名称搜索人物 (name={person_name})")
    print("="*60)
    
    try:
        person = await immich_client.get_person_by_name(person_name)
        
        if person:
            print(f"\n✅ 成功找到人物:")
            print(f"  ID: {person.get('id')}")
            print(f"  姓名: {person.get('name')}")
            print(f"  缩略图路径: {person.get('thumbnailPath')}")
            print(f"  是否隐藏: {person.get('isHidden')}")
            print(f"  是否收藏: {person.get('isFavorite')}")
            print(f"  更新时间: {person.get('updatedAt')}")
            return person
        else:
            print(f"\n⚠️  未找到人物: {person_name}")
            return None
    except Exception as e:
        print(f"\n❌ 搜索人物失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_get_timeline_buckets(immich_client: ImmichClient, person_id: str):
    """测试获取时间桶列表"""
    print("\n" + "="*60)
    print(f"测试 3: 获取时间桶列表 (person_id={person_id[:20]}...)")
    print("="*60)
    
    try:
        time_buckets = await immich_client.get_timeline_buckets(person_id)
        
        if time_buckets:
            print(f"\n✅ 成功获取 {len(time_buckets)} 个时间桶:")
            for i, bucket in enumerate(time_buckets[:10], 1):  # 只显示前10个
                print(f"  {i}. {bucket}")
            return time_buckets
        else:
            print("\n⚠️  未获取到时间桶")
            return []
    except Exception as e:
        print(f"\n❌ 获取时间桶失败: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_get_person_assets_by_timeline(immich_client: ImmichClient, person_id: str):
    """测试通过 timeline 获取人物资产"""
    print("\n" + "="*60)
    print(f"测试 4: 通过 timeline 获取人物资产 (person_id={person_id[:20]}...)")
    print("="*60)
    
    try:
        asset_ids = await immich_client.get_person_assets_by_timeline(person_id)
        
        if asset_ids:
            print(f"\n✅ 成功获取 {len(asset_ids)} 个资产 ID:")
            for i, asset_id in enumerate(asset_ids[:5], 1):  # 只显示前5个
                print(f"  {i}. {asset_id}")
            return asset_ids
        else:
            print("\n⚠️  未获取到资产")
            return []
    except Exception as e:
        print(f"\n❌ 获取资产失败: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_get_asset_thumbnail(immich_client: ImmichClient, asset_id: str):
    """测试获取单个资产缩略图"""
    print("\n" + "="*60)
    print(f"测试 5: 获取资产缩略图 (asset_id={asset_id[:20]}...)")
    print("="*60)
    
    try:
        thumbnail_path = await immich_client.get_asset_thumbnail(asset_id, size="thumbnail")
        
        if thumbnail_path:
            import os
            size = os.path.getsize(thumbnail_path) if os.path.exists(thumbnail_path) else 0
            print(f"\n✅ 成功获取缩略图:")
            print(f"  路径: {thumbnail_path}")
            print(f"  大小: {size} bytes")
            return thumbnail_path
        else:
            print("\n⚠️  未获取到缩略图")
            return None
    except Exception as e:
        print(f"\n❌ 获取缩略图失败: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_get_person_thumbnails_by_id(immich_client: ImmichClient, person_id: str, limit: int = 3):
    """测试通过 ID 获取人物所有缩略图"""
    print("\n" + "="*60)
    print(f"测试 6: 通过 ID 获取人物所有缩略图 (person_id={person_id[:20]}..., limit={limit})")
    print("="*60)
    
    try:
        thumbnail_paths = await immich_client.get_person_thumbnails_by_id(person_id, limit=limit)
        
        if thumbnail_paths:
            import os
            print(f"\n✅ 成功获取 {len(thumbnail_paths)} 张缩略图:")
            for i, path in enumerate(thumbnail_paths, 1):
                size = os.path.getsize(path) if os.path.exists(path) else 0
                print(f"  {i}. {path} ({size} bytes)")
            return thumbnail_paths
        else:
            print("\n⚠️  未获取到缩略图")
            return []
    except Exception as e:
        print(f"\n❌ 获取缩略图失败: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_get_person_thumbnails_by_name(immich_client: ImmichClient, person_name: str, limit: int = 3):
    """测试通过名称获取人物所有缩略图"""
    print("\n" + "="*60)
    print(f"测试 7: 通过名称获取人物所有缩略图 (person_name={person_name}, limit={limit})")
    print("="*60)
    
    try:
        thumbnail_paths = await immich_client.get_person_thumbnails_by_name(person_name, limit=limit)
        
        if thumbnail_paths:
            import os
            print(f"\n✅ 成功获取 {len(thumbnail_paths)} 张缩略图:")
            for i, path in enumerate(thumbnail_paths, 1):
                size = os.path.getsize(path) if os.path.exists(path) else 0
                print(f"  {i}. {path} ({size} bytes)")
            return thumbnail_paths
        else:
            print("\n⚠️  未获取到缩略图")
            return []
    except Exception as e:
        print(f"\n❌ 获取缩略图失败: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_search_person_assets(immich_client: ImmichClient, person_name: str):
    """测试搜索人物资产"""
    print("\n" + "="*60)
    print(f"测试 8: 搜索人物资产 (person_name={person_name})")
    print("="*60)
    
    try:
        asset_ids = await immich_client.search_person_assets(person_name, limit=10)
        
        if asset_ids:
            print(f"\n✅ 成功找到 {len(asset_ids)} 个资产 ID:")
            for i, asset_id in enumerate(asset_ids[:5], 1):  # 只显示前5个
                print(f"  {i}. {asset_id}")
            return asset_ids
        else:
            print("\n⚠️  未找到资产")
            return []
    except Exception as e:
        print(f"\n❌ 搜索资产失败: {e}")
        import traceback
        traceback.print_exc()
        return []


async def main():
    """主测试函数"""
    print("="*60)
    print("ImmichClient 完整功能测试")
    print("="*60)
    
    # 测试数据
    test_person_name = "Blue"
    test_person_id = "94777e17-bd75-4615-ac41-6f041b661af0"
    
    # 1. 初始化客户端
    immich_client = await test_initialization()
    if not immich_client:
        print("\n❌ 客户端初始化失败，终止测试")
        return
    
    # 2. 测试通过名称搜索人物
    person = await test_get_person_by_name(immich_client, test_person_name)
    if not person:
        print("\n⚠️  未找到测试人物，使用指定的 person_id")
        person_id = test_person_id
    else:
        person_id = person.get("id")
    
    # 3. 测试获取时间桶列表
    time_buckets = await test_get_timeline_buckets(immich_client, person_id)
    
    # 4. 测试获取人物资产
    asset_ids = await test_get_person_assets_by_timeline(immich_client, person_id)
    
    # 5. 测试获取单个资产缩略图（如果有资产）
    if asset_ids:
        await test_get_asset_thumbnail(immich_client, asset_ids[0])
    
    # 6. 测试通过 ID 获取人物所有缩略图
    await test_get_person_thumbnails_by_id(immich_client, person_id, limit=3)
    
    # 7. 测试通过名称获取人物所有缩略图
    await test_get_person_thumbnails_by_name(immich_client, test_person_name, limit=3)
    
    # 8. 测试搜索人物资产
    await test_search_person_assets(immich_client, test_person_name)
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

