from .base import BaseInputHandler
from pynput import keyboard
from pynput import mouse

class CameraHandler():
    def __init__(self, manager):
        self.manager = manager

    def process_events(self, event_queue):
        while not event_queue.empty():
            event_type, event_data = event_queue.get()
            if event_type == 'key':
                self.on_key_press_event(event_data)
            elif event_type == 'click':
                self.on_click_event(event_data)

    def on_key_press_event(self, event_data):
        print(f"Key pressed: {event_data}")
        print(type(event_data))
        if isinstance(event_data, keyboard.Key):
            if event_data == keyboard.Key.enter:
                self.manager.initialize_camera()
                print("Enter key pressed in Camera")
            if event_data == keyboard.Key.space:
                print("Space key pressed in Camera")
            elif event_data == keyboard.Key.esc:
                print("Escape key pressed in Camera")
        elif isinstance(event_data, keyboard.KeyCode):
            if event_data.char == 'q':
                print("Q key pressed in Camera")
                self.manager.release_camera()
            elif event_data.char == 's':
                print("S key pressed in Camera")
                self.manager.save_frame()
            elif event_data.char == 'r':
                print("R key pressed in Camera")
                self.manager.toggle_recording()
            else:
                print(f"Unknown key pressed in Camera: {event_data.char}")
        else:
            print(f"Unknown event type: {type(event_data)}")

    def on_click_event(self, event_data):
        x, y, button = event_data
        print(f"Mouse clicked at ({x}, {y}) with {button}")
#             # 在这里处理鼠标点击事件
