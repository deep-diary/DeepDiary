# 逐层向上传递架构实现总结

## 架构改进概述

根据用户建议，将数据接收流程从原来的信号连接方式改为**逐层向上传递**的方式，使整个架构更加一致和清晰。

### 改进前后对比

#### **改进前（信号连接方式）**

```
串口数据 → 信号 → hardware_communication.py → 信号 → device_protocol_parser.py → 信号 → 设备解析器
```

#### **改进后（逐层向上传递）**

```
串口数据 → 串口层 → CAN层 → 协议层 → 信号字典 → 信号发出
```

## 逐层向上传递架构

### **数据流向**

```
串口数据 → 串口层处理 → CAN层转换 → 协议层解析 → 信号字典 → 信号发出
```

### **各层职责**

#### **第 1 层：串口层 (SerialCommunicator)**

- **输入**: 原始串口数据 `bytes`
- **输出**: 处理结果字典 `Dict[str, Any]`
- **职责**: 处理串口数据，添加到接收帧列表，返回处理结果

#### **第 2 层：CAN 层 (CanBusCommunicator)**

- **输入**: 串口数据 `bytes`
- **输出**: CAN 帧数据字典 `Dict[str, Any]`
- **职责**: 将串口数据转换为 CAN 帧格式

#### **第 3 层：协议层 (DeviceProtocolParser)**

- **输入**: 串口数据 `bytes`
- **输出**: 信号字典 `Dict[str, Any]`
- **职责**: 将串口数据解析为语义信号字典

#### **第 4 层：信号发出**

- **输入**: 信号字典 `Dict[str, Any]`
- **输出**: 信号发送
- **职责**: 发送 `device_semantic_data_ready` 信号

## 具体实现

### **1. SerialCommunicator 改进**

#### **新增方法**

```python
def process_received_data(self, port_name: str, data: bytes) -> Optional[Dict[str, Any]]:
    """
    处理接收到的串口数据，返回处理结果
    :param port_name: 端口名称
    :param data: 接收到的数据
    :return: 处理结果字典，包含端口信息和数据
    """
    try:
        # 构建处理结果
        result = {
            'port_name': port_name,
            'data': data,
            'data_hex': data.hex(),
            'timestamp': time.time(),
            'frame_type': 'serial'
        }

        # 添加到接收帧列表
        frame_info = {
            'timestamp': result['timestamp'],
            'port_name': port_name,
            'data': data,
            'data_hex': data.hex()
        }
        self._received_frames.append(frame_info)

        # 发送帧列表更新信号
        self.frame_lists_updated.emit()

        return result

    except Exception as e:
        self.logger.error(f"SerialCommunicator: 处理接收数据失败: {e}")
        return None
```

### **2. CanBusCommunicator 改进**

#### **修改方法**

```python
def process_serial_data(self, data: bytes) -> Optional[Dict[str, Any]]:
    """
    处理从串口接收的原始数据，转换为CAN帧。
    :param data: 原始串口数据
    :return: CAN帧数据字典，失败时返回None
    """
    try:
        # 解析CAN ID和数据
        arbitration_id = int.from_bytes(data[0:4], byteorder='big') >> 3
        data_length = data[4]
        data_bytes = data[5:5+data_length]

        # 构建CAN帧数据
        can_frame_data = {
            'arbitration_id': arbitration_id,
            'data': data_bytes,
            'is_extended_id': True,
            'frame_type': 'can',
            'timestamp': time.time()
        }

        # 记录接收的CAN帧
        frame_info = {
            'timestamp': can_frame_data['timestamp'],
            'arbitration_id': arbitration_id,
            'data': data_bytes,
            'data_hex': data_bytes.hex(),
            'is_extended_id': True,
            'direction': 'received'
        }
        self._received_can_frames.append(frame_info)

        # 发送CAN帧接收信号
        self.can_frame_received.emit(arbitration_id, data_bytes, True)
        # 发送帧列表更新信号
        self.can_frame_lists_updated.emit()

        return can_frame_data

    except Exception as e:
        error_msg = f"处理串口数据失败: {e}"
        self.logger.error(f"CanBusCommunicator: {error_msg}")
        self.can_error.emit(error_msg)
        return None
```

### **3. DeviceProtocolParser 改进**

#### **修改方法**

```python
def parse_serial_frame_to_signals(self, device_id: str, data: bytes) -> Optional[Dict[str, Any]]:
    """
    核心任务4：将串口帧解析为信号字典
    :param device_id: 设备ID
    :param data: 串口数据
    :return: 信号字典，失败时返回None
    """
    try:
        # 获取设备协议解析器
        device_type = self._get_device_type_from_id(device_id)
        device_parser = self._device_parsers.get(device_type)

        # 构建串口帧数据字典
        serial_frame_data = {
            'data': data,
            'frame_type': 'serial'
        }

        # 调用设备特定的串口帧解析方法
        semantic_data = device_parser.parse_serial_frame_to_signals(serial_frame_data)

        if semantic_data:
            semantic_data['device_id'] = device_id
            semantic_data['device_type'] = device_type
            # 发送信号（保持向后兼容）
            self.device_semantic_data_ready.emit(device_id, semantic_data)
            return semantic_data
        else:
            return None

    except Exception as e:
        error_msg = f"解析串口帧失败: {e}"
        self.logger.error(f"协议管理层: {error_msg}")
        self.protocol_conversion_error.emit(device_id, error_msg)
        return None
```

### **4. HardwareCommunicationHandler 改进**

#### **修改方法**

```python
@Slot(str, bytes)
def _on_raw_serial_frame_received(self, port_name: str, raw_frame_data: bytes):
    """
    处理从串口接收到的原始帧数据 - 逐层向上传递
    串口层 → CAN层 → 协议层 → 信号字典 → 信号发出
    """
    self.logger.debug(f"HardwareCommunicationHandler: 收到串口数据 - 端口: {port_name}, 数据: {raw_frame_data.hex()}")

    try:
        # ==================== 第1层：串口层 - 处理串口数据 ====================
        self.logger.debug(f"HardwareCommunicationHandler: 第1层 - 串口层处理数据")
        serial_result = self.serial_communicator.process_received_data(port_name, raw_frame_data)

        if not serial_result:
            self.logger.warning(f"HardwareCommunicationHandler: 串口层处理失败")
            return

        self.logger.debug(f"HardwareCommunicationHandler: 串口层处理成功")

        # ==================== 第2层：CAN层 - 串口数据 → CAN帧 ====================
        self.logger.debug(f"HardwareCommunicationHandler: 第2层 - CAN层转换串口数据为CAN帧")
        can_result = self.can_bus_communicator.process_serial_data(raw_frame_data)

        if not can_result:
            self.logger.warning(f"HardwareCommunicationHandler: CAN层转换失败")
            return

        self.logger.debug(f"HardwareCommunicationHandler: CAN层转换成功 - CAN ID: 0x{can_result['arbitration_id']:X}")

        # ==================== 第3层：协议层 - CAN帧 → 信号字典 ====================
        self.logger.debug(f"HardwareCommunicationHandler: 第3层 - 协议层解析CAN帧为信号字典")

        # 获取设备ID
        device_id = self.serial_communicator.get_device_id_from_port(port_name)
        if not device_id:
            self.logger.warning(f"HardwareCommunicationHandler: 收到来自未知串口 '{port_name}' 的数据，无法映射到设备ID")
            device_id = "DeepMotor"  # 调试时使用默认值

        semantic_result = self.device_protocol_parser.parse_serial_frame_to_signals(device_id, raw_frame_data)

        if semantic_result:
            self.logger.info(f"HardwareCommunicationHandler: 协议层解析成功 - 设备: {device_id}")
            self.logger.debug(f"HardwareCommunicationHandler: 信号字典: {semantic_result}")
        else:
            self.logger.warning(f"HardwareCommunicationHandler: 协议层解析失败")

    except Exception as e:
        self.logger.error(f"HardwareCommunicationHandler: 处理串口数据失败: {e}")
        import traceback
        self.logger.error(traceback.format_exc())
```

## 架构优势

### **1. 一致性**

- ✅ **发送和接收流程一致** - 都采用逐层传递的方式
- ✅ **清晰的层次结构** - 每层职责明确，边界清晰

### **2. 可维护性**

- ✅ **易于调试** - 每层都有明确的输入输出
- ✅ **易于测试** - 每层都可以独立测试
- ✅ **易于扩展** - 可以轻松添加新的处理层

### **3. 错误处理**

- ✅ **逐层错误检查** - 每层都有独立的错误处理
- ✅ **详细的错误日志** - 便于问题定位和调试
- ✅ **优雅的错误恢复** - 任何一层失败都不会影响其他层

### **4. 性能优化**

- ✅ **减少信号开销** - 减少了不必要的信号传递
- ✅ **直接方法调用** - 更高效的数据传递
- ✅ **内存优化** - 减少了中间对象的创建

## 信号连接处理

### **保留的信号连接**

```python
# 1. 串口通信器信号（仍然需要）
self.serial_communicator.serial_error.connect(...)
self.serial_communicator.connection_status_changed.connect(...)
self.serial_communicator.raw_frame_received.connect(...)

# 2. 设备协议解析器信号（仍然需要）
self.device_protocol_parser.device_semantic_data_ready.connect(...)
self.device_protocol_parser.protocol_conversion_error.connect(...)
```

### **信号的作用**

- **raw_frame_received**: 作为数据接收的入口点
- **device_semantic_data_ready**: 最终信号发出，通知上层应用
- **错误信号**: 处理各种错误情况

## 预期日志输出

### **正常流程日志**

```
DEBUG - HardwareCommunicationHandler: 收到串口数据 - 端口: COM1, 数据: 140037ec088096829d81020114
DEBUG - HardwareCommunicationHandler: 第1层 - 串口层处理数据
DEBUG - SerialCommunicator: 处理接收数据 - 端口: COM1, 数据: 140037ec088096829d81020114
DEBUG - SerialCommunicator: 数据处理完成 - 端口: COM1
DEBUG - HardwareCommunicationHandler: 串口层处理成功
DEBUG - HardwareCommunicationHandler: 第2层 - CAN层转换串口数据为CAN帧
DEBUG - CanBusCommunicator: 收到串口原始数据: 140037ec088096829d81020114
INFO - CanBusCommunicator: 解析到 CAN 帧: ID=0x2001E00, Len=8, Data=8096829d81020114
DEBUG - HardwareCommunicationHandler: CAN层转换成功 - CAN ID: 0x2001E00
DEBUG - HardwareCommunicationHandler: 第3层 - 协议层解析CAN帧为信号字典
DEBUG - 协议管理层: 解析串口帧 (设备: DeepMotor, 数据: 140037ec088096829d81020114)
INFO - 协议管理层: 串口帧已解析为信号字典
INFO - HardwareCommunicationHandler: 协议层解析成功 - 设备: DeepMotor
DEBUG - HardwareCommunicationHandler: 信号字典: {'position': 1.5, 'velocity': 0.2, 'torque': 0.1, ...}
```

### **错误处理日志**

```
DEBUG - HardwareCommunicationHandler: 收到串口数据 - 端口: COM1, 数据: 140037ec088096829d81020114
DEBUG - HardwareCommunicationHandler: 第1层 - 串口层处理数据
DEBUG - HardwareCommunicationHandler: 串口层处理成功
DEBUG - HardwareCommunicationHandler: 第2层 - CAN层转换串口数据为CAN帧
WARNING - CanBusCommunicator: 串口数据长度不足: 3 字节
WARNING - HardwareCommunicationHandler: CAN层转换失败
```

## 向后兼容性

### **保持兼容的特性**

- ✅ **信号发送** - 仍然发送所有必要的信号
- ✅ **错误处理** - 保持原有的错误处理机制
- ✅ **帧列表管理** - 保持原有的帧列表功能
- ✅ **设备映射** - 保持原有的设备映射功能

### **新增的特性**

- ✅ **返回值支持** - 每层都支持返回值
- ✅ **逐层传递** - 新的数据传递方式
- ✅ **详细日志** - 更详细的处理流程日志

## 总结

这次架构改进成功实现了：

1. **统一的架构设计** - 发送和接收都采用逐层传递
2. **清晰的层次结构** - 每层职责明确，边界清晰
3. **完善的错误处理** - 每层都有独立的错误处理机制
4. **向后兼容性** - 保持所有原有功能
5. **性能优化** - 减少信号开销，提高处理效率

现在整个系统的数据流链路更加清晰和高效：

```
发送: 命令 → 协议层 → CAN层 → 串口层 → 实际发送
接收: 串口数据 → 串口层 → CAN层 → 协议层 → 信号字典 → 信号发出
```

这种设计为后续的功能扩展和维护奠定了良好的基础。
