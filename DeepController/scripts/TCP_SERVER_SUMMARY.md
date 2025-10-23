# 📺 ESP32 TCP 视频流服务器 - 完整方案

## 🎉 项目概述

本方案为 ESP32 摄像头提供了完整的 TCP 视频流传输和接收解决方案，支持本地监控和云端部署。

---

## 📦 已创建文件清单

### 🔧 ESP32 端（客户端）

| 文件 | 位置 | 说明 |
|------|------|------|
| `tcp_client.h` | `main/boards/atk-dnesp32s3/streaming/` | TCP 客户端头文件 |
| `tcp_client.cc` | `main/boards/atk-dnesp32s3/streaming/` | TCP 客户端实现 |
| `config.h` | `main/boards/atk-dnesp32s3/` | 配置文件（已修改） |
| `board_extensions.h` | `main/boards/atk-dnesp32s3/` | 扩展功能头文件（已修改） |
| `board_extensions.cc` | `main/boards/atk-dnesp32s3/` | 扩展功能实现（已修改） |
| `atk_dnesp32s3.cc` | `main/boards/atk-dnesp32s3/` | 主板文件（已修改） |

### 💻 PC/服务器端（接收端）

| 文件 | 位置 | 说明 |
|------|------|------|
| `tcp_video_server_simple.py` | `scripts/` | 简化版服务器（快速测试） |
| `tcp_video_server.py` | `scripts/` | 完整版服务器（视频录制） |
| `tcp_video_server_web.py` | `scripts/` | Web 版服务器（云端部署） |
| `requirements_tcp_server.txt` | `scripts/` | Python 依赖文件 |
| `start_server.sh` | `scripts/` | 快速启动脚本 |
| `TCP_SERVER_README.md` | `scripts/` | 详细使用文档 |

### 📚 文档

| 文件 | 位置 | 说明 |
|------|------|------|
| `README.md` | `main/boards/atk-dnesp32s3/streaming/` | 流媒体模块说明（已更新） |
| `TCP_SERVER_README.md` | `scripts/` | 服务器端完整文档 |

---

## 🚀 快速开始指南

### Step 1: 配置 ESP32

1. 修改 `main/boards/atk-dnesp32s3/config.h`：
```c
#define ENABLE_TCP_CLIENT_MODE 1
#define TCP_SERVER_IP "你的电脑IP"
#define TCP_SERVER_PORT 8080
```

2. 编译上传：
```bash
idf.py build flash
```

### Step 2: 启动服务器

#### 方式 1: 使用快速启动脚本（推荐）
```bash
cd scripts
./start_server.sh
```

#### 方式 2: 手动启动

**简化版（快速测试）：**
```bash
python tcp_video_server_simple.py
```

**完整版（视频录制）：**
```bash
python tcp_video_server.py --save-video
```

**Web 版（浏览器访问）：**
```bash
python tcp_video_server_web.py
# 访问 http://localhost:8000
```

### Step 3: 查看视频

- **简化版/完整版**: 自动弹出 OpenCV 窗口显示视频
- **Web 版**: 在浏览器中打开 `http://localhost:8000`

---

## 🌟 三种服务器对比

| 特性 | 简化版 | 完整版 | Web 版 |
|------|--------|--------|--------|
| **代码行数** | ~80 行 | ~450 行 | ~600 行 |
| **实时显示** | ✅ OpenCV | ✅ OpenCV | ✅ 浏览器 |
| **视频录制** | ❌ | ✅ MP4 | ❌ |
| **截图保存** | ❌ | ✅ | ✅ |
| **统计信息** | 基础 | 详细 | 实时 |
| **多客户端** | ❌ | ✅ | ✅ |
| **Web 界面** | ❌ | ❌ | ✅ |
| **云端部署** | ❌ | ❌ | ✅ |
| **适用场景** | 快速测试 | 本地监控 | 远程监控 |

---

## 💡 典型使用场景

### 场景 1: 本地开发调试
```bash
# 使用简化版快速验证功能
python tcp_video_server_simple.py
```

### 场景 2: 家庭安防监控
```bash
# 使用完整版，录制视频保存
python tcp_video_server.py --save-video --save-dir ~/Videos/esp32
```

### 场景 3: 远程监控（云端部署）
```bash
# 在云服务器上运行 Web 版
python tcp_video_server_web.py --tcp-port 8080 --web-port 80

# 通过浏览器访问
# http://your-server-ip
```

### 场景 4: 多摄像头监控
```bash
# 启动多个 Web 服务实例（不同端口）
python tcp_video_server_web.py --tcp-port 8081 --web-port 8001 &
python tcp_video_server_web.py --tcp-port 8082 --web-port 8002 &
```

---

## 🔥 核心功能特性

### ESP32 客户端
- ✅ **自动连接**: WiFi 连接成功后自动启动
- ✅ **自动重连**: 断线后 3 秒自动重连
- ✅ **双线程**: 发送和接收线程分离
- ✅ **高帧率**: 约 30fps 实时传输
- ✅ **低延迟**: TCP 协议保证数据可靠性
- ✅ **可配置**: IP、端口、重连间隔等均可配置

### 服务器端（完整版）
- ✅ **实时显示**: OpenCV 窗口显示视频流
- ✅ **视频录制**: 自动保存 MP4 格式视频
- ✅ **截图功能**: 按 `s` 键保存当前帧
- ✅ **统计信息**: 帧率、带宽、连接时长等
- ✅ **多客户端**: 支持多个 ESP32 同时连接
- ✅ **信息覆盖**: 时间戳、帧号、客户端信息

### 服务器端（Web 版）
- ✅ **浏览器访问**: 无需安装客户端软件
- ✅ **响应式设计**: 支持手机、平板、电脑
- ✅ **实时状态**: 自动更新连接状态和帧率
- ✅ **在线截图**: 点击按钮下载当前帧
- ✅ **多用户**: 多人同时观看同一视频流
- ✅ **RESTful API**: 提供 JSON 格式状态接口

---

## 📊 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| **帧率** | ~30 fps | 可调整（修改延时） |
| **分辨率** | 320x240 (QVGA) | 可配置 |
| **延迟** | < 100ms | 局域网环境 |
| **带宽** | ~500 KB/s | 取决于 JPEG 质量 |
| **并发数** | 5+ | 取决于服务器性能 |

---

## 🛠️ 高级配置

### 调整帧率

**ESP32 端（降低帧率节省带宽）：**
```cpp
// tcp_client.cc 第 78 行
vTaskDelay(pdMS_TO_TICKS(66));  // 改为约 15fps
```

**ESP32 端（提高帧率）：**
```cpp
vTaskDelay(pdMS_TO_TICKS(16));  // 改为约 60fps
```

### 调整图像质量

**降低质量（节省带宽）：**
```cpp
// board_extensions.cc
config.jpeg_quality = 15;  // 更高的数值 = 更低的质量
```

**提高质量（更清晰）：**
```cpp
config.jpeg_quality = 8;  // 更低的数值 = 更高的质量
```

### 修改分辨率

```cpp
// board_extensions.cc
config.frame_size = FRAMESIZE_VGA;  // 640x480
// 其他选项: FRAMESIZE_QVGA, FRAMESIZE_CIF, FRAMESIZE_SVGA 等
```

---

## 🌐 云端部署示例

### 阿里云/腾讯云部署

```bash
# 1. 连接到服务器
ssh user@your-server-ip

# 2. 安装依赖
sudo apt update
sudo apt install python3 python3-pip
pip3 install opencv-python-headless numpy

# 3. 上传服务器文件
scp tcp_video_server_web.py user@your-server-ip:~/

# 4. 后台运行
nohup python3 tcp_video_server_web.py --tcp-port 8080 --web-port 80 > server.log 2>&1 &

# 5. 开放防火墙
sudo ufw allow 8080/tcp  # ESP32 连接端口
sudo ufw allow 80/tcp    # Web 访问端口

# 6. 访问
# http://your-server-ip
```

---

## 📖 完整文档

- **ESP32 客户端**: `main/boards/atk-dnesp32s3/streaming/README.md`
- **服务器端**: `scripts/TCP_SERVER_README.md`
- **本文档**: 快速参考和总结

---

## 🎯 常见问题解决

### Q1: ESP32 无法连接服务器

**检查清单：**
```bash
# 1. 确认服务器运行
netstat -an | grep 8080

# 2. 测试端口
telnet your-ip 8080

# 3. 检查防火墙
sudo ufw status

# 4. 查看 ESP32 日志
idf.py monitor
```

### Q2: 视频卡顿

**解决方案：**
- 降低 JPEG 质量
- 减小分辨率
- 降低帧率
- 使用有线网络
- 检查 WiFi 信号强度

### Q3: 图像花屏

**可能原因：**
- 网络数据包丢失
- JPEG 帧不完整
- 缓冲区溢出

**解决方案：**
- 使用 TCP 协议（已使用）
- 增大接收缓冲区
- 检查网络质量

---

## 📝 开发者备注

### 代码架构
```
ESP32 (Client)              Server (Python)
┌─────────────┐            ┌──────────────┐
│  Camera     │            │   Socket     │
│     ↓       │            │      ↓       │
│  JPEG       │  ───TCP──> │  Receiver    │
│  Encoder    │            │      ↓       │
│     ↓       │            │   JPEG       │
│  TCP Send   │            │   Decoder    │
└─────────────┘            │      ↓       │
                           │   Display    │
                           └──────────────┘
```

### 数据格式
- ESP32 发送：连续的 JPEG 帧（包含 SOI 和 EOI 标记）
- 服务器接收：通过查找 `0xFFD8` 和 `0xFFD9` 分割帧

### 扩展建议
- [ ] 添加 H.264 编码支持
- [ ] 实现 RTSP 协议
- [ ] 添加运动检测
- [ ] 集成人脸识别
- [ ] 云端存储集成
- [ ] 推送通知功能

---

## 🙏 致谢

- 基于 ALIENTEK ESP32-S3 lwip_demo 示例
- 使用 OpenCV 图像处理库
- ESP-IDF 框架支持

---

**作者:** DeepDiary Team  
**日期:** 2025-10-23  
**版本:** v1.0  
**许可:** MIT License

---

## 📞 技术支持

遇到问题？
1. 查看 `TCP_SERVER_README.md` 详细文档
2. 检查日志输出
3. 参考故障排查部分
4. 提交 Issue 或联系技术支持

**祝你使用愉快！🎉**

