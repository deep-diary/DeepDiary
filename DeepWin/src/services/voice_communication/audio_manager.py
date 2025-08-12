#!/usr/bin/env python3
# Copyright (C) Alibaba Group. All Rights Reserved.
# MIT License (https://opensource.org/licenses/MIT)

"""
语音通信管理器

这个模块负责管理语音输入输出功能，包括：
1. 语音识别和合成
2. 与阿里百炼平台的通信
3. 守护进程管理
4. 配置和日志管理
"""

import os
import sys
import time
import json
import logging
import multiprocessing
import threading
import signal
from typing import Optional, Dict, Any, Callable
from pathlib import Path
import random

from PySide6.QtCore import QObject, Signal, Slot, QThread, QThreadPool, QTimer

# 导入阿里百炼相关模块
from dashscope.multimodal.dialog_state import DialogState
from dashscope.multimodal.multimodal_dialog import MultiModalDialog, MultiModalCallback
from dashscope.multimodal.multimodal_request_params import (
    Upstream, Downstream, ClientInfo, RequestParameters, 
    Device, RequestToRespondParameters
)

# 导入音频工具类
from .ListeningStateMonitor import ListeningStateMonitor
from .AudioRecorder import AudioRecorder
from .B64PCMPlayer import B64PCMPlayer
import pyaudio
import dotenv

# 导入项目相关模块
from ...data_management.log_manager import LogManager
from ...data_management.config_manager import ConfigManager
from .TMultiModalConversation import TMultiModalConversation

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


class VoiceManager(QObject):
    """
    语音通信管理器
    
    负责管理语音输入输出功能，包括：
    1. 语音识别和合成
    2. 与阿里百炼平台的通信
    3. 守护进程管理
    4. 配置和日志管理
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
    
    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, parent=None):
        """
        初始化语音管理器
        
        Args:
            log_manager: 全局日志管理器实例
            config_manager: 全局配置管理器实例
            parent: QObject父对象
        """
        super().__init__(parent)
        self.logger = log_manager.get_logger(__name__)
        self.config_manager = config_manager
        
        self.logger.info("VoiceManager: 初始化中...")
        
        # 加载配置
        self._load_config()
        
        # 初始化状态
        self.dialog_id = None
        self.conversation = None
        self.is_conversation_active = False

        # 创建对话线程
        self.conversation_thread = threading.Thread(target=self.conversation_round,daemon=True,args=(2,))
        
        # 初始化音频相关
        self._init_audio()

        # 创建对话实例
        self.conversation = TMultiModalConversation(
            app_id=self.app_id,
            workspace_id=self.workspace_id,
            api_key=self.api_key,
            dialog_id=self.dialog_id,
            conversation_mode=self.conversation_mode
        )

        # 连接ChatCallback的信号（在创建对话实例之后）
        self._connect_chat_callback()

        
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
            
            # 验证必要的配置
            if not all([self.app_id, self.workspace_id, self.api_key]):
                raise ValueError("缺少必要的语音服务配置: APP_ID, WORKSPACE_ID, API_KEY")
            
            self.logger.info("语音配置加载成功")
            
        except Exception as e:
            self.logger.error(f"加载语音配置失败: {e}")
            raise
    
    def _init_audio(self):
        """初始化音频相关组件"""
        try:
            # 这里可以初始化音频设备检测等
            self.logger.info("音频组件初始化完成")
        except Exception as e:
            self.logger.warning(f"音频组件初始化警告: {e}")

    def conversation_round(self, round_number: int = 1) -> bool:
        """
        执行一轮对话
        
        Args:
            round_number: 当前对话轮次编号
            
        Returns:
            bool: 对话是否成功完成
        """
        round_num = 0
        # Run conversation rounds
        for round_num in range(MAX_CONVERSATION_ROUNDS):
            self.logger.info(f" round ----------------------: {round_num + 1}")
            
            # Start speech interaction
            if self.conversation.get_conversation_mode() != "duplex":
                self.conversation.start_speech_interaction()
            
            # 等待对话完成
            time.sleep(CONVERSATION_TIMEOUT)

            # Stop speech for push2talk mode
            if self.conversation.get_conversation_mode() == "push2talk":
                self.conversation.stop_speech_interaction()

            # 如果不是最后一轮，等待下一次Listening状态
            if round_num < MAX_CONVERSATION_ROUNDS - 1:
                self.logger.info(f"waiting for next Listening state after round {round_num + 1}...")
                
                # 等待响应结束后的下一轮对话
                if self.conversation.wait_for_listening_state(timeout=CONVERSATION_TIMEOUT):
                    self.logger.info(f"ready for next round")
                else:
                    self.logger.warning(f"timeout waiting for next Listening state, continuing anyway")
                    time.sleep(2)  # 短暂等待后继续
            else:
                # 最后一轮，等待一段时间让对话完成
                self.logger.info(f"final round completed, waiting for conversation to finish")
                time.sleep(CONVERSATION_TIMEOUT)
                
            if not self.is_conversation_active:
                break

        self.logger.info(f"conversation round completed, total round_num------------->: {round_num}")
        return round_num

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
                self.logger.error("VoiceManager: 对话实例未创建，无法开始语音对话")
                return False
            
            self.logger.info("启动语音对话...")
            
            # 设置对话状态为活跃
            self.is_conversation_active = True
            
            # 设置为语音模式
            if hasattr(self.conversation, 'callback') and self.conversation.callback:
                self.conversation.callback.set_voice_mode(True)
                self.logger.info("VoiceManager: 已设置为语音对话模式")
            
            # 开始对话
            self.conversation.start_conversation()

            # 线程启动
            self.conversation_thread.start()

            # 阻塞启动对话
            # round_num = self.conversation_round(MAX_CONVERSATION_ROUNDS)

            # 文件语音启动
            # audio_file = self.conversation._get_audio_file()
            # self.conversation._stream_audio(audio_file)  

            
            self.logger.info(f"conversation completed successfully")
            return True
            
        except KeyboardInterrupt:
            self.logger.info(f"用户中断")
            if self.conversation:
                self.conversation.stop_conversation()
            self.is_conversation_active = False
            return False
        except Exception as e:
            self.logger.error(f"错误: {e}")
            if self.conversation:
                self.conversation.stop_conversation()
            self.is_conversation_active = False
            return False

    def start_text_conversation(self) -> bool:
        """
        开始文本对话
        """
        if not self.conversation:
            self.logger.error("VoiceManager: 对话实例未创建，无法开始文本对话")
            return False
            
        try:
            # 设置为文本模式
            if hasattr(self.conversation, 'callback') and self.conversation.callback:
                self.conversation.callback.set_voice_mode(False)
                self.logger.info("VoiceManager: 已设置为文本对话模式")
            
            # 开始对话
            self.conversation.start_conversation()
            self.conversation.conversation.request_to_respond('prompt','将电机位置调大些')
            self.logger.info("VoiceManager: 文本对话启动成功")
            return True
        except Exception as e:
            self.logger.error(f"VoiceManager: 启动文本对话失败: {e}")
            return False
    
    def stop_voice_conversation(self) -> bool:
        """
        停止语音对话
        
        Returns:
            bool: 是否成功停止
        """
        try:
            if not self.is_conversation_active or not self.conversation:
                self.logger.warning("没有活跃的语音对话")
                return False
            
            self.logger.info("停止语音对话...")
            
            # 设置停止标志
            self.is_conversation_active = False
            
            # 停止对话
            try:
                self.conversation.stop_conversation()
            except Exception as e:
                self.logger.warning(f"停止对话时出错: {e}")
            
            # 清理资源
            self.conversation = None
            self.is_conversation_active = False
            self.dialog_id = None
            self.conversation_thread = None
            
            # 发送信号
            self.conversation_stopped.emit()
            self.voice_state_changed.emit("语音对话已停止")
            
            self.logger.info("语音对话已停止")
            return True
            
        except Exception as e:
            error_msg = f"停止语音对话失败: {e}"
            self.logger.error(error_msg)
            self.conversation_error.emit(error_msg)
            return False
    
    
    def get_conversation_status(self) -> Dict[str, Any]:
        """
        获取对话状态
        
        Returns:
            Dict: 包含状态信息的字典
        """
        status = {
            'is_active': self.is_conversation_active,
            'dialog_id': self.dialog_id,
            'conversation_mode': self.conversation_mode
        }
        
        if self.conversation:
            try:
                status['dialog_state'] = str(self.conversation.get_dialog_state())
            except:
                status['dialog_state'] = 'unknown'
        
        # 添加线程状态信息
        if self.conversation_thread:
            status['thread_alive'] = self.conversation_thread.is_alive()
            status['thread_name'] = self.conversation_thread.name
            status['active_flag'] = self.is_conversation_active
        else:
            status['thread_alive'] = False
            status['thread_name'] = None
            status['active_flag'] = self.is_conversation_active
        
        return status
    
    def _on_conversation_error(self, error: Exception):
        """处理对话错误"""
        error_msg = f"语音对话错误: {error}"
        self.logger.error(error_msg)
        self.conversation_error.emit(error_msg)
        self.voice_state_changed.emit(f"错误: {error}")
        
        # 自动清理状态
        self.is_conversation_active = False
        self.conversation = None
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("VoiceManager: 开始清理...")
        
        try:
            if self.is_conversation_active:
                self.stop_voice_conversation()
        except Exception as e:
            self.logger.warning(f"清理语音对话时出错: {e}")
        
        # 确保线程完全清理
        if self.conversation_thread and self.conversation_thread.is_alive():
            self.logger.info("等待剩余线程清理...")
            # 增加超时时间，让所有线程有足够时间清理
            self.conversation_thread.join(timeout=10.0)
            
            if self.conversation_thread.is_alive():
                self.logger.warning("对话线程未能在超时时间内结束")
        
        # 强制清理所有相关资源
        try:
            if hasattr(self, 'conversation') and self.conversation:
                self.conversation = None
            
            if hasattr(self, 'callback') and self.callback:
                self.callback = None
                
            # 等待一下让系统线程有时间清理
            time.sleep(1.0)
            
        except Exception as e:
            self.logger.warning(f"强制清理资源时出错: {e}")
        
        self.logger.info("VoiceManager: 清理完成")
    
    def _connect_chat_callback(self):
        """连接ChatCallback的信号"""
        if self.conversation and hasattr(self.conversation, 'callback') and self.conversation.callback:
            try:
                self.conversation.callback.voice_response_processed.connect(self._on_voice_response_processed)
                self.logger.info("VoiceManager: 已连接ChatCallback信号")
            except Exception as e:
                self.logger.warning(f"连接ChatCallback信号失败: {e}")
        else:
            self.logger.warning("VoiceManager: 无法连接ChatCallback信号，conversation或callback不可用")
    
    @Slot(dict)
    def _on_voice_response_processed(self, payload: dict):
        """处理语音响应，提取commands并发出信号"""
        try:
            if "output" in payload and "extra_info" in payload["output"]:
                extra_info = payload["output"]["extra_info"]
                commands_str = extra_info.get("commands", "[]")
                
                if commands_str and commands_str != "[]":
                    self.logger.info(f"VoiceManager: 发现commands: {commands_str}")
                    
                    # 解析commands
                    commands_list = json.loads(commands_str)
                    for command in commands_list:
                        self.logger.info(f"VoiceManager: 处理命令: {command}")
                        # 发出语音命令接收信号，让Handler接收
                        self.voice_command_received.emit(command)
                        
        except Exception as e:
            self.logger.error(f"处理语音响应时发生错误: {str(e)}")
