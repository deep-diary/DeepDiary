# 新架构设计总结

## 架构优化概述

根据您的需求，我们重新设计了协议管理层架构，实现了以下目标：

1. **协议管理层代码尽可能不动**，新增设备只需在设备协议子层添加代码
2. **统一的协议转换和路由中心**，处理 4 个核心任务
3. **完整的信号传递链路**，支持 CAN 协议和串口协议的统一处理
4. **向后兼容**，保持现有代码的兼容性

## 新架构层次结构

```
应用层 (UI/业务逻辑)
    ↓
协议管理层 (DeviceProtocolParser) - 4个核心任务
    ↓
通信层 (SerialCommunicator + CanBusCommunicator)
    ↓
硬件层 (串口设备)
```

## 协议管理层的 4 个核心任务

### 1. 命令 → CAN 帧

```python
@Slot(str, str, dict)
def convert_command_to_can_frame(self, device_id: str, command_name: str, params: Dict[str, Any]):
    """将抽象命令转换为CAN帧格式"""
```

### 2. 命令 → 串口帧

```python
@Slot(str, str, dict)
def convert_command_to_serial_frame(self, device_id: str, command_name: str, params: Dict[str, Any]):
    """将抽象命令直接转换为串口帧（跳过CAN层）"""
```

### 3. CAN 帧 → 信号字典

```python
@Slot(str, int, bytes, bool)
def parse_can_frame_to_signals(self, device_id: str, arbitration_id: int, data: bytes, is_extended_id: bool):
    """将CAN帧解析为信号字典"""
```

### 4. 串口帧 → 信号字典

```python
@Slot(str, bytes)
def parse_serial_frame_to_signals(self, device_id: str, data: bytes):
    """将串口帧解析为信号字典"""
```

## 完整的信号传递链路

### 接收链路（硬件 → 应用）

```
串口设备 → SerialCommunicator → CanBusCommunicator → DeviceProtocolParser → 上层应用
    ↓              ↓                    ↓                    ↓
原始串口数据 → 串口帧列表 → CAN帧列表 → 信号字典 → 业务语义数据
```

### 发送链路（应用 → 硬件）

```
上层应用 → DeviceProtocolParser → CanBusCommunicator → SerialCommunicator → 串口设备
    ↓              ↓                    ↓                    ↓
抽象命令 → CAN帧/串口帧 → 串口数据 → 串口帧列表 → 硬件设备
```

## 信号连接示例

```python
# 创建通信模块实例
serial_comm = SerialCommunicator(log_manager, config_manager)
can_comm = CanBusCommunicator(log_manager, config_manager)
protocol_parser = DeviceProtocolParser(log_manager, config_manager)

# ==================== 接收链路 ====================
# 串口 → CAN通信器
serial_comm.raw_frame_received.connect(can_comm.process_serial_data)

# CAN通信器 → 协议管理层
can_comm.can_frame_received.connect(protocol_parser.parse_can_frame_to_signals)

# 串口 → 协议管理层（直接路径）
serial_comm.raw_frame_received.connect(protocol_parser.parse_serial_frame_to_signals)

# 协议管理层 → 上层应用
protocol_parser.device_semantic_data_ready.connect(on_device_semantic_data)

# ==================== 发送链路 ====================
# 协议管理层 → CAN通信器
protocol_parser.can_frame_ready.connect(can_comm.send_can_frame)

# 协议管理层 → 串口通信器
protocol_parser.serial_frame_ready.connect(serial_comm.send_bytes)

# CAN通信器 → 串口通信器
can_comm.serial_data_to_send.connect(serial_comm.send_bytes)
```

## 设备协议子层实现

### 基础协议解析器接口

```python
class BaseProtocolParser(QObject):
    # 4个核心任务接口
    def convert_command_to_can_frame(self, command_name: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """将抽象命令转换为CAN帧格式"""

    def convert_command_to_serial_frame(self, command_name: str, params: Dict[str, Any]) -> Optional[bytes]:
        """将抽象命令直接转换为串口帧"""

    def parse_can_frame_to_signals(self, can_frame_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """将CAN帧解析为信号字典"""

    def parse_serial_frame_to_signals(self, serial_frame_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """将串口帧解析为信号字典"""
```

### 设备特定实现示例（DeepMotor）

```python
class DeepMotorProtocolParser(BaseProtocolParser):
    def convert_command_to_can_frame(self, command_name: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """DeepMotor特定的CAN帧转换"""
        command_data = self.deep_motor_mapping.map_and_call(command_name, params)
        return {
            'arbitration_id': 0x140037EC,
            'data': command_data,
            'is_extended_id': True
        }

    def convert_command_to_serial_frame(self, command_name: str, params: Dict[str, Any]) -> Optional[bytes]:
        """DeepMotor特定的串口帧转换"""
        command_data = self.deep_motor_mapping.map_and_call(command_name, params)
        return b'AT' + command_data + b'\r\n'

    # ... 其他方法实现
```

## 新增设备的步骤

### 1. 创建设备协议目录

```
device_protocols/
└── new_device_protocol/
    ├── __init__.py
    ├── new_device_parser.py
    ├── protocol.py
    └── mapping.py
```

### 2. 实现设备协议解析器

```python
class NewDeviceProtocolParser(BaseProtocolParser):
    def __init__(self, log_manager, config_manager, parent=None):
        super().__init__(log_manager, config_manager, parent)
        # 初始化设备特定的协议和映射

    def convert_command_to_can_frame(self, command_name: str, params: Dict[str, Any]):
        # 实现设备特定的CAN帧转换
        pass

    def convert_command_to_serial_frame(self, command_name: str, params: Dict[str, Any]):
        # 实现设备特定的串口帧转换
        pass

    def parse_can_frame_to_signals(self, can_frame_data: Dict[str, Any]):
        # 实现设备特定的CAN帧解析
        pass

    def parse_serial_frame_to_signals(self, serial_frame_data: Dict[str, Any]):
        # 实现设备特定的串口帧解析
        pass
```

### 3. 自动发现和注册

设备协议解析器会自动被 `DeviceProtocolParser` 发现和注册，无需修改协议管理层代码。

## 架构优势

### 1. 职责分离

- **协议管理层**：统一的协议转换和路由中心
- **设备协议子层**：设备特定的协议实现
- **通信层**：硬件通信和数据转换
- **应用层**：业务逻辑和 UI

### 2. 可扩展性

- 新增设备只需在设备协议子层添加代码
- 协议管理层代码尽可能不动
- 支持 CAN 协议和串口协议的统一处理

### 3. 信号驱动

- 完整的信号传递链路
- 松耦合的模块间通信
- 实时的事件通知机制

### 4. 向后兼容

- 保持现有代码的兼容性
- 渐进式迁移到新架构
- 支持多种协议格式

### 5. 易于测试

- 每个层次都可以独立测试
- 清晰的接口定义
- 模拟数据支持

## 使用示例

### 发送命令

```python
# 通过CAN协议发送
protocol_parser.convert_command_to_can_frame("DeepMotor1", "set_motor_speed", {"speed": 1000})

# 直接通过串口发送（跳过CAN层）
protocol_parser.convert_command_to_serial_frame("DeepMotor1", "set_motor_speed", {"speed": 1000})
```

### 接收数据

```python
# 接收CAN帧并解析
protocol_parser.parse_can_frame_to_signals("DeepMotor1", 0x140037EC, data, True)

# 接收串口帧并解析
protocol_parser.parse_serial_frame_to_signals("DeepMotor1", data)
```

## 演示脚本

运行完整信号传递链路演示：

```bash
cd deepwin/services/hardware_communication
python demo_complete_signal_chain.py
```

## 总结

新架构实现了以下目标：

1. ✅ **协议管理层代码尽可能不动**
2. ✅ **统一的协议转换和路由中心**
3. ✅ **4 个核心任务的完整实现**
4. ✅ **完整的信号传递链路**
5. ✅ **支持 CAN 协议和串口协议的统一处理**
6. ✅ **新增设备只需在设备协议子层添加代码**
7. ✅ **向后兼容现有代码**

这个架构为后续的设备扩展和功能增强提供了坚实的基础。
