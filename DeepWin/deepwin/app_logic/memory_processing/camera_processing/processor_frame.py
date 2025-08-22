from .base import CameraProcessorBase
from image_processing.manager import ImageManager
import cv2

class ProcessorFrame():
    def __init__(self, frame_manager=None, frame_processors=None):
        self.frame_processors = frame_processors if frame_processors is not None else []
        self.image_processing_manager = frame_manager
        self.scale = 1.0  # 添加缩放比例

    def set_frame_processors(self, processors):
        """设置帧处理器列表"""
        self.frame_processors = processors if processors is not None else []

    def process(self, frame, is_display=False):
        """处理帧"""
        if frame is None:
            return None

        try:
            # 如果没有处理器或处理器管理器，直接返回原始帧
            if not self.frame_processors or self.image_processing_manager is None:
                processed_frame = frame
            else:
                processed_frame = self.image_processing_manager.process_image_list(frame, self.frame_processors, output_rgb=False)
            
            if is_display:
                # 应用缩放
                if self.scale != 1.0:
                    height, width = processed_frame.shape[:2]
                    new_width = int(width * self.scale)
                    new_height = int(height * self.scale)
                    processed_frame = cv2.resize(processed_frame, (new_width, new_height))
                
                # 显示帧
                cv2.imshow('Camera Stream', processed_frame)
                cv2.waitKey(1)

            return processed_frame
        except Exception as e:
            print(f"Frame processing error: {e}")
            return frame  # 出错时返回原始帧
        

    def adjust_scale(self, increase=True):
        """调整显示比例"""
        if increase:
            self.scale = min(3.0, self.scale + 0.1)  # 最大放大3倍
        else:
            self.scale = max(0.5, self.scale - 0.1)  # 最小缩小0.5倍
        print(f"Display scale: {self.scale:.1f}x")
    
