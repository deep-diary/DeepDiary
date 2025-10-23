#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32 摄像头 TCP 视频流接收服务器
支持接收连续的 JPEG 图像帧并实时显示

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

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class TcpVideoServer:
    """TCP 视频流接收服务器"""
    
    # JPEG 文件标记
    JPEG_START = b'\xff\xd8'  # JPEG 起始标记
    JPEG_END = b'\xff\xd9'    # JPEG 结束标记
    
    def __init__(self, host='0.0.0.0', port=8080, save_video=False, save_dir='recordings'):
        """
        初始化 TCP 视频服务器
        
        Args:
            host: 监听地址，默认 0.0.0.0 (所有网卡)
            port: 监听端口，默认 8080
            save_video: 是否保存视频
            save_dir: 视频保存目录
        """
        self.host = host
        self.port = port
        self.save_video = save_video
        self.save_dir = Path(save_dir)
        
        self.server_socket = None
        self.is_running = False
        self.client_count = 0
        
        # 视频保存相关
        self.video_writer = None
        self.frame_count = 0
        self.fps = 30  # 假设帧率
        
        # 统计信息
        self.total_frames = 0
        self.total_bytes = 0
        self.start_time = None
        
        # 创建保存目录
        if self.save_video:
            self.save_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"视频保存目录: {self.save_dir.absolute()}")
    
    def start(self):
        """启动服务器"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self.is_running = True
            logger.info(f"TCP 视频服务器已启动")
            logger.info(f"监听地址: {self.host}:{self.port}")
            logger.info(f"等待 ESP32 客户端连接...")
            
            while self.is_running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    self.client_count += 1
                    logger.info(f"客户端已连接: {client_address} (总连接数: {self.client_count})")
                    
                    # 为每个客户端创建处理线程
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address),
                        daemon=True
                    )
                    client_thread.start()
                    
                except Exception as e:
                    if self.is_running:
                        logger.error(f"接受连接时出错: {e}")
        
        except Exception as e:
            logger.error(f"启动服务器失败: {e}")
        finally:
            self.stop()
    
    def handle_client(self, client_socket, client_address):
        """
        处理客户端连接
        
        Args:
            client_socket: 客户端套接字
            client_address: 客户端地址
        """
        buffer = b''
        window_name = f"ESP32 Camera - {client_address[0]}:{client_address[1]}"
        
        self.start_time = time.time()
        self.frame_count = 0
        
        # 初始化视频写入器
        if self.save_video:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            video_file = self.save_dir / f"esp32_video_{timestamp}.mp4"
            # 暂时使用占位尺寸，收到第一帧后更新
            self.video_writer = None
            logger.info(f"准备保存视频到: {video_file}")
        
        try:
            while self.is_running:
                # 接收数据
                data = client_socket.recv(4096)
                if not data:
                    logger.warning(f"客户端 {client_address} 断开连接")
                    break
                
                buffer += data
                self.total_bytes += len(data)
                
                # 查找完整的 JPEG 帧
                while True:
                    # 查找 JPEG 起始标记
                    start_idx = buffer.find(self.JPEG_START)
                    if start_idx == -1:
                        # 没有找到起始标记，保留最后2字节（可能是被截断的标记）
                        buffer = buffer[-2:] if len(buffer) >= 2 else buffer
                        break
                    
                    # 从起始标记之后查找结束标记
                    end_idx = buffer.find(self.JPEG_END, start_idx + 2)
                    if end_idx == -1:
                        # 没有找到结束标记，保留从起始标记开始的所有数据
                        buffer = buffer[start_idx:]
                        break
                    
                    # 提取完整的 JPEG 帧 (包含结束标记的2字节)
                    jpeg_data = buffer[start_idx:end_idx + 2]
                    buffer = buffer[end_idx + 2:]  # 移除已处理的数据
                    
                    # 解码并显示图像
                    self.process_frame(jpeg_data, window_name, client_address, video_file if self.save_video else None)
                
        except Exception as e:
            logger.error(f"处理客户端 {client_address} 时出错: {e}")
        finally:
            # 清理资源
            client_socket.close()
            cv2.destroyWindow(window_name)
            
            if self.video_writer:
                self.video_writer.release()
                logger.info(f"视频已保存，共 {self.frame_count} 帧")
            
            # 显示统计信息
            if self.start_time:
                elapsed = time.time() - self.start_time
                avg_fps = self.frame_count / elapsed if elapsed > 0 else 0
                avg_bandwidth = (self.total_bytes / elapsed / 1024) if elapsed > 0 else 0
                logger.info(f"连接统计 - 帧数: {self.frame_count}, "
                          f"平均帧率: {avg_fps:.2f} fps, "
                          f"平均带宽: {avg_bandwidth:.2f} KB/s")
            
            logger.info(f"客户端 {client_address} 已断开")
    
    def process_frame(self, jpeg_data, window_name, client_address, video_file=None):
        """
        处理接收到的 JPEG 帧
        
        Args:
            jpeg_data: JPEG 图像数据
            window_name: OpenCV 窗口名称
            client_address: 客户端地址
            video_file: 视频文件路径（如果需要保存）
        """
        try:
            # 解码 JPEG
            img_array = np.frombuffer(jpeg_data, dtype=np.uint8)
            frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            
            if frame is None:
                logger.warning(f"解码 JPEG 失败，数据长度: {len(jpeg_data)}")
                return
            
            self.frame_count += 1
            self.total_frames += 1
            
            # 添加信息到图像
            frame_with_info = self.add_overlay_info(frame, client_address)
            
            # 显示图像
            cv2.imshow(window_name, frame_with_info)
            
            # 保存视频
            if self.save_video:
                if self.video_writer is None:
                    # 第一次收到帧，初始化视频写入器
                    height, width = frame.shape[:2]
                    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    self.video_writer = cv2.VideoWriter(
                        str(video_file), fourcc, self.fps, (width, height)
                    )
                    logger.info(f"视频写入器已初始化: {width}x{height} @ {self.fps}fps")
                
                self.video_writer.write(frame)
            
            # 按键处理
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                logger.info("用户请求退出")
                self.is_running = False
            elif key == ord('s'):
                # 保存截图
                screenshot_dir = Path('screenshots')
                screenshot_dir.mkdir(exist_ok=True)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                screenshot_file = screenshot_dir / f"screenshot_{timestamp}.jpg"
                cv2.imwrite(str(screenshot_file), frame)
                logger.info(f"截图已保存: {screenshot_file}")
            
            # 每100帧显示一次统计
            if self.frame_count % 100 == 0:
                elapsed = time.time() - self.start_time
                current_fps = self.frame_count / elapsed if elapsed > 0 else 0
                logger.info(f"已接收 {self.frame_count} 帧, 当前帧率: {current_fps:.2f} fps")
        
        except Exception as e:
            logger.error(f"处理帧时出错: {e}")
    
    def add_overlay_info(self, frame, client_address):
        """
        在图像上添加信息覆盖层
        
        Args:
            frame: 原始图像
            client_address: 客户端地址
            
        Returns:
            添加了信息的图像
        """
        frame_copy = frame.copy()
        height, width = frame_copy.shape[:2]
        
        # 计算实时帧率
        if self.start_time:
            elapsed = time.time() - self.start_time
            current_fps = self.frame_count / elapsed if elapsed > 0 else 0
        else:
            current_fps = 0
        
        # 添加半透明黑色背景
        overlay = frame_copy.copy()
        cv2.rectangle(overlay, (0, 0), (width, 60), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.5, frame_copy, 0.5, 0, frame_copy)
        
        # 添加文本信息
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        color = (255, 255, 255)
        thickness = 1
        
        # 第一行：客户端信息
        text1 = f"ESP32: {client_address[0]}:{client_address[1]}"
        cv2.putText(frame_copy, text1, (10, 20), font, font_scale, color, thickness)
        
        # 第二行：帧率和帧数
        text2 = f"FPS: {current_fps:.1f} | Frame: {self.frame_count}"
        cv2.putText(frame_copy, text2, (10, 40), font, font_scale, color, thickness)
        
        # 添加时间戳
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        text_size = cv2.getTextSize(timestamp, font, font_scale, thickness)[0]
        cv2.putText(frame_copy, timestamp, (width - text_size[0] - 10, 20), 
                   font, font_scale, color, thickness)
        
        return frame_copy
    
    def stop(self):
        """停止服务器"""
        logger.info("正在停止服务器...")
        self.is_running = False
        
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
        
        cv2.destroyAllWindows()
        logger.info("服务器已停止")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='ESP32 摄像头 TCP 视频流接收服务器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 基本使用（监听所有网卡，端口8080）
  python tcp_video_server.py
  
  # 指定端口
  python tcp_video_server.py --port 9090
  
  # 保存视频
  python tcp_video_server.py --save-video
  
  # 指定保存目录
  python tcp_video_server.py --save-video --save-dir /path/to/recordings
  
  # 指定监听地址和端口
  python tcp_video_server.py --host 192.168.1.100 --port 8080

快捷键:
  q - 退出程序
  s - 保存当前帧截图
        """
    )
    
    parser.add_argument('--host', default='0.0.0.0',
                       help='监听地址 (默认: 0.0.0.0 监听所有网卡)')
    parser.add_argument('--port', type=int, default=8080,
                       help='监听端口 (默认: 8080)')
    parser.add_argument('--save-video', action='store_true',
                       help='保存接收到的视频')
    parser.add_argument('--save-dir', default='recordings',
                       help='视频保存目录 (默认: recordings)')
    parser.add_argument('--fps', type=int, default=30,
                       help='保存视频的帧率 (默认: 30)')
    parser.add_argument('--log-level', default='INFO',
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='日志级别 (默认: INFO)')
    
    args = parser.parse_args()
    
    # 设置日志级别
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # 显示启动信息
    logger.info("=" * 60)
    logger.info("ESP32 摄像头 TCP 视频流接收服务器")
    logger.info("=" * 60)
    logger.info(f"监听地址: {args.host}")
    logger.info(f"监听端口: {args.port}")
    logger.info(f"保存视频: {'是' if args.save_video else '否'}")
    if args.save_video:
        logger.info(f"保存目录: {args.save_dir}")
        logger.info(f"视频帧率: {args.fps} fps")
    logger.info("=" * 60)
    logger.info("按 'q' 键退出程序")
    logger.info("按 's' 键保存当前帧截图")
    logger.info("=" * 60)
    
    # 创建并启动服务器
    server = TcpVideoServer(
        host=args.host,
        port=args.port,
        save_video=args.save_video,
        save_dir=args.save_dir
    )
    server.fps = args.fps
    
    try:
        server.start()
    except KeyboardInterrupt:
        logger.info("\n收到键盘中断信号")
        server.stop()
    except Exception as e:
        logger.error(f"服务器运行时出错: {e}")
        server.stop()


if __name__ == '__main__':
    main()

