import cv2
import numpy as np
from .tracker_base import ImageTracker

class CVTracker(ImageTracker):
    """OpenCV跟踪器"""
    def __init__(self, tracker_type='CSRT'):
        super().__init__()
        self.tracker_type = tracker_type
        self.tracker = None
        self.initialized = False
        
        # 可用的跟踪器类型
        self.OPENCV_TRACKERS = {
            'CSRT': cv2.TrackerCSRT_create,
            'KCF': cv2.TrackerKCF_create,
            'MOSSE': cv2.TrackerMOSSE_create,
        }

    def init(self, image, bbox):
        """初始化跟踪器
        Args:
            image: 初始图像
            bbox: 初始边界框 (x, y, w, h)
        """
        if self.tracker_type not in self.OPENCV_TRACKERS:
            raise ValueError(f"Unsupported tracker type: {self.tracker_type}")
            
        self.tracker = self.OPENCV_TRACKERS[self.tracker_type]()
        self.tracker.init(image, tuple(bbox))
        self.initialized = True
        self.update(bbox, image.shape)

    def track(self, image):
        """跟踪目标
        Args:
            image: 当前图像
        Returns:
            bbox: 目标框 (x, y, w, h) 或 None
        """
        if not self.initialized:
            return None
            
        success, bbox = self.tracker.update(image)
        if success:
            self.update(bbox, image.shape)
            return bbox
        else:
            self.target_found = False
            return None

    def reset(self):
        """重置跟踪器"""
        super().reset()
        self.tracker = None
        self.initialized = False 