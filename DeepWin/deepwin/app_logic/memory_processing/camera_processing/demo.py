import cv2
import argparse
import numpy as np
from .manager import CameraManager
from .input_handler import CameraInputHandler
from input_handling.manager import InputManager
from image_processing.manager import ImageManager
from uart_processing.manager import UartManager
from uart_processing.config_manager import ConfigManager
import time
from uart_processing.input_handler import ScaraInputHandler


class CameraDemo:
    def __init__(self):
        self.image_manager = ImageManager()
        self.camera_manager = CameraManager(frame_manager=self.image_manager)
        
        # 添加UART管理器用于控制云台
        self.input_handler = ScaraInputHandler()


    def test_camera_control(self):
        """测试摄像头控制"""
        print("\nTesting Camera Control...")
        try:
            
            # 获取串口相关处理器
            camera_processor = self.input_handler.camera_processor
            scara_processor = self.input_handler.scara_processor
            
            # 创建输入处理器
            input_handler = CameraInputHandler(self.camera_manager)
            input_manager = InputManager()
            
            # 注册处理器
            input_manager.register_handler('camera', input_handler)
            input_manager.set_active_handler('camera')
            
            print("\nCamera Control Instructions:")
            print("\nImage Processing:")
            print("  f: Enable face recognition")
            print("  d: Enable face detection")
            print("  m: Enable face mesh")
            print("  h: Enable hand gesture")
            print("  p: Enable pose detection")
            print("  o: Enable OCR")
            print("  c: Enable QR code detection")
            print("  y: Enable YOLO detection")
            print("  a: Enable all processors")
            print("  n: Disable all processors")
            print("\nDisplay Control:")
            print("  j: Zoom in")
            print("  k: Zoom out")
            print("\nRecording Control:")
            print("  s: Save current frame")
            print("  r: Toggle recording")
            print("  q: Quit")
            
            # 启动输入管理器
            input_manager.start()
            
            # 主循环
            while True:
                frame = self.camera_manager.read_frame()
                if frame is None:
                    print("Failed to read frame")
                    continue
                    
                try:
                    # 处理帧
                    processed_frame = self.camera_manager.process_frame(frame, is_display=True)
                    
                    # 获取当前启用的处理器名称和结果
                    active_processor = self.image_manager.get_active_processor()
                    if not active_processor:
                        continue

                
                    processor_results = self.image_manager.get_processor_result(active_processor)
                
                    if processor_results:
                        # Camera 控制
                        # 获取滤波后的误差值
                        filtered_error = processor_results.get('filtered_norm_error', [0, 0])
                        target_found = processor_results.get('target_found', False)
                        # 发送误差控制指令
                        camera_processor.set_error(
                            filtered_error[0],
                            filtered_error[1],
                            target_found=target_found
                        )
                        # scara 控制
                        can_pinch_control = processor_results.get('can_pinch_control', False)
                        filtered_pinch = processor_results.get('filtered_pinch', 0)
                        if can_pinch_control:
                            # 打印filtered_pinch的值
                            print(f'filtered_pinch is: {filtered_pinch}')
                            scara_processor.set_pinch_control(filtered_pinch)
                        
                    else:
                        # 如果没有处理结果，发送零误差
                        camera_processor.set_error(0, 0, target_found=False)
                        time.sleep(0.1)
                
                except Exception as e:
                    print(f"Frame processing error: {e}")
                    # 显示原始帧
                    cv2.imshow('Camera Stream', frame)
                
                if cv2.waitKey(1) == ord('q'):
                    break
            
            # 清理资源
            input_manager.stop()
            cv2.destroyAllWindows()
            self.uart_manager.disconnect()
            return True
            
        except Exception as e:
            print(f"Camera control test failed: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Camera Processing Demo')
    parser.add_argument('--test', choices=['camera'], default='camera', help='Test to run')
    
    args = parser.parse_args()
    demo = CameraDemo()
    
    if args.test == 'camera':
        demo.test_camera_control()

if __name__ == "__main__":
    main() 