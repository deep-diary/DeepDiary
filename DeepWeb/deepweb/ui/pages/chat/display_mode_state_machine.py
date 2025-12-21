#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Display Mode State Machine - 显示模式状态机
统一管理三种显示模式的切换逻辑

作者: DeepDiary Team
日期: 2025-01-27
"""

from enum import Enum
from typing import Optional, List, Dict, Any, Tuple
import logging
import gradio as gr


class DisplayMode(Enum):
    """显示模式枚举"""
    CHAT = "chat"           # 聊天模式：左侧聊天框，右侧 iframe 轮播人物照片
    SLIDESHOW = "slideshow" # 全屏轮播模式：全屏 iframe 轮播照片
    SEARCH = "search"        # 自然语言搜索模式：左侧聊天框，右侧 gallery 显示搜索结果


class DisplayModeStateMachine:
    """显示模式状态机
    
    职责：
    1. 管理模式切换逻辑
    2. 统一管理组件的显示/隐藏
    3. 管理定时器的启动/停止
    4. 管理 iframe 的创建/释放
    5. 处理进入和退出逻辑
    """
    
    def __init__(self, chat_page):
        """
        初始化状态机
        
        Args:
            chat_page: ChatPage 实例，用于访问组件和服务
        """
        self.chat_page = chat_page
        self.logger = chat_page.logger
        self.current_mode = DisplayMode.CHAT
        self.previous_mode = None
        
        # 缓存最后使用的 iframe URL，避免频繁更新导致闪烁
        self._last_iframe_url: Optional[str] = None
        self._last_search_mode_update: Optional[str] = None
        self._last_search_gallery_visible: bool = False
        
    def enter_chat_mode(self, kiosk_url: Optional[str] = None) -> Tuple:
        """
        进入聊天模式
        
        Args:
            kiosk_url: Kiosk URL（可选，如果提供则更新 iframe）
            
        Returns:
            所有组件的更新元组
        """
        if self.current_mode == DisplayMode.CHAT:
            # 已经在聊天模式，只更新 iframe（如果有新 URL）
            if kiosk_url:
                return self._update_chat_iframe(kiosk_url)
            return self._no_change()
        
        # 退出当前模式
        self._exit_current_mode()
        
        # 更新状态
        self.previous_mode = self.current_mode
        self.current_mode = DisplayMode.CHAT
        
        # 执行进入逻辑
        return self._enter_chat_mode_logic(kiosk_url)
    
    def enter_slideshow_mode(self, person_id: Optional[str] = None) -> Tuple:
        """
        进入全屏轮播模式
        
        Args:
            person_id: 人物 ID（可选）
            
        Returns:
            所有组件的更新元组
        """
        if self.current_mode == DisplayMode.SLIDESHOW:
            # 已经在全屏模式，只更新 iframe（如果有新 person_id）
            if person_id:
                return self._update_slideshow_iframe(person_id)
            return self._no_change()
        
        # 退出当前模式
        self._exit_current_mode()
        
        # 更新状态
        self.previous_mode = self.current_mode
        self.current_mode = DisplayMode.SLIDESHOW
        
        # 执行进入逻辑
        return self._enter_slideshow_mode_logic(person_id)
    
    def enter_search_mode(self, assets: Optional[List[Dict]] = None) -> Tuple:
        """
        进入搜索模式
        
        Args:
            assets: 搜索结果资产列表（可选）
            
        Returns:
            所有组件的更新元组
        """
        if self.current_mode == DisplayMode.SEARCH:
            # 已经在搜索模式，只更新 gallery（如果有新 assets）
            if assets:
                return self._update_search_gallery(assets)
            return self._no_change()
        
        # 退出当前模式
        self._exit_current_mode()
        
        # 更新状态
        self.previous_mode = self.current_mode
        self.current_mode = DisplayMode.SEARCH
        
        # 执行进入逻辑
        return self._enter_search_mode_logic(assets)
    
    def _exit_current_mode(self):
        """退出当前模式"""
        if self.current_mode == DisplayMode.CHAT:
            self._exit_chat_mode_logic()
        elif self.current_mode == DisplayMode.SLIDESHOW:
            self._exit_slideshow_mode_logic()
        elif self.current_mode == DisplayMode.SEARCH:
            self._exit_search_mode_logic()
    
    def _enter_chat_mode_logic(self, kiosk_url: Optional[str] = None) -> Tuple:
        """进入聊天模式的逻辑"""
        # 1. 重置空闲定时器
        self.chat_page.chat_service.update_message_time()
        
        # 2. 更新服务层模式
        self.chat_page.chat_service.set_current_mode("chat")
        self.chat_page.current_view = "chat"
        
        # 3. 更新 iframe URL（如果有）
        kiosk_iframe_update = gr.update()
        if kiosk_url:
            kiosk_iframe_update = self._update_chat_iframe(kiosk_url)[2]  # 获取 iframe 更新
        elif self._last_iframe_url:
            # 使用缓存的 URL
            kiosk_iframe_update = self._update_chat_iframe(self._last_iframe_url)[2]
        else:
            # 使用默认 URL
            default_url = self.chat_page.kiosk_base_url
            kiosk_iframe_update = self._update_chat_iframe(default_url)[2]
        
        # 4. 更新模式标记
        self._last_search_mode_update = "chat"
        
        self.logger.info(f"[状态机] 进入聊天模式")
        
        return (
            gr.update(visible=True),   # chat_view
            gr.update(visible=False),  # slideshow_view
            kiosk_iframe_update,        # chat_iframe (聊天模式 iframe，更新高度为500px，可见)
            gr.update(visible=False),  # slideshow_iframe (全屏模式 iframe，隐藏)
            gr.update(visible=True),   # search_gallery (与 iframe 同时显示)
            gr.update(active=True)     # timer - 启用聊天定时器
        )
    
    def _enter_slideshow_mode_logic(self, person_id: Optional[str] = None) -> Tuple:
        """进入全屏轮播模式的逻辑"""
        # 1. 更新服务层模式
        self.chat_page.chat_service.set_current_mode("slideshow")
        self.chat_page.current_view = "slideshow"
        
        # 2. 更新全屏 iframe（总是更新 value，确保 iframe 正确显示）
        # 使用最后保存的 person_id，如果没有则使用 None（显示所有照片）
        if person_id is None:
            person_info = self.chat_page.chat_service.get_last_person_info()
            person_id = person_info.get("person_id")
        
        # 使用全屏模式的 iframe 组件更新（高度1080px）
        # 注意：无论是否有 person_id，都要更新 value，确保 iframe 正确显示
        slideshow_iframe_update_base = self.chat_page.slideshow_iframe_component.update_person(person_id, height=1080)
        slideshow_iframe_update = gr.update(
            value=slideshow_iframe_update_base.get("value"),
            visible=True
        )
        
        # 3. 如果从 search 模式切换过来，确保 search_gallery 隐藏
        # 重置搜索模式相关标记
        self._last_search_mode_update = None
        self._last_search_gallery_visible = False
        
        self.logger.info(f"[状态机] 进入全屏轮播模式: person_id={person_id}, height=1080px")
        
        return (
            gr.update(visible=False),  # chat_view
            gr.update(visible=True),   # slideshow_view
            gr.update(visible=False),  # chat_iframe (聊天模式 iframe，隐藏)
            slideshow_iframe_update,    # slideshow_iframe (全屏模式 iframe，更新高度为1080px，确保 value 更新)
            gr.update(visible=False),  # search_gallery (从 search 模式切换时，必须隐藏)
            gr.update(active=False)     # timer - 禁用聊天定时器，避免闪烁
        )
    
    def _enter_search_mode_logic(self, assets: Optional[List[Dict]] = None) -> Tuple:
        """进入搜索模式的逻辑"""
        # 1. 重置搜索模式保护期
        self.chat_page.chat_service.set_current_mode("search", reset_protection=True)
        
        # 2. 更新模式标记
        self._last_search_mode_update = "search"
        
        # 3. 更新 search_gallery（如果有 assets）
        search_gallery_update = gr.update(visible=True)
        if assets:
            search_gallery_update = gr.update(
                value=assets,
                visible=True
            )
            self._last_search_gallery_visible = True
        else:
            # 确保可见性正确
            if not self._last_search_gallery_visible:
                search_gallery_update = gr.update(visible=True)
                self._last_search_gallery_visible = True
        
        # 4. iframe 和 gallery 同时显示（不再隐藏 iframe）
        kiosk_iframe_update = gr.update(visible=True)
        
        self.logger.info(f"[状态机] 进入搜索模式: 共 {len(assets) if assets else 0} 张图片")
        
        return (
            gr.update(visible=True),   # chat_view
            gr.update(visible=False),  # slideshow_view
            kiosk_iframe_update,       # chat_iframe (聊天模式 iframe，与 gallery 同时显示)
            gr.update(visible=False),  # slideshow_iframe (全屏模式 iframe，隐藏)
            search_gallery_update,     # search_gallery
            gr.update(active=True)     # timer - 保持启用聊天定时器（搜索模式需要实时更新）
        )
    
    def _exit_chat_mode_logic(self):
        """退出聊天模式的逻辑"""
        # 清理资源（如果需要）
        pass
    
    def _exit_slideshow_mode_logic(self):
        """退出全屏轮播模式的逻辑"""
        # 清理资源（如果需要）
        pass
    
    def _exit_search_mode_logic(self):
        """退出搜索模式的逻辑"""
        # 清理资源（如果需要）
        pass
    
    def get_ui_updates(self) -> Tuple:
        """
        获取当前模式的 UI 更新（用于定时更新）
        
        Returns:
            (chat_history, status_text, kiosk_iframe_update, search_gallery_update) 的更新
        """
        if self.current_mode == DisplayMode.CHAT:
            return self._get_chat_mode_updates()
        elif self.current_mode == DisplayMode.SLIDESHOW:
            return self._get_slideshow_mode_updates()
        elif self.current_mode == DisplayMode.SEARCH:
            return self._get_search_mode_updates()
    
    def _get_chat_mode_updates(self) -> Tuple:
        """获取聊天模式的 UI 更新"""
        kiosk_url = self.chat_page.chat_service.get_last_kiosk_url()
        # 如果没有保存的 URL，使用默认 URL（不带人物参数，轮播所有照片）
        if not kiosk_url:
            kiosk_url = self.chat_page.kiosk_base_url
        
        # 检查 URL 是否变化（避免频繁更新导致闪烁）
        if kiosk_url != self._last_iframe_url or self._last_search_mode_update != "chat":
            # 从 URL 中提取 person_id（如果有）
            person_id = None
            if "?person=" in kiosk_url:
                try:
                    person_id = kiosk_url.split("?person=")[1].split("&")[0]
                except:
                    pass
            
            # 使用 KioskIframe 组件更新（高度500px，聊天模式）
            kiosk_iframe_update_base = self.chat_page.chat_ui.kiosk_iframe_component.update_person(person_id, height=500)
            # 合并 visible 属性
            kiosk_iframe_update = gr.update(
                value=kiosk_iframe_update_base.get("value"),
                visible=True
            )
            self._last_iframe_url = kiosk_url
            self._last_search_mode_update = "chat"
            self._last_search_gallery_visible = False
        else:
            # URL 和模式都没变化，不更新 value（避免闪烁）
            kiosk_iframe_update = gr.update()
        
        # search_gallery 与 iframe 同时显示（不再隐藏）
        # 在聊天模式下，gallery 也显示（即使没有数据）
        search_gallery_update = gr.update(visible=True)
        
        return (
            self.chat_page.chat_service.get_chat_history(),
            self.chat_page.connection_status,
            kiosk_iframe_update,
            search_gallery_update
        )
    
    def _get_slideshow_mode_updates(self) -> Tuple:
        """获取全屏轮播模式的 UI 更新"""
        # 全屏模式下，完全不更新任何组件，减少闪烁
        self.logger.debug(f"[状态机] 当前为全屏轮播模式，不更新任何组件（避免刷新）")
        current_chat_history = self.chat_page.chat_service.get_chat_history()
        current_status = self.chat_page.connection_status
        return (
            current_chat_history,  # 返回当前值，不触发更新
            current_status,        # 返回当前值，不触发更新
            gr.update(),           # kiosk_iframe - 不更新（共用实例）
            gr.update()            # search_gallery - 不更新
        )
    
    def _get_search_mode_updates(self) -> Tuple:
        """获取搜索模式的 UI 更新
        
        重要：在搜索模式下，iframe 和 gallery 同时显示。
        """
        # 在搜索模式下，iframe 和 gallery 同时显示
        is_protected = self.chat_page.chat_service.is_search_mode_protected()
        
        # iframe 始终可见（与 gallery 同时显示）
        kiosk_iframe_update = gr.update(visible=True)
        
        # 更新 search_gallery（如果有待更新的数据）
        if hasattr(self.chat_page, '_pending_search_gallery') and self.chat_page._pending_search_gallery is not None:
            search_gallery_update = gr.update(
                value=self.chat_page._pending_search_gallery,
                visible=True
            )
            self.chat_page._pending_search_gallery = None  # 清除待更新数据
            self._last_search_gallery_visible = True
        else:
            # 没有新数据，但确保可见性正确（只在第一次切换时更新）
            if not hasattr(self, '_last_search_gallery_visible') or not self._last_search_gallery_visible:
                search_gallery_update = gr.update(visible=True)
                self._last_search_gallery_visible = True
            else:
                search_gallery_update = gr.update()  # 不更新，避免闪烁
        
        return (
            self.chat_page.chat_service.get_chat_history(),
            self.chat_page.connection_status,
            kiosk_iframe_update,
            search_gallery_update
        )
    
    def _update_chat_iframe(self, kiosk_url: str) -> Tuple:
        """更新聊天模式的 iframe"""
        # 从 URL 中提取 person_id（如果有）
        person_id = None
        if "?person=" in kiosk_url:
            try:
                person_id = kiosk_url.split("?person=")[1].split("&")[0]
            except:
                pass
        
        # 使用 KioskIframe 组件更新（高度500px，聊天模式）
        kiosk_iframe_update_base = self.chat_page.chat_ui.kiosk_iframe_component.update_person(person_id, height=500)
        # 合并 visible 属性
        kiosk_iframe_update = gr.update(
            value=kiosk_iframe_update_base.get("value"),
            visible=True
        )
        
        # 更新缓存的 URL
        self._last_iframe_url = kiosk_url
        
        return (
            gr.update(),  # chat_view - 不更新
            gr.update(),  # slideshow_view - 不更新
            kiosk_iframe_update,  # chat_iframe
            gr.update(),  # slideshow_iframe - 不更新
            gr.update(),  # search_gallery - 不更新
            gr.update()   # timer - 不更新
        )
    
    def _update_slideshow_iframe(self, person_id: Optional[str]) -> Tuple:
        """更新全屏模式的 iframe"""
        # 使用全屏模式的 iframe 组件更新（高度1080px）
        slideshow_iframe_update_base = self.chat_page.slideshow_iframe_component.update_person(person_id, height=1080)
        slideshow_iframe_update = gr.update(
            value=slideshow_iframe_update_base.get("value"),
            visible=True
        )
        
        return (
            gr.update(),  # chat_view - 不更新
            gr.update(),  # slideshow_view - 不更新
            gr.update(),  # chat_iframe - 不更新
            slideshow_iframe_update,  # slideshow_iframe
            gr.update(),  # search_gallery - 不更新
            gr.update()   # timer - 不更新
        )
    
    def _update_search_gallery(self, assets: List[Dict]) -> Tuple:
        """更新搜索模式的 gallery"""
        search_gallery_update = gr.update(
            value=assets,
            visible=True
        )
        self._last_search_gallery_visible = True
        
        return (
            gr.update(),  # chat_view - 不更新
            gr.update(),  # slideshow_view - 不更新
            gr.update(visible=False),  # chat_iframe - 确保隐藏
            gr.update(),  # slideshow_iframe - 不更新
            search_gallery_update,  # search_gallery
            gr.update()   # timer - 不更新
        )
    
    def _no_change(self) -> Tuple:
        """返回不改变的更新（避免刷新）"""
        return (
            gr.update(),  # chat_view - 不更新
            gr.update(),  # slideshow_view - 不更新
            gr.update(),  # chat_iframe - 不更新
            gr.update(),  # slideshow_iframe - 不更新
            gr.update(),  # search_gallery - 不更新
            gr.update()   # timer - 不更新
        )
    
    def get_current_mode(self) -> DisplayMode:
        """获取当前模式"""
        return self.current_mode
    
    def get_current_mode_str(self) -> str:
        """获取当前模式字符串"""
        return self.current_mode.value

