# MQTT功能集成示例

本文档展示如何在主项目中集成和使用用户MQTT功能。

## 集成状态

✅ **已完成集成** - MQTT功能已成功集成到 `BoardExtensions` 类中，会在WiFi连接后自动启动。

## 自动启动流程

1. **板级初始化** - 在 `atk_dnesp32s3` 构造函数中创建 `BoardExtensions` 对象
2. **MQTT初始化** - 在 `BoardExtensions` 构造函数中调用 `InitializeUserMqtt()`
3. **WiFi连接** - 当WiFi连接成功后，自动启动MQTT客户端
4. **设备信息上报** - 连接成功后自动发送设备信息

## 配置MQTT服务器

### 方法1：使用默认配置
```cpp
// 使用默认配置（34.172.161.212:1883）
UserMqttConfig::LoadFromNvs();
```

### 方法2：自定义配置
```cpp
// 设置自定义MQTT服务器
UserMqttConfig::SetBrokerHost("your-mqtt-server.com");
UserMqttConfig::SetBrokerPort(1883);
UserMqttConfig::SetClientId("ATK-DNESP32S3-001");
UserMqttConfig::SetUsername("your-username");
UserMqttConfig::SetPassword("your-password");
UserMqttConfig::SaveToNvs();  // 保存到NVS
```

## 测试MQTT连接

### 1. 检查日志输出
启动设备后，查看串口日志：
```
I (12345) board_ext: 初始化用户MQTT客户端...
I (12346) board_ext: 用户MQTT客户端初始化完成
I (12347) board_ext: 启动用户MQTT客户端...
I (12348) UserMqttConfig: Configuration loaded from NVS
I (12349) UserMqttConfig: Broker: 34.172.161.212:1883, Client ID: ATK-DNESP32S3-ESP32S3-12345678
I (12350) UserMQTT: Initialized with broker: 34.172.161.212:1883, client_id: ATK-DNESP32S3-ESP32S3-12345678
I (12351) UserMQTT: Connecting to broker 34.172.161.212:1883
I (12352) UserMQTT: Successfully connected to broker
I (12353) UserMQTT: Subscribed to control topic: device/ATK-DNESP32S3-ESP32S3-12345678/control
I (12354) board_ext: 已连接到用户MQTT服务器
I (12355) UserMQTT: Device info sent to topic: device/ATK-DNESP32S3-ESP32S3-12345678/info
```

### 2. 发送测试命令
使用MQTT客户端工具（如MQTT Explorer）连接到服务器，向控制主题发送测试命令：

**主题**: `device/ATK-DNESP32S3-ESP32S3-12345678/control`

**测试LED控制**:
```json
{
  "type": "led",
  "target": "strip",
  "action": "on"
}
```

**测试系统状态**:
```json
{
  "type": "system",
  "target": "system",
  "action": "status"
}
```

### 3. 监控设备信息
订阅设备信息主题查看设备状态：

**主题**: `device/ATK-DNESP32S3-ESP32S3-12345678/info`

## 自定义扩展

### 添加新的控制命令
在 `RemoteControlHandler` 类中添加新的命令处理：

```cpp
// 在 remote_control_handler.h 中添加新的命令常量
static constexpr const char* CMD_CUSTOM = "custom";
static constexpr const char* ACTION_CUSTOM_DO_SOMETHING = "do_something";

// 在 remote_control_handler.cpp 中添加处理函数
void RemoteControlHandler::HandleCustomCommand(const RemoteControlCommand& command) {
    if (command.action == ACTION_CUSTOM_DO_SOMETHING) {
        // 实现自定义功能
        SendStatus("success", "Custom action executed");
    }
}
```

### 添加新的设备信息
在 `DeviceInfoCollector` 类中添加新的信息收集：

```cpp
// 在 device_info_collector.h 中添加新的字段
std::string custom_status;

// 在 device_info_collector.cpp 中实现收集逻辑
std::string DeviceInfoCollector::GetCustomStatus() const {
    // 实现自定义状态获取
    return "custom_value";
}
```

## 故障排除

### 1. MQTT连接失败
- 检查网络连接
- 验证MQTT服务器地址和端口
- 检查用户名和密码
- 查看防火墙设置

### 2. 设备信息不完整
- 检查设备组件是否正确初始化
- 验证 `DeviceInfoCollector` 中的组件引用
- 查看相关组件的状态

### 3. 远程控制不响应
- 检查 `RemoteControlHandler` 中的组件引用
- 验证命令格式是否正确
- 查看设备组件是否可用

## 性能优化

### 1. 减少内存使用
- 使用 `std::unique_ptr` 管理对象生命周期
- 及时释放不需要的资源
- 优化JSON序列化

### 2. 提高响应速度
- 使用异步任务处理控制命令
- 缓存设备信息减少重复收集
- 优化网络通信

### 3. 增强稳定性
- 添加重连机制
- 实现错误恢复
- 增加超时处理

## 安全考虑

1. **认证**：使用用户名和密码认证
2. **加密**：考虑使用SSL/TLS加密连接
3. **访问控制**：限制控制命令的权限
4. **数据验证**：验证接收到的命令格式

## 监控和调试

### 日志级别
- `UserMQTT` - MQTT客户端日志
- `UserMqttConfig` - 配置管理日志  
- `RemoteControl` - 远程控制日志
- `DeviceInfo` - 设备信息日志

### 调试工具
- 串口日志监控
- MQTT客户端工具
- 网络抓包分析
- 内存使用监控
