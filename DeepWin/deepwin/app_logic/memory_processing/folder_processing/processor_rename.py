from .base import FolderProcessorBase
import os
import time
import shutil

class RenameProcessor(FolderProcessorBase):
    """文件重命名处理器"""
    def __init__(self):
        super().__init__()
        
        # 设置默认参数
        rename_config = self.config.get('rename')
        if not rename_config:
            self.config.set('rename', 'output_folder', 'output/processed_folder/rename')
            self.config.set('rename', 'prefix', '')
            self.config.set('rename', 'suffix', '')
            self.config.set('rename', 'start_number', 1)
            self.config.set('rename', 'include_date', True)
            self.config.set('rename', 'remove_original_name', False)
            self.config.set('rename', 'create_copy', True)
        
        # 从配置文件加载参数
        self.output_folder = self.config.get('rename', 'output_folder', 'output/processed_folder/rename')
        self.prefix = self.config.get('rename', 'prefix', '')
        self.suffix = self.config.get('rename', 'suffix', '')
        self.start_number = self.config.get('rename', 'start_number', 1)
        self.include_date = self.config.get('rename', 'include_date', True)
        self.remove_original_name = self.config.get('rename', 'remove_original_name', False)
        self.create_copy = self.config.get('rename', 'create_copy', True)

    def process(self, folder_path=None):
        """处理文件夹中的文件重命名
        Args:
            folder_path: 输入文件夹路径
        Returns:
            bool: 处理是否成功
        """
        # 检查输入文件夹
        folder_path = self.check_input_folder(folder_path)
        
        try:
            # 获取所有文件
            files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
            total_files = len(files)
            print(f"\nFound {total_files} files in folder: {folder_path}")
            
            if not files:
                print("No files to rename")
                return False

            # 创建输出目录
            if self.create_copy:
                os.makedirs(self.output_folder, exist_ok=True)
                print(f"\nCreated output folder: {self.output_folder}")

            # 处理每个文件
            print("\nProcessing files...")
            for i, filename in enumerate(files, 1):
                old_path = os.path.join(folder_path, filename)
                file_ext = os.path.splitext(filename)[1]
                
                # 构建新文件名
                new_name_parts = []
                if self.prefix:
                    new_name_parts.append(self.prefix)
                
                if not self.remove_original_name:
                    new_name_parts.append(os.path.splitext(filename)[0])
                
                if self.include_date:
                    date_str = time.strftime("%Y%m%d", time.localtime(os.path.getmtime(old_path)))
                    new_name_parts.append(date_str)
                
                new_name_parts.append(f"{self.start_number + i - 1:03d}")
                
                if self.suffix:
                    new_name_parts.append(self.suffix)
                
                new_name = "_".join(filter(None, new_name_parts)) + file_ext
                
                # 确定新文件路径
                if self.create_copy:
                    new_path = os.path.join(self.output_folder, new_name)
                    shutil.copy2(old_path, new_path)
                else:
                    new_path = os.path.join(folder_path, new_name)
                    os.rename(old_path, new_path)
                
                print(f"Processing {i}/{total_files}: {filename} -> {new_name}", end='\r')
            
            print(f"\nSuccessfully processed {total_files} files")
            if self.create_copy:
                print(f"Renamed copies saved to: {self.output_folder}")
            return True
            
        except Exception as e:
            print(f"\nError processing files: {e}")
            return False

    def set_prefix(self, prefix):
        """设置文件名前缀"""
        self.prefix = prefix
        self.config.set('rename', 'prefix', prefix)

    def set_suffix(self, suffix):
        """设置文件名后缀"""
        self.suffix = suffix
        self.config.set('rename', 'suffix', suffix)

    def set_start_number(self, number):
        """设置起始编号"""
        self.start_number = number
        self.config.set('rename', 'start_number', number)

    def set_include_date(self, include):
        """设置是否包含日期"""
        self.include_date = include
        self.config.set('rename', 'include_date', include)

    def set_remove_original_name(self, remove):
        """设置是否移除原文件名"""
        self.remove_original_name = remove
        self.config.set('rename', 'remove_original_name', remove)

    def set_create_copy(self, create):
        """设置是否创建副本"""
        self.create_copy = create
        self.config.set('rename', 'create_copy', create)
