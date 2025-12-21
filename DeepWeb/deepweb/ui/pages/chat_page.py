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
import time
from typing import List, Dict, Any, Optional
from queue import Queue, Empty
import logging
import gradio as gr

# 导入组件
from deepweb.services.cloud_communication.websocket_client import WebSocketClient
from deepweb.ui.pages.chat.chat_service import ChatService
from deepweb.ui.pages.chat.chat_ui import ChatUI
from deepweb.ui.pages.chat.kiosk_iframe import KioskIframe


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
        
        # 4. Kiosk iframe 组件
        # 从配置中读取 Kiosk URL（如果有）
        if config_manager:
            all_config = config_manager.get_config()
            immich_config = all_config.get("immich", {})
            kiosk_base_url = immich_config.get("kiosk_url", "http://192.168.31.25:3000")
        else:
            kiosk_base_url = "http://192.168.31.25:3000"  # 默认值
        
        self.kiosk_base_url = kiosk_base_url
        self.logger.info(f"[ChatPage] 从配置读取kiosk_base_url: {self.kiosk_base_url}")
        
        # 优化：不再单独创建全屏模式的iframe实例
        # 全屏模式和聊天模式共用同一个iframe实例（在 chat_ui 中创建）
        # 通过切换高度和可见性来适应不同模式
        self.logger.info(f"[ChatPage] 优化：全屏模式和聊天模式共用iframe实例，kiosk_base_url={self.kiosk_base_url}")
        
        # UI 更新队列（用于异步更新）
        self.ui_update_queue = Queue(maxsize=100)
        
        # 待更新的 search_gallery 数据（用于自然语言搜索模式）
        self._pending_search_gallery: Optional[List] = None
        
        # 缓存最后使用的 iframe URL，避免频繁更新导致闪烁
        self._last_iframe_url: Optional[str] = None
        self._last_iframe_html: Optional[str] = None  # 缓存 HTML 内容，用于避免 translucent 类
        
        # 缓存最后更新的模式，避免频繁更新导致闪烁
        self._last_search_mode_update: Optional[str] = None
        self._last_search_gallery_visible: bool = False

        # 连接状态
        self.connection_status = "未连接"
        
        # 照片展示模式配置
        self.idle_threshold = 20.0  # 空闲阈值（秒）
        self.check_interval = 1.0   # 检查间隔（秒）- 改为5秒，减少闪烁
        self.current_view = "chat"  # 当前视图：chat 或 slideshow（兼容旧代码）
        
        # 事件驱动模式切换：待切换的模式标志位（None 表示不需要切换）
        self._pending_mode_switch: Optional[str] = None
        self._last_mode_check_time: float = 0.0  # 上次模式检查时间（用于防抖）

    def build(self):
        """
        构建 Gradio UI 界面（包含聊天视图和照片展示视图）
        
        Returns:
            Gradio Column 组件
        """
        with gr.Column() as main_container:
            # 聊天视图（默认显示，正常使用模式）
            with gr.Column(visible=True) as self.chat_view:  # 默认显示聊天模式
                # 构建聊天界面
                chat_interface = self.chat_ui.build(
                    device_id=self.ws_client.device_id,
                    client_id=self.ws_client.client_id,
                    websocket_url=self.ws_client.websocket_url,
                    chat_history=self.chat_service.get_chat_history(),
                    memory_markdown=self.chat_service.get_memory_markdown(),
                    kiosk_base_url=self.kiosk_base_url
                )
            
            # 照片展示视图（默认隐藏，全屏显示模式）
            # 全屏模式下使用独立的 iframe 实例，避免在隐藏的 chat_view 中显示
            with gr.Column(
                visible=False,  # 默认隐藏，进入全屏模式时显示
                elem_classes=["slideshow-view"],
                scale=1
            ) as self.slideshow_view:
                # 全屏模式专用的 iframe 实例（高度 1080px）
                self.slideshow_iframe_component = KioskIframe(self.logger, kiosk_base_url=self.kiosk_base_url)
                self.slideshow_iframe = self.slideshow_iframe_component.build(height=1080)
                
                # 初始化时设置为聊天模式
                self.chat_service.set_current_mode("chat")
                self.current_view = "chat"
                self.logger.info("[初始化] 默认进入聊天模式")
            
            # 添加调试按钮（用于手动切换模式，方便测试）
            with gr.Row(visible=True) as self.debug_buttons_row:  # 临时显示，调试结束后可以隐藏
                gr.Markdown("### 🧪 调试按钮（测试用）")
            with gr.Row(visible=True):  # 临时显示，调试结束后可以隐藏
                self.debug_btn_chat = gr.Button("切换到聊天模式", variant="primary", size="sm")
                self.debug_btn_slideshow = gr.Button("切换到全屏轮播模式", variant="secondary", size="sm")
                self.debug_btn_search = gr.Button("切换到搜索模式", variant="secondary", size="sm")
            
            # 绑定事件
            self.chat_ui.bind_events(
                on_connect=self.connect_websocket,
                on_disconnect=self.disconnect_websocket,
                on_send_message=self.send_message,
                on_clear_chat=self.clear_chat_history,
                on_refresh_memory=self.refresh_memory,
                on_clear_memory=self.clear_memory,
                on_update_ui=self.update_ui_with_slideshow_check,
                on_update_iframe=self.update_ui  # 专门用于 iframe 更新的函数
            )
            
            # 添加空闲检测定时器（用于检查是否应该切换到全屏轮播模式）
            # 优化方案：直接调用切换函数（类似调试按钮），但 iframe 不包含在输出中
            # iframe 由状态组件单独更新（2秒间隔），避免闪烁
            # 这样可以确保模式切换可靠执行，同时避免 iframe 闪烁
            self.idle_timer = gr.Timer(value=self.check_interval, active=True)
            self.idle_timer.tick(
                fn=self._check_idle_condition_and_apply_switch,  # 检查条件并直接执行切换
                inputs=[],
                outputs=[
                    self.chat_view,
                    self.slideshow_view,
                    # 注意：不包含 iframe，iframe 由状态组件单独更新（避免闪烁）
                    self.chat_ui.search_gallery,
                    self.chat_ui.timer          # 控制聊天定时器的 active 状态
                ]
            )
            
            # 绑定调试按钮事件（用于手动切换模式，方便测试）
            self.debug_btn_chat.click(
                fn=self._debug_switch_to_chat,
                inputs=[],
                outputs=[
                    self.chat_view,
                    self.slideshow_view,
                    self.chat_ui.kiosk_iframe,
                    self.slideshow_iframe,
                    self.chat_ui.search_gallery,
                    self.chat_ui.timer
                ]
            )
            self.debug_btn_slideshow.click(
                fn=self._debug_switch_to_slideshow,
                inputs=[],
                outputs=[
                    self.chat_view,
                    self.slideshow_view,
                    self.chat_ui.kiosk_iframe,
                    self.slideshow_iframe,
                    self.chat_ui.search_gallery,
                    self.chat_ui.timer
                ]
            )
            self.debug_btn_search.click(
                fn=self._debug_switch_to_search,
                inputs=[],
                outputs=[
                    self.chat_view,
                    self.slideshow_view,
                    self.chat_ui.kiosk_iframe,
                    self.slideshow_iframe,
                    self.chat_ui.search_gallery,
                    self.chat_ui.timer
                ]
            )

        return main_container

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

        # 更新消息时间（重置空闲定时器）
        self.chat_service.update_message_time()
        
        # 事件驱动：如果当前在全屏轮播模式，立即切换回聊天模式
        current_mode = self.chat_service.get_current_mode()
        if current_mode == "slideshow":
            self.logger.info("[事件驱动] 用户发送消息，设置切换到聊天模式标志")
            self._pending_mode_switch = "chat"
            # 注意：这里不直接调用 switch_to_chat_mode()，因为需要返回更新对象
            # 模式切换会在 update_ui 中处理
        # 注意：搜索模式下，用户发送新消息时不自动切换模式
        # 只有识别到新人物时才切换回聊天模式
        
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
    
    def update_ui_with_slideshow_check(self) -> tuple:
        """
        更新 UI 界面（定时调用，包含照片展示模式检查）
        优化：事件驱动模式切换，只在真正需要时更新组件
        
        Returns:
            (chat_history, status_text, kiosk_iframe_update, search_gallery_update) 的更新
        """
        # 记录是否有新消息
        has_new_message = False
        
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
                has_new_message = True
                
            except Empty:
                break
        
        # 处理 UI 更新队列
        while True:
            try:
                update_data = self.ui_update_queue.get_nowait()
                self._process_ui_update(update_data)
            except Empty:
                break
        
        # 如果有新消息，更新消息时间并检查是否需要切换模式（事件驱动）
        if has_new_message:
            self.chat_service.update_message_time()
            # 事件驱动：收到新消息时，如果在全屏模式，立即切换
            current_mode = self.chat_service.get_current_mode()
            if current_mode == "slideshow":
                self.logger.info("[事件驱动] 收到新消息，设置切换到聊天模式标志")
                self._pending_mode_switch = "chat"
                self.current_view = "chat"
        
        # 注意：模式切换的更新由 mode_switch_timer 单独处理
        # 这里不需要检查模式切换，因为模式切换是异步的，由专门的定时器处理
        
        # 调用原有的 update_ui 逻辑
        # 注意：iframe 更新由状态组件单独处理，这里不返回 iframe 更新
        chat_history, status_text, _, search_gallery_update = self.update_ui()
        
        return (chat_history, status_text, search_gallery_update)
    
    def update_ui(self) -> tuple:
        """
        更新 UI 界面（定时调用）
        
        Returns:
            (chat_history, status_text, kiosk_iframe_update, search_gallery_update) 的更新
        """
        current_mode = self.chat_service.get_current_mode()
        
        # 根据当前模式控制组件的可见性和内容
        kiosk_iframe_update = gr.update()  # 默认不更新
        search_gallery_update = gr.update()  # 默认不更新
        
        # 全屏轮播模式：不更新任何内容，避免刷新导致闪屏
        if current_mode == "slideshow":
            # 优化：在全屏模式下，完全不更新任何组件，减少闪烁
            # 注意：即使返回 gr.update()，Gradio 仍可能触发检查
            # 但这是 Gradio 的限制，我们只能尽量减少更新频率
            # 通过返回相同的值（chat_history 和 connection_status），减少重新渲染
            self.logger.debug(f"[update_ui] 当前为全屏轮播模式，不更新任何组件（避免刷新）")
            # 返回当前值，不触发更新
            current_chat_history = self.chat_service.get_chat_history()
            current_status = self.connection_status
            return (
                current_chat_history,  # 返回当前值，不触发更新
                current_status,        # 返回当前值，不触发更新
                gr.update(),           # kiosk_iframe - 不更新（共用实例）
                gr.update()            # search_gallery - 不更新
            )
        
        if current_mode == "chat":
            # 聊天模式：显示 kiosk_iframe，隐藏 search_gallery
            kiosk_url = self.chat_service.get_last_kiosk_url()
            # 如果没有保存的 URL，使用默认 URL（不带人物参数，轮播所有照片）
            if not kiosk_url:
                kiosk_url = self.kiosk_base_url
            
            # 检查 URL 是否变化（避免频繁更新导致闪烁）
            if not hasattr(self, '_last_iframe_url'):
                self._last_iframe_url = None
            
            # 检查模式是否变化
            if not hasattr(self, '_last_search_mode_update'):
                self._last_search_mode_update = None
            
            # 只在 URL 变化或模式切换时才更新（避免闪烁和 translucent 类）
            if kiosk_url != self._last_iframe_url or self._last_search_mode_update != "chat":
                # 从 URL 中提取 person_id（如果有）
                person_id = None
                if "?person=" in kiosk_url:
                    try:
                        person_id = kiosk_url.split("?person=")[1].split("&")[0]
                    except:
                        pass
                
                # 使用 KioskIframe 组件更新（高度800px，聊天模式）
                kiosk_iframe_update_base = self.chat_ui.kiosk_iframe_component.update_person(person_id, height=800)
                # 合并 visible 属性（gr.update 返回的是字典，需要合并）
                kiosk_iframe_update = gr.update(
                    value=kiosk_iframe_update_base.get("value"),
                    visible=True
                )
                self._last_iframe_url = kiosk_url
                self._last_search_mode_update = "chat"
                self._last_search_gallery_visible = False  # 重置 gallery 可见性标记
            else:
                # URL 和模式都没变化，不更新 value（避免闪烁和 translucent 类）
                # 只返回空的 gr.update()，不包含 value，这样 Gradio 就不会更新内容，也就不会添加 translucent 类
                kiosk_iframe_update = gr.update()
            
            # 确保 search_gallery 隐藏（只在模式切换时更新）
            if self._last_search_mode_update != "chat":
                search_gallery_update = gr.update(visible=False)
            else:
                search_gallery_update = gr.update()  # 不更新，避免闪烁
            
        elif current_mode == "search":
            # 搜索模式：隐藏 kiosk_iframe，显示 search_gallery
            # 在搜索模式下，iframe 必须始终隐藏（包括保护期内）
            # 检查是否在保护期内，如果在保护期内，强制隐藏 iframe
            is_protected = self.chat_service.is_search_mode_protected()
            
            # 如果模式刚切换，或者当前模式标记不是 search，强制更新可见性
            if not hasattr(self, '_last_search_mode_update') or self._last_search_mode_update != "search":
                kiosk_iframe_update = gr.update(visible=False)
                self._last_search_mode_update = "search"
            elif is_protected:
                # 在保护期内，确保 iframe 始终隐藏（防止同时显示）
                kiosk_iframe_update = gr.update(visible=False)
            else:
                # 已经更新过可见性且不在保护期，不重复更新（避免闪烁）
                kiosk_iframe_update = gr.update()
            
            # 更新 search_gallery（如果有待更新的数据）
            if self._pending_search_gallery is not None:
                search_gallery_update = gr.update(
                    value=self._pending_search_gallery,
                    visible=True
                )
                self._pending_search_gallery = None  # 清除待更新数据
                self._last_search_gallery_visible = True
            else:
                # 没有新数据，但确保可见性正确（只在第一次切换时更新）
                if not hasattr(self, '_last_search_gallery_visible') or not self._last_search_gallery_visible:
                    search_gallery_update = gr.update(visible=True)
                    self._last_search_gallery_visible = True
                else:
                    search_gallery_update = gr.update()  # 不更新，避免闪烁
        
        # 返回当前状态
        return (
            self.chat_service.get_chat_history(),
            self.connection_status,
            kiosk_iframe_update,
            search_gallery_update
        )
    
    def _check_idle_condition_and_apply_switch(self) -> tuple:
        """
        检查空闲条件并直接执行模式切换（定时器调用）
        优化方案：直接调用切换函数（类似调试按钮），但 iframe 不包含在输出中
        iframe 由状态组件单独更新（2秒间隔），避免闪烁
        
        Returns:
            组件的更新（4个值：chat_view, slideshow_view, search_gallery, timer）
            不包含 iframe，iframe 由状态组件单独更新
        """
        import time
        current_time = time.time()
        current_mode = self.chat_service.get_current_mode()
        
        # 防抖：如果距离上次检查时间太短（<0.5秒），跳过检查
        if current_time - self._last_mode_check_time < 0.5:
            return self._no_change_without_iframe()
        
        self._last_mode_check_time = current_time
        
        # 如果当前在全屏轮播模式，检查是否应该切换回聊天模式
        if current_mode == "slideshow":
            if self.chat_service.should_exit_slideshow():
                self.logger.info("[定时器] 检测到新消息，直接切换到聊天模式")
                result = self.switch_to_chat_mode()
                # 返回不包含 iframe 的更新（iframe 由状态组件单独更新）
                return (result[0], result[1], result[4], result[5])  # chat_view, slideshow_view, search_gallery, timer
            # 否则保持全屏轮播模式，不更新
            return self._no_change_without_iframe()
        
        # 无论当前在什么模式（chat 或 search），如果空闲20秒，都切换到全屏轮播模式
        should_enter = self.chat_service.should_enter_slideshow(self.idle_threshold)
        if should_enter:
            # 检查是否已经在全屏模式（避免重复切换）
            if current_mode == "slideshow":
                self.logger.debug(f"[定时器] 已经在全屏轮播模式，跳过")
                return self._no_change_without_iframe()
            
            self.logger.info(f"[定时器] 满足进入全屏轮播模式条件，直接执行切换 (idle_threshold={self.idle_threshold}s)")
            result = self.switch_to_slideshow_mode()
            # 返回不包含 iframe 的更新（iframe 由状态组件单独更新）
            return (result[0], result[1], result[4], result[5])  # chat_view, slideshow_view, search_gallery, timer
        else:
            # 记录当前空闲时间，用于调试
            current_time = time.time()
            last_message_time = self.chat_service.last_message_time
            last_person_update_time = self.chat_service.last_person_update_time
            idle_time = current_time - max(last_message_time, last_person_update_time)
            self.logger.debug(f"[定时器] 未满足进入全屏轮播模式条件: idle_time={idle_time:.1f}s < {self.idle_threshold}s")
        
        # 否则保持当前模式，不更新
        return self._no_change_without_iframe()
    
    def _no_change_without_iframe(self) -> tuple:
        """返回不改变的更新（不包含 iframe）"""
        return (
            gr.update(),  # chat_view - 不更新
            gr.update(),  # slideshow_view - 不更新
            gr.update(),  # search_gallery - 不更新
            gr.update()   # timer - 不更新（保持当前状态）
        )
    
    def _debug_switch_to_chat(self) -> tuple:
        """调试用：手动切换到聊天模式"""
        self.logger.info("[调试] 手动切换到聊天模式")
        # 直接调用切换函数，不使用标志位
        return self.switch_to_chat_mode()
    
    def _debug_switch_to_slideshow(self) -> tuple:
        """调试用：手动切换到全屏轮播模式"""
        self.logger.info("[调试] 手动切换到全屏轮播模式")
        # 直接调用切换函数，不使用标志位
        return self.switch_to_slideshow_mode()
    
    def _debug_switch_to_search(self) -> tuple:
        """调试用：手动切换到搜索模式"""
        self.logger.info("[调试] 手动切换到搜索模式")
        # 搜索模式需要 assets，这里使用空列表
        # 直接调用切换函数，不使用标志位
        return self.switch_to_search_mode([])
    
    def check_and_switch_to_slideshow(self) -> Optional[tuple]:
        """
        检查并执行模式切换（由 update_ui 调用，事件驱动）
        注意：这个方法现在主要用于检查，实际切换由 _apply_mode_switch_from_state 执行
        通过状态组件的变化触发（事件驱动）
        
        Returns:
            如果有待切换的模式，返回切换结果；否则返回 None
        """
        # 检查是否有待切换的模式
        if hasattr(self, '_pending_mode_switch') and self._pending_mode_switch is not None:
            # 有待切换的模式，但实际切换由 _apply_mode_switch_from_state 执行
            # 通过状态组件的变化触发（事件驱动）
            # 这里只返回 None，让调用者知道有待切换的模式
            return None
        
        return None
    
    def _no_change(self) -> tuple:
        """
        返回不改变的更新（避免刷新）
        
        注意：gr.update() 不带参数表示"不更新组件"，但 Gradio 仍会检查这个更新对象，
        可能触发内部检查，导致轻微的重新渲染。这是 Gradio 的限制。
        """
        current_mode = self.chat_service.get_current_mode()
        if current_mode == "slideshow":
            # 全屏模式下记录日志（用于调试）
            self.logger.debug(f"[_no_change] 全屏轮播模式，不更新任何组件（避免闪屏）")
        
        # 统一返回：不更新任何组件（两个分支返回完全相同，合并为一个）
        return (
            gr.update(),  # chat_view - 不更新
            gr.update(),  # slideshow_view - 不更新
            gr.update(),  # chat_iframe - 不更新
            gr.update(),  # slideshow_iframe - 不更新
            gr.update(),  # search_gallery - 不更新
            gr.update()   # timer - 不更新（保持当前状态）
        )
    
    def _build_iframe_html(self, kiosk_url: Optional[str] = None, height: str = "800px") -> str:
        """
        构建 iframe HTML 内容
        
        Args:
            kiosk_url: Kiosk URL（可选，如果为 None 则使用默认 URL）
            height: iframe 高度，默认 800px（聊天模式），全屏模式使用 100vh
            
        Returns:
            HTML 字符串
        """
        if not kiosk_url:
            kiosk_url = self.kiosk_base_url
        
        # 注意：size 参数应该在调用此方法前已经添加到 URL 中
        # 这里不再重复添加，避免重复参数
        
        # 如果高度是 100vh，使用 JavaScript 动态计算（避免 100vh 的问题）
        if height == "100vh":
            # 使用 JavaScript 动态计算视口高度
            container_id = f"iframe-container-{abs(hash(kiosk_url))}"
            iframe_id = f"iframe-{abs(hash(kiosk_url))}"
            html_content = f"""
            <div id="{container_id}" style="width: 100%; margin: 0; padding: 0; overflow: hidden;">
                <iframe 
                    id="{iframe_id}"
                    src="{kiosk_url}" 
                    width="100%" 
                    frameborder="0"
                    style="border: none; margin: 0; padding: 0; display: block; width: 100%;"
                    allowfullscreen
                ></iframe>
                <script>
                    (function() {{
                        function setHeight() {{
                            var container = document.getElementById('{container_id}');
                            var iframe = document.getElementById('{iframe_id}');
                            if (container && iframe) {{
                                var height = window.innerHeight;
                                container.style.height = height + 'px';
                                iframe.style.height = height + 'px';
                            }}
                        }}
                        setHeight();
                        window.addEventListener('resize', setHeight);
                    }})();
                </script>
            </div>
            """
        else:
            # 使用固定高度（聊天模式）
            html_content = f"""
            <div style="width: 100%; height: {height}; margin: 0; padding: 0; overflow: hidden;">
                <iframe 
                    src="{kiosk_url}" 
                    width="100%" 
                    height="{height}" 
                    frameborder="0"
                    style="border: none; margin: 0; padding: 0; display: block;"
                    allowfullscreen
                ></iframe>
            </div>
            """
        return html_content
    
    def switch_to_chat_mode(self, kiosk_url: Optional[str] = None) -> tuple:
        """
        切换到聊天模式（模式 A）
        
        Args:
            kiosk_url: Kiosk URL（可选，如果提供则更新 iframe）
            
        Returns:
            所有组件的更新
        """
        self.chat_service.set_current_mode("chat")
        self.current_view = "chat"
        self.logger.info("切换到聊天模式")
        
        # 如果没有提供 kiosk_url，使用最后保存的，如果没有则使用默认 URL
        if not kiosk_url:
            kiosk_url = self.chat_service.get_last_kiosk_url()
            if not kiosk_url:
                kiosk_url = self.kiosk_base_url
        
        # 从 URL 中提取 person_id（如果有）
        person_id = None
        if "?person=" in kiosk_url:
            try:
                person_id = kiosk_url.split("?person=")[1].split("&")[0]
            except:
                pass
        
        # 使用 KioskIframe 组件更新（高度800px，聊天模式）
        kiosk_iframe_update_base = self.chat_ui.kiosk_iframe_component.update_person(person_id, height=800)
        # 合并 visible 属性（gr.update 返回的是字典，需要合并）
        kiosk_iframe_update = gr.update(
            value=kiosk_iframe_update_base.get("value"),
            visible=True
        )
        
        # 更新缓存的 URL
        self._last_iframe_url = kiosk_url
        
        return (
            gr.update(visible=True),   # chat_view
            gr.update(visible=False),  # slideshow_view
            kiosk_iframe_update,        # chat_iframe (聊天模式 iframe，更新高度为800px)
            gr.update(visible=False),  # slideshow_iframe (全屏模式 iframe，隐藏)
            gr.update(visible=False),  # search_gallery
            gr.update(active=True)     # timer - 启用聊天定时器
        )
    
    def switch_to_slideshow_mode(self) -> tuple:
        """
        切换到全屏轮播模式（模式 B）
        
        Returns:
            所有组件的更新
        """
        self.chat_service.set_current_mode("slideshow")
        self.current_view = "slideshow"
        
        # 使用最后保存的 person_id，如果没有则使用 None（显示所有照片）
        person_info = self.chat_service.get_last_person_info()
        person_id = person_info.get("person_id")
        
        # 打印切换到全屏模式的信息
        self.logger.info(f"[全屏模式] 切换到全屏轮播模式: person_id={person_id}, height=1080px")
        
        # 全屏模式下使用独立的 iframe 实例（在 slideshow_view 中）
        # 使用全屏模式的 iframe 组件更新（高度1080px）
        slideshow_iframe_update_base = self.slideshow_iframe_component.update_person(person_id, height=1080)
        # 合并 visible 属性
        slideshow_iframe_update = gr.update(
            value=slideshow_iframe_update_base.get("value"),
            visible=True  # 全屏模式下 iframe 可见
        )
        
        return (
            gr.update(visible=False),  # chat_view
            gr.update(visible=True),   # slideshow_view
            gr.update(visible=False),  # chat_iframe (聊天模式 iframe，隐藏)
            slideshow_iframe_update,    # slideshow_iframe (全屏模式 iframe，更新高度为1080px)
            gr.update(),                # search_gallery (不变)
            gr.update(active=False)     # timer - 禁用聊天定时器，避免闪烁
        )
    
    def switch_to_search_mode(self, assets: List[Dict]) -> tuple:
        """
        切换到自然语言搜索模式（模式 C）
        
        Args:
            assets: 搜索结果资产列表（最多6张）
            
        Returns:
            所有组件的更新
        """
        self.chat_service.set_current_mode("search")
        self.logger.info(f"切换到自然语言搜索模式: 共 {len(assets)} 张图片")
        
        # 注意：assets 会在 _download_and_update_thumbnails 中处理
        # 这里只是切换模式，实际的 Gallery 更新会在下载完成后进行
        
        return (
            gr.update(visible=True),   # chat_view
            gr.update(visible=False),  # slideshow_view
            gr.update(visible=False),  # chat_iframe (聊天模式 iframe，隐藏)
            gr.update(visible=False),  # slideshow_iframe (全屏模式 iframe，隐藏)
            gr.update(visible=True),   # search_gallery
            gr.update(active=True)     # timer - 保持启用聊天定时器（搜索模式需要实时更新）
        )
    
    def switch_to_chat_page(self) -> tuple:
        """
        切换回聊天页面（兼容旧代码）
        
        Returns:
            所有组件的更新
        """
        return self.switch_to_chat_mode()
    
    def _on_websocket_message(self, message: Dict[str, Any]):
        """
        WebSocket 消息接收回调
        
        Args:
            message: WebSocket 消息字典
        """
        # 消息会通过 get_message() 方法处理，这里可以记录日志
        self.logger.debug(f"收到 WebSocket 消息: type={message.get('type')}")
        
        # 更新消息时间（重置空闲定时器）
        self.chat_service.update_message_time()
        
        # 事件驱动：如果当前在照片展示模式，设置切换到聊天模式标志
        current_mode = self.chat_service.get_current_mode()
        if current_mode == "slideshow":
            self.logger.info("[事件驱动] 收到WebSocket消息，设置切换到聊天模式标志")
            self._pending_mode_switch = "chat"
            self.current_view = "chat"
    
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
        
        # 更新消息时间（重置空闲定时器）
        self.chat_service.update_message_time()
        
        # 事件驱动：如果当前在照片展示模式，设置切换到聊天模式标志
        current_mode = self.chat_service.get_current_mode()
        if current_mode == "slideshow":
            self.logger.info("[事件驱动] 收到WebSocket消息，设置切换到聊天模式标志")
            self._pending_mode_switch = "chat"
            self.current_view = "chat"
        
        if result_type == "user_message":
            # 用户消息
            self.chat_service.add_chat_message(data)
            
        elif result_type == "assistant_message":
            # AI 回复消息
            self.chat_service.add_chat_message(data)
            
        elif result_type == "vision_message":
            # 视觉识别消息（已包含图片）
            self.chat_service.add_chat_message(data)
            # 注意：不再加载人物照片到 gallery，人物照片通过 Kiosk URL 在 iframe 中显示
            
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
            
            # 注意：不再加载人物照片到 gallery，人物照片通过 Kiosk URL 在 iframe 中显示
            
        elif result_type == "memory_update":
            # 更新记忆
            self.chat_service.update_memory(data["content"])
            
        elif result_type == "memory_append":
            # 追加记忆
            self.chat_service.append_memory(data["content"])
            
        elif result_type == "immich_kiosk_url_message":
            # Immich Kiosk URL 消息
            kiosk_url = data.get("kiosk_url")
            person_name = data.get("person_name")
            person_id = data.get("person_id")
            
            # 更新人物信息
            self.chat_service.update_person_info(
                person_name=person_name,
                person_id=person_id,
                kiosk_url=kiosk_url
            )
            
            # 如果当前在搜索模式，检查是否在保护期内
            # 如果不在搜索模式，更新 iframe URL
            current_mode = self.chat_service.get_current_mode()
            if current_mode == "search":
                # 检查是否在保护期内
                if self.chat_service.is_search_mode_protected():
                    # 在保护期内，忽略人物识别，保持搜索模式
                    self.logger.info(
                        f"搜索模式保护期内，忽略人物识别 {person_name}，保持搜索模式"
                    )
                else:
                    # 保护期已过，识别到新人物，切换到聊天模式
                    # 这是退出搜索模式的唯一条件（除了空闲超时）
                    self.chat_service.set_current_mode("chat")
                    # 清除缓存的 URL，强制更新 iframe
                    if hasattr(self, '_last_iframe_url'):
                        self._last_iframe_url = None
                    self.logger.info(
                        f"保护期已过，识别到新人物 {person_name}，从搜索模式切换到聊天模式: {kiosk_url}"
                    )
            else:
                # 更新 iframe URL（聊天模式或全屏轮播模式）
                # 注意：这里不能直接更新，需要通过定时器更新
                # 先保存到服务中，定时器会读取并更新
                # 清除缓存的 URL，强制更新 iframe
                if hasattr(self, '_last_iframe_url'):
                    self._last_iframe_url = None
                self.logger.info(f"收到 Kiosk URL，将在下次更新时刷新 iframe: {kiosk_url}")
        
        elif result_type == "immich_search_result_message":
            # Immich 搜索结果消息（需要批量下载缩略图）
            import time
            start_time = time.time()  # 记录开始时间
            
            # 先添加文本消息
            current_index = len(self.chat_service.chat_history)
            self.chat_service.add_chat_message({
                "role": data["role"],
                "content": data["content"],
                "session_id": data["session_id"]
            })
            
            # 判断是否为自然语言搜索（有 query 参数且不为空）
            query = data.get("query", "")
            if query:
                # 自然语言搜索：切换到搜索模式，并重置保护期
                # reset_protection=True 确保每次收到新的搜索请求都重置保护期
                self.chat_service.set_current_mode("search", reset_protection=True)
                self.logger.info(f"收到自然语言搜索请求，切换到搜索模式: query={query}")
                # 注意：切换到搜索模式后，只有识别到新人物时才切换回聊天模式
                # 或者空闲时间超过阈值时切换到全屏轮播模式
            
            self.logger.info(f"[性能统计] 收到 Immich 搜索结果，开始下载: asset_ids={data['asset_ids']}, 开始时间={start_time:.3f}")
            
            # 异步批量下载缩略图并更新消息
            self._download_and_update_thumbnails(
                asset_ids=data["asset_ids"],
                text_content=data["content"],
                expected_index=current_index,
                person_name=data.get("person_name"),
                query=query,
                count=data.get("count", 0),
                start_time=start_time  # 传递开始时间
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
        count: int = 0,
        start_time: Optional[float] = None
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
            import time
            
            # 记录各个阶段的时间
            thread_start_time = time.time()
            download_start_time = None
            download_end_time = None
            gallery_set_time = None
            
            self.logger.info(f"[性能统计] 后台线程开始批量下载缩略图: 共 {len(asset_ids)} 个资产, 线程启动耗时: {(thread_start_time - start_time) * 1000:.2f}ms")
            
            try:
                # 创建新的事件循环（因为在线程中）
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # 批量下载缩略图（返回 PIL Image 对象，性能最优）
                download_start_time = time.time()
                self.logger.info(f"[性能统计] 开始调用 download_immich_thumbnails_batch (return_pil=True), 耗时: {(download_start_time - start_time) * 1000:.2f}ms")
                
                thumbnail_images = loop.run_until_complete(
                    self.chat_service.download_immich_thumbnails_batch(asset_ids, return_pil=True)
                )
                
                download_end_time = time.time()
                download_duration = (download_end_time - download_start_time) * 1000
                total_duration = (download_end_time - start_time) * 1000
                self.logger.info(f"[性能统计] download_immich_thumbnails_batch 完成: 返回 {len(thumbnail_images)} 个 PIL Image 对象, 下载耗时: {download_duration:.2f}ms, 总耗时: {total_duration:.2f}ms")
                
                if thumbnail_images:
                    # 根据当前模式决定如何处理下载的缩略图
                    current_mode = self.chat_service.get_current_mode()
                    
                    gallery_set_time = time.time()
                    
                    if current_mode == "search":
                        # 自然语言搜索模式：设置到 search_gallery（最多6张）
                        search_photos = thumbnail_images[:6]  # 固定显示最多6张
                        # 注意：这里需要更新 search_gallery，但需要通过定时器更新
                        # 先保存到临时变量，定时器会读取
                        self._pending_search_gallery = search_photos
                        # 强制清除 iframe URL 缓存，确保下次更新时隐藏 iframe
                        if hasattr(self, '_last_iframe_url'):
                            self._last_iframe_url = None
                        # 重置模式标记，强制更新可见性
                        if hasattr(self, '_last_search_mode_update'):
                            self._last_search_mode_update = None
                        self.logger.info(f"[性能统计] 已将 {len(search_photos)} 张缩略图准备设置到 search_gallery（自然语言搜索模式）")
                    else:
                        # 其他模式（聊天模式）：不使用 gallery，使用 iframe 显示
                        # 人物照片通过 Kiosk URL 在 iframe 中轮播，不需要下载缩略图
                        # 这里只记录日志，不设置 gallery
                        self.logger.info(f"[性能统计] 下载了 {len(thumbnail_images)} 张缩略图，但当前为 {current_mode} 模式，使用 iframe 显示，不设置 gallery")
                    
                    gallery_set_end_time = time.time()
                    gallery_set_duration = (gallery_set_end_time - gallery_set_time) * 1000
                    total_duration_final = (gallery_set_end_time - start_time) * 1000
                    
                    self.logger.info(f"[性能统计] 完整流程耗时统计:")
                    self.logger.info(f"  - 收到消息到线程启动: {(thread_start_time - start_time) * 1000:.2f}ms")
                    self.logger.info(f"  - 线程启动到开始下载: {(download_start_time - thread_start_time) * 1000:.2f}ms")
                    self.logger.info(f"  - 下载耗时: {download_duration:.2f}ms (平均每张: {download_duration / len(thumbnail_images):.2f}ms)")
                    self.logger.info(f"  - 处理 gallery 耗时: {gallery_set_duration:.2f}ms")
                    self.logger.info(f"  - 总耗时: {total_duration_final:.2f}ms")
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
    
    # 注意：以下方法已废弃，不再使用
    # 人物照片现在通过 Kiosk URL 在 iframe 中显示，不需要加载到 gallery
    # 保留这些方法定义以避免可能的引用错误，但不会被执行
