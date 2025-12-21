#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebSocket Client for DeepWeb
用于与 xiaozhi-server 进行 WebSocket 通信的客户端

作者: DeepDiary Team
日期: 2025-01-27
"""

import asyncio
import websockets
import json
import threading
from typing import Optional, Callable, Dict, Any
from queue import Queue, Empty
import logging


class WebSocketClient:
    """
    WebSocket 客户端类
    
    职责：
    - 管理与 WebSocket 服务器的连接
    - 处理消息的发送和接收
    - 提供连接状态回调
    - 提供消息接收回调
    """
    
    def __init__(self, logger: logging.Logger):
        """
        初始化 WebSocket 客户端
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger
        
        # WebSocket 连接相关
        self.websocket_url = "ws://localhost:8000/xiaozhi/v1/"
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.is_connected = False
        
        # 设备配置
        self.device_id = "b4:3a:45:a8:dc:e0"
        self.client_id = "gradio-client"
        
        # 监听线程
        self.ws_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # 消息队列（用于接收消息）
        self.message_queue = Queue(maxsize=1000)
        
        # 回调函数
        self.on_message_callback: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_status_change_callback: Optional[Callable[[str], None]] = None
    
    def set_callbacks(
        self,
        on_message: Optional[Callable[[Dict[str, Any]], None]] = None,
        on_status_change: Optional[Callable[[str], None]] = None
    ):
        """
        设置回调函数
        
        Args:
            on_message: 消息接收回调函数，参数为消息字典
            on_status_change: 连接状态变化回调函数，参数为状态字符串
        """
        self.on_message_callback = on_message
        self.on_status_change_callback = on_status_change
    
    def connect(self, device_id: str, client_id: str, websocket_url: str) -> str:
        """
        连接到 WebSocket 服务器
        
        Args:
            device_id: 设备ID
            client_id: 客户端ID
            websocket_url: WebSocket URL
            
        Returns:
            连接状态消息
        """
        try:
            # 更新配置
            self.device_id = device_id
            self.client_id = client_id
            self.websocket_url = websocket_url
            
            # 断开现有连接
            if self.is_connected:
                self.disconnect()
            
            # 启动 WebSocket 监听线程
            self.stop_event.clear()
            self.ws_thread = threading.Thread(target=self._websocket_listener, daemon=True)
            self.ws_thread.start()
            
            self.logger.info(f"正在连接到 WebSocket: {websocket_url}")
            return "正在连接..."
            
        except Exception as e:
            self.logger.error(f"连接 WebSocket 时出错: {e}")
            return f"连接失败: {str(e)}"
    
    def disconnect(self) -> str:
        """
        断开 WebSocket 连接
        
        Returns:
            断开状态消息
        """
        try:
            self.stop_event.set()
            self.is_connected = False
            
            if self.ws_thread and self.ws_thread.is_alive():
                self.ws_thread.join(timeout=2.0)
            
            self.logger.info("WebSocket 连接已断开")
            if self.on_status_change_callback:
                self.on_status_change_callback("已断开连接")
            return "已断开连接"
            
        except Exception as e:
            self.logger.error(f"断开 WebSocket 时出错: {e}")
            return f"断开失败: {str(e)}"
    
    def send_message(self, message: str) -> bool:
        """
        发送消息到 WebSocket 服务器
        
        Args:
            message: 要发送的消息内容
            
        Returns:
            是否发送成功
        """
        if not message or not message.strip():
            return False
        
        if not self.is_connected or not self.websocket:
            self.logger.warning("WebSocket 未连接，无法发送消息")
            return False
        
        try:
            # 构建消息
            ws_message = {
                "type": "hello",
                "content": message.strip()
            }
            
            # 在新的事件循环中发送消息
            async def send():
                try:
                    await self.websocket.send(json.dumps(ws_message))
                    self.logger.debug(f"发送消息成功: {message}")
                except Exception as e:
                    self.logger.error(f"发送消息失败: {e}")
            
            # 运行异步发送
            asyncio.run(send())
            return True
            
        except Exception as e:
            self.logger.error(f"发送消息时出错: {e}")
            return False
    
    def get_message(self, timeout: float = 0.1) -> Optional[Dict[str, Any]]:
        """
        从消息队列获取消息（非阻塞）
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            消息字典，如果没有消息返回 None
        """
        try:
            return self.message_queue.get(timeout=timeout)
        except Empty:
            return None
    
    def _websocket_listener(self):
        """
        WebSocket 监听线程
        """
        while not self.stop_event.is_set():
            try:
                # 构建 WebSocket URL，包含查询参数
                ws_url = f"{self.websocket_url}?device-id={self.device_id}&client-id={self.client_id}"
                
                self.logger.info(f"尝试连接 WebSocket: {ws_url}")
                
                async def listen():
                    try:
                        async with websockets.connect(ws_url) as websocket:
                            self.websocket = websocket
                            self.is_connected = True
                            
                            if self.on_status_change_callback:
                                self.on_status_change_callback("已连接")
                            
                            self.logger.info("WebSocket 连接成功")
                            
                            while not self.stop_event.is_set():
                                try:
                                    # 设置超时时间
                                    message = await asyncio.wait_for(
                                        websocket.recv(),
                                        timeout=1.0
                                    )
                                    
                                    # 处理接收到的消息
                                    self._handle_message(message)
                                    
                                except asyncio.TimeoutError:
                                    # 超时，继续监听
                                    continue
                                except websockets.exceptions.ConnectionClosed:
                                    self.logger.warning("WebSocket 连接被关闭")
                                    break
                    
                    except Exception as e:
                        self.logger.error(f"WebSocket 连接出错: {e}")
                        if self.on_status_change_callback:
                            self.on_status_change_callback(f"连接失败: {str(e)}")
                        await asyncio.sleep(5)  # 等待5秒后重试
                
                # 运行异步监听
                asyncio.run(listen())
                
            except Exception as e:
                self.logger.error(f"WebSocket 监听线程出错: {e}")
                if not self.stop_event.is_set():
                    import time
                    time.sleep(5)  # 等待5秒后重试
                    
            finally:
                self.is_connected = False
                self.websocket = None
                if self.on_status_change_callback:
                    self.on_status_change_callback("未连接")
    
    def _handle_message(self, message: str):
        """
        处理接收到的 WebSocket 消息
        
        Args:
            message: 接收到的消息字符串
        """
        try:
            data = json.loads(message)
            
            # 将消息放入队列
            self.message_queue.put(data)
            
            # 调用回调函数
            if self.on_message_callback:
                self.on_message_callback(data)
                
        except json.JSONDecodeError as e:
            self.logger.error(f"解析 WebSocket 消息失败: {e}, 消息内容: {message}")
        except Exception as e:
            self.logger.error(f"处理 WebSocket 消息时出错: {e}")

