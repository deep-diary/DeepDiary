# DeepWeb - Web 页面说明

## Thumbler 不倒翁页

### 1. 页面概述

Thumbler 不倒翁页是一个用于监控和控制不倒翁设备的 Web 页面，提供实时视频流显示、设备状态监控和远程控制功能。

**配置参数：**

- `DEVICE_ID`: 设备唯一标识符（例如：`ATK-DNESP32S3-9888e000ae28`）
- `HOST`: 流媒体服务器地址（默认：`34.172.161.212`）

**页面主要功能模块：**

1. **摄像头显示** - 实时视频流播放
2. **MQTT 接收** - 设备状态数据实时显示
3. **MQTT 发送** - 设备控制命令发送

---

### 2. 摄像头显示模块

#### 2.1 功能说明

- 从流媒体服务器拉取实时视频流
- 支持 RTSP 和 HTTP 两种协议
- 优先使用 HTTP 协议，便于在网页中嵌入播放

#### 2.2 流地址格式

- **RTSP 地址**: `rtsp://{HOST}:8554/{DEVICE_ID}`
- **HTTP 地址**: `http://{HOST}:8888/{DEVICE_ID}`
- **Web 播放地址（推荐）**: `https://www.deep-diary.com/mediamtx/{DEVICE_ID}`

#### 2.3 实现要求

- 参考 `rtsp_page.py` 的实现方式
- 使用浏览器 iframe 嵌入 MediaMTX 播放器（支持音视频同步）
- 可选：提供 OpenCV 帧提取功能（用于 AI 图像处理）
- 支持流地址动态更新
- 显示连接状态和流信息

---

### 3. MQTT 接收模块

#### 3.1 订阅主题

```
Thumbler/{DEVICE_ID}/status
```

#### 3.2 消息字段说明

| 字段名                   | 类型    | 说明                          | 单位/取值范围                                                         |
| ------------------------ | ------- | ----------------------------- | --------------------------------------------------------------------- |
| `cur_cam_switch`         | boolean | 摄像头开关状态                | true/false                                                            |
| `g_acc_x`                | float   | X 轴加速度                    | m/s²                                                                  |
| `g_acc_y`                | float   | Y 轴加速度                    | m/s²                                                                  |
| `g_acc_z`                | float   | Z 轴加速度                    | m/s²                                                                  |
| `g_acc_g`                | float   | 总加速度                      | m/s²                                                                  |
| `g_pitch`                | float   | 俯仰角                        | 度 (°)                                                                |
| `g_roll`                 | float   | 翻滚角                        | 度 (°)                                                                |
| `cur_led_mode`           | integer | 当前 LED 工作模式             | 0: 关闭, 1: 静态颜色, 2: 闪烁, 3: 呼吸灯, 4: 流水灯/滚动, 5: 系统状态 |
| `cur_led_brightness`     | integer | 当前 LED 默认亮度             | 0-255                                                                 |
| `cur_led_low_brightness` | integer | 当前 LED 低亮度               | 0-255                                                                 |
| `cur_led_color_red`      | integer | 当前 LED 颜色 - 红色分量      | 0-255                                                                 |
| `cur_led_color_green`    | integer | 当前 LED 颜色 - 绿色分量      | 0-255                                                                 |
| `cur_led_color_blue`     | integer | 当前 LED 颜色 - 蓝色分量      | 0-255                                                                 |
| `cur_led_interval_ms`    | integer | 当前 LED 动画间隔时间         | 毫秒                                                                  |
| `cur_led_scroll_length`  | integer | 当前 LED 滚动模式下的亮灯数量 | 1-最大 LED 数量                                                       |
| `cur_tumbler_mode`       | integer | 不倒翁工作模式                | 0: 静止, 1: 左右循环晃动, 2: 来回旋转, 3: 充电中                      |
| `is_has_people`          | boolean | 当前环境是否有人              | true/false                                                            |
| `power_percent`          | integer | 当前系统电量                  | 0-100 (%)                                                             |
| `timestamp`              | integer | 时间戳                        | Unix 时间戳（秒）                                                     |

#### 3.3 消息 JSON 格式示例

```json
{
  "cur_cam_switch": true,
  "g_acc_x": 0.12,
  "g_acc_y": -0.05,
  "g_acc_z": 9.81,
  "g_acc_g": 9.82,
  "g_pitch": 2.5,
  "g_roll": -1.2,
  "cur_led_mode": 2,
  "cur_led_brightness": 128,
  "cur_led_low_brightness": 16,
  "cur_led_color_red": 0,
  "cur_led_color_green": 255,
  "cur_led_color_blue": 0,
  "cur_led_interval_ms": 500,
  "cur_led_scroll_length": 3,
  "cur_tumbler_mode": 1,
  "is_has_people": true,
  "power_percent": 85,
  "timestamp": 1704067200
}
```

#### 3.4 UI 显示要求

- 实时显示所有状态字段
- 使用仪表盘或进度条显示电量
- 使用图表显示加速度和角度数据（可选）
- 显示 LED 模式和工作模式的文字描述
- 使用颜色标识设备状态（如：有人/无人、充电中等）
- 参考 `mqtt_page.py` 的消息队列和定时刷新机制

---

### 4. MQTT 发送模块

#### 4.1 发布主题

```
Thumbler/{DEVICE_ID}/cmd
```

#### 4.2 控制字段说明

**基础控制字段：**

| 字段名             | 类型    | 说明               | 单位/取值范围                                    |
| ------------------ | ------- | ------------------ | ------------------------------------------------ |
| `tar_cam_switch`   | boolean | 摄像头开关控制指令 | true: 开启, false: 关闭                          |
| `tar_pitch`        | float   | 目标俯仰角         | 度 (°)，范围待定                                 |
| `tar_roll`         | float   | 目标翻滚角         | 度 (°)，范围待定                                 |
| `tar_tumbler_mode` | integer | 目标不倒翁工作模式 | 0: 静止, 1: 左右循环晃动, 2: 来回旋转, 3: 充电中 |

**LED 控制字段：**

| 字段名                    | 类型    | 说明                               | 单位/取值范围                                                         |
| ------------------------- | ------- | ---------------------------------- | --------------------------------------------------------------------- |
| `tar_led_mode`            | integer | 目标 LED 工作模式                  | 0: 关闭, 1: 静态颜色, 2: 闪烁, 3: 呼吸灯, 4: 流水灯/滚动, 5: 系统状态 |
| `tar_led_brightness`      | integer | 目标 LED 默认亮度                  | 0-255                                                                 |
| `tar_led_low_brightness`  | integer | 目标 LED 低亮度（用于系统状态）    | 0-255                                                                 |
| `tar_led_color_red`       | integer | LED 颜色 - 红色分量                | 0-255                                                                 |
| `tar_led_color_green`     | integer | LED 颜色 - 绿色分量                | 0-255                                                                 |
| `tar_led_color_blue`      | integer | LED 颜色 - 蓝色分量                | 0-255                                                                 |
| `tar_led_color_low_red`   | integer | LED 低颜色 - 红色分量（呼吸/滚动） | 0-255                                                                 |
| `tar_led_color_low_green` | integer | LED 低颜色 - 绿色分量（呼吸/滚动） | 0-255                                                                 |
| `tar_led_color_low_blue`  | integer | LED 低颜色 - 蓝色分量（呼吸/滚动） | 0-255                                                                 |
| `tar_led_interval_ms`     | integer | LED 动画间隔时间（毫秒）           | > 0，建议范围：50-1000                                                |
| `tar_led_scroll_length`   | integer | LED 滚动模式下的亮灯数量           | 1-最大 LED 数量，仅用于滚动模式                                       |

#### 4.3 消息 JSON 格式示例

**基础控制示例：**

```json
{
  "tar_cam_switch": true,
  "tar_pitch": 10.0,
  "tar_roll": -5.0,
  "tar_tumbler_mode": 1,
  "timestamp": 1704067200
}
```

**LED 静态颜色示例（模式 1）：**

```json
{
  "tar_led_mode": 1,
  "tar_led_brightness": 128,
  "tar_led_color_red": 255,
  "tar_led_color_green": 0,
  "tar_led_color_blue": 0,
  "timestamp": 1704067200
}
```

**LED 闪烁示例（模式 2）：**

```json
{
  "tar_led_mode": 2,
  "tar_led_brightness": 128,
  "tar_led_color_red": 0,
  "tar_led_color_green": 255,
  "tar_led_color_blue": 0,
  "tar_led_interval_ms": 500,
  "timestamp": 1704067200
}
```

**LED 呼吸灯示例（模式 3）：**

```json
{
  "tar_led_mode": 3,
  "tar_led_brightness": 128,
  "tar_led_color_low_red": 0,
  "tar_led_color_low_green": 0,
  "tar_led_color_low_blue": 0,
  "tar_led_color_red": 0,
  "tar_led_color_green": 255,
  "tar_led_color_blue": 0,
  "tar_led_interval_ms": 50,
  "timestamp": 1704067200
}
```

**LED 流水灯/滚动示例（模式 4）：**

```json
{
  "tar_led_mode": 4,
  "tar_led_brightness": 128,
  "tar_led_color_low_red": 0,
  "tar_led_color_low_green": 0,
  "tar_led_color_low_blue": 0,
  "tar_led_color_red": 0,
  "tar_led_color_green": 0,
  "tar_led_color_blue": 255,
  "tar_led_scroll_length": 3,
  "tar_led_interval_ms": 100,
  "timestamp": 1704067200
}
```

**完整控制示例（包含所有参数）：**

```json
{
  "tar_cam_switch": true,
  "tar_pitch": 10.0,
  "tar_roll": -5.0,
  "tar_led_mode": 2,
  "tar_led_brightness": 128,
  "tar_led_low_brightness": 16,
  "tar_led_color_red": 255,
  "tar_led_color_green": 128,
  "tar_led_color_blue": 0,
  "tar_led_color_low_red": 0,
  "tar_led_color_low_green": 0,
  "tar_led_color_low_blue": 0,
  "tar_led_interval_ms": 500,
  "tar_led_scroll_length": 3,
  "tar_tumbler_mode": 1,
  "timestamp": 1704067200
}
```

#### 4.4 UI 控制界面要求

**基础控制：**

- 提供摄像头开关切换按钮
- 提供俯仰角和翻滚角的滑块或输入框
- 提供不倒翁工作模式选择按钮组

**LED 控制：**

- 提供 LED 模式选择下拉菜单（0:关闭, 1:静态, 2:闪烁, 3:呼吸, 4:流水, 5:系统状态）
- 提供 LED 默认亮度滑块（0-255）
- 提供 LED 低亮度滑块（0-255，用于系统状态）
- 提供颜色选择器（RGB）用于主颜色
- 提供颜色选择器（RGB）用于低颜色（呼吸灯和流水灯模式）
- 提供动画间隔时间输入框（毫秒，建议 50-1000）
- 提供滚动长度输入框（仅流水灯模式，1-最大 LED 数量）
- 根据选择的 LED 模式动态显示/隐藏相关参数：
  - 模式 0（关闭）：无需额外参数
  - 模式 1（静态）：需要主颜色和亮度
  - 模式 2（闪烁）：需要主颜色、亮度和间隔时间
  - 模式 3（呼吸）：需要低颜色、主颜色、亮度和间隔时间
  - 模式 4（流水）：需要低颜色、主颜色、亮度、间隔时间和滚动长度
  - 模式 5（系统状态）：使用系统默认状态，无需参数

**通用要求：**

- 显示发送状态和结果反馈
- 支持批量发送多个控制参数
- 提供参数验证（范围检查）

---

### 5. 技术实现要点

#### 5.1 页面类结构

参考 `rtsp_page.py` 和 `mqtt_page.py` 的实现方式，建议创建 `ThumblerPage` 类：

```python
class ThumblerPage:
    def __init__(self, device_id: str, host: str, mqtt_manager, log_manager):
        # 初始化参数
        # 初始化视频流管理器
        # 初始化 MQTT 消息队列

    def build(self):
        # 构建 Gradio UI 组件
        # 返回页面组件
```

#### 5.2 MQTT 消息处理

- 使用消息队列（`Queue`）缓存接收到的消息
- 使用 `gr.Timer` 定时刷新 UI（建议 1 秒间隔）
- 实现 `push_mqtt_message()` 方法供外部调用
- 实现 `_drain_mqtt_messages()` 方法处理队列消息

#### 5.3 视频流处理

- 使用 `RtspPage` 类或类似实现
- 支持流地址动态配置
- 显示连接状态和错误提示

#### 5.4 错误处理

- 网络连接失败时的重试机制
- MQTT 消息格式验证
- 视频流断线重连
- 用户友好的错误提示

---

### 6. UI 布局建议

```
┌─────────────────────────────────────────────────────────┐
│  Thumbler 不倒翁控制页面                                 │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────┐  ┌─────────────────────────┐ │
│  │                      │  │  设备状态监控            │ │
│  │   视频流显示区域      │  │  - 电量: [████░░] 85%   │ │
│  │  (iframe 播放器)      │  │  - 摄像头: ✅ 开启      │ │
│  │                      │  │  - 人员检测: 👤 有人    │ │
│  │                      │  │  - 工作模式: 左右晃动    │ │
│  └──────────────────────┘  │                         │ │
│                            │  传感器数据              │ │
│  ┌──────────────────────┐  │  - X轴加速度: 0.12 m/s² │ │
│  │   控制面板            │  │  - Y轴加速度: -0.05     │ │
│  │  - 摄像头开关         │  │  - Z轴加速度: 9.81      │ │
│  │  - 俯仰角控制         │  │  - 俯仰角: 2.5°         │ │
│  │  - 翻滚角控制         │  │  - 翻滚角: -1.2°        │ │
│  │  - LED 模式           │  │                         │ │
│  │  - LED 亮度           │  │  LED 状态               │ │
│  │  - 工作模式           │  │  - 模式: 流水灯         │ │
│  │  - [发送控制命令]     │  │  - 亮度: 80%            │ │
│  └──────────────────────┘  └─────────────────────────┘ │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

### 7. 开发参考

- **视频流实现**: 参考 `DeepWeb/deepweb/ui/pages/rtsp_page.py`
- **MQTT 通信实现**: 参考 `DeepWeb/deepweb/ui/pages/mqtt_page.py`
- **MQTT 配置**: 参考 `DeepWeb/deepweb/services/device_communication/mqtt_config.py`
- **日志管理**: 使用 `log_manager` 进行日志记录

---

### 8. 待确认事项

- [ ] 俯仰角和翻滚角的具体取值范围
- [ ] LED 模式的具体枚举值定义
- [ ] 不倒翁工作模式的详细说明
- [ ] MQTT 消息的 QoS 级别
- [ ] 消息发送频率限制
- [ ] 视频流的编码格式和分辨率
