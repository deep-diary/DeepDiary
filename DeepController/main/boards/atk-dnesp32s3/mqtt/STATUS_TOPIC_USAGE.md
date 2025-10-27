# 状态主题使用说明

## 主题层级关系

```
device/{client_id}/status              ← 通用状态主题（事件驱动）
├── device/{client_id}/status/system   ← 系统状态（周期发送）
├── device/{client_id}/status/sensor   ← 传感器状态（周期发送）
└── device/{client_id}/status/actuator ← 执行器状态（周期发送）
```

## 通用状态主题 `device/{client_id}/status`

**用途:** 事件性通知、命令执行结果  
**发送时机:** 事件驱动（不固定周期）  
**QoS:** 0

### 发送的场景：

1. **连接事件**
   - `SendStatus("connected", "Successfully connected to user MQTT broker")`
   - `SendStatus("test", "Device connected and ready for commands")`

2. **断开事件**
   - `SendStatus("disconnected", "Disconnected from user MQTT broker")`

3. **心跳消息（每60秒）**
   ```json
   {
     "type": "heartbeat",
     "timestamp": 1234,
     "device_id": "ATK-DNESP32S3-9888e000ae28"
   }
   ```

4. **命令执行结果**
   - `SendStatus("success", "LED turned on")`
   - `SendStatus("error", "Camera not available")`
   - `SendStatus("info", "System is running")`

## 子状态主题（周期发送）

### 1. `device/{client_id}/status/system` 
- **周期:** 10秒
- **数据:** WiFi、IP、内存、运行时间、温度等
- **特点:** 系统动态监控数据

### 2. `device/{client_id}/status/sensor`
- **周期:** 3秒
- **数据:** 加速度、俯仰角、翻滚角等
- **特点:** 传感器实时数据

### 3. `device/{client_id}/status/actuator`
- **周期:** 5秒
- **数据:** 机械臂、电机状态
- **特点:** 执行器状态监控

## 总结

**通用状态主题** 和 **子状态主题** 的职责不同：

- **通用状态 (`status`)**: 
  - 事件性通知（连接/断开/错误）
  - 命令执行结果反馈
  - 心跳消息
  - **不固定周期，按需发送**

- **子状态 (`status/system`, `status/sensor`, `status/actuator`)**:
  - 周期性数据监控
  - 设备运行状态追踪
  - **固定周期发送**

所以通用状态主题是**必要的**，它承担了**事件通知**和**命令反馈**的功能，而子主题负责**数据监控**。两者互为补充，不是重复。
