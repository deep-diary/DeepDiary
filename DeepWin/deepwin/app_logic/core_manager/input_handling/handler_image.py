from .base import BaseInputHandler
import keyboard
import mouse

class ImageHandler():
    def __init__(self, manager):
        self.manager = manager

    def process_events(self, event_queue):
        queue = event_queue
        event_type, event_data = queue.get()
        if event_type == 'key':
            self.on_key_press_event(event_data)
        elif event_type == 'click':
            self.on_click_event(event_data)

    def on_key_press_event(self, event_data):
        print(f"Key pressed: {event_data}")
        key = event_data

        if key == keyboard.Key.space:
            print("Space key pressed in Camera")
        elif key == keyboard.Key.esc:
            print("Escape key pressed in Camera")
        elif key == keyboard.Key.enter:
            print("Enter key pressed in Camera")
        elif key == keyboard.Key.backspace:
            print("Backspace key pressed in Camera")
        elif key == 'q':
            print("Q key pressed in Camera")
        elif key == 's':
            print("S key pressed in Camera")
        elif key == 'r':
            print("R key pressed in Camera")

    def on_click_event(self, event_data):
        x, y, button = event_data
        print(f"Mouse clicked at ({x}, {y}) with {button}")
#             # 在这里处理鼠标点击事件
