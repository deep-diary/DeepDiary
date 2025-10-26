"""
MQTT客户端管理类
提供完整的MQTT连接、发布、订阅功能管理
"""

import paho.mqtt.client as mqtt
import time
import threading
import json
from typing import Dict, List, Callable, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

# 尝试导入配置文件，如果不存在则使用默认配置
try:
    from mqtt_config import get_server_config, get_topic_template, format_topic, get_message_schema
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    def get_server_config(server_name="default"):
        return {"host": "localhost", "port": 1883, "username": None, "password": None}
    def get_topic_template(category, topic_type):
        return ""
    def format_topic(template, **kwargs):
        return template.format(**kwargs) if template else ""
    def get_message_schema(message_type):
        return {}


class ConnectionStatus(Enum):
    """连接状态枚举"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"


@dataclass
class TopicConfig:
    """主题配置类"""
    topic: str
    description: str = ""
    callback: Optional[Callable] = None
    qos: int = 0
    retain: bool = False
    enabled: bool = True


@dataclass
class MessageInfo:
    """消息信息类"""
    topic: str
    payload: Union[str, bytes, dict]
    qos: int = 0
    retain: bool = False
    timestamp: Optional[float] = None


class MQTTManager:
    """MQTT客户端管理类"""
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: int = 1883,
                 client_id: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None,
                 keepalive: int = 60,
                 auto_reconnect: bool = True,
                 reconnect_interval: int = 5,
                 debug: bool = False):
        """
        初始化MQTT管理器
        
        Args:
            host: MQTT代理服务器地址
            port: MQTT代理服务器端口
            client_id: 客户端ID，如果为None则自动生成
            username: 用户名
            password: 密码
            keepalive: 保活时间
            auto_reconnect: 是否自动重连
            reconnect_interval: 重连间隔（秒）
            debug: 是否开启调试模式
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.username = username
        self.password = password
        self.keepalive = keepalive
        self.auto_reconnect = auto_reconnect
        self.reconnect_interval = reconnect_interval
        self.debug = debug
        
        # 连接状态
        self.status = ConnectionStatus.DISCONNECTED
        self.last_error = None
        
        # 订阅主题管理
        self.subscriptions: Dict[str, TopicConfig] = {}
        
        # 发布主题管理
        self.publish_topics: Dict[str, TopicConfig] = {}
        
        # 消息队列
        self.message_queue: List[MessageInfo] = []
        self.queue_lock = threading.Lock()
        
        # 统计信息
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'connection_attempts': 0,
            'last_connect_time': None,
            'last_disconnect_time': None
        }
        
        # 创建MQTT客户端
        self.client = mqtt.Client(
            client_id=client_id,
            callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
        
        # 设置回调函数
        self._setup_callbacks()
        
        # 重连线程
        self._reconnect_thread = None
        self._stop_reconnect = threading.Event()
        
    @classmethod
    def from_config(cls, 
                   server_name: str = "default",
                   client_id: Optional[str] = None,
                   debug: bool = False,
                   **kwargs):
        """
        从配置文件创建MQTT管理器实例
        
        Args:
            server_name: 服务器配置名称
            client_id: 客户端ID
            debug: 是否开启调试模式
            **kwargs: 额外的配置参数，会覆盖配置文件中的设置
            
        Returns:
            MQTTManager: MQTT管理器实例
        """
        if not CONFIG_AVAILABLE:
            raise ImportError("mqtt_config模块不可用，请确保mqtt_config.py文件存在")
            
        # 从配置文件获取服务器配置
        config = get_server_config(server_name)
        
        # 使用kwargs中的参数覆盖配置文件中的设置
        config.update(kwargs)
        
        return cls(
            host=config.get("host", "localhost"),
            port=config.get("port", 1883),
            client_id=client_id,
            username=config.get("username"),
            password=config.get("password"),
            keepalive=config.get("keepalive", 60),
            auto_reconnect=config.get("auto_reconnect", True),
            reconnect_interval=config.get("reconnect_interval", 5),
            debug=debug
        )
        
    def _setup_callbacks(self):
        """设置MQTT回调函数"""
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.client.on_subscribe = self._on_subscribe
        self.client.on_unsubscribe = self._on_unsubscribe
        self.client.on_log = self._on_log
        
    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """连接回调"""
        if not reason_code.is_failure:
            self.status = ConnectionStatus.CONNECTED
            self.stats['last_connect_time'] = time.time()
            self._log(f"连接到MQTT代理成功: {self.host}:{self.port}")
            
            # 重新订阅所有主题
            self._resubscribe_all()
            
        else:
            self.status = ConnectionStatus.FAILED
            self.last_error = f"连接失败: {reason_code}"
            self._log(f"连接失败: {reason_code}")
            
    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        """断开连接回调"""
        self.status = ConnectionStatus.DISCONNECTED
        self.stats['last_disconnect_time'] = time.time()
        self._log(f"与MQTT代理断开连接: {reason_code}")
        
        if self.auto_reconnect and not self._stop_reconnect.is_set():
            self._start_reconnect_thread()
            
    def _on_message(self, client, userdata, message):
        """消息接收回调"""
        self.stats['messages_received'] += 1
        
        topic = message.topic
        payload = message.payload.decode('utf-8')
        
        self._log(f"收到消息: {topic} -> {payload}")
        
        # 查找对应的回调函数
        callback = None
        for config in self.subscriptions.values():
            if self._topic_matches(topic, config.topic):
                callback = config.callback
                break
                
        if callback:
            try:
                # 尝试解析JSON
                try:
                    payload_data = json.loads(payload)
                except json.JSONDecodeError:
                    payload_data = payload
                    
                callback(topic, payload_data, message)
            except Exception as e:
                self._log(f"回调函数执行错误: {e}")
        else:
            self._log(f"未找到主题 {topic} 的回调函数")
            
    def _on_publish(self, client, userdata, mid, reason_code, properties):
        """发布消息回调"""
        if not reason_code.is_failure:
            self.stats['messages_sent'] += 1
            self._log(f"消息 {mid} 发布成功")
        else:
            self._log(f"消息 {mid} 发布失败: {reason_code}")
            
    def _on_subscribe(self, client, userdata, mid, reason_codes, properties):
        """订阅回调"""
        self._log(f"订阅成功: {reason_codes}")
        
    def _on_unsubscribe(self, client, userdata, mid, reason_codes, properties):
        """取消订阅回调"""
        self._log(f"取消订阅成功: {reason_codes}")
        
    def _on_log(self, client, userdata, level, buf):
        """日志回调"""
        if self.debug:
            self._log(f"MQTT日志: {buf}")
            
    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """检查主题是否匹配模式（支持通配符）"""
        if pattern == topic:
            return True
            
        # 简单的通配符匹配
        if '+' in pattern or '#' in pattern:
            pattern_parts = pattern.split('/')
            topic_parts = topic.split('/')
            
            # 处理 # 通配符（必须在最后）
            if pattern_parts[-1] == '#':
                # 移除 # 通配符，比较前面的部分
                pattern_parts = pattern_parts[:-1]
                if len(topic_parts) < len(pattern_parts):
                    return False
                # 只比较到模式长度
                topic_parts = topic_parts[:len(pattern_parts)]
            elif len(pattern_parts) != len(topic_parts):
                return False
                
            for i, pattern_part in enumerate(pattern_parts):
                if i >= len(topic_parts):
                    return False
                    
                if pattern_part == '+':
                    continue
                elif pattern_part != topic_parts[i]:
                    return False
                    
            return True
            
        return False
        
    def _resubscribe_all(self):
        """重新订阅所有主题"""
        for name, config in self.subscriptions.items():
            if config.enabled:
                self.client.subscribe(config.topic, config.qos)
                self._log(f"重新订阅主题: {config.topic}")
                
    def _start_reconnect_thread(self):
        """启动重连线程"""
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            return
            
        self._reconnect_thread = threading.Thread(target=self._reconnect_loop, daemon=True)
        self._reconnect_thread.start()
        
    def _reconnect_loop(self):
        """重连循环"""
        while not self._stop_reconnect.is_set():
            if self.status == ConnectionStatus.DISCONNECTED:
                self.status = ConnectionStatus.RECONNECTING
                self._log(f"尝试重连到 {self.host}:{self.port}")
                
                try:
                    self.connect()
                    time.sleep(1)  # 等待连接建立
                    if self.status == ConnectionStatus.CONNECTED:
                        self._log("重连成功")
                        break
                except Exception as e:
                    self._log(f"重连失败: {e}")
                    
            time.sleep(self.reconnect_interval)
            
    def _log(self, message: str):
        """日志输出"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] MQTT: {message}")
        
    def connect(self) -> bool:
        """连接到MQTT代理"""
        try:
            self.status = ConnectionStatus.CONNECTING
            self.stats['connection_attempts'] += 1
            
            # 设置认证信息
            if self.username and self.password:
                self.client.username_pw_set(self.username, self.password)
                
            self._log(f"连接到MQTT代理: {self.host}:{self.port}")
            self.client.connect(self.host, self.port, self.keepalive)
            
            # 启动网络循环
            self.client.loop_start()
            
            # 等待连接建立
            timeout = 10
            start_time = time.time()
            while self.status == ConnectionStatus.CONNECTING and (time.time() - start_time) < timeout:
                time.sleep(0.1)
                
            return self.status == ConnectionStatus.CONNECTED
            
        except Exception as e:
            self.status = ConnectionStatus.FAILED
            self.last_error = str(e)
            self._log(f"连接失败: {e}")
            return False
            
    def disconnect(self):
        """断开连接"""
        self._stop_reconnect.set()
        
        if self._reconnect_thread:
            self._reconnect_thread.join(timeout=1)
            
        self.client.loop_stop()
        self.client.disconnect()
        self.status = ConnectionStatus.DISCONNECTED
        self._log("已断开MQTT连接")
        
    def add_subscription_from_template(self,
                                     name: str,
                                     category: str,
                                     topic_type: str,
                                     callback: Callable,
                                     description: str = "",
                                     qos: int = 0,
                                     **template_kwargs) -> bool:
        """
        使用主题模板添加订阅
        
        Args:
            name: 订阅名称
            category: 主题分类 (device, sensor, system, user)
            topic_type: 主题类型 (status, control, data, etc.)
            callback: 回调函数
            description: 描述
            qos: 服务质量等级
            **template_kwargs: 模板参数
            
        Returns:
            bool: 是否成功
        """
        if not CONFIG_AVAILABLE:
            raise ImportError("mqtt_config模块不可用，请使用add_subscription方法")
            
        template = get_topic_template(category, topic_type)
        if not template:
            raise ValueError(f"未找到主题模板: {category}/{topic_type}")
            
        topic = format_topic(template, **template_kwargs)
        return self.add_subscription(name, topic, callback, description, qos)
        
    def add_subscription(self, 
                        name: str, 
                        topic: str, 
                        callback: Callable,
                        description: str = "",
                        qos: int = 0) -> bool:
        """
        添加订阅主题
        
        Args:
            name: 订阅名称
            topic: 主题
            callback: 回调函数
            description: 描述
            qos: 服务质量等级
            
        Returns:
            bool: 是否成功
        """
        try:
            config = TopicConfig(
                topic=topic,
                description=description,
                callback=callback,
                qos=qos
            )
            
            self.subscriptions[name] = config
            
            # 如果已连接，立即订阅
            if self.status == ConnectionStatus.CONNECTED:
                self.client.subscribe(topic, qos)
                
            self._log(f"添加订阅: {name} -> {topic}")
            return True
            
        except Exception as e:
            self._log(f"添加订阅失败: {e}")
            return False
            
    def remove_subscription(self, name: str) -> bool:
        """移除订阅主题"""
        try:
            if name in self.subscriptions:
                config = self.subscriptions[name]
                
                # 如果已连接，取消订阅
                if self.status == ConnectionStatus.CONNECTED:
                    self.client.unsubscribe(config.topic)
                    
                del self.subscriptions[name]
                self._log(f"移除订阅: {name}")
                return True
            else:
                self._log(f"订阅 {name} 不存在")
                return False
                
        except Exception as e:
            self._log(f"移除订阅失败: {e}")
            return False
            
    def add_publish_topic_from_template(self,
                                      name: str,
                                      category: str,
                                      topic_type: str,
                                      description: str = "",
                                      qos: int = 0,
                                      retain: bool = False,
                                      **template_kwargs) -> bool:
        """
        使用主题模板添加发布主题
        
        Args:
            name: 发布主题名称
            category: 主题分类 (device, sensor, system, user)
            topic_type: 主题类型 (status, control, data, etc.)
            description: 描述
            qos: 服务质量等级
            retain: 是否保留消息
            **template_kwargs: 模板参数
            
        Returns:
            bool: 是否成功
        """
        if not CONFIG_AVAILABLE:
            raise ImportError("mqtt_config模块不可用，请使用add_publish_topic方法")
            
        template = get_topic_template(category, topic_type)
        if not template:
            raise ValueError(f"未找到主题模板: {category}/{topic_type}")
            
        topic = format_topic(template, **template_kwargs)
        return self.add_publish_topic(name, topic, description, qos, retain)
        
    def add_publish_topic(self, 
                         name: str, 
                         topic: str,
                         description: str = "",
                         qos: int = 0,
                         retain: bool = False) -> bool:
        """添加发布主题"""
        try:
            config = TopicConfig(
                topic=topic,
                description=description,
                qos=qos,
                retain=retain
            )
            
            self.publish_topics[name] = config
            self._log(f"添加发布主题: {name} -> {topic}")
            return True
            
        except Exception as e:
            self._log(f"添加发布主题失败: {e}")
            return False
            
    def publish(self, 
                topic_or_name: str, 
                payload: Union[str, bytes, dict],
                qos: int = 0,
                retain: bool = False) -> bool:
        """
        发布消息
        
        Args:
            topic_or_name: 主题或发布主题名称
            payload: 消息内容
            qos: 服务质量等级
            retain: 是否保留消息
            
        Returns:
            bool: 是否成功
        """
        try:
            # 检查是否是发布主题名称
            if topic_or_name in self.publish_topics:
                config = self.publish_topics[topic_or_name]
                topic = config.topic
                qos = config.qos
                retain = config.retain
            else:
                topic = topic_or_name
                
            # 处理payload
            if isinstance(payload, dict):
                payload = json.dumps(payload, ensure_ascii=False)
            elif isinstance(payload, bytes):
                payload = payload.decode('utf-8')
                
            # 发布消息
            result = self.client.publish(topic, payload, qos, retain)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self._log(f"发布消息: {topic} -> {payload}")
                return True
            else:
                self._log(f"发布消息失败: {result.rc}")
                return False
                
        except Exception as e:
            self._log(f"发布消息异常: {e}")
            return False
            
    def publish_json(self, 
                    topic_or_name: str, 
                    data: dict,
                    qos: int = 0,
                    retain: bool = False) -> bool:
        """发布JSON消息"""
        return self.publish(topic_or_name, data, qos, retain)
        
    def get_status(self) -> dict:
        """获取状态信息"""
        return {
            'status': self.status.value,
            'host': self.host,
            'port': self.port,
            'client_id': self.client_id,
            'subscriptions_count': len(self.subscriptions),
            'publish_topics_count': len(self.publish_topics),
            'stats': self.stats.copy(),
            'last_error': self.last_error
        }
        
    def get_subscriptions(self) -> Dict[str, dict]:
        """获取所有订阅信息"""
        return {
            name: {
                'topic': config.topic,
                'description': config.description,
                'qos': config.qos,
                'enabled': config.enabled
            }
            for name, config in self.subscriptions.items()
        }
        
    def get_publish_topics(self) -> Dict[str, dict]:
        """获取所有发布主题信息"""
        return {
            name: {
                'topic': config.topic,
                'description': config.description,
                'qos': config.qos,
                'retain': config.retain
            }
            for name, config in self.publish_topics.items()
        }
        
    def enable_subscription(self, name: str) -> bool:
        """启用订阅"""
        if name in self.subscriptions:
            self.subscriptions[name].enabled = True
            if self.status == ConnectionStatus.CONNECTED:
                config = self.subscriptions[name]
                self.client.subscribe(config.topic, config.qos)
            return True
        return False
        
    def disable_subscription(self, name: str) -> bool:
        """禁用订阅"""
        if name in self.subscriptions:
            self.subscriptions[name].enabled = False
            if self.status == ConnectionStatus.CONNECTED:
                config = self.subscriptions[name]
                self.client.unsubscribe(config.topic)
            return True
        return False
        
    def wait_for_messages(self, timeout: Optional[float] = None):
        """等待消息（阻塞）"""
        if timeout:
            time.sleep(timeout)
        else:
            try:
                while self.status == ConnectionStatus.CONNECTED:
                    time.sleep(1)
            except KeyboardInterrupt:
                self._log("收到中断信号，停止等待")
                
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()


# 使用示例
if __name__ == "__main__":
    # 创建MQTT管理器
    mqtt_manager = MQTTManager(
        host="34.172.161.212",
        port=1883,
        debug=True
    )
    
    # 定义回调函数
    def on_test_message(topic, payload, message):
        print(f"收到测试消息: {topic} -> {payload}")
        
    def on_status_message(topic, payload, message):
        print(f"收到状态消息: {topic} -> {payload}")
        
    # 添加订阅
    mqtt_manager.add_subscription(
        name="test_topic",
        topic="testtopic/#",
        callback=on_test_message,
        description="测试主题订阅"
    )
    
    mqtt_manager.add_subscription(
        name="status_topic", 
        topic="device/status",
        callback=on_status_message,
        description="设备状态订阅"
    )
    
    # 添加发布主题
    mqtt_manager.add_publish_topic(
        name="control_topic",
        topic="device/control",
        description="设备控制主题"
    )
    
    # 连接并测试
    if mqtt_manager.connect():
        print("连接成功！")
        
        # 发布测试消息
        for i in range(5):
            mqtt_manager.publish("testtopic/demo", f"测试消息 {i}")
            time.sleep(1)
            
        # 发布JSON消息
        mqtt_manager.publish_json("device/control", {
            "command": "restart",
            "timestamp": time.time()
        })
        
        # 等待消息
        mqtt_manager.wait_for_messages(10)
        
    else:
        print("连接失败！")
        
    # 断开连接
    mqtt_manager.disconnect()
