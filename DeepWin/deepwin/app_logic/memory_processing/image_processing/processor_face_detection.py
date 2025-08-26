from .base import ImageProcessor
import mediapipe as mp
import cv2
import os

class FaceDetectionProcessor(ImageProcessor):
    def __init__(self, config_manager=None, log_manager=None):
        super().__init__(config_manager, log_manager)
        self.logger.info('FaceDetectionProcessor 初始化开始')
        # 更新保存路径 - 使用路径管理器
        from deepwin.utils.path_manager import get_path_manager
        path_manager = get_path_manager(self.config)
        self.output_dir = str(path_manager.get_image_processing_output_path('face_detection'))
        
        # 从配置文件加载处理器特定配置
        if self.config:
            face_config = self.config.get('image_processing.processors.face_detection', {})
            model_selection = face_config.get('model_selection', 1)
            min_detection_confidence = face_config.get('min_detection_confidence', 0.5)
        else:
            model_selection = 1
            min_detection_confidence = 0.5
            
        # 初始化 mediapipe 人脸检测器
        self.face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=model_selection,  # 0 for close range, 1 for far range
            min_detection_confidence=min_detection_confidence
        )
        
        self.enable_draw = face_config.get('draw', True) if self.config else True
        self.enable_save = face_config.get('save', False) if self.config else False
        
        self.logger.info('FaceDetectionProcessor 初始化完成')

    def process(self, input_source):
        """处理输入图像"""
        # 打开图像
        self.image, self.name = self.open(input_source)
        if self.image is None:
            return None
        
        # 处理图像获取人脸检测结果
        self.results = self.face_detection.process(self.image)
        
        # 更新追踪信息
        if self.results.detections:
            # 获取第一个检测到的人脸
            detection = self.results.detections[0]
            bbox = detection.location_data.relative_bounding_box
            
            # 计算人脸框的绝对坐标
            h, w = self.image.shape[:2]
            x = int(bbox.xmin * w)
            y = int(bbox.ymin * h)
            width = int(bbox.width * w)
            height = int(bbox.height * h)
            
            # 更新追踪信息
            self.update_tracking((x, y, width, height), self.image.shape)
            # 更新置信度
            self.confidence = detection.score[0]
        else:
            self.update_tracking(None, self.image.shape)
        
        # 根据配置决定是否绘制
        if self.enable_draw:
            self.image_processed = self.draw(self.image)
        else:
            # 只在不绘制时才拷贝原图
            self.image_processed = self.image.copy()
        
        # 根据配置决定是否保存
        if self.enable_save:
            self.save(self.image_processed)
        
        return self.image_processed

    def draw(self, image):
        """绘制检测结果和追踪信息"""
        if self.results and self.results.detections:
            h, w = image.shape[:2]
            
            for detection in self.results.detections:
                # 绘制人脸框
                bbox = detection.location_data.relative_bounding_box
                x = int(bbox.xmin * w)
                y = int(bbox.ymin * h)
                width = int(bbox.width * w)
                height = int(bbox.height * h)
                
                # 绘制矩形框
                cv2.rectangle(image, (x, y), (x + width, y + height), (0, 255, 0), 2)
            
            # 绘制追踪信息
            image = self.draw_tracking_info(image)
        
        return image

    def get_result_info(self):
        """获取处理结果信息"""
        # 确保追踪属性已正确设置
        if hasattr(self, 'tracker') and self.tracker is not None:
            tracking_status = self.tracker.get_status()
            if tracking_status:
                self.target_found = tracking_status.get('target_found', False)
                self.target_center = tracking_status.get('target_center', None)
                self.target_size = tracking_status.get('target_size', None)
                self.error_x = tracking_status.get('pixel_error', [0.0, 0.0])[0] if tracking_status.get('pixel_error') else 0.0
                self.error_y = tracking_status.get('pixel_error', [0.0, 0.0])[1] if tracking_status.get('pixel_error') else 0.0
        
        return {
            "status": "Face detected" if self.target_found else "No face detected",
            "target_found": self.target_found,
            "target_center": self.target_center.tolist() if self.target_found and self.target_center is not None and hasattr(self.target_center, 'tolist') else self.target_center,
            "target_size": self.target_size.tolist() if self.target_found and self.target_size is not None and hasattr(self.target_size, 'tolist') else self.target_size,
            "error_x": self.error_x,
            "error_y": self.error_y,
            "confidence": self.confidence
        } 