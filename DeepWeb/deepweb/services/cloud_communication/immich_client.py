#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Immich Client for DeepWeb
用于从 Immich 服务器获取图片的客户端

作者: DeepDiary Team
日期: 2025-01-09
"""

import aiohttp
import tempfile
import os
from typing import Optional, Dict, List
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ImmichClient:
    """Immich API 客户端，用于获取图片"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化 Immich 客户端
        
        Args:
            config: Immich 配置字典，包含:
                - api_url: Immich API 地址 (例如: http://127.0.0.1:2283/api)
                - api_key: API 密钥
                - email: 登录邮箱（可选，用于获取 Bearer token）
                - password: 登录密码（可选，用于获取 Bearer token）
                - timeout: 请求超时时间（秒），默认 30
        """
        config = config or {}
        self.api_url = config.get("api_url", "").rstrip("/")
        self.api_key = config.get("api_key", "")
        self.email = config.get("email", "")
        self.password = config.get("password", "")
        self.timeout = aiohttp.ClientTimeout(total=int(config.get("timeout", 30)))
        self.access_token = None
        
        # 检查配置
        if not self.api_url:
            self.enabled = False
            logger.warning("Immich API URL 未配置，图片获取功能将被禁用")
        elif not self.api_key and (not self.email or not self.password):
            self.enabled = False
            logger.warning("Immich 认证信息不完整（需要 api_key 或 email+password），图片获取功能将被禁用")
        else:
            self.enabled = True
            logger.info(f"Immich 客户端已初始化: API={self.api_url}")
    
    async def _get_headers(self) -> dict:
        """获取 API 请求头，优先使用 Bearer token"""
        if self.access_token:
            return {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }
        return {
            "x-api-key": self.api_key,
            "Accept": "application/json"
        }
    
    async def _ensure_authenticated(self):
        """确保已认证，如果需要则登录获取 token"""
        if self.access_token:
            return
        
        # 如果有 email 和 password，尝试登录获取 token
        if self.email and self.password:
            try:
                login_url = f"{self.api_url}/auth/login"
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.post(
                        login_url,
                        json={"email": self.email, "password": self.password},
                        headers={"Content-Type": "application/json"}
                    ) as response:
                        if response.status in [200, 201]:
                            result = await response.json()
                            self.access_token = result.get("accessToken")
                            if self.access_token:
                                logger.info("已通过登录获取 Bearer token")
            except Exception as e:
                logger.warning(f"登录获取 token 失败，将使用 api_key: {e}")
    
    async def get_asset_info(self, asset_id: str) -> Optional[Dict]:
        """
        获取资产信息
        
        Args:
            asset_id: 资产 ID
            
        Returns:
            资产信息字典，如果获取失败返回 None
        """
        if not self.enabled:
            logger.warning("Immich 客户端未启用，无法获取资产信息")
            return None
        
        try:
            await self._ensure_authenticated()
            # 使用正确的 API 端点：/api/assets/{id} (复数)
            url = f"{self.api_url}/assets/{asset_id}"
            logger.info(f"请求资产信息 URL: {url}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url, headers=await self._get_headers()) as response:
                    if response.status == 200:
                        asset_info = await response.json()
                        logger.info(f"成功获取资产信息: asset_id={asset_id}")
                        return asset_info
                    else:
                        error_text = await response.text()
                        logger.error(f"获取资产信息失败: {response.status} - {error_text[:200]}")
                        return None
        except Exception as e:
            logger.error(f"获取资产信息异常: {e}")
            return None
    
    async def download_asset(self, asset_id: str, save_path: Optional[str] = None) -> Optional[str]:
        """
        下载资产图片到本地文件
        
        Args:
            asset_id: 资产 ID
            save_path: 保存路径（可选，如果不提供则使用临时文件）
            
        Returns:
            保存的文件路径，如果下载失败返回 None
        """
        logger.info(f"开始下载 Immich 资产: asset_id={asset_id}, api_url={self.api_url}")
        
        if not self.enabled:
            logger.warning("Immich 客户端未启用，无法下载资产")
            return None
        
        try:
            logger.info("确保已认证...")
            await self._ensure_authenticated()
            logger.info(f"认证完成，access_token={'已设置' if self.access_token else '未设置'}")
            
            # 使用正确的 API 端点：/api/assets/{id}/original (复数 assets，路径 /original)
            download_url = f"{self.api_url}/assets/{asset_id}/original"
            logger.info(f"请求下载 URL: {download_url}")
            
            headers = await self._get_headers()
            logger.debug(f"请求头: {list(headers.keys())}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(download_url, headers=headers) as response:
                    logger.info(f"下载响应状态: {response.status}")
                    
                    if response.status == 200:
                        # 读取图片数据
                        logger.info("开始读取图片数据...")
                        image_data = await response.read()
                        image_size = len(image_data)
                        logger.info(f"图片数据读取完成: {image_size} bytes")
                        
                        # 确定保存路径
                        if save_path:
                            file_path = save_path
                        else:
                            # 创建临时文件
                            temp_file = tempfile.NamedTemporaryFile(
                                suffix=".jpg",
                                delete=False
                            )
                            file_path = temp_file.name
                            temp_file.close()
                            logger.info(f"创建临时文件: {file_path}")
                        
                        # 保存图片
                        with open(file_path, "wb") as f:
                            f.write(image_data)
                        
                        # 验证文件
                        if os.path.exists(file_path):
                            actual_size = os.path.getsize(file_path)
                            logger.info(f"成功下载资产图片: asset_id={asset_id}, path={file_path}, size={actual_size} bytes")
                            return file_path
                        else:
                            logger.error(f"文件保存后不存在: {file_path}")
                            return None
                    else:
                        # 下载失败
                        error_text = await response.text()
                        logger.error(f"下载资产失败: {response.status} - {error_text[:200]}")
                        return None
        except Exception as e:
            import traceback
            logger.error(f"下载资产异常: {e}, traceback: {traceback.format_exc()}")
            return None
    
    async def get_asset_thumbnail(self, asset_id: str, size: str = "thumbnail") -> Optional[str]:
        """
        获取资产缩略图
        
        Args:
            asset_id: 资产 ID
            size: 缩略图尺寸 (thumbnail, small, medium, large)
            
        Returns:
            缩略图文件路径，如果获取失败返回 None
        """
        if not self.enabled:
            logger.warning("Immich 客户端未启用，无法获取缩略图")
            return None
        
        try:
            await self._ensure_authenticated()
            # 尝试多个可能的端点（单数和复数形式）
            possible_urls = [
                f"{self.api_url}/assets/{asset_id}/thumbnail",  # 复数形式（优先）
                f"{self.api_url}/asset/{asset_id}/thumbnail",   # 单数形式
            ]
            params = {"size": size} if size else {}
            
            for url in possible_urls:
            
                async with aiohttp.ClientSession(timeout=self.timeout) as session:
                    async with session.get(
                        url,
                        headers=await self._get_headers(),
                        params=params
                    ) as response:
                        if response.status == 200:
                            # 读取图片数据
                            image_data = await response.read()
                            
                            # 创建临时文件
                            temp_file = tempfile.NamedTemporaryFile(
                                suffix=".jpg",
                                delete=False
                            )
                            file_path = temp_file.name
                            temp_file.close()
                            
                            # 保存图片
                            with open(file_path, "wb") as f:
                                f.write(image_data)
                            
                            logger.info(f"成功获取缩略图: {asset_id} -> {file_path} (使用端点: {url})")
                            return file_path
                        elif response.status == 404:
                            # 404 表示端点不存在，尝试下一个
                            logger.debug(f"端点 {url} 返回 404，尝试下一个")
                            continue
                        else:
                            error_text = await response.text()
                            logger.warning(f"端点 {url} 返回 {response.status}: {error_text[:200]}")
                            continue
            
            # 所有端点都失败
            logger.error(f"所有缩略图端点都失败: {asset_id}")
            return None
        except Exception as e:
            logger.error(f"获取缩略图异常: {e}")
            return None
    
    async def get_person_by_name(self, person_name: str) -> Optional[Dict]:
        """
        根据人物名称获取人物信息
        
        Args:
            person_name: 人物名称
            
        Returns:
            人物信息字典，包含 id 等字段，如果未找到返回 None
        """
        if not self.enabled:
            logger.warning("Immich 客户端未启用，无法搜索人物")
            return None
        
        try:
            await self._ensure_authenticated()
            
            # Immich API 官方文档: https://api.immich.app/endpoints/search/searchPerson
            # GET /api/search/person?name={name} - 直接搜索人物
            search_url = f"{self.api_url}/search/person"
            params = {"name": person_name}
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                headers = await self._get_headers()
                async with session.get(search_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        persons = await response.json()
                        
                        # 返回值是列表格式，直接处理
                        if persons:
                            # 返回第一个匹配的人物（通常搜索结果已经按相关性排序）
                            matched_person = persons[0]
                            logger.info(f"找到人物: {person_name}, ID: {matched_person.get('id')}")
                            return matched_person
                        else:
                            logger.warning(f"未找到名称为 '{person_name}' 的人物")
                            return None
                    else:
                        error_text = await response.text()
                        logger.error(f"搜索人物失败: {response.status} - {error_text[:200]}")
                        return None
        except Exception as e:
            logger.error(f"搜索人物异常: {e}")
            import traceback
            logger.debug(f"异常详情: {traceback.format_exc()}")
            return None
    
    async def get_timeline_buckets(self, person_id: str) -> List[str]:
        """
        获取人物的时间桶列表
        
        Args:
            person_id: 人物 ID
            
        Returns:
            时间桶字符串列表（格式如：'2024-04-01'）
        """
        if not self.enabled:
            logger.warning("Immich 客户端未启用，无法获取时间桶列表")
            return []
        
        try:
            await self._ensure_authenticated()
            
            # GET /api/timeline/buckets?personId={personId}
            buckets_url = f"{self.api_url}/timeline/buckets"
            params = {"personId": person_id}
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                headers = await self._get_headers()
                async with session.get(buckets_url, headers=headers, params=params) as response:
                    if response.status == 200:
                        buckets_data = await response.json()
                        
                        # 处理响应格式：可能是列表或字典
                        if isinstance(buckets_data, list):
                            buckets = buckets_data
                        elif isinstance(buckets_data, dict) and "buckets" in buckets_data:
                            buckets = buckets_data["buckets"]
                        else:
                            buckets = []
                        
                        # 提取 timeBucket 字段
                        time_buckets = []
                        for bucket_item in buckets:
                            if isinstance(bucket_item, dict):
                                time_bucket = bucket_item.get("timeBucket")
                                if time_bucket:
                                    time_buckets.append(time_bucket)
                            else:
                                time_buckets.append(str(bucket_item))
                        
                        logger.info(f"获取到 {len(time_buckets)} 个时间桶")
                        return time_buckets
                    else:
                        error_text = await response.text()
                        logger.warning(f"获取时间桶列表失败: {response.status} - {error_text[:200]}")
                        return []
        except Exception as e:
            logger.error(f"获取时间桶列表异常: {e}")
            import traceback
            logger.debug(f"异常详情: {traceback.format_exc()}")
            return []
    
    async def get_person_assets_by_timeline(self, person_id: str, time_buckets: Optional[List[str]] = None) -> List[str]:
        """
        通过 timeline/bucket API 获取人物的资产 ID 列表
        
        Args:
            person_id: 人物 ID
            time_buckets: 时间桶列表，如果不提供则先获取时间桶列表
            
        Returns:
            资产 ID 列表
        """
        if not self.enabled:
            logger.warning("Immich 客户端未启用，无法获取人物资产")
            return []
        
        try:
            await self._ensure_authenticated()
            
            asset_ids = []
            
            # 如果没有提供 time_buckets，先获取时间桶列表
            if time_buckets is None:
                time_buckets = await self.get_timeline_buckets(person_id)
                if not time_buckets:
                    logger.warning("无法获取时间桶列表，尝试默认日期格式")
                    # 如果获取失败，尝试日期格式（最近几个月）
                    from datetime import timedelta
                    current_date = datetime.now()
                    time_buckets = []
                    for i in range(12):  # 最近 12 个月
                        date = current_date - timedelta(days=30 * i)
                        # 格式化为 YYYY-MM-01（月初）
                        time_buckets.append(date.strftime("%Y-%m-01"))
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                headers = await self._get_headers()
                
                # 遍历每个时间桶
                for time_bucket in time_buckets:
                    try:
                        # 使用 timeline/bucket API
                        # API: GET /api/timeline/bucket?personId={personId}&timeBucket={timeBucket}
                        bucket_url = f"{self.api_url}/timeline/bucket"
                        params = {
                            "personId": person_id,
                            "timeBucket": time_bucket
                        }
                        
                        async with session.get(bucket_url, headers=headers, params=params) as response:
                            if response.status == 200:
                                bucket_data = await response.json()
                                
                                # 从响应中提取 id 数组
                                if isinstance(bucket_data, dict) and "id" in bucket_data:
                                    ids = bucket_data["id"]
                                    if isinstance(ids, list):
                                        asset_ids.extend(ids)
                                        logger.debug(f"时间桶 {time_bucket} 找到 {len(ids)} 个资产")
                                    else:
                                        logger.warning(f"时间桶 {time_bucket} 的 id 字段不是列表")
                                else:
                                    logger.debug(f"时间桶 {time_bucket} 没有资产数据")
                            elif response.status == 404:
                                # 404 表示该时间桶没有数据，继续下一个
                                logger.debug(f"时间桶 {time_bucket} 没有数据（404）")
                                continue
                            else:
                                error_text = await response.text()
                                logger.warning(f"获取时间桶 {time_bucket} 失败: {response.status} - {error_text[:200]}")
                    except Exception as e:
                        logger.warning(f"处理时间桶 {time_bucket} 时出错: {e}")
                        continue
            
            # 去重
            asset_ids = list(set(asset_ids))
            logger.info(f"找到 {len(asset_ids)} 个唯一资产")
            return asset_ids
            
        except Exception as e:
            logger.error(f"获取人物资产异常: {e}")
            import traceback
            logger.debug(f"异常详情: {traceback.format_exc()}")
            return []
    
    async def search_person_assets(self, person_name: str, limit: int = 50) -> List[str]:
        """
        根据人物名称搜索相关的资产 ID 列表
        
        Args:
            person_name: 人物名称
            limit: 返回的最大数量，默认 50（实际返回可能超过此值）
            
        Returns:
            资产 ID 列表
        """
        if not self.enabled:
            logger.warning("Immich 客户端未启用，无法搜索人物资产")
            return []
        
        try:
            # 1. 先获取人物信息
            person = await self.get_person_by_name(person_name)
            if not person:
                return []
            
            person_id = person.get("id")
            if not person_id:
                logger.error("人物信息中没有 ID")
                return []
            
            # 2. 使用 timeline/bucket API 获取资产（主要方法）
            # 注意：/api/people/{personId}/assets 端点不存在，使用 timeline/bucket API
            asset_ids = await self.get_person_assets_by_timeline(person_id)
            
            # 3. 限制返回数量
            if limit > 0 and len(asset_ids) > limit:
                asset_ids = asset_ids[:limit]
            
            logger.info(f"找到人物 '{person_name}' 的 {len(asset_ids)} 个资产")
            return asset_ids
            
        except Exception as e:
            logger.error(f"搜索人物资产异常: {e}")
            import traceback
            logger.debug(f"异常详情: {traceback.format_exc()}")
            return []
    
    async def get_person_thumbnails_by_id(self, person_id: str, limit: int = 50) -> List[str]:
        """
        根据人物 ID 获取人物所有照片的缩略图路径列表
        
        Args:
            person_id: 人物 ID
            limit: 返回的最大数量，默认 50
            
        Returns:
            缩略图文件路径列表
        """
        # 获取人物的资产 ID 列表
        asset_ids = await self.get_person_assets_by_timeline(person_id)
        if not asset_ids:
            return []
        
        # 限制返回数量
        if limit > 0 and len(asset_ids) > limit:
            asset_ids = asset_ids[:limit]
        
        # 下载所有缩略图
        thumbnail_paths = []
        for asset_id in asset_ids:
            try:
                thumbnail_path = await self.get_asset_thumbnail(asset_id, size="thumbnail")
                if thumbnail_path:
                    thumbnail_paths.append(thumbnail_path)
            except Exception as e:
                logger.warning(f"获取资产 {asset_id} 缩略图失败: {e}")
                continue
        
        logger.info(f"成功获取 {len(thumbnail_paths)} 张缩略图")
        return thumbnail_paths
    
    async def get_person_thumbnails_by_name(self, person_name: str, limit: int = 50) -> List[str]:
        """
        根据人物名称获取人物所有照片的缩略图路径列表
        
        Args:
            person_name: 人物名称
            limit: 返回的最大数量，默认 50
            
        Returns:
            缩略图文件路径列表
        """
        # 先通过名称获取人物信息
        person = await self.get_person_by_name(person_name)
        if not person:
            logger.warning(f"未找到名称为 '{person_name}' 的人物")
            return []
        
        person_id = person.get("id")
        if not person_id:
            logger.error("人物信息中没有 ID")
            return []
        
        # 调用 by_id 方法
        return await self.get_person_thumbnails_by_id(person_id, limit)

