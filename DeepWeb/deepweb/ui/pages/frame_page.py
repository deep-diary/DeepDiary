#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frame Page - 照片展示页面
使用 iframe 嵌入 Immich Kiosk 应用，实现照片轮播展示

作者: DeepDiary Team
日期: 2025-01-27
"""

import gradio as gr
from typing import Optional
import logging


class FramePage:
    """
    照片展示页面类
    
    职责：
    - 构建照片展示 UI（iframe 嵌入 Immich Kiosk）
    - 管理 iframe URL 的更新
    """
    
    def __init__(self, logger: logging.Logger, kiosk_base_url: str = "https://demo.immichkiosk.app"):
        """
        初始化照片展示页面
        
        Args:
            logger: 日志记录器
            kiosk_base_url: Immich Kiosk 基础 URL
        """
        self.logger = logger
        self.kiosk_base_url = kiosk_base_url.rstrip('/')
        self.html_component: Optional[gr.HTML] = None
    
    def build(self) -> gr.HTML:
        """
        构建照片展示页面 UI
        
        Returns:
            Gradio HTML 组件（包含 iframe）
        """
        # 初始 HTML（空 iframe，等待更新）
        initial_html = self._build_iframe_html(None)
        
        self.html_component = gr.HTML(
            value=initial_html,
            visible=True
        )
        
        return self.html_component
    
    def _build_iframe_html(self, person_id: Optional[str]) -> str:
        """
        构建 iframe HTML 内容
        
        Args:
            person_id: 人物 ID（可选）
            
        Returns:
            HTML 字符串
        """
        if person_id:
            # 根据 Immich Kiosk 文档，使用 people 参数
            kiosk_url = f"{self.kiosk_base_url}?people={person_id}"
        else:
            # 如果没有人物 ID，显示默认页面
            kiosk_url = self.kiosk_base_url
        
        html_content = f"""
        <div style="width: 100%; height: 100vh; margin: 0; padding: 0; overflow: hidden;">
            <iframe 
                src="{kiosk_url}" 
                width="100%" 
                height="100vh" 
                frameborder="0"
                style="border: none; margin: 0; padding: 0; display: block;"
                allowfullscreen
            ></iframe>
        </div>
        """
        
        return html_content
    
    def update_person(self, person_id: Optional[str]) -> gr.HTML:
        """
        更新显示的人物
        
        Args:
            person_id: 人物 ID
            
        Returns:
            Gradio HTML 更新对象
        """
        if person_id:
            self.logger.info(f"更新照片展示页面: person_id={person_id}")
        else:
            self.logger.info("清除照片展示页面人物")
        
        html_content = self._build_iframe_html(person_id)
        return gr.update(value=html_content)

