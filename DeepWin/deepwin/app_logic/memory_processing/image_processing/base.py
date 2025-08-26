from abc import ABC, abstractmethod
import cv2
import numpy as np
from PIL import Image
import os
import time
# 配置管理器现在从外部传入
from .tracker_base import ImageTracker
from deepwin.data_management.log_manager import LogManager

class ImageProcessor(ABC):
    """图像处理器基类"""
    def __init__(self, config_manager=None, log_manager=None):
        # 基础属性
        self.image = None
        self.image_processed = None
        self.name = None
        self.results = None
        
        # 配置管理
        self.config = config_manager
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
        
        # 追踪器实例化
        if self.config:
            tracking_config = self.config.get('image_processing.tracking', {})
            if tracking_config.get('enable_tracking', False):
                self.tracker = ImageTracker(self.config)
            else:
                self.tracker = None
        else:
            self.tracker = None
        
        # 路径相关 - 使用路径管理器
        from deepwin.utils.path_manager import get_path_manager
        path_manager = get_path_manager(self.config)
        self.output_dir = str(path_manager.get_image_processing_output_path())
        
        # 初始化追踪相关属性
        self.target_found = False
        self.target_center = None
        self.target_size = None
        self.error_x = 0.0
        self.error_y = 0.0
        self.confidence = 0.0

    def enable_tracking(self):
        """启用追踪功能"""
        if self.tracker is None:
            self.tracker = ImageTracker()

    def disable_tracking(self):
        """禁用追踪功能"""
        if self.tracker is not None:
            self.tracker.reset()
            self.tracker = None

    def update_tracking(self, bbox, image_shape):
        """更新追踪信息"""
        if self.tracker is not None:
            self.tracker.update(bbox, image_shape)

    def draw_tracking_info(self, image):
        """绘制追踪信息"""
        if self.tracker is not None and image is not None:
            # 创建图像副本以确保可写
            image_copy = image.copy()
            return self.tracker.draw(image_copy)
        return image

    def get_tracking_status(self):
        """获取追踪状态"""
        if self.tracker is not None:
            return self.tracker.get_status()
        return None

    def open(self, input_source, format='cv2'):
        """打开图像
        Args:
            input_source: 输入源（可以是路径、URL、图像数据）
            format: 输出格式 ('cv2', 'PIL', 'RGB')
        Returns:
            tuple: (image, name)
        """
        image = None
        name = None
        
        try:
            # 确保numpy已导入
            import numpy as np
            
            if isinstance(input_source, str) or hasattr(input_source, '__str__'):
                # 转换为字符串
                input_str = str(input_source)
                
                # 检查是否是URL
                if input_str.startswith(('http://', 'https://')):
                    # 使用requests下载图片
                    import requests
                    response = requests.get(input_str, timeout=10)
                    if response.status_code == 200:
                        # 将图片数据转换为numpy数组
                        image_array = np.asarray(bytearray(response.content), dtype=np.uint8)
                        name = input_str.split('/')[-1]  # 使用URL最后部分作为名称
                        if format == 'PIL':
                            # 直接转换为PIL图像
                            from io import BytesIO
                            image = Image.open(BytesIO(response.content))
                        else:
                            # 转换为OpenCV格式
                            image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                else:
                    # 本地文件路径
                    name = input_str
                    if format == 'PIL':
                        image = Image.open(input_str)
                    else:
                        image = cv2.imread(input_str)
            elif isinstance(input_source, np.ndarray):
                # 输入是OpenCV图像
                image = input_source.copy()  # 创建副本以避免修改原图
                name = "array"
            elif isinstance(input_source, Image.Image):
                # 输入是PIL图像
                image = input_source.copy()  # 创建副本以避免修改原图
                name = "PIL_image"
            else:
                raise ValueError("Unsupported input source type")

            # 格式转换
            if image is not None:
                if format == 'PIL' and isinstance(image, np.ndarray):
                    # OpenCV转PIL
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(image)
                elif format == 'cv2' and isinstance(image, Image.Image):
                    # PIL转OpenCV
                    image = np.array(image)
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                elif format == 'RGB' and isinstance(image, np.ndarray):
                    # BGR转RGB
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            return image, name
            
        except Exception as e:
            self.logger.error(f"打开图像失败: {e}")
            import traceback
            self.logger.debug(f"详细错误信息: {traceback.format_exc()}")
            return None, None

    def save(self, image=None):
        """保存图像
        Args:
            image: 要保存的图像，如果为None则保存当前图像
        Returns:
            str: 保存的文件路径
        """
        if image is None:
            image = self.image
        
        if image is None:
            self.logger.warning("没有图像可保存")
            return None
            
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f'image_{timestamp}.jpg'
        filepath = os.path.join(self.output_dir, filename)
        
        try:
            if isinstance(image, Image.Image):
                image.save(filepath)
            else:
                cv2.imwrite(filepath, image)
            self.logger.info(f"图像已保存到: {filepath}")
            return filepath
        except Exception as e:
            self.logger.error(f"保存图像失败: {e}")
            return None

    def clear(self):
        """清理输出目录"""
        try:
            for file in os.listdir(self.output_dir):
                file_path = os.path.join(self.output_dir, file)
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            self.logger.info(f"已清空输出目录: {self.output_dir}")
        except Exception as e:
            self.logger.error(f"清空输出目录失败: {e}")

    def reset(self):
        """重置处理器状态"""
        self.image = None
        self.name = None
        self.results = None
        self.target_found = False
        self.target_center = None
        self.target_size = None
        self.error_x = 0.0
        self.error_y = 0.0
        self.confidence = 0.0

    @abstractmethod
    def process(self, input_source):
        """处理输入图像"""
        pass

    def get_result_info(self):
        """获取处理结果信息"""
        return {
            "status": "Target detected" if self.target_found else "No target detected",
            "target_found": self.target_found,
            "target_center": self.target_center.tolist() if self.target_found else None,
            "target_size": self.target_size.tolist() if self.target_found else None,
            "error_x": self.error_x,
            "error_y": self.error_y,
            "confidence": self.confidence
        }
