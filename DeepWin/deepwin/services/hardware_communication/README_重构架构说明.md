# 串口转 CAN 架构重构说明

## 重构概述

根据您的建议，我们重构了串口转 CAN 的架构，将职责进行了清晰的分离，并移除了硬件相关的逻辑：

- **SerialCommunicator**: 专注于串口通信和串口帧列表管理
- **CanBusCommunicator**: 专注于串口转 CAN 逻辑和 CAN 帧列表管理（已抽象化，不处理硬件相关逻辑）

## 架构设计

### 1. SerialCommunicator（串口通信模块）

**职责**：

- 串口连接管理（打开/关闭串口）
- 串口数据发送和接收
- 串口帧列表管理（发送和接收的串口帧）
- 串口通信错误处理

**主要信号**：

- `raw_frame_received(str, bytes)`: 收到串口原始帧
- `raw_frame_send(str, bytes)`: 发送串口原始帧
- `frame_lists_updated()`: 串口帧列表更新信号

**主要方法**：

- `send_bytes(port_name, data)`: 发送串口数据
- `open_port(port_name, baud_rate, device_id)`: 打开串口
- `close_port(port_name)`: 关闭串口
- `clear_frame_lists()`: 清空串口帧列表
- `get_frame_lists_info()`: 获取串口帧列表信息

### 2. CanBusCommunicator（CAN 通信模块）

**职责**：

- 串口数据转 CAN 帧 (ser2can)
- CAN 帧转串口数据 (can2ser)
- CAN 帧列表管理（发送和接收的 CAN 帧）

**注意**：此模块已抽象化，不处理 DBC 解析和端口映射，这些应该在更高层处理。

**主要信号**：

- `can_frame_received(int, bytes, bool)`: 收到 CAN 帧
- `can_frame_sent(int, bytes, bool)`: 发送 CAN 帧
- `serial_data_to_send(bytes)`: 需要发送的串口数据
- `can_frame_lists_updated()`: CAN 帧列表更新信号

**主要方法**：

- `process_serial_data(data)`: 处理串口数据，转换为 CAN 帧
- `send_can_frame(arbitration_id, data, is_extended_id)`: 发送 CAN 帧
- `clear_can_frame_lists()`: 清空 CAN 帧列表
- `get_can_frame_lists_info()`: 获取 CAN 帧列表信息

## 数据流程

### 接收流程（串口 → CAN）

```
串口设备 → SerialCommunicator → CanBusCommunicator → 上层应用
    ↓              ↓                    ↓
原始串口数据 → 串口帧列表 → CAN帧列表 + DBC解析
```

1. 串口设备发送数据到 `SerialCommunicator`
2. `SerialCommunicator` 记录到串口帧列表，发送 `raw_frame_received` 信号
3. `CanBusCommunicator` 接收信号，解析为 CAN 帧
4. `CanBusCommunicator` 记录到 CAN 帧列表，进行 DBC 解析
5. 发送 `can_parsed_data_received` 信号给上层应用

### 发送流程（CAN → 串口）

```
上层应用 → CanBusCommunicator → SerialCommunicator → 串口设备
    ↓              ↓                    ↓
CAN命令 → CAN帧列表 → 串口帧列表 → 串口数据
```

1. 上层应用调用 `CanBusCommunicator.send_can_frame()`
2. `CanBusCommunicator` 将 CAN 帧转换为串口数据格式
3. `CanBusCommunicator` 记录到 CAN 帧列表，发送 `serial_data_to_send` 信号
4. `SerialCommunicator` 接收信号，发送串口数据
5. `SerialCommunicator` 记录到串口帧列表

## 信号连接示例

```python
# 创建通信模块实例
serial_comm = SerialCommunicator(log_manager, config_manager)
can_comm = CanBusCommunicator(log_manager, config_manager)

# 连接信号 - 串口到CAN
serial_comm.raw_frame_received.connect(on_serial_data_received)

def on_serial_data_received(port_name: str, data: bytes):
    # 转发给CAN通信器处理
    can_comm.process_serial_data(data)

# 连接信号 - CAN到串口
can_comm.serial_data_to_send.connect(on_serial_data_to_send)

def on_serial_data_to_send(data: bytes):
    # 转发给具体的串口发送
    serial_comm.send_bytes(port_name, data)

# 连接帧列表更新信号
serial_comm.frame_lists_updated.connect(on_serial_frame_lists_updated)
can_comm.can_frame_lists_updated.connect(on_can_frame_lists_updated)

# 连接CAN帧信号
can_comm.can_frame_received.connect(on_can_frame_received)
can_comm.can_frame_sent.connect(on_can_frame_sent)
```

## 数据格式

### 串口数据格式

```
AT + [CANID(4字节) + Len(1字节) + Data(N字节)] + \r\n
```

### CAN 帧格式

- **仲裁 ID**: 从串口数据的 CANID 字段解析（右移 3 位）
- **数据长度**: 从串口数据的 Len 字段获取
- **数据**: 从串口数据的 Data 字段提取
- **扩展 ID**: 默认为 True

## 帧列表管理

### 串口帧列表

每个串口帧记录包含：

```python
{
    'timestamp': float,      # 时间戳
    'port_name': str,        # 端口名称
    'data': bytes,          # 原始数据
    'data_hex': str         # 十六进制字符串
}
```

### CAN 帧列表

每个 CAN 帧记录包含：

```python
{
    'timestamp': float,           # 时间戳
    'port_name': str,            # 端口名称
    'arbitration_id': int,       # 仲裁ID
    'data': bytes,              # 数据字节
    'data_hex': str,            # 十六进制字符串
    'is_extended_id': bool,     # 是否为扩展ID
    'direction': str            # 方向：'sent' 或 'received'
}
```

## 配置管理

### 端口配置

```python
# 配置串口转CAN的端口
can_comm.configure_port('COM1', 'deepmotor', 'DeepMotor1')
```

### 帧列表配置

```python
# 设置最大帧列表长度
serial_comm.set_max_frame_list_size(1000)
can_comm.set_max_can_frame_list_size(1000)
```

## 优势

1. **职责分离**: 每个模块专注于自己的核心功能
2. **抽象化设计**: CAN 层不处理硬件相关的端口映射和 DBC 管理
3. **信号驱动**: 通过 Qt 信号实现松耦合的模块间通信
4. **独立管理**: 每个模块独立管理自己的帧列表
5. **易于扩展**: 可以轻松添加新的通信协议或设备类型
6. **便于调试**: 可以独立监控串口和 CAN 层的通信状态
7. **UI 友好**: 提供清晰的信号接口，便于 UI 层显示帧数据
8. **高层处理**: DBC 解析和端口映射在更高层处理，架构更清晰

## 使用示例

运行演示脚本查看完整的使用示例：

```bash
cd deepwin/services/hardware_communication
python demo_refactored_architecture.py
```

## 下一步计划

1. 在协调器中集成新的架构
2. 实现 UI 中的串口帧和 CAN 帧显示
3. 添加帧数据的过滤和搜索功能
4. 支持帧数据的导出和保存功能
