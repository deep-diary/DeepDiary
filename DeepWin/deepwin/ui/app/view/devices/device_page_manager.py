# coding: utf-8
"""
设备页面管理器
实现自动发现和加载设备页面的功能
"""
import os
import importlib
import inspect
from typing import Dict, List, Type, Optional
from PySide6.QtWidgets import QWidget

from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager
from .base_device_page import BaseDevicePage
import re


class DevicePageManager:
    """设备页面管理器"""
    
    def __init__(self, log_manager: LogManager, config_manager: ConfigManager):
        self.log_manager = log_manager
        self.logger = self.log_manager.get_logger(__name__)
        self.config_manager = config_manager
        
        # 设备页面缓存
        self._device_pages: Dict[str, Type[BaseDevicePage]] = {}
        self._device_instances: Dict[str, BaseDevicePage] = {}
        
        # 设备页面目录
        self.devices_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.logger.info("设备页面管理器初始化开始")
        self.discover_device_pages()
        self.logger.info("设备页面管理器初始化完成")
    
    def _snake_to_camel(self, name: str) -> str:
        """下划线转大驼峰"""
        return ''.join(word.capitalize() for word in name.split('_'))
    
    def discover_device_pages(self):
        """自动发现设备页面"""
        self.logger.info("开始自动发现设备页面")
        
        # 扫描设备目录
        for item in os.listdir(self.devices_dir):
            device_dir = os.path.join(self.devices_dir, item)
            
            # 检查是否是目录且不是特殊目录
            if not os.path.isdir(device_dir) or item.startswith('_') or item in ['__pycache__']:
                continue
            
            # 查找设备页面文件
            page_file = self._find_device_page_file(device_dir, item)
            if page_file:
                camel_name = self._snake_to_camel(item)
                self._load_device_page(camel_name, page_file)
        
        self.logger.info(f"设备页面发现完成，共发现 {len(self._device_pages)} 个设备页面")
    
    def _find_device_page_file(self, device_dir: str, device_name: str) -> Optional[str]:
        """查找设备页面文件"""
        # 可能的文件名模式
        possible_names = [
            f"{device_name}_page.py",
            f"{device_name}.py",
            "page.py",
            "main.py"
        ]
        
        for name in possible_names:
            file_path = os.path.join(device_dir, name)
            if os.path.isfile(file_path):
                self.logger.info(f"找到设备页面文件: {file_path}")
                return file_path
        
        self.logger.warning(f"未找到设备 {device_name} 的页面文件")
        return None
    
    def _load_device_page(self, device_name: str, page_file: str):
        """加载设备页面"""
        try:
            # 构建模块路径
            relative_path = os.path.relpath(page_file, self.devices_dir)
            module_path = relative_path.replace(os.sep, '.').replace('.py', '')
            
            # 导入模块
            module = importlib.import_module(f"deepwin.ui.app.view.devices.{module_path}")
            
            # 查找大驼峰类名
            class_name = f"{device_name}Page"
            device_page_class = getattr(module, class_name, None)
            if device_page_class and issubclass(device_page_class, BaseDevicePage):
                self._device_pages[device_name] = device_page_class
                self.logger.info(f"成功加载设备页面: {device_name} -> {device_page_class.__name__}")
            else:
                self.logger.warning(f"在模块 {module_path} 中未找到有效的设备页面类 {class_name}")
                
        except Exception as e:
            self.logger.error(f"加载设备页面 {device_name} 失败: {str(e)}")
    
    def get_device_page(self, device_name: str, parent: QWidget = None) -> Optional[BaseDevicePage]:
        """获取设备页面实例"""
        # 只用注册时的大驼峰key，不再做任何转换
        if device_name in self._device_instances:
            return self._device_instances[device_name]
        
        # 检查是否有页面类
        if device_name not in self._device_pages:
            self.logger.warning(f"未找到设备页面: {device_name}")
            return None
        
        try:
            # 创建新实例
            device_page_class = self._device_pages[device_name]
            instance = device_page_class(
                device_name=device_name,
                log_manager=self.log_manager,
                config_manager=self.config_manager,
                parent=parent
            )
            
            self._device_instances[device_name] = instance
            self.logger.info(f"创建设备页面实例: {device_name}")
            return instance
            
        except Exception as e:
            self.logger.error(f"创建设备页面实例失败 {device_name}: {str(e)}")
            return None
    
    def get_available_devices(self) -> List[str]:
        """获取可用的设备列表"""
        return list(self._device_pages.keys())
    
    def get_device_display_name(self, device_name: str) -> str:
        """获取设备显示名称"""
        # 直接返回注册时的大驼峰key
        return device_name
    
    def reload_device_pages(self):
        """重新加载设备页面"""
        self.logger.info("重新加载设备页面")
        self._device_pages.clear()
        self._device_instances.clear()
        self.discover_device_pages()
    
    def get_device_page_info(self, device_name: str) -> Dict:
        """获取设备页面信息"""
        if device_name not in self._device_pages:
            return {}
        
        device_class = self._device_pages[device_name]
        return {
            'name': device_name,
            'display_name': self.get_device_display_name(device_name),
            'class_name': device_class.__name__,
            'module': device_class.__module__,
            'has_instance': device_name in self._device_instances
        } 