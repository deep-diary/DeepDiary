#!/usr/bin/env python3
"""
VQA功能管理器

负责处理视觉问答功能，支持文本提示和图片路径输入
参考官方示例run_vqa.py实现
"""

import os
import base64
from typing import Optional, Dict, Any, Callable
from PySide6.QtCore import QObject, Signal
from dashscope.multimodal.multimodal_request_params import (
    Upstream, Downstream, ClientInfo, RequestParameters, 
    Device, RequestToRespondParameters,BizParams
)
from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager

class VQAManager(QObject):
    """VQA功能管理器"""
    
    # 信号定义
    vqa_response_received = Signal(str)  # VQA响应文本
    vqa_error = Signal(str)              # 错误信息
    vqa_status_changed = Signal(str)     # 状态变化
    
    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, conversation_instance=None, parent=None):
        """
        初始化VQA管理器
        
        Args:
            log_manager: 日志管理器实例
            config_manager: 配置管理器实例
            conversation_instance: 对话实例
            parent: QObject父对象
        """
        super().__init__(parent)
        self.log_manager = log_manager
        self.config_manager = config_manager
        self.logger = log_manager.get_logger(__name__) if log_manager else None
        
        self.conversation_instance = conversation_instance
        self.is_active = False
        self.current_image_path = ""
        self.current_prompt = ""
        
        self.logger.info("VQAManager: 初始化完成")
    
    def set_conversation_instance(self, conversation_instance):
        """
        设置对话实例
        
        Args:
            conversation_instance: 对话实例
        """
        self.conversation_instance = conversation_instance
        self.logger.info("VQAManager: 对话实例已设置")
    
    def start_vqa_with_image(self, image_path: str, prompt: str = "") -> bool:
        """
        使用图片启动VQA对话
        
        Args:
            image_path: 图片文件路径
            prompt: 文本提示，如果为空则等待语音指令
            
        Returns:
            bool: 是否成功启动
        """
        try:
            if not self.conversation_instance:
                raise RuntimeError("对话实例未设置")
            self.logger.info(f"VQA已启动，图片: {image_path}, 提示: {prompt}")
            
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"图片文件不存在: {image_path}")
            
            self.current_image_path = image_path
            self.current_prompt = prompt
            self.is_active = True
            
            # 读取图片并编码为base64
            image_data = self._load_image_as_base64(image_path)
            if not image_data:
                raise RuntimeError("图片编码失败")
            
            # 构造图片参数
            image_param = {"type": "base64", "value": image_data}           
            images_params = RequestToRespondParameters(images=[image_param])

            # 发送VQA请求
            if prompt:
                # 有文本提示，直接发送
                self.conversation_instance.conversation.request_to_respond(
                    "prompt", prompt, parameters=images_params
                )
                self.logger.info(f"VQA已启动，图片: {image_path}, 提示: {prompt}")
            else:
                # 无文本提示，等待语音指令
                self.conversation_instance.conversation.request_to_respond(
                    "prompt", "", parameters=images_params
                )
                self.logger.info(f"VQA已启动，图片: {image_path}, 等待语音指令")
            
            self.vqa_status_changed.emit("VQA已启动")
            return True
            
        except Exception as e:
            error_msg = f"启动VQA失败: {e}"
            self.logger.error(error_msg)
            self.vqa_error.emit(error_msg)
            return False
    
    def start_vqa_with_base64(self, image_base64: str, prompt: str = "") -> bool:
        """
        使用base64编码的图片启动VQA对话
        
        Args:
            image_base64: base64编码的图片数据
            prompt: 文本提示，如果为空则等待语音指令
            
        Returns:
            bool: 是否成功启动
        """
        try:
            if not self.conversation_instance:
                raise RuntimeError("对话实例未设置")
            
            self.current_prompt = prompt
            self.is_active = True
            
            # 构造图片参数
            image_param = {"type": "base64", "value": image_base64}
            images_params = RequestToRespondParameters(images=[image_param])
            
            # 发送VQA请求
            if prompt:
                # 有文本提示，直接发送
                self.conversation_instance.conversation.request_to_respond(
                    "prompt", prompt, parameters=images_params
                )
                self.logger.info(f"VQA已启动，base64图片, 提示: {prompt}")
            else:
                # 无文本提示，等待语音指令
                self.conversation_instance.conversation.request_to_respond(
                    "prompt", "", parameters=images_params
                )
                self.logger.info(f"VQA已启动，base64图片, 等待语音指令")
            
            self.vqa_status_changed.emit("VQA已启动")
            return True
            
        except Exception as e:
            error_msg = f"启动VQA失败: {e}"
            self.logger.error(error_msg)
            self.vqa_error.emit(error_msg)
            return False
    
    def start_vqa_with_current_frame(self, prompt: str = "") -> bool:
        """
        使用当前摄像头帧启动VQA对话（用于实时视频流）
        
        Args:
            prompt: 文本提示，如果为空则等待语音指令
            
        Returns:
            bool: 是否成功启动
        """
        try:
            if not self.conversation_instance:
                raise RuntimeError("对话实例未设置")
            
            self.current_prompt = prompt
            self.is_active = True
            
            # 在实时视频流中，图片数据已经通过视频帧发送
            # 我们只需要发送文本提示即可
            if prompt:
                # 有文本提示，直接发送
                self.conversation_instance.conversation.request_to_respond("prompt", prompt)
                self.logger.info(f"实时视频流VQA已启动，提示: {prompt}")
            else:
                # 无文本提示，等待语音指令
                self.conversation_instance.conversation.request_to_respond("prompt", "")
                self.logger.info(f"实时视频流VQA已启动，等待语音指令")
            
            self.vqa_status_changed.emit("实时视频流VQA已启动")
            return True
            
        except Exception as e:
            error_msg = f"启动实时视频流VQA失败: {e}"
            self.logger.error(error_msg)
            self.vqa_error.emit(error_msg)
            return False
    
    def send_vqa_prompt(self, prompt: str) -> bool:
        """
        发送VQA文本提示
        
        Args:
            prompt: 文本提示
            
        Returns:
            bool: 是否成功发送
        """
        try:
            if not self.is_active:
                raise RuntimeError("VQA未启动")
            
            if not self.conversation_instance:
                raise RuntimeError("对话实例未设置")
            
            # 如果有当前图片，重新发送带图片的请求
            if self.current_image_path and os.path.exists(self.current_image_path):
                return self.start_vqa_with_image(self.current_image_path, prompt)
            else:
                # 无图片，直接发送文本请求
                self.conversation_instance.conversation.request_to_respond("prompt", prompt)
                self.logger.info(f"VQA提示已发送: {prompt}")
                return True
            
        except Exception as e:
            error_msg = f"发送VQA提示失败: {e}"
            self.logger.error(error_msg)
            self.vqa_error.emit(error_msg)
            return False
    
    def _load_image_as_base64(self, image_path: str) -> str:
        """
        将图片文件加载为base64编码
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            str: base64编码的图片数据
        """
        try:
            with open(image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
                self.logger.debug(f"图片编码成功: {image_path}")
                return image_data
                
        except Exception as e:
            self.logger.error(f"图片编码失败 {image_path}: {e}")
            return ""
    
    def stop_vqa(self) -> bool:
        """
        停止VQA功能
        
        Returns:
            bool: 是否成功停止
        """
        try:
            if not self.is_active:
                self.logger.info("VQA未在运行")
                return True
            
            self.is_active = False
            self.current_image_path = ""
            self.current_prompt = ""
            
            self.vqa_status_changed.emit("VQA已停止")
            self.logger.info("VQA已停止")
            return True
            
        except Exception as e:
            error_msg = f"停止VQA失败: {e}"
            self.logger.error(error_msg)
            self.vqa_error.emit(error_msg)
            return False
    
    def get_vqa_status(self) -> Dict[str, Any]:
        """
        获取VQA状态
        
        Returns:
            Dict: 状态信息
        """
        status = {
            'is_active': self.is_active,
            'current_image_path': self.current_image_path,
            'current_prompt': self.current_prompt,
            'has_conversation_instance': self.conversation_instance is not None
        }
        
        return status
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("VQAManager: 开始清理...")
        try:
            self.stop_vqa()
        except Exception as e:
            self.logger.warning(f"清理VQA时出错: {e}")
        self.logger.info("VQAManager: 清理完成")
