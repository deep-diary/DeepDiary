import cv2
import os
import time

class CameraProcessorBase:
    def __init__(self):
        self.camera_index = 0
        self.cap = None
        self.current_frame = None
        self.current_frame_processed = None
        self.frame_width = 0
        self.frame_height = 0
        self.bytes_per_line = 0
        self.started = False
        self.is_recording = False
        self.frame_processors = []
        self.video_writer = None
        self.outframe_path = "output/processed_cameras/image"
        self.outvideo_path = "output/processed_cameras/video"
        os.makedirs(os.path.dirname(self.outframe_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.outvideo_path), exist_ok=True)
        

    def initialize_camera(self):
        if self.started:
            return
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            raise ValueError(f"无法打开摄像头 {self.camera_index}")
        self.frame_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.bytes_per_line = 3 * self.frame_width
        self.started = True

    def release_camera(self):
        if not self.started:
            return
        if self.cap:
            self.cap.release()
        self.started = False
        self.stop_recording()
        cv2.destroyAllWindows()

    def read_frame(self):
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = frame
                self.current_frame_processed = frame
                return frame
        return None
    
    def get_output_frame(self, is_save_processed=False):
        if is_save_processed:
            return self.current_frame_processed
        else:
            return self.current_frame

    def save_frame(self, is_save_processed=False):
        frame = self.get_output_frame(is_save_processed)

        if frame is not None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            image_path = f"{self.outframe_path}/frame_{timestamp}.png"
            os.makedirs(os.path.dirname(image_path), exist_ok=True)
            cv2.imwrite(image_path, frame)  # cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            print(f"保存帧到 {image_path}")

    def start_recording(self):
        self.is_recording = True
        print("开始录制")
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        video_path = os.path.join(self.outvideo_path, f"recorded_{timestamp}.avi")
        os.makedirs(os.path.dirname(video_path), exist_ok=True)  # 确保目录存在
        print(f"Initializing video writer with size: {self.frame_width}x{self.frame_height}")
        self.video_writer = cv2.VideoWriter(video_path, fourcc, 20.0, (self.frame_width, self.frame_height))

    def stop_recording(self):
        self.is_recording = False
        print("停止录制")
        self.video_writer = None
        if self.video_writer is not None:
            self.video_writer.release()

    def save_video(self):
        if self.video_writer is None or not self.is_recording:
            return
        print("Writing frame to video")
        self.video_writer.write(cv2.cvtColor(self.current_frame_processed, cv2.COLOR_RGB2BGR))

    
    def toggle_recording(self):
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()


