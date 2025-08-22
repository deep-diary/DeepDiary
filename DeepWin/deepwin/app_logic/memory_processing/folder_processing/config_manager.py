import json
import os

class ConfigManager:
    """配置管理器"""
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), 'configs', 'config.json')
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}

    def get(self, section, key=None, default=None):
        """获取配置值
        Args:
            section: 配置节名称
            key: 配置项名称，如果为None则返回整个节
            default: 默认值
        Returns:
            配置值或默认值
        """
        if key is None:
            return self.config.get(section, default)
        section_data = self.config.get(section, {})
        return section_data.get(key, default)

    def set(self, section, key, value):
        """设置配置值"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
        self._save_config()

    def _save_config(self):
        """保存配置文件"""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
