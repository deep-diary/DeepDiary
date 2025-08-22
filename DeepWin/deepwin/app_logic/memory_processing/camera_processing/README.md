# Camera Processing Package

## 简介

相机处理包,用于处理相机图像流和云台控制。支持实时图像采集、云台运动控制以及目标追踪等功能。

## 主要功能

### 1. 相机控制

```python
from camera_processing.manager import CameraManager

# 初始化相机管理器
manager = CameraManager()

# 打开相机
manager.open_camera(0)  # 使用默认相机

# 获取图像
frame = manager.get_frame()

# 关闭相机
manager.close_camera()
```

### 2. 云台控制

```python
from camera_processing.processor import CameraProcessor

processor = CameraProcessor()

# 设置云台角度
processor.set_angles(h_angle=30, v_angle=20)  # 水平30度,垂直20度

# 读取当前角度
angles = processor.read_angles()  # 返回(h_angle, v_angle)

# 设置追踪误差
processor.set_error(error_x=10, error_y=-5, target_found=True)
```

### 3. 状态信息

```python
# 获取云台状态
status = processor.get_status()
```

返回格式:

```python
{
    'horizontal_angle': float,  # 水平角度
    'vertical_angle': float,    # 垂直角度
    'error_x': float,          # X轴误差
    'error_y': float           # Y轴误差
}
```

## 重要参数

### CameraProcessor

- `h_angle_limits`: 水平角度范围 (-135°~135°)
- `v_angle_limits`: 垂直角度范围 (-85°~85°)

### CameraManager

- `frame_width`: 图像宽度
- `frame_height`: 图像高度
- `fps`: 帧率

## 配置说明

通过 config.json 配置相机和云台参数:

```json
{
  "camera": {
    "device_id": 0,
    "width": 640,
    "height": 480,
    "fps": 30
  },
  "gimbal": {
    "h_angle_limit": [-135, 135],
    "v_angle_limit": [-85, 85],
    "speed": 30
  }
}
```

## 注意事项

1. 确保相机已正确连接
2. 云台角度设置需在限制范围内
3. 图像格式为 BGR(OpenCV 默认格式)
4. 所有角度单位为度
