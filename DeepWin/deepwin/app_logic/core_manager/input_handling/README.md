# Input Handling Package

## 简介

输入处理包,用于处理键盘、鼠标等输入设备的事件。支持热键配置、手势识别等功能。

## 主要功能

### 1. 键盘事件处理

```python
from input_handling.keyboard_handler import KeyboardHandler

handler = KeyboardHandler()

# 注册按键回调
@handler.on_key_press('space')
def on_space():
    print("Space pressed")

# 注册组合键
@handler.on_hotkey('ctrl+s')
def on_save():
    print("Save triggered")

# 开始监听
handler.start()
```

### 2. 鼠标事件处理

```python
from input_handling.mouse_handler import MouseHandler

mouse = MouseHandler()

# 注册鼠标事件
@mouse.on_click
def on_click(x, y, button, pressed):
    print(f"Click at ({x}, {y})")

@mouse.on_scroll
def on_scroll(dx, dy):
    print(f"Scroll: {dx}, {dy}")
```

### 3. 手势处理

```python
from input_handling.gesture_handler import GestureHandler

gesture = GestureHandler()

# 注册手势回调
@gesture.on_gesture("swipe_left")
def on_swipe_left():
    print("Swipe left detected")
```

## 事件类型

```python
class InputEvent:
    KEY_PRESS = 1
    KEY_RELEASE = 2
    MOUSE_CLICK = 3
    MOUSE_MOVE = 4
    MOUSE_SCROLL = 5
    GESTURE = 6
```

## 配置说明

```json
{
  "keyboard": {
    "enable_hotkeys": true,
    "hotkeys": {
      "ctrl+s": "save",
      "ctrl+q": "quit"
    }
  },
  "mouse": {
    "sensitivity": 1.0,
    "invert_y": false
  },
  "gesture": {
    "min_distance": 50,
    "max_time": 1.0
  }
}
```

## 注意事项

1. 键盘监听需要适当权限
2. 避免在回调函数中执行耗时操作
3. 手势识别可能需要校准
