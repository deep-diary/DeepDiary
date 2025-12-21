#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kiosk Iframe Component - Immich Kiosk iframe 组件
使用 iframe 嵌入 Immich Kiosk 应用，实现照片轮播展示

作者: DeepDiary Team
日期: 2025-01-27
"""

import gradio as gr
from typing import Optional
import logging


class KioskIframe:
    """
    Immich Kiosk iframe 组件类
    
    职责：
    - 构建照片展示 UI（iframe 嵌入 Immich Kiosk）
    - 管理 iframe URL 的更新
    """
    
    def __init__(self, logger: logging.Logger, kiosk_base_url: str = "https://demo.immichkiosk.app"):
        """
        初始化 Kiosk iframe 组件
        
        Args:
            logger: 日志记录器
            kiosk_base_url: Immich Kiosk 基础 URL
        """
        self.logger = logger
        self.kiosk_base_url = kiosk_base_url.rstrip('/')
        self.html_component: Optional[gr.HTML] = None
    
    def build(self, height: int = 1080) -> gr.HTML:
        """
        构建照片展示 UI 组件
        
        Args:
            height: iframe 高度（像素），默认 1080px
        
        Returns:
            Gradio HTML 组件（包含 iframe）
        """
        # 初始 HTML（使用默认 Kiosk URL，不带人物参数）
        initial_html = self._build_iframe_html(None, height=height)
        
        self.logger.info(f"[KioskIframe] 构建iframe组件，kiosk_base_url={self.kiosk_base_url}, height={height}px")
        self.logger.info(f"[KioskIframe] 初始HTML长度: {len(initial_html)} 字符")
        
        # 注意：Gradio 5.49.0 可能不支持 apply_default_css 和 css_template
        # 使用内联样式确保样式生效，并通过全局CSS补充
        self.html_component = gr.HTML(
            value=initial_html,
            visible=True,
            elem_classes=["kiosk-iframe-component"]  # 添加类名，便于全局CSS选择
        )
        
        return self.html_component
    
    def _build_iframe_html(self, person_id: Optional[str], height: int = 1080) -> str:
        """
        构建 iframe HTML 内容
        
        Args:
            person_id: 人物 ID（可选）
            height: iframe 高度（像素）
            
        Returns:
            HTML 字符串
        """
        if person_id:
            # 根据 Immich Kiosk 文档，使用 person 参数
            kiosk_url = f"{self.kiosk_base_url}?person={person_id}"
        else:
            # 如果没有人物 ID，显示默认页面（所有照片）
            kiosk_url = self.kiosk_base_url
        
        # 使用固定高度，内联样式确保生效
        # 根据高度判断是聊天模式（800px）还是全屏模式（1080px）
        # 聊天模式使用 relative 定位，全屏模式使用 absolute 定位
        position_style = "absolute" if height >= 1080 else "relative"
        
        # 外层容器：红色背景（调试用）
        # 内层容器：绿色背景（调试用）
        # iframe：蓝色背景（调试用）
        html_content = f"""
        <div id="kiosk-container" style="position: {position_style}; top: 0; left: 0; width: 100%; height: {height}px; margin: 0; padding: 0; overflow: hidden; background: #ff0000 !important; z-index: 1;">
            <div id="kiosk-inner" style="position: relative; width: 100%; height: 100%; margin: 0; padding: 0; background: #00ff00 !important;">
                <iframe 
                    id="kiosk-iframe"
                    src="{kiosk_url}" 
                    width="100%" 
                    height="100%"
                    frameborder="0"
                    style="border: none !important; margin: 0 !important; padding: 0 !important; display: block !important; width: 100% !important; height: 100% !important; background: #0000ff !important;"
                    allowfullscreen
                ></iframe>
            </div>
        </div>
        """
        
        # 记录HTML内容长度和URL（用于调试）
        self.logger.info(f"[KioskIframe._build_iframe_html] 构建iframe HTML: URL={kiosk_url}, height={height}px, HTML长度={len(html_content)}字符")
        
        return html_content
    
    def update_person(self, person_id: Optional[str], height: int = 1080) -> gr.HTML:
        """
        更新显示的人物
        
        Args:
            person_id: 人物 ID
            height: iframe 高度（像素）
            
        Returns:
            Gradio HTML 更新对象
        """
        if person_id:
            self.logger.info(f"[KioskIframe] 更新照片展示: person_id={person_id}, height={height}px")
        else:
            self.logger.info(f"[KioskIframe] 清除照片展示人物，height={height}px")
        
        html_content = self._build_iframe_html(person_id, height=height)
        return gr.update(value=html_content)

