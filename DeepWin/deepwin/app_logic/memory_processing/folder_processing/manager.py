from .processor_canvas import CanvasProcessor
from .config_manager import ConfigManager
from .processor_rename import RenameProcessor
from .processor_duplicate_finder import DuplicateFinderProcessor
from .processor_auto_classifier import AutoClassifierProcessor

class FolderManager:
    """文件夹处理管理器"""
    def __init__(self):
        self.config = ConfigManager()
        # 初始化所有处理器
        self.processors = {
            'canvas': CanvasProcessor(),
            'rename': RenameProcessor(),
            'duplicate': DuplicateFinderProcessor(),
            'classify': AutoClassifierProcessor()
        }

    def get_processor(self, processor_type):
        """获取指定类型的处理器"""
        return self.processors.get(processor_type)

    def process_folder(self, folder_path, processor_name):
        """处理文件夹
        Args:
            folder_path: 要处理的文件夹路径
            processor_name: 处理器名称
        Returns:
            处理结果
        """
        processor = self.get_processor(processor_name)
        if processor is None:
            raise ValueError(f"Processor '{processor_name}' not found.")
        
        return processor.process(folder_path)
    


