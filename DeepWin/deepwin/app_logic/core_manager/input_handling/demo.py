import time
from .manager import InputManager
from camera_processing.input_handler import CameraInputHandler
from image_processing.input_handler import ImageInputHandler

class InputDemo:
    def __init__(self):
        self.input_manager = InputManager()

    def test_keyboard_events(self):
        """测试键盘事件"""
        print("\nTesting Keyboard Events...")
        try:
            self.input_manager.start()
            print("Press keys to test (press 'q' to quit)...")
            time.sleep(5)  # 等待5秒进行测试
            self.input_manager.stop()
            return True
        except Exception as e:
            print(f"Keyboard event test failed: {e}")
            return False

    def test_mouse_events(self):
        """测试鼠标事件"""
        print("\nTesting Mouse Events...")
        try:
            self.input_manager.start()
            print("Click mouse to test (wait 5 seconds)...")
            time.sleep(5)  # 等待5秒进行测试
            self.input_manager.stop()
            return True
        except Exception as e:
            print(f"Mouse event test failed: {e}")
            return False

    def test_all(self):
        """运行所有测试"""
        tests = [
            self.test_keyboard_events,
            self.test_mouse_events
        ]
        
        results = []
        for test in tests:
            try:
                result = test()
                results.append((test.__name__, result))
            except Exception as e:
                results.append((test.__name__, False))
                print(f"Test {test.__name__} failed with error: {e}")

        print("\nTest Results:")
        for name, result in results:
            print(f"{name}: {'Success' if result else 'Failed'}")

        return all(result for _, result in results) 