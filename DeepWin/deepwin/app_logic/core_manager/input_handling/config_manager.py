import json
import os
from typing import Any, Dict

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self.package_dir = os.path.dirname(os.path.abspath(__file__))
            self.config_path = os.path.join(self.package_dir, 'configs', 'config.json')
            self._config = self.load_config()
            self._initialized = True

    def load_config(self) -> Dict:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print(f"Config file not found: {self.config_path}")
                return {}
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def get(self, section: str, key: str = None, default: Any = {}) -> Any:
        """获取配置值
        Args:
            section: 配置节名称
            key: 配置项名称，如果为None则返回整个节
            default: 默认值
        """
        
        if section not in self._config:
            print(f"Section not found: {section}")
            return default
        
        if not key:
            return self._config[section]
        
        return self._config[section].get(key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        """设置配置值"""
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value
        self.save_config()

    def save_config(self) -> None:
        """保存配置到文件"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving config: {e}")
