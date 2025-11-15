#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32 摄像头 TCP 视频流服务器（RTSP推流版）
接收TCP客户端发送的JPEG帧，推送到MediaMTX流媒体服务器

作者: DeepDiary Team
日期: 2025-10-23
"""

import socket
import cv2
import numpy as np
import argparse
import logging
import threading
import time
import subprocess
from datetime import datetime
from queue import Queue
from typing import Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class VideoStreamHandler:
    """视频流处理器 - 管理接收到的视频帧并推送到RTSP服务器"""
    
    JPEG_START = b'\xff\xd8'
    JPEG_END = b'\xff\xd9'
    
    def __init__(self, frame_queue_size=10):
        self.frame_lock = threading.Lock()
        self.frame_count = 0
        self.client_info = None
        self.last_update = None
        # 帧队列用于推流
        self.frame_queue = Queue(maxsize=frame_queue_size)
        # 图像尺寸（首次接收到帧时确定）
        self.frame_width = None
        self.frame_height = None
    
    def process_data(self, buffer):
        """
        处理接收到的数据，提取 JPEG 帧
        
        Args:
            buffer: 数据缓冲区
            
        Returns:
            tuple: (剩余缓冲区, 是否有新帧)
        """
        has_new_frame = False
        
        while True:
            # 查找起始标记
            start_idx = buffer.find(self.JPEG_START)
            if start_idx == -1:
                buffer = buffer[-2:] if len(buffer) >= 2 else buffer
                break
            
            # 查找结束标记
            end_idx = buffer.find(self.JPEG_END, start_idx + 2)
            if end_idx == -1:
                buffer = buffer[start_idx:]
                break
            
            # 提取 JPEG 数据
            jpeg_data = buffer[start_idx:end_idx + 2]
            buffer = buffer[end_idx + 2:]
            
            # 解码图像
            img_array = np.frombuffer(jpeg_data, dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if frame is not None:
                with self.frame_lock:
                    self.frame_count += 1
                    self.last_update = time.time()
                    has_new_frame = True
                    
                    # 首次接收时确定图像尺寸
                    if self.frame_width is None or self.frame_height is None:
                        self.frame_height, self.frame_width = frame.shape[:2]
                        logger.info(f"检测到图像尺寸: {self.frame_width}x{self.frame_height}")
                
                # 将帧添加到队列（非阻塞，如果队列满则丢弃旧帧）
                if not self.frame_queue.full():
                    self.frame_queue.put(frame.copy())
                else:
                    # 队列满时，丢弃最旧的帧，添加新帧
                    try:
                        self.frame_queue.get_nowait()
                        self.frame_queue.put(frame.copy())
                    except:
                        pass
        
        return buffer, has_new_frame
    
    def get_frame(self, timeout=1.0):
        """从队列获取帧（用于推流）"""
        try:
            return self.frame_queue.get(timeout=timeout)
        except:
            return None


class RTSPPusher:
    """RTSP推流器 - 将视频帧推送到MediaMTX服务器"""
    
    def __init__(self, server_host='35.192.64.247', server_port=8554, stream_name='camera_stream'):
        self.server_host = server_host
        self.server_port = server_port
        self.stream_name = stream_name
        self.rtsp_url = f'rtsp://{server_host}:{server_port}/{stream_name}'
        
        self.is_streaming = False
        self.is_initialized = False
        self.process: Optional[subprocess.Popen] = None
        self.push_thread = None
        self.frame_width = None
        self.frame_height = None
        self.fps = 30
        self.stream_handler = None
    
    def start(self, stream_handler):
        """启动推流器（后台等待第一帧后自动开始推流）"""
        if self.is_streaming:
            logger.warning("推流已在进行中")
            return False
        
        self.stream_handler = stream_handler
        self.is_streaming = True
        # 启动后台线程，等待第一帧后自动开始推流
        self.push_thread = threading.Thread(target=self._wait_and_push, daemon=True)
        self.push_thread.start()
        logger.info("RTSP推流器已启动，等待第一帧...")
        return True
    
    def _wait_and_push(self):
        """等待第一帧后开始推流"""
        # 持续等待第一帧（不设置超时）
        while self.is_streaming and not self.is_initialized:
            frame = self.stream_handler.get_frame(timeout=1.0)
            if frame is not None:
                # 获取到第一帧，确定图像尺寸
                self.frame_height, self.frame_width = frame.shape[:2]
                logger.info(f"收到第一帧，图像尺寸: {self.frame_width}x{self.frame_height}")
                logger.info(f"开始推流到: {self.rtsp_url}")
                
                # 将第一帧放回队列
                self.stream_handler.frame_queue.put(frame)
                
                # 标记已初始化
                self.is_initialized = True
                break
        
        if self.is_initialized:
            # 开始推流
            self._push_frames()
    
    def _push_frames(self):
        """推流线程 - 从队列获取帧并推送到RTSP服务器"""
        # 构建FFmpeg命令
        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'rawvideo',
            '-pix_fmt', 'bgr24',
            '-s', f'{self.frame_width}x{self.frame_height}',
            '-r', str(self.fps),
            '-i', 'pipe:',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-crf', '23',
            '-pix_fmt', 'yuv420p',
            '-g', str(self.fps),
            '-keyint_min', str(self.fps // 2),
            '-f', 'rtsp',
            '-rtsp_transport', 'tcp',
            self.rtsp_url
        ]
        
        try:
            logger.info(f"启动FFmpeg推流到: {self.rtsp_url}")
            self.process = subprocess.Popen(
                ffmpeg_cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            push_count = 0
            last_stats_time = time.time()
            
            while self.is_streaming:
                # 从队列获取帧
                frame = self.stream_handler.get_frame(timeout=1.0)
                if frame is None:
                    continue
                
                # 确保帧尺寸匹配
                if frame.shape[:2] != (self.frame_height, self.frame_width):
                    frame = cv2.resize(frame, (self.frame_width, self.frame_height))
                
                try:
                    # 发送帧到FFmpeg
                    self.process.stdin.write(frame.tobytes())
                    self.process.stdin.flush()
                    push_count += 1
                    
                    # 每5秒显示一次统计
                    current_time = time.time()
                    if current_time - last_stats_time >= 5.0:
                        logger.info(f"已推送 {push_count} 帧到RTSP服务器")
                        last_stats_time = current_time
                
                except BrokenPipeError:
                    logger.error("FFmpeg管道断开，检查FFmpeg进程状态")
                    if self.process.poll() is not None:
                        stdout, stderr = self.process.communicate()
                        logger.error(f"FFmpeg进程退出，退出码: {self.process.returncode}")
                        if stderr:
                            logger.error(f"FFmpeg错误: {stderr.decode('utf-8', errors='ignore')}")
                    break
                except Exception as e:
                    logger.error(f"发送帧失败: {e}")
                    break
        
        except Exception as e:
            logger.error(f"推流线程异常: {e}")
        finally:
            self.is_streaming = False
            if self.process:
                try:
                    self.process.stdin.close()
                    self.process.terminate()
                    self.process.wait(timeout=5)
                except:
                    self.process.kill()
                self.process = None
            logger.info("推流已停止")
    
    def stop(self):
        """停止推流"""
        if not self.is_streaming:
            return
        
        logger.info("停止RTSP推流...")
        self.is_streaming = False
        
        if self.push_thread:
            self.push_thread.join(timeout=5)
        
        if self.process:
            try:
                self.process.stdin.close()
                self.process.terminate()
                self.process.wait(timeout=5)
            except:
                self.process.kill()
            self.process = None


class TcpVideoReceiver:
    """TCP 视频接收器"""
    
    def __init__(self, host='0.0.0.0', port=8080, stream_handler=None):
        self.host = host
        self.port = port
        self.stream_handler = stream_handler or VideoStreamHandler()
        self.is_running = False
        self.server_thread = None
    
    def start(self):
        """启动 TCP 接收服务"""
        self.is_running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        logger.info(f"TCP 接收服务已启动: {self.host}:{self.port}")
    
    def _run_server(self):
        """运行 TCP 服务器"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        
        logger.info(f"等待 ESP32 客户端连接...")
        
        while self.is_running:
            try:
                client_socket, client_address = server_socket.accept()
                logger.info(f"ESP32 客户端已连接: {client_address}")
                
                # 更新客户端信息
                self.stream_handler.client_info = f"{client_address[0]}:{client_address[1]}"
                
                # 处理客户端
                threading.Thread(
                    target=self._handle_client,
                    args=(client_socket, client_address),
                    daemon=True
                ).start()
            
            except Exception as e:
                if self.is_running:
                    logger.error(f"接受连接时出错: {e}")
    
    def _handle_client(self, client_socket, client_address):
        """处理客户端连接"""
        buffer = b''
        
        try:
            while self.is_running:
                data = client_socket.recv(4096)
                if not data:
                    logger.warning(f"客户端 {client_address} 断开连接")
                    break
                
                buffer += data
                buffer, has_new_frame = self.stream_handler.process_data(buffer)
                
                # 每100帧显示一次统计
                if has_new_frame and self.stream_handler.frame_count % 100 == 0:
                    logger.info(f"已接收 {self.stream_handler.frame_count} 帧")
        
        except Exception as e:
            logger.error(f"处理客户端时出错: {e}")
        finally:
            client_socket.close()
            logger.info(f"客户端 {client_address} 已断开")
    
    def stop(self):
        """停止接收服务"""
        self.is_running = False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='ESP32 摄像头 TCP 视频流服务器（RTSP推流版）')
    parser.add_argument('--tcp-host', default='0.0.0.0', help='TCP 监听地址')
    parser.add_argument('--tcp-port', type=int, default=8080, help='TCP 监听端口')
    parser.add_argument('--rtsp-host', default='35.192.64.247', help='MediaMTX RTSP 服务器地址')
    parser.add_argument('--rtsp-port', type=int, default=8554, help='MediaMTX RTSP 服务器端口')
    parser.add_argument('--stream-name', default='camera_stream', help='RTSP 流名称')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("ESP32 摄像头 TCP 视频流服务器（RTSP推流版）")
    logger.info("=" * 60)
    logger.info(f"TCP 接收地址: {args.tcp_host}:{args.tcp_port}")
    logger.info(f"RTSP 推流地址: rtsp://{args.rtsp_host}:{args.rtsp_port}/{args.stream_name}")
    logger.info("=" * 60)
    
    # 创建视频流处理器
    stream_handler = VideoStreamHandler()
    
    # 创建 RTSP 推流器
    rtsp_pusher = RTSPPusher(
        server_host=args.rtsp_host,
        server_port=args.rtsp_port,
        stream_name=args.stream_name
    )
    
    # 启动 TCP 接收服务
    tcp_receiver = TcpVideoReceiver(args.tcp_host, args.tcp_port, stream_handler)
    tcp_receiver.start()
    
    # 启动 RTSP 推流器（后台等待第一帧后自动开始推流）
    rtsp_pusher.start(stream_handler)
    
    logger.info("服务器已启动，等待TCP客户端连接...")
    logger.info("收到第一帧后将自动开始推流到RTSP服务器")
    logger.info("按 Ctrl+C 停止服务器")
    
    try:
        # 保持运行，等待客户端连接
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("\n收到键盘中断信号，正在停止...")
    except Exception as e:
        logger.error(f"运行时出错: {e}")
    finally:
        logger.info("正在停止服务...")
        rtsp_pusher.stop()
        tcp_receiver.stop()
        logger.info("服务器已停止")


if __name__ == '__main__':
    main()

