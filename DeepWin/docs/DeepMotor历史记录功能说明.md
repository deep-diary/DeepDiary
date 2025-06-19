# DeepMotor 历史记录功能说明

## 概述

DeepMotor 类现在支持历史记录功能，可以自动保存每次状态更新的历史数据，便于后续进行曲线绘制和数据分析。

## 功能特性

### 1. 自动历史记录

- 每次调用 `update_state_from_semantic_data()` 时自动保存状态快照
- 每个历史记录包含完整的状态信息和时间戳
- 支持配置历史记录长度，默认 100 条记录

### 2. 历史记录管理

- 自动维护历史记录长度限制
- 当记录数超过限制时，自动移除最旧的记录
- 支持动态调整历史记录长度

### 3. 数据查询功能

- 获取完整历史记录
- 获取特定字段的历史数据（用于曲线绘制）
- 按时间范围查询历史记录
- 获取最近 N 条记录

## 配置说明

### 配置文件设置

在 `config/config.json` 中添加以下配置：

```json
{
  "device_settings": {
    "deepmotor_history_length": 100
  }
}
```

- `deepmotor_history_length`: 历史记录的最大长度，默认值为 100

## API 接口

### 初始化

```python
from src.app_logic.device_logic_manager.devices.deep_motor.deep_motor import DeepMotor
from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager

# 初始化管理器
log_manager = LogManager()
config_manager = ConfigManager(log_manager, 'config/config.json')

# 创建 DeepMotor 实例
motor = DeepMotor("DeepMotor1", log_manager, config_manager)
```

### 历史记录查询方法

#### 1. 获取完整历史记录

```python
history = motor.get_state_history()
# 返回: List[Dict[str, Any]] - 包含时间戳的完整历史记录列表
```

#### 2. 获取特定字段的历史数据

```python
position_history = motor.get_field_history('position')
velocity_history = motor.get_field_history('velocity')
temperature_history = motor.get_field_history('temperature')
torque_history = motor.get_field_history('torque')

# 返回: List[tuple] - 每个元素为 (timestamp, value) 元组
# 例如: [(1750320795.03927, 50.0), (1750320795.139953, 50.902), ...]
```

#### 3. 按时间范围查询

```python
start_time = 1750320795.0
end_time = 1750320796.0
time_range_history = motor.get_time_range_history(start_time, end_time)
# 返回: List[Dict[str, Any]] - 指定时间范围内的历史记录
```

#### 4. 获取最近的历史记录

```python
recent_history = motor.get_recent_history(10)  # 获取最近10条记录
# 返回: List[Dict[str, Any]] - 最近N条历史记录
```

#### 5. 获取历史记录统计信息

```python
history_length = motor.get_state_history_length()  # 当前历史记录数量
```

### 历史记录管理方法

#### 1. 动态设置历史记录长度

```python
motor.set_history_length(200)  # 设置为200条记录
```

#### 2. 清空历史记录

```python
motor.clear_history()
```

## 使用示例

### 基本使用

```python
# 模拟状态更新
semantic_data = {
    "position": 100.0,
    "velocity": 20.0,
    "temperature": 30.0,
    "torque": 1.0,
    "error_code": 0,
    "connection_status": "Connected"
}

# 更新状态（会自动保存到历史记录）
motor.update_state_from_semantic_data(semantic_data)

# 获取位置历史数据用于绘制曲线
position_data = motor.get_field_history('position')
timestamps = [p[0] for p in position_data]
positions = [p[1] for p in position_data]

# 现在可以使用 timestamps 和 positions 进行曲线绘制
```

### 曲线绘制示例

```python
import matplotlib.pyplot as plt

# 获取各字段的历史数据
position_history = motor.get_field_history('position')
velocity_history = motor.get_field_history('velocity')
temperature_history = motor.get_field_history('temperature')

# 提取时间和数据
times = [p[0] for p in position_history]
positions = [p[1] for p in position_history]
velocities = [v[1] for v in velocity_history]
temperatures = [t[1] for t in temperature_history]

# 创建子图
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8))

# 绘制位置曲线
ax1.plot(times, positions, 'b-', label='Position')
ax1.set_ylabel('Position')
ax1.legend()
ax1.grid(True)

# 绘制速度曲线
ax2.plot(times, velocities, 'r-', label='Velocity')
ax2.set_ylabel('Velocity')
ax2.legend()
ax2.grid(True)

# 绘制温度曲线
ax3.plot(times, temperatures, 'g-', label='Temperature')
ax3.set_ylabel('Temperature')
ax3.set_xlabel('Time')
ax3.legend()
ax3.grid(True)

plt.tight_layout()
plt.show()
```

### 数据导出

```python
import csv

# 导出历史记录为CSV文件
history = motor.get_state_history()
with open('motor_history.csv', 'w', newline='', encoding='utf-8') as f:
    if history:
        writer = csv.DictWriter(f, fieldnames=history[0].keys())
        writer.writeheader()
        writer.writerows(history)
```

## 注意事项

1. **内存使用**: 历史记录存储在内存中，记录数量过多可能影响性能
2. **时间戳**: 每个历史记录都包含时间戳，便于进行时间序列分析
3. **数据完整性**: 历史记录包含完整的状态信息，便于后续分析
4. **配置管理**: 历史记录长度可以通过配置文件动态调整

## 性能优化建议

1. 根据实际需求设置合适的历史记录长度
2. 定期清理不需要的历史记录
3. 对于长时间运行的应用，考虑将历史记录持久化到数据库

## 扩展功能

未来可以考虑添加以下功能：

- 历史记录持久化到数据库
- 历史记录压缩和归档
- 实时历史记录可视化
- 历史记录数据分析和统计
