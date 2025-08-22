from abc import ABC, abstractmethod
from pynput import keyboard, mouse
import cv2
import queue
import time
from .config_manager import ConfigManager

class InputHandler(ABC):
    """输入处理器基类"""
    @abstractmethod
    def handle_key_press(self, key):
        """处理键盘按下瞬间事件"""
        pass

    @abstractmethod
    def handle_key_holding(self, key):
        """处理键盘持续按下事件"""
        pass

    @abstractmethod
    def handle_key_release(self, key):
        """处理键盘释放事件"""
        pass

    @abstractmethod
    def handle_mouse_event(self, event, x, y, flags, param):
        """处理OpenCV窗口的鼠标事件
        Args:
            event: OpenCV鼠标事件类型
            x, y: 窗口内的鼠标坐标
            flags: 事件标志
            param: 额外参数
        """
        pass

class InputListener:
    """输入监听器"""
    def __init__(self):
        self.config = ConfigManager()
        self.event_queue = queue.Queue()
        self.handlers = {}
        self.active_handler = None
        self.window_name = None
        
        # 按键状态跟踪
        self.pressed_keys = set()
        self.key_press_time = {}
        self.key_hold_threshold = 0.2  # 持续按下阈值（秒）
        
        # 初始化键盘监听器
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )

    def start(self):
        """启动监听"""
        self.keyboard_listener.start()
        self._start_key_holding_check()

    def stop(self):
        """停止监听"""
        self.keyboard_listener.stop()
        if self.window_name:
            cv2.destroyWindow(self.window_name)

    def _start_key_holding_check(self):
        """启动按键持续检查"""
        import threading
        def check_holding_keys():
            while self.keyboard_listener.running:
                current_time = time.time()
                for key in list(self.pressed_keys):
                    if (current_time - self.key_press_time.get(key, 0)) >= self.key_hold_threshold:
                        if self.active_handler:
                            self.handlers[self.active_handler].handle_key_holding(key)
                time.sleep(0.1)  # 降低CPU使用率

        holding_thread = threading.Thread(target=check_holding_keys, daemon=True)
        holding_thread.start()

    def register_handler(self, name: str, handler: InputHandler):
        """注册事件处理器"""
        self.handlers[name] = handler
        if self.active_handler is None:
            self.active_handler = name

    def set_active_handler(self, name: str):
        """设置活动的处理器"""
        if name in self.handlers:
            self.active_handler = name

    def set_window(self, window_name: str):
        """设置OpenCV窗口名称并注册鼠标回调"""
        self.window_name = window_name
        cv2.setMouseCallback(window_name, self._on_mouse_event)

    def _on_key_press(self, key):
        """键盘按下事件回调"""
        if key not in self.pressed_keys:
            # 首次按下
            self.pressed_keys.add(key)
            self.key_press_time[key] = time.time()
            if self.active_handler:
                self.handlers[self.active_handler].handle_key_press(key)

    def _on_key_release(self, key):
        """键盘释放事件回调"""
        self.pressed_keys.discard(key)
        self.key_press_time.pop(key, None)
        if self.active_handler:
            self.handlers[self.active_handler].handle_key_release(key)

    def _on_mouse_event(self, event, x, y, flags, param):
        """OpenCV窗口鼠标事件回调"""
        if self.active_handler:
            self.handlers[self.active_handler].handle_mouse_event(event, x, y, flags, param)
