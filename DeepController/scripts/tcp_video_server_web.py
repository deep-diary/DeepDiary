#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32 摄像头 TCP 视频流服务器（Web 版）
适合部署到云端服务器，通过浏览器查看视频流

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
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class VideoStreamHandler:
    """视频流处理器 - 管理接收到的视频帧"""
    
    JPEG_START = b'\xff\xd8'
    JPEG_END = b'\xff\xd9'
    
    def __init__(self):
        self.latest_frame = None
        self.frame_lock = threading.Lock()
        self.frame_count = 0
        self.client_info = None
        self.last_update = None
    
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
                    self.latest_frame = frame
                    self.frame_count += 1
                    self.last_update = time.time()
                    has_new_frame = True
        
        return buffer, has_new_frame
    
    def get_latest_frame(self):
        """获取最新的图像帧"""
        with self.frame_lock:
            return self.latest_frame.copy() if self.latest_frame is not None else None
    
    def get_jpeg_frame(self):
        """获取最新帧的 JPEG 编码"""
        frame = self.get_latest_frame()
        if frame is None:
            return None
        
        # 添加信息覆盖层
        frame = self.add_overlay(frame)
        
        # 编码为 JPEG
        _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return jpeg.tobytes()
    
    def add_overlay(self, frame):
        """添加信息覆盖层"""
        frame_copy = frame.copy()
        height, width = frame_copy.shape[:2]
        
        # 添加时间戳
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cv2.putText(frame_copy, timestamp, (10, height - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # 添加帧号
        cv2.putText(frame_copy, f"Frame: {self.frame_count}", (10, 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # 添加客户端信息
        if self.client_info:
            cv2.putText(frame_copy, f"ESP32: {self.client_info}", (10, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return frame_copy


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


class WebStreamHandler(BaseHTTPRequestHandler):
    """Web 流处理器 - 通过 HTTP 提供视频流"""
    
    stream_handler = None  # 由外部设置
    
    def do_GET(self):
        """处理 GET 请求"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/':
            # 主页
            self.send_html_page()
        elif parsed_path.path == '/stream':
            # 视频流
            self.send_video_stream()
        elif parsed_path.path == '/snapshot':
            # 截图
            self.send_snapshot()
        elif parsed_path.path == '/status':
            # 状态信息
            self.send_status()
        else:
            self.send_error(404, "File not found")
    
    def send_html_page(self):
        """发送 HTML 页面"""
        html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ESP32 摄像头监控</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1a1a1a;
            color: #fff;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: #4CAF50;
        }
        .video-container {
            text-align: center;
            margin: 20px 0;
            background-color: #000;
            padding: 10px;
            border-radius: 8px;
        }
        img {
            max-width: 100%;
            height: auto;
            border: 2px solid #4CAF50;
            border-radius: 4px;
        }
        .controls {
            text-align: center;
            margin: 20px 0;
        }
        button {
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            margin: 5px;
            cursor: pointer;
            border-radius: 4px;
            font-size: 16px;
        }
        button:hover {
            background-color: #45a049;
        }
        .status {
            background-color: #2c2c2c;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }
        .status-item {
            margin: 10px 0;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            color: #888;
            font-size: 14px;
        }
    </style>
    <script>
        function refreshImage() {
            var img = document.getElementById('videoStream');
            img.src = '/stream?' + new Date().getTime();
        }
        
        function takeSnapshot() {
            window.open('/snapshot', '_blank');
        }
        
        function updateStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('frameCount').textContent = data.frame_count;
                    document.getElementById('clientInfo').textContent = data.client_info || '未连接';
                    document.getElementById('lastUpdate').textContent = data.last_update || 'N/A';
                })
                .catch(error => console.error('Error:', error));
        }
        
        // 定期更新状态
        setInterval(updateStatus, 1000);
        
        // 页面加载时更新一次
        window.onload = updateStatus;
    </script>
</head>
<body>
    <div class="container">
        <h1>🎥 ESP32 摄像头实时监控</h1>
        
        <div class="video-container">
            <img id="videoStream" src="/stream" alt="Video Stream">
        </div>
        
        <div class="controls">
            <button onclick="refreshImage()">🔄 刷新画面</button>
            <button onclick="takeSnapshot()">📷 保存截图</button>
        </div>
        
        <div class="status">
            <h3>📊 状态信息</h3>
            <div class="status-item">
                <strong>ESP32 客户端:</strong> <span id="clientInfo">加载中...</span>
            </div>
            <div class="status-item">
                <strong>接收帧数:</strong> <span id="frameCount">0</span>
            </div>
            <div class="status-item">
                <strong>最后更新:</strong> <span id="lastUpdate">N/A</span>
            </div>
        </div>
        
        <div class="footer">
            <p>ESP32 摄像头 TCP 视频流服务器 | DeepDiary Team © 2025</p>
            <p>访问 /stream 查看原始视频流 | 访问 /snapshot 获取快照</p>
        </div>
    </div>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_video_stream(self):
        """发送 MJPEG 视频流"""
        self.send_response(200)
        self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
        self.end_headers()
        
        try:
            while True:
                jpeg_data = self.stream_handler.get_jpeg_frame()
                if jpeg_data:
                    self.wfile.write(b'--frame\r\n')
                    self.send_header('Content-type', 'image/jpeg')
                    self.send_header('Content-length', str(len(jpeg_data)))
                    self.end_headers()
                    self.wfile.write(jpeg_data)
                    self.wfile.write(b'\r\n')
                
                time.sleep(0.033)  # 约30fps
        
        except Exception as e:
            logger.error(f"发送视频流时出错: {e}")
    
    def send_snapshot(self):
        """发送快照"""
        jpeg_data = self.stream_handler.get_jpeg_frame()
        if jpeg_data:
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.send_header('Content-length', str(len(jpeg_data)))
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            self.send_header('Content-Disposition', f'attachment; filename="snapshot_{timestamp}.jpg"')
            self.end_headers()
            self.wfile.write(jpeg_data)
        else:
            self.send_error(503, "No frame available")
    
    def send_status(self):
        """发送状态信息"""
        status = {
            'frame_count': self.stream_handler.frame_count,
            'client_info': self.stream_handler.client_info,
            'last_update': datetime.fromtimestamp(self.stream_handler.last_update).strftime('%Y-%m-%d %H:%M:%S') 
                          if self.stream_handler.last_update else None
        }
        
        import json
        response = json.dumps(status)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def log_message(self, format, *args):
        """重写日志方法以使用自定义日志"""
        logger.debug("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format % args))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='ESP32 摄像头 TCP 视频流服务器（Web 版）')
    parser.add_argument('--tcp-host', default='0.0.0.0', help='TCP 监听地址')
    parser.add_argument('--tcp-port', type=int, default=8080, help='TCP 监听端口')
    parser.add_argument('--web-host', default='0.0.0.0', help='Web 服务器监听地址')
    parser.add_argument('--web-port', type=int, default=8000, help='Web 服务器监听端口')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("ESP32 摄像头 TCP 视频流服务器（Web 版）")
    logger.info("=" * 60)
    logger.info(f"TCP 接收端口: {args.tcp_port}")
    logger.info(f"Web 访问端口: {args.web_port}")
    logger.info("=" * 60)
    
    # 创建视频流处理器
    stream_handler = VideoStreamHandler()
    
    # 启动 TCP 接收服务
    tcp_receiver = TcpVideoReceiver(args.tcp_host, args.tcp_port, stream_handler)
    tcp_receiver.start()
    
    # 设置 Web 处理器的流处理器
    WebStreamHandler.stream_handler = stream_handler
    
    # 启动 Web 服务器
    try:
        web_server = HTTPServer((args.web_host, args.web_port), WebStreamHandler)
        logger.info(f"Web 服务器已启动: http://{args.web_host}:{args.web_port}")
        logger.info(f"请在浏览器中访问: http://localhost:{args.web_port}")
        logger.info("按 Ctrl+C 停止服务器")
        web_server.serve_forever()
    
    except KeyboardInterrupt:
        logger.info("\n收到键盘中断信号，正在停止...")
        tcp_receiver.stop()
        web_server.shutdown()
        logger.info("服务器已停止")


if __name__ == '__main__':
    main()

