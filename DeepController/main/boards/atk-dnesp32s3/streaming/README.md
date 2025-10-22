# 流媒体模块 (Streaming Module)

## 功能概述

本模块提供了摄像头视频流的推送和服务功能，包括：
- **MJPEG服务器**: HTTP方式提供Motion JPEG视频流
- **HTTP流**: 基础的HTTP流媒体支持
- **RTSP支持**: 通过MediaMTX实现RTSP流媒体（文档）

## 文件说明

### 核心文件

- **mjpeg_server.cc/h**: MJPEG HTTP服务器
  - 内置HTTP服务器
  - Motion JPEG格式推送
  - 可通过浏览器、VLC直接访问
  
- **http_stream.cc/h**: HTTP流媒体基础支持
  - HTTP分块传输
  - 流式数据推送

### 配置和脚本

- **setup_mediamtx.sh**: MediaMTX服务器安装配置脚本
- **test_rtsp.sh**: RTSP流测试脚本
- **mediamtx-config.yml**: MediaMTX配置文件

### 文档

- **README_RTSP.md**: RTSP功能总体介绍
- **RTSP_USAGE.md**: RTSP使用说明
- **RTSP_PUSH_GUIDE.md**: RTSP推流指南
- **PUSH_MODE_SUMMARY.md**: 推流模式总结
- **IMPLEMENTATION_SUMMARY.md**: 实现总结和架构说明

## MJPEG服务器

### 功能特性
- 独立HTTP服务器，无需外部程序
- 支持多客户端同时访问
- 可配置帧率和JPEG质量
- 兼容VLC、浏览器、ffmpeg等播放器

### 快速开始

#### 1. 初始化服务器
```cpp
#include "mjpeg_server.h"

// 创建MJPEG服务器（端口8080）
auto mjpeg_server = std::make_unique<MjpegServer>(8080);

// 配置参数
mjpeg_server->SetFrameRate(10);    // 10fps
mjpeg_server->SetJpegQuality(80);  // JPEG质量80

// 启动服务器
if (mjpeg_server->Start()) {
    ESP_LOGI(TAG, "MJPEG服务器启动成功");
    ESP_LOGI(TAG, "访问地址: %s", mjpeg_server->GetUrl().c_str());
}
```

#### 2. 访问视频流

**浏览器访问**:
```
http://<ESP32_IP>:8080/stream
```

**VLC播放器**:
1. 打开网络流
2. 输入地址：`http://<ESP32_IP>:8080/stream`
3. 点击播放

**ffmpeg命令**:
```bash
ffplay http://<ESP32_IP>:8080/stream
```

#### 3. 停止服务器
```cpp
if (mjpeg_server->IsRunning()) {
    mjpeg_server->Stop();
}
```

### API参考

#### MjpegServer类

```cpp
class MjpegServer {
public:
    // 构造函数（指定端口）
    MjpegServer(uint16_t port = 8080);
    
    // 启动服务器
    bool Start();
    
    // 停止服务器
    void Stop();
    
    // 检查运行状态
    bool IsRunning() const;
    
    // 设置帧率（fps）
    void SetFrameRate(uint8_t fps);
    
    // 设置JPEG质量（0-100）
    void SetJpegQuality(uint8_t quality);
    
    // 获取访问URL
    std::string GetUrl() const;
};
```

### 配置参数

```cpp
// 推荐配置
mjpeg_server->SetFrameRate(10);    // 10fps，平衡流畅度和带宽
mjpeg_server->SetJpegQuality(80);  // 质量80，兼顾画质和文件大小

// 低带宽配置
mjpeg_server->SetFrameRate(5);     // 5fps
mjpeg_server->SetJpegQuality(60);  // 质量60

// 高质量配置
mjpeg_server->SetFrameRate(15);    // 15fps
mjpeg_server->SetJpegQuality(90);  // 质量90
```

## 使用示例

### 完整的初始化流程
```cpp
// 在板级初始化中
void InitializeMjpegServer() {
    if (camera_ == nullptr) {
        ESP_LOGI(TAG, "相机未初始化，跳过MJPEG服务器");
        return;
    }
    
    // 创建服务器
    mjpeg_server_ = std::make_unique<MjpegServer>(8080);
    mjpeg_server_->SetFrameRate(10);
    mjpeg_server_->SetJpegQuality(80);
    
    ESP_LOGI(TAG, "MJPEG服务器对象创建完成");
    ESP_LOGI(TAG, "等待WiFi连接后自动启动...");
}

// WiFi连接后启动
void StartMjpegServerWhenReady() {
    if (mjpeg_server_ == nullptr || mjpeg_server_->IsRunning()) {
        return;
    }
    
    ESP_LOGI(TAG, "WiFi已连接，启动MJPEG服务器...");
    vTaskDelay(pdMS_TO_TICKS(2000));  // 等待网络就绪
    
    if (mjpeg_server_->Start()) {
        ESP_LOGI(TAG, "访问地址: %s", mjpeg_server_->GetUrl().c_str());
    }
}
```

### 动态调整参数
```cpp
// 根据网络状况动态调整
void AdjustStreamQuality(NetworkQuality quality) {
    if (quality == NETWORK_GOOD) {
        mjpeg_server_->SetFrameRate(15);
        mjpeg_server_->SetJpegQuality(90);
    } else if (quality == NETWORK_POOR) {
        mjpeg_server_->SetFrameRate(5);
        mjpeg_server_->SetJpegQuality(60);
    }
}
```

## RTSP功能（通过MediaMTX）

虽然ESP32本身不提供RTSP服务器，但可以通过以下方式实现RTSP功能：

### 架构方案
```
ESP32 (MJPEG) → MediaMTX (转换) → RTSP客户端
```

### 快速部署

#### 1. 安装MediaMTX
```bash
cd streaming/
chmod +x setup_mediamtx.sh
./setup_mediamtx.sh
```

#### 2. 配置MediaMTX
编辑 `mediamtx-config.yml`，设置ESP32的MJPEG地址：
```yaml
paths:
  esp32cam:
    source: http://<ESP32_IP>:8080/stream
```

#### 3. 启动MediaMTX
```bash
./mediamtx
```

#### 4. 访问RTSP流
```bash
# VLC播放
vlc rtsp://localhost:8554/esp32cam

# ffplay播放
ffplay rtsp://localhost:8554/esp32cam
```

### 测试脚本
```bash
# 测试RTSP流
cd streaming/
chmod +x test_rtsp.sh
./test_rtsp.sh
```

## 性能优化

### 1. 帧率优化
```cpp
// 根据实际需求选择合适帧率
// 监控应用: 5-10fps
// 实时交互: 10-15fps
// 流畅视频: 15-25fps
mjpeg_server->SetFrameRate(10);
```

### 2. 带宽优化
```cpp
// 降低JPEG质量可显著减少带宽
// 质量60: ~20KB/帧 (QVGA)
// 质量80: ~30KB/帧 (QVGA)
// 质量90: ~40KB/帧 (QVGA)
mjpeg_server->SetJpegQuality(70);
```

### 3. 分辨率优化
```cpp
// 在相机初始化时设置合适分辨率
config.frame_size = FRAMESIZE_QVGA;  // 320x240，推荐
// config.frame_size = FRAMESIZE_VGA; // 640x480，需要更多带宽
```

### 4. 多客户端优化
- 限制最大并发连接数
- 使用帧缓存共享
- 避免重复编码

## 网络要求

### 带宽估算
```
带宽 = 帧率 × 平均帧大小

示例(QVGA, 质量80):
10fps × 30KB = 300KB/s = 2.4Mbps
```

### 推荐配置
- **局域网**: 10fps, 质量80-90
- **WiFi**: 8fps, 质量70-80
- **移动网络**: 5fps, 质量60-70

## 故障排查

### 常见问题

**1. 无法访问视频流**
- 检查ESP32 IP地址
- 确认防火墙设置
- 验证端口8080是否开放
- 检查WiFi连接状态

**2. 视频卡顿**
- 降低帧率
- 降低JPEG质量
- 减小分辨率
- 检查网络带宽

**3. 延迟较大**
- 降低帧率可能反而增加延迟
- 检查网络丢包率
- 优化WiFi信号强度
- 减少客户端数量

**4. 服务器启动失败**
- 检查端口是否被占用
- 确认WiFi已连接
- 查看ESP32日志

### 调试方法

```cpp
// 启用详细日志
esp_log_level_set("mjpeg_server", ESP_LOG_DEBUG);

// 检查服务器状态
ESP_LOGI(TAG, "服务器运行: %s", 
         mjpeg_server->IsRunning() ? "是" : "否");
ESP_LOGI(TAG, "访问URL: %s", mjpeg_server->GetUrl().c_str());
```

## 依赖关系

- **Camera模块**: 获取摄像头帧数据（`esp32_camera`）
- **WiFi模块**: 网络连接
- **HTTP服务器**: ESP-IDF HTTP服务器组件
- **JPEG编码器**: 摄像头内置或软件编码

## 安全建议

1. **访问控制**:
   - 添加HTTP认证（计划中）
   - 使用HTTPS加密（计划中）
   - 限制IP白名单

2. **资源限制**:
   - 限制最大客户端数
   - 设置连接超时
   - 监控CPU和内存使用

3. **网络隔离**:
   - 仅在可信网络使用
   - 不要暴露在公网
   - 使用VPN访问

## 扩展功能

### 计划中的功能
- [ ] HTTP认证
- [ ] HTTPS支持
- [ ] H.264编码（硬件加速）
- [ ] 录像功能
- [ ] 快照接口
- [ ] 双向音频
- [ ] 移动侦测
- [ ] 云端推流

### 可集成的功能
- 人脸识别
- 物体检测
- 二维码识别
- OCR文字识别
- 图像增强

## 相关文档

详细信息请参考：
- `README_RTSP.md` - RTSP功能介绍
- `RTSP_USAGE.md` - RTSP使用详解
- `RTSP_PUSH_GUIDE.md` - 推流配置指南
- `IMPLEMENTATION_SUMMARY.md` - 技术实现细节

## 技术规格

### MJPEG格式
- **编码**: Motion JPEG
- **容器**: HTTP分块传输
- **边界**: multipart/x-mixed-replace
- **兼容性**: 所有主流浏览器和播放器

### HTTP服务器
- **协议**: HTTP/1.1
- **方法**: GET
- **端点**: /stream
- **并发**: 支持多客户端

### 性能指标
- **延迟**: < 200ms (局域网)
- **帧率**: 最高25fps (实际取决于网络)
- **分辨率**: 最高VGA (640x480)
- **编码时间**: < 50ms/帧 (QVGA)

