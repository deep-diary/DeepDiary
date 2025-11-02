"""
MQTT客户端管理类 - 简化版
利用paho-mqtt的内置功能，避免过度封装
"""

import paho.mqtt.client as mqtt
import time
import json
import logging
from typing import Callable, Optional, Dict, Any, Union

from .mqtt_config_loader import MQTTConfigLoader


class MQTTManager:
    """
    MQTT客户端管理类 - 简化版
    
    设计理念：
    - 使用统一的消息回调，在应用层根据topic分发
    - 直接使用paho-mqtt的功能，避免过度封装
    - 保持简单，只封装必要的功能
    """
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: int = 1883,
                 client_id: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 keepalive: int = 60,
                 log_manager=None,
                 from_config: bool = True,
                 server_name: str = "default"):
        """
        初始化MQTT管理器
        
        Args:
            host: MQTT代理服务器地址（如果 from_config=True，会被配置覆盖）
            port: MQTT代理服务器端口（如果 from_config=True，会被配置覆盖）
            client_id: 客户端ID
            username: 用户名（如果 from_config=True，会被配置覆盖）
            password: 密码（如果 from_config=True，会被配置覆盖）
            keepalive: 保活时间（如果 from_config=True，会被配置覆盖）
            log_manager: 日志管理器实例
            from_config: 是否从配置文件加载服务器配置和自动订阅主题（默认 True）
            server_name: 服务器配置名称（仅当 from_config=True 时有效，默认 "default"）
        """
        # 设置日志（需要先设置，因为后续可能用到）
        if log_manager:
            self.logger = log_manager.get_logger(__name__)
        else:
            self.logger = logging.getLogger(__name__)
        
        # 配置加载器
        self.config_loader = MQTTConfigLoader()
        
        # 如果 from_config=True，从配置文件加载服务器配置
        if from_config:
            config = self.config_loader.get_server_config(server_name)
            
            # 使用配置文件中的值
            host = config.get("host", host)
            port = config.get("port", port)
            username = config.get("username") if username is None else username
            password = config.get("password") if password is None else password
            keepalive = config.get("keepalive", keepalive)
        
        self.host = host
        self.port = port
        self.client_id = client_id
        self.keepalive = keepalive
        
        # 连接标志位（由回调函数更新）
        self._is_connected = False
        self._message_callback: Optional[Callable] = None  # 统一的消息回调
        
        # 自动重连控制（默认启用）
        self.auto_reconnect = True
        
        # 待订阅的主题列表（连接成功后自动订阅）
        self._pending_subscriptions: list = []  # [(topic, qos), ...]
        
        # 如果 from_config=True，直接从 TOPIC_CONFIGS 列表读取主题配置
        if from_config:
            topic_configs = self.config_loader.topic_configs  # 现在是列表
            if topic_configs:
                self.logger.info(f"从配置读取到 {len(topic_configs)} 个主题配置")
                for topic_config in topic_configs:
                    topic_template = topic_config.get("name", "")
                    if not topic_template:
                        continue
                    
                    # 格式化主题名称（如果有 client_id 占位符）
                    try:
                        if "{client_id}" in topic_template:
                            topic_name = topic_template.format(client_id=self.client_id or "+")
                        else:
                            topic_name = topic_template
                    except Exception as e:
                        self.logger.error(f"格式化主题失败: {e}")
                        continue
                    
                    qos = topic_config.get("qos", 0)
                    
                    if (topic_name, qos) not in self._pending_subscriptions:
                        self._pending_subscriptions.append((topic_name, qos))
                        self.logger.info(f"主题已加入自动订阅队列: {topic_name} (QoS: {qos})")
        
        # 创建MQTT客户端
        self.client = mqtt.Client(
            client_id=client_id,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        
        # 设置认证信息
        if username and password:
            self.client.username_pw_set(username, password)
        
        # 设置回调函数
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # 统计信息
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'connection_attempts': 0,
        }
        
        # 默认自动连接
        self.connect()
        self.logger.info("MQTTManager initialized")
    
    def set_message_callback(self, callback: Callable[[str, Any, mqtt.MQTTMessage], None]):
        """
        设置统一的消息回调函数
        
        Args:
            callback: 回调函数，接收 (topic, payload, message) 参数
                - topic: 消息主题
                - payload: 解析后的payload（尝试JSON解析，失败则返回字符串）
                - message: paho-mqtt的message对象
        """
        self._message_callback = callback
        self.logger.info("消息回调已设置")
    
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """连接回调"""
        if not reason_code.is_failure:
            self._is_connected = True
            self.stats['connection_attempts'] += 1
            self.logger.info(f"连接到MQTT代理成功: {self.host}:{self.port}")
            
            # 自动订阅待订阅的主题
            if self._pending_subscriptions:
                self.logger.info(f"开始自动订阅 {len(self._pending_subscriptions)} 个待订阅主题")
                for topic, qos in self._pending_subscriptions:
                    self._do_subscribe(topic, qos)
                self._pending_subscriptions.clear()
        else:
            self._is_connected = False
            self.logger.info(f"连接失败: {reason_code}")
    
    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        """断开连接回调"""
        self._is_connected = False
        reason_str = str(reason_code)
        if hasattr(reason_code, 'getName'):
            reason_str = f"{reason_str} ({reason_code.getName()})"
        self.logger.info(f"与MQTT代理断开连接: {reason_str}")
        
        # 根据 auto_reconnect 设置决定是否停止自动重连
        # 注意：paho-mqtt的loop_start()会在断开时自动重连
        if not self.auto_reconnect:
            self.logger.info("自动重连已禁用，停止网络循环")
            try:
                self.client.loop_stop()
            except Exception as e:
                self.logger.warning(f"停止网络循环时出错: {e}")
    
    def _on_message(self, client, userdata, message):
        """
        统一的消息接收回调
        
        message对象已包含所有信息：
        - message.topic: 主题
        - message.payload: 原始payload（bytes）
        - message.qos: QoS等级
        - message.retain: 是否保留消息
        """
        self.stats['messages_received'] += 1
        
        topic = message.topic
        payload_bytes = message.payload
        
        # 尝试解析为字符串
        try:
            payload_str = payload_bytes.decode('utf-8')
        except UnicodeDecodeError:
            self.logger.warning(f"无法解码消息payload: {topic}")
            return
        
        # 尝试解析JSON
        payload = payload_str
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError:
            pass  # 保持为字符串
        
        self.logger.info(f"收到消息: {topic} -> {payload}")
        
        # 调用统一的消息回调（在应用层根据topic分发）
        if self._message_callback:
            try:
                self._message_callback(topic, payload, message)
            except Exception as e:
                self.logger.error(f"消息回调执行错误: {e}", exc_info=True)
    
    def connect(self, wait_for_connection: bool = True, timeout: float = 10.0) -> bool:
        """
        连接到MQTT代理
        
        Args:
            wait_for_connection: 是否等待连接建立（默认 True）
                                 如果为 False，立即返回 True（表示已发起连接）
                                 连接结果通过 _on_connect 回调异步通知
            timeout: 等待连接的超时时间（秒），仅在 wait_for_connection=True 时有效
            
        Returns:
            bool: 
                - 如果 wait_for_connection=True: 返回实际连接结果
                - 如果 wait_for_connection=False: 总是返回 True（表示已发起连接）
        """
        try:
            # 如果已连接，直接返回
            if self.client.is_connected():
                self._is_connected = True
                return True
            
            if self._is_connected:
                return True
            
            self.logger.info(f"连接到MQTT代理: {self.host}:{self.port}")
            
            # 连接
            self.client.connect(self.host, self.port, self.keepalive)
            
            # 启动网络循环（非阻塞，后台线程）
            # 注意：loop_start()会在断开时自动重连
            self.client.loop_start()
            
            # 根据参数决定是否等待连接建立
            if wait_for_connection:
                # 等待连接建立（等待_on_connect回调触发）
                start_time = time.time()
                while not self._is_connected and (time.time() - start_time) < timeout:
                    time.sleep(0.1)
                
                if self._is_connected:
                    self.logger.info(f"连接成功（等待时间: {time.time() - start_time:.2f}秒）")
                else:
                    self.logger.warning(f"连接超时（{timeout}秒）")
                
                return self._is_connected
            else:
                # 不等待，立即返回
                self.logger.info("已发起连接，等待异步回调通知结果")
                return True
            
        except Exception as e:
            self._is_connected = False
            self.logger.error(f"连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self._is_connected = False
            self.logger.info("已断开MQTT连接")
        except Exception as e:
            self.logger.error(f"断开连接失败: {e}")
    
    def subscribe(self, topic: str, qos: int = 0, queue_if_disconnected: bool = False) -> bool:
        """
        订阅主题
        
        Args:
            topic: 主题（支持通配符 + 和 #）
            qos: 服务质量等级
            queue_if_disconnected: 如果未连接，是否加入待订阅队列（连接成功后自动订阅）
            
        Returns:
            bool: 是否成功
        """
        # 检查连接状态
        if not self.client.is_connected():
            if queue_if_disconnected:
                # 加入待订阅队列
                if (topic, qos) not in self._pending_subscriptions:
                    self._pending_subscriptions.append((topic, qos))
                    self.logger.info(f"主题已加入待订阅队列: {topic} (QoS: {qos})")
                return True
            else:
                self.logger.warning("未连接，无法订阅")
                return False
        
        return self._do_subscribe(topic, qos)
    
    def _do_subscribe(self, topic: str, qos: int = 0) -> bool:
        """实际执行订阅操作（内部方法）"""
        try:
            result, mid = self.client.subscribe(topic, qos)
            if result == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"订阅主题: {topic} (QoS: {qos})")
                return True
            else:
                self.logger.error(f"订阅失败: {topic}, 错误码: {result}")
                return False
        except Exception as e:
            self.logger.error(f"订阅异常: {topic}, {e}")
            return False
    
    def unsubscribe(self, topic: str) -> bool:
        """取消订阅"""
        # 检查连接状态
        if not self.client.is_connected():
            return False
        
        try:
            result, mid = self.client.unsubscribe(topic)
            if result == mqtt.MQTT_ERR_SUCCESS:
                self.logger.info(f"取消订阅: {topic}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"取消订阅异常: {e}")
            return False
    
    def publish(self, topic: str, payload: Union[str, bytes, dict], qos: int = 0, retain: bool = False) -> bool:
        """
        发布消息
        
        Args:
            topic: 主题
            payload: 消息内容（str、bytes或dict）
            qos: 服务质量等级
            retain: 是否保留消息
            
        Returns:
            bool: 是否成功
        """
        # 检查连接状态
        if not self.client.is_connected():
            self.logger.warning("未连接，无法发布")
            return False
        
        try:
            # 处理payload
            if isinstance(payload, dict):
                payload_str = json.dumps(payload, ensure_ascii=False)
            elif isinstance(payload, bytes):
                payload_str = payload.decode('utf-8')
            else:
                payload_str = str(payload)
            
            # 发布消息
            result = self.client.publish(topic, payload_str, qos, retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self.stats['messages_sent'] += 1
                self.logger.info(f"发布消息: {topic} -> {payload_str[:100]}...")
                return True
            else:
                self.logger.error(f"发布失败: {topic}, 错误码: {result.rc}")
                return False
                
        except Exception as e:
            self.logger.error(f"发布消息异常: {e}")
            return False
    
    # ==================== 配置驱动的辅助方法（可选） ====================
    
    def subscribe_from_config(self, topic_key: str, client_id: str = "+") -> bool:
        """
        基于配置文件中的主题键订阅主题
        
        Args:
            topic_key: 主题键（如 "device_status", "device_info"）
            client_id: 设备ID；默认使用 '+' 通配符订阅所有设备
            
        Returns:
            bool: 是否成功
        """
        try:
            cfg = self.config_loader.get_topic_config(topic_key)
            if not cfg:
                self.logger.error(f"未找到主题配置: {topic_key}")
                return False
            
            topic = self.config_loader.format_topic_from_config(topic_key, client_id)
            qos = int(cfg.get("qos", 0))
            return self.subscribe(topic, qos)
        except Exception as e:
            self.logger.error(f"配置驱动的订阅失败: {topic_key}, {e}")
            return False
    
    def get_status(self) -> dict:
        """获取状态信息"""
        return {
            'status': 'connected' if self._is_connected else 'disconnected',
            'host': self.host,
            'port': self.port,
            'client_id': self.client_id,
            'stats': self.stats.copy(),
        }
    
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
