"""
轨迹规划使用示例
展示如何在DeepMotor项目中使用轨迹规划功能
"""

from robot_trajectory import RobotTrajectory
import numpy as np

def example_quintic_trajectory():
    """五次多项式轨迹示例"""
    print("=== 五次多项式轨迹示例 ===")
    
    trajectory = RobotTrajectory()
    
    # 定义轨迹参数
    t0, tf = 0, 5  # 起始和结束时间
    q0, qf = 0, 10  # 起始和结束位置
    v0, vf = 0, 0   # 起始和结束速度
    a0, af = 0, 0   # 起始和结束加速度
    
    # 生成轨迹
    t, pos, vel, acc = trajectory.quintic_polynomial_trajectory(
        t0, tf, q0, qf, v0, vf, a0, af
    )
    
    # 绘制轨迹
    trajectory.plot_trajectory(t, pos, vel, acc, "五次多项式轨迹示例")
    
    # 输出关键数据点
    print(f"起始位置: {pos[0]:.3f}")
    print(f"结束位置: {pos[-1]:.3f}")
    print(f"最大速度: {np.max(np.abs(vel)):.3f}")
    print(f"最大加速度: {np.max(np.abs(acc)):.3f}")

def example_waypoint_trajectory():
    """多路径点轨迹示例"""
    print("\n=== 多路径点轨迹示例 ===")
    
    trajectory = RobotTrajectory()
    
    # 定义路径点
    waypoints = [0, 5, -2, 8, 0]  # 位置序列
    total_time = 10  # 总时间
    
    # 生成轨迹
    t, pos, vel, acc = trajectory.generate_waypoint_trajectory(
        waypoints, total_time, method='quintic'
    )
    
    # 计算原始轨迹点的时间
    original_times = np.linspace(0, total_time, len(waypoints))
    
    # 绘制轨迹（包含原始轨迹点）
    trajectory.plot_trajectory(t, pos, vel, acc, "多路径点轨迹示例", 
                              original_waypoints=waypoints, original_times=original_times)
    
    # 输出关键数据点
    print(f"路径点数量: {len(waypoints)}")
    print(f"总时间: {total_time}秒")
    print(f"最大速度: {np.max(np.abs(vel)):.3f}")
    print(f"最大加速度: {np.max(np.abs(acc)):.3f}")

def example_cubic_spline():
    """三次样条轨迹示例"""
    print("\n=== 三次样条轨迹示例 ===")
    
    trajectory = RobotTrajectory()
    
    # 定义路径点和时间
    waypoints = np.array([0, 2, -1, 3, 0])
    times = np.array([0, 1, 2, 3, 4])
    
    # 生成轨迹
    t, pos, vel, acc = trajectory.cubic_spline_trajectory(
        waypoints, times, bc_type='clamped'
    )
    
    # 绘制轨迹（包含原始轨迹点）
    trajectory.plot_trajectory(t, pos, vel, acc, "三次样条轨迹示例",
                              original_waypoints=waypoints, original_times=times)
    
    # 输出关键数据点
    print(f"路径点: {waypoints}")
    print(f"时间点: {times}")
    print(f"最大速度: {np.max(np.abs(vel)):.3f}")
    print(f"最大加速度: {np.max(np.abs(acc)):.3f}")

def example_motor_control():
    """电机控制轨迹示例"""
    print("\n=== 电机控制轨迹示例 ===")
    
    trajectory = RobotTrajectory()
    
    # 模拟电机控制场景
    # 从位置0移动到位置10，然后回到位置0
    waypoints = [0, 10, 0]
    total_time = 6  # 6秒完成整个运动
    
    # 生成轨迹
    t, pos, vel, acc = trajectory.generate_waypoint_trajectory(
        waypoints, total_time, method='quintic'
    )
    
    # 计算原始轨迹点的时间
    original_times = np.linspace(0, total_time, len(waypoints))
    
    # 绘制轨迹（包含原始轨迹点）
    trajectory.plot_trajectory(t, pos, vel, acc, "电机控制轨迹示例",
                              original_waypoints=waypoints, original_times=original_times)
    
    # 输出控制指令（模拟）
    print("电机控制指令序列:")
    for i in range(0, len(t), 10):  # 每10个点输出一次
        print(f"时间 {t[i]:.2f}s: 位置={pos[i]:.3f}, 速度={vel[i]:.3f}, 加速度={acc[i]:.3f}")

def example_custom_trajectory():
    """自定义轨迹示例"""
    print("\n=== 自定义轨迹示例 ===")
    
    trajectory = RobotTrajectory()
    
    # 自定义复杂的路径点序列
    waypoints = [0, 3, -1, 5, 2, 8, 0]
    total_time = 15
    
    # 生成轨迹
    t, pos, vel, acc = trajectory.generate_waypoint_trajectory(
        waypoints, total_time, method='cubic'
    )
    
    # 计算原始轨迹点的时间
    original_times = np.linspace(0, total_time, len(waypoints))
    
    # 绘制轨迹（包含原始轨迹点）
    trajectory.plot_trajectory(t, pos, vel, acc, "自定义复杂轨迹示例",
                              original_waypoints=waypoints, original_times=original_times)
    
    # 分析轨迹特性
    print(f"轨迹分析:")
    print(f"  路径点: {waypoints}")
    print(f"  总时间: {total_time}秒")
    print(f"  最大位置: {np.max(pos):.3f}")
    print(f"  最小位置: {np.min(pos):.3f}")
    print(f"  最大速度: {np.max(np.abs(vel)):.3f}")
    print(f"  最大加速度: {np.max(np.abs(acc)):.3f}")
    print(f"  平均速度: {np.mean(np.abs(vel)):.3f}")

if __name__ == "__main__":
    # 运行所有示例
    example_quintic_trajectory()
    example_waypoint_trajectory()
    example_cubic_spline()
    example_motor_control()
    example_custom_trajectory()
    
    print("\n=== 所有示例运行完成 ===")
    print("这些轨迹规划功能可以替代pyrobotics包，提供更灵活的轨迹控制。") 