# DeepMotor 页面组件架构

## 概述

DeepMotor 页面已经重构为模块化组件架构，将原来的大文件拆分为多个独立的功能组件，提高了代码的可维护性和可扩展性。

## 组件结构

### 1. 通用绘图组件 (`UniversalPlotWidget`)

**文件位置**: `components/universal_plot_widget.py`

**功能**:

- 提供统一的 matplotlib 绘图接口
- 支持多种数据类型的高性能绘制
- 实现按需刷新，避免 UI 阻塞
- 支持轨迹对比、历史数据、示教轨迹等多种绘图模式

**主要特性**:

- 节流更新机制，避免频繁重绘
- 数据 hash 检测，避免重复绘制
- 自动坐标轴范围调整
- 支持多种数据格式（DataFrame、列表、字典等）

### 2. 通信显示组件 (`CommunicationWidget`)

**文件位置**: `components/communication_widget.py`

**功能**:

- 显示串口和 CAN 通信的收发数据
- 带时间戳和描述信息
- 支持协议切换（串口/CAN）
- 自动滚动和统计功能

**主要特性**:

- 实时数据显示，带毫秒级时间戳
- 十六进制和 ASCII 格式显示
- 发送/接收数据分离显示
- 数据导出功能
- 最大显示条目限制，防止内存溢出

### 3. 电机控制组件 (`MotorControlWidget`)

**文件位置**: `components/motor_control_widget.py`

**功能**:

- 电机参数设置（ID、位置、速度）
- 基本控制功能（初始化、使能、失能等）
- 点动控制
- 状态显示

**主要特性**:

- 实时参数调整
- 状态反馈显示
- 按钮状态管理
- 参数验证和范围限制

### 4. 示教控制组件 (`TeachingControlWidget`)

**文件位置**: `components/teaching_control_widget.py`

**功能**:

- 示教录制控制
- 轨迹执行管理
- 轨迹列表管理
- 执行参数设置

**主要特性**:

- 示教状态管理
- 轨迹选择和管理
- 执行时长控制
- 轨迹规划开关
- 进度显示

### 5. 历史曲线组件 (`HistoryCurveWidget`)

**文件位置**: `components/history_curve_widget.py`

**功能**:

- 历史数据显示
- 参数选择
- 数据请求管理
- 与通用绘图组件集成

**主要特性**:

- 参数自动切换
- 定时数据请求
- 轨迹数据特殊处理
- 与示教控制联动

## 主页面 (`DeepMotorPageNew`)

**文件位置**: `deep_motor_page_new.py`

**功能**:

- 整合所有组件
- 统一信号管理
- 对外接口提供
- 组件间协调

**主要特性**:

- 模块化布局设计
- 信号统一管理
- 组件间解耦
- 清晰的对外接口

## 架构优势

### 1. 模块化设计

- 每个组件职责单一，功能明确
- 组件间低耦合，高内聚
- 便于单独测试和维护

### 2. 性能优化

- 绘图组件实现按需刷新
- 数据 hash 检测避免重复绘制
- 定时器节流机制
- 内存使用优化

### 3. 可扩展性

- 新功能可以独立开发组件
- 现有组件可以独立升级
- 支持组件替换和扩展

### 4. 代码质量

- 遵循 PEP 8 规范
- 完整的类型提示
- 详细的文档字符串
- 统一的错误处理

## 使用方式

### 1. 直接使用组件

```python
from components import MotorControlWidget, CommunicationWidget

# 创建组件
motor_control = MotorControlWidget("电机控制", log_manager)
communication = CommunicationWidget("通信监控", log_manager)

# 连接信号
motor_control.command_requested.connect(your_command_handler)
communication.protocol_changed.connect(your_protocol_handler)
```

### 2. 使用完整页面

```python
from deep_motor_page_new import DeepMotorPageNew

# 创建页面
page = DeepMotorPageNew("DeepMotor", log_manager, config_manager)

# 连接对外信号
page.ui_deepmotor_command.connect(your_command_handler)
page.request_history_data.connect(your_data_handler)
```

### 3. 运行演示

```bash
cd DeepWin/deepwin/ui/app/view/devices/deep_motor
python demo_new_components.py
```

## 信号系统

### 对外信号

- `ui_deepmotor_command`: 设备命令信号
- `request_sim_data`: 模拟数据请求信号
- `request_history_data`: 历史数据请求信号
- `start_teaching_requested`: 开始示教信号
- `stop_teaching_requested`: 停止示教信号
- `execute_teaching_requested`: 执行示教信号
- `request_trajectory_data`: 轨迹数据请求信号
- `request_trajectory_list`: 轨迹列表请求信号

### 内部信号

- 组件间通过信号进行通信
- 主页面统一管理所有信号
- 支持信号转发和转换

## 配置和日志

- 所有组件都支持日志管理器
- 统一的配置管理
- 可配置的更新频率和参数

## 未来扩展

1. **新组件开发**: 可以轻松添加新的功能组件
2. **组件升级**: 现有组件可以独立升级而不影响其他组件
3. **布局优化**: 支持动态布局调整
4. **主题支持**: 支持深色/浅色主题切换
5. **国际化**: 支持多语言界面

## 注意事项

1. 所有组件都继承自 QWidget，确保 Qt 兼容性
2. 信号连接需要在组件创建后立即进行
3. 日志管理器是可选的，但建议使用
4. 组件销毁时会自动清理资源
5. 大数据量时注意内存使用

## 开发指南

1. **新组件开发**:

   - 继承自 QWidget
   - 实现必要的信号
   - 提供清晰的对外接口
   - 添加完整的文档字符串

2. **信号设计**:

   - 信号命名要清晰明确
   - 参数类型要明确
   - 避免信号循环

3. **性能考虑**:

   - 使用定时器节流
   - 避免频繁的 UI 更新
   - 合理使用缓存机制

4. **错误处理**:
   - 使用 try-except 包装关键操作
   - 记录详细的错误日志
   - 提供用户友好的错误提示
