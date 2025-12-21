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
from deepweb.ui.pages.chat.display_mode_state_machine import DisplayModeStateMachine, DisplayMode


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

        # 连接状态
        self.connection_status = "未连接"
        
        # 照片展示模式配置
        self.idle_threshold = 20.0  # 空闲阈值（秒）
        self.check_interval = 1.0   # 检查间隔（秒）
        self.current_view = "chat"  # 当前视图：chat 或 slideshow（兼容旧代码）
        
        # 状态机（在 build 方法中初始化，因为需要访问组件）
        self.state_machine: Optional[DisplayModeStateMachine] = None
        self._last_mode_check_time: float = 0.0  # 上次模式检查时间（用于防抖）
        self._pending_mode_switch_result: Optional[tuple] = None  # 待应用的模式切换结果

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
            
            # 初始化状态机（在组件创建之后）
            self.state_machine = DisplayModeStateMachine(self)
            self.logger.info("[ChatPage] 状态机已初始化")
            
            # 添加调试按钮（用于手动切换模式，方便测试）
            with gr.Row(visible=True) as self.debug_buttons_row:  # 临时显示，调试结束后可以隐藏
                gr.Markdown("### 🧪 调试按钮（测试用）")
            with gr.Row(visible=True):  # 临时显示，调试结束后可以隐藏
                self.debug_btn_chat = gr.Button("切换到聊天模式", variant="primary", size="sm")
                self.debug_btn_slideshow = gr.Button("切换到全屏轮播模式", variant="primary", size="sm")
                self.debug_btn_search = gr.Button("切换到搜索模式", variant="primary", size="sm")
            
            # 绑定事件
            self.chat_ui.bind_events(
                on_connect=self.connect_websocket,
                on_disconnect=self.disconnect_websocket,
                on_send_message=self.send_message,
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
                fn=self._check_idle_condition_and_apply_switch,
                inputs=[],
                outputs=[
                    self.chat_view,
                    self.slideshow_view,
                    self.chat_ui.search_gallery,
                    self.chat_ui.timer,
                    self.chat_ui.iframe_immediate_trigger  # 用于立即触发 iframe 更新
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
        if self.state_machine and self.state_machine.get_current_mode() == DisplayMode.SLIDESHOW:
            self.logger.info("[事件驱动] 用户发送消息，切换到聊天模式")
            # 注意：这里不直接调用状态机切换，因为需要返回更新对象
            # 模式切换会在定时器中处理
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
            if self.state_machine and self.state_machine.get_current_mode() == DisplayMode.SLIDESHOW:
                self.logger.info("[事件驱动] 收到新消息，将在定时器中切换到聊天模式")
                self.current_view = "chat"
        
        # 使用状态机获取 UI 更新
        if self.state_machine:
            chat_history, status_text, _, search_gallery_update = self.state_machine.get_ui_updates()
            return (chat_history, status_text, search_gallery_update)
        else:
            # 状态机未初始化，返回默认值
            return (
                self.chat_service.get_chat_history(),
                self.connection_status,
                gr.update(),
                gr.update()
            )
    
    def update_ui(self) -> tuple:
        """
        更新 UI 界面（定时调用）
        
        Returns:
            (chat_history, status_text, kiosk_iframe_update, search_gallery_update) 的更新
        """
        # 使用状态机获取 UI 更新
        if self.state_machine:
            return self.state_machine.get_ui_updates()
        else:
            # 状态机未初始化，返回默认值
            return (
                self.chat_service.get_chat_history(),
                self.connection_status,
                gr.update(),
                gr.update()
            )
    
    def _check_idle_condition_and_apply_switch(self) -> tuple:
        """
        检查空闲条件并直接执行模式切换（定时器调用）
        
        Returns:
            组件的更新（5个值：chat_view, slideshow_view, search_gallery, timer, iframe_immediate_trigger）
        """
        import time
        current_time = time.time()
        
        if not self.state_machine:
            return self._no_change_with_trigger(gr.update())
        
        # 检查是否有待应用的模式切换结果（用于立即应用模式切换）
        if hasattr(self, '_pending_mode_switch_result') and self._pending_mode_switch_result is not None:
            result = self._pending_mode_switch_result
            self._pending_mode_switch_result = None  # 清除待应用的结果
            # 返回完整的模式切换更新（chat_view, slideshow_view, kiosk_iframe, slideshow_iframe, search_gallery, timer）
            # 但定时器只需要返回 (chat_view, slideshow_view, search_gallery, timer, iframe_immediate_trigger)
            trigger_update = gr.update(value=time.time())  # 立即触发 iframe 更新
            self.logger.info("[定时器] 应用待处理的模式切换更新")
            return (result[0], result[1], result[4], result[5], trigger_update)
        
        current_mode = self.state_machine.get_current_mode()
        
        # 检查是否需要立即更新 iframe（用于模式切换时立即隐藏 iframe）
        need_immediate_update = getattr(self, '_need_immediate_iframe_update', False)
        if need_immediate_update:
            self._need_immediate_iframe_update = False  # 清除标志
            # 立即触发 iframe 更新
            trigger_update = gr.update(value=time.time())
        else:
            trigger_update = gr.update()  # 不更新
        
        # 防抖：如果距离上次检查时间太短（<0.5秒），跳过检查（但仍返回 trigger_update）
        if current_time - self._last_mode_check_time < 0.5:
            return self._no_change_with_trigger(trigger_update)
        
        self._last_mode_check_time = current_time
        
        # 如果当前在全屏轮播模式，检查是否应该切换回聊天模式
        if current_mode == DisplayMode.SLIDESHOW:
            if self.chat_service.should_exit_slideshow():
                self.logger.info("[定时器] 检测到新消息，直接切换到聊天模式")
                result = self.switch_to_chat_mode()
                return (result[0], result[1], result[4], result[5], trigger_update)
            return self._no_change_with_trigger(trigger_update)
        
        # 无论当前在什么模式（chat 或 search），如果空闲20秒，都切换到全屏轮播模式
        should_enter = self.chat_service.should_enter_slideshow(self.idle_threshold)
        if should_enter:
            if current_mode == DisplayMode.SLIDESHOW:
                self.logger.debug(f"[定时器] 已经在全屏轮播模式，跳过")
                return self._no_change_with_trigger(trigger_update)
            
            self.logger.info(f"[定时器] 满足进入全屏轮播模式条件，直接执行切换 (idle_threshold={self.idle_threshold}s)")
            result = self.switch_to_slideshow_mode()
            return (result[0], result[1], result[4], result[5], trigger_update)
        else:
            # 记录当前空闲时间，用于调试
            current_time = time.time()
            last_message_time = self.chat_service.last_message_time
            last_person_update_time = self.chat_service.last_person_update_time
            idle_time = current_time - max(last_message_time, last_person_update_time)
            self.logger.debug(f"[定时器] 未满足进入全屏轮播模式条件: idle_time={idle_time:.1f}s < {self.idle_threshold}s")
        
        return self._no_change_with_trigger(trigger_update)
    
    def _no_change_with_trigger(self, trigger_update=None) -> tuple:
        """返回不改变的更新（包含 iframe_immediate_trigger）"""
        if trigger_update is None:
            trigger_update = gr.update()
        return (
            gr.update(),  # chat_view - 不更新
            gr.update(),  # slideshow_view - 不更新
            gr.update(),  # search_gallery - 不更新
            gr.update(),  # timer - 不更新
            trigger_update  # iframe_immediate_trigger - 根据标志决定是否更新
        )
    
    def _debug_switch_to_chat(self) -> tuple:
        """调试用：手动切换到聊天模式"""
        self.logger.info("[调试] 手动切换到聊天模式")
        # 直接调用 switch_to_chat_mode，状态机内部已处理所有逻辑（包括 update_message_time）
        return self.switch_to_chat_mode()
    
    def _debug_switch_to_slideshow(self) -> tuple:
        """调试用：手动切换到全屏轮播模式"""
        self.logger.info("[调试] 手动切换到全屏轮播模式")
        # 直接调用 switch_to_slideshow_mode，状态机内部已处理所有逻辑
        return self.switch_to_slideshow_mode()
    
    def _debug_switch_to_search(self) -> tuple:
        """调试用：手动切换到搜索模式"""
        self.logger.info("[调试] 手动切换到搜索模式")
        # 直接调用 switch_to_search_mode，状态机内部已处理所有逻辑
        return self.switch_to_search_mode([])
    
    def check_and_switch_to_slideshow(self) -> Optional[tuple]:
        """
        检查并执行模式切换（由 update_ui 调用，事件驱动）
        注意：这个方法已废弃，模式切换现在由状态机统一管理
        
        Returns:
            None（已废弃）
        """
        # 已废弃，模式切换由状态机统一管理
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
        if not self.state_machine:
            return self._no_change()
        
        # 如果没有提供 kiosk_url，使用最后保存的，如果没有则使用默认 URL
        if not kiosk_url:
            kiosk_url = self.chat_service.get_last_kiosk_url()
            if not kiosk_url:
                kiosk_url = self.kiosk_base_url
        
        # 使用状态机切换模式
        return self.state_machine.enter_chat_mode(kiosk_url)
    
    def switch_to_slideshow_mode(self) -> tuple:
        """
        切换到全屏轮播模式（模式 B）
        
        Returns:
            所有组件的更新
        """
        if not self.state_machine:
            return self._no_change()
        
        # 使用最后保存的 person_id，如果没有则使用 None（显示所有照片）
        person_info = self.chat_service.get_last_person_info()
        person_id = person_info.get("person_id")
        
        # 使用状态机切换模式
        # 注意：状态机内部会确保 slideshow_iframe 的 value 被正确更新
        result = self.state_machine.enter_slideshow_mode(person_id)
        self.logger.info(f"[switch_to_slideshow_mode] 切换到全屏模式，person_id={person_id}")
        return result
    
    def switch_to_search_mode(self, assets: List[Dict]) -> tuple:
        """
        切换到自然语言搜索模式（模式 C）
        
        Args:
            assets: 搜索结果资产列表（最多6张）
            
        Returns:
            所有组件的更新
        """
        if not self.state_machine:
            return self._no_change()
        
        self.logger.info(f"切换到自然语言搜索模式: 共 {len(assets)} 张图片")
        
        # 使用状态机切换模式
        # 注意：assets 会在 _download_and_update_thumbnails 中处理
        # 这里只是切换模式，实际的 Gallery 更新会在下载完成后进行
        return self.state_machine.enter_search_mode(assets)
    
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
        if self.state_machine and self.state_machine.get_current_mode() == DisplayMode.SLIDESHOW:
            self.logger.info("[事件驱动] 收到WebSocket消息，将在定时器中切换到聊天模式")
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
        if self.state_machine and self.state_machine.get_current_mode() == DisplayMode.SLIDESHOW:
            self.logger.info("[事件驱动] 收到WebSocket消息，将在定时器中切换到聊天模式")
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
            
            # 如果当前在搜索模式，检查是否在保护期内
            if self.state_machine:
                current_mode = self.state_machine.get_current_mode()
                if current_mode == DisplayMode.SEARCH:
                    # 检查是否在保护期内
                    if self.chat_service.is_search_mode_protected():
                        # 在保护期内，完全忽略人物识别，保持搜索模式
                        # 注意：不更新人物信息，不更新 kiosk_url，不触发任何 iframe 相关操作
                        # iframe 在 _get_search_mode_updates 中会始终返回 visible=False
                        self.logger.info(
                            f"搜索模式保护期内，忽略人物识别 {person_name}，保持搜索模式（不更新 iframe）"
                        )
                        # 不调用 update_person_info，避免影响保护期结束后的逻辑
                        return  # 直接返回，不处理
                    else:
                        # 保护期已过，识别到新人物，切换到聊天模式
                        # 这是退出搜索模式的唯一条件（除了空闲超时）
                        self.logger.info(
                            f"保护期已过，识别到新人物 {person_name}，从搜索模式切换到聊天模式: {kiosk_url}"
                        )
                        # 先更新人物信息，然后切换模式
                        self.chat_service.update_person_info(
                            person_name=person_name,
                            person_id=person_id,
                            kiosk_url=kiosk_url
                        )
                        # 使用状态机切换模式（会显示 iframe）
                        self.state_machine.enter_chat_mode(kiosk_url)
                        return  # 已处理，直接返回
                else:
                    # 不在搜索模式（聊天模式或全屏轮播模式）
                    # 更新人物信息
                    self.chat_service.update_person_info(
                        person_name=person_name,
                        person_id=person_id,
                        kiosk_url=kiosk_url
                    )
                    # 更新 iframe URL（聊天模式或全屏轮播模式）
                    # 注意：这里不能直接更新，需要通过定时器更新
                    # 先保存到服务中，定时器会读取并更新
                    self.logger.info(f"收到 Kiosk URL，将在下次更新时刷新 iframe: {kiosk_url}")
            else:
                # 状态机未初始化，只更新人物信息
                self.chat_service.update_person_info(
                    person_name=person_name,
                    person_id=person_id,
                    kiosk_url=kiosk_url
                )
        
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
                # 自然语言搜索：立即切换到搜索模式，并更新 UI 组件（隐藏 iframe，显示 gallery）
                self.logger.info(f"收到自然语言搜索请求，立即切换到搜索模式: query={query}")
                # 使用状态机切换模式，并立即触发 UI 更新
                if self.state_machine:
                    # 先清除所有缓存，确保强制更新
                    self.state_machine._last_iframe_url = None
                    self.state_machine._last_search_mode_update = None
                    # 切换模式，获取完整的更新元组
                    switch_result = self.state_machine.enter_search_mode([])  # 先切换模式，assets 会在下载完成后更新
                    # 保存待应用的模式切换结果，让定时器立即应用
                    self._pending_mode_switch_result = switch_result
                    # 同时设置标志，让定时器立即触发 iframe 更新
                    if not hasattr(self, '_need_immediate_iframe_update'):
                        self._need_immediate_iframe_update = False
                    self._need_immediate_iframe_update = True
                    self.logger.info("[模式切换] 已设置待应用的模式切换结果，将在下次定时器调用时应用")
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
