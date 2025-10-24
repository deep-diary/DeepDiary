# MediaMTX 流媒体系统使用说明

## 系统架构

MediaMTX 流媒体系统由三个核心模块组成：

1. **`mediamtx_push.py`** - 推流器类
2. **`mediamtx_pull.py`** - 拉流器类
3. **`mediamtx_manager.py`** - 管理器类

## 模块说明

### 1. MediaMTX 推流器 (`mediamtx_push.py`)

#### 主要功能

- 从摄像头捕获视频流
- 支持两种推流方式：直接推流和管道推流
- 自动检测 DirectShow 设备（Windows）
- 实时统计和监控

#### 核心类：`MediaMTXPusher`

```python
from mediamtx_push import MediaMTXPusher

# 创建推流器
pusher = MediaMTXPusher(server_host='34.172.161.212', server_port=8554)

# 设置推流参数
pusher.set_stream_params(width=640, height=480, fps=30, crf=23)

# 开始推流
pusher.start_stream(camera_index=0, method='pipeline')  # 或 'direct'

# 获取统计信息
stats = pusher.get_stats()

# 停止推流
pusher.stop_stream()
```

#### 推流方式对比

| 方式       | 优点           | 缺点       | 适用场景 |
| ---------- | -------------- | ---------- | -------- |
| `direct`   | 性能好，延迟低 | 兼容性问题 | 稳定环境 |
| `pipeline` | 兼容性好，稳定 | 稍高延迟   | 推荐使用 |

### 2. MediaMTX 拉流器 (`mediamtx_pull.py`)

#### 主要功能

- 从 RTSP 服务器拉取视频流
- 自动重连机制
- 多种传输协议支持（TCP/UDP）
- 实时预览和统计

#### 核心类：`MediaMTXPuller`

```python
from mediamtx_pull import MediaMTXPuller

# 创建拉流器
puller = MediaMTXPuller(server_host='34.172.161.212', server_port=8554)

# 设置流名称
puller.set_stream_name('camera_stream')

# 开始播放
puller.start_play(show_preview=True, show_stats=True)

# 获取统计信息
stats = puller.get_stats()

# 停止播放
puller.stop_play()
```

### 3. MediaMTX 管理器 (`mediamtx_manager.py`)

#### 主要功能

- 统一管理推流和拉流
- 自动监控和重连
- 系统状态监控
- 多流管理

#### 核心类：`MediaMTXManager`

```python
from mediamtx_manager import MediaMTXManager

# 创建管理器
manager = MediaMTXManager(server_host='34.172.161.212', server_port=8554)

# 启动推流
manager.start_push(
    camera_index=0,
    stream_name='camera_stream',
    method='pipeline',
    width=640, height=480, fps=30, crf=23
)

# 启动拉流
manager.start_pull(
    stream_name='camera_stream',
    show_preview=True,
    show_stats=True
)

# 启动监控
manager.start_monitoring()

# 查看状态
manager.print_status()

# 清理资源
manager.cleanup()
```

## 使用示例

### 基本推流示例

```python
from mediamtx_push import MediaMTXPusher

def basic_push():
    pusher = MediaMTXPusher()
    pusher.set_stream_params(width=640, height=480, fps=30)

    try:
        pusher.start_stream(camera_index=0, method='pipeline')
        print("推流已启动，按Ctrl+C停止")

        while pusher.is_streaming:
            time.sleep(1)
    except KeyboardInterrupt:
        print("停止推流")
    finally:
        pusher.stop_stream()

if __name__ == "__main__":
    basic_push()
```

### 基本拉流示例

```python
from mediamtx_pull import MediaMTXPuller

def basic_pull():
    puller = MediaMTXPuller()

    try:
        puller.start_play(show_preview=True, show_stats=True)
    except KeyboardInterrupt:
        print("停止播放")
    finally:
        puller.stop_play()

if __name__ == "__main__":
    basic_pull()
```

### 完整系统示例

```python
from mediamtx_manager import MediaMTXManager
import time

def full_system():
    manager = MediaMTXManager()

    try:
        # 启动推流
        manager.start_push(
            camera_index=0,
            stream_name='camera_stream',
            method='pipeline'
        )

        # 等待推流稳定
        time.sleep(3)

        # 启动拉流
        manager.start_pull(
            stream_name='camera_stream',
            show_preview=True
        )

        # 启动监控
        manager.start_monitoring()

        # 保持运行
        while True:
            time.sleep(10)
            manager.print_status()

    except KeyboardInterrupt:
        print("停止系统")
    finally:
        manager.cleanup()

if __name__ == "__main__":
    full_system()
```

## 配置参数

### 推流参数

| 参数      | 默认值  | 说明              |
| --------- | ------- | ----------------- |
| `width`   | 640     | 视频宽度          |
| `height`  | 480     | 视频高度          |
| `fps`     | 30      | 帧率              |
| `bitrate` | '1000k' | 比特率            |
| `crf`     | 23      | 质量因子（18-28） |

### 拉流参数

| 参数              | 默认值 | 说明           |
| ----------------- | ------ | -------------- |
| `max_retry_count` | 5      | 最大重连次数   |
| `retry_delay`     | 3.0    | 重连延迟（秒） |
| `show_preview`    | True   | 显示预览窗口   |
| `show_stats`      | True   | 显示统计信息   |

### 管理参数

| 参数               | 默认值 | 说明           |
| ------------------ | ------ | -------------- |
| `auto_reconnect`   | True   | 自动重连       |
| `monitor_interval` | 10.0   | 监控间隔（秒） |

## 故障排除

### 常见问题

1. **推流失败**

   - 检查摄像头是否被占用
   - 确认网络连接
   - 尝试不同的推流方法

2. **拉流失败**

   - 检查 RTSP 服务器状态
   - 确认流名称正确
   - 检查防火墙设置

3. **连接不稳定**
   - 调整重连参数
   - 检查网络质量
   - 使用 TCP 传输

### 调试技巧

1. **启用详细日志**:

   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **测试连接**:

   ```python
   from mediamtx_pull import test_rtsp_connection
   success = test_rtsp_connection('rtsp://34.172.161.212:8554/camera_stream')
   ```

3. **查看状态**:
   ```python
   manager.print_status()
   ```

## 性能优化

### 推流优化

- 使用`pipeline`方法提高稳定性
- 调整 CRF 值平衡质量和带宽
- 设置合适的 GOP 大小

### 拉流优化

- 使用 TCP 传输减少丢包
- 设置小缓冲区减少延迟
- 启用自动重连

### 系统优化

- 定期监控系统状态
- 及时清理资源
- 合理设置监控间隔

## 扩展功能

### 可以添加的功能

- 多摄像头推流
- 录制功能
- 截图功能
- 流质量监控
- Web 管理界面
- 配置文件支持

### 集成建议

- 与 Web 框架集成
- 添加数据库支持
- 实现用户认证
- 添加通知系统
