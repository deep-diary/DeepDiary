# gui_voice_handler.py
# GUI控制语音处理器，专门处理界面相关的语音指令

from typing import Dict, Any, List
from .base_voice_handler import BaseVoiceHandler

class GuiVoiceHandler(BaseVoiceHandler):
    """GUI控制语音处理器"""
    
    def _register_command_handlers(self):
        # GUI控制命令
        self.supported_commands.extend([
            'gui_switch_page', 'gui_show_device', 'gui_hide_device',
            'gui_maximize', 'gui_minimize', 'gui_fullscreen',
            'gui_set_theme', 'gui_refresh', 'gui_close'
        ])
        
        # 注册命令处理器
        self.command_handlers.update({
            'gui_switch_page': self._handle_gui_switch_page,
            'gui_show_device': self._handle_gui_show_device,
            'gui_hide_device': self._handle_gui_hide_device,
            'gui_maximize': self._handle_gui_maximize,
            'gui_minimize': self._handle_gui_minimize,
            'gui_fullscreen': self._handle_gui_fullscreen,
            'gui_set_theme': self._handle_gui_set_theme,
            'gui_refresh': self._handle_gui_refresh,
            'gui_close': self._handle_gui_close,
        })
        
    def _handle_gui_switch_page(self, params: List[Dict[str, Any]]) -> bool:
        """处理页面切换命令"""
        page_name = "home"
        for param in params:
            if param.get('name') == 'page':
                page_name = param.get('value', 'home')
                
        self.logger.info(f"GuiVoiceHandler: 切换到页面: {page_name}")
        # TODO: 实现页面切换逻辑
        return True
        
    def _handle_gui_show_device(self, params: List[Dict[str, Any]]) -> bool:
        """处理显示设备命令"""
        device_name = "all"
        for param in params:
            if param.get('name') == 'device':
                device_name = param.get('value', 'all')
                
        self.logger.info(f"GuiVoiceHandler: 显示设备: {device_name}")
        return True
        
    def _handle_gui_hide_device(self, params: List[Dict[str, Any]]) -> bool:
        """处理隐藏设备命令"""
        device_name = "all"
        for param in params:
            if param.get('name') == 'device':
                device_name = param.get('value', 'all')
                
        self.logger.info(f"GuiVoiceHandler: 隐藏设备: {device_name}")
        return True
        
    def _handle_gui_maximize(self, params: List[Dict[str, Any]]) -> bool:
        """处理窗口最大化命令"""
        self.logger.info("GuiVoiceHandler: 窗口最大化")
        return True
        
    def _handle_gui_minimize(self, params: List[Dict[str, Any]]) -> bool:
        """处理窗口最小化命令"""
        self.logger.info("GuiVoiceHandler: 窗口最小化")
        return True
        
    def _handle_gui_fullscreen(self, params: List[Dict[str, Any]]) -> bool:
        """处理全屏命令"""
        self.logger.info("GuiVoiceHandler: 切换全屏")
        return True
        
    def _handle_gui_set_theme(self, params: List[Dict[str, Any]]) -> bool:
        """处理主题设置命令"""
        theme = "light"
        for param in params:
            if param.get('name') == 'theme':
                theme = param.get('value', 'light')
                
        self.logger.info(f"GuiVoiceHandler: 设置主题: {theme}")
        return True
        
    def _handle_gui_refresh(self, params: List[Dict[str, Any]]) -> bool:
        """处理界面刷新命令"""
        self.logger.info("GuiVoiceHandler: 刷新界面")
        return True
        
    def _handle_gui_close(self, params: List[Dict[str, Any]]) -> bool:
        """处理关闭命令"""
        self.logger.info("GuiVoiceHandler: 关闭应用")
        return True
