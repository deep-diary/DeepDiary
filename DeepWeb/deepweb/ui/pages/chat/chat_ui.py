#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chat UI - 聊天界面组件
负责构建和管理聊天界面的 UI 组件

作者: DeepDiary Team
日期: 2025-01-27
"""

import gradio as gr
from typing import List, Dict, Any, Optional, Tuple
import logging
from deepweb.ui.pages.chat.kiosk_iframe import KioskIframe


class ChatUI:
    """
    聊天界面组件类
    
    职责：
    - 构建 Gradio UI 组件
    - 处理用户交互事件
    - 更新界面显示
    """
    
    def __init__(self, logger: logging.Logger):
        """
        初始化聊天 UI 组件
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
        
        # UI 组件引用（在 build 方法中初始化）
        self.device_id_input: Optional[gr.Textbox] = None
        self.client_id_input: Optional[gr.Textbox] = None
        self.websocket_url_input: Optional[gr.Textbox] = None
        self.connect_btn: Optional[gr.Button] = None
        self.disconnect_btn: Optional[gr.Button] = None
        self.status_text: Optional[gr.Textbox] = None
        self.chatbot: Optional[gr.Chatbot] = None
        self.msg_input: Optional[gr.Textbox] = None
        self.send_btn: Optional[gr.Button] = None
        self.clear_btn: Optional[gr.Button] = None
        self.kiosk_iframe_component: Optional[KioskIframe] = None  # Kiosk iframe 组件实例
        self.kiosk_iframe: Optional[gr.HTML] = None  # Immich Kiosk iframe（用于聊天模式）
        self.search_gallery: Optional[gr.Gallery] = None  # 搜索结果 Gallery（用于自然语言搜索模式）
        self.timer: Optional[gr.Timer] = None
    
    def build(
        self,
        device_id: str = "connect_websocket",
        client_id: str = "gradio-client",
        websocket_url: str = "ws://localhost:8000/xiaozhi/v1/",
        chat_history: List[Dict[str, str]] = None,
        memory_markdown: str = "# 记忆显示区\n\n待开发功能...",
        kiosk_base_url: str = "http://192.168.31.25:3000"
    ) -> gr.Column:
        """
        构建 Gradio UI 界面
        
        Args:
            device_id: 默认设备ID
            client_id: 默认客户端ID
            websocket_url: 默认 WebSocket URL
            chat_history: 初始聊天历史
            memory_markdown: 初始记忆内容
            
        Returns:
            Gradio Column 组件
        """
        if chat_history is None:
            chat_history = []
        
        with gr.Column(elem_classes=["chat-interface"]) as chat_interface:

            
            # 连接配置区域
            with gr.Accordion("连接配置", open=False):
                with gr.Row():
                    self.device_id_input = gr.Textbox(
                        label="设备ID (Device ID)",
                        value=device_id,
                        placeholder="设备ID",
                        interactive=True
                    )
                    self.client_id_input = gr.Textbox(
                        label="客户端ID (Client ID)",
                        value=client_id,
                        placeholder="gradio-client",
                        interactive=True
                    )
                    self.websocket_url_input = gr.Textbox(
                        label="WebSocket URL",
                        value=websocket_url,
                        placeholder="ws://localhost:8000/xiaozhi/v1/",
                        interactive=True
                    )
                
                with gr.Row():
                    self.connect_btn = gr.Button("🔗 连接", variant="primary")
                    self.disconnect_btn = gr.Button("❌ 断开连接", variant="secondary")
                    self.status_text = gr.Textbox(
                        label="连接状态",
                        value="未连接",
                        interactive=False
                    )
            
            # 主要聊天区域 - 左右布局（1:1比例）
            with gr.Row():
                # 左侧：聊天界面
                with gr.Column(scale=1):
                    gr.Markdown("### 💬 聊天记录")
                    
                    # 聊天历史显示
                    self.chatbot = gr.Chatbot(
                        label="对话历史",
                        value=chat_history,
                        height=800,
                        show_label=False,
                        bubble_full_width=False,
                        type="messages",
                        avatar_images=(None, "🤖")
                    )
                    
                    # 消息输入区域
                    with gr.Row():
                        self.msg_input = gr.Textbox(
                            # label="输入消息",
                            placeholder="输入消息与深记对话...",
                            scale=4,
                            interactive=True
                        )
                        self.send_btn = gr.Button("发送", scale=1, variant="primary")
                    
                    # 清除聊天记录按钮（与发送按钮同一行）
                    with gr.Row():
                        self.clear_btn = gr.Button("🗑️ 清除聊天记录", size="sm")
                
                # 右侧：显示区域（根据模式切换显示内容）
                with gr.Column(scale=1) as right_panel:
                    # 模式 A: Immich Kiosk iframe（默认显示，用于聊天模式）
                    # 使用 KioskIframe 组件，高度 800px（聊天模式）
                    self.kiosk_iframe_component = KioskIframe(self.logger, kiosk_base_url=kiosk_base_url)
                    self.kiosk_iframe = self.kiosk_iframe_component.build(height=800)
                    
                    # 模式 C: 搜索结果 Gallery（默认隐藏，用于自然语言搜索模式）
                    self.search_gallery = gr.Gallery(
                        label="搜索结果",
                        show_label=False,
                        height=800,
                        columns=3,
                        rows=2,
                        value=[],
                        visible=False,
                        allow_preview=True
                    )
            
            # 定时更新聊天记录和记忆显示（每秒更新一次）
            self.timer = gr.Timer(1.0)
        
        return chat_interface
    
    def bind_events(
        self,
        on_connect,
        on_disconnect,
        on_send_message,
        on_clear_chat,
        on_update_ui,
        on_refresh_memory=None,  # 保留参数以保持兼容性，但不再使用
        on_clear_memory=None     # 保留参数以保持兼容性，但不再使用
    ):
        """
        绑定事件处理函数
        
        Args:
            on_connect: 连接按钮点击处理函数
            on_disconnect: 断开连接按钮点击处理函数
            on_send_message: 发送消息处理函数
            on_clear_chat: 清除聊天记录处理函数
            on_update_ui: UI 更新处理函数（定时调用）
            on_refresh_memory: 刷新记忆处理函数（已废弃，不再使用）
            on_clear_memory: 清除记忆处理函数（已废弃，不再使用）
        """
        # 连接配置相关
        self.connect_btn.click(
            fn=on_connect,
            inputs=[self.device_id_input, self.client_id_input, self.websocket_url_input],
            outputs=[self.status_text]
        ).then(
            fn=lambda: gr.update(interactive=False),
            inputs=[],
            outputs=[self.connect_btn]
        ).then(
            fn=lambda: gr.update(interactive=True),
            inputs=[],
            outputs=[self.disconnect_btn]
        )
        
        self.disconnect_btn.click(
            fn=on_disconnect,
            inputs=[],
            outputs=[self.status_text]
        ).then(
            fn=lambda: gr.update(interactive=True),
            inputs=[],
            outputs=[self.connect_btn]
        ).then(
            fn=lambda: gr.update(interactive=False),
            inputs=[],
            outputs=[self.disconnect_btn]
        )
        
        # 消息发送相关
        self.send_btn.click(
            fn=on_send_message,
            inputs=[self.msg_input],
            outputs=[]
        ).then(
            fn=lambda: "",
            inputs=[],
            outputs=[self.msg_input]
        )
        
        self.msg_input.submit(
            fn=on_send_message,
            inputs=[self.msg_input],
            outputs=[]
        ).then(
            fn=lambda: "",
            inputs=[],
            outputs=[self.msg_input]
        )
        
        # 聊天记录操作
        self.clear_btn.click(
            fn=on_clear_chat,
            inputs=[],
            outputs=[self.chatbot]
        )
        
        # 记忆操作（按钮已隐藏，不绑定事件）
        # 由于 memory_display 已删除，这些按钮的事件绑定已移除
        # self.refresh_memory_btn.click(
        #     fn=on_refresh_memory,
        #     inputs=[],
        #     outputs=[self.memory_display]
        # )
        # 
        # self.clear_memory_btn.click(
        #     fn=on_clear_memory,
        #     inputs=[],
        #     outputs=[self.memory_display]
        # )
        
        # 定时更新（包含所有需要更新的组件）
        self.timer.tick(
            fn=on_update_ui,
            inputs=[],
            outputs=[self.chatbot, self.status_text, self.kiosk_iframe, self.search_gallery]
        )

