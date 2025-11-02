"""
MQTT 配置解析与访问类
集中封装对 mqtt_config.py 的读取与访问，避免在其他模块中散落导入多处函数。
所有函数逻辑都在此类中实现，直接读取 mqtt_config.py 中的常量字典。
"""

from typing import Dict, Any, Optional
from pathlib import Path
import json


class MQTTConfigLoader:
    """封装 mqtt_config 的读取与访问方法。所有逻辑在类中实现。"""

    def __init__(self) -> None:
        # 延迟导入，确保打包/运行环境下模块路径稳定
        from . import mqtt_config as cfg  # type: ignore
        self._cfg = cfg

    @property
    def topic_configs(self) -> list:
        """获取所有主题配置（列表格式）"""
        try:
            return list(self._cfg.TOPIC_CONFIGS)  # type: ignore[attr-defined]
        except Exception:
            return []

    @property
    def topic_templates(self) -> Dict[str, Any]:
        """获取所有主题模板"""
        try:
            return dict(self._cfg.TOPIC_TEMPLATES)  # type: ignore[attr-defined]
        except Exception:
            return {}

    @property
    def protocol_version(self) -> Optional[str]:
        """获取协议版本"""
        try:
            return getattr(self._cfg, "PROTOCOL_VERSION", None)
        except Exception:
            return None

    def get_server_config(self, server_name: str = "default") -> Dict[str, Any]:
        """
        获取MQTT服务器配置
        
        Args:
            server_name: 服务器配置名称
            
        Returns:
            Dict: 服务器配置字典，如果不存在则返回 default 配置的副本
        """
        try:
            servers = self._cfg.MQTT_SERVERS  # type: ignore[attr-defined]
            # 如果指定的服务器配置不存在，使用 default
            config = servers.get(server_name, servers.get("default", {}))
            # 返回副本，避免外部修改影响原始配置
            return config.copy() if config else {}
        except Exception:
            return {}

    def get_topic_template(self, category: str, topic_type: str) -> str:
        """
        获取主题模板
        
        Args:
            category: 主题分类 (device)
            topic_type: 主题类型 (info, status, control)
            
        Returns:
            str: 主题模板字符串，如果不存在返回空字符串
        """
        try:
            templates = self._cfg.TOPIC_TEMPLATES  # type: ignore[attr-defined]
            return templates.get(category, {}).get(topic_type, "")
        except Exception:
            return ""

    def get_topic_config(self, topic_key: str) -> Dict[str, Any]:
        """
        获取主题详细配置（包含 QoS、周期等信息）
        
        Args:
            topic_key: 主题键名 (test, device_info, device_status, control)
            
        Returns:
            Dict: 主题配置字典，如果不存在返回空字典
        """
        try:
            configs = self._cfg.TOPIC_CONFIGS  # type: ignore[attr-defined]
            config = configs.get(topic_key, {})
            # 返回副本，避免外部修改影响原始配置
            return config.copy() if config else {}
        except Exception:
            return {}

    @staticmethod
    def format_topic(template: str, **kwargs) -> str:
        """
        格式化主题字符串
        
        Args:
            template: 主题模板
            **kwargs: 模板参数（如 client_id）
            
        Returns:
            str: 格式化后的主题字符串
        """
        try:
            return template.format(**kwargs) if template else ""
        except Exception:
            return ""

    def format_topic_from_config(self, topic_key: str, client_id: str) -> str:
        """
        根据主题配置键名和 client_id 格式化主题
        
        Args:
            topic_key: 主题配置键名 (test, device_info, device_status, control)
            client_id: 客户端ID（设备ID）
            
        Returns:
            str: 格式化后的主题字符串
        """
        config = self.get_topic_config(topic_key)
        template = config.get("name", "")
        if not template:
            return ""
        
        try:
            return template.format(client_id=client_id)
        except Exception:
            return template  # 如果格式化失败，返回原始模板

    def get_message_schema(self, message_type: str) -> Dict[str, Any]:
        """
        获取消息类型的数据结构定义
        
        Args:
            message_type: 消息类型名称 (test, device_info, device_status, control)
            
        Returns:
            Dict: 消息结构定义（包含 fields），如果不存在返回空字典
        """
        try:
            message_types = self._cfg.MESSAGE_TYPES  # type: ignore[attr-defined]
            schema = message_types.get(message_type, {})
            # 返回副本，避免外部修改影响原始配置
            return schema.copy() if schema else {}
        except Exception:
            return {}

    def get_status_category_schema(self, message_type: str, category: str) -> Dict[str, Any]:
        """
        获取 device_status 消息中特定分类的字段定义
        
        Args:
            message_type: 消息类型（通常是 "device_status"）
            category: 分类名称 (system, sensor, actuator)
            
        Returns:
            Dict: 分类的字段定义，如果不存在返回空字典
        """
        if message_type != "device_status":
            return {}
        
        try:
            message_types = self._cfg.MESSAGE_TYPES  # type: ignore[attr-defined]
            schema = message_types.get(message_type, {})
            # 注意：根据当前 mqtt_config.py 的结构，MESSAGE_TYPES 中的 device_status 没有 categories 字段
            # 而是使用 device_status_system, device_status_sensor 等作为独立的消息类型
            # 如果需要获取分类，应该直接使用对应的消息类型
            return schema.get("categories", {}).get(category, {})
        except Exception:
            return {}

    def load_protocol_json(self) -> Optional[Dict[str, Any]]:
        """
        加载 mqtt_protocol.json 文件
        
        Returns:
            Dict: 协议定义字典，如果文件不存在或加载失败返回 None
        """
        try:
            # 查找协议文件（在 mqtt_config.py 同级目录）
            config_file = Path(__file__).parent / "mqtt_protocol.json"
            if not config_file.exists():
                return None
            
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
