from .base import ImageProcessor
import mediapipe as mp
import cv2
import numpy as np
import os
from .filters import MeanFilter, KalmanFilter1D, FilterChain
import time
import json

class HandGestureProcessor(ImageProcessor):
    def __init__(self):
        super().__init__()
        print('HandGestureProcessor init\r\n')
        # 更新保存路径
        self.output_dir = os.path.join(self.output_dir, 'hand_gesture')
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 初始化 mediapipe 手势检测器
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=4,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mpDraw = mp.solutions.drawing_utils
        
        # 从配置文件加载处理器特定配置
        hand_config = self.config.get('processors', 'hand_gesture')
        self.enable_draw = hand_config.get('draw', True)
        self.enable_save = hand_config.get('save', False)
        
        # 夹取控制相关配置
        self.pinch_min_distance = hand_config.get('pinch_min_distance', 20)  # 最小夹取距离（像素）
        self.pinch_max_distance = hand_config.get('pinch_max_distance', 200)  # 最大夹取距离（像素）
        
        # 手势相关属性
        self.hand_landmarks = []  # 所有手的关键点
        self.handedness = []      # 手的左右属性
        self.index_finger_depths = []  # 食指深度信息
        
        # 手指关键点索引
        self.finger_tips = [4, 8, 12, 16, 20]  # 拇指到小指的指尖
        self.finger_pips = [2, 6, 10, 14, 18]  # 第一关节
        self.finger_mcps = [1, 5, 9, 13, 17]   # 指根
        
        # 手势分析结果
        self.hand_gestures = []  # 每只手的手势信息
        
        # 初始化滤波器
        self.pinch_filter = FilterChain([
            MeanFilter(window_size=3),  # 均值滤波消除突变
            KalmanFilter1D(process_variance=0.1, measurement_variance=1.0)  # 卡尔曼滤波平滑输出
        ])
        
        # 绘画相关状态
        self.is_drawing_mode_ready = False
        self.is_drawing_mode_hold = False
        self.is_drawing_mode_stop = False
        self.is_drawing_mode = False
        self.drawing_gesture_start_time = 0
        self.drawing_points = []  # 存储绘画轨迹点
        self.DRAWING_GESTURE_DURATION = 3.0  # 进入绘画模式需要保持的时间(秒)

    def _normalize_pinch_distance(self, distance):
        """将夹取距离归一化到0-100范围
        Args:
            distance: 原始像素距离
        Returns:
            float: 归一化后的值(0-100)
        """
        if distance <= self.pinch_min_distance:
            return 0
        elif distance >= self.pinch_max_distance:
            return 100
        
        # 线性映射到0-100
        normalized = ((distance - self.pinch_min_distance) / 
                     (self.pinch_max_distance - self.pinch_min_distance) * 100)
        return normalized

    def _analyze_hand_gesture(self, hand_landmarks, handedness):
        """分析单手的手势并返回绘画状态
        Args:
            hand_landmarks: 手的关键点
            handedness: 手的左右属性
        Returns:
            dict: 包含绘画点和绘画模式状态的字典
        """
        h, w = self.image.shape[:2]
        landmarks = hand_landmarks.landmark
        
        # 计算参考距离（拇指根部到小指根部的距离）
        d_ref = np.linalg.norm(
            np.array([landmarks[0].x * w, landmarks[0].y * h]) -  # 拇指根部
            np.array([landmarks[5].x * w, landmarks[5].y * h])    # 小指根部
        )
        
        # 动态更新夹取距离阈值
        self.pinch_max_distance = 1.5 * d_ref
        self.pinch_min_distance = 0.2 * d_ref
        
        # 计算手的中心位置
        center_x = sum(lm.x for lm in landmarks) / len(landmarks)
        center_y = sum(lm.y for lm in landmarks) / len(landmarks)
        
        # 计算伸直的手指数量
        extended_fingers = []
        for finger_id in range(5):
            if finger_id == 0:  # 拇指特殊处理
                if handedness == 'Left':
                    extended = landmarks[self.finger_tips[0]].x < landmarks[self.finger_pips[0]].x
                else:
                    extended = landmarks[self.finger_tips[0]].x > landmarks[self.finger_pips[0]].x
            else:  # 其他手指
                extended = landmarks[self.finger_tips[finger_id]].y < landmarks[self.finger_pips[finger_id]].y
            extended_fingers.append(extended)
        
        # 计算拇指和食指距离
        thumb_tip = np.array([landmarks[4].x * w, landmarks[4].y * h])
        index_tip = np.array([landmarks[8].x * w, landmarks[8].y * h])
        pinch_distance = np.linalg.norm(thumb_tip - index_tip)
        
        # 归一化夹取距离（使用动态阈值）
        normalized_distance = self._normalize_pinch_distance(pinch_distance)
        
        # 应用滤波
        filtered_distance = self.pinch_filter.update(normalized_distance)
        # 最大值最小值限制
        filtered_distance = max(min(filtered_distance, 100), 0)
        
        # 检测是否握拳（所有手指都弯曲）
        is_fist = sum(extended_fingers) == 0
        
        # 检测OK手势（拇指和食指形成圆圈，其他手指伸直）
        is_ok = (pinch_distance < self.pinch_min_distance and  # 拇指和食指接触
                not extended_fingers[1] and  # 食指弯曲
                all(extended_fingers[2:]))  # 其他手指伸直
        
        # 检测是否可以进行夹取控制
        # 条件：拇指和食指张开，其他手指弯曲
        can_pinch_control = (extended_fingers[0] and extended_fingers[1] and 
                           not any(extended_fingers[2:]))
        
        # 检查是否进入绘画模式
        self.check_drawing_gesture(extended_fingers)
        self.update_drawing_mode()
                    
        drawing_point = None
        if self.is_drawing_mode:
            # 获取食指指尖坐标
            drawing_point = landmarks[8]
            self.drawing_points.append(index_tip)
                
        
        return {
            "center": (int(center_x * w), int(center_y * h)),
            "handedness": handedness,
            "num_extended": sum(extended_fingers),
            "pinch_distance": pinch_distance,
            "normalized_pinch": normalized_distance,
            "filtered_pinch": filtered_distance,
            "thumb_tip": thumb_tip,
            "index_tip": index_tip,
            "is_fist": is_fist,
            "is_ok": is_ok,
            "can_pinch_control": can_pinch_control,
            "pinch_control_value": normalized_distance if can_pinch_control else None,
            "is_drawing_mode": self.is_drawing_mode,
            "drawing_point":drawing_point
        }

    def process(self, input_source):
        """处理输入图像"""
        try:
            # 打开图像并转换为RGB格式
            self.image, self.name = self.open(input_source, format='RGB')
            if self.image is None:
                print("Failed to open image")
                return None
            
            # 确保图像是numpy数组格式
            if not isinstance(self.image, np.ndarray):
                print("Image is not in numpy array format")
                return None
            
            # 处理图像获取手势结果
            self.results = self.hands.process(self.image)
            
            # 重置手势属性
            self.hand_landmarks = []
            self.handedness = []
            self.index_finger_depths = []
            self.hand_gestures = []
            
            # 更新追踪信息
            if self.results.multi_hand_landmarks:
                h, w = self.image.shape[:2]
                
                # 处理每只手
                for hand_idx, hand_landmarks in enumerate(self.results.multi_hand_landmarks):
                    # 保存手的关键点
                    self.hand_landmarks.append(hand_landmarks)
                    
                    # 保存手的左右属性
                    handedness = "Right" if self.results.multi_handedness[hand_idx].classification[0].label == "Left" else "Left"
                    self.handedness.append(handedness)
                    
                    # 计算食指深度
                    wrist_z = hand_landmarks.landmark[0].z
                    index_tip_z = hand_landmarks.landmark[8].z
                    self.index_finger_depths.append(wrist_z - index_tip_z)
                    
                    # 获取手的边界框
                    points = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark]
                    points = np.array(points)
                    x, y, width, height = cv2.boundingRect(points)
                    
                    # 更新追踪信息（使用第一只手的位置）
                    if hand_idx == 0:
                        self.update_tracking((x, y, width, height), self.image.shape)
                    
                    # 分析手势
                    gesture_info = self._analyze_hand_gesture(hand_landmarks, self.handedness[hand_idx])
                    self.hand_gestures.append(gesture_info)
            
            else:
                # 如果没有检测到手，更新追踪器状态为未检测到
                self.update_tracking(None, self.image.shape)
            
            # 根据配置决定是否绘制
            if self.enable_draw:
                self.image_processed = self.draw(self.image)
            else:
                # 只在不绘制时拷贝原图
                self.image_processed = self.image.copy()
            
            # RGB 2 BGR
            self.image_processed = cv2.cvtColor(self.image_processed, cv2.COLOR_RGB2BGR)

            # 根据配置决定是否保存
            if self.enable_save:
                self.save(self.image_processed)

            return self.image_processed
        except Exception as e:
            print(f"Error processing image: {e}")
            return None

    def draw(self, image, layers=None):
        """分层绘制检测结果
        Args:
            image: 输入图像
            layers: 需要绘制的层，字典格式，包含各层的开关状态
        """
        if layers is None:
            layers = {
                'hand_keypoints': True,
                'tracking_info': True,
                'drawing_trace': True,
                'pinch_info': True
            }
        
        drawing_image = image.copy()
        
        if self.results.multi_hand_landmarks:
            for hand_idx, (hand_landmarks, handedness) in enumerate(
                zip(self.results.multi_hand_landmarks, self.results.multi_handedness)):
                
                # 绘制手部关键点和连接线
                if layers.get('hand_keypoints', True):
                    drawing_image = self._draw_hand_keypoints(drawing_image, hand_landmarks)
                
                # 绘制手势信息
                if layers.get('pinch_info', True):
                    drawing_image = self._draw_gesture_info(drawing_image, hand_idx)
                
                # 绘制绘画轨迹
                if layers.get('drawing_trace', False):
                    drawing_image = self._draw_drawing_trace(drawing_image) 

                # 绘制追踪信息
                if layers.get('tracking_info', True):
                    drawing_image = self.draw_tracking_info(drawing_image)
        
        return drawing_image
    
    # 绘制手部关键点
    def _draw_hand_keypoints(self, drawing_image, hand_landmarks):
        """绘制手部关键点"""
        self.mpDraw.draw_landmarks(
            drawing_image,
            hand_landmarks,
            self.mp_hands.HAND_CONNECTIONS
        )
        
        # 绘制关键点
        for i, landmark in enumerate(hand_landmarks.landmark):
            h, w = drawing_image.shape[:2]
            cx, cy = int(landmark.x * w), int(landmark.y * h)
            depth_z = landmark.z
            
            # 根据不同关键点类型使用不同颜色和大小
            radius = int(6 * (1 + depth_z))
            if i == 0:  # 手腕
                cv2.circle(drawing_image, (cx,cy), radius*2, (0,0,255), -1)
            elif i == 8:  # 食指尖
                cv2.circle(drawing_image, (cx,cy), radius*2, (193,182,255), -1)
            elif i in [1,5,9,13,17]:  # 指根
                cv2.circle(drawing_image, (cx,cy), radius, (16,144,247), -1)
            elif i in [2,6,10,14,18]:  # 第一关节
                cv2.circle(drawing_image, (cx,cy), radius, (1,240,255), -1)
            elif i in [3,7,11,15,19]:  # 第二关节
                cv2.circle(drawing_image, (cx,cy), radius, (140,47,240), -1)
            elif i in [4,12,16,20]:  # 指尖（除食指外）
                cv2.circle(drawing_image, (cx,cy), radius, (223,155,60), -1)
        return drawing_image

    # 绘制手势信息
    def _draw_gesture_info(self, image, hand_idx):
        """绘制手势信息"""
        if hand_idx < len(self.hand_gestures):
            gesture = self.hand_gestures[hand_idx]
            y_offset = 60 + hand_idx * 150
            
            # 绘制基本信息
            cv2.putText(image, f"Hand {hand_idx}: {gesture['handedness']}", 
                       (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.7, (255, 0, 255), 2)
            # 绘制手指数量
            cv2.putText(image, f"Fingers: {gesture['num_extended']}", 
                       (10, y_offset + 30), cv2.FONT_HERSHEY_SIMPLEX, 
                       0.7, (255, 0, 255), 2)
            # 绘制OK手势
            if gesture.get('is_ok'):
                cv2.putText(image, "OK", 
                           (10, y_offset + 60), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (0, 255, 0), 2)
            # 绘制夹持控制信息
            if gesture.get('can_pinch_control'):
                thumb_pos = tuple(map(int, gesture['thumb_tip']))
                index_pos = tuple(map(int, gesture['index_tip']))
                cv2.line(image, thumb_pos, index_pos, (0, 255, 0), 2)
                
                mid_point = ((thumb_pos[0] + index_pos[0])//2, 
                           (thumb_pos[1] + index_pos[1])//2)
                cv2.circle(image, mid_point, 5, (0, 0, 255), -1)
                
                cv2.putText(image, 
                           f"{gesture['filtered_pinch']:.0f}%",
                           (mid_point[0] - 20, mid_point[1] - 10),
                           cv2.FONT_HERSHEY_SIMPLEX,
                           0.7, (255, 255, 255), 2)
        return image

    # 绘制轨迹
    def _draw_drawing_trace(self, image):
        """绘制绘画轨迹"""
        if not self.drawing_points or self.is_drawing_mode_stop:
            return image
        
        points = np.array(self.drawing_points, dtype=np.int32)
        cv2.polylines(image, [points], False, (0, 0, 255), 2)
        cv2.circle(image, tuple(points[-1]), 5, (0, 0, 255), -1)
        # 在图像左下角绘制绘画模式状态
        cv2.putText(image, "Drawing Mode: ON" if self.is_drawing_mode else "Drawing Mode: OFF", 
                    (10, image.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, (0, 255, 0), 2)
        # 绘制当前绘画点坐标
        cv2.putText(image, f"({points[-1][0]}, {points[-1][1]})", 
                    (10, image.shape[0] - 40), cv2.FONT_HERSHEY_SIMPLEX, 
                    0.7, (0, 255, 0), 2)

        return image

    def get_result_info(self):
        """获取处理结果信息"""
        # 获取追踪信息
        tracking_info = self.get_tracking_status()
        
        # 获取手势信息
        additional_info = {
            "num_hands": len(self.hand_landmarks),
            "handedness": self.handedness,
            "index_finger_depths": [float(depth) for depth in self.index_finger_depths],
            "hand_gestures": []
        }
        
        for gesture in self.hand_gestures:
            processed_gesture = {
                "center": list(gesture["center"]),
                "handedness": gesture["handedness"],
                "num_extended": int(gesture["num_extended"]),
                "pinch_distance": float(gesture["pinch_distance"]),
                "normalized_pinch": float(gesture["normalized_pinch"]),
                "is_fist": bool(gesture["is_fist"]),
                "is_ok": bool(gesture["is_ok"]),
                "can_pinch_control": bool(gesture["can_pinch_control"]),
                "pinch_control_value": float(gesture["normalized_pinch"]) if gesture["can_pinch_control"] else None,
                "is_drawing_mode": bool(gesture["is_drawing_mode"])
            }
            additional_info["hand_gestures"].append(processed_gesture)
        
        # 合并信息
        return {**tracking_info, **additional_info}

    def check_drawing_gesture(self, extended_fingers):
        """检查是否是绘画手势（食指伸直，其他手指弯曲）"""
        self.is_drawing_mode_ready = extended_fingers == [False, True, False, False, False]  # 只有食指伸直
        self.is_drawing_mode_stop = extended_fingers == [False, False, False, False, False]  # 所有手指弯曲
        self.is_drawing_mode_hold = extended_fingers == [True, True, True, True, True] or not extended_fingers# 所有手指伸开

    def update_drawing_mode(self):
        """更新绘画模式状态"""
        current_time = time.time()
        
        if self.is_drawing_mode_ready:  
            if not self.is_drawing_mode:
                if self.drawing_gesture_start_time == 0:
                    self.drawing_gesture_start_time = current_time
                elif current_time - self.drawing_gesture_start_time >= self.DRAWING_GESTURE_DURATION:
                    self.is_drawing_mode = True
                    print("Entered drawing mode")

        if self.is_drawing_mode_hold:
            if self.is_drawing_mode:
                self.drawing_gesture_start_time = current_time
                self.is_drawing_mode = False
                print("Exited drawing mode but still holding")

        if self.is_drawing_mode_stop:
            if self.is_drawing_mode:
                self.save_drawing()
                self.is_drawing_mode = False
                print("Exited drawing mode")
            self.drawing_gesture_start_time = 0

    def save_drawing(self):
        """保存绘画轨迹和图像"""
        if not self.drawing_points:
            return

        # 创建保存目录
        save_dir = os.path.join("output", "drawings")
        os.makedirs(save_dir, exist_ok=True)

        # 生成文件名
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        image_filename = f"drawing_image_{timestamp}.jpg"
        json_filename = f"drawing_data_{timestamp}.json"
        
        # 创建白色背景图像
        height, width = 480, 640  # 可以根据实际需要调整
        canvas = np.ones((height, width, 3), dtype=np.uint8) * 255

        # 绘制轨迹
        points = np.array(self.drawing_points, dtype=np.int32)
        if len(points) > 1:
            cv2.polylines(canvas, [points], False, (0, 0, 255), 2)

        # 保存图像
        image_filepath = os.path.join(save_dir, image_filename)
        cv2.imwrite(image_filepath, canvas)
        print(f"Drawing image saved to: {image_filepath}")

        # 保存绘图轨迹数据
        drawing_data = {
            "timestamp": timestamp,
            "points": [{"x": int(pt[0]), "y": int(pt[1])} for pt in self.drawing_points]
        }
        
        json_filepath = os.path.join(save_dir, json_filename)
        with open(json_filepath, 'w') as json_file:
            json.dump(drawing_data, json_file, indent=4)
        print(f"Drawing data saved to: {json_filepath}")

        # 清空轨迹点
        self.drawing_points.clear()
