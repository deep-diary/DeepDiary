#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat Service - 聊天业务逻辑服务层
处理聊天相关的业务逻辑，包括消息解析、状态管理等

作者: DeepDiary Team
日期: 2025-01-27
"""

import json
import base64
import tempfile
import os
import asyncio
import threading
import time
from typing import List, Dict, Any, Optional
from queue import Queue, Empty
import logging

# 导入 Immich 相关模块
try:
    from deepweb.services.cloud_communication.immich_api import ImmichAPI
    from deepweb.app_logic.cloud_com_logical.immich_logic import ImmichLogic
    from immich_python_sdk.models.asset_media_size import AssetMediaSize
except ImportError as e:
    ImmichAPI = None
    ImmichLogic = None
    AssetMediaSize = None


class ChatService:
    """
    聊天业务逻辑服务类
    
    职责：
    - 处理 WebSocket 消息的解析和转换
    - 管理聊天历史记录
    - 处理图片下载和转换
    - 管理记忆内容
    - 提供业务数据给 UI 层
    """
    
    def __init__(self, logger: logging.Logger, config_manager=None, immich_logic: Optional[ImmichLogic] = None):
        """
        初始化聊天服务
        
        Args:
            logger: 日志记录器
            config_manager: 配置管理器（可选）
            immich_logic: Immich 业务逻辑处理器（可选）
        """
        self.logger = logger
        self.config_manager = config_manager
        
        # 聊天历史记录
        self.chat_history: List[Dict[str, str]] = []
        
        # 记忆内容
        self.memory_markdown = "# 记忆显示区\n\n待开发功能..."
        
        # 注意：person_galleries 和 current_gallery_person 已废弃
        # 人物照片现在通过 Kiosk URL 在 iframe 中显示，不再使用 gallery
        # 保留这些属性以避免可能的引用错误，但不再使用
        self.person_galleries: Dict[str, List[str]] = {}
        self.current_gallery_person: Optional[str] = None
        
        # 照片展示模式相关状态
        self.current_mode: str = "chat"  # 当前模式：chat/slideshow/search
        self.last_person_name: Optional[str] = None  # 最后一次识别到的人物名称
        self.last_person_id: Optional[str] = None    # 最后一次识别到的人物ID
        self.last_kiosk_url: Optional[str] = None     # 最后一次收到的 Kiosk URL
        self.last_message_time: float = 0.0          # 最后一次消息的时间戳
        self.last_person_update_time: float = 0.0    # 最后一次人物更新的时间戳
        self.idle_threshold: float = 20.0            # 空闲阈值（秒）
        self.search_mode_enter_time: float = 0.0     # 进入搜索模式的时间戳
        self.search_mode_protection_period: float = 10.0  # 搜索模式保护期（秒），在此期间内忽略人物识别
        
        # LLM流式响应合并：存储当前正在接收的消息
        self.current_llm_message: Dict[str, Any] = {}
        
        # 临时文件管理
        self.temp_dir = tempfile.mkdtemp(prefix="chat_images_")
        self.temp_files: List[str] = []
        
        # Immich 业务逻辑处理器
        self.immich_logic = immich_logic
        if not self.immich_logic:
            self._init_immich_logic()
    
    def _init_immich_logic(self):
        """初始化 Immich 业务逻辑处理器"""
        if ImmichAPI is None or ImmichLogic is None:
            self.logger.warning("ImmichAPI 或 ImmichLogic 未导入，图片获取功能将被禁用")
            return
        
        try:
            # 从 config_manager 获取 Immich 配置
            if self.config_manager:
                all_config = self.config_manager.get_config()
                immich_config = all_config.get("immich", {})
                self.logger.info(f"从 config_manager 获取 Immich 配置: api_url={immich_config.get('api_url')}")
            else:
                # 如果没有 config_manager，尝试从环境变量获取
                immich_config = {
                    "api_url": os.getenv("IMMICH_API_URL", "http://127.0.0.1:2283/api"),
                    "api_key": os.getenv("IMMICH_API_KEY", ""),
                    "timeout": int(os.getenv("IMMICH_TIMEOUT", "30"))
                }
                self.logger.info(f"从环境变量获取 Immich 配置: api_url={immich_config.get('api_url')}")
            
            # 如果配置了 API key，创建 API 客户端和业务逻辑处理器
            if immich_config.get("api_key"):
                immich_api = ImmichAPI(immich_config)
                if immich_api.enabled:
                    self.immich_logic = ImmichLogic(immich_api)
                    self.logger.info(f"Immich 业务逻辑处理器初始化成功: api_url={immich_api.api_url}")
                else:
                    self.logger.warning("Immich API 初始化失败，将使用降级方案")
                    self.immich_logic = None
            else:
                self.logger.info("Immich 配置未设置，将使用降级方案（base64 图片）")
        except Exception as e:
            self.logger.error(f"初始化 Immich 业务逻辑处理器失败: {e}")
            self.immich_logic = None
    
    def process_websocket_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 WebSocket 消息，转换为业务数据
        
        Args:
            message: WebSocket 消息字典
            
        Returns:
            处理后的业务数据字典，包含 type 和 data
        """
        try:
            message_type = message.get("type", "")
            
            self.logger.info(f"处理 WebSocket 消息: type={message_type}")
            
            if message_type == "stt":
                # 用户语音转文字消息
                return self._process_stt_message(message)
            
            elif message_type == "llm_sentence":
                # AI 回复消息（完整句子）
                return self._process_llm_sentence_message(message)
            
            elif message_type == "vision":
                # 视觉识别结果
                return self._process_vision_message(message)
            
            elif message_type == "memory_markdown":
                # 记忆内容（Markdown格式）
                return self._process_memory_markdown_message(message)
            
            elif message_type == "memory_images":
                # 记忆图片
                return self._process_memory_images_message(message)
            
            elif message_type == "immich_search_result":
                # Immich 搜索结果
                return self._process_immich_search_result_message(message)
            
            elif message_type == "immich_kiosk_url":
                # Immich Kiosk URL 消息
                return self._process_immich_kiosk_url_message(message)
            
            else:
                # 其他类型的消息（如 llm 流式片段，不处理）
                self.logger.debug(f"未处理的 WebSocket 消息类型: {message_type}")
                return {"type": "ignored", "data": None}
                
        except Exception as e:
            self.logger.error(f"处理 WebSocket 消息时出错: {e}")
            return {"type": "error", "data": {"error": str(e)}}
    
    def _process_stt_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理 STT 消息"""
        text = message.get("text", "")
        session_id = message.get("session_id", "")
        speaker = message.get("speaker", None)
        
        # 检查是否是JSON格式的文本
        try:
            if text.strip().startswith("{") and text.strip().endswith("}"):
                parsed = json.loads(text)
                if isinstance(parsed, dict) and "content" in parsed:
                    text = parsed["content"]
                    if "speaker" in parsed:
                        speaker = parsed["speaker"]
        except (json.JSONDecodeError, TypeError):
            pass
        
        # 清除该 session_id 的流式消息缓存（如果有）
        if session_id in self.current_llm_message:
            del self.current_llm_message[session_id]
        
        return {
            "type": "user_message",
            "data": {
                "role": "user",
                "content": text,
                "session_id": session_id,
                "speaker": speaker
            }
        }
    
    def _process_llm_sentence_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理 LLM 句子消息"""
        text = message.get("text", "")
        session_id = message.get("session_id", "")
        
        # 清除该 session_id 的流式消息缓存（如果有）
        if session_id in self.current_llm_message:
            del self.current_llm_message[session_id]
        
        text_cleaned = text.strip()
        
        return {
            "type": "assistant_message",
            "data": {
                "role": "assistant",
                "content": text_cleaned,
                "session_id": session_id,
                "_is_sentence": True
            }
        }
    
    def _process_vision_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理视觉识别消息"""
        result = message.get("result", "")
        people = message.get("people", [])
        people_ids = message.get("people_ids", [])
        session_id = message.get("session_id", "")
        asset_id = message.get("asset_id", None)
        image_data_uri = message.get("image", None)
        
        # 构建文本内容
        text_content = result
        if people:
            text_content += f"\n\n识别到的人物：{', '.join(people)}"
        
        # 处理图片
        if asset_id and self.immich_logic and self.immich_logic.api.enabled:
            # 使用 asset_id 下载图片（异步）
            return {
                "type": "vision_message_with_asset",
                "data": {
                    "role": "assistant",
                    "content": text_content,
                    "session_id": session_id,
                    "asset_id": asset_id,
                    "image_data_uri": image_data_uri,  # 降级方案
                    "people": people,  # 包含人物名称列表
                    "people_ids": people_ids  # 包含人物 ID 列表
                }
            }
        elif image_data_uri:
            # 使用 base64 图片
            image_path = self._save_base64_image(image_data_uri)
            if image_path:
                content = [image_path, text_content]
            else:
                content = text_content
            
            return {
                "type": "vision_message",
                "data": {
                    "role": "assistant",
                    "content": content,
                    "session_id": session_id,
                    "people": people,  # 包含人物名称列表
                    "people_ids": people_ids  # 包含人物 ID 列表
                }
            }
        else:
            # 没有图片
            return {
                "type": "vision_message",
                "data": {
                    "role": "assistant",
                    "content": text_content,
                    "session_id": session_id,
                    "people": people,  # 包含人物名称列表
                    "people_ids": people_ids  # 包含人物 ID 列表
                }
            }
    
    def _process_memory_markdown_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理记忆 Markdown 消息"""
        content = message.get("content", "")
        session_id = message.get("session_id", "")
        
        return {
            "type": "memory_update",
            "data": {
                "content": content,
                "session_id": session_id
            }
        }
    
    def _process_memory_images_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """处理记忆图片消息"""
        images = message.get("images", [])
        session_id = message.get("session_id", "")
        
        if images:
            image_markdown = "\n".join([f"![相关照片]({img})" for img in images[:6]])
            return {
                "type": "memory_append",
                "data": {
                    "content": f"\n\n## 相关照片\n\n{image_markdown}",
                    "session_id": session_id
                }
            }
        else:
            return {"type": "ignored", "data": None}
    
    def _process_immich_search_result_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 Immich 搜索结果消息
        
        从消息中提取 asset_id 列表，准备下载缩略图
        
        Args:
            message: WebSocket 消息字典，格式：
                {
                    "type": "immich_search_result",
                    "data": {
                        "assets": [
                            {"id": "asset-id-1", ...},
                            {"id": "asset-id-2", ...}
                        ],
                        "count": 10,
                        "query": "...",
                        "person_name": "...",
                        ...
                    },
                    "device_id": "..."
                }
        
        Returns:
            处理后的业务数据字典
        """
        data = message.get("data", {})
        assets = data.get("assets", [])
        session_id = message.get("device_id", "")  # 使用 device_id 作为 session_id
        query = data.get("query", "")
        person_name = data.get("person_name")
        count = data.get("count", 0)
        
        # 提取所有 asset_id
        asset_ids = []
        for asset in assets:
            asset_id = asset.get("id")
            if asset_id:
                asset_ids.append(asset_id)
        
        if not asset_ids:
            self.logger.warning("Immich 搜索结果中没有找到 asset_id")
            return {"type": "ignored", "data": None}
        
        self.logger.debug(f"收到 Immich 搜索结果: 共 {len(asset_ids)} 个资产, query={query}, person_name={person_name}")
        self.logger.debug(f"资产ID列表: {asset_ids}")
        
        # 如果识别到人物，更新人物跟踪信息
        if person_name:
            # 异步获取人物ID（不阻塞当前流程）
            asyncio.create_task(self._update_person_info(person_name))
        
        # 构建文本内容（使用空格分隔，避免换行符导致 Gradio 误判为文件路径）
        text_content = f"找到 {count} 张相关照片"
        if person_name:
            text_content += f"（{person_name}）"
        if query:
            text_content += f" | 查询关键词: {query}"
        
        # 返回需要下载缩略图的消息类型
        return {
            "type": "immich_search_result_message",
            "data": {
                "role": "assistant",
                "content": text_content,
                "session_id": session_id,
                "asset_ids": asset_ids,  # 需要下载的 asset_id 列表
                "person_name": person_name,  # 人物名称（如果有）
                "query": query,  # 查询关键词
                "count": count  # 结果数量
            }
        }
    
    async def download_immich_image(self, asset_id: str) -> Optional[str]:
        """
        从 Immich 服务器下载图片
        
        Args:
            asset_id: Immich 资产 ID
            
        Returns:
            下载的图片文件路径，如果下载失败返回 None
        """
        self.logger.debug(f"开始下载 Immich 图片: asset_id={asset_id}")
        
        if not self.immich_logic or not self.immich_logic.api.enabled:
            self.logger.warning("Immich logic 未初始化或未启用")
            return None
        
        try:
            # 使用 ImmichAPI 的 download_asset 方法
            image_data = await self.immich_logic.api.download_asset(asset_id)
            
            if image_data:
                # 保存为临时文件
                temp_file = tempfile.NamedTemporaryFile(
                    dir=self.temp_dir,
                    suffix=".jpg",
                    delete=False
                )
                temp_file.write(image_data)
                temp_file.close()
                
                image_path = temp_file.name
                if os.path.exists(image_path):
                    file_size = os.path.getsize(image_path)
                    self.temp_files.append(image_path)
                    self.logger.debug(f"成功从 Immich 下载图片: asset_id={asset_id}, path={image_path}, size={file_size} bytes")
                    return image_path
                else:
                    self.logger.warning(f"保存图片文件失败: asset_id={asset_id}")
                    return None
            else:
                self.logger.warning(f"从 Immich 下载图片失败: asset_id={asset_id}")
                return None
        except Exception as e:
            import traceback
            self.logger.error(f"从 Immich 下载图片异常: {e}, traceback: {traceback.format_exc()}")
            return None
    
    async def download_immich_thumbnails_batch(self, asset_ids: List[str], return_base64: bool = True, return_pil: bool = False) -> List:
        """
        批量下载 Immich 缩略图
        
        Args:
            asset_ids: Immich 资产 ID 列表
            return_base64: 是否返回 base64 data URI（True）或文件路径（False）
            return_pil: 是否返回 PIL Image 对象（优先级高于 return_base64，性能最优）
            
        Returns:
            下载成功的缩略图列表：
            - return_pil=True: PIL Image 对象列表（推荐，性能最优）
            - return_base64=True: base64 data URI 列表
            - 否则: 文件路径列表
        """
        self.logger.debug(f"开始批量下载 Immich 缩略图: 共 {len(asset_ids)} 个资产, return_pil={return_pil}, return_base64={return_base64}")
        
        if not self.immich_logic or not self.immich_logic.api.enabled:
            self.logger.warning("Immich logic 未初始化或未启用")
            return []
        
        if not asset_ids:
            return []
        
        try:
            # 使用 ImmichLogic 的 batch_download_thumbnails 方法
            if AssetMediaSize is None:
                self.logger.error("AssetMediaSize 未导入，无法下载缩略图")
                return []
            
            self.logger.debug(f"调用 immich_logic.batch_download_thumbnails: asset_ids={asset_ids}, return_pil={return_pil}, return_base64={return_base64}")
            result = await self.immich_logic.batch_download_thumbnails(
                asset_ids=asset_ids,
                save_dir=self.temp_dir if not return_base64 and not return_pil else None,  # 如果返回 base64 或 PIL，不需要保存目录
                thumbnail_size=AssetMediaSize.THUMBNAIL,
                return_base64=return_base64,
                return_pil=return_pil
            )
            
            self.logger.debug(f"batch_download_thumbnails 返回结果: success={result.get('success')}, downloaded={result.get('downloaded')}, failed={result.get('failed')}")
            
            if result.get("success"):
                if return_pil:
                    # 返回 PIL Image 对象列表（性能最优）
                    pil_images = result.get("pil_images", [])
                    self.logger.debug(f"获取到 {len(pil_images)} 个 PIL Image 对象（性能最优：内存占用最小，无需编码/解码）")
                    return pil_images
                elif return_base64:
                    # 返回 base64 data URI 列表
                    base64_data_uris = result.get("base64_data_uris", [])
                    self.logger.debug(f"获取到 {len(base64_data_uris)} 个 base64 data URI（未保存文件，避免文件 I/O）")
                    return base64_data_uris
                else:
                    # 返回文件路径列表
                    thumbnail_paths = result.get("saved_files", [])
                    self.logger.debug(f"获取到 {len(thumbnail_paths)} 个文件路径: {thumbnail_paths}")
                    
                    # 记录临时文件，用于后续清理
                    for path in thumbnail_paths:
                        if path and path not in self.temp_files:
                            self.temp_files.append(path)
                    
                    self.logger.debug(f"批量下载完成: 成功 {len(thumbnail_paths)}/{len(asset_ids)} 张缩略图")
                    return thumbnail_paths
            else:
                errors = result.get("errors", [])
                self.logger.warning(f"批量下载缩略图失败: {errors}")
                return []
        except Exception as e:
            import traceback
            self.logger.error(f"批量下载缩略图异常: {e}, traceback: {traceback.format_exc()}")
            return []
    
    async def get_person_photos(self, person_name: str, limit: int = 50) -> List[str]:
        """
        获取指定人物的所有照片缩略图路径列表
        
        Args:
            person_name: 人物名称
            limit: 返回的最大数量，默认 50
            
        Returns:
            缩略图文件路径列表
        """
        self.logger.debug(f"开始获取人物照片: person_name={person_name}, limit={limit}")
        
        if not self.immich_logic or not self.immich_logic.api.enabled:
            self.logger.warning("Immich logic 未初始化或未启用")
            return []
        
        try:
            # 使用 ImmichLogic 的 search_random_by_person 方法获取资产列表
            assets = await self.immich_logic.search_random_by_person(person_name, size=limit)
            
            if not assets:
                self.logger.warning(f"未找到人物 '{person_name}' 的照片")
                return []
            
            # 提取 asset_ids
            asset_ids = [asset.get("id") for asset in assets if asset.get("id")]
            
            if not asset_ids:
                self.logger.warning(f"未找到有效的资产ID")
                return []
            
            # 批量下载缩略图
            if AssetMediaSize is None:
                self.logger.error("AssetMediaSize 未导入，无法下载缩略图")
                return []
            
            result = await self.immich_logic.batch_download_thumbnails(
                asset_ids=asset_ids,
                save_dir=self.temp_dir,
                thumbnail_size=AssetMediaSize.THUMBNAIL
            )
            
            if result.get("success"):
                thumbnail_paths = result.get("saved_files", [])
                # 记录临时文件，用于后续清理
                for path in thumbnail_paths:
                    if path and path not in self.temp_files:
                        self.temp_files.append(path)
                
                self.logger.debug(f"成功获取 {len(thumbnail_paths)} 张人物照片: person_name={person_name}")
                return thumbnail_paths
            else:
                self.logger.warning(f"下载人物照片失败: {result.get('errors', [])}")
                return []
        except Exception as e:
            import traceback
            self.logger.error(f"获取人物照片异常: {e}, traceback: {traceback.format_exc()}")
            return []
    
    async def get_person_photos_by_id(self, person_id: str, limit: int = 50) -> List[str]:
        """
        根据人物 ID 获取该人物的所有照片缩略图路径列表
        
        Args:
            person_id: 人物 ID
            limit: 返回的最大数量，默认 50
            
        Returns:
            缩略图文件路径列表
        """
        self.logger.debug(f"开始获取人物照片: person_id={person_id}, limit={limit}")
        
        if not self.immich_logic or not self.immich_logic.api.enabled:
            self.logger.warning("Immich logic 未初始化或未启用")
            return []
        
        try:
            # 直接使用 search_random API，传入 person_ids
            assets = await self.immich_logic.api.search_random(
                person_ids=[person_id],
                size=limit
            )
            
            if not assets:
                self.logger.warning(f"未找到人物ID '{person_id}' 的照片")
                return []
            
            # 提取 asset_ids
            asset_ids = [asset.get("id") for asset in assets if asset.get("id")]
            
            if not asset_ids:
                self.logger.warning(f"未找到有效的资产ID")
                return []
            
            # 批量下载缩略图
            if AssetMediaSize is None:
                self.logger.error("AssetMediaSize 未导入，无法下载缩略图")
                return []
            
            result = await self.immich_logic.batch_download_thumbnails(
                asset_ids=asset_ids,
                save_dir=self.temp_dir,
                thumbnail_size=AssetMediaSize.THUMBNAIL
            )
            
            if result.get("success"):
                thumbnail_paths = result.get("saved_files", [])
                # 记录临时文件，用于后续清理
                for path in thumbnail_paths:
                    if path and path not in self.temp_files:
                        self.temp_files.append(path)
                
                self.logger.debug(f"成功获取 {len(thumbnail_paths)} 张人物照片: person_id={person_id}")
                return thumbnail_paths
            else:
                self.logger.warning(f"下载人物照片失败: {result.get('errors', [])}")
                return []
        except Exception as e:
            import traceback
            self.logger.error(f"获取人物照片异常: {e}, traceback: {traceback.format_exc()}")
            return []
    
    def _save_base64_image(self, image_data_uri: str) -> Optional[str]:
        """
        将 base64 data URI 转换为临时文件
        
        Args:
            image_data_uri: base64 data URI 格式的图片数据
            
        Returns:
            临时文件路径，如果转换失败返回 None
        """
        try:
            if not image_data_uri.startswith("data:image/"):
                self.logger.warning(f"无效的图片 data URI 格式: {image_data_uri[:50]}...")
                return None
            
            # 提取 MIME 类型和 base64 数据
            header, encoded = image_data_uri.split(",", 1)
            mime_type = header.split(";")[0].split(":")[1]
            
            # 确定文件扩展名
            ext_map = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/gif": ".gif",
                "image/bmp": ".bmp",
                "image/webp": ".webp"
            }
            ext = ext_map.get(mime_type, ".jpg")
            
            # 解码 base64 数据
            image_data = base64.b64decode(encoded)
            
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(
                dir=self.temp_dir,
                suffix=ext,
                delete=False
            )
            temp_file.write(image_data)
            temp_file.close()
            
            self.temp_files.append(temp_file.name)
            self.logger.debug(f"已将 base64 图片保存为临时文件: {temp_file.name}")
            return temp_file.name
            
        except Exception as e:
            self.logger.error(f"保存 base64 图片失败: {e}")
            return None
    
    def add_chat_message(self, message: Dict[str, Any]):
        """
        添加聊天消息到历史记录
        
        Args:
            message: 消息字典，包含 role 和 content
        """
        # 处理说话人信息
        speaker = message.get("speaker")
        content = message.get("content")
        
        if speaker:
            if isinstance(content, str):
                content = f"[{speaker}] {content}"
            elif isinstance(content, list) and len(content) >= 2:
                content[1] = f"[{speaker}] {content[1]}"
            elif isinstance(content, list) and len(content) == 1:
                content.append(f"[{speaker}]")
        
        message_obj = {
            "role": message.get("role"),
            "content": content
        }
        
        self.chat_history.append(message_obj)
        self.logger.debug(f"添加聊天消息: role={message.get('role')}, content_length={len(str(content))}")
    
    def update_chat_message(self, index: int, content: Any):
        """
        更新已存在的聊天消息
        
        Args:
            index: 消息索引
            content: 新的消息内容
        """
        if 0 <= index < len(self.chat_history):
            self.chat_history[index]["content"] = content
            self.logger.info(f"已更新消息索引 {index}")
    
    def update_memory(self, content: str):
        """更新记忆内容"""
        self.memory_markdown = content
    
    def append_memory(self, content: str):
        """追加记忆内容"""
        self.memory_markdown += content
    
    def clear_chat_history(self):
        """清除聊天记录"""
        self.chat_history = []
        self.current_llm_message = {}
        # 注意：person_galleries 已废弃，但保留清理逻辑以避免错误
        self.person_galleries = {}
        self.current_gallery_person = None
        self._cleanup_temp_files()
        self.logger.info("聊天记录已清除")
    
    def clear_memory(self):
        """清除记忆内容"""
        self.memory_markdown = "# 记忆显示区\n\n待开发功能..."
        self.logger.info("记忆显示区已清除")
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """获取聊天历史记录"""
        return self.chat_history
    
    def get_memory_markdown(self) -> str:
        """获取记忆内容"""
        return self.memory_markdown
    
    def get_person_gallery(self, person_name: str) -> List[str]:
        """
        获取指定人物的照片列表（已废弃）
        
        注意：此方法已废弃，人物照片现在通过 Kiosk URL 在 iframe 中显示
        
        Args:
            person_name: 人物名称
            
        Returns:
            照片路径列表（始终返回空列表）
        """
        # 返回空列表，因为不再使用 gallery
        return []
    
    def set_person_gallery(self, person_name: str, image_data: List[str]):
        """
        设置指定人物的照片列表（已废弃）
        
        注意：此方法已废弃，人物照片现在通过 Kiosk URL 在 iframe 中显示
        
        Args:
            person_name: 人物名称
            image_data: 照片数据列表（不再使用）
        """
        # 不再执行任何操作，仅记录日志
        self.logger.debug(f"set_person_gallery 被调用但已废弃: person_name={person_name}, count={len(image_data) if image_data else 0}")
    
    async def _update_person_info(self, person_name: str):
        """
        更新人物信息（名称和ID）
        
        Args:
            person_name: 人物名称
        """
        if not person_name:
            return
        
        current_time = time.time()
        
        # 如果人物名称发生变化，需要重新获取ID
        if person_name != self.last_person_name:
            self.logger.info(f"检测到新人物: {person_name}")
            
            # 尝试获取人物ID
            person_id = None
            if self.immich_logic and self.immich_logic.api:
                try:
                    person_ids = await self.immich_logic.api.search_person(
                        name=person_name,
                        return_ids=True,
                        timeout=5.0
                    )
                    if person_ids and len(person_ids) > 0:
                        person_id = person_ids[0]  # 使用第一个匹配的人物ID
                        self.logger.info(f"获取到人物ID: {person_name} -> {person_id}")
                    else:
                        self.logger.warning(f"未找到人物ID: {person_name}")
                except Exception as e:
                    self.logger.error(f"获取人物ID失败: {person_name}, 错误: {e}")
            
            # 更新人物信息
            self.last_person_name = person_name
            self.last_person_id = person_id
            self.last_person_update_time = current_time
        
        # 更新最后消息时间
        self.last_message_time = current_time
    
    def update_message_time(self):
        """
        更新最后消息时间（当收到新消息时调用）
        """
        self.last_message_time = time.time()
    
    def _process_immich_kiosk_url_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 Immich Kiosk URL 消息
        
        Args:
            message: WebSocket 消息字典，格式：
                {
                    "type": "immich_kiosk_url",
                    "data": {
                        "kiosk_url": "...",
                        "person_name": "...",
                        "person_id": "...",
                        "device_id": "..."
                    },
                    "device_id": "..."
                }
        
        Returns:
            处理后的业务数据字典
        """
        data = message.get("data", {})
        kiosk_url = data.get("kiosk_url", "")
        person_name = data.get("person_name")
        person_id = data.get("person_id")
        session_id = message.get("device_id", "")  # 使用 device_id 作为 session_id
        
        if not kiosk_url:
            self.logger.warning("Immich Kiosk URL 消息中没有找到 kiosk_url")
            return {"type": "ignored", "data": None}
        
        # 更新人物信息和 Kiosk URL
        current_time = time.time()
        if person_name:
            self.last_person_name = person_name
            self.last_person_id = person_id
            self.last_person_update_time = current_time
            self.logger.info(f"更新人物信息: person_name={person_name}, person_id={person_id}")
        
        self.last_kiosk_url = kiosk_url
        self.last_message_time = current_time
        
        self.logger.info(f"收到 Immich Kiosk URL: {kiosk_url}, person_name={person_name}, person_id={person_id}")
        
        return {
            "type": "immich_kiosk_url_message",
            "data": {
                "kiosk_url": kiosk_url,
                "person_name": person_name,
                "person_id": person_id,
                "session_id": session_id
            }
        }
    
    def should_enter_slideshow(self, idle_threshold: Optional[float] = None) -> bool:
        """
        判断是否应该进入全屏轮播模式
        
        Args:
            idle_threshold: 空闲阈值（秒），如果为 None 则使用 self.idle_threshold
            
        Returns:
            是否应该进入全屏轮播模式
        """
        if idle_threshold is None:
            idle_threshold = self.idle_threshold
        
        current_time = time.time()
        
        # 计算空闲时间（从最后一次消息或人物更新开始）
        idle_time = current_time - max(self.last_message_time, self.last_person_update_time)
        
        # 无论是否有识别到人物，只要空闲时间达到阈值，就进入全屏轮播模式
        if idle_time >= idle_threshold:
            self.logger.debug(
                f"满足进入全屏轮播模式条件: idle_time={idle_time:.1f}s >= {idle_threshold}s, "
                f"person_name={self.last_person_name}, has_kiosk_url={bool(self.last_kiosk_url)}"
            )
            return True
        
        return False
    
    def should_exit_slideshow(self) -> bool:
        """
        判断是否应该退出全屏轮播模式（有新消息时）
        
        Returns:
            是否应该退出全屏轮播模式
        """
        # 如果距离最后一次消息时间很短（小于1秒），说明刚刚有新消息
        current_time = time.time()
        time_since_last_message = current_time - self.last_message_time
        
        if time_since_last_message < 1.0:
            self.logger.debug(f"检测到新消息，应该退出全屏轮播模式: time_since_last_message={time_since_last_message:.1f}s")
            return True
        
        return False
    
    def get_last_person_info(self) -> Dict[str, Optional[str]]:
        """
        获取最后识别到的人物信息
        
        Returns:
            包含 person_name 和 person_id 的字典
        """
        return {
            "person_name": self.last_person_name,
            "person_id": self.last_person_id
        }
    
    def update_person_info(self, person_name: Optional[str] = None, person_id: Optional[str] = None, kiosk_url: Optional[str] = None):
        """
        更新人物信息
        
        Args:
            person_name: 人物名称
            person_id: 人物 ID
            kiosk_url: Kiosk URL
        """
        current_time = time.time()
        
        if person_name:
            self.last_person_name = person_name
            self.last_person_update_time = current_time
        
        if person_id:
            self.last_person_id = person_id
        
        if kiosk_url:
            self.last_kiosk_url = kiosk_url
        
        self.last_message_time = current_time
    
    def set_current_mode(self, mode: str, reset_protection: bool = False):
        """
        设置当前模式
        
        Args:
            mode: 模式名称（chat/slideshow/search）
            reset_protection: 是否重置保护期（用于在 search 模式下收到新的搜索请求时）
        """
        if mode in ["chat", "slideshow", "search"]:
            old_mode = self.current_mode
            self.current_mode = mode
            
            # 如果切换到 search 模式，记录进入时间（用于保护期）
            # 注意：每次切换到 search 模式都重置保护期（包括已经在 search 模式时）
            if mode == "search":
                # 如果已经在 search 模式且需要重置保护期，或者从其他模式切换到 search
                if reset_protection or old_mode != "search":
                    self.search_mode_enter_time = time.time()
                    if old_mode != "search":
                        self.logger.info(f"切换到模式: {mode}，保护期开始（{self.search_mode_protection_period}秒）")
                    else:
                        # 已经在 search 模式，收到新的搜索请求，重置保护期
                        self.logger.info(f"收到新的搜索请求，重置保护期（{self.search_mode_protection_period}秒）")
                # 如果已经在 search 模式且不需要重置，保持原有保护期
            elif mode != "search" and old_mode == "search":
                # 退出 search 模式，清除保护期
                self.search_mode_enter_time = 0.0
                self.logger.info(f"退出搜索模式，切换到: {mode}")
            else:
                self.logger.info(f"切换到模式: {mode}")
        else:
            self.logger.warning(f"无效的模式: {mode}")
    
    def get_current_mode(self) -> str:
        """
        获取当前模式
        
        Returns:
            当前模式名称
        """
        return self.current_mode
    
    def is_search_mode_protected(self) -> bool:
        """
        检查搜索模式是否在保护期内
        
        Returns:
            如果在保护期内返回 True，否则返回 False
        """
        if self.current_mode != "search":
            return False
        
        if self.search_mode_enter_time == 0.0:
            return False
        
        current_time = time.time()
        elapsed_time = current_time - self.search_mode_enter_time
        
        is_protected = elapsed_time < self.search_mode_protection_period
        if is_protected:
            self.logger.debug(
                f"搜索模式保护期内: 已过 {elapsed_time:.1f}s / {self.search_mode_protection_period}s"
            )
        
        return is_protected
    
    def get_last_kiosk_url(self) -> Optional[str]:
        """
        获取最后收到的 Kiosk URL
        
        Returns:
            Kiosk URL，如果没有则返回 None
        """
        return self.last_kiosk_url
    
    def _cleanup_temp_files(self):
        """清理临时文件"""
        try:
            for temp_file in self.temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        self.logger.debug(f"已删除临时文件: {temp_file}")
                except Exception as e:
                    self.logger.warning(f"删除临时文件失败: {temp_file}, 错误: {e}")
            
            self.temp_files.clear()
            
            # 尝试删除临时目录（如果为空）
            try:
                if os.path.exists(self.temp_dir) and not os.listdir(self.temp_dir):
                    os.rmdir(self.temp_dir)
            except Exception as e:
                self.logger.debug(f"删除临时目录失败（可能不为空）: {e}")
        except Exception as e:
            self.logger.error(f"清理临时文件时出错: {e}")

