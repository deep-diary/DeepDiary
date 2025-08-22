from input_handling.base import InputHandler
from pynput import keyboard
import cv2

class CameraInputHandler(InputHandler):
    def __init__(self, camera_manager):
        self.camera_manager = camera_manager

    def handle_key_press(self, key):
        """处理键盘按下事件"""
        try:
            if isinstance(key, keyboard.KeyCode):
                # 图像处理器控制
                if key.char == 'f':  # 改用f键代替r键
                    self.camera_manager.set_frame_processors(['face_recognition'])
                    print("Enabled face recognition")
                elif key.char == 'd':
                    self.camera_manager.set_frame_processors(['face_detection'])
                    print("Enabled face detection")
                elif key.char == 'm':
                    self.camera_manager.set_frame_processors(['face_mesh'])
                    print("Enabled face mesh")
                elif key.char == 'h':
                    self.camera_manager.set_frame_processors(['hand_gesture'])
                    print("Enabled hand gesture")
                elif key.char == 'p':
                    self.camera_manager.set_frame_processors(['pose'])
                    print("Enabled pose detection")
                elif key.char == 'o':
                    self.camera_manager.set_frame_processors(['easy_ocr'])
                    print("Enabled OCR")
                elif key.char == 'c':
                    self.camera_manager.set_frame_processors(['qr_code'])
                    print("Enabled QR code detection")
                elif key.char == 'y':
                    self.camera_manager.set_frame_processors(['yolo'])
                    print("Enabled YOLO detection")
                elif key.char == 'a':
                    self.camera_manager.set_frame_processors([
                        'face_recognition', 'face_detection', 'face_mesh',
                        'hand_gesture', 'pose', 'easy_ocr', 'qr_code', 'yolo'
                    ])
                    print("Enabled all processors")
                elif key.char == 'n':
                    self.camera_manager.set_frame_processors(None)
                    print("Disabled all processors")
                
                # 显示控制
                elif key.char == 'j':
                    self.camera_manager.adjust_display_scale(increase=True)
                elif key.char == 'k':
                    self.camera_manager.adjust_display_scale(increase=False)
                
                # 录制和保存控制
                elif key.char == 's':
                    print("Saving current frame")
                    self.camera_manager.save_frame()
                elif key.char == 'r':
                    print("Toggling recording")
                    self.camera_manager.toggle_recording()
                elif key.char == 'q':
                    print("Releasing camera")
                    self.camera_manager.release_camera()
                    cv2.destroyAllWindows()
                    return True
        except Exception as e:
            print(f"Error handling key press: {e}")

    def handle_key_release(self, key):
        """处理键盘释放事件"""
        pass

    def handle_mouse_event(self, x, y, button, pressed):
        print(f"Mouse event: {x}, {y}, {button}, {pressed}")
        pass

    def handle_key_holding(self, key):
        """处理键盘持续按下事件"""
        pass