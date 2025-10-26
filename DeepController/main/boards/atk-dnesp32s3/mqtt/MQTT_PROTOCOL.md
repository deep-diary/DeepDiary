# DeepController MQTT 协议说明文档

## 概述

本文档详细说明了DeepController设备的MQTT通信协议，包括上行（设备到服务器）和下行（服务器到设备）的消息格式、主题结构和数据规范。

## 协议版本
- **版本**: v1.0
- **更新日期**: 2025-10-26
- **设备型号**: ATK-DNESP32S3

## 主题结构

### 基础主题格式
```
deepcontroller/{device_id}/{message_type}
```

### 具体主题列表

#### 上行主题（设备 → 服务器）

| 主题 | 描述 | 频率 | QoS |
|------|------|------|-----|
| `deepcontroller/{device_id}/status` | 设备状态信息 | 30秒 | 1 |
| `deepcontroller/{device_id}/sensor` | 传感器数据 | 10秒 | 1 |
| `deepcontroller/{device_id}/motor` | 电机状态 | 5秒 | 1 |
| `deepcontroller/{device_id}/arm` | 机械臂状态 | 5秒 | 1 |
| `deepcontroller/{device_id}/camera` | 摄像头状态 | 30秒 | 1 |
| `deepcontroller/{device_id}/system` | 系统信息 | 60秒 | 1 |
| `deepcontroller/{device_id}/alarm` | 告警信息 | 实时 | 2 |
| `deepcontroller/{device_id}/log` | 日志信息 | 按需 | 0 |

#### 下行主题（服务器 → 设备）

| 主题 | 描述 | QoS |
|------|------|-----|
| `deepcontroller/{device_id}/command` | 控制命令 | 1 |
| `deepcontroller/{device_id}/config` | 配置更新 | 1 |
| `deepcontroller/{device_id}/firmware` | 固件更新 | 1 |
| `deepcontroller/{device_id}/query` | 查询请求 | 1 |

## 消息格式

### 通用消息结构

所有MQTT消息都使用JSON格式，包含以下通用字段：

```json
{
  "device_id": "ATK-DNESP32S3-ESP32-S3-12345678",
  "timestamp": 1706284800,
  "message_type": "status|sensor|motor|arm|camera|system|alarm|log",
  "data": { ... },
  "version": "1.0"
}
```

### 1. 设备状态消息 (status)

**主题**: `deepcontroller/{device_id}/status`

```json
{
  "device_id": "ATK-DNESP32S3-ESP32-S3-12345678",
  "timestamp": 1706284800,
  "message_type": "status",
  "data": {
    "device_type": "ATK-DNESP32S3",
    "firmware_version": "1.0.0",
    "wifi_ssid": "MyWiFi",
    "ip_address": "192.168.1.100",
    "free_heap": 245760,
    "uptime_seconds": 3600,
    "cpu_temperature": 0.0,
    "components": {
      "camera_available": true,
      "can_bus_available": true,
      "led_strip_available": true,
      "gimbal_available": true,
      "sensor_available": true
    },
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
  },
  "version": "1.0"
}
```

### 2. 传感器数据消息 (sensor)

**主题**: `deepcontroller/{device_id}/sensor`

```json
{
  "device_id": "ATK-DNESP32S3-ESP32-S3-12345678",
  "timestamp": 1706284800,
  "message_type": "sensor",
  "data": {
    "sensor_available": true,
    "sensor_status": "connected",
    "acceleration": {
      "x": 0.12,
      "y": -0.05,
      "z": 9.81,
      "total": 9.82
    },
    "orientation": {
      "pitch": 1.2,
      "roll": -0.3
    },
    "unit": {
      "acceleration": "m/s²",
      "orientation": "degrees"
    }
  },
  "version": "1.0"
}
```

### 3. 电机状态消息 (motor)

**主题**: `deepcontroller/{device_id}/motor`

```json
{
  "device_id": "ATK-DNESP32S3-ESP32-S3-12345678",
  "timestamp": 1706284800,
  "message_type": "motor",
  "data": {
    "motor_connected": true,
    "motor_count": 6,
    "motor_status": "connected",
    "motors": [
      {
        "id": 1,
        "position": 0.0,
        "velocity": 0.0,
        "torque": 0.0,
        "temperature": 25.0,
        "status": "idle"
      }
    ]
  },
  "version": "1.0"
}
```

### 4. 机械臂状态消息 (arm)

**主题**: `deepcontroller/{device_id}/arm`

```json
{
  "device_id": "ATK-DNESP32S3-ESP32-S3-12345678",
  "timestamp": 1706284800,
  "message_type": "arm",
  "data": {
    "arm_connected": true,
    "arm_motor_count": 6,
    "arm_status": "connected",
    "joints": [
      {
        "joint_id": 1,
        "angle": 0.0,
        "velocity": 0.0,
        "torque": 0.0,
        "status": "idle"
      }
    ],
    "end_effector": {
      "position": {"x": 0.0, "y": 0.0, "z": 0.0},
      "orientation": {"x": 0.0, "y": 0.0, "z": 0.0}
    }
  },
  "version": "1.0"
}
```

### 5. 摄像头状态消息 (camera)

**主题**: `deepcontroller/{device_id}/camera`

```json
{
  "device_id": "ATK-DNESP32S3-ESP32-S3-12345678",
  "timestamp": 1706284800,
  "message_type": "camera",
  "data": {
    "camera_available": true,
    "camera_status": "connected",
    "streaming": true,
    "resolution": {
      "width": 640,
      "height": 480
    },
    "format": "JPEG",
    "fps": 30,
    "quality": 80
  },
  "version": "1.0"
}
```

### 6. 系统信息消息 (system)

**主题**: `deepcontroller/{device_id}/system`

```json
{
  "device_id": "ATK-DNESP32S3-ESP32-S3-12345678",
  "timestamp": 1706284800,
  "message_type": "system",
  "data": {
    "memory": {
      "free_heap": 245760,
      "min_free_heap": 200000,
      "total_internal_ram": 327680,
      "free_spiram": 4194304,
      "total_spiram": 8388608
    },
    "chip": {
      "model": "ESP32-S3",
      "revision": "0",
      "features": "WiFi BLE"
    },
    "flash": "8MB",
    "psram": "8MB"
  },
  "version": "1.0"
}
```

### 7. 告警消息 (alarm)

**主题**: `deepcontroller/{device_id}/alarm`

```json
{
  "device_id": "ATK-DNESP32S3-ESP32-S3-12345678",
  "timestamp": 1706284800,
  "message_type": "alarm",
  "data": {
    "alarm_level": "warning|error|critical",
    "alarm_type": "motor_overheat|sensor_error|communication_failure",
    "description": "Motor 1 temperature exceeds 60°C",
    "component": "motor",
    "component_id": 1,
    "value": 65.0,
    "threshold": 60.0,
    "unit": "°C"
  },
  "version": "1.0"
}
```

## 下行消息格式

### 1. 控制命令 (command)

**主题**: `deepcontroller/{device_id}/command`

```json
{
  "command_id": "cmd_001",
  "timestamp": 1706284800,
  "command_type": "motor_control|arm_control|camera_control|led_control",
  "target": "motor|arm|camera|led",
  "action": "start|stop|move|set_position|set_speed",
  "parameters": {
    "motor_id": 1,
    "position": 90.0,
    "speed": 50.0,
    "duration": 5000
  },
  "priority": "high|normal|low",
  "timeout": 10000
}
```

### 2. 配置更新 (config)

**主题**: `deepcontroller/{device_id}/config`

```json
{
  "config_id": "config_001",
  "timestamp": 1706284800,
  "config_type": "sensor|motor|camera|system",
  "parameters": {
    "sensor": {
      "sample_rate": 100,
      "range": "8G",
      "bandwidth": "100Hz"
    },
    "motor": {
      "max_speed": 100,
      "max_torque": 50,
      "acceleration": 10
    },
    "camera": {
      "resolution": "640x480",
      "quality": 80,
      "fps": 30
    }
  }
}
```

### 3. 查询请求 (query)

**主题**: `deepcontroller/{device_id}/query`

```json
{
  "query_id": "query_001",
  "timestamp": 1706284800,
  "query_type": "status|sensor|motor|arm|camera|system",
  "parameters": {
    "include_details": true,
    "time_range": {
      "start": 1706280000,
      "end": 1706284800
    }
  }
}
```

## 错误处理

### 错误响应格式

```json
{
  "device_id": "ATK-DNESP32S3-ESP32-S3-12345678",
  "timestamp": 1706284800,
  "message_type": "error",
  "data": {
    "error_code": "INVALID_COMMAND|PARAMETER_ERROR|DEVICE_BUSY|HARDWARE_ERROR",
    "error_message": "Invalid motor ID specified",
    "command_id": "cmd_001",
    "details": {
      "parameter": "motor_id",
      "value": 10,
      "valid_range": "1-6"
    }
  },
  "version": "1.0"
}
```

### 常见错误代码

| 错误代码 | 描述 |
|----------|------|
| `INVALID_COMMAND` | 无效的命令类型 |
| `PARAMETER_ERROR` | 参数错误 |
| `DEVICE_BUSY` | 设备忙碌 |
| `HARDWARE_ERROR` | 硬件错误 |
| `COMMUNICATION_ERROR` | 通信错误 |
| `PERMISSION_DENIED` | 权限不足 |

## 数据单位说明

### 传感器数据
- **加速度**: m/s² (米每秒平方)
- **角度**: degrees (度)
- **温度**: °C (摄氏度)

### 电机数据
- **位置**: degrees (度)
- **速度**: rpm (转每分钟)
- **扭矩**: N·m (牛·米)

### 机械臂数据
- **关节角度**: degrees (度)
- **位置**: mm (毫米)
- **速度**: mm/s (毫米每秒)

## 实现建议

### Web界面开发建议

1. **实时数据展示**
   - 使用WebSocket连接MQTT代理
   - 订阅所有设备状态主题
   - 实现数据可视化图表

2. **控制界面**
   - 发布控制命令到设备
   - 实现命令确认和错误处理
   - 提供参数验证

3. **历史数据**
   - 存储MQTT消息到数据库
   - 提供数据查询和分析功能
   - 实现告警历史记录

### 安全建议

1. **认证授权**
   - 使用MQTT用户名/密码认证
   - 实现设备ID白名单
   - 定期更新认证信息

2. **数据加密**
   - 使用TLS加密MQTT连接
   - 敏感数据额外加密
   - 实现消息签名验证

## 版本历史

- **v1.0** (2025-10-26): 初始版本，包含基本设备状态和传感器数据

## 联系方式

如有问题或建议，请联系DeepDiary团队。
