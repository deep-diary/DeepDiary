    #!/usr/bin/env python3
# Copyright (C) Alibaba Group. All Rights Reserved.
# MIT License (https://opensource.org/licenses/MIT)

"""
音频工具类
包含音频录制器和监听状态监控器
"""

import time
import threading
from typing import Callable, Optional
from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager

import pyaudio

# 配置常量
AUDIO_CHUNK_SIZE = 3200
AUDIO_SLEEP_INTERVAL = 0.1


class AudioRecorder:
    """
    非阻塞音频录制器
    使用多线程从麦克风录制音频，并通过回调函数发送数据
    """
    
    def __init__(self, pya: pyaudio.PyAudio, log_manager: LogManager, config_manager: ConfigManager,
                 sample_rate=16000, chunk_size=AUDIO_CHUNK_SIZE, 
                 callback: Callable[[bytes], None] = None):
        '''
        初始化音频录制器
        
        参数:
        pya: pyaudio.PyAudio - PyAudio实例
        log_manager: 日志管理器实例
        config_manager: 配置管理器实例
        sample_rate: int - 音频采样率，默认16000Hz
        chunk_size: int - 音频块大小（字节数）
        callback: Callable - 音频数据回调函数，用于发送录制的音频数据
        '''
        self.pya = pya
        self.log_manager = log_manager
        self.config_manager = config_manager
        self.logger = log_manager.get_logger(__name__) 
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.callback = callback
        
        # 初始化PyAudio输入流，用于录制音频
        self.recorder_stream = pya.open(format=pyaudio.paInt16,
                channels=1,  # 单声道
                rate=sample_rate,  # 采样率
                input=True)  # 输入模式
        
        # 线程锁，用于保护状态变量
        self.status_lock = threading.Lock()
        self.status = 'stopped'  # 录制状态：recording/stopped
        
        # 录制状态控制
        self.should_record = False
        
        # 录制线程（延迟创建，避免重复启动问题）
        self.recorder_thread: Optional[threading.Thread] = None
        
    def start_recording(self):
        """开始录制音频"""
        with self.status_lock:
            if self.status == 'stopped':
                # 检查音频流是否有效
                if not self.recorder_stream or not self.recorder_stream.is_active():
                    self.logger.info("音频流无效，尝试重新初始化...")
                    if not self._reinitialize_stream():
                        self.logger.error("无法初始化音频流，录制启动失败")
                        return False
                
                self.status = 'recording'
                self.should_record = True
                
                # 创建并启动录制线程（如果不存在）
                if self.recorder_thread is None or not self.recorder_thread.is_alive():
                    self.recorder_thread = threading.Thread(target=self.recorder_loop, daemon=True)
                    self.recorder_thread.start()
                    self.logger.debug("音频录制器开始录制")
                else:
                    self.logger.debug("音频录制器已在录制中")
                
                return True
            else:
                self.logger.debug("音频录制器已在录制状态")
                return True
    
    def stop_recording(self):
        """停止录制音频"""
        with self.status_lock:
            if self.status == 'recording':
                self.status = 'stopped'
                self.should_record = False
                self.logger.debug("音频录制器停止录制")
                return True
            else:
                self.logger.debug("音频录制器已在停止状态")
                return True
    
    def recorder_loop(self):
        """
        录制循环线程
        从麦克风读取音频数据并通过回调函数发送
        """
        self.logger.debug("音频录制线程启动")
        
        while self.status != 'stopped':
            if not self.should_record:
                time.sleep(0.01)
                continue
                
            try:
                # 检查音频流是否仍然有效
                if not self.recorder_stream or not self.recorder_stream.is_active():
                    self.logger.warning("音频流已关闭，重新初始化...")
                    self._reinitialize_stream()
                    if not self.recorder_stream:
                        self.logger.error("无法重新初始化音频流，退出录制循环")
                        break
                    continue
                
                # 读取音频数据块
                audio_data = self.recorder_stream.read(self.chunk_size, exception_on_overflow=False)
                
                if audio_data and self.callback:
                    # 通过回调函数发送音频数据
                    self.callback(audio_data)
                    time.sleep(AUDIO_SLEEP_INTERVAL)
                elif not audio_data:
                    # 如果没有数据，短暂等待后继续
                    time.sleep(0.01)
                elif not self.callback:
                    self.logger.warning("音频录制器回调函数为空")
                    time.sleep(0.01)
                    
            except Exception as e:
                self.logger.error(f"录制音频时出错: {e}")
                # 尝试恢复音频流
                if "Stream closed" in str(e) or "Stream not active" in str(e):
                    self.logger.info("检测到音频流关闭，尝试恢复...")
                    if self._reinitialize_stream():
                        self.logger.info("音频流恢复成功，继续录制")
                        continue
                    else:
                        self.logger.error("音频流恢复失败，退出录制循环")
                        break
                else:
                    # 其他错误，短暂等待后继续
                    self.logger.warning(f"其他错误，等待后重试: {e}")
                    time.sleep(0.1)
                    continue
        
        self.logger.debug("音频录制线程结束")
    
    def shutdown(self):
        """
        关闭录制器
        停止录制线程并释放资源
        """
        self.logger.debug("关闭音频录制器")
        self.stop_recording()
        
        # 等待录制线程结束
        if self.recorder_thread and self.recorder_thread.is_alive():
            self.recorder_thread.join(timeout=1.0)  # 最多等待1秒
        
        # 关闭音频流
        try:
            if hasattr(self, 'recorder_stream') and self.recorder_stream:
                if self.recorder_stream.is_active():
                    self.recorder_stream.stop_stream()
                self.recorder_stream.close()
                self.recorder_stream = None
        except Exception as e:
            self.logger.error(f"关闭音频流时出错: {e}")
        
        self.logger.debug("音频录制器已关闭")
    
    def _reinitialize_stream(self) -> bool:
        """
        重新初始化音频流
        
        Returns:
            bool: 是否成功重新初始化
        """
        try:
            # 关闭旧的音频流
            if hasattr(self, 'recorder_stream') and self.recorder_stream:
                try:
                    self.recorder_stream.close()
                except Exception as e:
                    self.logger.warning(f"关闭旧音频流时出错: {e}")
            
            # 创建新的音频流
            self.recorder_stream = self.pya.open(
                format=pyaudio.paInt16,
                channels=1,  # 单声道
                rate=self.sample_rate,  # 采样率
                input=True  # 输入模式
            )
            
            self.logger.info("音频流重新初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"重新初始化音频流失败: {e}")
            self.recorder_stream = None
            return False
