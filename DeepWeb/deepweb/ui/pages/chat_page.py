#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat Page - 聊天页面主类
整合 WebSocket 客户端、业务逻辑服务和 UI 组件

作者: DeepDiary Team
日期: 2025-01-27
"""

import threading
import asyncio
from typing import List, Dict, Any, Optional
from queue import Queue, Empty
import logging

# 导入组件
from deepweb.services.cloud_communication.websocket_client import WebSocketClient
from deepweb.ui.pages.chat.chat_service import ChatService
from deepweb.ui.pages.chat.chat_ui import ChatUI


class ChatPage:
    """
    聊天页面主类
    
    职责：
    - 整合 WebSocket 客户端、业务逻辑服务和 UI 组件
    - 协调各层之间的交互
    - 处理 UI 事件和更新
    """
    
    def __init__(self, logger: logging.Logger, config_manager=None):
        """
        初始化聊天页面

        Args:
            logger: 日志记录器（从 LogManager 获取）
            config_manager: 配置管理器（可选，用于获取 Immich 配置）
        """
        self.logger = logger
        self.config_manager = config_manager

        # 初始化各层组件
        # 1. WebSocket 客户端层（服务层）
        self.ws_client = WebSocketClient(self.logger)
        self.ws_client.set_callbacks(
            on_message=self._on_websocket_message,
            on_status_change=self._on_status_change
        )
        
        # 2. 业务逻辑层
        self.chat_service = ChatService(self.logger, config_manager)
        
        # 3. UI 组件层
        self.chat_ui = ChatUI(self.logger)
        
        # UI 更新队列（用于异步更新）
        self.ui_update_queue = Queue(maxsize=100)

        # 连接状态
        self.connection_status = "未连接"

    def build(self):
        """
        构建 Gradio UI 界面
        
        Returns:
            Gradio Column 组件
        """
        # 构建 UI
        chat_interface = self.chat_ui.build(
            device_id=self.ws_client.device_id,
            client_id=self.ws_client.client_id,
            websocket_url=self.ws_client.websocket_url,
            chat_history=self.chat_service.get_chat_history(),
            memory_markdown=self.chat_service.get_memory_markdown()
        )
        
        # 绑定事件
        self.chat_ui.bind_events(
            on_connect=self.connect_websocket,
            on_disconnect=self.disconnect_websocket,
            on_send_message=self.send_message,
            on_clear_chat=self.clear_chat_history,
            on_refresh_memory=self.refresh_memory,
            on_clear_memory=self.clear_memory,
            on_update_ui=self.update_ui
            )

        return chat_interface

    def connect_websocket(self, device_id: str, client_id: str, websocket_url: str) -> str:
        """
        连接到 WebSocket 服务器

        Args:
            device_id: 设备ID
            client_id: 客户端ID
            websocket_url: WebSocket URL

        Returns:
            连接状态消息
        """
        return self.ws_client.connect(device_id, client_id, websocket_url)

    def disconnect_websocket(self) -> str:
        """
        断开 WebSocket 连接

        Returns:
            断开状态消息
        """
        return self.ws_client.disconnect()

    def send_message(self, message: str):
        """
        发送消息到 WebSocket 服务器

        Args:
            message: 要发送的消息
        """
        if not message or not message.strip():
            return

        success = self.ws_client.send_message(message)
        if not success:
            self.logger.warning("发送消息失败")

    def clear_chat_history(self) -> List:
        """
        清除聊天记录

        Returns:
            清空后的聊天历史
        """
        self.chat_service.clear_chat_history()
        return self.chat_service.get_chat_history()

    def refresh_memory(self) -> str:
        """
        刷新记忆显示区

        Returns:
            记忆内容
        """
        # 这里可以添加从服务器获取最新记忆的逻辑
        self.logger.info("记忆已刷新")
        return self.chat_service.get_memory_markdown()

    def clear_memory(self) -> str:
        """
        清除记忆显示区

        Returns:
            清空后的记忆内容
        """
        self.chat_service.clear_memory()
        return self.chat_service.get_memory_markdown()
    
    def update_ui(self) -> tuple:
        """
        更新 UI 界面（定时调用）
        
        Returns:
            (chat_history, person_gallery, status_text) 的更新
        """
        # 处理消息队列
        updated = False
        
        # 处理 WebSocket 消息
        while True:
            try:
                message = self.ws_client.get_message(timeout=0.01)
                if message is None:
                    break
                
                # 业务层处理消息
                result = self.chat_service.process_websocket_message(message)
                
                # 根据处理结果更新 UI
                self._handle_service_result(result)
                updated = True
                
            except Empty:
                break
        
        # 处理 UI 更新队列
        while True:
            try:
                update_data = self.ui_update_queue.get_nowait()
                self._process_ui_update(update_data)
                updated = True
            except Empty:
                break
        
        # 获取当前显示的人物照片（显示最新设置的人物）
        current_person_gallery = []
        person_galleries = getattr(self.chat_service, 'person_galleries', {})
        current_gallery_person = getattr(self.chat_service, 'current_gallery_person', None)
        
        if current_gallery_person and current_gallery_person in person_galleries:
            # 显示最新设置的人物相册
            current_person_gallery = person_galleries[current_gallery_person]
            self.logger.debug(f"显示人物相册: {current_gallery_person}, 共 {len(current_person_gallery)} 张照片")
        elif person_galleries:
            # 如果没有记录当前人物，显示最后一个设置的人物（Python 3.7+ 字典保持插入顺序）
            # 或者显示第一个有照片的人物
            for person_name, photos in person_galleries.items():
                if photos:
                    current_person_gallery = photos
                    self.logger.debug(f"显示第一个找到的人物相册: {person_name}, 共 {len(photos)} 张照片")
                    break
        
        # 返回当前状态（移除了memory_markdown）
        return (
            self.chat_service.get_chat_history(),
            current_person_gallery,
            self.connection_status
        )
    
    def _on_websocket_message(self, message: Dict[str, Any]):
        """
        WebSocket 消息接收回调
        
        Args:
            message: WebSocket 消息字典
        """
        # 消息会通过 get_message() 方法处理，这里可以记录日志
        self.logger.debug(f"收到 WebSocket 消息: type={message.get('type')}")
    
    def _on_status_change(self, status: str):
        """
        连接状态变化回调
        
        Args:
            status: 状态字符串
        """
        self.connection_status = status
        self.logger.info(f"连接状态变化: {status}")
    
    def _handle_service_result(self, result: Dict[str, Any]):
        """
        处理业务层的处理结果
        
        Args:
            result: 业务层返回的结果字典，包含 type 和 data
        """
        result_type = result.get("type")
        data = result.get("data")
        
        if result_type == "user_message":
            # 用户消息
            self.chat_service.add_chat_message(data)
            
        elif result_type == "assistant_message":
            # AI 回复消息
            self.chat_service.add_chat_message(data)
            
        elif result_type == "vision_message":
            # 视觉识别消息（已包含图片）
            self.chat_service.add_chat_message(data)
            # 如果有识别到人物，加载人物照片（优先使用 people_ids）
            people_ids = data.get("people_ids", [])
            people = data.get("people", [])
            if people_ids:
                self._load_people_photos_by_ids(people_ids, people)
            elif people:
                self._load_people_photos(people)
            
        elif result_type == "vision_message_with_asset":
            # 视觉识别消息（需要下载图片）
            # 先添加文本消息
            current_index = len(self.chat_service.chat_history)
            self.chat_service.add_chat_message({
                "role": data["role"],
                "content": data["content"],
                "session_id": data["session_id"]
            })
            
            # 异步下载图片并更新消息
            self._download_and_update_image(
                asset_id=data["asset_id"],
                image_data_uri=data.get("image_data_uri"),
                text_content=data["content"],
                expected_index=current_index
            )
            
            # 如果有识别到人物，加载人物照片（优先使用 people_ids）
            people_ids = data.get("people_ids", [])
            people = data.get("people", [])
            if people_ids:
                self._load_people_photos_by_ids(people_ids, people)
            elif people:
                self._load_people_photos(people)
            
        elif result_type == "memory_update":
            # 更新记忆
            self.chat_service.update_memory(data["content"])
            
        elif result_type == "memory_append":
            # 追加记忆
            self.chat_service.append_memory(data["content"])
            
        elif result_type == "immich_search_result_message":
            # Immich 搜索结果消息（需要批量下载缩略图）
            # 先添加文本消息
            current_index = len(self.chat_service.chat_history)
            self.chat_service.add_chat_message({
                "role": data["role"],
                "content": data["content"],
                "session_id": data["session_id"]
            })
            
            # 异步批量下载缩略图并更新消息
            self._download_and_update_thumbnails(
                asset_ids=data["asset_ids"],
                text_content=data["content"],
                expected_index=current_index,
                person_name=data.get("person_name"),
                query=data.get("query"),
                count=data.get("count", 0)
            )
            
        elif result_type == "ignored":
            # 忽略的消息
            pass
            
        elif result_type == "error":
            # 错误消息
            self.logger.error(f"处理消息时出错: {data.get('error')}")
    
    def _download_and_update_image(
        self,
        asset_id: str,
        image_data_uri: Optional[str],
        text_content: str,
        expected_index: int
    ):
        """
        异步下载图片并更新消息
        
        Args:
            asset_id: Immich 资产 ID
            image_data_uri: base64 图片（降级方案）
            text_content: 文本内容
            expected_index: 期望的消息索引
        """
        def download_and_update():
            """在后台线程中下载图片并更新消息"""
            self.logger.info(f"后台线程开始下载图片: asset_id={asset_id}")
            try:
                # 创建新的事件循环（因为在线程中）
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # 下载图片
                image_path = loop.run_until_complete(
                    self.chat_service.download_immich_image(asset_id)
                )
                
                if image_path:
                    self.logger.info(f"图片下载成功，开始更新消息: image_path={image_path}")
                    
                    # 等待一小段时间，确保消息已经添加到历史记录
                    import time
                    time.sleep(0.1)
                    
                    # 尝试更新消息
                    found = False
                    if expected_index < len(self.chat_service.chat_history):
                        msg = self.chat_service.chat_history[expected_index]
                        if (msg.get("role") == "assistant" and 
                            isinstance(msg.get("content"), str) and
                            msg.get("content") == text_content):
                            # 更新消息，添加图片
                            self.chat_service.update_chat_message(
                                expected_index,
                                [image_path, text_content]
                            )
                            found = True
                    
                    # 如果索引不匹配，尝试通过内容匹配
                    if not found:
                        for i in range(len(self.chat_service.chat_history) - 1, -1, -1):
                            msg = self.chat_service.chat_history[i]
                            msg_content = msg.get("content", "")
                            if (msg.get("role") == "assistant" and 
                                isinstance(msg_content, str) and 
                                msg_content == text_content):
                                self.chat_service.update_chat_message(
                                    i,
                                    [image_path, text_content]
                                )
                                found = True
                                break
                    
                    if not found:
                        self.logger.warning("未找到匹配的消息进行更新")
                else:
                    # 下载失败，尝试使用 base64
                    if image_data_uri:
                        self.logger.info("尝试使用 base64 图片作为降级方案")
                        image_path = self.chat_service._save_base64_image(image_data_uri)
                        if image_path:
                            for i in range(len(self.chat_service.chat_history) - 1, -1, -1):
                                msg = self.chat_service.chat_history[i]
                                if (msg.get("role") == "assistant" and 
                                    isinstance(msg.get("content"), str) and 
                                    msg.get("content") == text_content):
                                    self.chat_service.update_chat_message(
                                        i,
                                        [image_path, text_content]
                                    )
                                    break
            except Exception as e:
                import traceback
                self.logger.error(f"下载图片时出错: {e}, traceback: {traceback.format_exc()}")
            finally:
                loop.close()
        
        # 在后台线程中执行下载
        download_thread = threading.Thread(target=download_and_update, daemon=True)
        download_thread.start()
    
    def _download_and_update_thumbnails(
        self,
        asset_ids: List[str],
        text_content: str,
        expected_index: int,
        person_name: Optional[str] = None,
        query: Optional[str] = None,
        count: int = 0
    ):
        """
        异步批量下载缩略图并更新消息
        
        Args:
            asset_ids: Immich 资产 ID 列表
            text_content: 文本内容
            expected_index: 期望的消息索引
            person_name: 人物名称（可选）
            query: 查询关键词（可选）
            count: 结果数量
        """
        def download_and_update():
            """在后台线程中批量下载缩略图并更新消息"""
            self.logger.info(f"后台线程开始批量下载缩略图: 共 {len(asset_ids)} 个资产")
            try:
                # 创建新的事件循环（因为在线程中）
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # 批量下载缩略图
                self.logger.info(f"准备调用 download_immich_thumbnails_batch: asset_ids={asset_ids}")
                thumbnail_paths = loop.run_until_complete(
                    self.chat_service.download_immich_thumbnails_batch(asset_ids)
                )
                self.logger.info(f"download_immich_thumbnails_batch 返回: {len(thumbnail_paths)} 个路径")
                
                if thumbnail_paths:
                    self.logger.info(f"缩略图下载成功: 共 {len(thumbnail_paths)} 张")
                    
                    # 将缩略图设置到 person_gallery 中
                    # 如果有 person_name，使用 person_name；否则使用 "搜索结果" 作为 key
                    gallery_key = person_name if person_name else "搜索结果"
                    
                    # 获取该人物已有的照片（如果有）
                    existing_photos = self.chat_service.get_person_gallery(gallery_key)
                    
                    # 合并新下载的照片（去重）
                    all_photos = list(existing_photos) if existing_photos else []
                    for photo_path in thumbnail_paths:
                        if photo_path and photo_path not in all_photos:
                            all_photos.append(photo_path)
                    
                    # 设置到 person_gallery
                    self.chat_service.set_person_gallery(gallery_key, all_photos)
                    self.logger.info(f"已将 {len(thumbnail_paths)} 张缩略图设置到 gallery: {gallery_key}, 总计 {len(all_photos)} 张")
                else:
                    self.logger.warning("没有成功下载任何缩略图")
            except Exception as e:
                import traceback
                self.logger.error(f"批量下载缩略图时出错: {e}, traceback: {traceback.format_exc()}")
            finally:
                loop.close()
        
        # 在后台线程中执行下载
        download_thread = threading.Thread(target=download_and_update, daemon=True)
        download_thread.start()
    
    def _process_ui_update(self, update_data: Dict[str, Any]):
        """
        处理 UI 更新数据
        
        Args:
            update_data: UI 更新数据字典
        """
        update_type = update_data.get("type")
        
        if update_type == "chat_update":
            # 更新已存在的聊天消息
            index = update_data.get("index", -1)
            content = update_data.get("content")
            self.chat_service.update_chat_message(index, content)
        else:
            self.logger.debug(f"未处理的 UI 更新类型: {update_type}")
    
    def _load_people_photos(self, people: List[str]):
        """
        异步加载人物照片（通过人物名称）
        
        Args:
            people: 人物名称列表
        """
        def load_photos():
            """在后台线程中加载人物照片"""
            for person_name in people:
                try:
                    # 检查是否已经加载过
                    if person_name in self.chat_service.person_galleries:
                        self.logger.debug(f"人物 '{person_name}' 的照片已存在，跳过加载")
                        continue
                    
                    self.logger.info(f"开始加载人物照片: {person_name}")
                    
                    # 创建新的事件循环（因为在线程中）
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # 获取人物照片
                    photo_paths = loop.run_until_complete(
                        self.chat_service.get_person_photos(person_name, limit=50)
                    )
                    
                    if photo_paths:
                        # 保存到相册
                        self.chat_service.set_person_gallery(person_name, photo_paths)
                        self.logger.info(f"成功加载人物 '{person_name}' 的照片，共 {len(photo_paths)} 张")
                    else:
                        self.logger.warning(f"未找到人物 '{person_name}' 的照片")
                    
                    loop.close()
                    
                except Exception as e:
                    import traceback
                    self.logger.error(f"加载人物 '{person_name}' 照片时出错: {e}, traceback: {traceback.format_exc()}")
        
        # 在后台线程中执行加载
        load_thread = threading.Thread(target=load_photos, daemon=True)
        load_thread.start()
    
    def _load_people_photos_by_ids(self, people_ids: List[str], people_names: List[str] = None):
        """
        异步加载人物照片（通过人物 ID，优先使用）
        
        Args:
            people_ids: 人物 ID 列表
            people_names: 人物名称列表（可选，用于显示和存储）
        """
        def load_photos():
            """在后台线程中加载人物照片"""
            # 创建新的事件循环（因为在线程中）
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                # 合并所有人物照片
                all_photo_paths = []
                
                for idx, person_id in enumerate(people_ids):
                    try:
                        if not person_id:
                            continue
                        
                        # 获取人物名称（如果有）
                        person_name = people_names[idx] if people_names and idx < len(people_names) else f"Person_{person_id[:8]}"
                        
                        # 检查是否已经加载过（通过名称检查）
                        if person_name in self.chat_service.person_galleries:
                            self.logger.debug(f"人物 '{person_name}' 的照片已存在，跳过加载")
                            # 将已存在的照片添加到合并列表
                            existing_photos = self.chat_service.get_person_gallery(person_name)
                            all_photo_paths.extend(existing_photos)
                            continue
                        
                        self.logger.info(f"开始加载人物照片: person_id={person_id}, person_name={person_name}")
                        
                        # 通过 ID 获取人物照片
                        photo_paths = loop.run_until_complete(
                            self.chat_service.get_person_photos_by_id(person_id, limit=50)
                        )
                        
                        if photo_paths:
                            # 保存到相册（使用人物名称作为 key）
                            self.chat_service.set_person_gallery(person_name, photo_paths)
                            all_photo_paths.extend(photo_paths)
                            self.logger.info(f"成功加载人物 '{person_name}' 的照片，共 {len(photo_paths)} 张")
                        else:
                            self.logger.warning(f"未找到人物 ID '{person_id}' 的照片")
                        
                    except Exception as e:
                        import traceback
                        person_name = people_names[idx] if people_names and idx < len(people_names) else f"Person_{person_id[:8]}"
                        self.logger.error(f"加载人物 ID '{person_id}' ({person_name}) 照片时出错: {e}, traceback: {traceback.format_exc()}")
                
                # 如果有多个人物，将所有照片合并到一个相册中显示
                if len(people_ids) > 1 and all_photo_paths:
                    # 使用第一个有名称的人物作为 key，或者使用 "Multiple_People"
                    display_name = people_names[0] if people_names and people_names[0] else "Multiple_People"
                    self.chat_service.set_person_gallery(display_name, all_photo_paths)
                    self.logger.info(f"合并了 {len(people_ids)} 个人物的照片，共 {len(all_photo_paths)} 张")
                
            finally:
                loop.close()
        
        # 在后台线程中执行加载
        load_thread = threading.Thread(target=load_photos, daemon=True)
        load_thread.start()
