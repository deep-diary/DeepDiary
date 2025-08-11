# DeepArm 开发步骤与计划

## 项目概述

DeepArm 是 DeepWin 系统中的机械臂控制模块，采用分层架构设计，包含 GUI 界面、设备逻辑层、协议解析层和硬件通信层。本文档详细规划了 DeepArm 功能的开发步骤和实现计划。DeepArm 是由 6 个 DeepMotor 组合实现的，因此，不少逻辑代码，都可以参考 DeepMotor

## 当前状态分析

### 已完成的基础架构

1. **设备逻辑层** (`/deep_arm/`)

   - ✅ `deep_arm.py`: 核心逻辑类，继承自 BaseDevice
   - ✅ `state_model.py`: 状态模型定义，包含 6 个关节角度、末端执行器位置等
   - ✅ `teaching_trajectory_manager.py`: 示教轨迹管理框架（待完善）

2. **协议解析层** (`/deep_arm_protocol/`)

   - ✅ `deep_arm_parser.py`: 协议解析器，支持 CAN 信号转换
   - ✅ 基础命令编码：`move_joint_angles`、`reset_arm`

3. **GUI 框架** (`/devices/deep_arm/`)

   - ✅ `deep_arm_page.py`: 基础页面框架（待完善 UI）

4. **协调器架构**
   - ✅ 完整的信号传递链路：GUI → Coordinator → DeviceLogicManager → ProtocolParser → Hardware
   - ✅ 设备状态更新反馈链路：Hardware → ProtocolParser → DeviceLogicManager → Coordinator → GUI

## 开发计划

### 第一阶段：GUI 界面开发

#### 1.1 基础界面布局设计

**目标**: 创建完整的 DeepArm 控制界面

**任务清单**:

- [ ] 设计 6 个关节角度控制滑块/输入框
- [ ] 添加末端执行器位置显示区域
- [ ] 创建安全状态指示器（急停、碰撞检测、工作空间限制）
- [ ] 添加温度监控显示
- [ ] 设计关节状态表格（角度、速度、扭矩）
- [ ] 添加设备连接状态指示
- [ ] 界面通过卡片分为如下几部分：1. 控制卡片，主要下发一些控制指令；2. 示教卡片，主要执行示教相关逻辑，具体可以参考 DeepMotor 逻辑；3. 反馈卡片，主要显示 6 轴机械臂的反馈信息，这个卡片期望分为 2 部分，左边是机械臂实时状态显示，根据 URDF 及当前的目标及实际关键，显示机械臂的状态，右边是一些常规信息显示，比如温度监控，安全状态指示器等

**技术实现**:

```python
# 在 deep_arm_page.py 中实现
class DeepArmPage(BaseDevicePage):
    def setup_ui(self):
        # 创建主布局
        # 添加关节控制区域
        # 添加状态显示区域
        # 添加安全监控区域
        # 添加示教功能区域
```

#### 1.2 控制功能实现

**目标**: 实现 GUI 到协调器的命令传递

**任务清单**:

- [ ] 实现关节角度控制信号连接
- [ ] 添加急停按钮功能
- [ ] 实现复位功能
- [ ] 添加状态刷新机制
- [ ] 实现实时数据更新显示

**信号连接示例**:

```python
def setup_signals(self):
    # 连接关节控制信号
    self.joint1_slider.valueChanged.connect(
        lambda value: self.ui_device_command.emit("DeepArm", f"move_joint_angles({value}, ...)")
    )
    # 连接急停信号
    self.emergency_stop_button.clicked.connect(
        lambda: self.ui_device_command.emit("DeepArm", "emergency_stop")
    )
```

### 第二阶段：设备逻辑层完善

#### 2.1 状态模型增强

**目标**: 完善 DeepArm 状态模型，支持更多功能

**任务清单**:

- [ ] 添加关节限位检测
- [ ] 实现末端执行器姿态计算
- [ ] 添加运动状态跟踪
- [ ] 实现安全状态聚合
- [ ] 添加历史状态记录

**代码增强**:

```python
# 在 state_model.py 中添加
@dataclass
class DeepArmState(BaseDeviceState):
    # 新增字段
    joint_limits_reached: List[bool] = None
    end_effector_orientation: Dict[str, float] = None
    motion_status: str = "idle"  # idle, moving, error
    safety_status: Dict[str, bool] = None
    historical_states: List[Dict] = None
```

#### 2.2 命令处理完善

**目标**: 扩展 DeepArm 支持的命令集

**任务清单**:

- [ ] 实现关节速度控制
- [ ] 添加末端执行器位置控制
- [ ] 实现轨迹规划命令
- [ ] 添加参数配置命令
- [ ] 实现状态查询命令

**命令扩展**:

```python
def execute_abstract_command(self, command_name: str, args: List[Any], send_request_signal):
    if command_name == "set_joint_velocity":
        # 设置关节速度
    elif command_name == "move_to_position":
        # 移动到指定位置
    elif command_name == "set_trajectory":
        # 设置轨迹
    elif command_name == "configure_parameters":
        # 配置参数
```

#### 2.3 异常检测增强

**目标**: 完善安全监控和异常处理

**任务清单**:

- [ ] 实现关节角度超限检测
- [ ] 添加温度异常监控
- [ ] 实现碰撞预测算法
- [ ] 添加运动冲突检测
- [ ] 实现自动安全响应

### 第三阶段：协议解析层优化

#### 3.1 DBC 文件创建

**目标**: 创建完整的 DeepArm CAN 协议定义

**任务清单**:

- [ ] 定义关节角度信号（6 个关节）
- [ ] 添加末端执行器位置信号
- [ ] 定义安全状态信号
- [ ] 添加温度监控信号
- [ ] 定义控制命令信号

**DBC 文件结构**:

```
VERSION "DeepArm Protocol v1.0"

BO_ 101 JointStatus: 8 Vector__XXX
 SG_ Joint1Angle : 0|16@1+ (0.1,0) [0|6553.5] "deg" Vector__XXX
 SG_ Joint2Angle : 16|16@1+ (0.1,0) [0|6553.5] "deg" Vector__XXX
 SG_ Joint3Angle : 32|16@1+ (0.1,0) [0|6553.5] "deg" Vector__XXX
 SG_ Joint4Angle : 48|16@1+ (0.1,0) [0|6553.5] "deg" Vector__XXX

BO_ 102 EndEffectorStatus: 6 Vector__XXX
 SG_ EndEffectorX : 0|16@1+ (0.01,0) [0|655.35] "mm" Vector__XXX
 SG_ EndEffectorY : 16|16@1+ (0.01,0) [0|655.35] "mm" Vector__XXX
 SG_ EndEffectorZ : 32|16@1+ (0.01,0) [0|655.35] "mm" Vector__XXX

BO_ 103 SafetyStatus: 2 Vector__XXX
 SG_ EmergencyStop : 0|1@1+ (1,0) [0|1] "" Vector__XXX
 SG_ CollisionDetected : 1|1@1+ (1,0) [0|1] "" Vector__XXX
 SG_ WorkspaceLimitReached : 2|1@1+ (1,0) [0|1] "" Vector__XXX
```

#### 3.2 协议解析优化

**目标**: 完善协议解析器的功能和性能

**任务清单**:

- [ ] 实现信号校验和错误检测
- [ ] 添加数据平滑处理
- [ ] 实现协议版本兼容性
- [ ] 添加数据压缩和解压
- [ ] 实现协议统计和监控

#### 3.3 命令编码完善

**目标**: 扩展支持的命令编码

**任务清单**:

- [ ] 实现关节速度控制编码
- [ ] 添加末端执行器位置控制编码
- [ ] 实现轨迹命令编码
- [ ] 添加参数配置编码
- [ ] 实现状态查询编码

### 第四阶段：示教功能实现

#### 4.1 轨迹录制功能

**目标**: 实现机械臂轨迹录制

**任务清单**:

- [ ] 实现轨迹录制开始/停止
- [ ] 添加轨迹点采样控制
- [ ] 实现轨迹数据存储
- [ ] 添加轨迹编辑功能
- [ ] 实现轨迹验证

**实现示例**:

```python
class TeachingTrajectoryManager(QObject):
    def start_recording(self, device_id: str, sample_rate: float = 10.0):
        """开始录制轨迹"""
        self._recording_sessions[device_id] = {
            'points': [],
            'start_time': time.time(),
            'sample_rate': sample_rate
        }
        # 启动定时器进行采样

    def stop_recording(self, device_id: str, trajectory_name: str):
        """停止录制并保存轨迹"""
        session = self._recording_sessions.pop(device_id, None)
        if session:
            trajectory_data = {
                'name': trajectory_name,
                'points': session['points'],
                'duration': time.time() - session['start_time'],
                'sample_rate': session['sample_rate']
            }
            self._save_trajectory(trajectory_data)
```

#### 4.2 轨迹播放功能

**目标**: 实现轨迹回放控制

**任务清单**:

- [ ] 实现轨迹加载和解析
- [ ] 添加播放速度控制
- [ ] 实现轨迹循环播放
- [ ] 添加播放进度监控
- [ ] 实现轨迹暂停/恢复

#### 4.3 轨迹管理功能

**目标**: 实现轨迹的存储和管理

**任务清单**:

- [ ] 实现轨迹文件存储
- [ ] 添加轨迹列表管理
- [ ] 实现轨迹导入/导出
- [ ] 添加轨迹分类和标签
- [ ] 实现轨迹搜索功能

### 第五阶段：集成测试与优化

#### 5.1 功能集成测试

**目标**: 验证各层之间的协作

**任务清单**:

- [ ] GUI 到设备逻辑层测试
- [ ] 设备逻辑层到协议解析层测试
- [ ] 协议解析层到硬件通信层测试
- [ ] 完整数据链路测试
- [ ] 异常处理测试

#### 5.2 性能优化

**目标**: 提升系统性能和响应速度

**任务清单**:

- [ ] 优化数据更新频率
- [ ] 实现数据缓存机制
- [ ] 优化内存使用
- [ ] 提升 UI 响应速度
- [ ] 实现异步处理优化

#### 5.3 用户体验优化

**目标**: 提升用户操作体验

**任务清单**:

- [ ] 优化界面布局和交互
- [ ] 添加操作提示和帮助
- [ ] 实现快捷键支持
- [ ] 添加操作确认机制
- [ ] 实现状态可视化

## 开发优先级

### 高优先级（必须完成）

1. GUI 基础界面布局
2. 关节角度控制功能
3. 设备状态显示
4. 基础协议解析

### 中优先级（重要功能）

1. 安全状态监控
2. 示教轨迹录制
3. 轨迹播放功能
4. 异常处理机制

### 低优先级（增强功能）

1. 高级轨迹编辑
2. 性能优化
3. 用户体验优化
4. 扩展功能开发

## 技术规范

### 代码规范

- 遵循 PEP 8 Python 代码规范
- 使用类型注解
- 添加详细的文档字符串
- 实现适当的错误处理

### 信号规范

- 使用统一的信号命名规范
- 确保信号参数类型一致
- 实现信号连接的错误处理

### 测试规范

- 为每个模块编写单元测试
- 实现集成测试
- 进行性能测试
- 执行用户验收测试

## 风险评估

### 技术风险

1. **协议兼容性**: 实际硬件协议可能与设计不符
2. **性能瓶颈**: 实时数据更新可能影响 UI 响应
3. **内存泄漏**: 长时间运行可能出现内存问题

### 缓解措施

1. 与硬件团队确认协议细节
2. 实现数据更新频率控制
3. 定期进行内存使用监控

## 时间规划

### 第一阶段（1-2 周）

- GUI 界面开发
- 基础控制功能

### 第二阶段（2-3 周）

- 设备逻辑层完善
- 状态模型增强

### 第三阶段（2-3 周）

- 协议解析优化
- DBC 文件创建

### 第四阶段（3-4 周）

- 示教功能实现
- 轨迹管理

### 第五阶段（1-2 周）

- 集成测试
- 性能优化

**总计**: 9-14 周

## 验收标准

### 功能验收

- [ ] 所有关节角度控制正常工作
- [ ] 设备状态实时显示准确
- [ ] 示教轨迹录制和播放功能完整
- [ ] 异常处理机制有效

### 性能验收

- [ ] UI 响应时间 < 100ms
- [ ] 数据更新延迟 < 50ms
- [ ] 内存使用稳定
- [ ] CPU 使用率合理

### 质量验收

- [ ] 代码覆盖率 > 80%
- [ ] 无严重 bug
- [ ] 文档完整
- [ ] 用户操作流畅

## 后续维护

### 版本管理

- 使用语义化版本号
- 维护更新日志
- 实现向后兼容

### 监控和日志

- 实现详细的日志记录
- 添加性能监控
- 建立错误报告机制

### 用户反馈

- 收集用户使用反馈
- 定期进行功能评估
- 持续改进用户体验

---

**文档版本**: v1.0  
**创建日期**: 2024 年 12 月  
**维护人员**: DeepWin 开发团队
