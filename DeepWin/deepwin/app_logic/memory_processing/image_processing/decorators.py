import time
import cv2
from .config_manager import ConfigManager

def display_fps():
    def decorator(func):
        def wrapper(*args, **kwargs):
            config_manager = ConfigManager()
            show_fps = config_manager.get('image_processing', 'show_fps', False)
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            fps = 1 / (end_time - start_time)
            if show_fps:
                image = result[0]
                cv2.putText(image, f"FPS: {fps:.2f}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
                return (image,) + result[1:]
            return result
        return wrapper
    return decorator