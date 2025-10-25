# ATK-DNESP32S3 用户MQTT通信模块

本模块实现了与用户服务器的MQTT通信功能，与开源项目的MQTT功能独立运行，主要用于设备状态反馈和远程控制指令接收。

## 功能特性

- **独立MQTT客户端**：使用独立的MQTT连接ID，避免与主项目MQTT冲突
- **设备信息上报**：自动收集并上报设备状态、硬件信息、运行状态等
- **远程控制**：接收并执行来自服务器的远程控制指令
- **心跳机制**：定期发送心跳包维持连接
- **自动重连**：网络断开时自动重连
- **配置管理**：支持NVS存储配置信息

## 文件结构

```
mqtt/
├── user_mqtt_client.h/cpp      # 主MQTT客户端类
├── user_mqtt_config.h/cpp      # 配置管理类
├── remote_control_handler.h/cpp # 远程控制指令处理器
├── device_info_collector.h/cpp  # 设备信息收集器
└── README.md                   # 本文档
```

## 核心类说明

### 1. UserMqttClient
主要的MQTT客户端类，负责：
- MQTT连接管理
- 消息发布和订阅
- 心跳发送
- 连接状态监控

### 2. UserMqttConfig
配置管理类，提供：
- 静态配置方法
- NVS存储支持
- 默认配置管理

### 3. RemoteControlHandler
远程控制指令处理器，支持：
- LED控制
- 电机控制
- 机械臂控制
- 云台控制
- 摄像头控制
- 系统控制

### 4. DeviceInfoCollector
设备信息收集器，收集：
- 设备基本信息
- 硬件状态
- 运行状态
- 组件可用性

## 使用方法

### 1. 基本初始化

```cpp
#include "user_mqtt_client.h"
#include "user_mqtt_config.h"
#include "remote_control_handler.h"
#include "device_info_collector.h"

// 创建MQTT客户端
UserMqttClient mqtt_client;

// 创建远程控制处理器
RemoteControlHandler control_handler;

// 创建设备信息收集器
DeviceInfoCollector info_collector;

// 设置设备组件引用
control_handler.SetDeepMotor(deep_motor);
control_handler.SetDeepArm(deep_arm);
control_handler.SetGimbal(gimbal);
control_handler.SetLedStrip(led_strip);
control_handler.SetCamera(camera);

info_collector.SetDeepMotor(deep_motor);
info_collector.SetDeepArm(deep_arm);
info_collector.SetGimbal(gimbal);
info_collector.SetLedStrip(led_strip);
info_collector.SetCamera(camera);
```

### 2. 配置MQTT连接

```cpp
// 方法1：使用默认配置
UserMqttConfig::LoadFromNvs();  // 从NVS加载配置

// 方法2：手动设置配置
UserMqttConfig::SetBrokerHost("your-mqtt-broker.com");
UserMqttConfig::SetBrokerPort(1883);
UserMqttConfig::SetClientId("ATK-DNESP32S3-001");
UserMqttConfig::SetUsername("your-username");
UserMqttConfig::SetPassword("your-password");
UserMqttConfig::SaveToNvs();  // 保存到NVS
```

### 3. 启动MQTT客户端

```cpp
// 创建配置对象
UserMqttClientConfig config;
config.broker_host = UserMqttConfig::GetBrokerHost();
config.broker_port = UserMqttConfig::GetBrokerPort();
config.client_id = UserMqttConfig::GetClientId();
config.username = UserMqttConfig::GetUsername();
config.password = UserMqttConfig::GetPassword();

// 初始化客户端
if (mqtt_client.Initialize(config)) {
    // 设置回调函数
    mqtt_client.SetControlCallback([&control_handler](const RemoteControlCommand& cmd) {
        control_handler.HandleCommand(cmd);
    });
    
    mqtt_client.SetConnectionCallback([](bool connected) {
        if (connected) {
            ESP_LOGI("MQTT", "Connected to user MQTT broker");
        } else {
            ESP_LOGW("MQTT", "Disconnected from user MQTT broker");
        }
    });
    
    // 连接MQTT服务器
    if (mqtt_client.Connect()) {
        ESP_LOGI("MQTT", "Successfully connected to user MQTT broker");
        
        // 发送设备信息
        DeviceInfo info = info_collector.CollectDeviceInfo();
        mqtt_client.SendDeviceInfo(info);
    }
}
```

### 4. 定期发送设备信息

```cpp
// 在主循环中定期发送设备信息
void send_device_info_periodically() {
    static uint32_t last_send_time = 0;
    uint32_t current_time = esp_timer_get_time() / 1000000; // 转换为秒
    
    if (current_time - last_send_time >= 300) { // 每5分钟发送一次
        DeviceInfo info = info_collector.CollectDeviceInfo();
        mqtt_client.SendDeviceInfo(info);
        last_send_time = current_time;
    }
}
```

## MQTT主题结构

### 发布主题
- **设备信息**：`device/{client_id}/info`
- **状态信息**：`device/{client_id}/status`
- **心跳包**：`device/{client_id}/status` (type: "heartbeat")

### 订阅主题
- **控制指令**：`device/{client_id}/control`

## 协议说明

### 1. 设备信息协议

设备信息以JSON格式发布到 `device/{client_id}/info` 主题：

```json
{
  "device_id": "ATK-DNESP32S3-ESP32S3-12345678",
  "device_type": "ATK-DNESP32S3",
  "firmware_version": "1.0.0",
  "wifi_ssid": "YourWiFi",
  "ip_address": "192.168.1.100",
  "free_heap": 245760,
  "uptime_seconds": 3600,
  "cpu_temperature": 0.0,
  "camera_available": true,
  "can_bus_available": true,
  "led_strip_available": true,
  "gimbal_available": true,
  "arm": {
    "connected": true,
    "motor_count": 6,
    "status": "connected"
  },
  "motor": {
    "connected": true,
    "motor_count": 6,
    "status": "connected"
  }
}
```

### 2. 状态信息协议

状态信息以JSON格式发布到 `device/{client_id}/status` 主题：

```json
{
  "type": "status",
  "status": "connected",
  "message": "Successfully connected to user MQTT broker",
  "timestamp": 1703123456,
  "device_id": "ATK-DNESP32S3-ESP32S3-12345678"
}
```

### 3. 心跳协议

心跳包以JSON格式发布到 `device/{client_id}/status` 主题：

```json
{
  "type": "heartbeat",
  "timestamp": 1703123456,
  "device_id": "ATK-DNESP32S3-ESP32S3-12345678"
}
```

### 4. 远程控制协议

控制指令以JSON格式发送到 `device/{client_id}/control` 主题：

#### LED控制
```json
{
  "type": "led",
  "target": "strip",
  "action": "on"
}
```

```json
{
  "type": "led",
  "target": "strip", 
  "action": "color",
  "parameters": {
    "r": 255,
    "g": 0,
    "b": 0
  }
}
```

#### 电机控制
```json
{
  "type": "motor",
  "target": "motor_1",
  "action": "start",
  "parameters": {
    "motor_id": 1
  }
}
```

```json
{
  "type": "motor",
  "target": "motor_1",
  "action": "set_speed",
  "parameters": {
    "motor_id": 1,
    "speed": 100
  }
}
```

#### 机械臂控制
```json
{
  "type": "arm",
  "target": "arm",
  "action": "home"
}
```

```json
{
  "type": "arm",
  "target": "arm",
  "action": "move",
  "parameters": {
    "x": 100.0,
    "y": 200.0,
    "z": 50.0
  }
}
```

#### 云台控制
```json
{
  "type": "gimbal",
  "target": "gimbal",
  "action": "pan",
  "parameters": {
    "angle": 45.0
  }
}
```

#### 摄像头控制
```json
{
  "type": "camera",
  "target": "camera",
  "action": "capture"
}
```

#### 系统控制
```json
{
  "type": "system",
  "target": "system",
  "action": "restart"
}
```

```json
{
  "type": "system",
  "target": "system",
  "action": "status"
}
```

## 支持的远程控制命令

### LED控制
- `on` - 开启LED
- `off` - 关闭LED
- `color` - 设置颜色 (参数: r, g, b)
- `brightness` - 设置亮度 (参数: brightness)
- `effect` - 设置效果 (参数: effect_type)

### 电机控制
- `start` - 启动电机 (参数: motor_id)
- `stop` - 停止电机 (参数: motor_id)
- `set_speed` - 设置速度 (参数: motor_id, speed)
- `set_position` - 设置位置 (参数: motor_id, position)

### 机械臂控制
- `home` - 回零位
- `move` - 移动到指定位置 (参数: x, y, z)
- `grip` - 抓取
- `release` - 释放

### 云台控制
- `pan` - 水平旋转 (参数: angle)
- `tilt` - 垂直旋转 (参数: angle)
- `reset` - 复位

### 摄像头控制
- `capture` - 拍照
- `start_stream` - 开始流媒体
- `stop_stream` - 停止流媒体

### 系统控制
- `restart` - 重启系统
- `status` - 获取状态
- `info` - 获取设备信息

## 配置参数

### 默认配置
- **Broker地址**: `34.172.161.212`
- **端口**: `1883`
- **Keepalive**: `60秒`
- **SSL**: `关闭`

### 配置存储
配置信息存储在NVS的 `user_mqtt` 命名空间中：
- `broker_host` - MQTT服务器地址
- `broker_port` - MQTT服务器端口
- `client_id` - 客户端ID
- `username` - 用户名
- `password` - 密码
- `keepalive_interval` - 心跳间隔
- `use_ssl` - 是否使用SSL

## 错误处理

### 连接错误
- 网络不可用时自动重连
- 最大重试次数：5次
- 重连间隔：30秒

### 消息错误
- JSON解析失败时记录错误日志
- 未知命令类型时返回错误状态
- 设备组件不可用时返回错误信息

## 注意事项

1. **连接ID冲突**：使用连接ID 1，避免与主项目MQTT连接冲突
2. **内存管理**：注意cJSON对象的生命周期管理
3. **线程安全**：MQTT回调在独立线程中执行，注意线程安全
4. **资源清理**：程序退出时正确清理MQTT连接和定时器
5. **配置持久化**：重要配置建议保存到NVS

## 集成到主项目

要将此MQTT模块集成到主项目中，需要在 `BoardExtensions` 类中添加相应的初始化和启动代码。具体集成步骤请参考项目集成文档。

## 调试和日志

启用相关日志标签：
- `UserMQTT` - MQTT客户端日志
- `UserMqttConfig` - 配置管理日志
- `RemoteControl` - 远程控制日志
- `DeviceInfo` - 设备信息日志

## 版本历史

- **v1.0.0** - 初始版本，支持基本的MQTT通信和远程控制功能
