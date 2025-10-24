# MQTT 管理类使用说明

这是一个功能完整的 MQTT 客户端管理类，提供了连接管理、消息发布、主题订阅等完整的 MQTT 通讯功能。

## 文件结构

- `mqtt_manager.py` - 核心 MQTT 管理类
- `mqtt_example.py` - 使用示例
- `mqtt_config.py` - 配置文件和主题模板
- `test_mqtt.py` - 原始测试脚本

## 主要特性

### 🔗 连接管理

- 自动连接和重连
- 连接状态监控
- 多种认证方式支持
- 连接统计信息

### 📤 消息发布

- 支持文本、JSON、二进制消息
- 可配置 QoS 级别
- 消息保留功能
- 发布主题管理

### 📥 消息订阅

- 动态添加/删除订阅
- 支持通配符主题
- 自定义回调函数
- 订阅状态管理

### 🛠️ 高级功能

- 上下文管理器支持
- 线程安全
- 详细的日志记录
- 统计信息收集
- 错误处理机制

## 快速开始

### 1. 基本使用

```python
from mqtt_manager import MQTTManager

# 创建MQTT管理器
mqtt = MQTTManager(
    host="your-mqtt-server.com",
    port=1883,
    debug=True
)

# 定义消息处理函数
def on_message(topic, payload, message):
    print(f"收到消息: {topic} -> {payload}")

# 添加订阅
mqtt.add_subscription(
    name="test_topic",
    topic="test/#",
    callback=on_message
)

# 连接并发布消息
if mqtt.connect():
    mqtt.publish("test/hello", "Hello MQTT!")
    mqtt.wait_for_messages(10)  # 等待10秒
    mqtt.disconnect()
```

### 2. 使用上下文管理器

```python
with MQTTManager(host="localhost", port=1883) as mqtt:
    mqtt.add_subscription("test", "test/#", lambda t, p, m: print(f"收到: {p}"))
    mqtt.publish("test/hello", "Hello World!")
    mqtt.wait_for_messages(5)
# 连接会自动断开
```

### 3. 发布 JSON 消息

```python
mqtt.publish_json("device/status", {
    "device_id": "device_001",
    "status": "online",
    "timestamp": time.time(),
    "battery": 85
})
```

## 详细 API 说明

### MQTTManager 类

#### 初始化参数

| 参数               | 类型 | 默认值      | 说明                       |
| ------------------ | ---- | ----------- | -------------------------- |
| host               | str  | "localhost" | MQTT 服务器地址            |
| port               | int  | 1883        | MQTT 服务器端口            |
| client_id          | str  | None        | 客户端 ID，None 时自动生成 |
| username           | str  | None        | 用户名                     |
| password           | str  | None        | 密码                       |
| keepalive          | int  | 60          | 保活时间                   |
| auto_reconnect     | bool | True        | 是否自动重连               |
| reconnect_interval | int  | 5           | 重连间隔（秒）             |
| debug              | bool | False       | 是否开启调试模式           |

#### 主要方法

##### 连接管理

- `connect()` - 连接到 MQTT 服务器
- `disconnect()` - 断开连接
- `get_status()` - 获取连接状态和统计信息

##### 订阅管理

- `add_subscription(name, topic, callback, description="", qos=0)` - 添加订阅
- `remove_subscription(name)` - 移除订阅
- `enable_subscription(name)` - 启用订阅
- `disable_subscription(name)` - 禁用订阅
- `get_subscriptions()` - 获取所有订阅信息

##### 发布管理

- `add_publish_topic(name, topic, description="", qos=0, retain=False)` - 添加发布主题
- `publish(topic_or_name, payload, qos=0, retain=False)` - 发布消息
- `publish_json(topic_or_name, data, qos=0, retain=False)` - 发布 JSON 消息
- `get_publish_topics()` - 获取所有发布主题信息

##### 其他方法

- `wait_for_messages(timeout=None)` - 等待消息（阻塞）
- `__enter__()` / `__exit__()` - 上下文管理器支持

## 配置管理

使用 `mqtt_config.py` 可以方便地管理 MQTT 配置：

```python
from mqtt_config import get_server_config, get_topic_template, format_topic

# 获取服务器配置
config = get_server_config("default")

# 获取主题模板
template = get_topic_template("device", "status")

# 格式化主题
topic = format_topic(template, device_id="device_001")
```

## 主题通配符支持

- `+` - 单级通配符，匹配一个主题级别
- `#` - 多级通配符，匹配多个主题级别

示例：

- `device/+/status` - 匹配 `device/device1/status`、`device/device2/status` 等
- `sensor/#` - 匹配 `sensor/temperature/data`、`sensor/humidity/data` 等

## 错误处理

类提供了完善的错误处理机制：

```python
# 检查连接状态
status = mqtt.get_status()
if status['status'] == 'failed':
    print(f"连接失败: {status['last_error']}")

# 检查发布结果
success = mqtt.publish("test/topic", "message")
if not success:
    print("发布失败")
```

## 统计信息

获取详细的统计信息：

```python
stats = mqtt.get_status()['stats']
print(f"发送消息数: {stats['messages_sent']}")
print(f"接收消息数: {stats['messages_received']}")
print(f"连接尝试次数: {stats['connection_attempts']}")
```

## 最佳实践

1. **使用上下文管理器**：确保连接正确关闭
2. **设置合适的 QoS**：根据消息重要性选择 QoS 级别
3. **处理异常**：总是检查连接和发布结果
4. **使用主题模板**：通过配置文件管理主题结构
5. **启用调试模式**：开发时开启调试模式便于排查问题

## 示例场景

### 物联网设备管理

```python
# 设备状态监控
mqtt.add_subscription(
    name="device_monitor",
    topic="device/+/status",
    callback=lambda t, p, m: update_device_status(p)
)

# 设备控制
mqtt.add_publish_topic("device_control", "device/{device_id}/control")

# 发送控制命令
mqtt.publish_json("device_control", {
    "command": "restart",
    "device_id": "device_001"
})
```

### 传感器数据收集

```python
# 订阅所有传感器数据
mqtt.add_subscription(
    name="sensor_data",
    topic="sensor/+/data",
    callback=lambda t, p, m: process_sensor_data(p)
)

# 发布传感器配置
mqtt.publish_json("sensor/config", {
    "sensor_id": "temp_001",
    "interval": 30,
    "threshold": 25.0
})
```

## 故障排除

### 常见问题

1. **连接失败**

   - 检查服务器地址和端口
   - 确认网络连接
   - 检查认证信息

2. **消息未收到**

   - 确认主题订阅正确
   - 检查 QoS 设置
   - 验证回调函数

3. **发布失败**
   - 检查连接状态
   - 确认主题格式正确
   - 检查消息内容

### 调试技巧

1. 启用调试模式：`debug=True`
2. 查看连接状态：`mqtt.get_status()`
3. 检查订阅列表：`mqtt.get_subscriptions()`
4. 监控统计信息：`mqtt.get_status()['stats']`

## 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。
