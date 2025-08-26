from .base import ImageProcessor
import mediapipe as mp
import cv2
import os
import numpy as np
import math

class PoseProcessor(ImageProcessor):
    def __init__(self, config_manager=None, log_manager=None):
        super().__init__(config_manager, log_manager)
        self.logger.info('PoseProcessor 初始化开始')
        # 更新保存路径
        self.output_dir = os.path.join(self.output_dir, 'pose')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 从配置文件加载处理器特定配置
        pose_config = self.config.get('image_processing.processors.pose', {}) if self.config else {}
        self.enable_draw = pose_config.get('draw', True)
        self.enable_save = pose_config.get('save', False)
        
        # 初始化姿势检测器
        self.pose = mp.solutions.pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 姿势相关属性
        self.results = None
        self.pose_state = {
            'is_jumping': False,
            'jump_height': 0.0,
            'left_arm_angle': 0.0,
            'right_arm_angle': 0.0,
            'body_rotation': 0.0,
            'standing_straight': False
        }
        
        # 显示相关配置
        self.font_scale = 0.5
        self.font_thickness = 2
        self.normal_color = (0, 255, 0)
        self.warning_color = (0, 0, 255)

    def _calculate_angle(self, a, b, c):
        """计算三个点形成的角度"""
        a = np.array([a.x, a.y])
        b = np.array([b.x, b.y])
        c = np.array([c.x, c.y])
        
        radians = np.arctan2(c[1] - b[1], c[0] - b[0]) - \
                 np.arctan2(a[1] - b[1], a[0] - b[0])
        angle = np.abs(radians * 180.0 / np.pi)
        
        if angle > 180.0:
            angle = 360 - angle
            
        return angle

    def _analyze_pose(self, landmarks):
        """分析姿势状态"""
        # 获取关键点
        left_ankle = landmarks[mp.solutions.pose.PoseLandmark.LEFT_ANKLE.value]
        right_ankle = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_ANKLE.value]
        left_hip = landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP.value]
        right_hip = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_HIP.value]
        left_shoulder = landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER.value]
        right_shoulder = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER.value]
        left_elbow = landmarks[mp.solutions.pose.PoseLandmark.LEFT_ELBOW.value]
        right_elbow = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_ELBOW.value]
        left_wrist = landmarks[mp.solutions.pose.PoseLandmark.LEFT_WRIST.value]
        right_wrist = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_WRIST.value]
        
        # 计算跳跃高度（脚踝相对于髋部的位置）
        hip_y = (left_hip.y + right_hip.y) / 2
        ankle_y = (left_ankle.y + right_ankle.y) / 2
        jump_height = hip_y - ankle_y
        
        # 判断是否跳跃（脚踝高于一定阈值）
        normal_height = 0.3  # 正常站立时脚踝到髋部的距离比例
        self.pose_state['is_jumping'] = jump_height < normal_height
        self.pose_state['jump_height'] = max(0, (normal_height - jump_height) * 100)  # 转换为百分比
        
        # 计算手臂角度
        self.pose_state['left_arm_angle'] = self._calculate_angle(
            left_shoulder, left_elbow, left_wrist)
        self.pose_state['right_arm_angle'] = self._calculate_angle(
            right_shoulder, right_elbow, right_wrist)
        
        # 计算身体旋转（基于肩膀线）
        shoulder_angle = math.degrees(math.atan2(
            right_shoulder.y - left_shoulder.y,
            right_shoulder.x - left_shoulder.x
        ))
        self.pose_state['body_rotation'] = shoulder_angle
        
        # 判断是否站直（基于髋部和肩部的垂直对齐）
        hip_center = np.array([(left_hip.x + right_hip.x) / 2, (left_hip.y + right_hip.y) / 2])
        shoulder_center = np.array([(left_shoulder.x + right_shoulder.x) / 2, 
                                  (left_shoulder.y + right_shoulder.y) / 2])
        vertical_angle = abs(math.degrees(math.atan2(
            shoulder_center[0] - hip_center[0],
            shoulder_center[1] - hip_center[1]
        )))
        self.pose_state['standing_straight'] = vertical_angle < 10  # 10度以内认为是站直

    def process(self, input_source):
        """处理输入图像"""
        try:
            # 打开图像
            self.image, self.name = self.open(input_source)
            if self.image is None:
                return None
            
            # 处理图像获取姿态检测结果
            self.results = self.pose.process(self.image)
            
            # 更新追踪信息
            if self.results.pose_landmarks:
                # 获取所有关键点坐标
                h, w = self.image.shape[:2]
                landmarks = [(lm.x * w, lm.y * h) for lm in self.results.pose_landmarks.landmark]
                landmarks = np.array(landmarks)
                
                # 计算边界框
                x, y, width, height = cv2.boundingRect(landmarks.astype(np.int32))
                
                # 更新追踪信息
                self.update_tracking((x, y, width, height), self.image.shape)
                self.confidence = 1.0  # 姿态检测没有置信度，设为1.0
                
                # 分析姿势状态
                self._analyze_pose(self.results.pose_landmarks.landmark)
            else:
                self.update_tracking(None, self.image.shape)
            
            # 根据配置决定是否绘制
            if self.enable_draw:
                self.image_processed = self.draw(self.image)
            else:
                self.image_processed = self.image.copy()
            
            # 根据配置决定是否保存
            if self.enable_save and self.tracker.target_found:
                self.save(self.image_processed)
            
            return self.image_processed
            
        except Exception as e:
            print(f"Error processing image: {e}")
            return self.image

    def draw(self, image):
        """绘制姿势检测结果"""
        if self.results.pose_landmarks:
            # 绘制骨架
            mp.solutions.drawing_utils.draw_landmarks(
                image, 
                self.results.pose_landmarks, 
                mp.solutions.pose.POSE_CONNECTIONS,
                mp.solutions.drawing_styles.get_default_pose_landmarks_style())
            
            # 绘制关键点序号
            for i, landmark in enumerate(self.results.pose_landmarks.landmark):
                x, y = int(landmark.x * image.shape[1]), int(landmark.y * image.shape[0])
                cv2.putText(image, str(i), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
            
            # 绘制追踪信息
            image = self.draw_tracking_info(image)
            
            # 显示姿势状态
            y_offset = 30
            
            # 跳跃状态
            jump_color = self.warning_color if self.pose_state['is_jumping'] else self.normal_color
            cv2.putText(image, 
                       f"Jumping: {'Yes' if self.pose_state['is_jumping'] else 'No'} ({self.pose_state['jump_height']:.1f}%)", 
                       (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       self.font_scale, 
                       jump_color, 
                       self.font_thickness)
            y_offset += 30
            
            # 手臂角度
            cv2.putText(image, 
                       f"Arms: L{self.pose_state['left_arm_angle']:.1f}° R{self.pose_state['right_arm_angle']:.1f}°", 
                       (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       self.font_scale, 
                       self.normal_color, 
                       self.font_thickness)
            y_offset += 30
            
            # 身体旋转
            cv2.putText(image, 
                       f"Body Rotation: {self.pose_state['body_rotation']:.1f}°", 
                       (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       self.font_scale, 
                       self.normal_color, 
                       self.font_thickness)
            y_offset += 30
            
            return image
        return image

    def get_result_info(self):
        """获取处理结果信息"""
        # 获取追踪信息
        tracking_info = self.get_tracking_status()
        
        # 获取姿态信息
        pose_info = {
            "pose_state": {
                "is_jumping": bool(self.pose_state['is_jumping']),
                "jump_height": float(self.pose_state['jump_height']),
                "left_arm_angle": float(self.pose_state['left_arm_angle']),
                "right_arm_angle": float(self.pose_state['right_arm_angle']),
                "body_rotation": float(self.pose_state['body_rotation']),
                "standing_straight": bool(self.pose_state['standing_straight'])
            }
        }
        
        # 合并信息
        return {**tracking_info, **pose_info}