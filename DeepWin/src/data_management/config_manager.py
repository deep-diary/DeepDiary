# src/data_management/config_manager.py
# 配置管理器

import json
import os
from PySide6.QtCore import QObject, Signal
from typing import Dict, Any, Optional

from src.data_management.log_manager import LogManager


class ConfigManager(QObject):
    """
    DeepWin 应用程序的配置管理器。
    负责加载、保存和提供对应用程序配置的统一访问。
    支持 JSON 格式的配置文件，并提供嵌套键的访问。
    """

    config_updated = Signal() # 配置更新时发出信号

    def __init__(self, log_manager: LogManager, config_file: str = 'config.json', parent: Optional[QObject] = None):
        """
        初始化配置管理器。
        :param log_manager: 全局日志管理器实例。
        :param config_file: 配置文件的路径和名称。
        :param parent: QObject 父对象。
        """
        super().__init__(parent)
        self.logger = log_manager.get_logger(__name__)
        self.config_file = config_file
        self._config: Dict[str, Any] = {}
        self._default_config: Dict[str, Any] = self._get_default_config()

        self.logger.info(f"ConfigManager: 初始化中，配置文件: {self.config_file}")
        self._load_config()
        self.logger.info("ConfigManager: 初始化完成。")

    def _get_default_config(self) -> Dict[str, Any]:
        """
        定义应用程序的默认配置。
        这是应用程序首次运行或配置文件不存在时的基准。
        """
        return {
            "general": {
                "theme": "light",
                "language": "zh_CN",
                "auto_sync_interval_minutes": 60,
                "data_storage_path": "data/"
            },
            "device_settings": {
                "deeparm_serial_port": "COM1",
                "deeparm_baud_rate": 9600,
                "deeparm_can_bustype": "virtual", # "virtual", "pcan", "socketcan"
                "deeparm_dbc_path": "deeparm.dbc", # 相对路径或绝对路径
                "deepmotor_serial_port": "COM2",
                "deepmotor_baud_rate": 115200
            },
            "network": {
                "server_address": "localhost:8000",
                "mqtt_broker_host": "localhost",
                "mqtt_broker_port": 1883
            },
            "ai_settings": {
                "image_recognition_enabled": True,
                "voice_recognition_enabled": True,
                "llm_api_key": "your_llm_api_key_here"
            }
        }

    def _load_config(self):
        """
        从文件加载配置。如果文件不存在或加载失败，则使用默认配置。
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置，确保新加入的配置项有默认值
                    self._config = self._merge_configs(self._default_config, loaded_config)
                self.logger.info(f"ConfigManager: 已从 '{self.config_file}' 加载配置。")
            except json.JSONDecodeError as e:
                self.logger.error(f"ConfigManager: 配置文件 '{self.config_file}' 格式错误: {e}。将使用默认配置。")
                self._config = self._default_config.copy()
            except Exception as e:
                self.logger.error(f"ConfigManager: 加载配置文件 '{self.config_file}' 失败: {e}。将使用默认配置。")
                self._config = self._default_config.copy()
        else:
            self.logger.warning(f"ConfigManager: 配置文件 '{self.config_file}' 不存在。将创建并使用默认配置。")
            self._config = self._default_config.copy()
            self._save_config() # 第一次运行，保存默认配置到文件

    def _save_config(self):
        """
        将当前配置保存到文件。
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file) or '.', exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            self.logger.info(f"ConfigManager: 配置已保存到 '{self.config_file}'。")
        except Exception as e:
            self.logger.error(f"ConfigManager: 保存配置文件 '{self.config_file}' 失败: {e}")

    def _merge_configs(self, default: Dict, override: Dict) -> Dict:
        """
        递归合并字典：用 override 中的值覆盖 default 中的值。
        如果 default 中有而 override 中没有的键，则保留 default 的值。
        如果 override 中有而 default 中没有的键，则添加 override 的值。
        """
        merged = default.copy()
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值。支持点分路径（如 'network.mqtt_broker_host'）。
        :param key_path: 配置项的路径，例如 "general.theme" 或 "device_settings.deeparm_baud_rate"。
        :param default: 如果配置项不存在，返回的默认值。
        :return: 配置值。
        """
        keys = key_path.split('.')
        current_level = self._config
        try:
            for key in keys:
                current_level = current_level[key]
            return current_level
        except KeyError:
            self.logger.warning(f"ConfigManager: 配置项 '{key_path}' 不存在。返回默认值: {default}")
            return default

    def set(self, key_path: str, value: Any):
        """
        设置配置值。支持点分路径。
        :param key_path: 配置项的路径。
        :param value: 要设置的新值。
        """
        keys = key_path.split('.')
        current_level = self._config
        for i, key in enumerate(keys):
            if i == len(keys) - 1: # 最后一层键
                current_level[key] = value
            else: # 中间层键
                if key not in current_level or not isinstance(current_level[key], dict):
                    current_level[key] = {} # 如果不存在或不是字典，则创建一个新的字典
                current_level = current_level[key]
        self._save_config() # 每次设置后都保存
        self.config_updated.emit() # 发出配置更新信号
        self.logger.info(f"ConfigManager: 配置项 '{key_path}' 已设置为 '{value}'。")

    def get_all(self) -> Dict[str, Any]:
        """
        获取所有配置数据。
        :return: 包含所有配置的字典。
        """
        return self._config.copy() # 返回副本以防止外部直接修改

    def reload_config(self):
        """
        重新加载配置文件。
        """
        self.logger.info("ConfigManager: 正在重新加载配置文件...")
        self._load_config()
        self.config_updated.emit()
        self.logger.info("ConfigManager: 配置重新加载完成。")

    def cleanup(self):
        """
        清理配置管理器资源（如果需要）。
        """
        self.logger.info("ConfigManager: 清理完成。")

