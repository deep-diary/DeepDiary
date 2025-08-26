from .base import ImageProcessor
import mediapipe as mp
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_mesh = mp.solutions.face_mesh
import cv2
import os
import numpy as np

class FaceMeshProcessor(ImageProcessor):
    def __init__(self, config_manager=None, log_manager=None):
        super().__init__(config_manager, log_manager)
        self.logger.info('FaceMeshProcessor 初始化开始')
        # 更新保存路径
        self.output_dir = os.path.join(self.output_dir, 'face_mesh')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化 mediapipe 人脸网格检测器
        self.face_mesh = mp.solutions.face_mesh.FaceMesh(
            static_image_mode=False,
            max_num_faces=2,
            refine_landmarks=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 从配置文件加载处理器特定配置
        mesh_config = self.config.get('image_processing.processors.face_mesh', {}) if self.config else {}
        self.enable_draw = mesh_config.get('draw', True)
        self.enable_save = mesh_config.get('save', False)
        
        # 特征点相关属性
        self.landmarks = None
        self.face_oval = None  # 脸部轮廓点
        self.left_eye = None   # 左眼点
        self.right_eye = None  # 右眼点
        self.lips = None       # 嘴唇点
        
        # 从配置文件加载标定参数
        calibration = self.config.get('image_processing.processors.face_mesh.calibration', {}) if self.config else {}
        self.ref_face_width_px = calibration.get('ref_face_width_px', 300)  # 50cm处人脸宽度对应的像素值
        self.ref_face_width_cm = calibration.get('ref_face_width_cm', 15)   # 标准人脸宽度(cm)
        self.ref_distance_cm = calibration.get('ref_distance_cm', 50)        # 标定距离(cm)
        
        # 眼睛状态阈值
        self.eye_aspect_ratio_threshold = 0.28  # 眼睛开闭判断阈值
        self.eye_gaze_threshold = 0.2         # 眼球偏移判断阈值

        # 嘴巴状态阈值
        self.mouth_aspect_ratio_threshold = 0.8  # 嘴巴开合判断阈值
        
        # 关键点索引
        self.left_eye_indices = [159,145,33,133]  # 左眼轮廓点
        self.right_eye_indices = [386,374,362,263]  # 右眼轮廓点
        self.left_iris_indices = [468, 469, 470, 471, 472]   # 左眼珠点
        self.right_iris_indices = [473, 474, 475, 476, 477]  # 右眼珠点
        # self.mouth_indices = [0, 37, 39, 40, 267, 269, 270, 291, 321, 375, 405]  # 嘴唇点
        self.mouth_outline_indices = [0, 17, 61, 291]  # 嘴巴轮廓点
        self.eyebrow_indices = {
            'left': [70, 63, 105, 66, 107],   # 左眉毛点
            'right': [336, 296, 334, 293, 300] # 右眉毛点
        }
        
        # 状态信息
        self.face_state = {
            'left_eye': {'open': False, 'gaze': 'center'},
            'right_eye': {'open': False, 'gaze': 'center'},
            'cross_eyed': False,
            'mouth_open': False,
            'frowning': False,
            'head_rotation': {'pitch': 0, 'yaw': 0, 'roll': 0},
            'face_distance': 0
        }

        # 添加显示相关的配置
        self.font_scale = 0.5
        self.font_thickness = 2
        self.distance_warning_threshold = 60  # 距离警告阈值(cm)
        
        # 状态颜色配置
        self.normal_color = (0, 255, 0)    # 正常状态颜色(BGR)
        self.warning_color = (0, 0, 255)    # 警告状态颜色(BGR)

    def _calculate_eye_aspect_ratio(self, eye_points):
        """计算眼睛纵横比（用于判断开闭）"""
        # 垂直距离
        v1 = np.linalg.norm(eye_points[0] - eye_points[1])
        # 水平距离
        h = np.linalg.norm(eye_points[2] - eye_points[3])
        # 计算比率
        ear = v1 / h
        return ear

    def _analyze_eye_gaze(self, iris_points, eye_points):
        """分析眼球方向"""
        # 计算虹膜中心
        iris_center = np.mean(iris_points, axis=0)
        # 计算眼睛边界框
        eye_left = np.min(eye_points[:, 0])
        eye_right = np.max(eye_points[:, 0])
        # 计算虹膜中心在眼睛宽度中的相对位置
        relative_pos = (iris_center[0] - eye_left) / (eye_right - eye_left)
        
        if relative_pos < 0.4:
            return 'left'
        elif relative_pos > 0.6:
            return 'right'
        return 'center'

    def _calculate_mouth_aspect_ratio(self, mouth_points):
        """计算嘴巴开合程度"""
        # 垂直距离
        v = np.linalg.norm(mouth_points[0] - mouth_points[1])
        # 水平距离
        h = np.linalg.norm(mouth_points[2] - mouth_points[3])
        return v / h

    def _analyze_eyebrows(self, landmarks, face_width):
        """分析眉毛状态（判断是否皱眉）"""
        # 计算眉毛曲率和高度变化
        left_eyebrow = np.array([(landmarks[idx].x, landmarks[idx].y) for idx in self.eyebrow_indices['left']])
        right_eyebrow = np.array([(landmarks[idx].x, landmarks[idx].y) for idx in self.eyebrow_indices['right']])
        
        # 简单的皱眉判断：检查眉毛中点是否低于两端
        def check_frown(eyebrow):
            mid_y = eyebrow[2][1]
            ends_y = (eyebrow[0][1] + eyebrow[-1][1]) / 2
            return mid_y > ends_y
        
        return check_frown(left_eyebrow) and check_frown(right_eyebrow)

    def _estimate_head_pose(self, landmarks):
        """估计头部姿态"""
        # 使用关键点估计头部旋转
        face_3d = []
        face_2d = []
        
        for idx, lm in enumerate(landmarks):
            if idx in [33, 263, 1, 61, 291, 199]:
                x, y = lm.x, lm.y
                z = lm.z
                face_3d.append([x, y, z])
                face_2d.append([x, y])
        
        face_3d = np.array(face_3d, dtype=np.float64)
        face_2d = np.array(face_2d, dtype=np.float64)
        
        # 使用solvePnP估计头部姿态
        focal_length = self.image.shape[1]
        center = (self.image.shape[1]/2, self.image.shape[0]/2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype=np.float64)
        dist_coeffs = np.zeros((4,1))
        
        success, rotation_vec, translation_vec = cv2.solvePnP(
            face_3d, face_2d, camera_matrix, dist_coeffs)
        
        if success:
            rotation_mat, _ = cv2.Rodrigues(rotation_vec)
            angles = self._rotation_matrix_to_angles(rotation_mat)
            return angles
        return {'pitch': 0, 'yaw': 0, 'roll': 0}

    def _estimate_face_distance(self, face_width_px):
        """估计人脸距离（考虑头部旋转）"""
        # 基于相似三角形原理计算距离
        distance = (self.ref_face_width_px * self.ref_distance_cm) / (face_width_px)
        
        # 考虑头部旋转的影响
        if abs(self.face_state['head_rotation']['yaw']) > 5:
            # 根据偏航角补偿距离估计
            yaw_rad = np.radians(abs(self.face_state['head_rotation']['yaw']))
            distance *= np.cos(yaw_rad)
        
        return distance

    def process(self, input_source):
        """处理输入图像"""
        # 打开图像
        self.image, self.name = self.open(input_source)
        if self.image is None:
            return None
        
        # 处理图像获取人脸网格结果
        self.results = self.face_mesh.process(self.image)
        
        # 更新追踪信息
        if self.results.multi_face_landmarks:
            landmarks = self.results.multi_face_landmarks[0].landmark
            self.landmarks = landmarks
            
            # 获取脸部轮廓点
            h, w = self.image.shape[:2]
            face_points = []
            for idx in mp.solutions.face_mesh.FACEMESH_FACE_OVAL:
                point = landmarks[idx[0]]
                x, y = int(point.x * w), int(point.y * h)
                face_points.append((x, y))
            
            if face_points:
                # 计算脸部边界框
                face_points = np.array(face_points)
                x, y, width, height = cv2.boundingRect(face_points)
                
                # 更新追踪信息
                self.update_tracking(bbox=(x, y, width, height), image_shape=self.image.shape)
                
                # 保存特征点组
                self.face_oval = face_points
                self.left_eye = self._get_landmark_points([159,145,33,133], w, h)
                self.right_eye = self._get_landmark_points([386,374,362,26], w, h)
                self.lips = self._get_landmark_points([0, 17, 61, 29], w, h)
                
                # 分析面部状态
                self._analyze_face_state(landmarks, w, h)
        else:
            self.update_tracking(None, self.image.shape)
            self.landmarks = None
            self.face_oval = None
            self.left_eye = None
            self.right_eye = None
            self.lips = None
        
        # 根据配置决定是否绘制
        if self.enable_draw:
            self.image_processed = self.draw(self.image)
        else:
            self.image_processed = self.image.copy()
        
        # 根据配置决定是否保存
        if self.enable_save:
            self.save(self.image_processed)
        
        return self.image_processed

    def _get_landmark_points(self, indices, width, height):
        """获取特定索引的特征点坐标"""
        if not self.landmarks:
            return None
        points = []
        for idx in indices:
            point = self.landmarks[idx]
            x, y = int(point.x * width), int(point.y * height)
            points.append((x, y))
        return np.array(points)

    def draw(self, image):
        """绘制处理结果"""
        # 绘制人脸网格
        if self.results and self.results.multi_face_landmarks:
            for face_landmarks in self.results.multi_face_landmarks:
                mp_drawing.draw_landmarks(
                    image=image,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles
                    .get_default_face_mesh_tesselation_style())
                mp_drawing.draw_landmarks(
                    image=image,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_CONTOURS,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles
                    .get_default_face_mesh_contours_style())
                mp_drawing.draw_landmarks(
                    image=image,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_IRISES,
                    landmark_drawing_spec=None,
                    connection_drawing_spec=mp_drawing_styles
                    .get_default_face_mesh_iris_connections_style())
                # 绘制关键点序号
                # for i, landmark in enumerate(face_landmarks.landmark):
                #     x, y = int(landmark.x * image.shape[1]), int(landmark.y * image.shape[0])
                #     # 如果是嘴唇点，则用红色显示
                #     if i in self.mouth_outline_indices:
                #         cv2.putText(image, str(i), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                #     elif i in self.left_eye_indices or i in self.right_eye_indices:
                #         cv2.putText(image, str(i), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 0), 1)
                #     elif i in self.left_iris_indices or i in self.right_iris_indices:
                #         cv2.putText(image, str(i), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 255), 1)
                #     elif i in self.eyebrow_indices['left'] or i in self.eyebrow_indices['right']:
                #         cv2.putText(image, str(i), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 0, 0), 1)
                #     else:
                #         # cv2.putText(image, str(i), (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
                #         pass
            
         # 绘制追踪信息
            image = self.draw_tracking_info(image)
        
        # 绘制状态信息
        if self.face_state:
            y_offset = 60  # 在FPS信息下方显示
            
            # 左眼状态
            left_eye_color = self.normal_color if self.face_state['left_eye']['open'] else self.warning_color
            cv2.putText(image, 
                       f"Left Eye: {'Open' if self.face_state['left_eye']['open'] else 'Closed'}, Gaze: {self.face_state['left_eye']['gaze']}", 
                       (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       self.font_scale, 
                       left_eye_color, 
                       self.font_thickness)
            y_offset += 30
            
            # 右眼状态
            right_eye_color = self.normal_color if self.face_state['right_eye']['open'] else self.warning_color
            cv2.putText(image, 
                       f"Right Eye: {'Open' if self.face_state['right_eye']['open'] else 'Closed'}, Gaze: {self.face_state['right_eye']['gaze']}", 
                       (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       self.font_scale, 
                       right_eye_color, 
                       self.font_thickness)
            y_offset += 30
            
            # 嘴巴状态
            mouth_color = self.normal_color if self.face_state['mouth_open'] else self.warning_color
            cv2.putText(image, 
                       f"Mouth: {'Open' if self.face_state['mouth_open'] else 'Closed'}", 
                       (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       self.font_scale, 
                       mouth_color, 
                       self.font_thickness)
            y_offset += 30
            
            # 表情状态
            cv2.putText(image, 
                       f"Expression: {'Frowning' if self.face_state['frowning'] else 'Normal'}", 
                       (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       self.font_scale, 
                       self.normal_color, 
                       self.font_thickness)
            y_offset += 30
            
            # 距离状态
            distance = self.face_state['face_distance']
            distance_color = self.warning_color if distance < self.distance_warning_threshold else self.normal_color
            cv2.putText(image, 
                       f"Distance: {distance:.1f}cm", 
                       (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       self.font_scale, 
                       distance_color, 
                       self.font_thickness)
            y_offset += 30
            
            # 头部旋转状态
            rot = self.face_state['head_rotation']
            cv2.putText(image, 
                       f"Head: P{rot['pitch']:.0f} Y{rot['yaw']:.0f} R{rot['roll']:.0f}", 
                       (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 
                       self.font_scale, 
                       self.normal_color, 
                       self.font_thickness)
        
        return image

    def get_result_info(self):
        """获取处理结果信息"""
        # 获取追踪信息
        tracking_info = self.get_tracking_status()
        
        # 获取面部状态信息
        face_state_serializable = {
            'left_eye': {
                'open': int(self.face_state['left_eye']['open']),
                'gaze': self.face_state['left_eye']['gaze']
            },
            'right_eye': {
                'open': int(self.face_state['right_eye']['open']),
                'gaze': self.face_state['right_eye']['gaze']
            },
            'cross_eyed': int(self.face_state['cross_eyed']),
            'mouth_open': int(self.face_state['mouth_open']),
            'frowning': int(self.face_state['frowning']),
            'head_rotation': {
                'pitch': float(self.face_state['head_rotation']['pitch']),
                'yaw': float(self.face_state['head_rotation']['yaw']),
                'roll': float(self.face_state['head_rotation']['roll'])
            },
            'face_distance': float(self.face_state['face_distance'])
        }
        
        # 合并信息
        return {
            **tracking_info,
            "face_state": face_state_serializable,
        }

    def _rotation_matrix_to_angles(self, rotation_matrix):
        """将旋转矩阵转换为欧拉角
        Args:
            rotation_matrix: 3x3旋转矩阵
        Returns:
            dict: 包含pitch、yaw、roll的字典
        """
        try:
            # 从旋转矩阵计算欧拉角
            sy = np.sqrt(rotation_matrix[0, 0] * rotation_matrix[0, 0] +
                        rotation_matrix[1, 0] * rotation_matrix[1, 0])
            
            singular = sy < 1e-6

            if not singular:
                pitch = np.arctan2(rotation_matrix[2, 1], rotation_matrix[2, 2])
                yaw = np.arctan2(-rotation_matrix[2, 0], sy)
                roll = np.arctan2(rotation_matrix[1, 0], rotation_matrix[0, 0])
            else:
                pitch = np.arctan2(-rotation_matrix[1, 2], rotation_matrix[1, 1])
                yaw = np.arctan2(-rotation_matrix[2, 0], sy)
                roll = 0

            # 转换为角度
            pitch = np.degrees(pitch)
            yaw = np.degrees(yaw)
            roll = np.degrees(roll)

            return {
                'pitch': pitch,  # 俯仰角（上下点头）
                'yaw': yaw,      # 偏航角（左右转头）
                'roll': roll     # 翻滚角（头部倾斜）
            }
        except Exception as e:
            print(f"Error calculating rotation angles: {e}")
            return {'pitch': 0, 'yaw': 0, 'roll': 0}

    def _analyze_face_state(self, landmarks, w, h):
        """分析面部状态
        Args:
            landmarks: 面部特征点列表
            w: 图像宽度
            h: 图像高度
        """
        try:
            # 分析眼睛状态
            for eye in ['left', 'right']:
                eye_indices = self.left_eye_indices if eye == 'left' else self.right_eye_indices
                iris_indices = self.left_iris_indices if eye == 'left' else self.right_iris_indices
                
                # 获取眼睛和虹膜点
                eye_points = np.array([(landmarks[idx].x * w, landmarks[idx].y * h) 
                                     for idx in eye_indices])
                iris_points = np.array([(landmarks[idx].x * w, landmarks[idx].y * h) 
                                      for idx in iris_indices])
                
                # 分析眼睛状态
                ear = self._calculate_eye_aspect_ratio(eye_points)
                gaze = self._analyze_eye_gaze(iris_points, eye_points)
                
                self.face_state[f'{eye}_eye']['open'] = ear > self.eye_aspect_ratio_threshold
                self.face_state[f'{eye}_eye']['gaze'] = gaze
                print(f"{eye} eye aspect ratio: {ear:.2f}")
            
            # 检测斗鸡眼
            self.face_state['cross_eyed'] = (
                self.face_state['left_eye']['gaze'] == 'right' and 
                self.face_state['right_eye']['gaze'] == 'left'
            )
            
            # 分析嘴巴状态
            mouth_points = np.array([(landmarks[idx].x * w, landmarks[idx].y * h) 
                                   for idx in self.mouth_outline_indices])
            mar = self._calculate_mouth_aspect_ratio(mouth_points)
            self.face_state['mouth_open'] = mar > self.mouth_aspect_ratio_threshold
            print(f"Mouth aspect ratio: {mar:.2f}")
            
            # 分析眉毛状态
            self.face_state['frowning'] = self._analyze_eyebrows(landmarks, w)
            
            # 估计头部姿态
            self.face_state['head_rotation'] = self._estimate_head_pose(landmarks)
            
            # 估计人脸距离
            if self.face_oval is not None:
                face_width = cv2.boundingRect(self.face_oval)[2]
                self.face_state['face_distance'] = self._estimate_face_distance(face_width)
            
        except Exception as e:
            print(f"Error analyzing face state: {e}")
            import traceback
            traceback.print_exc()