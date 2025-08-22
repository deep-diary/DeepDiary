from .base import FolderProcessorBase
import os
import hashlib
import shutil
import time

class DuplicateFinderProcessor(FolderProcessorBase):
    """重复文件查找处理器"""
    def __init__(self):
        super().__init__()
        
        # 设置默认参数
        duplicate_config = self.config.get('duplicate')
        if not duplicate_config:
            self.config.set('duplicate', 'output_folder', 'output/processed_folder/duplicate')
            self.config.set('duplicate', 'move_duplicates', True)
            self.config.set('duplicate', 'min_size', 1024)  # 最小文件大小(bytes)
            self.config.set('duplicate', 'save_report', True)
            
        # 从配置文件加载参数
        self.output_folder = self.config.get('duplicate', 'output_folder', 'output/processed_folder/duplicate')
        self.move_duplicates = self.config.get('duplicate', 'move_duplicates', True)
        self.min_size = self.config.get('duplicate', 'min_size', 1024)
        self.save_report = self.config.get('duplicate', 'save_report', True)
        
        # 初始化结果存储
        self.duplicates = []
        self.total_saved_space = 0

    def process(self, folder_path=None):
        """处理文件夹，查找重复文件
        Args:
            folder_path: 要处理的文件夹路径
        Returns:
            bool: 是否成功处理
        """
        # 检查输入文件夹
        folder_path = self.check_input_folder(folder_path)
        
        try:
            print(f"\nScanning folder: {folder_path}")
            hash_dict = {}
            total_files = sum([len(files) for r, d, files in os.walk(folder_path)])
            processed_files = 0
            skipped_files = 0

            # 扫描文件
            for dirpath, dirnames, filenames in os.walk(folder_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    
                    # 检查文件大小
                    file_size = os.path.getsize(file_path)
                    if file_size < self.min_size:
                        skipped_files += 1
                        continue
                    
                    # 计算文件哈希
                    file_hash = self.hash_file(file_path)
                    if file_hash in hash_dict:
                        hash_dict[file_hash].append((file_path, file_size))
                    else:
                        hash_dict[file_hash] = [(file_path, file_size)]
                    
                    processed_files += 1
                    print(f"Processed {processed_files}/{total_files} files", end='\r')

            print(f"\nSkipped {skipped_files} files (smaller than {self.min_size} bytes)")

            # 找出重复文件
            self.duplicates = [(hash_val, files) for hash_val, files in hash_dict.items() 
                             if len(files) > 1]
            
            if not self.duplicates:
                print("\nNo duplicate files found.")
                return True

            # 处理重复文件
            if self.move_duplicates:
                self._handle_duplicates()
            
            # 生成报告
            if self.save_report:
                self._generate_report()

            print(f"\nFound {len(self.duplicates)} groups of duplicate files")
            print(f"Total space that could be saved: {self.total_saved_space / (1024*1024):.2f} MB")
            return True

        except Exception as e:
            print(f"\nError processing folder: {e}")
            return False

    def hash_file(self, file_path):
        """计算文件哈希值"""
        BLOCK_SIZE = 65536
        file_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                fb = f.read(BLOCK_SIZE)
                while len(fb) > 0:
                    file_hash.update(fb)
                    fb = f.read(BLOCK_SIZE)
            return file_hash.hexdigest()
        except Exception as e:
            print(f"Error hashing file {file_path}: {e}")
            return None

    def _handle_duplicates(self):
        """处理重复文件（移动到输出目录）"""
        print("\nMoving duplicate files...")
        os.makedirs(self.output_folder, exist_ok=True)
        
        for hash_val, files in self.duplicates:
            # 保留第一个文件，移动其他副本
            original = files[0]
            duplicates = files[1:]
            
            # 创建以哈希值命名的子目录
            hash_dir = os.path.join(self.output_folder, hash_val[:8])
            os.makedirs(hash_dir, exist_ok=True)
            
            # 移动重复文件
            for file_path, file_size in duplicates:
                self.total_saved_space += file_size
                if self.move_duplicates:
                    new_path = os.path.join(hash_dir, os.path.basename(file_path))
                    shutil.move(file_path, new_path)

    def _generate_report(self):
        """生成重复文件报告"""
        report_path = os.path.join(self.output_folder, 
                                 f'duplicate_report_{time.strftime("%Y%m%d_%H%M%S")}.txt')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("Duplicate Files Report\n")
            f.write("=====================\n\n")
            
            for hash_val, files in self.duplicates:
                f.write(f"\nHash: {hash_val}\n")
                f.write("Files:\n")
                for file_path, file_size in files:
                    f.write(f"  - {file_path} ({file_size/1024:.2f} KB)\n")
            
            f.write(f"\nTotal space that could be saved: {self.total_saved_space/(1024*1024):.2f} MB\n")
        
        print(f"\nReport saved to: {report_path}")
