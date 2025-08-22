from .base import ImageProcessor
from insightface.app import FaceAnalysis
import cv2
import os
from .decorators import display_fps
import numpy as np
from .config_manager import ConfigManager
import datetime
import time

class FaceRecognitionProcessor(ImageProcessor):
    def __init__(self):
        super().__init__()
        print('FaceRecognitionProcessor init\r\n')
        
        # 获取配置
        self.config = ConfigManager()
        processor_config = self.config.get('processors', {}).get('face_recognition', {})
        
        # 从配置中读取参数
        self.enable_draw = processor_config.get('draw', True)
        self.enable_save = processor_config.get('save', True)
        self.save_faces = processor_config.get('save_faces', True)
        self.face_scale = processor_config.get('face_scale', 1.2)  # 人脸框放大倍率
        det_thresh = processor_config.get('det_thresh', 0.25)
        det_size = tuple(processor_config.get('det_size', [640, 640]))
        ctx_id = processor_config.get('ctx_id', 0)
        
        # 更新保存路径
        self.output_dir = os.path.join(self.output_dir, 'face_recognition')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化人脸分析器
        self.face_analyzer = FaceAnalysis(providers=['CUDAExecutionProvider'])
        self.face_analyzer.prepare(
            ctx_id=ctx_id,
            det_thresh=det_thresh,
            det_size=det_size
        )
        self.faces = []

    def _adjust_bbox(self, bbox, scale, img_shape):
        """调整边界框大小
        Args:
            bbox: 原始边界框 [x1, y1, x2, y2]
            scale: 放大倍率
            img_shape: 图像形状 (height, width)
        Returns:
            调整后的边界框
        """
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        new_width = width * scale
        new_height = height * scale
        
        new_x1 = max(0, int(center_x - new_width / 2))
        new_y1 = max(0, int(center_y - new_height / 2))
        new_x2 = min(img_shape[1], int(center_x + new_width / 2))
        new_y2 = min(img_shape[0], int(center_y + new_height / 2))
        
        return [new_x1, new_y1, new_x2, new_y2]

    # def save(self, image, processor_name):
    #     """保存处理后的图像和检测到的人脸
    #     Args:
    #         image: 输入图像
    #         processor_name: 处理器名称
    #     Returns:
    #         str: 保存的主图像路径
    #     """
    #     # 首先调用父类的save方法保存主图像
    #     save_path = super().save(image, processor_name)
        
    #     # 如果配置了保存人脸，则保存每个检测到的人脸
    #     if self.save_faces and self.faces:
    #         face_dir = os.path.join(self.save_dir, processor_name, 'faces')
    #         if not os.path.exists(face_dir):
    #             os.makedirs(face_dir)
            
    #         # 保存每个检测到的人脸
    #         for i, face in enumerate(self.faces):
    #             # 获取并调整边界框
    #             bbox = face.bbox.astype(int)
    #             adjusted_bbox = self._adjust_bbox(bbox, self.face_scale, image.shape)
                
    #             # 裁剪人脸图像
    #             face_crop = self.image[adjusted_bbox[1]:adjusted_bbox[3],   # image 是绘图后的人脸
    #                             adjusted_bbox[0]:adjusted_bbox[2]]
                
    #             # 生成人脸图像的保存路径
    #             timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    #             face_filename = f"{timestamp}_face_{i}{self.extension}"
    #             face_path = os.path.join(face_dir, face_filename)
                
    #             # 保存人脸图像
    #             cv2.imwrite(face_path, face_crop)
    #             print(f"Saved face {i+1} to {face_path}")
        
    #     return save_path

    def reset(self):
        # 重置处理器的状态
        self.faces = []
        self.image = None
        self.name = None

    def process(self, input_source):
        # 打开图像
        self.image, self.name = self.open(input_source)
        if self.image is None:
            return None
        
        # 处理图像获取人脸识别结果
        self.faces = self.face_analyzer.get(self.image)
        
        # 更新追踪信息
        if self.faces:
            # 获取置信度最高的人脸
            max_face = max(self.faces, key=lambda x: x.det_score)
            bbox = max_face.bbox.astype(int)
            x1, y1, x2, y2 = bbox
            width = x2 - x1
            height = y2 - y1
            
            # 更新追踪信息
            self.update_tracking((x1, y1, width, height), self.image.shape)
            self.confidence = float(max_face.det_score)
        else:
            self.update_tracking(None, self.image.shape)
        
        # 根据配置决定是否绘制
        if self.enable_draw:
            self.image_processed = self.draw(self.image)
        else:
            self.image_processed = self.image.copy()
        
        # 根据配置决定是否保存
        if self.enable_save:
            self.save(self.image_processed)
            if self.save_faces and self.faces:
                self._save_faces()
        
        return self.image_processed

    def draw(self, image):
        # 绘制人脸识别结果
        rimg = self.face_analyzer.draw_on(image, self.faces)
        
        # 绘制追踪信息
        rimg = self.draw_tracking_info(rimg)
        
        return rimg

    def _save_faces(self):
        """保存检测到的人脸"""
        if not self.faces:
            return
            
        face_dir = os.path.join(self.output_dir, 'faces')
        os.makedirs(face_dir, exist_ok=True)
        
        for i, face in enumerate(self.faces):
            # 获取并调整边界框
            bbox = face.bbox.astype(int)
            adjusted_bbox = self._adjust_bbox(bbox, self.face_scale, self.image.shape)
            
            # 裁剪人脸图像
            face_crop = self.image[adjusted_bbox[1]:adjusted_bbox[3],
                                 adjusted_bbox[0]:adjusted_bbox[2]]
            
            # 生成保存路径
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            face_filename = f"{timestamp}_face_{i}.jpg"
            face_path = os.path.join(face_dir, face_filename)
            
            # 保存人脸图像
            cv2.imwrite(face_path, face_crop)
            print(f"Saved face {i+1} to {face_path}")

    def get_result_info(self):
        """获取处理结果信息"""
        # 获取追踪信息
        tracking_info = self.get_tracking_status()
        
        # 获取人脸识别信息
        face_info = {
            "num_faces": len(self.faces),
            "faces": []
        }
        
        for face in self.faces:
            face_data = {
                "bbox": face.bbox.tolist(),
                "score": float(face.det_score),
                "gender": int(face.gender),
                "age": float(face.age)
            }
            face_info["faces"].append(face_data)
        
        # 合并信息
        return {**tracking_info, **face_info}