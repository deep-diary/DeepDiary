#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 Immich search/person 端点
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, project_root)

from deepweb.services.cloud_communication.immich_client import ImmichClient
from deepweb.config.config_manager import ConfigManager


async def test_search_person():
    """测试搜索人物功能"""
    print("="*60)
    print("测试 Immich search/person 端点")
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
        print(f"❌ 加载配置失败: {e}")
        return
    
    # 初始化 Immich 客户端
    try:
        immich_client = ImmichClient(immich_config)
        if not immich_client.enabled:
            print("❌ Immich 客户端未启用")
            return
        print("\n✅ Immich 客户端初始化成功")
    except Exception as e:
        print(f"❌ 初始化 Immich 客户端失败: {e}")
        return
    
    # 测试搜索人物
    test_person_name = "Alex"
    print(f"\n{'='*60}")
    print(f"测试搜索人物: {test_person_name}")
    print("="*60)
    
    try:
        person = await immich_client.get_person_by_name(test_person_name)
        
        if person:
            print(f"\n✅ 成功找到人物:")
            print(f"  ID: {person.get('id')}")
            print(f"  姓名: {person.get('name')}")
            print(f"  缩略图路径: {person.get('thumbnailPath')}")
            print(f"  是否隐藏: {person.get('isHidden')}")
            print(f"  是否收藏: {person.get('isFavorite')}")
            print(f"  更新时间: {person.get('updatedAt')}")
        else:
            print(f"\n⚠️  未找到人物: {test_person_name}")
    except Exception as e:
        print(f"\n❌ 搜索人物失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("测试结束")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_search_person())

