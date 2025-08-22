from .base import ImageProcessor
from ultralytics import YOLO
import cv2
import os
import numpy as np
import time
from collections import defaultdict

class YoloProcessor(ImageProcessor):
    def __init__(self, model_type=None):
        super().__init__()
        print('YoloProcessor init\r\n')
        # 更新保存路径
        self.output_dir = os.path.join(self.output_dir, 'yolo')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 从配置文件加载处理器特定配置
        yolo_config = self.config.get('processors', 'yolo')
        self.enable_draw = yolo_config.get('draw', True)
        self.enable_save = yolo_config.get('save', False)
        
        # 加载模型
        if model_type is None:
            self.model_type = yolo_config.get('model_type', 'yolo11n.pt')
        else:
            self.model_type = model_type
        self.conf_thresh = yolo_config.get('conf_thresh', 0.25)
        self.task = yolo_config.get('task', 'detect')  # detect, segment, classify
        self.track = yolo_config.get('track', False)   # 是否启用追踪
        
        try:
            self.model = YOLO(self.model_type)
        except Exception as e:
            print(f"Error loading YOLO model: {e}")
            self.model = None
        
        # 结果存储
        self.results = None
        self.tracked_objects = {}  # 追踪的目标
        
        # 显示配置
        self.font_scale = 0.5
        self.font_thickness = 2
        self.box_thickness = 2

    def process(self, input_source):
        """处理输入图像"""
        # 打开图像
        self.image, self.name = self.open(input_source)
        if self.image is None or self.model is None:
            return None
            
        try:
            # 根据任务类型处理图像
            if self.track:
                # 使用track方法时直接指定conf_thresh，避免后续过滤
                self.results = self.model.track(
                    self.image,
                    persist=True,
                    conf=self.conf_thresh,  # 添加置信度阈值
                    verbose=False
                )
                
                # Get the boxes and track IDs
                boxes = self.results[0].boxes.xywh.cpu()
                track_ids = self.results[0].boxes.id.int().cpu().tolist()

                # 更新多点追踪
                self.tracker.update_multi_tracks(boxes, track_ids)
            else:
                self.results = self.model(
                    self.image,
                    conf=self.conf_thresh,
                    verbose=False
                )
                
                # 普通检测模式下只更新单点追踪
                if len(self.results) > 0 and len(self.results[0].boxes) > 0:
                    boxes = self.results[0].boxes
                    conf_scores = boxes.conf.cpu().numpy()
                    max_conf_idx = np.argmax(conf_scores)
                    bbox = boxes.xywh[max_conf_idx].cpu().numpy()  # 直接使用xywh格式
                    self.update_tracking(bbox, self.image.shape)
                    self.confidence = float(conf_scores[max_conf_idx])
                else:
                    self.update_tracking(None, self.image.shape)
            
            # 根据配置决定是否绘制
            if self.enable_draw:
                self.image_processed = self.draw(self.image)
            else:
                self.image_processed = self.image.copy()
            
            return self.image_processed
            
        except Exception as e:
            print(f"Error processing image: {e}")
            import traceback
            traceback.print_exc()
            return self.image

    def draw(self, image):
        """绘制检测结果"""
        if self.results and len(self.results) > 0:
            
            # 使用YOLO的绘制功能绘制边界框和标签
            for result in self.results:
                annotated_frame = result.plot(boxes=True, labels=True)
            
            # 如果启用追踪，绘制轨迹
            if self.track:
                try:
                    annotated_frame = self.tracker.draw_multi_tracks(annotated_frame)
                except Exception as e:
                    print(f"Error drawing multi tracks: {e}")
            
            return annotated_frame
        return image

    def get_result_info(self):
        """获取处理结果信息"""
        # 获取基础追踪信息
        tracking_info = self.get_tracking_status()
        
        # 获取多点追踪信息（如果启用了追踪）
        if self.track:
            multi_track_info = self.tracker.get_multi_track_status()
        else:
            multi_track_info = {}
        
        # 获取检测结果信息
        detection_info = {
            "detections": []
        }
        
        if self.results and len(self.results) > 0:
            boxes = self.results[0].boxes
            for box in boxes:
                det_info = {
                    "bbox": [float(x) for x in box.xyxy[0].cpu().numpy()],  # 转换为普通float
                    "class": int(box.cls),
                    "class_name": self.model.names[int(box.cls)],
                    "confidence": float(box.conf)  # 转换为普通float
                }
                
                # 如果启用了追踪，添加追踪ID
                if self.track and hasattr(box, 'id'):
                    det_info["track_id"] = int(box.id.item())
                
                detection_info["detections"].append(det_info)
        
        # 合并所有信息
        return {**tracking_info, **multi_track_info, **detection_info}
    
    # 重新设定模型
    def set_model(self, model_type):
        self.model_type = model_type
        self.model.load(self.model_type)
