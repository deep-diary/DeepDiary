# Image Processing Package

## 简介

这是一个功能丰富的图像处理包，集成了多种图像处理功能，包括人脸检测、人脸识别、姿态检测、手势识别、OCR 文字识别、QR 码处理等。

## 主要功能

### 1. 人脸检测 (Face Detection)

使用 MediaPipe 实现的人脸检测功能。

```python
from image_processing.manager import ImageManager

manager = ImageManager()
result = manager.process_image("image.jpg", "face_detection")
info = manager.get_processor("face_detection").get_result_info()
```

返回信息格式：

```python
{
    "status": "Face detected",  # 或 "No face detected"
    "target_found": True,       # 是否检测到目标
    "target_center": [x, y],    # 目标中心坐标
    "target_size": [w, h],      # 目标大小
    "error_x": float,           # X轴误差
    "error_y": float,           # Y轴误差
    "confidence": float         # 置信度
}
```

### 2. 人脸网格 (Face Mesh)

使用 MediaPipe 实现的人脸网格检测。

```python
result = manager.process_image("image.jpg", "face_mesh")
info = manager.get_processor("face_mesh").get_result_info()
```

返回信息格式：

```python
{
    "status": "Face mesh detected",
    "landmarks_found": True,
    "landmark_count": int,      # 检测到的特征点数量
    "eye_state": {
        "left_eye": "open",     # 或 "closed"
        "right_eye": "open",    # 或 "closed"
        "blink_detected": bool
    }
}
```

### 3. 姿态检测 (Pose Detection)

使用 MediaPipe 实现的人体姿态检测。

```python
result = manager.process_image("image.jpg", "pose")
info = manager.get_processor("pose").get_result_info()
```

返回信息格式：

```python
{
    "target_found": bool,
    "target_center": [x, y],
    "target_size": [w, h],
    "pose_state": {
        "is_jumping": bool,
        "jump_height": float,
        "left_arm_angle": float,
        "right_arm_angle": float,
        "body_rotation": float,
        "standing_straight": bool
    }
}
```

### 4. 手势识别 (Hand Gesture)

使用 MediaPipe 实现的手势识别功能。

```python
result = manager.process_image("image.jpg", "hand_gesture")
info = manager.get_processor("hand_gesture").get_result_info()
```

返回信息格式：

```python
{
    "target_found": bool,
    "gesture_info": {
        "left_hand": {
            "gesture": str,     # 手势类型
            "confidence": float,
            "is_drawing": bool
        },
        "right_hand": {
            "gesture": str,
            "confidence": float,
            "is_drawing": bool
        }
    }
}
```

### 5. OCR 文字识别

支持两种 OCR 引擎：TrOCR 和 EasyOCR。

```python
# EasyOCR
result = manager.process_image("image.jpg", "easy_ocr")
info = manager.get_processor("easy_ocr").get_result_info()
```

返回信息格式：

```python
{
    "status": "OCR processed",
    "text_found": bool,
    "results": [
        {
            "text": str,
            "confidence": float,
            "position": [x1, y1, x2, y2]
        }
    ]
}
```

### 6. QR 码处理

支持 QR 码的生成、检测和解码。

```python
result = manager.process_image("image.jpg", "qr_code")
info = manager.get_processor("qr_code").get_result_info()
```

返回信息格式：

```python
{
    "target_found": bool,
    "qr_data": str,            # 解码数据
    "detection_time": float,
    "detection_history": [
        {
            "timestamp": float,
            "data": str,
            "position": (x, y),
            "size": (w, h)
        }
    ]
}
```

### 7. YOLO 目标检测

支持使用 YOLO 模型进行目标检测和追踪。

```python
result = manager.process_image("image.jpg", "yolo")
info = manager.get_processor("yolo").get_result_info()
```

返回信息格式：

```python
{
    "target_found": bool,
    "detections": [
        {
            "class": str,
            "confidence": float,
            "bbox": [x1, y1, x2, y2]
        }
    ],
    "tracking_info": {         # 仅在追踪模式下
        "track_id": int,
        "track_bbox": [x1, y1, x2, y2]
    }
}
```

## 配置管理

所有处理器的配置都可以通过 config.json 文件进行管理：

```python
from image_processing.config_manager import ConfigManager

config = ConfigManager()
processor_config = config.get('processors', 'face_detection')
```

## 错误处理

所有处理器都包含异常处理机制，当处理失败时会返回原始图像并在日志中记录错误信息。

## 性能监控

支持 FPS 显示和性能统计：

```python
from image_processing.decorators import display_fps

@display_fps()
def process_image():
    # 处理图像
    pass
```

## 依赖要求

- OpenCV
- MediaPipe
- NumPy
- EasyOCR
- PyTorch
- YOLO
- qrcode

## 注意事项

1. 所有处理器都支持实时处理和批处理
2. 可以通过配置文件调整各处理器的参数
3. 所有返回的图像都是 BGR 格式（OpenCV 默认格式）
4. 处理结果会自动缓存以提高性能
