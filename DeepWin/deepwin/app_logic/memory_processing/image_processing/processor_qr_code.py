from .base import ImageProcessor
import cv2
import qrcode
import numpy as np
import os
import time

class QrCodeProcessor(ImageProcessor):
    def __init__(self, config_manager=None, log_manager=None):
        super().__init__(config_manager, log_manager)
        self.logger.info('QrCodeProcessor 初始化开始')
        # 更新保存路径
        self.output_dir = os.path.join(self.output_dir, 'qr_code')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 从配置文件加载处理器特定配置
        qr_config = self.config.get('image_processing.processors.qr_code', {}) if self.config else {}
        self.enable_draw = qr_config.get('draw', True)
        self.enable_save = qr_config.get('save', False)
        
        # 初始化QR码检测器
        self.qr_detector = cv2.QRCodeDetector()
        
        # QR码相关属性
        self.qr_data = None          # 解码后的数据
        self.qr_points = None        # QR码顶点坐标
        self.qr_straight = None      # 校正后的QR码图像
        self.last_detection_time = 0 # 上次检测时间
        self.detection_history = []  # 检测历史记录

    def generate_qr_code(self, data, size=10, border=4):
        """生成QR码
        Args:
            data: 要编码的数据
            size: QR码大小
            border: 边框大小
        Returns:
            numpy.ndarray: QR码图像
        """
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # 生成PIL图像
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # 转换为OpenCV格式
            qr_array = np.array(qr_image)
            qr_array = qr_array.astype(np.uint8) * 255
            qr_array = cv2.cvtColor(qr_array, cv2.COLOR_GRAY2BGR)
            
            return qr_array
        except Exception as e:
            print(f"Error generating QR code: {e}")
            return None

    def process(self, input_source):
        """处理输入图像"""
        # 打开图像
        self.image, self.name = self.open(input_source)
        if self.image is None:
            return None
        
        try:
            # 检测和解码QR码
            data, points, straight = self.qr_detector.detectAndDecode(self.image)
            
            # 更新QR码属性
            self.qr_data = data
            self.qr_points = points
            self.qr_straight = straight
            
            # 更新追踪信息
            if points is not None and len(points) > 0:
                # 计算边界框
                points = points[0]  # 获取第一个QR码的点
                x = min(points[:, 0])
                y = min(points[:, 1])
                width = max(points[:, 0]) - x
                height = max(points[:, 1]) - y
                
                # 更新追踪信息
                self.update_tracking_info((x, y, width, height), self.image.shape)
                self.confidence = 1.0 if data else 0.5  # 如果成功解码则置信度为1
                
                # 记录检测结果
                current_time = time.time()
                self.detection_history.append({
                    'timestamp': current_time,
                    'data': data,
                    'position': (x, y),
                    'size': (width, height)
                })
                self.last_detection_time = current_time
            else:
                self.update_tracking_info(None, self.image.shape)
            
            # 根据配置决定是否绘制
            if self.enable_draw:
                self.image_processed = self.draw(self.image)
            else:
                self.image_processed = self.image.copy()
            
            # 根据配置决定是否保存
            if self.enable_save and self.target_found:
                self.save(self.image_processed)
            
            return self.image_processed
            
        except Exception as e:
            print(f"Error processing image: {e}")
            return self.image

    def draw(self, image):
        """绘制QR码检测结果"""
        if self.target_found and self.qr_points is not None:
            # 绘制QR码边界
            points = self.qr_points[0].astype(np.int32)
            cv2.polylines(image, [points], True, (0, 255, 0), 2)
            
            # 绘制中心点和追踪信息
            image = self.draw_tracking_info(image)
            
            # 显示解码数据
            if self.qr_data:
                cv2.putText(image, f"Data: {self.qr_data}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 
                           1, (0, 255, 0), 2)
                
                # 显示检测时间
                time_diff = time.time() - self.last_detection_time
                cv2.putText(image, f"Time: {time_diff:.2f}s", 
                           (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 
                           1, (0, 255, 0), 2)
        
        return image

    def get_result_info(self):
        """获取处理结果信息"""
        base_info = super().get_result_info()
        
        # 添加QR码相关信息，确保所有数值都是基本类型
        additional_info = {
            "qr_data": self.qr_data,
            "detection_time": float(self.last_detection_time),  # 转换为普通float
            "detection_history": [
                {
                    'timestamp': float(record['timestamp']),  # 转换为普通float
                    'data': record['data'],
                    'position': tuple(float(x) for x in record['position']),  # 转换为普通float
                    'size': tuple(float(x) for x in record['size'])  # 转换为普通float
                }
                for record in self.detection_history[-10:]  # 只保留最近10条记录
            ] if self.detection_history else None
        }
        
        return {**base_info, **additional_info} 