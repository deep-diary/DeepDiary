import time
import cv2

def display_fps():
    """FPS显示装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            fps = 1 / (end_time - start_time)
            
            # 如果结果是图像，则显示FPS
            if isinstance(result, (list, tuple)) and len(result) > 0:
                image = result[0]
                if hasattr(image, 'shape'):  # 检查是否为图像
                    cv2.putText(image, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                    return (image,) + result[1:]
            return result
        return wrapper
    return decorator