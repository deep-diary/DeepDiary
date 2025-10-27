#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT协议解析器
基于JSON文件动态解析协议并生成订阅配置

作者: DeepDiary Team
日期: 2025-01-27
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable


class MQTTProtocolParser:
    """MQTT协议解析器 - 基于JSON配置"""
    
    def __init__(self, protocol_file: Optional[str] = None):
        """
        初始化协议解析器
        
        Args:
            protocol_file: 协议文件路径，如果不提供则使用默认路径
        """
        if protocol_file is None:
            # 默认协议文件路径
            protocol_file = Path(__file__).parent / "mqtt_protocol.json"
        
        self.protocol_file = Path(protocol_file)
        self.protocol_data = {}
        
        # 加载协议
        self._load_protocol()
    
    def _load_protocol(self):
        """加载协议文件"""
        try:
            with open(self.protocol_file, 'r', encoding='utf-8') as f:
                self.protocol_data = json.load(f)
            print(f"协议文件已加载: {self.protocol_file}")
        except Exception as e:
            print(f"加载协议文件失败: {e}")
            self.protocol_data = {}
    
    def reload_protocol(self):
        """重新加载协议文件"""
        self._load_protocol()
    
    def get_version(self) -> str:
        """获取协议版本"""
        return self.protocol_data.get('version', 'unknown')
    
    def get_topics(self) -> Dict[str, Any]:
        """获取所有主题配置"""
        return self.protocol_data.get('topics', {})
    
    def get_topic_definitions(self) -> List[Dict[str, Any]]:
        """获取所有主题定义（用于订阅）"""
        topics = []
        
        for topic_key, topic_def in self.protocol_data.get('topics', {}).items():
            topic_name = topic_def.get('name', '')
            if topic_name:
                # 将 {client_id} 替换为 + 以支持通配符订阅
                topic_pattern = topic_name.replace('{client_id}', '+')
                
                topics.append({
                    'key': topic_key,
                    'name': topic_name,
                    'pattern': topic_pattern,
                    'description': topic_def.get('description', ''),
                    'qos': topic_def.get('qos', 0),
                    'retained': topic_def.get('retained', False),
                    'period_ms': topic_def.get('period_ms', 0),
                    'direction': topic_def.get('direction', 'sub'),
                    'fields': topic_def.get('fields', {}),
                    'categories': topic_def.get('categories', {})
                })
        
        return topics
    
    def get_subscribe_topics(self) -> List[Dict[str, Any]]:
        """获取需要订阅的主题列表"""
        all_topics = self.get_topic_definitions()
        
        # 只返回订阅类型的主题（默认或direction='sub'）
        subscribe_topics = []
        for topic in all_topics:
            direction = topic.get('direction', 'sub')
            if direction == 'sub' or 'direction' not in topic:
                subscribe_topics.append(topic)
        
        return subscribe_topics
    
    def get_publish_topics(self) -> List[Dict[str, Any]]:
        """获取需要发布主题的列表"""
        all_topics = self.get_topic_definitions()
        
        # 只返回direction='pub'的主题
        publish_topics = []
        for topic in all_topics:
            direction = topic.get('direction', 'sub')
            if direction == 'pub':
                publish_topics.append(topic)
        
        return publish_topics
    
    def extract_device_id(self, topic: str) -> Optional[str]:
        """
        从主题中提取设备ID
        
        Args:
            topic: MQTT主题，如 "device/ATK-DNESP32S3/info"
            
        Returns:
            设备ID，如果无法提取则返回None
        """
        try:
            parts = topic.split('/')
            if len(parts) >= 2 and parts[0] == 'device':
                return parts[1]
        except Exception:
            pass
        return None
    
    def get_topic_fields(self, topic_key: str) -> Dict[str, Any]:
        """获取指定主题的字段定义"""
        topics = self.protocol_data.get('topics', {})
        topic_def = topics.get(topic_key, {})
        
        # 检查是否有categories（新协议格式）
        if 'categories' in topic_def:
            return topic_def
        
        # 返回fields
        return {'fields': topic_def.get('fields', {})}
    
    def create_callback(self, topic_key: str, 
                       message_type: str,
                       handler_func: Callable) -> Callable:
        """
        创建回调函数包装器
        
        Args:
            topic_key: 主题键名（如 'device_info'）
            message_type: 消息类型（用于存储分类）
            handler_func: 实际的处理器函数
            
        Returns:
            包装后的回调函数
        """
        def callback(topic: str, payload: Dict[str, Any], message):
            # 提取设备ID
            device_id = self.extract_device_id(topic)
            
            # 准备消息信息
            message_info = {
                'topic': topic,
                'payload': payload,
                'device_id': device_id,
                'message_type': message_type,
                'topic_key': topic_key,
                'protocol': self
            }
            
            # 调用处理器
            handler_func(message_info)
        
        return callback
    
    def setup_subscriptions(self, mqtt_manager, handler_funcs: Dict[str, Callable]):
        """
        设置MQTT订阅
        
        Args:
            mqtt_manager: MQTTManager实例
            handler_funcs: 处理器函数字典，key为topic_key，value为处理器函数
        """
        topics = self.get_subscribe_topics()
        
        for topic_def in topics:
            topic_key = topic_def['key']
            topic_pattern = topic_def['pattern']
            
            # 获取对应的处理器
            handler_func = handler_funcs.get(topic_key)
            
            if handler_func:
                # 创建回调包装器
                callback = self.create_callback(topic_key, topic_key, handler_func)
                
                # 添加订阅
                success = mqtt_manager.add_subscription(
                    name=topic_key,
                    topic=topic_pattern,
                    callback=callback,
                    description=topic_def.get('description', ''),
                    qos=topic_def.get('qos', 0)
                )
                
                if success:
                    print(f"订阅成功: {topic_pattern} ({topic_def.get('description', '')})")
            else:
                print(f"警告: 未找到处理器 {topic_key}")
    
    def parse_message(self, topic_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析消息数据（根据协议定义）
        
        Args:
            topic_key: 主题键名
            payload: 原始消息数据
            
        Returns:
            解析后的消息数据
        """
        topic_def = self.protocol_data.get('topics', {}).get(topic_key, {})
        
        # 如果没有字段定义，直接返回原始数据
        if 'fields' not in topic_def and 'categories' not in topic_def:
            return payload
        
        # 检查是否有categories（device_status的特殊格式）
        if 'categories' in topic_def:
            # 新格式：包含categories，直接返回数据（categories用于定义结构）
            return payload
        else:
            # 旧格式：有fields定义
            parsed = {}
            fields = topic_def.get('fields', {})
            
            for field_key, field_def in fields.items():
                if field_key in payload:
                    parsed[field_key] = payload[field_key]
            
            return parsed


# 全局单例
_global_parser: Optional[MQTTProtocolParser] = None


def get_protocol_parser(protocol_file: Optional[str] = None) -> MQTTProtocolParser:
    """获取协议解析器单例"""
    global _global_parser
    
    if _global_parser is None:
        _global_parser = MQTTProtocolParser(protocol_file)
    
    return _global_parser


# 使用示例
if __name__ == "__main__":
    parser = MQTTProtocolParser()
    
    print(f"协议版本: {parser.get_version()}")
    
    topics = parser.get_subscribe_topics()
    print(f"\n订阅主题数量: {len(topics)}")
    
    for topic in topics:
        print(f"\n主题: {topic['key']}")
        print(f"  模式: {topic['pattern']}")
        print(f"  描述: {topic['description']}")
        print(f"  QoS: {topic['qos']}")

