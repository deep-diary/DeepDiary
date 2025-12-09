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
from typing import Optional, Dict
from pathlib import Path
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
            url = f"{self.api_url}/asset/{asset_id}/thumbnail"
            params = {"size": size} if size else {}
            
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
                        
                        logger.info(f"成功获取缩略图: {asset_id} -> {file_path}")
                        return file_path
                    else:
                        logger.error(f"获取缩略图失败: {response.status} - {await response.text()}")
                        return None
        except Exception as e:
            logger.error(f"获取缩略图异常: {e}")
            return None

