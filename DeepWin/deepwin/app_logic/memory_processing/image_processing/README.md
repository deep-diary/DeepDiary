# DeepWin 图像处理包

## 简介

这是 DeepWin 项目的图像处理包，集成了多种图像处理功能，包括人脸检测、人脸识别、姿态检测、手势识别、OCR 文字识别、QR 码处理等。该包已完全整合到 DeepWin 项目中，使用统一的日志管理和配置管理。

## 包结构

```
image_processing/
├── __init__.py                 # 包初始化文件，导出主要接口
├── README.md                   # 本文档
├── manager.py                  # 图像处理管理器，统一管理所有处理器
├── base.py                     # 图像处理器基类
├── decorators.py               # 装饰器，如FPS显示等
├── decorators.py               # 装饰器，如FPS显示等
├── filters.py                  # 图像滤波器
├── input_handler.py            # 输入处理器
├── tracker_base.py             # 追踪器基类
├── tracker_cv.py               # OpenCV追踪器实现
├── processor_*.py              # 各种图像处理器实现
│   ├── processor_face_detection.py      # 人脸检测
│   ├── processor_face_recognition.py    # 人脸识别
│   ├── processor_face_mesh.py           # 人脸网格
│   ├── processor_pose.py                # 姿态检测
│   ├── processor_hand_gesture.py        # 手势识别
│   ├── processor_ocr.py                 # OCR文字识别
│   ├── processor_easy_ocr.py            # EasyOCR文字识别
│   ├── processor_qr_code.py             # QR码处理
│   └── processor_yolo.py                # YOLO目标检测
├── configs/                    # 配置文件目录
│   └── config.json             # 图像处理配置
├── demo/                       # 演示图像和视频
└── demo.py                     # 演示脚本
```

## 主要功能

### 1. 人脸检测 (Face Detection)

使用 MediaPipe 实现的人脸检测功能。

### 2. 人脸网格 (Face Mesh)

使用 MediaPipe 实现的人脸网格检测。

### 3. 姿态检测 (Pose Detection)

使用 MediaPipe 实现的人体姿态检测。

### 4. 手势识别 (Hand Gesture)

使用 MediaPipe 实现的手势识别功能。

### 5. OCR 文字识别

支持两种 OCR 引擎：TrOCR 和 EasyOCR。

### 6. QR 码处理

支持 QR 码的生成、检测和解码。

### 7. YOLO 目标检测

支持使用 YOLO 模型进行目标检测和追踪。

## 使用示例

```python
from deepwin.app_logic.memory_processing.image_processing import ImageManager
from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager

# 初始化日志和配置管理器
log_manager = LogManager()
config_manager = ConfigManager(log_manager)

# 创建图像管理器
manager = ImageManager(log_manager, config_manager)

# 处理图像
result = manager.process_image("input.jpg", "face_detection")

# 获取结果信息
info = manager.get_processor("face_detection").get_result_info()
print(f"检测到人脸: {info['target_found']}")
```

## 配置管理

```python
from deepwin.config.config_manager import ConfigManager
from deepwin.data_management.log_manager import LogManager

# 初始化配置管理器
log_manager = LogManager()
config_manager = ConfigManager(log_manager)

# 获取图像处理配置
image_config = config_manager.get('image_processing')

# 获取处理器配置
processor_config = config_manager.get('image_processing.processors.face_detection')

# 获取追踪配置
tracking_config = config_manager.get('image_processing.tracking')
```

## 日志管理

```python
from deepwin.data_management.log_manager import LogManager

# 获取日志管理器
log_manager = LogManager()
logger = log_manager.get_logger(__name__)

# 记录日志
logger.info("处理完成")
logger.error("处理失败")
```

## 依赖要求

- OpenCV >= 4.5.0
- MediaPipe >= 0.8.0
- NumPy >= 1.19.0
- PyTorch >= 1.8.0
- Python >= 3.8

## 注意事项

1. 所有处理器都支持实时处理和批处理
2. 可以通过配置文件调整各处理器的参数
3. 所有返回的图像都是 BGR 格式（OpenCV 默认格式）
4. 处理结果会自动缓存以提高性能
5. 使用统一的日志管理和配置管理
