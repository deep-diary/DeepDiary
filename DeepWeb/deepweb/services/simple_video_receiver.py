#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的TCP视频接收服务
专门用于接收ESP32摄像头视频流，供Streamlit使用

作者: DeepDiary Team
日期: 2025-01-27
"""

import socket
# 延迟导入 cv2，避免 NumPy 版本兼容性问题导致模块导入失败
# cv2 将在使用时才导入
import numpy as np
import threading
import time
from datetime import datetime
from typing import Optional

class SimpleVideoReceiver:
    """简化的视频接收器"""
    
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.frame_count = 0
        self.client_info = None
        self.last_update = None
        self.is_running = False
        self.server_thread = None
        self._cv2 = None  # 延迟导入的 cv2 模块
        
        # JPEG标记
        self.JPEG_START = b'\xff\xd8'
        self.JPEG_END = b'\xff\xd9'
    
    def _ensure_cv2(self):
        """确保 cv2 模块已导入（延迟导入，避免 NumPy 版本兼容性问题）"""
        if self._cv2 is None:
            try:
                import cv2
                self._cv2 = cv2
            except Exception as e:
                print(f"警告: 无法导入 OpenCV (cv2): {e}")
                print("提示: 请安装 opencv-python-headless 并确保 NumPy 版本兼容")
                print("建议: pip install 'numpy<2' opencv-python-headless")
                self._cv2 = False  # 标记为导入失败
                return None
        return self._cv2 if self._cv2 is not False else None
    
    def start(self):
        """启动TCP接收服务"""
        if self.is_running:
            return
        
        self.is_running = True
        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()
        print(f"TCP视频接收服务已启动: {self.host}:{self.port}")
    
    def stop(self):
        """停止接收服务"""
        self.is_running = False
        if self.server_thread:
            self.server_thread.join(timeout=1)
        print("TCP视频接收服务已停止")
    
    def _run_server(self):
        """运行TCP服务器"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            print(f"等待ESP32客户端连接...")
            
            while self.is_running:
                try:
                    client_socket, client_address = server_socket.accept()
                    print(f"ESP32客户端已连接: {client_address}")
                    
                    # 更新客户端信息
                    self.client_info = f"{client_address[0]}:{client_address[1]}"
                    
                    # 处理客户端
                    threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    ).start()
                
                except Exception as e:
                    if self.is_running:
                        print(f"接受连接时出错: {e}")
        
        except Exception as e:
            print(f"启动TCP服务器失败: {e}")
        finally:
            server_socket.close()
    
    def _handle_client(self, client_socket, client_address):
        """处理客户端连接"""
        buffer = b''
        
        try:
            while self.is_running:
                data = client_socket.recv(4096)
                if not data:
                    print(f"客户端 {client_address} 断开连接")
                    break
                
                buffer += data
                buffer = self._process_data(buffer)
        
        except Exception as e:
            print(f"处理客户端时出错: {e}")
        finally:
            client_socket.close()
            print(f"客户端 {client_address} 已断开")
    
    def _process_data(self, buffer):
        """处理接收到的数据，提取JPEG帧"""
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
            
            # 提取JPEG数据
            jpeg_data = buffer[start_idx:end_idx + 2]
            buffer = buffer[end_idx + 2:]
            
            # 解码图像
            try:
                cv2 = self._ensure_cv2()
                if cv2 is None:
                    # OpenCV 未安装，跳过解码
                    continue
                
                img_array = np.frombuffer(jpeg_data, dtype=np.uint8)
                frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    with self.frame_lock:
                        self.latest_frame = frame
                        self.frame_count += 1
                        self.last_update = time.time()
                    
                    # 每100帧显示一次统计
                    if self.frame_count % 100 == 0:
                        print(f"已接收 {self.frame_count} 帧")
            
            except Exception as e:
                print(f"解码图像失败: {e}")
        
        return buffer
    
    def get_latest_frame(self):
        """获取最新的图像帧"""
        with self.frame_lock:
            if self.latest_frame is not None:
                return self.latest_frame.copy()
            else:
                return None
    
    def get_frame_count(self):
        """获取帧数"""
        return self.frame_count
    
    def get_client_info(self):
        """获取客户端信息"""
        return self.client_info
    
    def get_last_update(self):
        """获取最后更新时间"""
        return self.last_update
    
    def is_connected(self):
        """检查是否有客户端连接"""
        return self.client_info is not None and self.frame_count > 0


# 全局视频接收器实例
video_receiver = SimpleVideoReceiver()

def get_video_receiver():
    """获取全局视频接收器实例"""
    return video_receiver

def start_video_service():
    """启动视频服务"""
    video_receiver.start()

def stop_video_service():
    """停止视频服务"""
    video_receiver.stop()

if __name__ == "__main__":
    # 测试代码
    receiver = SimpleVideoReceiver()
    
    try:
        receiver.start()
        print("视频接收服务运行中，按Ctrl+C停止...")
        
        while True:
            time.sleep(1)
            if receiver.is_connected():
                print(f"状态: 已连接, 帧数: {receiver.get_frame_count()}")
            else:
                print("状态: 等待连接...")
    
    except KeyboardInterrupt:
        print("\n正在停止服务...")
        receiver.stop()
        print("服务已停止")
