#!/usr/bin/env python3
"""
文本转录管理器

负责处理文本转语音功能，支持随时发送文本并返回对应的语音
"""

import logging
from typing import Optional, Dict, Any, Callable
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)

class TranscriptManager(QObject):
    """文本转录管理器"""
    
    # 信号定义
    transcript_response_received = Signal(str)  # 转录响应文本
    transcript_error = Signal(str)              # 错误信息
    transcript_status_changed = Signal(str)     # 状态变化
    
    def __init__(self, conversation_instance=None, parent=None):
        """
        初始化转录管理器
        
        Args:
            conversation_instance: 对话实例
            parent: QObject父对象
        """
        super().__init__(parent)
        self.conversation_instance = conversation_instance
        self.is_active = False
        self.current_text = ""
        
        logger.info("TranscriptManager: 初始化完成")
    
    def set_conversation_instance(self, conversation_instance):
        """
        设置对话实例
        
        Args:
            conversation_instance: 对话实例
        """
        self.conversation_instance = conversation_instance
        logger.info("TranscriptManager: 对话实例已设置")
    
    def start_transcript(self, text: str) -> bool:
        """
        开始文本转录
        
        Args:
            text: 要转录的文本
            
        Returns:
            bool: 是否成功启动
        """
        try:
            if not self.conversation_instance:
                raise RuntimeError("对话实例未设置")
            
            self.current_text = text
            self.is_active = True
            
            # 发送转录请求
            self.conversation_instance.conversation.request_to_respond("transcript", text)
            
            self.transcript_status_changed.emit("转录已启动")
            logger.info(f"转录已启动，文本: {text}")
            return True
            
        except Exception as e:
            error_msg = f"启动转录失败: {e}"
            logger.error(error_msg)
            self.transcript_error.emit(error_msg)
            return False
    
    def send_transcript_text(self, text: str) -> bool:
        """
        发送转录文本
        
        Args:
            text: 要转录的文本
            
        Returns:
            bool: 是否成功发送
        """
        try:
            if not self.conversation_instance:
                raise RuntimeError("对话实例未设置")
            
            self.current_text = text
            
            # 发送转录请求
            self.conversation_instance.conversation.request_to_respond("transcript", text)
            
            logger.info(f"转录文本已发送: {text}")
            return True
            
        except Exception as e:
            error_msg = f"发送转录文本失败: {e}"
            logger.error(error_msg)
            self.transcript_error.emit(error_msg)
            return False
    
    def stop_transcript(self) -> bool:
        """
        停止转录功能
        
        Returns:
            bool: 是否成功停止
        """
        try:
            if not self.is_active:
                logger.info("转录未在运行")
                return True
            
            self.is_active = False
            self.current_text = ""
            
            self.transcript_status_changed.emit("转录已停止")
            logger.info("转录已停止")
            return True
            
        except Exception as e:
            error_msg = f"停止转录失败: {e}"
            logger.error(error_msg)
            self.transcript_error.emit(error_msg)
            return False
    
    def get_transcript_status(self) -> Dict[str, Any]:
        """
        获取转录状态
        
        Returns:
            Dict: 状态信息
        """
        status = {
            'is_active': self.is_active,
            'current_text': self.current_text,
            'has_conversation_instance': self.conversation_instance is not None
        }
        
        return status
    
    def cleanup(self):
        """清理资源"""
        logger.info("TranscriptManager: 开始清理...")
        try:
            self.stop_transcript()
        except Exception as e:
            logger.warning(f"清理转录时出错: {e}")
        logger.info("TranscriptManager: 清理完成")
