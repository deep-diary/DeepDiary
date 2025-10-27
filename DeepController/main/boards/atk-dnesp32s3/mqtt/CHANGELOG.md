# MQTT 协议重构变更日志

## 概述

本次重构重新设计了MQTT协议，将固定配置信息和动态状态信息分离，实现了分级状态发布，并建立了统一的协议定义文件。

## 主要变更

### 1. 数据结构分离 (user_mqtt_client.h)

**新增结构体**：

- `DeviceConfigInfo`: 设备固定配置信息
  - 设备ID、型号、固件版本、MAC地址、芯片信息
  - 硬件能力标志

- `DeviceStatus::SystemInfo`: 系统动态信息
  - WiFi、IP、内存、运行时间、温度、网络状态

- `DeviceStatus::SensorData`: 传感器数据
  - 三轴加速度、总加速度、俯仰角、翻滚角、传感器状态

- `DeviceStatus::ActuatorStatus`: 执行器状态
  - 机械臂连接状态、电机数量、状态信息
  - 电机连接状态、电机数量、状态信息

### 2. 新增主题配置 (user_mqtt_client.h)

在 `UserMqttClientConfig` 中新增：
- `config_topic`: 设备配置发布主题
- `system_status_topic`: 系统状态发布主题
- `sensor_status_topic`: 传感器状态发布主题  
- `actuator_status_topic`: 执行器状态发布主题

主题格式：
```
device/{client_id}/config
device/{client_id}/status/system
device/{client_id}/status/sensor
device/{client_id}/status/actuator
```

### 3. 新增发送方法 (user_mqtt_client.h/cpp)

新增方法：
- `SendDeviceConfig()`: 发送设备固定配置
- `SendSystemStatus()`: 发送系统状态
- `SendSensorStatus()`: 发送传感器数据
- `SendActuatorStatus()`: 发送执行器状态

### 4. 数据收集器更新 (device_info_collector.h/cpp)

新增方法：
- `CollectDeviceConfig()`: 收集设备固定配置
- `CollectSystemStatus()`: 收集系统状态
- `CollectSensorStatus()`: 收集传感器数据
- `CollectActuatorStatus()`: 收集执行器状态

新增辅助方法：
- `GetMacAddress()`: 获取MAC地址
- `GetChipModel()`: 获取芯片型号
- `GetChipRevision()`: 获取芯片版本

### 5. 循环发送逻辑更新 (board_extensions.cc)

修改了周期性发送逻辑，实现不同周期发送不同类型的数据：

| 数据类型 | 发送周期 | 任务计数 |
|---------|---------|---------|
| 设备配置 | 60秒 | 20次 |
| 系统状态 | 10秒 | 3次 |
| 传感器数据 | 3秒 | 1次 |
| 执行器状态 | 6秒 | 2次 |
| 完整设备信息（兼容） | 30秒 | 10次 |

**关键特性**：
- 首次连接立即发送设备配置
- 使用静态计数器控制发送频率
- 保持与旧版代码的兼容性

### 6. 协议定义文件 (mqtt_protocol.json)

创建了统一的JSON格式协议定义文件，包含：
- 所有主题的完整定义
- 每个字段的数据类型
- 发送周期信息
- 字段描述

### 7. 协议生成器 (generate_protocol.py)

创建了自动生成C++代码的Python脚本，支持：
- 根据JSON定义生成头文件
- 自动生成结构体定义
- 自动生成主题常量

### 8. 文档

新增文档：
- `MQTT_PROTOCOL.md`: 完整的协议文档
- `CHANGELOG.md`: 变更日志（本文件）

## 发送周期对比

### 重构前
```
device/{client_id}/info - 每30秒发送完整设备信息（包含固定+动态）
```

### 重构后
```
device/{client_id}/config - 每60秒发送设备固定配置
device/{client_id}/status/system - 每10秒发送系统动态信息
device/{client_id}/status/sensor - 每3秒发送传感器数据
device/{client_id}/status/actuator - 每6秒发送执行器状态

device/{client_id}/info - 每30秒发送完整设备信息（保留兼容性）
```

## 优势

1. **协议清晰**: 分离固定配置和动态状态，语义更清晰
2. **发送高效**: 不同数据按不同频率发送，减少不必要的数据传输
3. **易于扩展**: 统一的协议定义文件，易于添加新字段和新主题
4. **服务器友好**: JSON格式的协议定义，服务器端可自动解析
5. **向后兼容**: 保留原有接口，不影响现有功能

## 使用示例

### 生成协议代码

```bash
cd DeepController/main/boards/atk-dnesp32s3/mqtt
python3 generate_protocol.py
```

### 在代码中使用

```cpp
// 收集并发送设备配置（每60秒）
DeviceConfigInfo config = device_info_collector_->CollectDeviceConfig();
user_mqtt_client_->SendDeviceConfig(config);

// 收集并发送系统状态（每10秒）
DeviceStatus::SystemInfo system_status = device_info_collector_->CollectSystemStatus();
user_mqtt_client_->SendSystemStatus(system_status);

// 收集并发送传感器数据（每3秒）
DeviceStatus::SensorData sensor_status = device_info_collector_->CollectSensorStatus();
user_mqtt_client_->SendSensorStatus(sensor_status);

// 收集并发送执行器状态（每6秒）
DeviceStatus::ActuatorStatus actuator_status = device_info_collector_->CollectActuatorStatus();
user_mqtt_client_->SendActuatorStatus(actuator_status);
```

## 向后兼容

为了保持向后兼容，以下内容保持不变：
- `DeviceInfo` 结构体
- `SendDeviceInfo()` 方法
- `CollectDeviceInfo()` 方法
- `SendStatus()` 通用状态方法
- `SendHeartbeat()` 心跳方法

## 注意事项

1. 传感器数据现在包含在分级状态主题中，发送周期为3秒
2. 设备配置信息首次连接时立即发送，之后每60秒发送一次
3. 系统状态、传感器数据和执行器状态分别在不同的主题中发送
4. 服务器端需要订阅多个主题来获取完整设备信息

## 测试建议

1. 验证所有新方法是否正确实现
2. 验证发送周期是否符合预期
3. 验证数据格式是否正确
4. 验证服务器端是否能正确解析所有主题
5. 验证向后兼容性是否保持

## 后续优化

1. 可以进一步优化传感器数据的发送频率（如果对实时性要求更高）
2. 可以考虑将某些不常变化的数据发送频率降低
3. 可以添加更多状态分类（如网络状态、硬件错误等）
4. 可以实现更灵活的周期配置（通过配置文件）

