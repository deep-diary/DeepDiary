#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESP32 摄像头 TCP 视频流接收服务器（简化版）
快速测试用，无复杂功能

作者: DeepDiary Team
日期: 2025-10-23
"""

import socket
import cv2
import numpy as np

# 配置
HOST = '0.0.0.0'  # 监听所有网卡
PORT = 8080       # 监听端口

# JPEG 标记
JPEG_START = b'\xff\xd8'
JPEG_END = b'\xff\xd9'

def main():
    # 创建服务器
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(1)
    
    print(f"TCP 服务器启动，监听 {HOST}:{PORT}")
    print("等待 ESP32 连接...")
    
    # 等待连接
    client, addr = server.accept()
    print(f"客户端已连接: {addr}")
    
    buffer = b''
    frame_count = 0
    
    try:
        while True:
            # 接收数据
            data = client.recv(4096)
            if not data:
                print("连接断开")
                break
            
            buffer += data
            
            # 查找并处理 JPEG 帧
            while True:
                # 查找起始标记
                start_idx = buffer.find(JPEG_START)
                if start_idx == -1:
                    buffer = buffer[-2:] if len(buffer) >= 2 else buffer
                    break
                
                # 查找结束标记
                end_idx = buffer.find(JPEG_END, start_idx + 2)
                if end_idx == -1:
                    buffer = buffer[start_idx:]
                    break
                
                # 提取 JPEG 数据
                jpeg_data = buffer[start_idx:end_idx + 2]
                buffer = buffer[end_idx + 2:]
                
                # 解码并显示
                img_array = np.frombuffer(jpeg_data, dtype=np.uint8)
                frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                
                if frame is not None:
                    frame_count += 1
                    
                    # 添加帧号
                    cv2.putText(frame, f"Frame: {frame_count}", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    
                    # 显示
                    cv2.imshow('ESP32 Camera', frame)
                    
                    # 按 'q' 退出
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        print("退出程序")
                        return
                    
                    # 每100帧显示一次
                    if frame_count % 100 == 0:
                        print(f"已接收 {frame_count} 帧")
    
    except KeyboardInterrupt:
        print("\n程序中断")
    
    finally:
        client.close()
        server.close()
        cv2.destroyAllWindows()
        print(f"总共接收 {frame_count} 帧")

if __name__ == '__main__':
    main()

