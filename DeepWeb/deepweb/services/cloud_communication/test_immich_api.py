#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Immich API 测试脚本
用于测试 Immich API 的各种功能，特别是人物相关的 API

使用方法:
    python test_immich_api.py

作者: DeepDiary Team
日期: 2025-01-27
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from deepweb.services.cloud_communication.immich_client import ImmichClient
from deepweb.config.config_manager import ConfigManager


async def test_get_persons(immich_client: ImmichClient):
    """测试获取人物列表"""
    print("\n" + "="*60)
    print("测试 1: 获取人物列表")
    print("="*60)
    
    try:
        await immich_client._ensure_authenticated()
        
        import aiohttp
        # Immich API 官方文档: https://api.immich.app/endpoints/people
        # GET /api/people - 获取所有人物信息
        person_url = f"{immich_client.api_url}/people"
        
        print(f"\n使用官方端点: {person_url}")
        async with aiohttp.ClientSession(timeout=immich_client.timeout) as session:
            headers = await immich_client._get_headers()
            async with session.get(person_url, headers=headers) as response:
                print(f"状态码: {response.status}")
                if response.status == 200:
                    persons_data = await response.json()
                    # 处理不同的响应格式
                    if isinstance(persons_data, list):
                        persons = persons_data
                    elif isinstance(persons_data, dict) and "items" in persons_data:
                        persons = persons_data["items"]
                    elif isinstance(persons_data, dict) and "data" in persons_data:
                        persons = persons_data["data"]
                    else:
                        persons = []
                    
                    if persons:
                        print(f"✅ 成功获取 {len(persons)} 个人物")
                        if persons:
                            print("\n前 5 个人物信息:")
                            for i, person in enumerate(persons[:5], 1):
                                print(f"  {i}. ID: {person.get('id')}, 名称: {person.get('name')}")
                        return persons
                    else:
                        print("⚠️  返回空列表")
                        return []
                else:
                    error_text = await response.text()
                    print(f"❌ 错误: {error_text[:500]}")
                    return []
    except Exception as e:
        print(f"异常: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_get_timeline_buckets(immich_client: ImmichClient, person_id: str):
    """测试获取 timeline buckets 列表"""
    print("\n" + "="*60)
    print(f"测试 2-1: 获取 Timeline Buckets 列表 (personId={person_id[:20]}...)")
    print("="*60)
    
    try:
        await immich_client._ensure_authenticated()
        
        import aiohttp
        # 尝试获取时间桶列表
        buckets_url = f"{immich_client.api_url}/timeline/buckets"
        params = {"personId": person_id}
        
        async with aiohttp.ClientSession(timeout=immich_client.timeout) as session:
            async with session.get(
                buckets_url,
                headers=await immich_client._get_headers(),
                params=params
            ) as response:
                print(f"请求 URL: {buckets_url}")
                print(f"请求参数: {params}")
                print(f"状态码: {response.status}")
                
                if response.status == 200:
                    buckets_data = await response.json()
                    print(f"\n响应数据:")
                    print(f"  类型: {type(buckets_data)}")
                    if isinstance(buckets_data, list):
                        print(f"  找到 {len(buckets_data)} 个时间桶")
                        if buckets_data:
                            print(f"  前 5 个时间桶:")
                            for i, bucket in enumerate(buckets_data[:5], 1):
                                print(f"    {i}. {bucket}")
                        return buckets_data
                    elif isinstance(buckets_data, dict):
                        print(f"  响应键: {list(buckets_data.keys())}")
                        return buckets_data
                    return buckets_data
                else:
                    error_text = await response.text()
                    print(f"❌ 错误: {error_text[:500]}")
                    return None
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_timeline_bucket(immich_client: ImmichClient, person_id: str, time_bucket: str = "2024"):
    """测试 timeline/bucket API"""
    print("\n" + "="*60)
    print(f"测试 2-2: Timeline Bucket API (personId={person_id[:20]}..., timeBucket={time_bucket})")
    print("="*60)
    
    try:
        await immich_client._ensure_authenticated()
        
        import aiohttp
        bucket_url = f"{immich_client.api_url}/timeline/bucket"
        params = {
            "personId": person_id,
            "timeBucket": time_bucket
        }
        
        async with aiohttp.ClientSession(timeout=immich_client.timeout) as session:
            async with session.get(
                bucket_url,
                headers=await immich_client._get_headers(),
                params=params
            ) as response:
                print(f"请求 URL: {bucket_url}")
                print(f"请求参数: {params}")
                print(f"状态码: {response.status}")
                
                if response.status == 200:
                    bucket_data = await response.json()
                    print(f"\n响应数据结构:")
                    print(f"  键: {list(bucket_data.keys())}")
                    
                    if "id" in bucket_data:
                        asset_ids = bucket_data["id"]
                        print(f"\n找到 {len(asset_ids)} 个资产 ID")
                        if asset_ids:
                            print(f"  前 5 个资产 ID:")
                            for i, asset_id in enumerate(asset_ids[:5], 1):
                                print(f"    {i}. {asset_id}")
                    
                    # 打印其他有用的信息
                    if "fileCreatedAt" in bucket_data:
                        dates = bucket_data["fileCreatedAt"]
                        print(f"\n文件创建时间范围:")
                        if dates:
                            print(f"  最早: {dates[-1]}")
                            print(f"  最新: {dates[0]}")
                    
                    return bucket_data
                else:
                    error_text = await response.text()
                    print(f"错误: {error_text[:500]}")
                    return None
    except Exception as e:
        print(f"异常: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_search_person_assets(immich_client: ImmichClient, person_name: str):
    """测试搜索人物资产"""
    print("\n" + "="*60)
    print(f"测试 3: 搜索人物资产 (person_name={person_name})")
    print("="*60)
    
    try:
        asset_ids = await immich_client.search_person_assets(person_name, limit=10)
        print(f"找到 {len(asset_ids)} 个资产")
        if asset_ids:
            print(f"\n前 5 个资产 ID:")
            for i, asset_id in enumerate(asset_ids[:5], 1):
                print(f"  {i}. {asset_id}")
        return asset_ids
    except Exception as e:
        print(f"异常: {e}")
        import traceback
        traceback.print_exc()
        return []


async def test_get_person_thumbnails(immich_client: ImmichClient, person_name: str):
    """测试获取人物缩略图"""
    print("\n" + "="*60)
    print(f"测试 4: 获取人物缩略图 (person_name={person_name})")
    print("="*60)
    
    try:
        thumbnail_paths = await immich_client.get_person_thumbnails_by_name(person_name, limit=5)
        print(f"成功获取 {len(thumbnail_paths)} 张缩略图")
        if thumbnail_paths:
            print(f"\n缩略图路径:")
            for i, path in enumerate(thumbnail_paths[:5], 1):
                import os
                size = os.path.getsize(path) if os.path.exists(path) else 0
                print(f"  {i}. {path} ({size} bytes)")
        return thumbnail_paths
    except Exception as e:
        print(f"异常: {e}")
        import traceback
        traceback.print_exc()
        return []


async def main():
    """主测试函数"""
    print("="*60)
    print("Immich API 测试脚本")
    print("="*60)
    print("\n测试数据:")
    print("  - personId: 9bf2d16c-2364-43ec-be4c-ebbe9d520051")
    print("  - 人物姓名: Alex")
    print("="*60)
    
    # 加载配置
    try:
        config_manager = ConfigManager()
        all_config = config_manager.get_config()
        immich_config = all_config.get("immich", {})
        print(f"\n配置信息:")
        print(f"  API URL: {immich_config.get('api_url')}")
        print(f"  User: {immich_config.get('user')}")
        print(f"  Email: {immich_config.get('email')}")
        print(f"  Has API Key: {bool(immich_config.get('api_key'))}")
    except Exception as e:
        print(f"加载配置失败: {e}")
        return
    
    # 创建 Immich 客户端
    immich_client = ImmichClient(immich_config)
    if not immich_client.enabled:
        print("\n❌ Immich 客户端未启用，请检查配置")
        return
    
    print("\n✅ Immich 客户端初始化成功")
    
    # 测试 1: 获取人物列表
    persons = await test_get_persons(immich_client)
    
    # 使用指定的测试人物（如果列表为空）
    if not persons:
        print("\n⚠️  未获取到人物列表，使用指定的测试人物")
        # 使用用户提供的测试数据
        test_person_id = "9bf2d16c-2364-43ec-be4c-ebbe9d520051"
        test_person_name = "Alex"
        print(f"\n使用指定测试人物: {test_person_name} (ID: {test_person_id})")
    else:
        # 从列表中查找 Alex，如果找不到则使用第一个
        test_person = None
        for person in persons:
            if person.get("name", "").lower() == "alex":
                test_person = person
                break
        
        if not test_person:
            test_person = persons[0]
        
        test_person_id = test_person.get("id")
        test_person_name = test_person.get("name", "Unknown")
        
        print(f"\n选择测试人物: {test_person_name} (ID: {test_person_id[:20]}...)")
    
    # 测试 2: Timeline Bucket API（主要方法）
    # 注意：/api/people/{personId}/assets 端点不存在，直接使用 timeline/bucket API
    asset_ids = []
    print("\n使用 timeline/bucket API 获取人物资产...")
    
    # 先尝试获取可用的时间桶列表
    buckets = await test_get_timeline_buckets(immich_client, test_person_id)
    
    # 如果获取到时间桶列表，使用它们
    if buckets:
        if isinstance(buckets, list):
            time_buckets = buckets
        elif isinstance(buckets, dict) and "buckets" in buckets:
            time_buckets = buckets["buckets"]
        else:
            time_buckets = []
        
        if time_buckets:
            print(f"\n使用获取到的时间桶列表: {time_buckets[:5]}...")
            for bucket_item in time_buckets[:10]:  # 限制为前 10 个
                # 从时间桶字典中提取 timeBucket 字段
                if isinstance(bucket_item, dict):
                    time_bucket = bucket_item.get("timeBucket")
                else:
                    time_bucket = str(bucket_item)
                
                if time_bucket:
                    bucket_data = await test_timeline_bucket(immich_client, test_person_id, time_bucket)
                    if bucket_data and bucket_data.get("id"):
                        asset_ids_from_bucket = bucket_data.get("id", [])
                        if asset_ids_from_bucket:
                            print(f"✅ 时间桶 {time_bucket} 有数据，找到 {len(asset_ids_from_bucket)} 个资产")
                            asset_ids.extend(asset_ids_from_bucket[:10])  # 限制为前 10 个
                            break
    
    # 如果还是没有数据，尝试用户提供的格式 "20"
    if not asset_ids:
        print("\n尝试用户提供的 timeBucket 格式...")
        time_buckets = ["20", "2024", "2023", "2022", "2021", "2020"]
        for time_bucket in time_buckets:
            bucket_data = await test_timeline_bucket(immich_client, test_person_id, time_bucket)
            if bucket_data and bucket_data.get("id"):
                asset_ids_from_bucket = bucket_data.get("id", [])
                if asset_ids_from_bucket:
                    print(f"✅ 时间桶 {time_bucket} 有数据，找到 {len(asset_ids_from_bucket)} 个资产")
                    asset_ids = asset_ids_from_bucket[:10]  # 限制为前 10 个
                    break
    
    # 测试 3: 搜索人物资产（使用人物名称）
    # 如果 timeline/bucket 已经获取到资产 ID，跳过名称搜索
    if not asset_ids:
        asset_ids = await test_search_person_assets(immich_client, test_person_name)
    
    # 测试 4: 获取缩略图（只测试前 2 张）
    if asset_ids and len(asset_ids) > 0:
        print(f"\n找到 {len(asset_ids)} 个资产 ID，开始测试缩略图下载...")
        print(f"\n开始下载缩略图（限制 2 张）...")
        # 直接使用 get_asset_thumbnail 方法
        thumbnail_paths = []
        for asset_id in asset_ids[:2]:
            try:
                print(f"  正在下载资产 {asset_id[:20]}... 的缩略图...")
                thumbnail_path = await immich_client.get_asset_thumbnail(asset_id, size="thumbnail")
                if thumbnail_path:
                    import os
                    size = os.path.getsize(thumbnail_path) if os.path.exists(thumbnail_path) else 0
                    thumbnail_paths.append(thumbnail_path)
                    print(f"  ✅ 成功: {thumbnail_path} ({size} bytes)")
                else:
                    print(f"  ⚠️  返回 None")
            except Exception as e:
                print(f"  ❌ 获取资产 {asset_id[:20]}... 缩略图失败: {e}")
        
        if thumbnail_paths:
            print(f"\n✅ 测试完成！成功获取 {len(thumbnail_paths)} 张缩略图")
        else:
            print(f"\n⚠️  未获取到缩略图")
    else:
        print(f"\n⚠️  未找到人物资产，跳过缩略图测试")
    
    print("\n" + "="*60)
    print("测试结束")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

