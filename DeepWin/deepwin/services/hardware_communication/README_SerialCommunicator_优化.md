# SerialCommunicator 优化说明

## 优化概述

本次优化为 `SerialCommunicator` 类添加了发送和接收帧的列表管理功能，以支持上位机显示发送及接收的帧数据。

## 新增功能

### 1. 帧列表管理

- **发送帧列表** (`_sent_frames`): 记录所有发送的帧数据
- **接收帧列表** (`_received_frames`): 记录所有接收的帧数据
- **默认长度**: 1000 帧（可配置）
- **先进先出机制**: 使用 `collections.deque` 实现，超过最大长度时自动删除最旧的帧

### 2. 帧数据结构

每个帧记录包含以下信息：

```python
frame_info = {
    'timestamp': time.time(),    # 时间戳
    'port_name': str,           # 端口名称
    'data': bytes,              # 原始数据
    'data_hex': str             # 十六进制字符串
}
```

### 3. 新增信号

- **`frame_lists_updated`**: 当发送或接收帧后触发，用于通知 UI 更新

### 4. 新增方法

#### 帧列表管理方法

- **`clear_frame_lists()`**: 清空发送和接收帧列表
- **`get_sent_frames()`**: 获取发送帧列表的副本
- **`get_received_frames()`**: 获取接收帧列表的副本
- **`get_frame_lists_info()`**: 获取帧列表的统计信息
- **`set_max_frame_list_size(size)`**: 设置帧列表的最大长度

#### 方法详细说明

##### `clear_frame_lists()`

```python
def clear_frame_lists(self):
    """清空发送和接收帧列表"""
```

- 清空所有发送和接收的帧记录
- 发送 `frame_lists_updated` 信号通知 UI 更新

##### `get_frame_lists_info()`

```python
def get_frame_lists_info(self) -> Dict[str, Any]:
    """获取帧列表信息"""
```

返回包含以下信息的字典：

- `sent_frames_count`: 发送帧数量
- `received_frames_count`: 接收帧数量
- `max_list_size`: 最大列表长度
- `sent_frames`: 发送帧列表
- `received_frames`: 接收帧列表

##### `set_max_frame_list_size(size)`

```python
def set_max_frame_list_size(self, size: int):
    """设置帧列表的最大长度"""
```

- 动态调整帧列表的最大长度
- 如果新长度小于当前帧数量，会保留最新的帧

## 使用示例

### 基本使用

```python
from deepwin.services.hardware_communication.serial_communicator import SerialCommunicator

# 创建实例
serial_comm = SerialCommunicator(log_manager, config_manager)

# 连接信号
serial_comm.frame_lists_updated.connect(on_frame_lists_updated)

# 获取帧列表信息
info = serial_comm.get_frame_lists_info()
print(f"发送帧: {info['sent_frames_count']}, 接收帧: {info['received_frames_count']}")

# 清空列表
serial_comm.clear_frame_lists()

# 设置最大长度
serial_comm.set_max_frame_list_size(500)
```

### UI 集成示例

```python
def on_frame_lists_updated(self):
    """帧列表更新回调"""
    info = self.serial_comm.get_frame_lists_info()

    # 更新发送框
    self.update_send_frame_display(info['sent_frames'])

    # 更新接收框
    self.update_receive_frame_display(info['received_frames'])

def update_send_frame_display(self, frames):
    """更新发送帧显示"""
    for frame in frames:
        timestamp = time.strftime('%H:%M:%S', time.localtime(frame['timestamp']))
        display_text = f"[{timestamp}] {frame['port_name']} -> {frame['data_hex']}"
        # 添加到UI控件中

def update_receive_frame_display(self, frames):
    """更新接收帧显示"""
    for frame in frames:
        timestamp = time.strftime('%H:%M:%S', time.localtime(frame['timestamp']))
        display_text = f"[{timestamp}] {frame['port_name']} <- {frame['data_hex']}"
        # 添加到UI控件中
```

## 性能考虑

1. **内存使用**: 使用 `deque` 数据结构，内存效率高
2. **自动清理**: 超过最大长度时自动删除旧帧，避免内存泄漏
3. **信号优化**: 只在帧列表更新时发送信号，避免频繁的 UI 更新

## 兼容性

- 完全向后兼容，不影响现有功能
- 所有新增功能都是可选的
- 现有代码无需修改即可继续使用

## 演示脚本

运行 `demo_serial_communicator.py` 可以查看所有新功能的演示：

```bash
cd deepwin/services/hardware_communication
python demo_serial_communicator.py
```

## 下一步计划

1. 在协调器中连接 `frame_lists_updated` 信号
2. 实现 UI 中的发送框和接收框显示
3. 添加帧数据的过滤和搜索功能
4. 支持帧数据的导出功能
