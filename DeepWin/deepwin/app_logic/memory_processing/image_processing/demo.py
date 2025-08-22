import cv2
import argparse
import os
from .manager import ImageManager

class ImageDemo:
    """图像处理演示类"""
    def __init__(self):
        self.manager = ImageManager()
        # 获取demo文件夹的路径（在image_processing包内）
        self.demo_folder = os.path.join(os.path.dirname(__file__), 'demo')

    def test_face_detection(self, image_path=None):
        """测试人脸检测"""
        print("\nTesting Face Detection...")
        try:
            # 如果没有指定图像，使用默认的demo图像
            if image_path is None:
                image_path = os.path.join(self.demo_folder, 'face_detection.jpg')
                
            if not os.path.exists(image_path):
                print(f"Error: Test image not found: {image_path}")
                return False

            result = self.manager.process_image(image_path, 'face_detection')
            if result is not None:
                cv2.imshow("Face Detection Result", result)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                return True
            return False
        except Exception as e:
            print(f"Face detection test failed: {e}")
            return False

    def test_face_mesh(self, image_path=None):
        """测试人脸网格"""
        print("\nTesting Face Mesh...")
        try:
            if image_path is None:
                image_path = os.path.join(self.demo_folder, 'mesh_left_eye_close.jpg')

            if not os.path.exists(image_path):
                print(f"Error: Test image not found: {image_path}")
                return False

            result = self.manager.process_image(image_path, 'face_mesh')
            if result is not None:
                cv2.imshow("Face Mesh Result", result)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                return True
            return False
        except Exception as e:
            print(f"Face mesh test failed: {e}")
            return False

    def test_pose(self, image_path=None):
        """测试姿态检测"""
        print("\nTesting Pose Detection...")
        try:
            if image_path is None:
                image_path = os.path.join(self.demo_folder, 'pose1.jpg')

            if not os.path.exists(image_path):
                print(f"Error: Test image not found: {image_path}")
                return False

            result = self.manager.process_image(image_path, 'pose')
            if result is not None:
                cv2.imshow("Pose Detection Result", result)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                return True
            return False
        except Exception as e:
            print(f"Pose detection test failed: {e}")
            return False

    def test_ocr(self, image_path=None):
        """测试OCR文字识别"""
        print("\nTesting OCR...")
        try:
            if image_path is None:
                image_path = os.path.join(self.demo_folder, 'ocr.png')

            if not os.path.exists(image_path):
                print(f"Error: Test image not found: {image_path}")
                return False

            result = self.manager.process_image(image_path, 'ocr')
            if result is not None:
                cv2.imshow("OCR Result", result)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                return True
            return False
        except Exception as e:
            print(f"OCR test failed: {e}")
            return False

    def test_easy_ocr(self, image_path=None):
        """测试EasyOCR文字识别"""
        print("\nTesting EasyOCR...")
        try:
            if image_path is None:
                image_path = os.path.join(self.demo_folder, 'easy_ocr.png')

            if not os.path.exists(image_path):
                print(f"Error: Test image not found: {image_path}")
                return False

            result = self.manager.process_image(image_path, 'easy_ocr')
            if result is not None:
                cv2.imshow("EasyOCR Result", result)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                return True
            return False
        except Exception as e:
            print(f"EasyOCR test failed: {e}")
            return False

    def test_face_recognition(self, image_path=None):
        """测试人脸识别"""
        print("\nTesting Face Recognition...")
        try:
            if image_path is None:
                image_path = os.path.join(self.demo_folder, 'face_recognition.jpg')

            if not os.path.exists(image_path):
                print(f"Error: Test image not found: {image_path}")
                return False

            result = self.manager.process_image(image_path, 'face_recognition')
            if result is not None:
                cv2.imshow("Face Recognition Result", result)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                return True
            return False
        except Exception as e:
            print(f"Face recognition test failed: {e}")
            return False

    def test_hand_gesture(self, image_path=None):
        """测试手势识别"""
        print("\nTesting Hand Gesture Recognition...")
        try:
            if image_path is None:
                image_path = os.path.join(self.demo_folder, 'hand_gesture_right.jpg')

            if not os.path.exists(image_path):
                print(f"Error: Test image not found: {image_path}")
                return False

            result = self.manager.process_image(image_path, 'hand_gesture')
            if result is not None:
                cv2.imshow("Hand Gesture Result", result)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                return True
            return False
        except Exception as e:
            print(f"Hand gesture test failed: {e}")
            return False

    def test_qr_code(self, image_path=None):
        """测试二维码处理"""
        print("\nTesting QR Code Processing...")
        try:
            if image_path is None:
                # 首先生成一个测试用的二维码
                qr_processor = self.manager.get_processor('qr_code')
                test_data = "https://github.com/your_repository"
                qr_image = qr_processor.generate_qr_code(test_data)
                
                # 保存生成的二维码作为测试图像
                test_image_path = os.path.join(self.demo_folder, 'qr_test.jpg')
                cv2.imwrite(test_image_path, qr_image)
                image_path = test_image_path

            if not os.path.exists(image_path):
                print(f"Error: Test image not found: {image_path}")
                return False

            # 处理二维码图像
            result = self.manager.process_image(image_path, 'qr_code')
            if result is not None:
                cv2.imshow("QR Code Result", result)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                return True
            return False
        except Exception as e:
            print(f"QR code test failed: {e}")
            return False

    def test_yolo_detection(self, image_path=None):
        """测试YOLO目标检测"""
        print("\nTesting YOLO Detection...")
        try:
            if image_path is None:
                image_path = os.path.join(self.demo_folder, 'yolo11_train.jpg')

            if not os.path.exists(image_path):
                print(f"Error: Test image not found: {image_path}")
                return False
            # 使用自定义模型
            self.manager.get_processor('yolo').set_model('tesla_cap.pt')
            result = self.manager.process_image(image_path, 'yolo')
            if result is not None:
                cv2.imshow("YOLO Detection Result", result)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                return True
            return False
        except Exception as e:
            print(f"YOLO detection test failed: {e}")
            return False

    def test_yolo_tracking(self, video_path=None):
        """测试YOLO目标追踪"""
        print("\nTesting YOLO Tracking...")
        try:
            if video_path is None:
                video_path = os.path.join(self.demo_folder, 'street.mp4')

            if not os.path.exists(video_path):
                print(f"Error: Test video not found: {video_path}")
                return False

            # 设置追踪模式
            processor = self.manager.get_processor('yolo')
            processor.track = True
            
            # 打开视频
            cap = cv2.VideoCapture(video_path)
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                    
                result = processor.process(frame)
                if result is not None:
                    cv2.imshow("YOLO Tracking Result", result)
                    
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                    
            cap.release()
            cv2.destroyAllWindows()
            
            # 恢复检测模式
            processor.track = False
            return True
        except Exception as e:
            print(f"YOLO tracking test failed: {e}")
            return False

    def test_all(self, image_path=None):
        """运行所有测试"""
        tests = [
            (lambda: self.test_face_detection(image_path), "Face Detection Test"),
            (lambda: self.test_face_recognition(image_path), "Face Recognition Test"),
            (lambda: self.test_face_mesh(image_path), "Face Mesh Test"),
            (lambda: self.test_pose(image_path), "Pose Detection Test"),
            (lambda: self.test_hand_gesture(image_path), "Hand Gesture Test"),
            (lambda: self.test_ocr(image_path), "OCR Test"),
            (lambda: self.test_easy_ocr(image_path), "EasyOCR Test"),
            (lambda: self.test_qr_code(image_path), "QR Code Test"),
            (lambda: self.test_yolo_detection(image_path), "YOLO Detection Test"),
            (lambda: self.test_yolo_tracking(image_path), "YOLO Tracking Test")
        ]
        
        results = []
        for test_func, test_name in tests:
            try:
                result = test_func()
                results.append((test_name, result))
            except Exception as e:
                print(f"Test {test_name} failed with error: {e}")
                results.append((test_name, False))

        print("\nTest Results:")
        for name, result in results:
            print(f"{name}: {'Success' if result else 'Failed'}")

        return all(result for _, result in results)

def main():
    parser = argparse.ArgumentParser(description='Image Processing Demo')
    parser.add_argument('--test', 
                       choices=['face_detection', 'face_recognition', 'mesh', 'pose', 
                               'hand_gesture', 'ocr', 'easy_ocr', 'qr_code', 'yolo_detection', 'yolo_tracking', 'all'],
                       default='face_detection', 
                       help='Test to run')
    parser.add_argument('--image', type=str, help='Optional custom input image path')
    
    args = parser.parse_args()
    demo = ImageDemo()
    
    test_funcs = {
        'face_detection': demo.test_face_detection,
        'face_recognition': demo.test_face_recognition,
        'mesh': demo.test_face_mesh,
        'pose': demo.test_pose,
        'hand_gesture': demo.test_hand_gesture,
        'ocr': demo.test_ocr,
        'easy_ocr': demo.test_easy_ocr,
        'qr_code': demo.test_qr_code,
        'yolo_detection': demo.test_yolo_detection,
        'yolo_tracking': demo.test_yolo_tracking,
        'all': demo.test_all
    }
    
    test_func = test_funcs.get(args.test)
    if test_func:
        test_func(args.image)
    else:
        print(f"Unknown test: {args.test}")
        print("\nAvailable tests:")
        print("  face_detection  - Test face detection")
        print("  face_recognition- Test face recognition")
        print("  mesh           - Test face mesh")
        print("  pose           - Test pose detection")
        print("  hand_gesture   - Test hand gesture recognition")
        print("  ocr            - Test OCR")
        print("  easy_ocr       - Test EasyOCR")
        print("  qr_code        - Test QR Code")
        print("  yolo_detection - Test YOLO Detection")
        print("  yolo_tracking - Test YOLO Tracking")
        print("  all            - Run all tests")

if __name__ == "__main__":
    main()