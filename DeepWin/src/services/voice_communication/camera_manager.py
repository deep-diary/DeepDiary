#!/usr/bin/env python3
"""
摄像头管理器

负责管理电脑摄像头的开启、关闭和帧捕获功能
支持非阻塞运行，通过回调函数将数据传递给主线程
"""

import cv2
import threading
import time
import base64
from typing import Optional, Callable, Dict, Any
from PySide6.QtCore import QObject, Signal, QThread
from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager

class CameraManager(QObject):
    """摄像头管理器"""
    
    # 信号定义
    frame_captured = Signal(str)  # base64编码的图像数据
    camera_error = Signal(str)    # 错误信息
    camera_status_changed = Signal(bool)  # 摄像头状态
    
    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, frame_interval: float = 0.5, parent=None):
        """
        初始化摄像头管理器
        
        Args:
            log_manager: 日志管理器实例
            config_manager: 配置管理器实例
            frame_interval: 帧捕获间隔（秒），默认500ms
            parent: QObject父对象
        """
        super().__init__(parent)
        self.log_manager = log_manager
        self.config_manager = config_manager
        self.logger = log_manager.get_logger(__name__) if log_manager else None
        
        self.frame_interval = frame_interval
        self.camera = None
        self.is_running = False
        self.capture_thread = None
        self.frame_callback = None
        
        # 摄像头参数
        self.camera_index = 0  # 默认摄像头索引
        self.frame_width = 640
        self.frame_height = 480
        self.frame_quality = 80  # JPEG质量
        
        self.logger.info("CameraManager: 初始化完成")
    
    def get_current_frame(self) -> Optional[str]:
        """
        获取当前捕获的帧数据
        
        Returns:
            str: base64编码的当前帧数据，如果没有则返回None
        """
        if hasattr(self, '_current_frame_data'):
            return self._current_frame_data
        return None

    def set_frame_callback(self, callback: Callable[[str], None]):
        """
        设置帧数据回调函数
        
        Args:
            callback: 回调函数，接收base64编码的图像数据
        """
        self.frame_callback = callback
        self.logger.info("CameraManager: 帧回调函数已设置")
    
    def start_camera(self, camera_index: int = 0) -> bool:
        """
        启动摄像头
        
        Args:
            camera_index: 摄像头索引
            
        Returns:
            bool: 是否成功启动
        """
        try:
            if self.is_running:
                self.logger.warning("摄像头已在运行中")
                return True
            
            self.camera_index = camera_index
            self.camera = cv2.VideoCapture(camera_index)
            
            if not self.camera.isOpened():
                raise RuntimeError(f"无法打开摄像头 {camera_index}")
            
            # 设置摄像头参数
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            
            self.is_running = True
            
            # 启动帧捕获线程
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                daemon=True
            )
            self.capture_thread.start()
            
            self.camera_status_changed.emit(True)
            self.logger.info(f"摄像头 {camera_index} 启动成功")
            return True
            
        except Exception as e:
            error_msg = f"启动摄像头失败: {e}"
            self.logger.error(error_msg)
            self.camera_error.emit(error_msg)
            return False
    
    def stop_camera(self) -> bool:
        """
        停止摄像头
        
        Returns:
            bool: 是否成功停止
        """
        try:
            if not self.is_running:
                self.logger.info("摄像头未在运行")
                return True
            
            self.is_running = False
            
            # 等待线程结束
            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=2.0)
            
            # 释放摄像头资源
            if self.camera:
                self.camera.release()
                self.camera = None
            
            self.camera_status_changed.emit(False)
            self.logger.info("摄像头已停止")
            return True
            
        except Exception as e:
            error_msg = f"停止摄像头失败: {e}"
            self.logger.error(error_msg)
            self.camera_error.emit(error_msg)
            return False
    
    def _capture_loop(self):
        """帧捕获循环"""
        self.logger.info("开始帧捕获循环")
        
        try:
            while self.is_running and self.camera and self.camera.isOpened():
                # 捕获帧
                ret, frame = self.camera.read()
                
                if ret:
                    # 编码为base64
                    frame_data = self._encode_frame(frame)
                    
                    # 保存当前帧数据
                    self._current_frame_data = frame_data
                    
                    # 通过回调函数发送数据
                    if self.frame_callback:
                        self.frame_callback(frame_data)
                    
                    # 发送信号
                    self.frame_captured.emit(frame_data)
                    
                    # 等待指定间隔
                    time.sleep(self.frame_interval)
                else:
                    self.logger.warning("摄像头帧捕获失败")
                    time.sleep(0.1)
                    
        except Exception as e:
            error_msg = f"帧捕获循环错误: {e}"
            self.logger.error(error_msg)
            self.camera_error.emit(error_msg)
        finally:
            self.logger.info("帧捕获循环结束")
    
    def _encode_frame(self, frame) -> str:
        """
        将OpenCV帧编码为base64字符串
        
        Args:
            frame: OpenCV帧
            
        Returns:
            str: base64编码的图像数据
        """
        try:
            # 调整帧大小
            resized_frame = cv2.resize(frame, (self.frame_width, self.frame_height))
            
            # 编码为JPEG
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.frame_quality]
            _, buffer = cv2.imencode('.jpg', resized_frame, encode_param)
            
            # 转换为base64
            frame_base64 = base64.b64encode(buffer).decode('utf-8')
            return frame_base64
            
        except Exception as e:
            self.logger.error(f"帧编码失败: {e}")
            return ""
    
    def set_frame_interval(self, interval: float):
        """
        设置帧捕获间隔
        
        Args:
            interval: 间隔时间（秒）
        """
        self.frame_interval = max(0.1, interval)  # 最小间隔100ms
        self.logger.info(f"帧捕获间隔设置为 {self.frame_interval}s")
    
    def set_frame_size(self, width: int, height: int):
        """
        设置帧大小
        
        Args:
            width: 帧宽度
            height: 帧高度
        """
        self.frame_width = max(320, width)
        self.frame_height = max(240, height)
        self.logger.info(f"帧大小设置为 {self.frame_width}x{self.frame_height}")
    
    def set_frame_quality(self, quality: int):
        """
        设置JPEG质量
        
        Args:
            quality: JPEG质量 (1-100)
        """
        self.frame_quality = max(1, min(100, quality))
        self.logger.info(f"JPEG质量设置为 {self.frame_quality}")
    
    def get_camera_status(self) -> Dict[str, Any]:
        """
        获取摄像头状态
        
        Returns:
            Dict: 状态信息
        """
        status = {
            'is_running': self.is_running,
            'camera_index': self.camera_index,
            'frame_width': self.frame_width,
            'frame_height': self.frame_height,
            'frame_interval': self.frame_interval,
            'frame_quality': self.frame_quality
        }
        
        if self.camera:
            status['is_opened'] = self.camera.isOpened()
            status['fps'] = self.camera.get(cv2.CAP_PROP_FPS)
        else:
            status['is_opened'] = False
            status['fps'] = 0
        
        return status
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("CameraManager: 开始清理...")
        try:
            self.stop_camera()
        except Exception as e:
            self.logger.warning(f"清理摄像头时出错: {e}")
        self.logger.info("CameraManager: 清理完成")
