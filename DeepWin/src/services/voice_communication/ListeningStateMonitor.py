#!/usr/bin/env python3
# Copyright (C) Alibaba Group. All Rights Reserved.
# MIT License (https://opensource.org/licenses/MIT)

"""
音频工具类
包含音频录制器和监听状态监控器
"""

import time
import threading
import logging
from typing import Callable, Optional

import pyaudio

logger = logging.getLogger('dashscope')

# 配置常量
AUDIO_CHUNK_SIZE = 3200
AUDIO_SLEEP_INTERVAL = 0.1


class ListeningStateMonitor:
    """监控Listening状态的工具类"""
    
    def __init__(self):
        self.listening_event = threading.Event()
        self.listening_count = 0
        self.lock = threading.Lock()
    
    def on_listening_state(self):
        """当进入Listening状态时调用"""
        with self.lock:
            self.listening_count += 1
            logger.info(f"Listening state detected (count: {self.listening_count})")
            self.listening_event.set()
    
    def on_responding_ended(self):
        """当响应结束时调用，准备下一轮对话"""
        with self.lock:
            logger.info("Response ended, preparing for next round")
            self.listening_event.set()
    
    def wait_for_next_listening(self, timeout: float = 30.0) -> bool:
        """
        等待下一次Listening状态
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            bool: 是否成功等到Listening状态
        """
        # 清除当前事件状态
        self.listening_event.clear()
        
        logger.info(f"Waiting for next Listening state (timeout: {timeout}s)...")
        
        # 等待事件被设置
        success = self.listening_event.wait(timeout)
        
        if success:
            logger.info("Next Listening state detected!")
        else:
            logger.warning(f"Timeout waiting for Listening state after {timeout}s")
        
        return success
    
    def get_listening_count(self) -> int:
        """获取Listening状态的计数"""
        with self.lock:
            return self.listening_count
    
    def reset(self):
        """重置监控器状态"""
        with self.lock:
            self.listening_count = 0
            self.listening_event.clear()

