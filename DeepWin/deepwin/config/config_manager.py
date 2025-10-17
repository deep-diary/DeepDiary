#!/usr/bin/env python3
"""
Unified Configuration Manager for DeepWin

Handles loading, validation, and management of configuration files
Supports multiple formats, environment-specific configs, and Qt integration
"""

import os
import json
import yaml
import toml
from pathlib import Path
from typing import Dict, Any, Optional, Union
import logging
from deepwin.data_management.log_manager import LogManager

# Qt integration
try:
    from PySide6.QtCore import QObject, Signal
    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False

class ConfigManager:
    """统一的配置管理器，支持多种配置格式和环境"""
    
    def __init__(self, log_manager: LogManager = None, config_dir: Optional[str] = None):
        # 修复日志管理器初始化问题
        if log_manager:
            self.logger = log_manager.get_logger(__name__)
        else:
            # 如果没有提供日志管理器，创建一个简单的日志记录器
            import logging
            self.logger = logging.getLogger(__name__)
            if not self.logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                self.logger.addHandler(handler)
                self.logger.setLevel(logging.INFO)
        
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent
        self.config_cache = {}
        self.current_env = os.getenv('DEEPWIN_ENV', 'development')
        
        # 支持的配置文件格式
        self.supported_formats = {
            '.json': self._load_json,
            '.yaml': self._load_yaml,
            '.yml': self._load_yaml,
            '.toml': self._load_toml,
            '.env': self.load_env
        }
        
        # 默认配置
        self._default_config = self._get_default_config()
        self._config = {}
        
        # 加载配置
        self._load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
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
                "deeparm_can_bustype": "virtual",
                "deeparm_dbc_path": "deeparm.dbc",
                "deepmotor_serial_port": "COM2",
                "deepmotor_baud_rate": 115200,
                "deepmotor_history_length": 100,
                "deepmotor_teaching_interval": 0.1,
                "deepmotor_trajectory_interp_freq": 50
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
            },
            "voice": {
                "app_id": "",
                "workspace_id": "",
                "api_key": "",
                "voice_name": "longxiaochun_v2",
                "sample_rate": 48000,
                "audio_chunk_size": 3200,
                "websocket_url": "wss://dashscope.aliyuncs.com/api-ws/v1/inference",
                "model_name": "multimodal-dialog",
                "conversation_mode": "duplex"
            }
        }
    
    def _load_config(self):
        """加载配置文件"""
        # 尝试加载环境特定的配置文件
        config_files = [
            f"config_{self.current_env}.json",
            f"config_{self.current_env}.yaml",
            f"config_{self.current_env}.yml",
            f"config_{self.current_env}.toml",
            "config.json",  # 默认配置文件
            "config.yaml",
            "config.yml",
            "config.toml"
        ]
        
        for config_file in config_files:
            config_path = self.config_dir / config_file
            if config_path.exists():
                try:
                    loaded_config = self._load_config_file(config_path)
                    # 合并默认配置，确保新加入的配置项有默认值
                    self._config = self._merge_configs(self._default_config, loaded_config)
                    self.logger.info(f"成功加载配置文件: {config_file}")
                    return
                except Exception as e:
                    self.logger.warning(f"加载配置文件失败 {config_file}: {e}")
                    continue
        
        # 如果没有找到配置文件，使用默认配置
        self.logger.warning("未找到配置文件，使用默认配置")
        self._config = self._default_config.copy()
        self._save_config()  # 保存默认配置到文件
    
    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """根据文件扩展名加载配置文件"""
        file_ext = config_path.suffix.lower()
        
        if file_ext in self.supported_formats:
            return self.supported_formats[file_ext](config_path)
        else:
            raise ValueError(f"不支持的配置文件格式: {file_ext}")
    
    def _load_json(self, config_path: Path) -> Dict[str, Any]:
        """加载JSON配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_yaml(self, config_path: Path) -> Dict[str, Any]:
        """加载YAML配置文件"""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except ImportError:
            self.logger.error("PyYAML未安装，无法加载YAML配置文件")
            return {}
    
    def _load_toml(self, config_path: Path) -> Dict[str, Any]:
        """加载TOML配置文件"""
        try:
            import toml
            return toml.load(config_path)
        except ImportError:
            self.logger.error("toml未安装，无法加载TOML配置文件")
            return {}
    
    def load_env(self, config_path: Path = None) -> Dict[str, Any]:
        """加载环境变量配置文件"""
        try:
            from dotenv import load_dotenv
            # 从指定路径加载.env文件，允许覆盖现有环境变量
            if not load_dotenv(override=True):
                self.logger.debug(f"未找到环境变量配置文件: {config_path}")
            else:
                self.logger.info(f"成功加载环境变量配置文件: {config_path}")
            
            # 获取所有环境变量
            config = {}
            for key, value in os.environ.items():
                config[key] = value
                # # 只记录重要的环境变量，减少日志输出
                # if key.startswith(('DEEPWIN_', 'DB_', 'API_', 'APP_', 'DASHSCOPE_', 'CONDA_')):
                #     self.logger.debug(f"环境变量: {key} = {value}")
            return config
            
        except ImportError:
            self.logger.error("python-dotenv未安装，无法加载.env文件")
            return {}
        except Exception as e:
            self.logger.error(f"加载环境变量配置文件失败: {e}")
            return {}
    
    def _merge_configs(self, default: Dict, override: Dict) -> Dict:
        """递归合并字典：用 override 中的值覆盖 default 中的值"""
        merged = default.copy()
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        return merged
    
    def _save_config(self):
        """保存配置到文件"""
        try:
            config_path = self.config_dir / "config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            self.logger.info(f"配置已保存到: {config_path}")
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        获取配置值。支持点分路径（如 'network.mqtt_broker_host'）。
        :param key_path: 配置项的路径
        :param default: 如果配置项不存在，返回的默认值
        :return: 配置值
        """
        keys = key_path.split('.')
        current_level = self._config
        try:
            for key in keys:
                current_level = current_level[key]
            return current_level
        except KeyError:
            self.logger.warning(f"配置项 '{key_path}' 不存在。返回默认值: {default}")
            return default
    
    def set(self, key_path: str, value: Any):
        """
        设置配置值。支持点分路径。
        :param key_path: 配置项的路径
        :param value: 要设置的新值
        """
        keys = key_path.split('.')
        current_level = self._config
        for i, key in enumerate(keys):
            if i == len(keys) - 1:  # 最后一层键
                current_level[key] = value
            else:  # 中间层键
                if key not in current_level or not isinstance(current_level[key], dict):
                    current_level[key] = {}  # 如果不存在或不是字典，则创建一个新的字典
                current_level = current_level[key]
        
        self._save_config()  # 每次设置后都保存
        self.logger.info(f"配置项 '{key_path}' 已设置为 '{value}'。")
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置数据"""
        return self._config.copy()  # 返回副本以防止外部直接修改
    
    def reload_config(self):
        """重新加载配置文件"""
        self.logger.info("正在重新加载配置文件...")
        self._load_config()
        self.logger.info("配置重新加载完成。")
    
    def get_config_value(self, config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """获取配置值，支持点号分隔的键路径"""
        keys = key_path.split('.')
        current = config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        
        return current
    
    def set_config_value(self, config: Dict[str, Any], key_path: str, value: Any) -> bool:
        """设置配置值，支持点号分隔的键路径"""
        keys = key_path.split('.')
        current = config
        
        # 遍历到最后一个键的父级
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # 设置最后一个键的值
        current[keys[-1]] = value
        return True
    
    def save_config(self, config: Dict[str, Any], config_name: str = 'config', format: str = 'json') -> bool:
        """保存配置到文件"""
        try:
            if format == 'json':
                config_path = self.config_dir / f"{config_name}.json"
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
            elif format in ['yaml', 'yml']:
                config_path = self.config_dir / f"{config_name}.yaml"
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            elif format == 'toml':
                config_path = self.config_dir / f"{config_name}.toml"
                with open(config_path, 'w', encoding='utf-8') as f:
                    toml.dump(config, f)
            else:
                raise ValueError(f"不支持的格式: {format}")
            
            self.logger.info(f"配置已保存到: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置文件失败: {e}")
            return False
    
    def get_environment_config(self) -> str:
        """获取当前环境"""
        return self.current_env
    
    def set_environment(self, env: str):
        """设置环境"""
        self.current_env = env
        self.logger.info(f"环境已设置为: {env}")
    
    def cleanup(self):
        """清理配置管理器资源"""
        self.logger.info("配置管理器清理完成。")


# Qt集成版本（如果需要Qt信号支持）
if QT_AVAILABLE:
    class QtConfigManager(ConfigManager, QObject):
        """支持Qt信号的配置管理器"""
        
        config_updated = Signal()  # 配置更新时发出信号
        
        def __init__(self, log_manager=None, config_dir: Optional[str] = None, parent=None):
            ConfigManager.__init__(self, log_manager, config_dir)
            QObject.__init__(self, parent)
        
        def set(self, key_path: str, value: Any):
            """重写set方法，添加信号发射"""
            super().set(key_path, value)
            self.config_updated.emit()  # 发出配置更新信号
        
        def reload_config(self):
            """重写reload_config方法，添加信号发射"""
            super().reload_config()
            self.config_updated.emit()  # 发出配置更新信号
else:
    # 如果没有Qt，QtConfigManager就是ConfigManager的别名
    QtConfigManager = ConfigManager
