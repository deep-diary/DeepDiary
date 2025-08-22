from input_handling.base import InputHandler
from pynput import keyboard

class ImageInputHandler(InputHandler):
    def __init__(self, image_manager):
        self.image_manager = image_manager

    def handle_key_event(self, key):
        if isinstance(key, keyboard.KeyCode):
            if key.char == 's':
                self.image_manager.save_current_image()
            elif key.char == 'n':
                self.image_manager.next_image()
            elif key.char == 'p':
                self.image_manager.previous_image()

    def handle_mouse_event(self, x, y, button, pressed):
        pass 