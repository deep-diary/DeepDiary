"""
DeepWin 图像处理包

这是一个功能丰富的图像处理包，集成了多种图像处理功能，
包括人脸检测、人脸识别、姿态检测、手势识别、OCR 文字识别、QR 码处理等。

主要组件:
- ImageManager: 图像处理管理器，统一管理所有处理器
- ImageProcessor: 图像处理器基类
- 各种专用处理器: 人脸检测、识别、姿态、手势、OCR、QR码、YOLO等
- 追踪器: 支持目标追踪和轨迹分析
- 配置管理: 统一的配置管理接口
- 日志管理: 统一的日志记录接口

使用示例:
    from deepwin.app_logic.memory_processing.image_processing import ImageManager
    
    manager = ImageManager()
    result = manager.process_image("image.jpg", "face_detection")
    info = manager.get_processor("face_detection").get_result_info()
"""

from .manager import ImageManager
from .base import ImageProcessor

# 导出主要的公共接口
__all__ = [
    'ImageManager',
    'ImageProcessor'
]

# 版本信息
__version__ = '1.0.0'
__author__ = 'DeepWin Team'
__description__ = 'DeepWin 图像处理包 - 集成多种图像处理功能'
