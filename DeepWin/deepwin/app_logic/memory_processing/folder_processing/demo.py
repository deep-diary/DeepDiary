import cv2
import argparse
from .manager import FolderManager

class FolderDemo:
    """文件夹处理演示类"""
    def __init__(self):
        self.manager = FolderManager()

    def test_canvas_creation(self, folder_path=None):
        """测试画布创建"""
        print("\nTesting Canvas Creation...")
        try:
            output_path = self.manager.process_folder(folder_path, 'canvas')
            if output_path:
                print(f"Canvas created successfully: {output_path}")
                # 显示结果
                canvas = cv2.imread(output_path)
                cv2.imshow("Canvas Result", canvas)
                cv2.waitKey(0)
                cv2.destroyAllWindows()
                return True
            return False
        except Exception as e:
            print(f"Canvas creation failed: {e}")
            return False

    def test_rename(self, folder_path=None):
        """测试文件重命名"""
        print("\nTesting File Rename...")
        try:
            result = self.manager.process_folder(folder_path, 'rename')
            print(f"Rename operation {'succeeded' if result else 'failed'}")
            return result
        except Exception as e:
            print(f"Rename test failed: {e}")
            return False

    def test_duplicate_finder(self, folder_path=None):
        """测试重复文件查找"""
        print("\nTesting Duplicate Finder...")
        try:
            result = self.manager.process_folder(folder_path, 'duplicate')
            print(f"Duplicate finding {'succeeded' if result else 'failed'}")
            return result
        except Exception as e:
            print(f"Duplicate finder test failed: {e}")
            return False

    def test_auto_classifier(self, folder_path=None):
        """测试自动分类"""
        print("\nTesting Auto Classifier...")
        try:
            result = self.manager.process_folder(folder_path, 'classify')
            print(f"Auto classification {'succeeded' if result else 'failed'}")
            return result
        except Exception as e:
            print(f"Auto classifier test failed: {e}")
            return False

    def test_all(self, folder_path=None):
        """运行所有测试"""
        tests = [
            (lambda: self.test_canvas_creation(folder_path), "Canvas Creation Test"),
            (lambda: self.test_rename(folder_path), "File Rename Test"),
            (lambda: self.test_duplicate_finder(folder_path), "Duplicate Finder Test"),
            (lambda: self.test_auto_classifier(folder_path), "Auto Classifier Test")
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
    parser = argparse.ArgumentParser(description='Folder Processing Demo')
    parser.add_argument('--test', 
                       choices=['canvas', 'rename', 'duplicate', 'classify', 'all'],
                       default='canvas', 
                       help='Test to run')
    parser.add_argument('--folder', type=str, help='Optional custom input folder path')
    
    args = parser.parse_args()
    demo = FolderDemo()
    
    test_funcs = {
        'canvas': demo.test_canvas_creation,
        'rename': demo.test_rename,
        'duplicate': demo.test_duplicate_finder,
        'classify': demo.test_auto_classifier,
        'all': demo.test_all
    }
    
    test_func = test_funcs.get(args.test)
    if test_func:
        test_func(args.folder)
    else:
        print(f"Unknown test: {args.test}")
        print("\nAvailable tests:")
        print("  canvas    - Test canvas creation")
        print("  rename    - Test file rename")
        print("  duplicate - Test duplicate finder")
        print("  classify  - Test auto classifier")
        print("  all       - Run all tests")

if __name__ == "__main__":
    main() 