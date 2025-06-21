# DeepMotor 轨迹规划模块

## 问题解决

### pyrobotics 安装错误

原问题：`pyrobotics` 包使用 Python 2 语法，与 Python 3 不兼容。

**错误信息：**

```
SyntaxError: Missing parentheses in call to 'print'. Did you mean print(...)?
```

### 解决方案

我们创建了自定义的轨迹规划模块来替代 `pyrobotics`，提供更灵活和现代化的功能。

## 文件说明

### 1. `robot_trajectory.py` - 核心轨迹规划模块

提供以下功能：

- **五次多项式轨迹规划** (`quintic_polynomial_trajectory`)
- **三次样条轨迹插值** (`cubic_spline_trajectory`)
- **多路径点轨迹生成** (`generate_waypoint_trajectory`)
- **自动中文字体配置**
- **轨迹可视化** (`plot_trajectory`)

### 2. `trajectory_example.py` - 使用示例

包含多个实际应用示例：

- 五次多项式轨迹示例
- 多路径点轨迹示例
- 三次样条轨迹示例
- 电机控制轨迹示例
- 自定义复杂轨迹示例

### 3. `quintic_interpolation.py` - 原始插值示例

修复了中文字体显示问题，现在可以正常显示中文标签。

### 4. `matplotlib_config.py` - 字体配置工具

提供跨平台的中文字体自动检测和配置功能。

## 使用方法

### 基本使用

```python
from robot_trajectory import RobotTrajectory

# 创建轨迹规划器
trajectory = RobotTrajectory()

# 生成五次多项式轨迹
t, pos, vel, acc = trajectory.quintic_polynomial_trajectory(
    t0=0, tf=5, q0=0, qf=10, v0=0, vf=0
)

# 绘制轨迹
trajectory.plot_trajectory(t, pos, vel, acc, "轨迹标题")
```

### 多路径点轨迹

```python
# 定义路径点
waypoints = [0, 5, -2, 8, 0]
total_time = 10

# 生成轨迹
t, pos, vel, acc = trajectory.generate_waypoint_trajectory(
    waypoints, total_time, method='quintic'
)
```

### 三次样条插值

```python
waypoints = np.array([0, 2, -1, 3, 0])
times = np.array([0, 1, 2, 3, 4])

t, pos, vel, acc = trajectory.cubic_spline_trajectory(
    waypoints, times, bc_type='clamped'
)
```

## 功能特性

### 1. 轨迹规划算法

- **五次多项式**：平滑的位置、速度、加速度曲线
- **三次样条**：通过指定路径点的平滑插值
- **线性+抛物线过渡**：带平滑过渡的线性轨迹

### 2. 边界条件支持

- **自然边界**：默认的三次样条边界条件
- **固定边界**：首尾速度为零
- **周期性边界**：适用于循环轨迹

### 3. 可视化功能

- 自动中文字体配置
- 位置、速度、加速度三合一图表
- 网格线和标签支持

### 4. 跨平台兼容

- Windows：SimHei, Microsoft YaHei
- macOS：PingFang SC, Hiragino Sans GB
- Linux：WenQuanYi Micro Hei, Noto Sans CJK SC

## 与 pyrobotics 的对比

| 功能        | pyrobotics       | 我们的模块     |
| ----------- | ---------------- | -------------- |
| Python 版本 | Python 2         | Python 3       |
| 安装难度    | 困难（语法错误） | 简单（无依赖） |
| 中文字体    | 不支持           | 自动配置       |
| 轨迹算法    | 基础             | 丰富           |
| 可视化      | 基础             | 现代化         |
| 维护性      | 停止维护         | 持续更新       |

## 运行示例

```bash
# 运行核心演示
python robot_trajectory.py

# 运行详细示例
python trajectory_example.py

# 运行原始插值示例
python quintic_interpolation.py
```

## 集成到项目

在您的 DeepMotor 项目中使用：

```python
# 在 deep_motor.py 中导入
from .robot_trajectory import RobotTrajectory

class DeepMotor:
    def __init__(self):
        self.trajectory_planner = RobotTrajectory()

    def plan_movement(self, target_position, duration):
        """规划电机运动轨迹"""
        t, pos, vel, acc = self.trajectory_planner.quintic_polynomial_trajectory(
            0, duration, self.current_position, target_position
        )
        return t, pos, vel, acc
```

## 总结

通过创建自定义的轨迹规划模块，我们成功解决了 `pyrobotics` 的兼容性问题，并提供了更强大、更易用的功能。这个解决方案：

1. ✅ 完全兼容 Python 3
2. ✅ 支持中文字体显示
3. ✅ 提供多种轨迹规划算法
4. ✅ 包含详细的使用示例
5. ✅ 易于集成到现有项目
6. ✅ 持续维护和扩展

现在您可以正常使用轨迹规划功能，无需担心 `pyrobotics` 的安装问题。
