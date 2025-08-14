#!/usr/bin/env python3
# Copyright (C) Alibaba Group. All Rights Reserved.
# MIT License (https://opensource.org/licenses/MIT)

"""
Multi-modal Dialog Conversation Manager

This module manages voice-based conversations with DashScope multi-modal dialog API.
"""

import random
import sys
import time
import os
import multiprocessing
import threading
import signal
import json
from typing import Optional, Dict, Any

from dashscope.common.logging import logger
from dashscope.multimodal.dialog_state import DialogState
from dashscope.multimodal.multimodal_dialog import MultiModalDialog, MultiModalCallback
from dashscope.multimodal.multimodal_request_params import (
    Upstream, Downstream, ClientInfo, RequestParameters, 
    Device, RequestToRespondParameters
)

# 导入音频工具类
from AudioRecorder import AudioRecorder
from ListeningStateMonitor import ListeningStateMonitor
from B64PCMPlayer import B64PCMPlayer
from ChatCallback import ChatCallback
from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager

# 导入B64PCMPlayer用于音频播放
import pyaudio

# 移除未使用的全局变量
# begin_time: int = 0

# Configuration constants
AUDIO_CHUNK_SIZE = 3200
AUDIO_SLEEP_INTERVAL = 0.1
MAX_CONVERSATION_ROUNDS = 3
CONVERSATION_TIMEOUT = 10
WEBSOCKET_URL = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"
MODEL_NAME = "multimodal-dialog"
VOICE_NAME = "longxiaochun_v2"
SAMPLE_RATE = 48000


class TMultiModalConversation:
    """Multi-modal conversation manager"""
    
    def __init__(self, log_manager: LogManager, config_manager: ConfigManager,
                 app_id: str, workspace_id: str, api_key: str, 
                 dialog_id: str = "", conversation_mode: str = "duplex"):
        
        """Initialize conversation with provided credentials"""
        self.log_manager = log_manager
        self.config_manager = config_manager
        self.logger = log_manager.get_logger(__name__) if log_manager else None
        
        self.logger.debug("Initializing conversation")
        
        # 初始化Listening状态监控器
        self.listening_monitor = ListeningStateMonitor(
            log_manager=log_manager,
            config_manager=config_manager
        )
        
        # Configure request parameters
        up_stream = Upstream(type="AudioOnly", mode=conversation_mode, audio_format="pcm") # AudioAndVideo, AudioOnly
        client_info = ClientInfo(user_id="demo_user", device=Device(uuid="demo_device_12345"))
        request_params = RequestParameters(
            upstream=up_stream,
            downstream=Downstream(voice=VOICE_NAME, sample_rate=SAMPLE_RATE),
            client_info=client_info
        )

        # 创建带有音频播放功能的回调处理器
        self.callback = ChatCallback(
            self.listening_monitor,
            log_manager=self.log_manager,
            config_manager=self.config_manager
        )
        
        # 设置回调处理器中的conversation实例引用
        self.callback.conversation_instance = self
        
        # 创建音频录制器，用于非阻塞录制
        self.audio_recorder = AudioRecorder(
            pya=self.callback.pya,
            log_manager=self.log_manager,
            config_manager=self.config_manager,
            sample_rate=16000,  # 麦克风采样率
            chunk_size=AUDIO_CHUNK_SIZE,
            callback=self._send_audio_data_callback
        )
        
        # 设置回调处理器中的录制器引用
        self.callback.audio_recorder = self.audio_recorder
        
        self.conversation = MultiModalDialog(
            app_id=app_id,
            workspace_id=workspace_id,
            url=WEBSOCKET_URL,
            request_params=request_params,
            multimodal_callback=self.callback,
            api_key=api_key,
            dialog_id=dialog_id,
            model=MODEL_NAME
        )

    def start_conversation(self):
        """Start conversation session"""
        self.conversation.start("")
        logger.info("Conversation started")

    def get_conversation_mode(self) -> str:
        """Get current conversation mode"""
        return self.conversation.get_conversation_mode()

    def get_dialog_state(self) -> DialogState:
        """Get current dialog state"""
        return self.conversation.get_dialog_state()

    def wait_for_listening_state(self, timeout: float = 30.0) -> bool:
        """
        等待系统进入Listening状态
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            bool: 是否成功等到Listening状态
        """
        return self.listening_monitor.wait_for_next_listening(timeout)

    def get_listening_count(self) -> int:
        """获取Listening状态的计数"""
        return self.listening_monitor.get_listening_count()

    def start_speech_interaction(self):
        """Start speech interaction with audio streaming"""
        # Wait for listening state
        while self.conversation.get_dialog_state() != DialogState.LISTENING:
            time.sleep(0.1)
        
        logger.info(f"starting speech")
        # self.conversation.send_heart_beat()
        self.conversation.start_speech()

        # # Stream audio file
        # audio_file = self._get_audio_file()
        # self._stream_audio(audio_file)

    def stop_speech_interaction(self):
        """Stop speech interaction"""
        logger.info("Stopping speech")
        self.conversation.stop_speech()

    def send_local_responding_started(self):
        """Notify local response started"""
        self.conversation.local_responding_started()

    def send_local_responding_ended(self):
        """Notify local response ended"""
        self.conversation.local_responding_ended()

    def _send_audio_data_callback(self, audio_data: bytes):
        """音频录制器的回调函数，用于发送录制的音频数据到服务器"""
        if self.conversation and self.conversation.get_dialog_state() == DialogState.LISTENING:
            self.conversation.send_audio_data(audio_data)
            logger.debug(f"_send_audio_data_callback sent audio data: {len(audio_data)} bytes")
    

    
    def stop_conversation(self):
        """Stop conversation session"""
        self.conversation.stop()

        # 停止音频录制器
        if hasattr(self, 'audio_recorder'):
            self.audio_recorder.shutdown()
        # 显示统计信息
        listening_count = self.get_listening_count()
        logger.info(f"completed. Total Listening states: {listening_count}")
        logger.info("Conversation stopped")

    def test_image_vqa(self, image_data: str, question: str, image_type: str = "base64"):
        """Test visual Q&A with image"""
        logger.info("Testing image VQA")
        image = {"type": image_type, "value": image_data}
        images_params = RequestToRespondParameters(images=[image])
        self.conversation.request_to_respond("prompt", question, parameters=images_params)

    def _get_audio_file(self) -> str:
        """Get audio file path"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        audio_files = [os.path.join(current_dir, '1_plus_1.wav')]
        return random.choice(audio_files)

    def _stream_audio(self, file_path: str):
        """Stream audio file to conversation"""
        global begin_time
        
        if not os.path.exists(file_path):
            logger.error(f"Audio file not found: {file_path}")
            return
        
        logger.debug(f"streaming: {file_path}")
        
        with open(file_path, "rb") as f:
            while True:
                data = f.read(AUDIO_CHUNK_SIZE)
                if not data:
                    break
                self.conversation.send_audio_data(data)
                time.sleep(AUDIO_SLEEP_INTERVAL)
            
            begin_time = int(time.time() * 1000)
            logger.debug(f"streaming completed at: {begin_time}ms")
            
            # Send empty packets for non-push2talk modes
            if self.get_conversation_mode() != "push2talk":
                while self.conversation.get_dialog_state() == DialogState.LISTENING:
                    time.sleep(0.1)
                    self.conversation.send_audio_data(bytearray(AUDIO_CHUNK_SIZE))
