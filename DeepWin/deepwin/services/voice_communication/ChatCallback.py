#!/usr/bin/env python3
# Copyright (C) Alibaba Group. All Rights Reserved.
# MIT License (https://opensource.org/licenses/MIT)

"""
Multi-modal Dialog Conversation Callback Handler

This module handles callback events for multi-modal conversations with DashScope API.
"""

import json
import time
from typing import Dict, Any

from dashscope.common.logging import logger
from dashscope.multimodal.dialog_state import DialogState
from dashscope.multimodal.multimodal_dialog import MultiModalCallback
from ...data_management.log_manager import LogManager
from ...config.config_manager import ConfigManager

# 导入音频工具类
from .ListeningStateMonitor import ListeningStateMonitor

# 导入B64PCMPlayer用于音频播放
import pyaudio
from .B64PCMPlayer import B64PCMPlayer

from PySide6.QtCore import QObject, Signal

# 导入通信序列枚举
from .dashscope_com_state import CommunicationSequence, COMMUNICATION_SEQUENCE_LOGS


# Configuration constants
SAMPLE_RATE = 48000


class ChatCallback(MultiModalCallback, QObject):
    """Callback handler for multi-modal conversation events"""
    
    # 定义语音命令信号
    voice_command_received = Signal(dict)  # 语音命令接收信号 (command_data)
    voice_response_processed = Signal(dict)  # 语音响应处理完成信号 (payload)
    state_changed = Signal(DialogState)  # 对话状态变化信号
    
    def __init__(self, listening_monitor: ListeningStateMonitor, log_manager: LogManager, config_manager: ConfigManager):
        """初始化回调处理器，创建音频播放器和录制器"""
        QObject.__init__(self)
        MultiModalCallback.__init__(self)
        self.log_manager = log_manager
        self.config_manager = config_manager
        self.logger = log_manager.get_logger(__name__) if log_manager else None
        self.first_listening = True
        self.listening_monitor = listening_monitor
        self.conversation_instance = None
        
        # 初始化PyAudio
        self.pya = pyaudio.PyAudio()
        
        # 创建B64PCMPlayer实例，使用与服务器相同的采样率
        self.audio_player = B64PCMPlayer(
            pya=self.pya,
            log_manager=log_manager,
            config_manager=config_manager,
            sample_rate=SAMPLE_RATE,  # 使用与服务器相同的采样率
            chunk_size_ms=100,  # 100毫秒的音频块
            save_file=False  # 不保存文件
        )
        
        # 创建音频录制器，用于非阻塞录制
        self.audio_recorder = None  # 将在conversation中初始化
        self.conversation_instance = None  # 将在conversation中设置
        
        # 添加对话模式标识
        self.is_voice_mode = False  # 默认为文本模式
        
        self.logger.info("音频播放器初始化完成")

    def set_conversation_instance(self, conversation_instance: 'TMultiModalConversation'):
        """设置对话实例"""
        self.conversation_instance = conversation_instance

    def set_voice_mode(self, is_voice: bool):
        """设置对话模式
        
        Args:
            is_voice: True为语音模式，False为文本模式
        """
        self.is_voice_mode = is_voice
        mode_str = "语音" if is_voice else "文本"
        logger.info(f"ChatCallback: 设置为{mode_str}对话模式")
    
    def on_connected(self):
        self.logger.warning("---------------> 00: Connected to server")

    def on_started(self, dialog_id: str):
        # 保存对话ID到实例变量，而不是使用全局变量
        self.dialog_id = dialog_id
        self.log_communication_sequence(CommunicationSequence.SEQ_02_SYSTEM_STARTED)

    def on_stopped(self):
        self.log_communication_sequence(CommunicationSequence.SEQ_34_SYSTEM_STOPPED)
        # 关闭音频录制器
        if hasattr(self, 'audio_recorder') and self.audio_recorder:
            try:
                self.audio_recorder.shutdown()
            except Exception as e:
                logger.warning(f"关闭音频录制器时出错: {e}")
        # 关闭音频播放器
        if hasattr(self, 'audio_player') and self.audio_player:
            try:
                self.audio_player.shutdown()
            except Exception as e:
                logger.warning(f"关闭音频播放器时出错: {e}")
        if hasattr(self, 'pya') and self.pya:
            try:
                self.pya.terminate()
            except Exception as e:
                logger.warning(f"关闭PyAudio时出错: {e}")

    def on_state_changed(self, state: DialogState):
        
        state_messages = {
            DialogState.LISTENING: "Listening for input...",
            DialogState.THINKING: "Processing request...",
            DialogState.RESPONDING: "Generating response..."
        }
        if state in state_messages:
            logger.info(state_messages[state])
            self.state_changed.emit(state)
        
        # 监控Listening状态
        if state == DialogState.LISTENING:
            self.log_communication_sequence(CommunicationSequence.SEQ_03_DIALOG_LISTENING)
            self.listening_monitor.on_listening_state()
            
            # 只在语音模式下启动音频录制
            if self.is_voice_mode:
                logger.info("LISTENING state detected (语音模式), starting audio recording")
                if self.conversation_instance and hasattr(self, 'audio_recorder'):
                    if self.audio_recorder.start_recording():
                        logger.info("音频录制启动成功")
                    else:
                        logger.warning("音频录制启动失败")
            else:
                logger.info("LISTENING state detected (文本模式), 跳过音频录制")

        if state == DialogState.THINKING:
            self.log_communication_sequence(CommunicationSequence.SEQ_11_DIALOG_THINKING)

        if state == DialogState.RESPONDING:
            self.log_communication_sequence(CommunicationSequence.SEQ_13_DIALOG_RESPONDING)


    def on_speech_audio_data(self, data: bytes):
        """
        接收并播放音频数据
        服务器返回的音频数据会在这里被接收并播放
        """
        self.log_communication_sequence(CommunicationSequence.SEQ_16_PLAY_AUDIO)
        
        # 将接收到的音频数据直接添加到播放器
        # 注意：这里假设服务器返回的是原始PCM数据，如果是Base64编码的数据，需要使用add_data方法
        try:
            self.audio_player.add_byte_data(data)
            logger.debug(f"音频数据已添加到播放队列，数据长度: {len(data)} bytes")
        except Exception as e:
            logger.error(f"播放音频数据时出错: {e}")

    def on_error(self, error: Exception):
        self.logger.error(f"-------> Error: {error}")
        # 确保在出错时也关闭音频录制器和播放器
        try:
            if hasattr(self, 'audio_recorder') and self.audio_recorder:
                self.audio_recorder.shutdown()
        except Exception as e:
            logger.warning(f"关闭音频录制器时出错: {e}")
            
        try:
            if hasattr(self, 'audio_player') and self.audio_player:
                self.audio_player.shutdown()
        except Exception as e:
            logger.warning(f"关闭音频播放器时出错: {e}")
            
        try:
            if hasattr(self, 'pya') and self.pya:
                self.pya.terminate()
        except Exception as e:
            logger.warning(f"关闭PyAudio时出错: {e}")
        
        # 不直接退出程序，而是记录错误并通知上层
        logger.error("语音对话发生错误，请检查配置和网络连接")
        # 可以在这里发出信号通知UI层
        if hasattr(self, 'conversation_instance') and self.conversation_instance:
            try:
                # 如果conversation_instance有错误处理方法，调用它
                if hasattr(self.conversation_instance, '_on_conversation_error'):
                    self.conversation_instance._on_conversation_error(error)
            except Exception as e:
                logger.warning(f"调用错误处理方法时出错: {e}")

    def on_responding_started(self):
        self.log_communication_sequence(CommunicationSequence.SEQ_14_RESPONDING_STARTED)
        if self.conversation_instance:
            self.conversation_instance.send_local_responding_started()

    def on_responding_ended(self, payload: Dict[str, Any]):
        self.log_communication_sequence(CommunicationSequence.SEQ_17_RESPONDING_ENDED)
        
        self.audio_player.wait_for_complete() # 等待播放完成
        self.logger.warning("本地播放完成，继续等待2秒")
        time.sleep(2)

        if self.conversation_instance:
            self.conversation_instance.send_local_responding_ended()
        self.log_communication_sequence(CommunicationSequence.SEQ_19_DIALOG_LISTENING_AGAIN)
        
        # 响应结束后停止录制（仅在语音模式下）
        if self.is_voice_mode and hasattr(self, 'audio_recorder'):
            if self.audio_recorder.stop_recording():
                logger.info("Response ended, stopped audio recording")
            else:
                logger.warning("Response ended, failed to stop audio recording")
        else:
            logger.info("Response ended (文本模式), 跳过音频录制")
        
        # 响应结束后，通知ListeningStateMonitor准备下一轮对话
        self.listening_monitor.on_responding_ended()

    def on_speech_started(self):
        """处理语音开始事件"""
        self.log_communication_sequence(CommunicationSequence.SEQ_08_SPEECH_STARTED)
        if self.is_voice_mode and hasattr(self, 'audio_recorder'):
            if self.audio_recorder.start_recording():
                logger.info("语音开始，音频录制启动成功")
            else:
                logger.warning("语音开始，音频录制启动失败")
        else:
            logger.info("语音开始事件 (文本模式), 跳过音频录制")

    def on_speech_ended(self):
        """处理语音结束事件"""
        self.log_communication_sequence(CommunicationSequence.SEQ_10_SPEECH_ENDED)
        if self.is_voice_mode and hasattr(self, 'audio_recorder'):
            if self.audio_recorder.stop_recording():
                logger.info("语音结束，音频录制停止成功")
            else:
                logger.warning("语音结束，音频录制停止失败")
        else:
            logger.info("语音结束事件 (文本模式), 跳过音频录制")

    def on_speech_content(self, payload: Dict[str, Any]):
        self.log_communication_sequence(CommunicationSequence.SEQ_09_SPEECH_CONTENT)
        if payload:
            self.logger.info(f"-------> Speech content: {payload}")
            # 检查是否是语音结束事件
            if payload.get('output', {}).get('finished', False):
                if self.is_voice_mode:
                    logger.info("Speech content finished, stopping audio recording")
                    if hasattr(self, 'audio_recorder'):
                        if self.audio_recorder.stop_recording():
                            logger.info("语音内容结束，音频录制停止成功")
                        else:
                            logger.warning("语音内容结束，音频录制停止失败")
                else:
                    logger.info("Speech content finished (文本模式), 跳过音频录制")

    def on_responding_content(self, payload: Dict[str, Any]):
        self.log_communication_sequence(CommunicationSequence.SEQ_12_RESPONDING_CONTENT)
        # Response content: {
        #     "output": {
        #         "event": "RespondingContent",
        #         "text": "\u5df2\u63d0\u9ad8\u8bed\u97f3\u52a9\u624b\u97f3\u91cf",
        #         "spoken": "\u5df2\u63d0\u9ad8\u8bed\u97f3\u52a9\u624b\u97f3\u91cf",
        #         "finished": true,
        #         "extra_info": {
        #             "agent_info": {
        #             "intent_infos": [
        #                 {
        #                     "domain": "general_command",
        #                     "intent": "increase_volume_default"
        #                     }
        #                 ],
        #                 "device": {
        #                     "device_id": "demo_device_12345"
        #                 },
        #                 "round": 3
        #             },
        #             "commands": "[{\"name\":\"increase_volume_default\",\"params\":[{\"name\":\"for\",\"value\":\"\u7cfb\u7edf\",\"normValue\":\"\u7cfb\u7edf\"}]}]",
        #             "query": "\u97f3\u91cf\u8c03\u9ad8\u4e00\u70b9\u3002"
        #         },
        #         "dialog_id": "d44ccf48-3475-4b76-97dd-e566a4d61df4",
        #         "round_id": "c7e8e27efb7746779954173e75656231",
        #         "llm_request_id": "b5a834a34eb94a09a5f1d1c24966bd9b"
        #     }
        # }

        if payload:
            self.logger.info(f"-------> Response content: {json.dumps(payload, indent=4)}")
        #  格式化打印payload

        try:
            # 发出语音响应处理信号，让VoiceManager接收
            self.voice_response_processed.emit(payload)
            
        except Exception as e:
            logger.error(f"处理语音响应时发生错误: {str(e)}")
            return

    def on_request_accepted(self):
        self.log_communication_sequence(CommunicationSequence.SEQ_21_REQUEST_ACCEPTED)

    def on_close(self, close_status_code: int, close_msg: str):
        self.log_communication_sequence(CommunicationSequence.SEQ_32_USER_LEAVE)
        self.logger.info(f"-------> Connection closed - Status: {close_status_code}, Message: {close_msg}")
        # 确保在连接关闭时也关闭音频录制器和播放器
        if hasattr(self, 'audio_recorder'):
            self.audio_recorder.shutdown()
        if hasattr(self, 'audio_player'):
            self.audio_player.shutdown()
        if hasattr(self, 'pya'):
            self.pya.terminate()


    def log_communication_sequence(self, sequence: CommunicationSequence):
        """
        记录通信序列。
        将通信方向、枚举值（包含序号）和消息内容输出到日志。

        Args:
            sequence (CommunicationSequence): 要记录的通信序列枚举值。
        """
        # 获取某个状态的日志信息
        seq_log = COMMUNICATION_SEQUENCE_LOGS[sequence]
        # 同步输出枚举值，因为它包含序号信息
        self.logger.warning(f"{seq_log['direction']}: {sequence.value} - {seq_log['message']}")


