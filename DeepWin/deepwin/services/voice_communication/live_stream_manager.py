#!/usr/bin/env python3
"""
实时视频流管理器

负责管理实时视频对话功能，支持随时开启、关闭
启用电脑摄像头，每隔500ms上传一帧图像
参考官方示例run_live_ai.py实现
"""

import threading
import time
from typing import Optional, Dict, Any, Callable
from PySide6.QtCore import QObject, Signal

# 导入摄像头管理器 - 使用相对导入提高兼容性
from .camera_manager import CameraManager
from deepwin.data_management.log_manager import LogManager
from deepwin.data_management.config_manager import ConfigManager
# 导入必要的类
from dashscope.multimodal.multimodal_request_params import RequestToRespondParameters

class LiveStreamManager(QObject):
    """实时视频流管理器"""
    
    # 信号定义
    live_stream_started = Signal()      # 实时流已启动
    live_stream_stopped = Signal()      # 实时流已停止
    live_stream_error = Signal(str)     # 错误信息
    frame_sent = Signal(str)            # 帧已发送
    
    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, conversation_instance=None, parent=None):
        """
        初始化实时视频流管理器
        
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
        self.camera_manager = CameraManager(
            log_manager=log_manager,
            config_manager=config_manager,
            frame_interval=0.5, 
            parent=self
        )
        self.is_active = False
        self.video_thread_running = False
        self.video_thread = None
        
        # 连接摄像头信号
        self.camera_manager.frame_captured.connect(self._on_frame_captured)
        self.camera_manager.camera_error.connect(self._on_camera_error)
        
        self.logger.info("LiveStreamManager: 初始化完成")
    
    def set_conversation_instance(self, conversation_instance):
        """
        设置对话实例
        
        Args:
            conversation_instance: 对话实例
        """
        self.conversation_instance = conversation_instance
        self.logger.info("LiveStreamManager: 对话实例已设置")
    
    def start_live_stream(self, camera_index: int = 0) -> bool:
        """
        启动实时视频流
        
        Args:
            camera_index: 摄像头索引
            
        Returns:
            bool: 是否成功启动
        """
        try:
            if self.is_active:
                self.logger.warning("实时视频流已在运行中")
                return True
            
            if not self.conversation_instance:
                raise RuntimeError("对话实例未设置")
            
            # 启动摄像头
            if not self.camera_manager.start_camera(camera_index):
                raise RuntimeError("摄像头启动失败")
            
            # 发送切换到视频模式的指令
            self.logger.info(f"发送切换到视频模式的指令")
            self._send_connect_video_command()
            self.logger.info(f"发送切换到视频模式的指令完成")
            
            # 启动视频帧发送线程
            self.video_thread_running = True
            self.video_thread = threading.Thread(
                target=self._video_frame_sending_loop,
                daemon=True
            )
            self.video_thread.start()
            
            self.is_active = True
            self.live_stream_started.emit()
            
            self.logger.info("实时视频流已启动")
            return True
            
        except Exception as e:
            error_msg = f"启动实时视频流失败: {e}"
            self.logger.error(error_msg)
            self.live_stream_error.emit(error_msg)
            return False
    
    def stop_live_stream(self) -> bool:
        """
        停止实时视频流
        
        Returns:
            bool: 是否成功停止
        """
        try:
            if not self.is_active:
                self.logger.info("实时视频流未在运行")
                return True
            
            # 停止视频帧发送
            self.video_thread_running = False
            
            # 等待视频线程结束
            if self.video_thread and self.video_thread.is_alive():
                self.video_thread.join(timeout=3.0)
            
            # 停止摄像头
            self.camera_manager.stop_camera()
            
            self.is_active = False
            self.live_stream_stopped.emit()
            
            self.logger.info("实时视频流已停止")
            return True
            
        except Exception as e:
            error_msg = f"停止实时视频流失败: {e}"
            self.logger.error(error_msg)
            self.live_stream_error.emit(error_msg)
            return False
    
    def _send_connect_video_command(self):
        """发送切换到视频模式的指令"""
        try:
            if not self.conversation_instance:
                self.logger.error(f"对话实例未设置")
                return
            self.logger.info(f"发送切换到视频模式的指令")
            # 构造视频连接命令
            video_connect_command = [{"action": "connect", "type": "voicechat_video_channel"}]
            
            # 导入必要的类
            from dashscope.multimodal.multimodal_request_params import RequestToRespondParameters, BizParams
            
            # 发送视频连接请求
            self.conversation_instance.conversation.request_to_respond(
                "prompt", "", 
                RequestToRespondParameters(biz_params=BizParams(videos=video_connect_command))
            )
            
            self.logger.info("视频模式连接指令已发送")
            
        except Exception as e:
            self.logger.error(f"发送视频连接指令失败: {e}")
    
    def _video_frame_sending_loop(self):
        """视频帧发送循环"""
        self.logger.info("开始视频帧发送循环")
        
        try:
            while self.video_thread_running and self.is_active:
                # 等待摄像头启动
                if not self.camera_manager.is_running:
                    time.sleep(0.1)
                    continue
                
                # 获取当前摄像头帧数据
                current_frame = self.camera_manager.get_current_frame()
                if current_frame:
                    # 发送当前帧
                    self._send_video_frame(current_frame)
                    self.logger.debug("视频帧已发送")
                
                # 等待下一帧
                time.sleep(0.5)  # 500ms间隔
                
        except Exception as e:
            self.logger.error(f"视频帧发送循环错误: {e}")
        finally:
            self.logger.info("视频帧发送循环结束")
    
    def _on_frame_captured(self, frame_data: str):
        """处理摄像头捕获的帧"""
        try:
            if not self.is_active or not self.conversation_instance:
                return
            
            # 发送视频帧
            self._send_video_frame(frame_data)
            
            # 发送信号
            self.frame_sent.emit(frame_data)
            
        except Exception as e:
            self.logger.error(f"处理视频帧失败: {e}")
    
    def _send_video_frame(self, frame_data: str):
        """发送单个视频帧"""
        try:
            if not self.conversation_instance:
                return
            
            
            # 构造图片参数 - 参考官方代码格式
            image_param = {"type": "base64", "value": frame_data}
            images_params = RequestToRespondParameters(images=[image_param])
            
            # 发送视频帧 - 通过updateInfo发送
            # 注意：这里使用update_info方法，与官方代码保持一致
            self.conversation_instance.conversation.update_info(parameters=images_params)
            
            self.logger.debug("视频帧已发送")
            
        except Exception as e:
            self.logger.error(f"发送视频帧失败: {e}")
    
    def _on_camera_error(self, error_msg: str):
        """处理摄像头错误"""
        self.logger.error(f"摄像头错误: {error_msg}")
        self.live_stream_error.emit(f"摄像头错误: {error_msg}")
    
    def set_frame_interval(self, interval: float):
        """
        设置帧捕获间隔
        
        Args:
            interval: 间隔时间（秒）
        """
        self.camera_manager.set_frame_interval(interval)
        self.logger.info(f"帧捕获间隔设置为 {interval}s")
    
    def set_frame_size(self, width: int, height: int):
        """
        设置帧大小
        
        Args:
            width: 帧宽度
            height: 帧高度
        """
        self.camera_manager.set_frame_size(width, height)
        self.logger.info(f"帧大小设置为 {width}x{height}")
    
    def get_live_stream_status(self) -> Dict[str, Any]:
        """
        获取实时视频流状态
        
        Returns:
            Dict: 状态信息
        """
        status = {
            'is_active': self.is_active,
            'video_thread_running': self.video_thread_running,
            'has_conversation_instance': self.conversation_instance is not None
        }
        
        # 添加摄像头状态
        camera_status = self.camera_manager.get_camera_status()
        status.update(camera_status)
        
        return status
    
    def cleanup(self):
        """清理资源"""
        self.logger.info("LiveStreamManager: 开始清理...")
        try:
            self.stop_live_stream()
            self.camera_manager.cleanup()
        except Exception as e:
            self.logger.warning(f"清理实时视频流时出错: {e}")
        self.logger.info("LiveStreamManager: 清理完成")
