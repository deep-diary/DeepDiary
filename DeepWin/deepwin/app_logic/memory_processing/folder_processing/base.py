from abc import ABC, abstractmethod
from .config_manager import ConfigManager
import os

class FolderProcessorBase(ABC):
    """文件夹处理器基类"""
    def __init__(self):
        self.config = ConfigManager()
        
        # 基础路径配置
        self.base_output_dir = 'output/processed_folder'  # 基础输出目录
        self.base_demo_dir = os.path.join(os.path.dirname(__file__), 'demo')  # 基础demo目录
        
        # 确保基础输出目录存在
        os.makedirs(self.base_output_dir, exist_ok=True)

    def get_config(self):
        """获取配置管理器"""
        return self.config

    def get_processor_output_dir(self, processor_name):
        """获取处理器的输出目录
        Args:
            processor_name: 处理器名称
        Returns:
            str: 输出目录路径
        """
        output_dir = os.path.join(self.base_output_dir, processor_name)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def get_processor_demo_dir(self, processor_name):
        """获取处理器的demo目录
        Args:
            processor_name: 处理器名称
        Returns:
            str: demo目录路径
        """
        return os.path.join(self.base_demo_dir, processor_name)

    def check_input_folder(self, folder_path):
        """检查输入文件夹
        Args:
            folder_path: 输入文件夹路径
        Returns:
            str: 有效的输入文件夹路径
        Raises:
            ValueError: 如果文件夹无效
        """
        if folder_path is None:
            # 使用默认demo文件夹
            processor_name = self.__class__.__name__.lower().replace('processor', '')
            folder_path = self.get_processor_demo_dir(processor_name)
        
        if not os.path.exists(folder_path):
            raise ValueError(f"Input folder not found: {folder_path}")
        
        return folder_path

    @abstractmethod
    def process(self, folder_path=None):
        """处理文件夹
        Args:
            folder_path: 要处理的文件夹路径，如果为None则使用默认demo文件夹
        Returns:
            处理结果
        """
        pass
