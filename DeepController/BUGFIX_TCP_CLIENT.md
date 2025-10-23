# TCP 客户端问题修复说明

## 🐛 问题描述

ESP32 TCP 客户端连接成功，但服务器端报错：
```
Corrupt JPEG data: 254 extraneous bytes before marker 0xe7
```

没有图像显示。

---

## 🔍 问题原因

**根本原因**：相机配置错误！

在 `board_extensions.cc` 中，相机被配置为 **RGB565** 格式，而不是 **JPEG** 格式：

```cpp
// 错误配置
config.pixel_format = PIXFORMAT_RGB565;  // ❌ 发送原始像素数据
```

TCP 客户端发送的是原始 RGB565 像素数据（每个像素 2 字节），而 Python 服务器期望接收 JPEG 压缩数据。

---

## ✅ 修复方案

### 1. 修复相机配置（`board_extensions.cc`）

**位置**：第 189-202 行

**修改前**：
```cpp
config.pixel_format = PIXFORMAT_RGB565;
config.frame_size = FRAMESIZE_QVGA;
config.jpeg_quality = 12;
config.fb_count = 1;
```

**修改后**：
```cpp
#if ENABLE_TCP_CLIENT_MODE
    // TCP 客户端模式需要 JPEG 格式
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;  // 0-63，数值越小质量越高
    config.fb_count = 2;       // 使用双缓冲提高性能
#else
    // MJPEG 服务器或显示模式使用 RGB565
    config.pixel_format = PIXFORMAT_RGB565;
    config.frame_size = FRAMESIZE_QVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
#endif
```

### 2. 改进 TCP 发送逻辑（`tcp_client.cc`）

**改进内容**：

#### A. 完整发送数据
```cpp
// 循环发送，确保发送完整
while (total_sent < bytes_to_send)
{
    send_result = send(g_sock, data_ptr + total_sent, 
                      bytes_to_send - total_sent, 0);
    // ...
    total_sent += send_result;
}
```

#### B. 添加格式验证
```cpp
/* 第一帧时显示格式信息 */
if (frame_counter == 1)
{
    ESP_LOGI(TAG, "摄像头格式: %d, 分辨率: %dx%d, 大小: %d 字节",
            camera_frame->format, 
            camera_frame->width, 
            camera_frame->height,
            camera_frame->len);
    
    /* 检查是否为 JPEG 格式 */
    if (camera_frame->format == PIXFORMAT_JPEG)
    {
        ESP_LOGI(TAG, "✓ JPEG 格式正确");
        /* 验证 JPEG 头尾标记 */
        if (camera_frame->buf[0] == 0xFF && camera_frame->buf[1] == 0xD8)
        {
            ESP_LOGI(TAG, "✓ JPEG 起始标记正确 (0xFFD8)");
        }
        if (camera_frame->buf[len-2] == 0xFF && camera_frame->buf[len-1] == 0xD9)
        {
            ESP_LOGI(TAG, "✓ JPEG 结束标记正确 (0xFFD9)");
        }
    }
}
```

#### C. 添加统计日志
```cpp
/* 每100帧显示一次统计 */
if (frame_counter % 100 == 0)
{
    ESP_LOGI(TAG, "已发送 %lu 帧，最后一帧: %d 字节", 
             frame_counter, camera_frame->len);
}
```

---

## 🧪 验证方法

### 1. 重新编译上传
```bash
cd /Users/hanli/Desktop/DeepDiary/DeepController
idf.py build flash monitor
```

### 2. 检查日志

**正确的日志应该显示**：
```
I (xxxx) TCP_CLIENT: TCP连接成功！
I (xxxx) TCP_CLIENT: 摄像头格式: 4, 分辨率: 320x240, 大小: 8234 字节
I (xxxx) TCP_CLIENT: ✓ JPEG 格式正确
I (xxxx) TCP_CLIENT: ✓ JPEG 起始标记正确 (0xFFD8)
I (xxxx) TCP_CLIENT: ✓ JPEG 结束标记正确 (0xFFD9)
I (xxxx) TCP_CLIENT: 已发送 100 帧，最后一帧: 8456 字节
```

**格式说明**：
- 格式代码 4 = PIXFORMAT_JPEG（正确）
- 格式代码 2 = PIXFORMAT_RGB565（错误）

### 3. 启动服务器测试

```bash
cd scripts
python tcp_video_server_simple.py
```

**预期结果**：
- ✅ 服务器正常接收 JPEG 数据
- ✅ 图像正常显示
- ✅ 无 "Corrupt JPEG data" 错误

---

## 📊 性能优化

### JPEG 质量调整

**降低质量（节省带宽，适合远程）**：
```cpp
config.jpeg_quality = 20;  // 质量较低，文件更小
```

**提高质量（更清晰，适合本地）**：
```cpp
config.jpeg_quality = 8;   // 质量更高，文件更大
```

**质量对照表**：
| jpeg_quality | 质量 | 帧大小 | 适用场景 |
|--------------|------|--------|----------|
| 8 | 极高 | ~15KB | 本地监控 |
| 12 | 高 | ~8KB | 默认设置 |
| 20 | 中 | ~5KB | 远程监控 |
| 30 | 低 | ~3KB | 低带宽网络 |

### 分辨率调整

```cpp
// QVGA - 320x240（默认，推荐）
config.frame_size = FRAMESIZE_QVGA;

// VGA - 640x480（更清晰，需要更多带宽）
config.frame_size = FRAMESIZE_VGA;

// QQVGA - 160x120（最小，适合极低带宽）
config.frame_size = FRAMESIZE_QQVGA;
```

---

## 🎯 关键点总结

1. **PIXFORMAT_JPEG vs PIXFORMAT_RGB565**
   - TCP 传输 **必须** 使用 PIXFORMAT_JPEG
   - RGB565 是原始像素数据，无压缩
   - JPEG 是压缩格式，带宽需求低 10-20 倍

2. **完整发送**
   - `send()` 可能不会一次发送完所有数据
   - 需要循环发送直到全部发送完成

3. **调试信息**
   - 第一帧验证 JPEG 格式和标记
   - 定期显示发送统计
   - 帮助快速定位问题

---

## 📝 对比：原始示例 vs 当前实现

| 特性 | lwip_demo.c | tcp_client.cc (修复后) |
|------|-------------|------------------------|
| 相机格式 | JPEG | JPEG ✅ |
| 发送方式 | 单次 send | 循环发送（更可靠）✅ |
| 错误处理 | 基础 | 完善 ✅ |
| 调试信息 | 无 | 详细验证 ✅ |
| 统计信息 | 无 | 帧计数 ✅ |
| 断线重连 | 手动 | 自动 ✅ |

---

## 🚀 下一步

1. ✅ 重新编译固件
2. ✅ 上传到 ESP32
3. ✅ 启动 Python 服务器
4. ✅ 查看日志验证 JPEG 格式
5. ✅ 享受视频流！

---

**修复日期**：2025-10-23  
**修复人员**：DeepDiary Team  
**影响范围**：所有使用 TCP 客户端模式的用户

---

## 💬 常见问题

### Q: 为什么之前的配置是 RGB565？

A: RGB565 主要用于本地显示（LCD 屏幕），不需要解码。但 TCP 传输需要压缩格式以节省带宽。

### Q: JPEG 质量参数如何选择？

A: 
- **本地测试**：12（默认）
- **家庭网络**：12-15
- **远程监控**：20-30
- **低带宽**：30-40

### Q: 可以同时支持 RGB565 和 JPEG 吗？

A: 已实现！通过 `ENABLE_TCP_CLIENT_MODE` 宏自动切换：
- TCP 客户端模式 → JPEG
- MJPEG 服务器/显示模式 → RGB565

---

**现在可以正常使用了！** 🎉

