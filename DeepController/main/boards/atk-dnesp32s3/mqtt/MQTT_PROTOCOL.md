# MQTT 协议设计文档

## 概述

本文档描述了DeepDiary设备的MQTT通信协议，包括主题设计、数据格式和发送周期。

## 主题结构

设备使用以下MQTT主题进行通信：

```
device/{client_id}/config        # 设备固定配置信息
device/{client_id}/status/system   # 系统动态状态
device/{client_id}/status/sensor   # 传感器数据
device/{device_id}/status/actuator # 执行器状态
device/{client_id}/control        # 远程控制命令
device/{client_id}/events         # 事件消息
device/{client_id}/info           # 完整设备信息（兼容旧版）
device/{client_id}/status         # 通用状态消息（兼容旧版）
```

## 数据发送周期

| 主题 | 发送周期 | 说明 |
|------|---------|------|
| `device/{client_id}/config` | 60秒 | 设备固定配置信息，首次连接时立即发送 |
| `device/{client_id}/status/system` | 10秒 | 系统动态信息（网络、内存、运行时间等） |
| `device/{client_id}/status/sensor` | 3秒 | 传感器数据（加速度、角度等） |
| `device/{client_id}/status/actuator` | 6秒 | 执行器状态（机械臂、电机等） |

## 数据结构

### 1. DeviceConfigInfo - 设备固定配置

**主题**: `device/{client_id}/config`  
**发送周期**: 60秒  
**数据内容**: 设备固定不变的配置信息

```json
{
  "device_id": "ATK-DNESP32S3-ESP32-S3-12:34:56",
  "device_type": "ATK-DNESP32S3",
  "firmware_version": "1.0.0",
  "mac_address": "12:34:56:78:9A:BC",
  "chip_model": "ESP32-S3",
  "chip_revision": "v0.1",
  "capabilities": {
    "camera": true,
    "can_bus": true,
    "led_strip": true,
    "gimbal": true,
    "arm": true,
    "motor": true,
    "sensor": true
  }
}
```

### 2. SystemInfo - 系统动态状态

**主题**: `device/{client_id}/status/system`  
**发送周期**: 10秒  
**数据内容**: 系统运行时动态变化的信息

```json
{
  "wifi_ssid": "MyWiFi",
  "ip_address": "192.168.1.100",
  "free_heap": 234567,
  "uptime_seconds": 3600,
  "cpu_temperature": 45.5,
  "network_status": "connected",
  "timestamp": 1234567890
}
```

### 3. SensorData - 传感器数据

**主题**: `device/{client_id}/status/sensor`  
**发送周期**: 3秒  
**数据内容**: 传感器实时数据

```json
{
  "acc_x": 0.12,
  "acc_y": -0.05,
  "acc_z": 9.81,
  "acc_g": 9.82,
  "pitch": 5.2,
  "roll": -2.1,
  "sensor_status": "connected",
  "timestamp": 1234567890
}
```

### 4. ActuatorStatus - 执行器状态

**主题**: `device/{client_id}/status/actuator`  
**发送周期**: 6秒  
**数据内容**: 机械臂和电机状态

```json
{
  "arm": {
    "connected": true,
    "motor_count": 6,
    "status": "idle"
  },
  "motor": {
    "connected": true,
    "motor_count": 6,
    "status": "running"
  },
  "timestamp": 1234567890
}
```

## 协议定义文件

协议定义位于 `mqtt_protocol.json`，包含完整的主题、字段、类型和周期定义。

### 生成代码

运行以下命令重新生成协议代码：

```bash
cd DeepController/main/boards/atk-dnesp32s3/mqtt
python3 generate_protocol.py
```

这将生成 `mqtt_protocol_generated.h` 文件，包含所有结构定义和常量。

## 代码使用示例

### 发送设备配置

```cpp
DeviceConfigInfo config = device_info_collector_->CollectDeviceConfig();
user_mqtt_client_->SendDeviceConfig(config);
```

### 发送系统状态

```cpp
DeviceStatus::SystemInfo system_status = device_info_collector_->CollectSystemStatus();
user_mqtt_client_->SendSystemStatus(system_status);
```

### 发送传感器数据

```cpp
DeviceStatus::SensorData sensor_status = device_info_collector_->CollectSensorStatus();
user_mqtt_client_->SendSensorStatus(sensor_status);
```

### 发送执行器状态

```cpp
DeviceStatus::ActuatorStatus actuator_status = device_info_collector_->CollectActuatorStatus();
user_mqtt_client_->SendActuatorStatus(actuator_status);
```

## 兼容性说明

为了保持向后兼容，原有的 `DeviceInfo` 结构体和 `SendDeviceInfo()` 方法仍然保留，但建议使用新的分级发送方法。

## 文件结构

```
mqtt/
├── user_mqtt_client.h              # MQTT客户端头文件
├── user_mqtt_client.cpp            # MQTT客户端实现
├── device_info_collector.h         # 设备信息收集器
├── device_info_collector.cpp       # 设备信息收集实现
├── mqtt_protocol.json              # 协议定义文件（JSON格式）
├── generate_protocol.py            # 协议生成器脚本
├── mqtt_protocol_generated.h        # 生成的协议代码（自动生成）
└── MQTT_PROTOCOL.md                # 本文档
```

## 修改协议

如需修改协议：

1. 编辑 `mqtt_protocol.json`
2. 运行 `python3 generate_protocol.py` 重新生成代码
3. 更新相关的收集器和发送逻辑

## 服务器端解析

服务器端可以根据协议定义文件 `mqtt_protocol.json` 自动生成解析代码。该文件包含：

- 所有主题的完整定义
- 每个字段的数据类型
- 发送周期信息
- 字段描述

这使得服务器端可以自动生成订阅主题和处理逻辑。
