from PySide6.QtCore import QObject, Signal
import time
from .decorators import display_fps
from .base import ImageProcessor
import cv2
import os
import importlib
from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager
# TODO: 如果执行某个处理器，但经过ImageManager，就会初始化所有的处理器，会占用很多内存和时间，看能否优化
# TODO：每个处理器后，是否需要统一色彩空间，不然有些是RGB，有些是BGR, 会导致有些不兼容
# TODO：打开图像的方式，默认是cv 打开，但有些场景，需要PIL打开，看能否优化，使之兼容，比如多传递一个参数
class ImageManager(QObject):
    # 定义可以向协调器发射的信号
    processing_started = Signal(str)    # 处理开始
    processing_finished = Signal(str)   # 处理完成，传递结果字符串
    processing_error = Signal(str)      # 处理出错，传递错误信息
    processing_progress = Signal(int) # 进度更新 (可选)
    
    def __init__(self,log_manager:LogManager,config_manager:ConfigManager):
        # 初始化日志管理器
        self.log_manager = log_manager
        self.logger = self.log_manager.get_logger(__name__)
        self.logger.info("ImageManager 初始化开始")
        
        self.config = config_manager
        self.max_disp_pixel = self.config.get('image_processing.display.max_display_pixel', 1280)
        
        # 初始化处理器字典，但不立即创建实例
        self.processors = {}
        
        # 获取处理器配置
        self.processors_config = self.config.get('image_processing.processors', {})
        
        # 初始化绘制和保存配置
        self.draws = {}
        self.saves = {}
        
        # 获取所有可用的处理器名称
        self.available_processors = self._get_available_processors()
        
        # 添加处理器别名映射，支持简化的处理器名称
        self.processor_aliases = {
            'mesh': 'face_mesh',
            'detection': 'face_detection',
            'recognition': 'face_recognition',
            'gesture': 'hand_gesture',
            'yolo': 'yolo'
        }
        
        for name in self.available_processors:
            processor_config = self.processors_config.get(name, {})
            self.draws[name] = processor_config.get('draw', True)
            self.saves[name] = processor_config.get('save', False)
        
        # 添加结果存储
        self.results = {}
        self.current_image = None
        self.show_fps = self.config.get('image_processing.display.show_fps', True)
        self.last_time = time.time()
        
        # 添加当前活动处理器跟踪clear
        self.active_processor = None # 当前活动的处理器名称
        
        self.logger.info("ImageManager 初始化完成")

    def _get_available_processors(self):
        """获取所有可用的处理器名称"""
        # 搜索当前目录下以processor_开头的文件
        processor_files = [f for f in os.listdir(os.path.dirname(__file__)) 
                         if f.startswith('processor_') and f.endswith('.py')]
        # 去掉文件名中的processor_前缀和.py后缀
        processor_names = [f.replace('processor_', '').replace('.py', '') 
                         for f in processor_files]
        self.logger.info(f"可用处理器: {processor_names}")
        return processor_names

    def _create_processor(self, processor_name):
        """创建处理器实例"""
        try:
            # 构造处理器类名
            processor_class_name = ''.join(word.capitalize() 
                                         for word in processor_name.split('_')) + "Processor"
            self.logger.info(f"创建处理器: {processor_class_name}")
            
            # 动态导入模块并获取类对象
            module_name = f"deepwin.app_logic.memory_processing.image_processing.processor_{processor_name}"
            module = importlib.import_module(module_name)
            processor_class = getattr(module, processor_class_name)
            
            # 创建实例，传递配置管理器和日志管理器
            return processor_class(self.config, self.log_manager)
            
        except (ImportError, AttributeError) as e:
            self.logger.error(f"创建处理器 '{processor_name}' 失败: {e}")
            return None

    def get_processor(self, processor_name):
        """获取处理器实例，如果不存在则创建"""
        # 检查是否是别名，如果是则转换为实际名称
        actual_name = self.processor_aliases.get(processor_name, processor_name)
        
        # 检查处理器名称是否有效
        if actual_name not in self.available_processors:
            self.logger.warning(f"无效的处理器名称: {processor_name} (映射后: {actual_name})")
            return None
            
        # 如果处理器还未创建，则创建它
        if actual_name not in self.processors:
            processor = self._create_processor(actual_name)
            if processor is not None:
                self.processors[actual_name] = processor
            
        return self.processors.get(actual_name)

    def get_processor_names(self):
        """获取所有可用的处理器名称"""
        return self.available_processors.copy()

    def clear_results(self):
        """清空所有处理结果"""
        self.results.clear()
        self.current_image = None
        self.active_processor = None  # 重置活动处理器
        
        # 只重置已创建的处理器
        for processor in self.processors.values():
            processor.reset()

    def clear_processors(self):
        """清空所有处理器实例"""
        self.processors.clear()
        self.active_processor = None

    def process_image(self, input_source, processor_name):
        """处理单个图像
        Args:
            input_source: 输入图像源
            processor_name: 处理器名称: 
            ['face_detection', 'face_recognition', 'face_mesh', 'pose', 'hand_gesture', 'ocr', 'easy_ocr', 'qr_code', 'yolo', 'all']
            也支持别名: ['detection', 'recognition', 'mesh', 'gesture']
        Returns:
            tuple: (processed_image, processor_name)
        """
        processor = self.get_processor(processor_name)
        if not processor:
            self.logger.error(f"处理器 '{processor_name}' 未找到")
            return input_source
        
        # 更新当前活动处理器
        self.active_processor = processor_name
        
        # 处理图像
        processed_image = processor.process(input_source)
        if processed_image is None:
            raise ValueError(f"Processor '{processor_name}' returned None.")
        
        # 保存处理结果
        self.results[processor_name] = processor.get_result_info()

        # 结构化打印结果
        # import json
        # print(json.dumps(self.results, indent=4))
        
        return processed_image

    def process_image_list(self, input_source, processor_names, output_rgb=False):
        """处理图像列表
        Args:
            input_source: 输入图像源
            processor_names: 处理器名称列表
            output_rgb: 是否输出RGB格式图像
        Returns:
            processed_image: 最终处理后的图像
        """
        # 清空之前的结果
        self.clear_results()
        
        start_time = time.time()
        if input_source is None:
            self.logger.error("输入源为空")
            return input_source
        
        # input_source = self.resize_image(input_source)
        processed_image = None
        
        # 处理每个处理器
        for processor_name in processor_names:
            processed_image = self.process_image(
                input_source if processed_image is None else processed_image,
                processor_name
            )
            # 最后处理的处理器将成为活动处理器
            self.active_processor = processor_name

        # 计算FPS
        finish_time = time.time()
        time_diff = finish_time - start_time
        fps = 1 / time_diff if time_diff > 0 else float('inf')

        # 显示FPS
        if self.show_fps:
            cv2.putText(processed_image, f"FPS: {fps:.2f}", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 转换颜色空间
        if output_rgb:
            processed_image = cv2.cvtColor(processed_image, cv2.COLOR_BGR2RGB)

        self.current_image = processed_image
        return processed_image

    def get_processor_result(self, processor_name):
        """获取指定处理器的结果
        Args:
            processor_name: 处理器名称
        Returns:
            dict: 处理结果，包含图像、信息和处理器引用
        """
        return self.results.get(processor_name)

    def get_all_results(self):
        """获取所有处理器的结果
        Returns:
            dict: 所有处理结果
        """
        return self.results

    def resize_image(self, image):
        if image is None:
            raise ValueError("Input image is None.")
        
        h, w = image.shape[:2]
        max_size = self.max_disp_pixel
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            new_size = (int(w * scale), int(h * scale))
            image = cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
        return image
    def save(self, image, processor_name):
        save_dir = os.path.join("processed_images", processor_name)
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{self.name}.jpg")
        cv2.imwrite(save_path, image)
        return save_path

    def get_active_processor(self):
        """获取当前活动的处理器名称
        Returns:
            str: 处理器名称，如果没有活动处理器则返回None
        """
        return self.active_processor
    
    def cleanup(self):
        """
        清理资源的方法。
        """
        self.logger.info("ImageProcessor: 执行清理工作。")
        # 可以在这里关闭文件句柄、释放模型等

