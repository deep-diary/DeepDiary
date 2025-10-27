# MQTT 主题与消息格式总结

## 1. 设备信息主题 (device_info)

**主题格式:** `device/{client_id}/info`  
**周期:** 60秒  
**QoS:** 1  
**描述:** 设备固定配置信息（静态数据）

**JSON 格式:**
```json
{
  "device_id": "ATK-DNESP32S3-ESP32-S3-98:88:e0",
  "device_type": "ATK-DNESP32S3",
  "firmware_version": "1.0.0",
  "mac_address": "98:88:e0:00:ae:28",
  "chip_model": "ESP32-S3",
  "chip_revision": "1",
  "hardware_capabilities": {
    "camera": true,
    "can_bus": true,
    "led_strip": false,
    "gimbal": true,
    "arm": false,
    "motor": false,
    "sensor": true
  }
}
```

**实现位置:**
- 收集: `device_info_collector.cpp` → `CollectDeviceConfig()`
- 发送: `board_extensions.cc` 第551行 (每60秒)

---

## 2. 设备状态主题 (device_status)

### 2.1 通用状态 (status)

**主题格式:** `device/{client_id}/status`  
**周期:** 按需（事件驱动）  
**QoS:** 0  
**描述:** 通用设备状态消息

**JSON 格式:**
```json
{
  "type": "status",
  "status": "connected",
  "message": "Successfully connected to user MQTT broker",
  "timestamp": 8,
  "device_id": "ATK-DNESP32S3-9888e000ae28"
}
```

**实现位置:**
- 方法: `UserMqttClient::SendStatus()`
- 用途: 连接/断开、测试消息等

---

### 2.2 系统状态 (status/system)

**主题格式:** `device/{client_id}/status/system`  
**周期:** 10秒  
**QoS:** 0  
**描述:** 系统动态信息

**JSON 格式:**
```json
{
  "wifi_ssid": "Blue",
  "ip_address": "192.168.31.77",
  "free_heap": 7855072,
  "uptime_seconds": 1234,
  "cpu_temperature": 0.0,
  "network_status": "connected",
  "timestamp": 1234
}
```

**实现位置:**
- 收集: `device_info_collector.cpp` → `CollectSystemStatus()`
- 发送: `board_extensions.cc` 第560行 (每10秒)

---

### 2.3 传感器状态 (status/sensor)

**主题格式:** `device/{client_id}/status/sensor`  
**周期:** 3秒  
**QoS:** 0  
**描述:** 传感器数据

**JSON 格式:**
```json
{
  "acc_x": 0.19,
  "acc_y": 0.02,
  "acc_z": 10.80,
  "acc_g": 10.82,
  "pitch": -1.0,
  "roll": 0.1,
  "sensor_status": "connected",
  "timestamp": 1234
}
```

**实现位置:**
- 收集: `device_info_collector.cpp` → `CollectSensorStatus()`
- 发送: `board_extensions.cc` 第569行 (每3秒)

---

### 2.4 执行器状态 (status/actuator)

**主题格式:** `device/{client_id}/status/actuator`  
**周期:** 5秒  
**QoS:** 0  
**描述:** 执行器（机械臂、电机）状态

**JSON 格式:**
```json
{
  "arm": {
    "connected": false,
    "motor_count": 0,
    "status": "not_available"
  },
  "motor": {
    "connected": false,
    "motor_count": 0,
    "status": "not_available"
  },
  "timestamp": 1234
}
```

**实现位置:**
- 收集: `device_info_collector.cpp` → `CollectActuatorStatus()`
- 发送: `board_extensions.cc` 第578行 (每5秒)

---

## 3. 设备事件主题 (device_events)

**主题格式:** `device/{client_id}/events`  
**周期:** 事件驱动  
**QoS:** 1  
**描述:** 设备事件消息（连接、断开、错误等）

**JSON 格式:**
```json
{
  "event_type": "connect",
  "event_message": "Device connected and ready",
  "timestamp": 1234
}
```

**实现位置:**
- 方法: `UserMqttClient::SendDeviceEvent()`
- 调用: 连接时发送 "connect" 事件
- 可扩展: 错误、状态变化等事件

---

## 4. 控制主题 (control) - 订阅

**主题格式:** `device/{client_id}/control`  
**方向:** 订阅（接收命令）  
**QoS:** 1  
**描述:** 远程控制命令

**JSON 格式:**
```json
{
  "type": "control",
  "target": "camera",
  "action": "capture",
  "parameters": {
    "quality": 80
  }
}
```

**实现位置:**
- 订阅: `user_mqtt_client.cpp` 第124行
- 处理: `user_mqtt_client.cpp` → `ParseControlMessage()`
- 执行: `remote_control_handler.cpp` → `HandleCommand()`

---

## 发送频率总结

| 主题 | 周期 | QoS | 类型 | 数据特性 |
|------|------|-----|------|----------|
| `device/{id}/info` | 60秒 | 1 | pub | 静态配置 |
| `device/{id}/status` | 按需 | 0 | pub | 通用状态 |
| `device/{id}/status/system` | 10秒 | 0 | pub | 系统信息 |
| `device/{id}/status/sensor` | 3秒 | 0 | pub | 传感器数据 |
| `device/{id}/status/actuator` | 5秒 | 0 | pub | 执行器状态 |
| `device/{id}/events` | 事件 | 1 | pub | 设备事件 |
| `device/{id}/control` | - | 1 | sub | 远程控制 |

---

## 代码逻辑流程

### 初始化流程
1. `BoardExtensions::InitializeUserMqtt()` - 创建设备信息收集器
2. `BoardExtensions::StartUserMqtt()` - 启动MQTT客户端
3. 配置所有主题路径
4. 连接到 MQTT broker
5. 订阅控制主题

### 主循环任务 (`user_main_loop_task`)
- 周期计数器每 100ms 递增
- 根据计数器值触发不同任务:
  - `cycle_counter % 10 == 0` → 传感器更新 (1秒)
  - `cycle_counter % 30 == 0` → 发送传感器状态 (3秒)
  - `cycle_counter % 50 == 0` → 发送执行器状态 (5秒)
  - `cycle_counter % 100 == 0` → 发送系统状态 (10秒)
  - `cycle_counter % 600 == 0` → 发送设备信息 (60秒)

### 事件驱动发送
- `SendStatus()` - 连接/断开时
- `SendDeviceEvent()` - 连接/错误事件
- `SendHeartbeat()` - 每60秒心跳

---

## 所有主题已实现 ✅

根据 `mqtt_protocol.json` 配置，所有4个主题类型都已实现：

1. ✅ `device_info` - 设备固定配置 (pub)
2. ✅ `device_status` - 设备动态状态 (pub, 3个子分类)
3. ✅ `device_events` - 设备事件消息 (pub)
4. ✅ `control` - 远程控制命令 (sub)

所有主题都按照配置文件定义的格式发送，便于服务器端测试和监控。
