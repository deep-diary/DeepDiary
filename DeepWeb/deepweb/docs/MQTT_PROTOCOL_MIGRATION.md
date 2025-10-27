# MQTT协议迁移说明

## 概述

本文档说明了对 MQTT 通信协议的重构，使其能够基于 JSON 协议文件动态配置，实现协议变更后无需修改业务代码的目标。

## 变更内容

### 1. 新增协议解析器 (`protocol_parser.py`)

创建了 `DeepWeb/deepweb/services/cloud_communication/mqtt/protocol_parser.py`，提供以下功能：

- **动态协议加载**：从 JSON 文件读取协议定义
- **自动订阅生成**：基于协议自动生成 MQTT 主题订阅
- **设备ID提取**：智能从主题中提取设备ID
- **消息格式解析**：根据协议定义解析消息数据

#### 主要方法：

```python
class MQTTProtocolParser:
    def get_subscribe_topics()  # 获取需要订阅的主题
    def get_publish_topics()     # 获取需要发布的主题
    def extract_device_id()      # 提取设备ID
    def setup_subscriptions()    # 自动设置订阅
    def parse_message()          # 解析消息
```

### 2. 更新 MQTT 服务适配器 (`mqtt_service_adapter.py`)

修改了 `DeepWeb/deepweb/services/mqtt_service_adapter.py`：

- **集成协议解析器**：使用协议解析器自动配置订阅
- **兼容新旧格式**：同时支持新协议和旧的 deepcontroller 格式
- **分类数据处理**：正确处理 device_status 中的 categories（system, sensor, actuator）

#### 主要变更：

1. 使用协议解析器初始化订阅
2. 保留旧格式的兼容性（deepcontroller 前缀）
3. 支持 device_status 的分类数据结构

### 3. 更新 MQTT 监控页面 (`06_📡_MQTT数据监控.py`)

修改了 `DeepWeb/deepweb/pages/06_📡_MQTT数据监控.py`：

- **动态订阅配置**：基于协议文件自动生成订阅
- **分分类数据处理**：正确处理新协议中 device_status 的 categories
- **事件显示**：新增设备事件（device_events）的显示

#### 主要变更：

1. 导入协议解析器
2. 基于协议自动设置订阅主题
3. 处理 device_status 中的 categories 数据
4. 新增 device_events 数据存储和显示
5. 添加事件显示标签页

### 4. 新增数据结构

为支持新协议，添加了以下数据存储：

```python
mqtt_data = {
    # 新协议格式
    'device_info': [],      # 设备信息
    'device_status': [],    # 设备状态
    'device_events': [],    # 设备事件
    
    # 从 device_status 中分离出来的类别
    'device_sensor': [],    # 传感器数据
    'device_motor': [],     # 电机数据
    'device_arm': [],       # 机械臂数据
    # ...
    
    # 保留旧格式（兼容 deepcontroller 前缀）
    'legacy_status': [],
    # ...
}
```

## 新协议格式

### device_info（设备信息）

```json
{
  "device_id": "ATK-DNESP32S3",
  "device_type": "机器人",
  "firmware_version": "1.0.0",
  "mac_address": "xx:xx:xx:xx:xx:xx",
  "chip_model": "ESP32-S3",
  "chip_revision": "v0.1",
  "hardware_capabilities": {
    "camera": true,
    "can_bus": false,
    "led_strip": true,
    "gimbal": false,
    "arm": true,
    "motor": true,
    "sensor": true
  }
}
```

### device_status（设备状态）

新协议中的 device_status 包含 categories：

```json
{
  "system": {
    "wifi_ssid": "WiFi名称",
    "ip_address": "192.168.1.100",
    "free_heap": 100000,
    "uptime_seconds": 3600,
    "cpu_temperature": 45.0,
    "network_status": "connected"
  },
  "sensor": {
    "acc_x": 0.0,
    "acc_y": 0.0,
    "acc_z": 9.81,
    "acc_g": 9.81,
    "pitch": 0.0,
    "roll": 0.0,
    "sensor_status": "normal"
  },
  "actuator": {
    "motor": {
      "connected": true,
      "motor_count": 6,
      "status": "normal"
    },
    "arm": {
      "connected": true,
      "motor_count": 6,
      "status": "normal"
    }
  }
}
```

### device_events（设备事件）

```json
{
  "event_type": "error|warning|info",
  "event_message": "事件消息内容",
  "timestamp": 1234567890
}
```

## 优势

### 1. 动态配置

- 协议变更只需修改 JSON 文件
- 无需修改业务代码
- 自动生成订阅配置

### 2. 易于维护

- 协议定义集中在一个文件
- 统一的解析逻辑
- 减少重复代码

### 3. 良好的扩展性

- 易于添加新的主题类型
- 灵活的数据结构支持
- 自动处理消息格式

## 使用示例

### 修改协议文件

编辑 `DeepWeb/deepweb/services/cloud_communication/mqtt/mqtt_protocol.json`：

```json
{
  "topics": {
    "device_info": {
      "name": "device/{client_id}/info",
      "description": "设备信息"
    },
    "device_status": {
      "name": "device/{client_id}/status",
      "description": "设备状态"
    }
  }
}
```

### 代码自动适配

修改协议文件后，代码会自动：

1. 加载新的协议定义
2. 更新订阅配置
3. 调整消息处理逻辑

## 测试建议

1. **测试设备信息**：验证 device/{device_id}/info 消息接收和显示
2. **测试设备状态**：验证 device/{device_id}/status 消息的分类数据处理
3. **测试设备事件**：验证 device/{device_id}/events 消息的接收和显示
4. **测试分类数据**：验证 device_status 中的 system、sensor、actuator 分类正确处理

## 注意事项

1. **协议文件路径**：确保 `mqtt_protocol.json` 在正确的位置
2. **QoS级别**：根据协议定义正确设置 QoS
3. **消息频率**：注意 `period_ms` 定义的发布频率

## 协议支持

系统现在只支持新协议格式：

- `device/{client_id}/info` - 设备固定配置信息
- `device/{client_id}/status` - 设备动态状态（包含 system、sensor、actuator 分类）
- `device/{client_id}/events` - 设备事件消息

旧的 `deepcontroller/` 前缀格式不再支持。

## 参考

- 协议文件：`DeepWeb/deepweb/services/cloud_communication/mqtt/mqtt_protocol.json`
- ESP32 协议文件：`DeepController/main/boards/atk-dnesp32s3/mqtt/mqtt_protocol.json`

