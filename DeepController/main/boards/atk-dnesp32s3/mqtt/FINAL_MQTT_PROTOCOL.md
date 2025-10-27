# 最终 MQTT 协议实现总结

## 主题架构（已简化）

```
device/{client_id}/
├── info                 ← 设备信息（静态配置，60秒）
├── status               ← 通用状态（事件驱动）
├── status/system        ← 系统状态（周期性，10秒）
├── status/sensor        ← 传感器状态（周期性，3秒）
├── status/actuator      ← 执行器状态（周期性，5秒）
└── control              ← 控制命令（订阅）
```

## 1. 设备信息主题 `device/{client_id}/info`

**用途:** 设备固定配置信息  
**周期:** 60秒  
**QoS:** 1  
**类型:** pub

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

---

## 2. 通用状态主题 `device/{client_id}/status`

**用途:** 事件性通知、命令反馈、心跳  
**周期:** 事件驱动  
**QoS:** 0  
**类型:** pub

**使用场景:**
1. **连接/断开通知**
   ```json
   { "type": "status", "status": "connected", "message": "...", "timestamp": 1234, "device_id": "..." }
   ```

2. **命令执行结果**
   ```json
   { "type": "status", "status": "success", "message": "LED turned on", "timestamp": 1234, "device_id": "..." }
   { "type": "status", "status": "error", "message": "Camera not available", "timestamp": 1234, "device_id": "..." }
   ```

3. **心跳消息（60秒）**
   ```json
   { "type": "heartbeat", "timestamp": 1234, "device_id": "..." }
   ```

---

## 3. 系统状态主题 `device/{client_id}/status/system`

**用途:** 系统动态监控数据  
**周期:** 10秒  
**QoS:** 0  
**类型:** pub

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

---

## 4. 传感器状态主题 `device/{client_id}/status/sensor`

**用途:** 传感器实时数据  
**周期:** 3秒  
**QoS:** 0  
**类型:** pub

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

---

## 5. 执行器状态主题 `device/{client_id}/status/actuator`

**用途:** 执行器状态监控  
**周期:** 5秒  
**QoS:** 0  
**类型:** pub

**JSON 格式:**
```json
{
  "arm": { "connected": false, "motor_count": 0, "status": "not_available" },
  "motor": { "connected": false, "motor_count": 0, "status": "not_available" },
  "timestamp": 1234
}
```

---

## 6. 控制主题 `device/{client_id}/control`

**用途:** 远程控制命令  
**周期:** 无  
**QoS:** 1  
**类型:** sub

**JSON 格式:**
```json
{
  "type": "control",
  "target": "camera",
  "action": "capture",
  "parameters": { "quality": 80 }
}
```

---

## 发送频率总结

| 主题 | 周期 | QoS | 用途 | 数据特性 |
|------|------|-----|------|----------|
| `device/{id}/info` | 60秒 | 1 | 设备信息 | 静态配置 |
| `device/{id}/status` | 事件 | 0 | 通用状态 | 事件通知、命令反馈、心跳 |
| `device/{id}/status/system` | 10秒 | 0 | 系统状态 | 系统动态数据 |
| `device/{id}/status/sensor` | 3秒 | 0 | 传感器状态 | 传感器实时数据 |
| `device/{id}/status/actuator` | 5秒 | 0 | 执行器状态 | 执行器状态 |
| `device/{id}/control` | - | 1 | 远程控制 | 订阅 |

---

## 代码实现位置

### 主题配置（board_extensions.cc:664-669）
```cpp
config.device_info_topic = "device/" + config.client_id + "/info";
config.control_topic = "device/" + config.client_id + "/control";
config.status_topic = "device/" + config.client_id + "/status";
config.system_status_topic = "device/" + config.client_id + "/status/system";
config.sensor_status_topic = "device/" + config.client_id + "/status/sensor";
config.actuator_status_topic = "device/" + config.client_id + "/status/actuator";
```

### 发送实现（board_extensions.cc）
- **设备信息** (551行): 60秒周期，使用 `CollectDeviceConfig()`
- **系统状态** (560行): 10秒周期，使用 `CollectSystemStatus()`
- **传感器状态** (569行): 3秒周期，使用 `CollectSensorStatus()`
- **执行器状态** (578行): 5秒周期，使用 `CollectActuatorStatus()`
- **通用状态** (714行): 连接时发送

### 订阅实现（user_mqtt_client.cpp:124行）
- 订阅控制主题 `device/{client_id}/control`

---

## 关键简化

1. ✅ 删除了 `device_events` 主题（功能和 `status` 主题重叠）
2. ✅ 统一使用 `status` 主题处理所有事件通知
3. ✅ 保持清晰的主题层级结构
4. ✅ 避免冗余，代码更简洁

所有主题都已实现并经过编译验证！
