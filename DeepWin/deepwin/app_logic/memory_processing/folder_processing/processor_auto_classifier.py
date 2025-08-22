from .base import FolderProcessorBase
import os
import shutil
import time

class AutoClassifierProcessor(FolderProcessorBase):
    """自动文件分类处理器"""
    def __init__(self):
        super().__init__()
        
        # 设置默认参数
        classifier_config = self.config.get('classifier')
        if not classifier_config:
            self.config.set('classifier', 'output_folder', 'output/processed_folder/classifier')
            self.config.set('classifier', 'create_copy', True)  # 是否创建副本而不是移动
            self.config.set('classifier', 'save_report', True)
            self.config.set('classifier', 'file_types', {
                "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"],
                "Documents": [".doc", ".docx", ".pdf", ".txt", ".xls", ".xlsx", ".ppt", ".pptx"],
                "Audio": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg"],
                "Video": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"],
                "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
                "Code": [".py", ".java", ".cpp", ".h", ".js", ".html", ".css"],
                "Others": []  # 未分类的文件
            })
        
        # 从配置文件加载参数
        self.output_folder = self.config.get('classifier', 'output_folder', 'output/processed_folder/classifier')
        self.create_copy = self.config.get('classifier', 'create_copy', True)
        self.save_report = self.config.get('classifier', 'save_report', True)
        self.file_types = self.config.get('classifier', 'file_types', {})
        
        # 初始化统计信息
        self.stats = {category: 0 for category in self.file_types.keys()}
        self.total_files = 0
        self.processed_files = 0

    def process(self, folder_path=None):
        """处理文件夹，自动分类文件
        Args:
            folder_path: 要处理的文件夹路径
        Returns:
            bool: 是否成功处理
        """
        # 检查输入文件夹
        folder_path = self.check_input_folder(folder_path)
        
        try:
            print(f"\nScanning folder: {folder_path}")
            
            # 获取所有文件
            all_files = []
            for root, _, files in os.walk(folder_path):
                for file in files:
                    all_files.append(os.path.join(root, file))
            
            self.total_files = len(all_files)
            print(f"Found {self.total_files} files")
            
            if not all_files:
                print("No files to classify")
                return True

            # 创建输出目录
            os.makedirs(self.output_folder, exist_ok=True)
            for category in self.file_types.keys():
                os.makedirs(os.path.join(self.output_folder, category), exist_ok=True)

            # 处理文件
            print("\nClassifying files...")
            for file_path in all_files:
                self._process_file(file_path)
                self.processed_files += 1
                print(f"Processed {self.processed_files}/{self.total_files} files", end='\r')

            print("\n\nClassification complete!")
            self._print_stats()
            
            # 生成报告
            if self.save_report:
                self._generate_report()
            
            return True

        except Exception as e:
            print(f"\nError processing folder: {e}")
            return False

    def _process_file(self, file_path):
        """处理单个文件"""
        file_ext = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path)
        
        # 确定文件类别
        target_category = "Others"
        for category, extensions in self.file_types.items():
            if file_ext in extensions:
                target_category = category
                break
        
        # 更新统计信息
        self.stats[target_category] += 1
        
        # 创建目标路径
        target_path = os.path.join(self.output_folder, target_category, file_name)
        
        # 确保文件名唯一
        if os.path.exists(target_path):
            base_name, ext = os.path.splitext(file_name)
            counter = 1
            while os.path.exists(target_path):
                new_name = f"{base_name}_{counter}{ext}"
                target_path = os.path.join(self.output_folder, target_category, new_name)
                counter += 1
        
        # 复制或移动文件
        if self.create_copy:
            shutil.copy2(file_path, target_path)
        else:
            shutil.move(file_path, target_path)

    def _print_stats(self):
        """打印分类统计信息"""
        print("\nClassification Statistics:")
        print("------------------------")
        for category, count in self.stats.items():
            print(f"{category}: {count} files")

    def _generate_report(self):
        """生成分类报告"""
        report_path = os.path.join(self.output_folder, 
                                 f'classification_report_{time.strftime("%Y%m%d_%H%M%S")}.txt')
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("File Classification Report\n")
            f.write("========================\n\n")
            
            f.write("Statistics:\n")
            f.write("-----------\n")
            for category, count in self.stats.items():
                f.write(f"{category}: {count} files\n")
            
            f.write(f"\nTotal files processed: {self.total_files}\n")
            f.write(f"Output directory: {self.output_folder}\n")
            
        print(f"\nReport saved to: {report_path}")

    def add_file_type(self, category, extensions):
        """添加新的文件类型
        Args:
            category: 类别名称
            extensions: 文件扩展名列表
        """
        if category not in self.file_types:
            self.file_types[category] = []
        self.file_types[category].extend(extensions)
        self.config.set('classifier', 'file_types', self.file_types)

