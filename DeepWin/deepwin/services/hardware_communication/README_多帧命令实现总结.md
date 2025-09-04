# 多帧命令实现总结

## 实现概述

根据用户需求，成功实现了多帧命令支持，并优化了代码结构以处理单帧和多帧命令的统一返回格式。同时去掉了 `create_AT_frame()` 调用，因为这是串口转 CAN 协议设置。

## 主要改进

### 1. 协议层多帧命令支持

#### **Protocol2Can 类**

- ✅ 添加了 `create_motor_init_frame(motor_id)` 方法
- ✅ 添加了 `create_motor_init_frame_all(motor_ids)` 方法
- ✅ 去掉了 `create_AT_frame()` 调用
- ✅ 返回格式：`List[Dict[str, Any]]` 每个元素包含 `{arbitration_id, data, is_extended_id}`

#### **Protocol2Serial 类**

- ✅ 添加了 `create_motor_init_frame(motor_id)` 方法
- ✅ 添加了 `create_motor_init_frame_all(motor_ids)` 方法
- ✅ 去掉了 `create_AT_frame()` 调用
- ✅ 返回格式：`List[bytes]` 每个元素为串口帧

### 2. 协议解析器更新

#### **DeepMotorProtocolParser 类**

- ✅ 更新了 `convert_command_to_can_frame` 方法支持多帧命令
- ✅ 返回类型：`Union[Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]]]`
- ✅ 支持 `motor_init` 和 `motor_init_all` 命令
- ✅ 自动识别单帧和多帧命令

### 3. 协议管理层优化

#### **DeviceProtocolParser 类**

- ✅ 更新了 `convert_command_to_can_frame` 方法
- ✅ 支持多帧命令的自动识别和处理
- ✅ 多帧命令时发送所有帧并返回完整帧列表
- ✅ 单帧命令时发送单帧并返回帧数据

### 4. 设备逻辑管理器重构

#### **DeviceLogicManagerHandler 类**

- ✅ 重构了 `_on_device_abstract_command_requested` 方法
- ✅ 添加了 `_process_singleframe_command` 方法
- ✅ 添加了 `_process_multiframe_command` 方法
- ✅ 添加了 `_send_serial_data` 通用方法
- ✅ 支持多帧命令的逐帧处理和帧间延迟

## 架构设计

### 多帧命令处理流程

```
命令 → 协议层 → 多帧CAN数据 → CAN层 → 多帧串口数据 → 串口层 → 逐帧发送
```

### 返回值优化

#### **统一返回格式**

```python
# 单帧命令
return {
    'arbitration_id': 0x1200FD01,
    'data': b'\x17p\x00\x00\x00\x00zD',
    'is_extended_id': True
}

# 多帧命令
return [
    {'arbitration_id': 0x1200FD01, 'data': b'...', 'is_extended_id': True},
    {'arbitration_id': 0x1200FD02, 'data': b'...', 'is_extended_id': True},
    {'arbitration_id': 0x1200FD03, 'data': b'...', 'is_extended_id': True},
    {'arbitration_id': 0x1200FD04, 'data': b'...', 'is_extended_id': True}
]
```

## 关键特性

### 1. **自动类型识别**

```python
if isinstance(can_frame_data, list):
    # 多帧命令处理
    self._process_multiframe_command(can_frame_data, device_id, command_name, params)
else:
    # 单帧命令处理
    self._process_singleframe_command(can_frame_data, device_id, command_name, params)
```

### 2. **多帧命令逐帧处理**

```python
for i, can_frame in enumerate(can_frames):
    # 第2层：CAN层转换
    serial_frame = self.can_bus_communicator.send_can_frame(...)

    # 第3层：串口层发送
    send_success = self.serial_communicator.send_bytes(target_port_name, serial_frame)

    # 帧间延迟
    if i < len(can_frames) - 1:
        time.sleep(0.01)
```

### 3. **完整的错误处理**

- 每层都有独立的错误检查
- 多帧命令中任何一帧失败都会停止处理
- 详细的错误日志和状态反馈

## 支持的命令

### 单帧命令

- `motor_set_speed` - 设置电机速度
- `motor_set_pos` - 设置电机位置
- `motor_set_torque` - 设置电机扭矩
- `motor_enable` - 使能电机
- `motor_disable` - 禁用电机
- `motor_zero` - 零点设置
- `motor_jog` - 点动控制
- `motor_jog_stop` - 停止点动

### 多帧命令

- `motor_init` - 电机初始化（复位 → 零点 → 模式 → 使能）
- `motor_init_all` - 多电机初始化

## 电机初始化序列

### 单电机初始化 (`motor_init`)

```python
[
    create_motor_reset_frame(motor_id),      # 复位
    create_motor_zero_frame(motor_id),       # 零点设置
    create_motor_mode_frame(motor_id, 1),    # 位置模式
    create_motor_enable_frame(motor_id)      # 使能
]
```

### 多电机初始化 (`motor_init_all`)

```python
# 对每个电机执行完整的初始化序列
for motor_id in motor_ids:
    all_frames.extend(create_motor_init_frame(motor_id))
```

## 日志输出示例

### 单帧命令日志

```
INFO - DeviceLogicManagerHandler: 协议层转换成功 - 单帧命令，CAN帧ID: 0x1200FD01
DEBUG - DeviceLogicManagerHandler: 第2层 - CAN层转换CAN帧为串口帧
INFO - DeviceLogicManagerHandler: CAN层转换成功 - 串口帧: 9007e808081770000000007a44
INFO - DeviceLogicManagerHandler: 串口层发送成功 - 端口: COM1
```

### 多帧命令日志

```
INFO - DeviceLogicManagerHandler: 协议层转换成功 - 多帧命令，共 4 帧
INFO - DeviceLogicManagerHandler: 开始处理多帧命令，共 4 帧
DEBUG - DeviceLogicManagerHandler: 处理第 1/4 帧
DEBUG - DeviceLogicManagerHandler: 第 1 帧转换成功 - 串口帧: 9007e808081770000000007a44
DEBUG - DeviceLogicManagerHandler: 处理第 2/4 帧
DEBUG - DeviceLogicManagerHandler: 第 2 帧转换成功 - 串口帧: 9007e808081770000000007a45
...
INFO - DeviceLogicManagerHandler: 多帧命令发送成功 - 端口: COM1
```

## 演示脚本

创建了 `demo_multiframe_commands.py` 演示脚本，包含：

1. **单帧命令演示** - 测试所有单帧命令的转换
2. **多帧命令演示** - 测试多帧命令的转换和处理
3. **直接协议调用演示** - 直接调用协议方法进行测试

### 运行演示

```bash
cd DeepWin\deepwin\services\hardware_communication
conda activate DiaryWin
python demo_multiframe_commands.py
```

## 架构优势

### 1. **向后兼容**

- 现有的单帧命令完全兼容
- 不需要修改现有的调用代码

### 2. **扩展性强**

- 可以轻松添加新的多帧命令
- 支持任意数量的帧

### 3. **错误处理完善**

- 每层都有独立的错误处理
- 多帧命令中任何一帧失败都会停止处理

### 4. **性能优化**

- 帧间延迟避免串口拥堵
- 逐帧处理确保可靠性

### 5. **日志详细**

- 完整的处理流程跟踪
- 便于调试和问题诊断

## 总结

这次实现成功解决了多帧命令的需求，主要特点：

1. ✅ **完整的多帧支持** - 从协议层到设备逻辑层的完整支持
2. ✅ **统一的返回格式** - 单帧和多帧命令的统一处理
3. ✅ **去掉 AT 帧调用** - 移除了串口转 CAN 协议设置
4. ✅ **完善的错误处理** - 每层都有独立的错误处理机制
5. ✅ **详细的日志记录** - 完整的处理流程跟踪
6. ✅ **向后兼容** - 现有代码无需修改
7. ✅ **扩展性强** - 便于添加新的多帧命令

这种设计为后续的功能扩展和维护奠定了良好的基础，是一个成功的多帧命令实现案例。
