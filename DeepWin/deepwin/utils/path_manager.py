#!/usr/bin/env python3
"""
DeepWin 路径管理器

统一管理项目中的各种路径，包括输出目录、模型目录、数据目录等。
"""

import os
from typing import Dict, Optional, Union
from pathlib import Path
from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager


class PathManager:
    """路径管理器"""
    
    def __init__(self, log_manager:LogManager, config_manager:ConfigManager, base_path: str = None):
        """
        初始化路径管理器
        
        Args:
            config_manager: 配置管理器实例
            base_path: 基础路径，如果为None则自动检测项目根目录
        """
        self.config_manager = config_manager
        
        if base_path:
            self.base_path = Path(base_path)
        else:
            # 自动检测项目根目录
            self.base_path = self._detect_project_root()
        
        # 默认路径配置
        self.default_paths = {
            "root": ".",
            "output": "output",
            "models": "models", 
            "data": "data",
            "logs": "logs",
            "temp": "temp",
            "userdata": "userdata",
            "configs": "configs",
            "resources": "resources"
        }
        
        # 初始化路径
        self._init_paths()
    
    def _detect_project_root(self) -> Path:
        """
        自动检测项目根目录
        
        从当前文件位置向上查找，直到找到包含特定标识文件或目录的项目根目录
        """
        current_path = Path(__file__).resolve()
        
        # 从当前文件位置向上查找项目根目录
        while current_path.parent != current_path:  # 避免无限循环
            # 检查是否包含项目标识文件/目录
            if (current_path / 'deepwin').exists() and (current_path / 'main.py').exists():
                return current_path
            if (current_path / 'deepwin').exists() and (current_path / 'requirements.txt').exists():
                return current_path
            if (current_path / 'deepwin').exists() and (current_path / 'setup.py').exists():
                return current_path
            
            current_path = current_path.parent
        
        # 如果没找到，回退到当前工作目录
        fallback_path = Path.cwd()
        print(f"警告: 无法自动检测项目根目录，使用当前工作目录: {fallback_path}")
        return fallback_path
    
    def _init_paths(self):
        """初始化所有路径"""
        # 从配置文件获取路径，如果没有则使用默认值
        if self.config_manager:
            config_paths = self.config_manager.get('paths', {})
            self.paths = {**self.default_paths, **config_paths}
        else:
            self.paths = self.default_paths.copy()
        
        # 确保所有路径都是相对于base_path的
        for key, path in self.paths.items():
            if path != ".":
                self.paths[key] = str(Path(path))
    
    def get_path(self, path_key: str, sub_path: str = None, create: bool = True) -> Path:
        """
        获取指定路径
        
        Args:
            path_key: 路径键名（如 'output', 'models'）
            sub_path: 子路径
            create: 是否自动创建目录
            
        Returns:
            Path对象
        """
        if path_key not in self.paths:
            raise ValueError(f"未知的路径键: {path_key}")
        
        # 构建完整路径
        if path_key == "root":
            full_path = self.base_path
        else:
            full_path = self.base_path / self.paths[path_key]
        
        # 添加子路径
        if sub_path:
            full_path = full_path / sub_path
        
        # 创建目录
        if create and not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
        
        return full_path
    
    def get_output_path(self, sub_dir: str = None, create: bool = True) -> Path:
        """获取输出目录路径"""
        return self.get_path('output', sub_dir, create)
    
    def get_models_path(self, sub_dir: str = None, create: bool = True) -> Path:
        """获取模型目录路径"""
        return self.get_path('models', sub_dir, create)
    
    def get_data_path(self, sub_dir: str = None, create: bool = True) -> Path:
        """获取数据目录路径"""
        return self.get_path('data', sub_dir, create)
    
    def get_logs_path(self, sub_dir: str = None, create: bool = True) -> Path:
        """获取日志目录路径"""
        return self.get_path('logs', sub_dir, create)
    
    def get_temp_path(self, sub_dir: str = None, create: bool = True) -> Path:
        """获取临时目录路径"""
        return self.get_path('temp', sub_dir, create)
    
    def get_userdata_path(self, sub_dir: str = None, create: bool = True) -> Path:
        """获取用户数据目录路径"""
        return self.get_path('userdata', sub_dir, create)
    
    def get_configs_path(self, sub_dir: str = None, create: bool = True) -> Path:
        """获取配置目录路径"""
        return self.get_path('configs', sub_dir, create)
    
    def get_resources_path(self, sub_dir: str = None, create: bool = True) -> Path:
        """获取资源目录路径"""
        return self.get_path('resources', sub_dir, create)
    
    def get_image_processing_output_path(self, processor_name: str = None, create: bool = True) -> Path:
        """
        获取图像处理输出目录路径
        
        Args:
            processor_name: 处理器名称
            create: 是否自动创建目录
            
        Returns:
            Path对象
        """
        base_output = self.get_output_path('processed_images', create)
        
        if processor_name:
            # 从配置获取子目录名称
            if self.config_manager:
                subdirs = self.config_manager.get('image_processing.save.subdirs', {})
                subdir_name = subdirs.get(processor_name, processor_name)
            else:
                subdir_name = processor_name
            
            processor_path = base_output / subdir_name
            if create:
                processor_path.mkdir(parents=True, exist_ok=True)
            return processor_path
        
        return base_output
    
    def get_database_path(self, db_type: str, sub_path: str = None, create: bool = True) -> Path:
        """
        获取数据库路径
        
        Args:
            db_type: 数据库类型 ('sqlite', 'qdrant', 'faiss')
            sub_path: 子路径
            create: 是否自动创建目录
            
        Returns:
            Path对象
        """
        if db_type == 'sqlite':
            return self.get_data_path('sqlite', create)
        elif db_type == 'qdrant':
            return self.get_data_path('qdrant', create)
        elif db_type == 'faiss':
            return self.get_data_path('faiss', create)
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
    
    def get_backup_path(self, db_type: str = None, create: bool = True) -> Path:
        """
        获取备份目录路径
        
        Args:
            db_type: 数据库类型，如果为None则返回通用备份目录
            create: 是否自动创建目录
            
        Returns:
            Path对象
        """
        if db_type:
            # 创建 backup/db_type 子目录
            backup_path = self.get_data_path('backup', create)
            db_backup_path = backup_path / db_type
            if create:
                db_backup_path.mkdir(parents=True, exist_ok=True)
            return db_backup_path
        else:
            return self.get_data_path('backup', create=create)
    
    def list_paths(self) -> Dict[str, str]:
        """列出所有配置的路径"""
        return self.paths.copy()
    
    def ensure_all_paths(self):
        """确保所有路径都存在"""
        for path_key in self.paths:
            if path_key != "root":
                self.get_path(path_key, create=True)
    
    def get_relative_path(self, absolute_path: Union[str, Path]) -> str:
        """获取相对于项目根目录的路径"""
        absolute_path = Path(absolute_path)
        try:
            return str(absolute_path.relative_to(self.base_path))
        except ValueError:
            return str(absolute_path)
    
    def get_absolute_path(self, relative_path: str) -> Path:
        """获取绝对路径"""
        return self.base_path / relative_path


# 便捷函数
def get_path_manager(config_manager=None, base_path: str = None) -> PathManager:
    """获取路径管理器实例"""
    return PathManager(config_manager, base_path)


def get_output_path(sub_dir: str = None, create: bool = True) -> Path:
    """快速获取输出目录路径"""
    return get_path_manager().get_output_path(sub_dir, create)


def get_models_path(sub_dir: str = None, create: bool = True) -> Path:
    """快速获取模型目录路径"""
    return get_path_manager().get_models_path(sub_dir, create)


def get_data_path(sub_dir: str = None, create: bool = True) -> Path:
    """快速获取数据目录路径"""
    return get_path_manager().get_data_path(sub_dir, create)


if __name__ == "__main__":
    # 测试代码
    pm = PathManager()
    print("默认路径配置:")
    for key, path in pm.list_paths().items():
        print(f"  {key}: {path}")
    
    print(f"\n输出目录: {pm.get_output_path()}")
    print(f"模型目录: {pm.get_models_path()}")
    print(f"数据目录: {pm.get_data_path()}")
    print(f"图像处理输出: {pm.get_image_processing_output_path('face_detection')}")
