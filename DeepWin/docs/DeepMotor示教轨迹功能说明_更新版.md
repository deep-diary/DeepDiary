# DeepMotor 示教轨迹功能说明

## 1. 功能概述

DeepMotor 示教轨迹功能允许用户录制、存储、规划和播放电机的运动轨迹。该功能支持实时示教录制、轨迹规划优化、可视化显示和精确播放。系统提供完整的自动化工作流，用户无需手动选择轨迹，提升了操作效率。

## 2. 系统架构

### 2.1 核心组件

- **TeachingTrajectoryManager**: 示教轨迹管理器，负责轨迹的录制、存储、规划和播放
- **RobotTrajectory**: 轨迹规划器，提供五次多项式和三次样条等轨迹规划算法
- **DeviceLogicManager**: 设备逻辑管理器，协调示教功能与设备控制
- **Coordinator**: 协调器，处理轨迹播放命令和设备控制信号
- **DeepMotorPage**: UI 界面，提供示教控制和轨迹可视化
- **GuiManager**: GUI 管理器，作为协调器与 UI 界面之间的桥梁

### 2.2 数据流架构

```
UI界面 (DeepMotorPage)
    ↓ 用户操作信号
协调器 (Coordinator)
    ↓ 设备控制信号
设备逻辑管理器 (DeviceLogicManager)
    ↓ 轨迹管理信号
示教轨迹管理器 (TeachingTrajectoryManager)
    ↓ 轨迹规划
轨迹规划器 (RobotTrajectory)
    ↓ 轨迹播放信号
设备控制 (DeepMotor)
```

### 2.3 详细软件架构

#### 2.3.1 文件结构

```
DeepWin/src/
├── app_logic/
│   ├── device_logic_manager/
│   │   ├── devices/
│   │   │   └── deep_motor/
│   │   │       ├── deep_motor.py              # DeepMotor设备逻辑
│   │   │       └── teaching_trajectory_manager.py  # 示教轨迹管理器
│   │   └── manager.py                         # 设备逻辑管理器
│   └── core_manager/
│       └── coordinator.py                     # 协调器
├── ui/app/view/
│   └── device_pages.py                        # DeepMotor UI界面
└── services/
    └── hardware_communication/
        └── device_protocols/
            └── deep_motor_protocol/
                └── deep_motor_parser.py        # 设备协议解析
```

#### 2.3.2 核心类职责

**DeepMotorPage (UI 界面)**

- 提供示教控制按钮和轨迹可视化
- 管理参数选择和曲线显示
- 发送用户操作信号到协调器
- 接收并显示设备状态和轨迹数据

**Coordinator (协调器)**

- 接收 UI 信号并转发到相应的处理器
- 管理设备状态更新和历史数据请求
- 协调示教功能的开始、结束和执行
- 处理轨迹数据请求和播放命令

**DeviceLogicManager (设备逻辑管理器)**

- 管理所有设备的逻辑状态
- 转发设备控制命令
- 处理设备状态更新
- 协调示教功能与设备控制

**TeachingTrajectoryManager (示教轨迹管理器)**

- 管理轨迹的录制、存储和加载
- 执行轨迹规划算法
- 提供轨迹播放功能
- 处理轨迹文件的序列化和反序列化

**DeepMotor (设备逻辑)**

- 管理设备状态和历史数据
- 处理设备控制命令
- 提供历史数据查询接口
- 管理数据缓存和过滤

### 2.4 信号传递机制

#### 2.4.1 UI 到协调器的信号

**DeepMotorPage 发出的信号:**

```python
# 示教相关信号
start_teaching_requested = Signal(str, int)      # (设备名, motor_id)
stop_teaching_requested = Signal(str)            # (设备名)
execute_teaching_requested = Signal(str, str, bool, int)  # (设备名, 轨迹名, 是否使用规划轨迹, motor_id)

# 轨迹管理信号
request_trajectory_data = Signal(str, str)       # (设备名, 轨迹名)
request_trajectory_list = Signal(str)            # (设备名)
replan_requested = Signal(str, str, float)       # (设备名, 轨迹名, 新时长)
restore_default_requested = Signal(str, str)     # (设备名, 轨迹名)
delete_trajectory_requested = Signal(str, str)   # (设备名, 轨迹名)

# 历史数据信号
request_history_data = Signal(str, str)          # (设备名, 参数名)
request_sim_data = Signal(str)                   # (设备名)
```

#### 2.4.2 协调器到设备逻辑的信号

**Coordinator 发出的信号:**

```python
# 设备控制信号
device_command = Signal(str, str)                # (设备名, 命令)
start_teaching = Signal(str, int)                # (设备名, motor_id)
stop_teaching = Signal(str)                      # (设备名)
execute_trajectory = Signal(str, str, bool, int) # (设备名, 轨迹名, 是否使用规划轨迹, motor_id)

# 数据请求信号
request_trajectory_data = Signal(str, str)       # (设备名, 轨迹名)
request_trajectory_list = Signal(str)            # (设备名)
request_history_data = Signal(str, str)          # (设备名, 参数名)
```

#### 2.4.3 设备逻辑到 UI 的信号

**Coordinator 接收并转发到 UI 的信号:**

```python
# 设备状态信号
device_status_updated = Signal(str, dict)        # (设备名, 状态字典)
device_data_updated = Signal(str, dict)          # (设备名, 数据字典)

# 轨迹相关信号
trajectory_list_updated = Signal(str, list)      # (设备名, 轨迹列表)
trajectory_data_updated = Signal(str, dict)      # (设备名, 轨迹数据)
trajectory_execution_progress = Signal(str, dict) # (设备名, 执行进度)
trajectory_execution_finished = Signal(str)      # (设备名)
trajectory_execution_error = Signal(str, str)    # (设备名, 错误信息)

# 历史数据信号
history_data_updated = Signal(str, dict)         # (设备名, 历史数据)
```

#### 2.4.4 信号连接关系

**在 Coordinator 中的信号连接:**

```python
# UI信号连接到设备逻辑
self.gui_manager.deep_motor_page.start_teaching_requested.connect(
    lambda device, motor_id: self._handle_start_teaching(device, motor_id))
self.gui_manager.deep_motor_page.stop_teaching_requested.connect(
    lambda device: self._handle_stop_teaching(device))
self.gui_manager.deep_motor_page.execute_teaching_requested.connect(
    lambda device, trajectory, use_planned, motor_id: self._handle_execute_teaching(device, trajectory, use_planned, motor_id))

# 设备逻辑信号连接到UI
self.device_logic_manager.device_status_updated.connect(
    lambda device_id, status: self._handle_device_status_update(device_id, status))
self.device_logic_manager.trajectory_list_updated.connect(
    lambda device_id, trajectory_list: self._handle_trajectory_list_update(device_id, trajectory_list))
self.device_logic_manager.trajectory_data_updated.connect(
    lambda device_id, trajectory_data: self._handle_trajectory_data_update(device_id, trajectory_data))
```

### 2.5 数据流详细说明

#### 2.5.1 示教录制数据流

1. **用户操作**: 点击"开始示教"按钮
2. **UI 信号**: `start_teaching_requested.emit("DeepMotor", motor_id)`
3. **协调器处理**: `_handle_start_teaching(device, motor_id)`
4. **设备控制**: 发送电机失能命令
5. **轨迹管理**: 启动轨迹录制模式
6. **数据采集**: 实时记录电机位置和速度
7. **数据过滤**: 应用时间间隔和位置变化过滤
8. **轨迹保存**: 自动保存轨迹文件
9. **UI 更新**: 更新轨迹列表和可视化显示

#### 2.5.2 轨迹播放数据流

1. **用户操作**: 点击"执行示教"按钮
2. **UI 信号**: `execute_teaching_requested.emit(device, trajectory, use_planned, motor_id)`
3. **协调器处理**: `_handle_execute_teaching(device, trajectory, use_planned, motor_id)`
4. **轨迹加载**: 从文件加载轨迹数据
5. **轨迹规划**: 如果需要，执行轨迹规划算法
6. **播放启动**: 启动播放定时器
7. **命令发送**: 按时间间隔发送位置控制命令
8. **进度更新**: 实时更新播放进度
9. **播放完成**: 发送完成信号并更新 UI 状态

#### 2.5.3 历史数据显示数据流

1. **参数切换**: 用户选择不同的参数
2. **数据请求**: `request_history_data.emit(device, param)`
3. **协调器转发**: 转发到设备逻辑管理器
4. **数据查询**: 从设备历史数据缓存中查询
5. **数据返回**: 返回 DataFrame 格式的历史数据
6. **UI 更新**: 更新历史曲线显示
7. **定时刷新**: 定时器定期刷新曲线数据

## 3. 功能详细说明

### 3.1 示教录制

#### 3.1.1 录制流程

1. 用户点击"开始示教"按钮
2. 系统发送电机失能命令，确保安全
3. 启动示教模式，开始记录轨迹点
4. 实时记录电机位置和速度数据
5. 用户点击"结束示教"按钮
6. 系统自动保存轨迹并更新 UI 显示

#### 3.1.2 自动化工作流

- **自动轨迹选择**: 示教结束后自动选中新保存的轨迹
- **自动 UI 更新**: 轨迹列表自动更新，无需手动刷新
- **自动可视化**: 自动切换到轨迹视图并显示规划结果
- **启动优化**: 程序启动时自动选中最新的轨迹

#### 3.1.3 数据过滤机制

- **时间间隔过滤**: 最小时间间隔 0.1 秒
- **位置变化过滤**: 最小位置变化 0.01 度
- **速度变化过滤**: 最小速度变化 0.01 度/秒
- **重复数据过滤**: 避免记录相同的位置和速度点

#### 3.1.4 轨迹文件格式

```json
{
  "device_id": "DeepMotor",
  "created_time": "2025-06-21T08:45:39.623070",
  "points": [
    {
      "timestamp": 1750466735.1530411,
      "type": "start",
      "message": "示教开始"
    },
    {
      "timestamp": 1750466737.0908213,
      "type": "point",
      "position": 12.56,
      "velocity": 0.49
    },
    {
      "timestamp": 1750466739.6230702,
      "type": "end",
      "message": "示教结束"
    }
  ]
}
```

### 3.2 轨迹规划

#### 3.2.1 规划算法

- **五次多项式轨迹**: 确保位置、速度、加速度的连续性，支持点位停靠模式
- **三次样条插值**: 提供平滑的轨迹曲线，支持平滑经过模式
- **线性轨迹**: 带抛物线过渡的线性运动

#### 3.2.2 规划模式

- **点位停靠模式**: 在每个中间路径点停止，确保精确到达
- **平滑经过模式**: 平滑穿过中间路径点，保持连续运动
- **原始时间模式**: 保持示教时的原始时间戳
- **均匀时间模式**: 重新生成均匀分布的时间点

#### 3.2.3 规划流程

1. 提取原始轨迹点的时间和位置数据
2. 根据模式选择时间处理方式
3. 使用相应算法生成规划轨迹
4. 生成 100 个轨迹点
5. 存储规划后的轨迹数据

#### 3.2.4 规划数据格式

```python
planned_data = {
    'original_points': valid_points,
    'planned_times': planned_t.tolist(),
    'planned_positions': planned_pos.tolist(),
    'planned_velocities': planned_vel.tolist(),
    'planned_accelerations': planned_acc.tolist(),
    'total_time': total_time,
    'point_count': len(planned_t)
}
```

### 3.3 轨迹播放

#### 3.3.1 播放机制

- **定时器播放**: 使用 QTimer，50ms 间隔（20Hz）
- **时间同步**: 根据规划轨迹的时间点精确播放
- **命令发送**: 通过信号机制发送位置控制命令

#### 3.3.2 播放流程

1. 用户选择轨迹并点击"执行示教"
2. 系统加载规划后的轨迹数据
3. 启动播放定时器
4. 按时间顺序发送轨迹点
5. 每个点发送`set_motor_position`命令
6. 播放完成后停止定时器

#### 3.3.3 播放信号

- `_trajectory_point_ready`: 轨迹点就绪信号
- `_trajectory_playback_started`: 播放开始信号
- `_trajectory_playback_finished`: 播放完成信号
- `_trajectory_playback_error`: 播放错误信号

### 3.4 轨迹可视化

#### 3.4.1 显示模式

- **原始轨迹**: 显示录制的原始轨迹点
- **规划轨迹**: 显示规划后的平滑轨迹
- **对比显示**: 同时显示原始轨迹和规划轨迹
- **示教轨迹**: 实时显示示教过程中的轨迹

#### 3.4.2 可视化功能

- 实时更新轨迹曲线
- 支持轨迹选择和切换
- 显示轨迹名称和时间轴
- 图例标识不同轨迹类型
- 自动轨迹选择优化

#### 3.4.3 UI 优化特性

- **智能轨迹选择**: 程序启动时自动选中最新的轨迹
- **无闪现切换**: 示教结束后直接显示新轨迹，无中间过渡
- **重试机制**: UI 初始化失败时自动重试，确保操作成功
- **状态保持**: 轨迹列表更新时保持用户选择状态

#### 3.4.4 历史曲线显示

- **参数选择**: 支持位置、速度、扭矩、温度等参数显示
- **实时更新**: 定时器每 100ms 更新一次曲线数据
- **数据缓存**: 使用 hash 比较避免不必要的数据刷新
- **坐标轴优化**: 自动调整坐标轴范围，确保曲线完整显示

## 4. 使用说明

### 4.1 示教录制操作

1. **开始示教**

   - 点击"开始示教"按钮
   - 系统自动失能电机
   - 开始记录轨迹点
   - 自动切换到示教轨迹视图

2. **录制过程**

   - 手动控制电机运动
   - 系统自动过滤重复数据
   - 实时显示录制状态

3. **结束示教**
   - 点击"结束示教"按钮
   - 系统自动保存轨迹
   - 自动选中新轨迹并显示规划结果
   - 无需手动选择或刷新

### 4.2 轨迹播放操作

1. **选择轨迹**

   - 从下拉框选择要播放的轨迹
   - 系统自动加载轨迹数据
   - 支持手动选择或自动选择

2. **执行播放**

   - 点击"执行示教"按钮
   - 系统开始播放轨迹
   - 实时显示播放进度

3. **停止播放**
   - 播放完成后自动停止
   - 或手动停止播放

### 4.3 轨迹可视化操作

1. **选择显示模式**

   - 在参数选择下拉框中选择轨迹类型
   - 支持原始轨迹、规划轨迹、对比显示

2. **查看轨迹**

   - 选择轨迹后自动显示
   - 支持缩放和平移操作
   - 显示轨迹详细信息

3. **轨迹重规划**
   - 调整执行时长参数
   - 点击"刷新曲线"进行重规划
   - 点击"恢复默认"使用原始时间

### 4.4 历史曲线操作

1. **参数选择**

   - 在参数下拉框中选择要显示的参数
   - 支持位置、速度、扭矩、温度等
   - 切换参数时自动刷新曲线

2. **数据刷新**

   - 系统自动定时刷新历史数据
   - 支持手动点击"刷新曲线"按钮
   - 使用 hash 比较优化刷新性能

3. **模拟数据**
   - 点击"发送模拟数据"按钮生成测试数据
   - 用于验证曲线显示功能
   - 模拟真实设备数据格式

## 5. 技术特性

### 5.1 性能优化

- **数据过滤**: 减少存储空间和播放时间
- **轨迹规划**: 提供平滑的运动曲线
- **定时器优化**: 精确的时间控制
- **按需规划**: 只在需要时进行轨迹规划，提高启动速度
- **Hash 比较**: 避免不必要的数据刷新，提升 UI 性能

### 5.2 安全机制

- **电机失能**: 示教时自动失能电机
- **错误处理**: 完善的异常处理机制
- **状态检查**: 播放前验证轨迹数据
- **UI 状态验证**: 确保 UI 组件完全初始化后再执行操作

### 5.3 扩展性

- **算法扩展**: 支持多种轨迹规划算法
- **设备扩展**: 可扩展到其他设备类型
- **功能扩展**: 支持速度控制和加速度控制

### 5.4 用户体验优化

- **自动化工作流**: 减少用户手动操作步骤
- **智能选择**: 自动选择最相关的轨迹
- **无延迟响应**: 优化 UI 响应速度
- **错误恢复**: 自动重试失败的操作

## 6. 故障排除

### 6.1 常见问题

1. **轨迹点重复**

   - 原因: 设备状态更新过于频繁
   - 解决: 调整过滤阈值参数

2. **播放不准确**

   - 原因: 时间同步问题
   - 解决: 检查定时器设置

3. **轨迹规划失败**

   - 原因: 轨迹点数量不足
   - 解决: 确保至少 2 个有效轨迹点

4. **UI 初始化失败**

   - 原因: 组件初始化时序问题
   - 解决: 系统会自动重试，无需手动干预

5. **历史曲线不显示**
   - 原因: 数据格式不匹配或 hash 比较问题
   - 解决: 检查数据格式，确认 hash 计算逻辑

### 6.2 调试方法

1. **日志查看**: 查看系统日志了解详细错误信息
2. **数据验证**: 检查轨迹文件格式和数据完整性
3. **信号调试**: 使用信号调试工具跟踪数据流
4. **UI 状态检查**: 查看控制台输出的 UI 状态信息
5. **Hash 调试**: 检查数据 hash 值，确认数据变化检测

## 7. 已知问题和 TODO

### 7.1 当前限制

1. **模拟数据模式**: 目前使用模拟数据进行验证，需要实现真实的设备通信
2. **轨迹执行测试**: 轨迹播放功能需要在实际硬件上进行测试验证

### 7.2 TODO 项目

1. **实时数据采集**:

   - 实现新线程，在示教模式下以 10Hz 频率发送请求报文
   - 接收电机响应报文，替代当前的模拟数据功能
   - 确保数据采集的实时性和准确性

2. **轨迹执行优化**:

   - 根据规划的时间点，按精确时间间隔发送位置请求
   - 测试轨迹播放的精度和稳定性
   - 优化播放过程中的时间同步机制

3. **日志系统完善**:
   - 为 UI 组件添加统一的日志管理
   - 实现日志级别的动态控制
   - 优化日志输出的格式和内容

## 8. 未来改进

### 8.1 功能增强

- 支持多轴同步轨迹
- 添加轨迹编辑功能
- 支持轨迹导入导出
- 实现轨迹版本管理

### 8.2 性能优化

- 优化轨迹规划算法
- 提高播放精度
- 减少内存占用
- 实现轨迹数据压缩

### 8.3 用户体验

- 改进可视化界面
- 添加轨迹预览功能
- 支持轨迹参数调整
- 实现轨迹播放进度条

### 8.4 硬件集成

- 实现真实的设备通信协议
- 支持多种电机类型
- 添加硬件状态监控
- 实现故障诊断功能
