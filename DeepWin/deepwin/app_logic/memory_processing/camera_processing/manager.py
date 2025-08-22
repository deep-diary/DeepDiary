from .processor_frame import ProcessorFrame
from .config_manager import CameraConfigManager
from .base import CameraProcessorBase
import cv2
import time

class CameraManager(CameraProcessorBase):
    _available_cameras = None  # 类级别的缓存

    def __init__(self, camera_index=0, frame_manager=None, frame_processors=None):
        print('Starting CameraManager initialization...')
        t_start = time.time()
        
        super().__init__()
        self.config_manager = CameraConfigManager()
        self.image_manager = frame_manager
        
        # 使用缓存的摄像头列表
        # if CameraManager._available_cameras is None:
        #     print('Checking available cameras...')
        #     CameraManager._available_cameras = self._check_cameras()
        # self.available_cameras = CameraManager._available_cameras
        self.available_cameras = [0,1]

        print(f"Available cameras: {self.available_cameras}")
        
        if camera_index not in self.available_cameras:
            raise ValueError(f"Camera index {camera_index} is not available")
        
        self.camera_index = camera_index
        print('Initializing camera...')
        self.initialize_camera()
        
        # 延迟初始化帧处理器
        self.frame_processor = ProcessorFrame(None, None)  # 先不传入处理器
        print(f'Total initialization time: {time.time() - t_start:.2f}s')

    def _check_cameras(self, timeout=0.1):
        """快速检查可用摄像头
        Args:
            timeout: 每个摄像头的检查超时时间
        """
        available = []
        max_cameras = self.config_manager.get('camera', 'max_cameras', 2)
        
        for i in range(max_cameras):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # 设置较短的超时时间
                    start_time = time.time()
                    while time.time() - start_time < timeout:
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            available.append(i)
                            break
                cap.release()
            except:
                continue
        
        return available

    def set_frame_processors(self, processors):
        """设置帧处理器列表"""
        if processors:
            # 延迟初始化图像处理管理器
            if self.frame_processor.image_processing_manager is None:
                self.frame_processor.image_processing_manager = self.image_manager
        self.frame_processor.set_frame_processors(processors)

    def adjust_display_scale(self, increase=True):
        """调整显示比例"""
        self.frame_processor.adjust_scale(increase)

    def get_available_cameras(self):
        """获取可用摄像头列表"""
        available_cameras = []
        max_cameras = self.config_manager.get('camera', 'max_cameras', 2)
        
        # 使用更快的检测方法
        for i in range(max_cameras):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    available_cameras.append(i)
                    cap.release()
                else:
                    break  # 如果打开失败，后面的索引也很可能失败
            except:
                break
        
        return available_cameras
    
    def display_camera_stream(self):
        """显示摄像头流"""
        while True:
            frame = self.read_frame()
            if frame is None:
                print("Failed to read frame. Exiting loop.")
                break
            
            # 处理并显示帧
            processed_frame = self.frame_processor.process(frame, is_display=True)
            self.current_frame_processed = processed_frame
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                print("Exiting loop on 'q' key press.")
                break
            elif key == ord('s'):
                self.save_frame()
        
        self.release_camera()
        cv2.destroyAllWindows()   

    def set_image_manager(self, image_manager):
        """设置图像处理管理器"""
        self.image_manager = image_manager
        self.frame_processor.image_processing_manager = image_manager

    def process_frame(self, frame, is_display=False):
        """处理帧"""
        self.current_frame_processed = self.frame_processor.process(frame, is_display)
        self.save_video()
        return self.current_frame_processed
        


