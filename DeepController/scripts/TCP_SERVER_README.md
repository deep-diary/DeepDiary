# ESP32 TCP 视频服务器使用指南

本目录提供了三个不同版本的 TCP 视频服务器，用于接收 ESP32 发送的摄像头图像流。

## 📦 安装依赖

```bash
# 安装 Python 依赖包
pip install -r requirements_tcp_server.txt

# 或者手动安装
pip install opencv-python numpy
```

## 🎯 服务器版本选择

### 1️⃣ **简化版** (`tcp_video_server_simple.py`)

**适用场景：** 快速测试、本地开发

**特点：**
- ✅ 代码简洁（~80 行）
- ✅ 快速启动
- ✅ 基本的图像显示功能
- ❌ 无高级功能

**使用方法：**
```bash
python tcp_video_server_simple.py
```

**快捷键：**
- `q` - 退出程序

---

### 2️⃣ **完整版** (`tcp_video_server.py`)

**适用场景：** 本地监控、视频录制、专业开发

**特点：**
- ✅ 完整功能
- ✅ 视频录制
- ✅ 截图保存
- ✅ 多客户端支持
- ✅ 详细统计信息
- ✅ 可配置参数

**基本使用：**
```bash
# 启动服务器（默认端口 8080）
python tcp_video_server.py

# 指定端口
python tcp_video_server.py --port 9090

# 启用视频录制
python tcp_video_server.py --save-video

# 完整配置
python tcp_video_server.py --host 0.0.0.0 --port 8080 --save-video --save-dir ./recordings --fps 30
```

**快捷键：**
- `q` - 退出程序
- `s` - 保存当前帧截图

**命令行参数：**
```
--host HOST          监听地址 (默认: 0.0.0.0)
--port PORT          监听端口 (默认: 8080)
--save-video         保存接收到的视频
--save-dir DIR       视频保存目录 (默认: recordings)
--fps FPS            保存视频的帧率 (默认: 30)
--log-level LEVEL    日志级别 (DEBUG/INFO/WARNING/ERROR)
```

---

### 3️⃣ **Web 版** (`tcp_video_server_web.py`)

**适用场景：** 云端部署、远程监控、多用户访问

**特点：**
- ✅ 浏览器访问
- ✅ 无需安装 OpenCV 窗口
- ✅ 支持多用户同时观看
- ✅ 响应式 Web 界面
- ✅ 实时状态显示
- ✅ 在线截图下载

**使用方法：**
```bash
# 启动服务器
python tcp_video_server_web.py

# 指定端口
python tcp_video_server_web.py --tcp-port 8080 --web-port 8000

# 完整配置
python tcp_video_server_web.py \
    --tcp-host 0.0.0.0 \
    --tcp-port 8080 \
    --web-host 0.0.0.0 \
    --web-port 8000
```

**访问方式：**
```
浏览器访问: http://服务器IP:8000
本地访问:   http://localhost:8000
```

**Web 接口：**
- `/` - 主页（视频显示和控制）
- `/stream` - 原始 MJPEG 视频流
- `/snapshot` - 下载当前帧截图
- `/status` - JSON 格式状态信息

---

## 🚀 快速开始

### Step 1: 配置 ESP32

在 `config.h` 中设置服务器地址：
```c
#define TCP_SERVER_IP "192.168.31.100"  // 改为你的电脑 IP
#define TCP_SERVER_PORT 8080
```

### Step 2: 启动服务器

**本地测试（推荐简化版）：**
```bash
python tcp_video_server_simple.py
```

**专业使用（推荐完整版）：**
```bash
python tcp_video_server.py --save-video
```

**云端部署（推荐 Web 版）：**
```bash
python tcp_video_server_web.py
```

### Step 3: 连接 ESP32

1. 编译并上传固件到 ESP32
2. ESP32 连接 WiFi
3. 自动连接到 TCP 服务器
4. 开始传输视频流

---

## 🌐 云端部署指南

### 部署到阿里云/腾讯云/AWS

**1. 准备服务器**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip

# CentOS/RHEL
sudo yum install python3 python3-pip
```

**2. 安装依赖**
```bash
pip3 install opencv-python-headless numpy
```

**3. 上传服务器文件**
```bash
scp tcp_video_server_web.py user@your-server-ip:/home/user/
```

**4. 运行服务器**
```bash
# 使用 nohup 后台运行
nohup python3 tcp_video_server_web.py --tcp-port 8080 --web-port 80 > server.log 2>&1 &

# 或使用 systemd 服务（推荐）
```

**5. 配置防火墙**
```bash
# 开放 TCP 端口（ESP32 连接）
sudo ufw allow 8080/tcp

# 开放 Web 端口（浏览器访问）
sudo ufw allow 80/tcp
```

**6. 配置 ESP32**
```c
#define TCP_SERVER_IP "your-server-public-ip"
#define TCP_SERVER_PORT 8080
```

### 使用 systemd 服务（推荐）

创建服务文件 `/etc/systemd/system/esp32-video.service`：
```ini
[Unit]
Description=ESP32 Video Stream Server
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/home/your-username
ExecStart=/usr/bin/python3 /home/your-username/tcp_video_server_web.py --tcp-port 8080 --web-port 80
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl start esp32-video
sudo systemctl enable esp32-video
sudo systemctl status esp32-video
```

---

## 📊 性能优化

### 降低延迟
```python
# 在代码中调整接收缓冲区大小
data = client_socket.recv(8192)  # 增加到 8KB
```

### 提高帧率
修改 ESP32 发送延时：
```cpp
// tcp_client.cc 第 78 行
vTaskDelay(pdMS_TO_TICKS(16));  // 改为约 60fps
```

### 降低带宽占用
调整 ESP32 JPEG 质量：
```cpp
// board_extensions.cc
config.jpeg_quality = 10;  // 降低质量（0-63，越小越高）
```

---

## 🔧 故障排查

### 1. ESP32 无法连接

**检查项：**
- [ ] 服务器是否正在运行？
- [ ] IP 地址是否正确？
- [ ] 端口是否被占用？
- [ ] 防火墙是否开放端口？

```bash
# 检查端口占用
netstat -an | grep 8080

# 测试端口连通性
telnet server-ip 8080
```

### 2. 视频卡顿

**原因：**
- 网络带宽不足
- 服务器性能不足
- 图像质量过高

**解决方案：**
- 降低 JPEG 质量
- 减小图像分辨率
- 使用有线网络

### 3. 图像花屏/解码失败

**原因：**
- 数据传输错误
- JPEG 帧不完整

**解决方案：**
- 检查网络质量
- 增加重连间隔
- 检查日志错误

---

## 📝 示例输出

### 服务器日志
```
2025-10-23 14:30:00 - INFO - TCP 视频服务器已启动
2025-10-23 14:30:00 - INFO - 监听地址: 0.0.0.0:8080
2025-10-23 14:30:05 - INFO - 客户端已连接: ('192.168.31.200', 54321)
2025-10-23 14:30:10 - INFO - 已接收 100 帧, 当前帧率: 28.50 fps
2025-10-23 14:30:15 - INFO - 已接收 200 帧, 当前帧率: 29.20 fps
```

### ESP32 日志
```
I (12345) TCP_CLIENT: TCP客户端初始化完成
I (12346) TCP_CLIENT: 服务器: 192.168.31.100:8080
I (15000) TCP_CLIENT: Socket创建成功，准备连接
I (15100) TCP_CLIENT: TCP连接成功！
I (15150) TCP_CLIENT: 发送 8234 字节
```

---

## 🎨 高级功能

### 1. 视频录制
```bash
python tcp_video_server.py --save-video --save-dir /path/to/recordings --fps 30
```

### 2. 多客户端监控
Web 版支持多个 ESP32 同时连接（需修改代码支持多客户端管理）

### 3. 运动检测
可以基于 OpenCV 添加运动检测功能：
```python
# 在 process_frame 中添加
if frame is not None:
    # 运动检测逻辑
    pass
```

### 4. 人脸识别
集成 OpenCV 人脸检测：
```python
face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
faces = face_cascade.detectMultiScale(frame, 1.1, 4)
```

---

## 📚 扩展阅读

- [OpenCV 官方文档](https://docs.opencv.org/)
- [Python Socket 编程](https://docs.python.org/3/library/socket.html)
- [MJPEG 流协议](https://en.wikipedia.org/wiki/Motion_JPEG)

---

## 🆘 获取帮助

遇到问题？
1. 查看日志输出
2. 检查网络连接
3. 阅读故障排查部分
4. 提交 Issue 或联系技术支持

---

## 📄 许可证

本项目基于 MIT 许可证开源

---

**作者:** DeepDiary Team  
**更新日期:** 2025-10-23

