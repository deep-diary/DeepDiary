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
from typing import List, Dict, Any, Optional
from queue import Queue, Empty
import logging

# 导入 Immich client
try:
    from deepweb.services.cloud_communication.immich_client import ImmichClient
except ImportError as e:
    ImmichClient = None


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
    
    def __init__(self, logger: logging.Logger, config_manager=None, immich_client: Optional[ImmichClient] = None):
        """
        初始化聊天服务
        
        Args:
            logger: 日志记录器
            config_manager: 配置管理器（可选）
            immich_client: Immich 客户端（可选）
        """
        self.logger = logger
        self.config_manager = config_manager
        
        # 聊天历史记录
        self.chat_history: List[Dict[str, str]] = []
        
        # 记忆内容
        self.memory_markdown = "# 记忆显示区\n\n待开发功能..."
        
        # 人物照片相册：存储每个人物的照片列表 {person_name: [image_paths]}
        self.person_galleries: Dict[str, List[str]] = {}
        
        # LLM流式响应合并：存储当前正在接收的消息
        self.current_llm_message: Dict[str, Any] = {}
        
        # 临时文件管理
        self.temp_dir = tempfile.mkdtemp(prefix="chat_images_")
        self.temp_files: List[str] = []
        
        # Immich 客户端
        self.immich_client = immich_client
        if not self.immich_client:
            self._init_immich_client()
    
    def _init_immich_client(self):
        """初始化 Immich 客户端"""
        if ImmichClient is None:
            self.logger.warning("ImmichClient 未导入，图片获取功能将被禁用")
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
                    "email": os.getenv("IMMICH_EMAIL", ""),
                    "password": os.getenv("IMMICH_PASSWORD", ""),
                    "timeout": int(os.getenv("IMMICH_TIMEOUT", "30"))
                }
                self.logger.info(f"从环境变量获取 Immich 配置: api_url={immich_config.get('api_url')}")
            
            # 如果配置了 API key 或 email+password，创建客户端
            has_api_key = bool(immich_config.get("api_key"))
            has_email_password = bool(immich_config.get("email") and immich_config.get("password"))
            
            if has_api_key or has_email_password:
                self.immich_client = ImmichClient(immich_config)
                if self.immich_client.enabled:
                    self.logger.info(f"Immich 客户端初始化成功: api_url={self.immich_client.api_url}")
                else:
                    self.logger.warning("Immich 客户端初始化失败，将使用降级方案")
                    self.immich_client = None
            else:
                self.logger.info("Immich 配置未设置，将使用降级方案（base64 图片）")
        except Exception as e:
            self.logger.error(f"初始化 Immich 客户端失败: {e}")
            self.immich_client = None
    
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
        if asset_id and self.immich_client and self.immich_client.enabled:
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
    
    async def download_immich_image(self, asset_id: str) -> Optional[str]:
        """
        从 Immich 服务器下载图片
        
        Args:
            asset_id: Immich 资产 ID
            
        Returns:
            下载的图片文件路径，如果下载失败返回 None
        """
        self.logger.info(f"开始下载 Immich 图片: asset_id={asset_id}")
        
        if not self.immich_client or not self.immich_client.enabled:
            self.logger.warning("Immich client 未初始化或未启用")
            return None
        
        try:
            image_path = await self.immich_client.download_asset(asset_id)
            
            if image_path and os.path.exists(image_path):
                file_size = os.path.getsize(image_path)
                self.temp_files.append(image_path)
                self.logger.info(f"成功从 Immich 下载图片: asset_id={asset_id}, path={image_path}, size={file_size} bytes")
                return image_path
            else:
                self.logger.warning(f"从 Immich 下载图片失败: asset_id={asset_id}")
                return None
        except Exception as e:
            import traceback
            self.logger.error(f"从 Immich 下载图片异常: {e}, traceback: {traceback.format_exc()}")
            return None
    
    async def get_person_photos(self, person_name: str, limit: int = 50) -> List[str]:
        """
        获取指定人物的所有照片缩略图路径列表
        
        Args:
            person_name: 人物名称
            limit: 返回的最大数量，默认 50
            
        Returns:
            缩略图文件路径列表
        """
        self.logger.info(f"开始获取人物照片: person_name={person_name}, limit={limit}")
        
        if not self.immich_client or not self.immich_client.enabled:
            self.logger.warning("Immich client 未初始化或未启用")
            return []
        
        try:
            thumbnail_paths = await self.immich_client.get_person_thumbnails_by_name(person_name, limit)
            
            # 记录临时文件，用于后续清理
            for path in thumbnail_paths:
                if path not in self.temp_files:
                    self.temp_files.append(path)
            
            self.logger.info(f"成功获取 {len(thumbnail_paths)} 张人物照片: person_name={person_name}")
            return thumbnail_paths
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
        self.logger.info(f"开始获取人物照片: person_id={person_id}, limit={limit}")
        
        if not self.immich_client or not self.immich_client.enabled:
            self.logger.warning("Immich client 未初始化或未启用")
            return []
        
        try:
            thumbnail_paths = await self.immich_client.get_person_thumbnails_by_id(person_id, limit)
            
            # 记录临时文件，用于后续清理
            for path in thumbnail_paths:
                if path not in self.temp_files:
                    self.temp_files.append(path)
            
            self.logger.info(f"成功获取 {len(thumbnail_paths)} 张人物照片: person_id={person_id}")
            return thumbnail_paths
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
        获取指定人物的照片列表
        
        Args:
            person_name: 人物名称
            
        Returns:
            照片路径列表
        """
        return self.person_galleries.get(person_name, [])
    
    def set_person_gallery(self, person_name: str, image_paths: List[str]):
        """
        设置指定人物的照片列表
        
        Args:
            person_name: 人物名称
            image_paths: 照片路径列表
        """
        self.person_galleries[person_name] = image_paths
        self.logger.info(f"已设置人物 '{person_name}' 的照片相册，共 {len(image_paths)} 张照片")
    
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

