#!/usr/bin/env python3
# Copyright (C) Alibaba Group. All Rights Reserved.
# MIT License (https://opensource.org/licenses/MIT)

"""
语音通信管理器

这个模块负责管理语音输入输出功能，包括：
1. 语音识别和合成
2. 与阿里百炼平台的通信
3. 文本对话功能
4. 文本转录功能
5. VQA功能
6. 实时视频流功能
7. 守护进程管理
8. 配置和日志管理

采用模块化设计，支持非阻塞运行
"""

import os
import sys
import time
import json
import logging
import threading
import queue
from typing import Optional, Dict, Any, Callable
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot, QThread, QTimer

# 导入阿里百炼相关模块
from dashscope.multimodal.dialog_state import DialogState
from dashscope.multimodal.multimodal_dialog import MultiModalDialog, MultiModalCallback
from dashscope.multimodal.multimodal_request_params import (
    Upstream, Downstream, ClientInfo, RequestParameters, 
    Device, RequestToRespondParameters, BizParams
)

# 导入音频工具类
from ListeningStateMonitor import ListeningStateMonitor
from AudioRecorder import AudioRecorder
from B64PCMPlayer import B64PCMPlayer

# 导入功能管理器 - 使用绝对导入提高兼容性
from camera_manager import CameraManager
from vqa_manager import VQAManager
from transcript_manager import TranscriptManager
from live_stream_manager import LiveStreamManager


import dotenv

# 导入项目相关模块
from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager
from TMultiModalConversation import TMultiModalConversation

# 尝试加载环境变量文件，支持多种路径
env_paths = [
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env'),  # DeepWin/.env
    os.path.join(os.path.dirname(__file__), '..', '..', '.env'),       # DeepWin/src/.env
    '.env'  # 当前工作目录
]

for env_path in env_paths:
    if os.path.exists(env_path):
        dotenv.load_dotenv(dotenv_path=env_path)
        break

# 配置常量
AUDIO_CHUNK_SIZE = 3200
AUDIO_SLEEP_INTERVAL = 0.1
MAX_CONVERSATION_ROUNDS = 3
CONVERSATION_TIMEOUT = 10
SAMPLE_RATE = 48000
VIDEO_FRAME_INTERVAL = 0.5  # 500ms


class VoiceManager(QObject):
    """
    语音通信管理器
    
    负责管理语音输入输出功能，采用模块化设计：
    1. 语音识别和合成
    2. 与阿里百炼平台的通信
    3. 文本对话功能
    4. 文本转录功能
    5. VQA功能
    6. 实时视频流功能
    7. 守护进程管理
    8. 配置和日志管理
    """
    
    # 信号定义
    conversation_started = Signal(str)  # dialog_id
    conversation_stopped = Signal()
    conversation_error = Signal(str)  # error_message
    command_parsed = Signal(list)  # commands_list
    command_executed = Signal(str, list)  # command_name, params
    voice_state_changed = Signal(str)  # state_message
    
    # 语音命令信号
    voice_command_received = Signal(dict)  # 转发给Handler的信号
    
    # 功能状态信号
    text_conversation_started = Signal()
    text_conversation_stopped = Signal()
    transcript_started = Signal()
    transcript_stopped = Signal()
    vqa_started = Signal()
    vqa_stopped = Signal()
    live_stream_started = Signal()
    live_stream_stopped = Signal()
    
    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, parent=None):
        """
        初始化语音管理器
        
        Args:
            log_manager: 全局日志管理器实例
            config_manager: 全局配置管理器实例
            parent: QObject父对象
        """
        super().__init__(parent)
        self.log_manager = log_manager
        self.logger = log_manager.get_logger(__name__)
        self.config_manager = config_manager
        
        self.logger.info("VoiceManager: 初始化中...")
        
        # 初始化状态
        self.dialog_id = None
        self.conversation = None
        self.is_conversation_active = False
        self.conversation_mode = "duplex"
        self.current_conversation_type = "text"  # text, vqa, transcript, live_stream
        
        # 状态属性
        self.conversation_round = 0  # 对话轮数
        self.voice_enabled = False   # 语音使能开关
        self.live_video_enabled = False  # 实时视频使能开关
        self.worker_thread_running = False  # 工作线程运行状态
        self._stop_requested = False  # 停止请求标志
        self.max_conversation_rounds = MAX_CONVERSATION_ROUNDS
        
        # 加载配置
        self._load_config()
        
        # 监听状态监控
        self.listening_monitor = ListeningStateMonitor(log_manager=self.log_manager, config_manager=self.config_manager)
        
        # 消息队列 - 用于串行执行指令
        self.message_queue = queue.Queue()
        self.is_processing_message = False
        
        # 工作线程
        self.worker_thread = None
        # 初始化功能管理器
        self._init_function_managers()
        # 创建对话实例
        self._create_conversation_instance()
        
        # 初始化音频相关
        # self._init_audio()

        self.logger.info(f"conversation: {self.conversation}")
        
        self.audio_recorder = self.conversation.audio_recorder
        
        # 连接信号
        self._connect_signals()
        
        # 自动启动工作线程
        self.start_worker_thread()
        
        self.logger.info("VoiceManager: 初始化完成")
    
    def _load_config(self):
        """加载语音配置"""
        try:
            # 尝试从配置文件加载
            voice_config = self.config_manager.get('voice', {})
            
            # 设置默认值
            self.app_id = voice_config.get('app_id') or os.getenv("APP_ID")
            self.workspace_id = voice_config.get('workspace_id') or os.getenv("WORKSPACE_ID")
            self.api_key = voice_config.get('api_key') or os.getenv("DASHSCOPE_API_KEY")
            
            # 语音参数
            self.voice_name = voice_config.get('voice_name', 'longxiaochun_v2')
            self.sample_rate = voice_config.get('sample_rate', 48000)
            self.audio_chunk_size = voice_config.get('audio_chunk_size', 3200)
            
            # 服务参数
            self.websocket_url = voice_config.get('websocket_url', 'wss://dashscope.aliyuncs.com/api-ws/v1/inference')
            self.model_name = voice_config.get('model_name', 'multimodal-dialog')
            self.conversation_mode = voice_config.get('conversation_mode', 'duplex')
            
            # 使能开关配置（只在配置文件中明确设置时才覆盖默认值）
            if 'video_enabled' in voice_config:
                self.live_video_enabled = voice_config.get('video_enabled', False)
            if 'voice_enabled' in voice_config:
                self.voice_enabled = voice_config.get('voice_enabled', False)
            
            # 验证必要的配置
            if not all([self.app_id, self.workspace_id, self.api_key]):
                self.logger.warning("缺少必要的语音服务配置: APP_ID, WORKSPACE_ID, API_KEY")
                # 设置默认值，避免后续使用时出错
                self.app_id = "default_app_id"
                self.workspace_id = "default_workspace_id"
                self.api_key = "default_api_key"
            
            self.logger.info("语音配置加载完成")
            
        except Exception as e:
            self.logger.error(f"加载语音配置失败: {e}")
            # 设置默认值，避免后续使用时出错
            self.app_id = "default_app_id"
            self.workspace_id = "default_workspace_id"
            self.api_key = "default_api_key"
    
    def _init_function_managers(self):
        """初始化功能管理器"""
        try:
            # 创建功能管理器，传递日志和配置管理器
            self.vqa_manager = VQAManager(
                log_manager=self.log_manager,
                config_manager=self.config_manager,
                parent=self
            )
            self.transcript_manager = TranscriptManager(
                log_manager=self.log_manager,
                config_manager=self.config_manager,
                parent=self
            )
            self.live_stream_manager = LiveStreamManager(
                log_manager=self.log_manager,
                config_manager=self.config_manager,
                parent=self
            )
            
            self.logger.info("功能管理器初始化完成")
            
        except Exception as e:
            self.logger.error(f"初始化功能管理器失败: {e}")
            # 设置默认值，避免后续使用时出错
            self.vqa_manager = None
            self.transcript_manager = None
            self.live_stream_manager = None
    
    def _create_conversation_instance(self):
        """创建对话实例"""
        try:
            # 检查必要的配置是否存在
            if not all([self.app_id, self.workspace_id, self.api_key]):
                self.logger.warning("缺少必要的语音服务配置，跳过对话实例创建")
                self.conversation = None
                return
            
            self.conversation = TMultiModalConversation(
                app_id=self.app_id,
                workspace_id=self.workspace_id,
                api_key=self.api_key,
                dialog_id=self.dialog_id,
                conversation_mode=self.conversation_mode,
                log_manager=self.log_manager,
                config_manager=self.config_manager
            )
            
            # 设置功能管理器的对话实例
            self.vqa_manager.set_conversation_instance(self.conversation)
            self.transcript_manager.set_conversation_instance(self.conversation)
            self.live_stream_manager.set_conversation_instance(self.conversation)
            
            self.logger.info("对话实例创建成功")
            
        except Exception as e:
            self.logger.error(f"创建对话实例失败: {e}")
            self.conversation = None
    
    def _connect_signals(self):
        """连接信号"""
        try:
            # 连接功能管理器的信号
            if self.vqa_manager and hasattr(self.vqa_manager, 'vqa_status_changed'):
                try:
                    self.vqa_manager.vqa_status_changed.connect(self._on_vqa_status_changed)
                except Exception as e:
                    self.logger.warning(f"连接VQA状态变化信号失败: {e}")
            
            if self.transcript_manager and hasattr(self.transcript_manager, 'transcript_status_changed'):
                try:
                    self.transcript_manager.transcript_status_changed.connect(self._on_transcript_status_changed)
                except Exception as e:
                    self.logger.warning(f"连接转录状态变化信号失败: {e}")
            
            if self.live_stream_manager and hasattr(self.live_stream_manager, 'live_stream_status_changed'):
                try:
                    self.live_stream_manager.live_stream_status_changed.connect(self._on_live_stream_status_changed)
                except Exception as e:
                    self.logger.warning(f"连接实时视频流状态变化信号失败: {e}")
            
            # 连接ChatCallback的信号（在创建对话实例之后）
            self._connect_chat_callback()
            
            # 连接对话状态变化信号，用于监控对话轮数
            if self.conversation and hasattr(self.conversation, 'callback'):
                try:
                    self.conversation.callback.state_changed.connect(self._on_dialog_state_changed)
                except Exception as e:
                    self.logger.warning(f"连接对话状态变化信号失败: {e}")
            
            self.logger.info("信号连接完成")
            
        except Exception as e:
            self.logger.warning(f"连接信号失败: {e}")
        

    
    def _update_status(self):
        """更新状态信息"""
        try:
            if self.conversation:
                try:
                    current_state = self.conversation.get_dialog_state()
                    self.voice_state_changed.emit(f"对话状态: {current_state}, 轮数: {self.conversation_round}")
                except Exception as e:
                    self.logger.debug(f"获取对话状态时出错: {e}")
            
            # 更新队列状态
            queue_status = self.get_queue_status()
            if queue_status['size'] > 0:
                self.voice_state_changed.emit(f"队列中待处理任务: {queue_status['size']}")
                
        except Exception as e:
            self.logger.debug(f"更新状态时出错: {e}")
    
    # ==================== 使能开关控制 ====================
    
    def get_enable_status(self) -> Dict[str, bool]:
        """获取使能状态"""
        return {
            'live_video_enabled': self.live_video_enabled,
            'voice_enabled': self.voice_enabled
        }
    
    # ==================== 文本对话功能 ====================
    
    def start_text_conversation(self, prompt: str) -> bool:
        """
        开始文本对话（兼容性接口，建议使用add_task_to_queue）
        
        Args:
            prompt: 文本提示
            
        Returns:
            bool: 是否成功启动
        """
        try:
            if not self.conversation:
                self.logger.error("对话实例未创建，无法开始文本对话")
                return False
            
            self.logger.info(f"启动文本对话: {prompt}")
            
            # 开始对话
            self.conversation.start_conversation()
            
            # 直接发送文本，避免通过消息队列
            self.conversation.conversation.request_to_respond('prompt', prompt)
            
            self.current_conversation_type = "text"
            self.is_conversation_active = True
            
            # 发送信号
            self.text_conversation_started.emit()
            self.conversation_started.emit("text_dialog")
            
            self.logger.info("文本对话启动成功")
            return True
            
        except Exception as e:
            error_msg = f"启动文本对话失败: {e}"
            self.logger.error(error_msg)
            self.conversation_error.emit(error_msg)
            return False
    
    def send_text_message(self, text: str) -> bool:
        """
        发送文本消息（兼容性接口，建议使用add_task_to_queue）
        
        Args:
            text: 文本消息
            
        Returns:
            bool: 是否成功发送
        """
        try:
            if not self.is_conversation_active or not self.conversation:
                self.logger.error("对话未启动，无法发送文本消息")
                return False
            
            # 直接发送文本，避免通过消息队列
            self.conversation.conversation.request_to_respond('prompt', text)
            
            self.logger.info(f"文本消息已发送: {text}")
            return True
            
        except Exception as e:
            error_msg = f"发送文本消息失败: {e}"
            self.logger.error(error_msg)
            self.conversation_error.emit(error_msg)
            return False
    
    # ==================== 文本转录功能 ====================
    
    def start_transcript(self, text: str) -> bool:
        """
        开始文本转录
        
        Args:
            text: 要转录的文本
            
        Returns:
            bool: 是否成功启动
        """
        try:
            if not self.conversation:
                self.logger.error("对话实例未创建，无法开始转录")
                return False
            
            self.logger.info(f"启动文本转录: {text}")
            
            # 开始对话
            self.conversation.start_conversation()
            
            # 直接调用转录管理器，避免通过消息队列
            success = self.transcript_manager.start_transcript(text)
            
            if success:
                self.current_conversation_type = "transcript"
                self.is_conversation_active = True
                
                # 发送信号
                self.transcript_started.emit()
                self.conversation_started.emit("transcript")
            
            return success
            
            return True
            
        except Exception as e:
            error_msg = f"启动文本转录失败: {e}"
            self.logger.error(error_msg)
            self.conversation_error.emit(error_msg)
            return False
    
    def send_transcript_text(self, text: str) -> bool:
        """
        发送转录文本
        
        Args:
            text: 要转录的文本
            
        Returns:
            bool: 是否成功发送
        """
        return self.transcript_manager.send_transcript_text(text)
    
    # ==================== VQA功能 ====================
    
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
            if not self.conversation:
                self.logger.error("对话实例未创建，无法开始VQA对话")
                return False
            
            self.logger.info(f"启动VQA对话，图片: {image_path}, 提示: {prompt}")
            
            # 开始对话
            self.conversation.start_conversation()
            
            # 直接调用VQA管理器，避免通过消息队列
            success = self.vqa_manager.start_vqa_with_image(image_path, prompt)
            
            if success:
                self.current_conversation_type = "vqa"
                self.is_conversation_active = True
                
                # 发送信号
                self.vqa_started.emit()
                self.conversation_started.emit("vqa")
            
            return success
            
        except Exception as e:
            error_msg = f"启动VQA对话失败: {e}"
            self.logger.error(error_msg)
            self.conversation_error.emit(error_msg)
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
            if not self.conversation:
                self.logger.error("对话实例未创建，无法开始VQA对话")
                return False
            
            self.logger.info(f"启动VQA对话，base64图片, 提示: {prompt}")
            
            # 开始对话
            self.conversation.start_conversation()
            
            # 使用VQA管理器
            success = self.vqa_manager.start_vqa_with_base64(image_base64, prompt)
            
            if success:
                self.current_conversation_type = "vqa"
                self.is_conversation_active = True
                
                # 发送信号
                self.vqa_started.emit()
                self.conversation_started.emit("vqa")
            
            return success
            
        except Exception as e:
            error_msg = f"启动VQA对话失败: {e}"
            self.logger.error(error_msg)
            self.conversation_error.emit(error_msg)
            return False
    
    def send_vqa_prompt(self, prompt: str) -> bool:
        """
        发送VQA文本提示
        
        Args:
            prompt: 文本提示
            
        Returns:
            bool: 是否成功发送
        """
        return self.vqa_manager.send_vqa_prompt(prompt)
    
    def start_vqa_with_current_frame(self, prompt: str = "") -> bool:
        """
        使用当前摄像头帧启动VQA对话（用于实时视频流）
        
        Args:
            prompt: 文本提示，如果为空则等待语音指令
            
        Returns:
            bool: 是否成功启动
        """
        return self.vqa_manager.start_vqa_with_current_frame(prompt)
    
    # ==================== 实时视频流功能 ====================
    
    def start_live_stream(self, camera_index: int = 0) -> bool:
        """
        启动实时视频流
        
        Args:
            camera_index: 摄像头索引
            
        Returns:
            bool: 是否成功启动
        """
        try:
            if not self.conversation:
                self.logger.error("对话实例未创建，无法开始实时视频流")
                return False
            
            self.logger.info(f"启动实时视频流，摄像头: {camera_index}")
            
            # 开始对话
            self.conversation.start_conversation()
            
            # 使用实时视频流管理器
            success = self.live_stream_manager.start_live_stream(camera_index)
            
            if success:
                self.current_conversation_type = "live_stream"
                self.is_conversation_active = True
                
                # 发送信号
                self.live_stream_started.emit()
                self.conversation_started.emit("live_stream")
            
            return success
            
        except Exception as e:
            error_msg = f"启动实时视频流失败: {e}"
            self.logger.error(error_msg)
            self.conversation_error.emit(error_msg)
            return False
    
    def stop_live_stream(self) -> bool:
        """
        停止实时视频流
        
        Returns:
            bool: 是否成功停止
        """
        return self.live_stream_manager.stop_live_stream()
    
    def set_live_video_enabled(self, enabled: bool):
        """
        设置实时视频使能状态
        
        Args:
            enabled: 是否使能实时视频
        """

        if not self.is_conversation_active:
            return
        
        self.live_video_enabled = enabled
        self.logger.info(f"实时视频使能状态设置为: {enabled}")
        
        # 直接通过LiveStreamManager控制视频流
        if enabled:
            self.live_stream_manager.start_live_stream()
        else:
            self.live_stream_manager.stop_live_stream()
    
    # ==================== 语音对话功能 ====================
    
    def start_voice_conversation(self) -> bool:
        """
        开始语音对话
        
        Returns:
            bool: 是否成功启动
        """
        try:
            if self.is_conversation_active:
                self.logger.warning("语音对话已在运行中")
                return False
                
            if not self.conversation:
                self.logger.error("对话实例未创建，无法开始语音对话")
                return False
            
            self.logger.info("启动语音对话...")
            
            # 开始对话
            self.conversation.start_conversation()
            
            self.current_conversation_type = "voice"
            self.is_conversation_active = True
            
            # 发送信号
            self.conversation_started.emit("voice")
            
            self.logger.info("语音对话启动成功")
            return True
            
        except Exception as e:
            error_msg = f"启动语音对话失败: {e}"
            self.logger.error(error_msg)
            self.conversation_error.emit(error_msg)
            return False
    
    def set_voice_enabled(self, enabled: bool):
        """
        设置语音使能状态
        
        Args:
            enabled: 是否使能语音
        """
        self.voice_enabled = enabled
        self.logger.info(f"语音使能状态设置为: {enabled}")
        
        if enabled and self.is_conversation_active:
            # 如果启用语音且对话活跃，启动语音录制
            if self.audio_recorder:
                self.audio_recorder.start_recording()
        elif not enabled:
            # 如果禁用语音，停止语音录制
            if self.audio_recorder:
                self.audio_recorder.stop_recording()

    
    # ==================== 停止功能 ====================
    
    def stop_conversation(self) -> bool:
        """
        停止当前对话
        
        Returns:
            bool: 是否成功停止
        """
        try:
            if not self.is_conversation_active:
                self.logger.warning("没有活跃的对话")
                return True
            
            self.logger.info("停止对话...")
            
            # 设置停止标志，让工作线程正常退出
            self._stop_requested = True
            
            # 根据当前对话类型停止相应功能
            if self.current_conversation_type == "vqa" and self.vqa_manager:
                try:
                    self.vqa_manager.stop_vqa()
                except Exception as e:
                    self.logger.warning(f"停止VQA时出错: {e}")
            elif self.current_conversation_type == "transcript" and self.transcript_manager:
                try:
                    self.transcript_manager.stop_transcript()
                except Exception as e:
                    self.logger.warning(f"停止转录时出错: {e}")
            elif self.current_conversation_type == "live_stream" and self.live_stream_manager:
                try:
                    self.live_stream_manager.stop_live_stream()
                except Exception as e:
                    self.logger.warning(f"停止实时视频流时出错: {e}")
            
            # 停止视频帧上传 - 通过LiveStreamManager处理
            if self.live_stream_manager and hasattr(self.live_stream_manager, 'is_active') and self.live_stream_manager.is_active:
                try:
                    self.live_stream_manager.stop_live_stream()
                except Exception as e:
                    self.logger.warning(f"停止视频帧上传时出错: {e}")
            
            # 停止语音录制
            if self.audio_recorder:
                try:
                    self.audio_recorder.stop_recording()
                except Exception as e:
                    self.logger.warning(f"停止语音录制时出错: {e}")
            
            # 停止对话
            if self.conversation:
                try:
                    self.conversation.stop_conversation()
                except Exception as e:
                    self.logger.warning(f"停止对话时出错: {e}")
            
            # 清理状态
            self.is_conversation_active = False
            self.current_conversation_type = "text"
            
            # 发送信号
            self.conversation_stopped.emit()
            self.voice_state_changed.emit("对话已停止")
            
            self.logger.info("对话已停止")
            return True
            
        except Exception as e:
            error_msg = f"停止对话失败: {e}"
            self.logger.error(error_msg)
            self.conversation_error.emit(error_msg)
            return False
    
    # ==================== 状态查询 ====================
    
    def get_conversation_status(self) -> Dict[str, Any]:
        """
        获取对话状态
        
        Returns:
            Dict: 包含状态信息的字典
        """
        status = {
            'is_active': self.is_conversation_active,
            'dialog_id': self.dialog_id,
            'conversation_mode': self.conversation_mode,
            'current_conversation_type': self.current_conversation_type,
            'conversation_round': getattr(self, 'conversation_round', 0),
            'voice_enabled': getattr(self, 'voice_enabled', False),
            'live_video_enabled': getattr(self, 'live_video_enabled', False),
            'worker_thread_running': getattr(self, 'worker_thread_running', False)
        }
        
        if self.conversation:
            try:
                status['dialog_state'] = str(self.conversation.get_dialog_state())
            except:
                status['dialog_state'] = 'unknown'
        
        # 添加各功能管理器的状态

        status['vqa_status'] = self.vqa_manager.get_vqa_status()
        status['transcript_status'] = self.transcript_manager.get_transcript_status()
        status['live_stream_status'] = self.live_stream_manager.get_live_stream_status()

        
        return status
    
    def get_conversation_round(self) -> int:
        """
        获取当前对话轮数
        
        Returns:
            int: 当前对话轮数
        """
        return getattr(self, 'conversation_round', 0)
    
    def wait_for_listening_state(self, timeout: float = 30.0) -> bool:
        """
        等待系统进入Listening状态
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            bool: 是否成功等到Listening状态
        """
        if self.conversation:
            return self.conversation.wait_for_listening_state(timeout)
        return False
    
    # ==================== 信号处理 ====================
    
    def _on_vqa_status_changed(self, status_msg: str):
        """处理VQA状态变化"""
        self.logger.info(f"VQA状态变化: {status_msg}")
        self.voice_state_changed.emit(f"VQA: {status_msg}")
    
    def _on_transcript_status_changed(self, status_msg: str):
        """处理转录状态变化"""
        self.logger.info(f"转录状态变化: {status_msg}")
        self.voice_state_changed.emit(f"转录: {status_msg}")
    
    def _on_live_stream_status_changed(self, status_msg: str):
        """处理实时视频流状态变化"""
        self.logger.info(f"实时视频流状态变化: {status_msg}")
        self.voice_state_changed.emit(f"实时视频流: {status_msg}")
    
    def _on_dialog_state_changed(self, state):
        """处理对话状态变化，用于监控对话轮数"""
        try:
            from dashscope.multimodal.dialog_state import DialogState
            
            if state == DialogState.RESPONDING:
                # 当开始响应时，增加对话轮数
                self.conversation_round += 1
                self.logger.info(f"对话轮数增加到: {self.conversation_round}")
                self.voice_state_changed.emit(f"对话轮数: {self.conversation_round}")
            
            elif state == DialogState.LISTENING:
                # 当进入监听状态时，记录状态
                self.logger.info("进入监听状态，准备接收输入")
                self.voice_state_changed.emit("进入监听状态")
                
        except Exception as e:
            self.logger.warning(f"处理对话状态变化时出错: {e}")
    
    def _connect_chat_callback(self):
        """连接ChatCallback的信号"""
        if self.conversation and hasattr(self.conversation, 'callback') and self.conversation.callback:
            try:
                # 这里需要根据实际的ChatCallback实现来连接信号
                self.conversation.callback.voice_response_processed.connect(self._on_voice_response_processed)
                self.logger.info("ChatCallback信号连接成功")
            except Exception as e:
                self.logger.warning(f"连接ChatCallback信号失败: {e}")
        else:
            self.logger.warning("无法连接ChatCallback信号，conversation或callback不可用")
    
    @Slot(dict)
    def _on_voice_response_processed(self, payload: dict):
        """处理语音响应，提取commands并发出信号"""
        try:
            if "output" in payload and "extra_info" in payload["output"]:
                extra_info = payload["output"]["extra_info"]
                commands_str = extra_info.get("commands", "[]")
                
                if commands_str and commands_str != "[]":
                    self.logger.info(f"发现commands: {commands_str}")
                    
                    # 解析commands
                    commands_list = json.loads(commands_str)
                    for command in commands_list:
                        self.logger.info(f"处理命令: {command}")
                        # 发出语音命令接收信号，让Handler接收
                        self.voice_command_received.emit(command)
                        
        except Exception as e:
            self.logger.error(f"处理语音响应时发生错误: {str(e)}")
    
    # ==================== 工作线程管理 ====================
    
    def start_worker_thread(self):
        """启动工作线程"""
        if hasattr(self, 'worker_thread') and self.worker_thread and self.worker_thread.is_alive():
            self.logger.warning("工作线程已在运行中")
            return False
        
        self._stop_requested = False
        self.worker_thread = threading.Thread(target=self._worker_thread_loop, daemon=True)
        self.worker_thread.start()
        self.worker_thread_running = True
        self.logger.info("工作线程已启动")
        return True
    
    def stop_worker_thread(self):
        """停止工作线程"""
        if hasattr(self, 'worker_thread') and self.worker_thread and self.worker_thread.is_alive():
            self._stop_requested = True
            self.worker_thread.join(timeout=5.0)  # 等待最多5秒
            self.worker_thread_running = False
            self.logger.info("工作线程已停止")
    
    def _worker_thread_loop(self):
        """工作线程主循环"""
        self.logger.info("工作线程开始运行")
        self.is_conversation_active = True
        self.conversation.start_conversation()
        try:
            while not self._stop_requested:
                # 处理消息队列中的任务
                self._process_message_queue()
                self._update_status()
                # 短暂休眠，避免CPU占用过高
                time.sleep(0.1)
                
        except Exception as e:
            self.logger.error(f"工作线程运行出错: {e}")
        finally:
            self.logger.info("工作线程已退出")
    
    def _process_message_queue(self):
        """处理消息队列中的任务"""
        if not hasattr(self, 'message_queue') or not self.message_queue:
            return
        
        try:
            # 获取队列中的下一个任务
            if not self.message_queue.empty():
                task = self.message_queue.get_nowait()
                if task:
                    self._execute_task(task)
                    self.message_queue.task_done()
        except Exception as e:
            self.logger.warning(f"处理消息队列时出错: {e}")
    
    def _execute_task(self, task: dict):
        """执行任务"""
        try:
            task_type = task.get('type')
            task_data = task.get('data', {})
            self.logger.info(f"执行任务: {task_type}, 数据: {task_data}, 状态: {self.is_conversation_active}")
            # 等待监听状态
            self.conversation.wait_for_listening_state()
            
            if task_type == 'text':
                # 直接发送文本，避免循环调用
                if self.conversation and self.is_conversation_active:
                    self.logger.info(f"conversation: start_text_conversation")
                    self.conversation.conversation.request_to_respond('prompt', task_data.get('text', ''))
                    self.logger.info(f"文本消息已发送: {task_data.get('text', '')}")
            elif task_type == 'vqa':
                # 直接调用VQA管理器
                if self.conversation and self.is_conversation_active and self.vqa_manager:
                    try:
                        data = task_data.get('data', '')
                        img = data.get('img', '')
                        prompt = data.get('prompt', '')
                        self.logger.info(f"执行VQA任务: {data}, {img}, {prompt}")
                        self.vqa_manager.start_vqa_with_image(img, prompt)
                    except Exception as e:
                        self.logger.error(f"执行VQA任务时出错: {e}")
                else:
                    self.logger.warning("VQA管理器不可用或对话未激活")
            elif task_type == 'transcript':
                # 直接调用转录管理器
                if self.conversation and self.is_conversation_active and self.transcript_manager:
                    try:
                        self.transcript_manager.start_transcript(task_data.get('text', ''))
                    except Exception as e:
                        self.logger.error(f"执行转录任务时出错: {e}")
                else:
                    self.logger.warning("转录管理器不可用或对话未激活")
            elif task_type == 'live_stream':
                # 直接调用实时视频流管理器
                if self.conversation and self.is_conversation_active and self.live_stream_manager:
                    try:
                        self.live_stream_manager.start_live_stream(task_data.get('camera_index', 0))
                    except Exception as e:
                        self.logger.error(f"执行实时视频流任务时出错: {e}")
                else:
                    self.logger.warning("实时视频流管理器不可用或对话未激活")
            
            self.logger.info(f"任务执行完成: {task_type}")
            
        except Exception as e:
            self.logger.error(f"执行任务时出错: {e}")
    
    def _on_audio_data_received(self, audio_data: bytes):
        """
        音频数据回调函数
        当AudioRecorder录制到音频数据时，会自动调用此函数
        
        Args:
            audio_data: 录制的音频数据
        """
        try:
            if self.conversation and self.is_conversation_active:
                # 直接发送音频数据到对话系统
                self.conversation.conversation.send_audio_data(audio_data)
                self.logger.debug("音频数据已发送到对话系统")
        except Exception as e:
            self.logger.warning(f"处理音频数据时出错: {e}")
    
    
    # ==================== 消息队列管理 ====================
    
    def add_task_to_queue(self, task_type: str, **kwargs):
        """
        添加任务到消息队列
        
        Args:
            task_type: 任务类型 (text, vqa, transcript, live_stream)
            **kwargs: 任务参数
        """
        if not hasattr(self, 'message_queue') or not self.message_queue:
            import queue
            self.message_queue = queue.Queue()
        
        task = {
            'type': task_type,
            'data': kwargs,
            'timestamp': time.time()
        }

        self.message_queue.put(task)
        self.logger.info(f"任务已添加到队列: {task_type}")
    
    def get_queue_status(self) -> dict:
        """
        获取队列状态
        
        Returns:
            dict: 队列状态信息
        """
        if not hasattr(self, 'message_queue') or not self.message_queue:
            return {'size': 0, 'empty': True}
        
        return {
            'size': self.message_queue.qsize(),
            'empty': self.message_queue.empty()
        }
    
    # ==================== 清理资源 ====================
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("VoiceManager: 开始清理...")
        
        try:
            # 停止工作线程
            if hasattr(self, 'worker_thread_running') and self.worker_thread_running:
                try:
                    self.stop_worker_thread()
                except Exception as e:
                    self.logger.warning(f"停止工作线程时出错: {e}")
            
            # 重置工作线程运行状态
            self.worker_thread_running = False
            
            # 清理工作线程引用
            if hasattr(self, 'worker_thread') and self.worker_thread:
                self.worker_thread = None
            
            # 停止状态监控定时器
            if hasattr(self, 'status_timer') and self.status_timer:
                try:
                    self.status_timer.stop()
                    self.status_timer = None
                except Exception as e:
                    self.logger.warning(f"停止状态监控定时器时出错: {e}")
            
            # 停止对话
            if self.is_conversation_active:
                try:
                    self.stop_conversation()
                except Exception as e:
                    self.logger.warning(f"停止对话时出错: {e}")
            
            # 停止视频帧上传 - 通过LiveStreamManager处理
            if self.live_stream_manager and hasattr(self.live_stream_manager, 'is_active') and self.live_stream_manager.is_active:
                try:
                    self.live_stream_manager.stop_live_stream()
                except Exception as e:
                    self.logger.warning(f"停止视频帧上传时出错: {e}")
            
            # 停止语音录制
            if self.audio_recorder:
                try:
                    self.audio_recorder.stop_recording()
                    # 关闭音频录制器
                    self.audio_recorder.shutdown()
                    self.audio_recorder = None
                except Exception as e:
                    self.logger.warning(f"关闭音频录制器时出错: {e}")
            
            # 清理各功能管理器
            if self.vqa_manager:
                try:
                    self.vqa_manager.cleanup()
                except Exception as e:
                    self.logger.warning(f"清理VQA管理器时出错: {e}")
            
            if self.transcript_manager:
                try:
                    self.transcript_manager.cleanup()
                except Exception as e:
                    self.logger.warning(f"清理转录管理器时出错: {e}")
            
            if self.live_stream_manager:
                try:
                    self.live_stream_manager.cleanup()
                except Exception as e:
                    self.logger.warning(f"清理实时视频流管理器时出错: {e}")
            

            
            # 清理功能管理器引用
            self.vqa_manager = None
            self.transcript_manager = None
            self.live_stream_manager = None
            
            # 清理对话实例
            if hasattr(self, 'conversation') and self.conversation:
                self.conversation = None
            
            # 清理消息队列
            if hasattr(self, 'message_queue') and self.message_queue:
                try:
                    while not self.message_queue.empty():
                        try:
                            self.message_queue.get_nowait()
                            self.message_queue.task_done()
                        except:
                            break
                    self.message_queue = None
                except Exception as e:
                    self.logger.warning(f"清理消息队列时出错: {e}")
            
            # 清理监听状态监控
            if hasattr(self, 'listening_monitor') and self.listening_monitor:
                self.listening_monitor = None
            
        except Exception as e:
            self.logger.warning(f"清理资源时出错: {e}")
        
        self.logger.info("VoiceManager: 清理完成")
