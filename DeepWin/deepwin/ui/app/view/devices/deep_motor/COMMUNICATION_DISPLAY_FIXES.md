# 通信显示修复总结

## 修复概述

根据用户反馈，我们对 DeepMotor 页面的通信显示功能进行了全面的修复和优化：

## 1. 修复 QTextCursor.End 错误

### 问题描述

- 错误信息：`'PySide6.QtGui.QTextCursor' object has no attribute 'End'`
- 原因：在 PySide6 中，应该使用`QTextCursor.MoveOperation.End`而不是`cursor.End`

### 解决方案

```python
# 修复前
cursor.movePosition(cursor.End)

# 修复后
cursor.movePosition(cursor.MoveOperation.End)
```

### 修改文件

- `components/communication_widget.py`

## 2. 修复滚动条位置问题

### 问题描述

- 新数据添加后，滚动条会跑到上面，导致最新数据被挤掉
- 用户无法看到最新的通信数据

### 解决方案

```python
# 使用更好的滚动方法
if self.auto_scroll_switch.isChecked():
    # 使用ensureCursorVisible确保最新内容可见
    text_edit.ensureCursorVisible()
    # 滚动到最底部
    scrollbar = text_edit.verticalScrollBar()
    scrollbar.setValue(scrollbar.maximum())
```

### 修改文件

- `components/communication_widget.py`

## 3. 提高发送框和接收框高度

### 问题描述

- 通信监控的发送框和接收框高度太小，显示内容有限

### 解决方案

```python
# 将最大高度从300px提高到600px
scroll_area.setMaximumHeight(600)
```

### 修改文件

- `components/communication_widget.py`

## 4. 修改电机命令显示格式

### 问题描述

- 显示的是命令字符串的字节，而不是实际发送的串口数据
- 期望显示经过串口层发送出去的实际数据

### 解决方案

- 移除了主页面的模拟数据显示逻辑
- 连接到实际的串口通信器信号
- 显示真实的串口发送数据

### 实现细节

1. **移除模拟数据**：从`_on_motor_command_requested`方法中移除模拟数据显示
2. **连接实际信号**：通过`HardwareCommunicationHandler`连接串口发送信号
3. **显示真实数据**：显示`self._sent_frames`中的实际串口数据

### 修改文件

- `deep_motor_page.py`
- `hardware_communication.py`

## 5. 修复多帧命令显示问题

### 问题描述

- 发送初始化命令时，实际有四帧数据，但只显示了一帧
- 用户无法看到完整的命令内容

### 解决方案

1. **增强串口通信器**：

   - 修改`send_bytes`方法，支持传递命令信息
   - 添加`get_sent_frame_info`方法获取帧信息

2. **增强设备逻辑管理器**：

   - 在调用`send_bytes`时传递命令信息
   - 包含命令名称、帧索引、总帧数、参数等

3. **优化显示格式**：
   - 单帧命令：`电机命令 - motor_enable(motor_id=6)`
   - 多帧命令：`电机命令 - motor_init(motor_id=6) [帧 1/4]`

### 实现细节

```python
# 串口通信器增强
def send_bytes(self, port_name: str, data: bytes, command_info: Optional[Dict] = None):
    # 记录命令信息
    frame_info = {
        'timestamp': time.time(),
        'port_name': port_name,
        'data': data,
        'data_hex': data.hex()
    }
    if command_info:
        frame_info.update(command_info)
    self._sent_frames.append(frame_info)

# 设备逻辑管理器增强
command_info = {
    'command': command_name,
    'frame_index': i + 1,
    'total_frames': len(can_frames),
    'params': params
}
send_success = self.serial_communicator.send_bytes(target_port_name, serial_frame, command_info)
```

### 修改文件

- `serial_communicator.py`
- `device_logic_manager.py`
- `hardware_communication.py`

## 技术改进总结

### 1. 数据流优化

- **之前**：显示模拟的命令字符串字节
- **现在**：显示真实的串口发送数据

### 2. 多帧支持

- **之前**：只显示一帧数据
- **现在**：显示所有发送的帧，包含帧索引信息

### 3. 信息丰富度

- **之前**：简单的命令名称
- **现在**：命令名称 + 参数 + 帧信息

### 4. 用户体验

- **之前**：滚动条位置错误，高度不足
- **现在**：自动滚动到最新数据，高度翻倍

## 显示格式示例

### 单帧命令

```
[18:58:41.946] 电机命令 - motor_enable(motor_id=6)
HEX: 2007E830080000000000000000
ASCII: ...............
```

### 多帧命令

```
[18:58:41.946] 电机命令 - motor_init(motor_id=6) [帧 1/4]
HEX: 2007E830080000000000000000
ASCII: ...............
--------------------------------------------------
[18:58:41.956] 电机命令 - motor_init(motor_id=6) [帧 2/4]
HEX: 2007E830080000000000000001
ASCII: ...............
```

## 测试验证

修复完成后，用户应该能够：

1. 看到真实的串口发送数据（而不是命令字符串）
2. 看到多帧命令的所有帧（如初始化的 4 帧）
3. 享受更高的显示框和正确的滚动行为
4. 获得更详细的命令信息（包含参数和帧索引）

## 后续建议

1. **性能优化**：可以考虑对大量通信数据进行分页显示
2. **过滤功能**：添加按命令类型或时间范围过滤的功能
3. **导出功能**：支持将通信数据导出为文件
4. **实时统计**：显示通信速率、错误率等统计信息
