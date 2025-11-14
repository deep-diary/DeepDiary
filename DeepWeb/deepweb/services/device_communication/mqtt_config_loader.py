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
        try:
            # 尝试相对导入（作为包的一部分）
            from . import mqtt_config as cfg  # type: ignore
        except ImportError:
            # 如果相对导入失败（直接运行文件时），使用绝对导入
            import sys
            from pathlib import Path
            # 添加当前目录到路径
            current_dir = Path(__file__).parent
            if str(current_dir) not in sys.path:
                sys.path.insert(0, str(current_dir))
            import mqtt_config as cfg
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
            # TOPIC_CONFIGS 是列表格式，需要遍历查找匹配的 key
            for config in configs:
                if config.get("key") == topic_key:
                    # 返回副本，避免外部修改影响原始配置
                    return config.copy() if config else {}
            return {}
        except Exception as e:
            # 记录错误以便调试
            import logging
            logging.warning(f"get_topic_config 失败: topic_key={topic_key}, error={e}")
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

    def format_topic_from_config(self, topic_key: str, client_id: Optional[str] = None, device_id: Optional[str] = None) -> str:
        """
        根据主题配置键名和 client_id/device_id 格式化主题
        
        Args:
            topic_key: 主题配置键名 (test, device_info, device_status, control, thumbler_status, thumbler_cmd)
            client_id: 客户端ID（设备ID），用于旧版主题格式
            device_id: 设备ID，用于新版主题格式（如 Thumbler）
            
        Returns:
            str: 格式化后的主题字符串
        """
        config = self.get_topic_config(topic_key)
        template = config.get("name", "")
        if not template:
            return ""
        
        # 优先使用 device_id，如果没有则使用 client_id
        device_identifier = device_id if device_id is not None else client_id
        if device_identifier is None:
            return template  # 如果都没有提供，返回原始模板
        
        try:
            # 尝试使用 device_id 格式化（新版格式，如 Thumbler）
            try:
                return template.format(device_id=device_identifier)
            except KeyError:
                # 如果模板中没有 device_id，尝试使用 client_id（旧版格式）
                return template.format(client_id=device_identifier)
        except Exception:
            return template  # 如果格式化失败，返回原始模板

    def get_topics_by_direction(self, direction: str) -> list:
        """
        根据方向获取主题配置列表
        
        Args:
            direction: 主题方向 ("pub" 或 "sub")
                - "pub": 设备发布，Web订阅（状态主题）
                - "sub": 设备订阅，Web发布（命令主题）
                
        Returns:
            list: 主题配置列表
        """
        try:
            configs = self._cfg.TOPIC_CONFIGS  # type: ignore[attr-defined]
            result = []
            for config in configs:
                if config.get("direction", "pub") == direction:
                    # 返回副本，避免外部修改影响原始配置
                    result.append(config.copy() if config else {})
            return result
        except Exception:
            return []
    
    def get_topic_choices_for_ui(self, direction: Optional[str] = None) -> list:
        """
        获取用于UI下拉选择的主题列表
        
        Args:
            direction: 主题方向过滤（可选）
                - "pub": 只返回状态主题
                - "sub": 只返回命令主题
                - None: 返回所有主题
                
        Returns:
            list: [(显示名称, topic_key), ...]
                显示名称格式: "描述 (主题模板)"
        """
        try:
            configs = self._cfg.TOPIC_CONFIGS  # type: ignore[attr-defined]
            choices = []
            
            for config in configs:
                # 如果指定了方向，进行过滤
                if direction and config.get("direction", "pub") != direction:
                    continue
                
                key = config.get("key", "")
                name = config.get("name", "")
                description = config.get("description", "")
                
                # 生成显示名称
                if description:
                    display_name = f"{description} ({name})"
                else:
                    display_name = name
                
                choices.append((display_name, key))
            
            return choices
        except Exception:
            return []
    
    def get_topic_qos(self, topic_key: str) -> int:
        """
        获取主题的 QoS 级别
        
        Args:
            topic_key: 主题配置键名
            
        Returns:
            int: QoS 级别，默认返回 0
        """
        config = self.get_topic_config(topic_key)
        return config.get("qos", 0)

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


# 使用示例
if __name__ == "__main__":
    loader = MQTTConfigLoader()
    
    # 获取服务器配置
    config = loader.get_server_config("default")
    print("默认服务器配置:", config)
    
    # 获取主题模板
    thumbler_status_template = loader.get_topic_template("thumbler", "status")
    print("Thumbler 状态主题模板:", thumbler_status_template)
    
    # 获取主题详细配置
    thumbler_status_config = loader.get_topic_config("thumbler_status")
    print("Thumbler 状态主题配置:", thumbler_status_config)
    
    # 格式化主题（使用配置）
    device_id = "ATK-DNESP32S3-9888e000ae28"
    thumbler_status_topic = loader.format_topic_from_config("thumbler_status", device_id=device_id)
    print(f"格式化后的状态主题: {thumbler_status_topic}")
    
    thumbler_cmd_topic = loader.format_topic_from_config("thumbler_cmd", device_id=device_id)
    print(f"格式化后的控制主题: {thumbler_cmd_topic}")
    
    # 获取消息结构
    status_schema = loader.get_message_schema("thumbler_status")
    print("Thumbler 状态消息字段:", list(status_schema.get("fields", {}).keys()))
    
    cmd_schema = loader.get_message_schema("thumbler_cmd")
    print("Thumbler 控制消息字段:", list(cmd_schema.get("fields", {}).keys()))
