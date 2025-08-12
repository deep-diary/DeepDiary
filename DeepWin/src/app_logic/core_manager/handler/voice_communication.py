# src/app_logic/core_manager/handler/voice_communication_handler.py
# 语音通信处理器，负责处理语音服务发出的信号连接和事件处理

from PySide6.QtCore import Slot
from src.app_logic.core_manager.base_handler import BaseHandler
from .voice_handlers import (
    HardwareVoiceHandler, GuiVoiceHandler, MemoryVoiceHandler,
    SystemVoiceHandler, AIVoiceHandler
)
import json
import logging

class VoiceCommunicationHandler(BaseHandler):
    """
    语音通信处理器 - 重构后的轻量级路由器
    负责：
    1. 接收语音命令信号
    2. 路由命令到专门的处理器
    3. 处理语音相关的状态更新
    4. 作为语音服务与其他模块的桥梁
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.voice_handlers = {}
        
    def _validate_dependencies(self):
        """验证必需的依赖项是否已设置"""
        # 检查基础依赖项
        if not self.logger:
            raise ValueError("缺少必需的依赖项: logger")
        if not self.device_logic_manager:
            raise ValueError("缺少必需的依赖项: device_logic_manager")
        if not self.config_manager:
            raise ValueError("缺少必需的依赖项: config_manager")
        
        # coordinator_handler是可选的，不强制要求
        if not self.coordinator_handler:
            self.logger.warning("VoiceCommunicationHandler: coordinator_handler未设置，某些功能可能受限")
        
        # voice_manager是可选的，不强制要求
        if not self.voice_manager:
            self.logger.warning("VoiceCommunicationHandler: voice_manager未设置，语音功能将不可用")
        
    def _connect_signals(self):
        """连接语音通信层相关的信号"""
        self.logger.debug("VoiceCommunicationHandler: 连接语音通信层信号...")
        
        # 连接VoiceManager的语音命令信号（如果可用）
        if self.voice_manager:
            self.voice_manager.voice_command_received.connect(self._on_voice_command_received)
            self.logger.info("VoiceCommunicationHandler: 已连接VoiceManager的voice_command_received信号")
        else:
            self.logger.warning("VoiceCommunicationHandler: VoiceManager不可用，跳过信号连接")
        
        self.logger.debug("VoiceCommunicationHandler: 语音通信层信号连接完成")
        
    def _initialize_voice_handlers(self):
        """初始化专门的语音指令处理器"""
        self.logger.info("VoiceCommunicationHandler: 初始化语音指令处理器...")
        
        try:
            # 创建并初始化各种专门的处理器
            self.voice_handlers['hardware'] = HardwareVoiceHandler(parent=self)
            self.voice_handlers['gui'] = GuiVoiceHandler(parent=self)
            self.voice_handlers['memory'] = MemoryVoiceHandler(parent=self)
            self.voice_handlers['system'] = SystemVoiceHandler(parent=self)
            self.voice_handlers['ai'] = AIVoiceHandler(parent=self)
            
            # 设置依赖项并初始化
            for handler_name, handler in self.voice_handlers.items():
                try:
                    # 如果有coordinator_handler，使用它；否则使用self
                    if self.coordinator_handler:
                        handler.set_coordinator_dependencies(self.coordinator_handler)
                    else:
                        # 如果没有coordinator_handler，直接设置基本依赖
                        handler.logger = self.logger
                        handler.config_manager = self.config_manager
                        handler.device_logic_manager = self.device_logic_manager
                        handler.voice_manager = self.voice_manager
                    
                    handler.initialize()
                    self.logger.info(f"VoiceCommunicationHandler: 已初始化 {handler_name} 处理器")
                except Exception as e:
                    self.logger.error(f"VoiceCommunicationHandler: 初始化 {handler_name} 处理器失败: {e}")
                    # 继续初始化其他处理器，不中断整个过程
                    continue
                
            self.logger.info(f"VoiceCommunicationHandler: 成功初始化 {len(self.voice_handlers)} 个语音指令处理器")
            
        except Exception as e:
            self.logger.error(f"VoiceCommunicationHandler: 初始化语音指令处理器失败: {e}")
            raise
            
    def initialize(self):
        """初始化处理器"""
        super().initialize()
        self._initialize_voice_handlers()
        
    @Slot(dict)
    def _on_voice_command_received(self, command_data: dict):
        """处理语音命令接收事件"""
        self.logger.info(f"VoiceCommunicationHandler: 收到语音命令: {command_data}")
        
        try:
            # 记录命令到协调器状态（如果可用）
            if self.coordinator_handler:
                self.coordinator_handler.app_status_message.emit(f"收到语音命令: {command_data.get('name', 'unknown')}")
            
            # 路由命令到专门的处理器
            self._route_command_to_handler(command_data)
            
        except Exception as e:
            error_msg = f"处理语音命令时发生错误: {str(e)}"
            self.logger.error(error_msg)
            # 直接记录错误，不需要发射信号
            if self.coordinator_handler:
                self.coordinator_handler.app_status_message.emit(f"语音错误: {error_msg}")
            
    def _route_command_to_handler(self, command_data: dict):
        """
        将语音命令路由到专门的处理器
        command: {'name': 'motor_set_pos', 'params': [{'name': 'pos', 'value': '1', 'normValue': '1'}]}
        """
        try:
            command_name = command_data.get('name', '')
            params = command_data.get('params', [])
            
            self.logger.info(f"VoiceCommunicationHandler: 路由命令 - 名称: {command_name}, 参数: {params}")
            
            # 根据命令前缀确定处理器类型
            handler_type = self._get_handler_type_by_command(command_name)
            
            if handler_type and handler_type in self.voice_handlers:
                # 路由到专门的处理器
                handler = self.voice_handlers[handler_type]
                if handler.can_handle_command(command_name):
                    success = handler.handle_command(command_name, params)
                    if success:
                        self.logger.info(f"VoiceCommunicationHandler: 命令 {command_name} 已成功路由到 {handler_type} 处理器")
                    else:
                        self.logger.warning(f"VoiceCommunicationHandler: 命令 {command_name} 在 {handler_type} 处理器中处理失败")
                else:
                    self.logger.warning(f"VoiceCommunicationHandler: {handler_type} 处理器不支持命令 {command_name}")
            else:
                # 未知命令类型
                self.logger.warning(f"VoiceCommunicationHandler: 未知命令类型: {command_name}")
                if self.coordinator_handler:
                    self.coordinator_handler.app_status_message.emit(f"未知语音命令: {command_name}")
                
        except Exception as e:
            error_msg = f"路由命令时发生错误: {str(e)}"
            self.logger.error(error_msg)
            if self.coordinator_handler:
                self.coordinator_handler.app_status_message.emit(f"语音命令路由错误: {error_msg}")
            
    def _get_handler_type_by_command(self, command_name: str) -> str:
        """根据命令名称确定处理器类型"""
        if command_name.startswith(('motor_', 'arm_', 'toy_')):
            return 'hardware'
        elif command_name.startswith('gui_'):
            return 'gui'
        elif command_name.startswith('memory_'):
            return 'memory'
        elif command_name.startswith('system_'):
            return 'system'
        elif command_name.startswith('ai_'):
            return 'ai'
        else:
            return None
            
            
    def get_handler_info(self) -> dict:
        """获取所有处理器的信息"""
        handler_info = {}
        for handler_type, handler in self.voice_handlers.items():
            handler_info[handler_type] = handler.get_handler_info()
        return handler_info
        
    def cleanup(self):
        """清理资源"""
        for handler_name, handler in self.voice_handlers.items():
            try:
                handler.cleanup()
                self.logger.info(f"VoiceCommunicationHandler: 已清理 {handler_name} 处理器")
            except Exception as e:
                self.logger.error(f"VoiceCommunicationHandler: 清理 {handler_name} 处理器失败: {e}")
                
