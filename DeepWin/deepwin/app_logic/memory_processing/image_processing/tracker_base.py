import numpy as np
import cv2
from collections import deque, defaultdict
from filterpy.kalman import KalmanFilter
from .config_manager import ConfigManager
import time

class ImageTracker:
    """图像追踪基类"""
    def __init__(self):
        self.config = ConfigManager()
        
        # 配置参数
        tracking_config = self.config.get('tracking', {})
        self.history_length = tracking_config.get('history_length', 30)
        self.enable_kalman = tracking_config.get('enable_kalman', True)
        self.enable_mean_filter = tracking_config.get('enable_mean_filter', True)
        
        # 目标信息
        self.target_found = False
        self.target_center = None      # 当前目标中心点 (x, y)
        self.target_size = None        # 当前目标大小 (w, h)
        self.bbox = None               # 当前边界框 (x, y, w, h)
        
        # 误差信息
        self.pixel_error = None        # 像素误差 (error_x, error_y)
        self.norm_error = None         # 归一化误差 (-1~1)
        
        # 历史轨迹
        self.center_history = deque(maxlen=self.history_length)
        self.mean_filtered_history = deque(maxlen=self.history_length)
        self.kalman_filtered_history = deque(maxlen=self.history_length)
        
        # 卡尔曼滤波器初始化
        self.kf = self._init_kalman()
        self.kf_initialized = False
        
        # 添加滤波后的误差属性
        self.filtered_pixel_error = None
        self.filtered_norm_error = None
        
        # 添加多点追踪相关属性
        self.multi_track_history = defaultdict(lambda: deque(maxlen=self.history_length))
        self.multi_track_colors = {}  # 为每个track_id存储固定的颜色
        self.multi_track_status = {}  # 存储每个track的状态信息
        
        # 颜色配置
        self.color_palette = np.random.randint(0, 255, size=(100, 3))  # 预生成100种颜色
        self.alpha_range = np.linspace(0.2, 1.0, self.history_length)  # 透明度渐变
        
        # 添加轨迹清理相关配置
        self.track_timeout = 1.0  # 轨迹超时时间（秒）
        self.cleanup_interval = 5.0  # 清理间隔（秒）
        self.last_cleanup_time = time.time()

    def _init_kalman(self):
        """初始化卡尔曼滤波器"""
        kf = KalmanFilter(dim_x=4, dim_z=2)  # 状态: [x, y, dx, dy], 观测: [x, y]
        
        # 状态转移矩阵
        kf.F = np.array([
            [1, 0, 1, 0],
            [0, 1, 0, 1],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        # 测量矩阵
        kf.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ])
        
        # 测量噪声
        kf.R *= 10
        
        # 过程噪声
        kf.Q = np.eye(4) * 0.1
        
        return kf

    def update(self, bbox, image_shape):
        """更新追踪信息
        Args:
            bbox: 目标框 (x, y, w, h)
            image_shape: 图像形状 (h, w)
        """
        h, w = image_shape[:2]
        image_center = np.array([w/2, h/2])
        
        if bbox is None:
            self.target_found = False
            # 重置所有误差
            self.pixel_error = np.array([0.0, 0.0])
            self.norm_error = np.array([0.0, 0.0])
            self.filtered_pixel_error = np.array([0.0, 0.0])
            self.filtered_norm_error = np.array([0.0, 0.0])
            return
            
        # 更新目标信息
        self.target_found = True
        self.bbox = np.array(bbox)
        x, y, width, height = bbox
        self.target_center = np.array([x + width/2, y + height/2])
        self.target_size = np.array([width, height])
        
        # 计算原始误差
        self.pixel_error = image_center - self.target_center
        self.norm_error = np.array([
            self.pixel_error[0] / (w / 2),
            self.pixel_error[1] / (h / 2)  # y轴向上为正
        ])
        
        # 更新历史轨迹
        self.center_history.append(self.target_center.copy())
        
        # 平均值滤波
        if self.enable_mean_filter:
            if len(self.center_history) >= 3:
                mean_pos = np.mean(list(self.center_history)[-3:],axis=0)  # 取最后3个点的平均值
            else:
                mean_pos = np.mean(self.center_history, axis=0)
            self.mean_filtered_history.append(mean_pos)
            # 计算均值滤波后的误差
            mean_pixel_error = image_center - mean_pos
            mean_norm_error = np.array([
                mean_pixel_error[0] / (w / 2),
                mean_pixel_error[1] / (h / 2)
            ])
        
        # 卡尔曼滤波
        if self.enable_kalman:
            if not self.kf_initialized:
                self.kf.x = np.array([self.target_center[0], self.target_center[1], 0, 0])
                self.kf_initialized = True
            
            # 预测和更新
            self.kf.predict()
            self.kf.update(self.target_center)
            
            # 保存滤波后的位置
            filtered_pos = self.kf.x[:2]
            self.kalman_filtered_history.append(filtered_pos)
            
            # 计算卡尔曼滤波后的误差
            filtered_pixel_error = image_center - filtered_pos
            filtered_norm_error = np.array([
                filtered_pixel_error[0] / (w / 2),
                filtered_pixel_error[1] / (h / 2)
            ])
            
            # 更新滤波后的误差属性
            self.filtered_pixel_error = filtered_pixel_error
            self.filtered_norm_error = filtered_norm_error
        else:
            # 如果没有启用卡尔曼滤波，使用均值滤波结果或原始误差
            if self.enable_mean_filter:
                self.filtered_pixel_error = mean_pixel_error
                self.filtered_norm_error = mean_norm_error
            else:
                self.filtered_pixel_error = self.pixel_error
                self.filtered_norm_error = self.norm_error

    def update_multi_tracks(self, boxes, track_ids):
        """更新多个目标的追踪信息"""
        if boxes is None or len(boxes) == 0:
            self.multi_track_history.clear()
            self.multi_track_colors.clear()
            self.multi_track_status.clear()
            return

        # 使用集合操作来高效处理过期轨迹
        current_track_ids = set(track_ids)
        expired_tracks = set(self.multi_track_history.keys()) - current_track_ids
        
        # 批量删除过期轨迹
        for track_id in expired_tracks:
            del self.multi_track_history[track_id]
            self.multi_track_colors.pop(track_id, None)
            self.multi_track_status.pop(track_id, None)

        # 使用numpy进行批量更新
        boxes = np.asarray(boxes)
        centers = boxes[:, :2]  # 直接使用中心点坐标

        # 批量更新轨迹
        for track_id, (center, box) in zip(track_ids, zip(centers, boxes)):
            self.multi_track_history[track_id].append((float(center[0]), float(center[1])))

            if len(self.multi_track_history[track_id]) > self.history_length:
                self.multi_track_history[track_id].pop()    
            
            # 只为新轨迹分配颜色
            if track_id not in self.multi_track_colors:
                self.multi_track_colors[track_id] = self.color_palette[
                    len(self.multi_track_colors) % len(self.color_palette)
                ]
                        
            # 更新track状态
            self.multi_track_status[track_id] = {
                'bbox': list(map(int, box)),  # [x, y, w, h]
                'center': list(map(int, center)),
                'size': list(map(int, box[2:]))  # [w, h]
            }

    def draw_multi_tracks(self, image):
        """绘制多目标追踪轨迹"""
        # 直接在原图上绘制，避免不必要的拷贝
        for track_id, track in self.multi_track_history.items():
            if len(track) < 2:
                continue
            
            try:
                # 转换轨迹点为numpy数组并确保是整数类型
                points = np.array(track, dtype=np.int32).reshape((-1, 1, 2))
                
                # 确保颜色是整数元组
                base_color = self.multi_track_colors.get(track_id, (230, 230, 230))
                color = tuple(map(int, base_color))  # 确保颜色值是整数
                
                # 使用polylines绘制轨迹
                cv2.polylines(image, 
                             [points],  # 需要是点列表的列表
                             isClosed=False, 
                             color=color, 
                             thickness=2)
                
                # 绘制当前位置点（轨迹的最后一个点）
                if len(track) > 0:
                    current_point = tuple(map(int, track[-1]))
                    cv2.circle(image, current_point, 4, color, -1)
                
            except Exception as e:
                print(f"Error drawing track {track_id}: {e}")
                continue
        
        return image

    def _cleanup_tracks(self, current_time):
        """清理过期的轨迹"""
        expired_tracks = []
        for track_id in self.multi_track_history:
            status = self.multi_track_status.get(track_id)
            if not status or (current_time - status['last_update']) > self.track_timeout:
                expired_tracks.append(track_id)
        
        # 删除过期的轨迹
        for track_id in expired_tracks:
            del self.multi_track_history[track_id]
            if track_id in self.multi_track_colors:
                del self.multi_track_colors[track_id]
            if track_id in self.multi_track_status:
                del self.multi_track_status[track_id]

    def get_multi_track_status(self):
        """获取多目标追踪状态"""
        return {
            'tracks': {
                track_id: {
                    'bbox': status['bbox'],  # 现在status中包含了bbox
                    'center': status['center'],
                    'size': status['size']
                    # 'history': list(self.multi_track_history[track_id])
                }
                for track_id, status in self.multi_track_status.items()
            },
            'active_tracks': len(self.multi_track_status)
        }

    def draw(self, image, color=(0, 255, 0)):
        """绘制追踪信息"""
        if not self.target_found or self.bbox is None:
            return image
        
        try:
            # 确保边界框坐标是有效的整数
            x, y, bw, bh = [int(v) for v in self.bbox]
            
            # 确保坐标在图像范围内
            h, w = image.shape[:2]
            x = max(0, min(x, w-1))
            y = max(0, min(y, h-1))
            bw = max(0, min(bw, w-x))
            bh = max(0, min(bh, h-y))
            
            # 绘制当前边界框
            cv2.rectangle(image, (x, y), (x + bw, y + bh), color, 2)
            
            # 绘制图像中心和目标中心
            image_center = (w//2, h//2)
            if self.target_center is not None:
                target_center = tuple(map(int, self.target_center))
                
                # 绘制中心点和连线
                cv2.circle(image, image_center, 5, (255, 0, 0), -1)
                cv2.circle(image, target_center, 5, (0, 0, 255), -1)
                cv2.line(image, image_center, target_center, (255, 0, 0), 2)
            
            # 绘制历史轨迹
            if len(self.center_history) > 0:
                self._draw_trajectory(image, self.center_history, (0, 255, 255))
            if self.enable_mean_filter and len(self.mean_filtered_history) > 0:
                self._draw_trajectory(image, self.mean_filtered_history, (255, 0, 255))
            if self.enable_kalman and len(self.kalman_filtered_history) > 0:
                self._draw_trajectory(image, self.kalman_filtered_history, (255, 255, 0))
            
            # 显示误差信息
            # if self.pixel_error is not None:
            #     cv2.putText(image, 
            #                f"Pixel Err: ({self.pixel_error[0]:.1f}, {self.pixel_error[1]:.1f})",
            #                (x, y + bh + 20), 
            #                cv2.FONT_HERSHEY_SIMPLEX, 
            #                0.5, 
            #                color, 
            #                1)
            
            # if self.norm_error is not None:
            #     cv2.putText(image, 
            #                f"Norm Err: ({self.norm_error[0]:.2f}, {self.norm_error[1]:.2f})",
            #                (x, y + bh + 40), 
            #                cv2.FONT_HERSHEY_SIMPLEX, 
            #                0.5, 
            #                color, 
            #                1)
            
            # 添加滤波后误差的显示
            if self.filtered_norm_error is not None:
                cv2.putText(image, 
                           f"Filtered Err: ({self.filtered_norm_error[0]:.2f}, {self.filtered_norm_error[1]:.2f})",
                           (x, y + bh + 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 
                           0.5, 
                           color, 
                           1)
            
        except Exception as e:
            print(f"Error drawing tracking info: {e}")
            import traceback
            traceback.print_exc()
        
        return image

    def _draw_trajectory(self, image, trajectory, color):
        """绘制轨迹
        Args:
            image: 图像
            trajectory: 轨迹点列表
            color: 基础颜色 (B,G,R)
        """
        if len(trajectory) < 2:
            return
            
        points = np.array([point for point in trajectory]).astype(np.int32)
        
        # 计算每个点的透明度
        alphas = np.linspace(0.2, 1.0, len(points))
        
        # 绘制轨迹线
        for i in range(len(points) - 1):
            alpha = alphas[i]
            pt1 = tuple(points[i])
            pt2 = tuple(points[i + 1])
            
            # 混合颜色
            blend_color = tuple(int(c * alpha) for c in color)
            cv2.line(image, pt1, pt2, blend_color, 2)

    def reset(self):
        """重置追踪器状态"""
        self.target_found = False
        self.target_center = None
        self.target_size = None
        self.bbox = None
        self.pixel_error = None
        self.norm_error = None
        self.center_history.clear()
        self.mean_filtered_history.clear()
        self.kalman_filtered_history.clear()
        self.kf_initialized = False

    def get_status(self):
        """获取追踪器状态"""
        return {
            'target_found': self.target_found,
            'target_center': self.target_center.tolist() if self.target_center is not None else None,
            'target_size': self.target_size.tolist() if self.target_size is not None else None,
            'pixel_error': self.pixel_error.tolist() if self.pixel_error is not None else None,
            'norm_error': self.norm_error.tolist() if self.norm_error is not None else None,
            'filtered_pixel_error': self.filtered_pixel_error.tolist() if self.filtered_pixel_error is not None else None,
            'filtered_norm_error': self.filtered_norm_error.tolist() if self.filtered_norm_error is not None else None
        } 