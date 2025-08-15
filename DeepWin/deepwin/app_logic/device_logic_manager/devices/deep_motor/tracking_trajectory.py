"""
机械臂轨迹规划与跟踪控制演示
展示静态轨迹规划和动态轨迹跟踪的不同实现思路
"""

import numpy as np
import matplotlib.pyplot as plt
import time
import matplotlib.font_manager as fm
import platform
from scipy.interpolate import CubicSpline

class TrajectoryTracker:
    """轨迹跟踪控制器"""
    
    def __init__(self):
        # 移除重复的字体配置，使用全局配置
        # self.setup_chinese_font()
        self.current_position = 0.0
        self.current_velocity = 0.0
        self.current_acceleration = 0.0
        self.target_position = 0.0
        self.target_velocity = 0.0
        
        # 控制参数 - 调整更合理的值
        self.kp = 2.0   # 位置增益
        self.kv = 1.0   # 速度增益
        self.ka = 0.1   # 加速度增益
        
        # 预测参数
        self.prediction_horizon = 0.1  # 预测时间窗口（缩短）
        self.target_history = []  # 目标历史轨迹
        self.max_history = 20     # 最大历史长度（减少）
        
    def static_trajectory_planning(self, waypoints, times):
        """
        静态轨迹规划（示教功能）
        
        Args:
            waypoints: 示教路径点
            times: 时间点
            
        Returns:
            tuple: (时间数组, 位置数组, 速度数组, 加速度数组)
        """
        print("=== 静态轨迹规划（示教功能）===")
        print(f"示教路径点: {waypoints}")
        print(f"时间点: {times}")
        
        # 使用三次样条插值生成平滑轨迹
        cs = CubicSpline(times, waypoints, bc_type=((1, 0), (1, 0)))
        
        # 生成轨迹数据
        t_interp = np.linspace(times[0], times[-1], 100)
        pos_interp = cs(t_interp)
        vel_interp = cs(t_interp, 1)
        acc_interp = cs(t_interp, 2)
        
        print(f"轨迹规划完成，总时间: {times[-1]:.2f}秒")
        return t_interp, pos_interp, vel_interp, acc_interp
    
    def update_target_history(self, target_pos, target_vel, current_time):
        """更新目标历史轨迹"""
        self.target_history.append({
            'time': current_time,
            'position': target_pos,
            'velocity': target_vel
        })
        
        # 保持历史长度
        if len(self.target_history) > self.max_history:
            self.target_history.pop(0)
    
    def predict_target_motion(self, current_time, prediction_time):
        """
        预测目标运动
        
        Args:
            current_time: 当前时间
            prediction_time: 预测时间
            
        Returns:
            tuple: (预测位置, 预测速度)
        """
        if len(self.target_history) < 2:
            return self.target_position, self.target_velocity
        
        # 提取最近的历史数据
        recent_times = [h['time'] for h in self.target_history[-5:]]  # 只取最近5个点
        recent_positions = [h['position'] for h in self.target_history[-5:]]
        
        # 使用简单的线性预测
        if len(recent_times) >= 2:
            # 计算最近的速度
            dt = recent_times[-1] - recent_times[-2]
            dp = recent_positions[-1] - recent_positions[-2]
            
            if abs(dt) > 1e-6:  # 避免除零
                current_velocity = dp / dt
                # 限制速度范围，避免数值不稳定
                current_velocity = np.clip(current_velocity, -10.0, 10.0)
                
                # 预测未来位置
                predicted_position = recent_positions[-1] + current_velocity * prediction_time
                predicted_velocity = current_velocity
                
                return predicted_position, predicted_velocity
        
        return self.target_position, self.target_velocity
    
    def dynamic_tracking_control(self, target_pos, target_vel, current_time, dt):
        """
        动态轨迹跟踪控制
        
        Args:
            target_pos: 目标位置
            target_vel: 目标速度
            current_time: 当前时间
            dt: 时间步长
            
        Returns:
            tuple: (控制输出, 新位置, 新速度, 新加速度)
        """
        # 更新目标历史
        self.update_target_history(target_pos, target_vel, current_time)
        
        # 预测目标运动
        predicted_pos, predicted_vel = self.predict_target_motion(
            current_time, self.prediction_horizon
        )
        
        # 计算跟踪误差
        pos_error = predicted_pos - self.current_position
        vel_error = predicted_vel - self.current_velocity
        
        # PID控制律
        control_output = (self.kp * pos_error + 
                         self.kv * vel_error + 
                         self.ka * self.current_acceleration)
        
        # 限制控制输出，避免数值不稳定
        control_output = np.clip(control_output, -5.0, 5.0)
        
        # 更新机器人状态（简化模型）
        self.current_acceleration = control_output
        self.current_velocity += self.current_acceleration * dt
        self.current_position += self.current_velocity * dt
        
        # 限制速度和位置范围
        self.current_velocity = np.clip(self.current_velocity, -10.0, 10.0)
        self.current_position = np.clip(self.current_position, -20.0, 20.0)
        
        return control_output, self.current_position, self.current_velocity, self.current_acceleration
    
    def simulate_static_execution(self, t, pos, vel, acc):
        """模拟静态轨迹执行"""
        print("开始执行静态轨迹...")
        
        execution_data = {
            'time': [],
            'position': [],
            'velocity': [],
            'acceleration': [],
            'target_position': []
        }
        
        for i, ti in enumerate(t):
            execution_data['time'].append(ti)
            execution_data['position'].append(pos[i])
            execution_data['velocity'].append(vel[i])
            execution_data['acceleration'].append(acc[i])
            execution_data['target_position'].append(pos[i])  # 静态轨迹中目标就是当前位置
        
        print("静态轨迹执行完成")
        return execution_data
    
    def simulate_dynamic_tracking(self, target_trajectory, duration, dt=0.01):
        """
        模拟动态轨迹跟踪
        
        Args:
            target_trajectory: 目标轨迹函数 (time) -> (position, velocity)
            duration: 跟踪持续时间
            dt: 时间步长
        """
        print("=== 动态轨迹跟踪（人脸追踪）===")
        print("开始动态跟踪...")
        
        tracking_data = {
            'time': [],
            'position': [],
            'velocity': [],
            'acceleration': [],
            'target_position': [],
            'target_velocity': [],
            'control_output': []
        }
        
        current_time = 0.0
        
        while current_time <= duration:
            # 获取目标位置和速度
            target_pos, target_vel = target_trajectory(current_time)
            
            # 执行跟踪控制
            control_output, pos, vel, acc = self.dynamic_tracking_control(
                target_pos, target_vel, current_time, dt
            )
            
            # 记录数据
            tracking_data['time'].append(current_time)
            tracking_data['position'].append(pos)
            tracking_data['velocity'].append(vel)
            tracking_data['acceleration'].append(acc)
            tracking_data['target_position'].append(target_pos)
            tracking_data['target_velocity'].append(target_vel)
            tracking_data['control_output'].append(control_output)
            
            current_time += dt
        
        print("动态跟踪完成")
        return tracking_data
    
    def plot_comparison(self, static_data, dynamic_data):
        """绘制静态轨迹和动态跟踪对比图"""
        fig, axes = plt.subplots(3, 2, figsize=(15, 10))
        
        # 静态轨迹
        axes[0, 0].plot(static_data['time'], static_data['position'], 'b-', linewidth=2, label='实际位置')
        axes[0, 0].plot(static_data['time'], static_data['target_position'], 'r--', linewidth=2, label='目标位置')
        axes[0, 0].set_title('静态轨迹 - 位置跟踪')
        axes[0, 0].set_ylabel('位置')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        axes[1, 0].plot(static_data['time'], static_data['velocity'], 'g-', linewidth=2)
        axes[1, 0].set_title('静态轨迹 - 速度')
        axes[1, 0].set_ylabel('速度')
        axes[1, 0].grid(True)
        
        axes[2, 0].plot(static_data['time'], static_data['acceleration'], 'm-', linewidth=2)
        axes[2, 0].set_title('静态轨迹 - 加速度')
        axes[2, 0].set_xlabel('时间')
        axes[2, 0].set_ylabel('加速度')
        axes[2, 0].grid(True)
        
        # 动态跟踪
        axes[0, 1].plot(dynamic_data['time'], dynamic_data['position'], 'b-', linewidth=2, label='实际位置')
        axes[0, 1].plot(dynamic_data['time'], dynamic_data['target_position'], 'r--', linewidth=2, label='目标位置')
        axes[0, 1].set_title('动态跟踪 - 位置跟踪')
        axes[0, 1].set_ylabel('位置')
        axes[0, 1].legend()
        axes[0, 1].grid(True)
        
        axes[1, 1].plot(dynamic_data['time'], dynamic_data['velocity'], 'g-', linewidth=2, label='实际速度')
        axes[1, 1].plot(dynamic_data['time'], dynamic_data['target_velocity'], 'r--', linewidth=2, label='目标速度')
        axes[1, 1].set_title('动态跟踪 - 速度跟踪')
        axes[1, 1].set_ylabel('速度')
        axes[1, 1].legend()
        axes[1, 1].grid(True)
        
        axes[2, 1].plot(dynamic_data['time'], dynamic_data['control_output'], 'c-', linewidth=2)
        axes[2, 1].set_title('动态跟踪 - 控制输出')
        axes[2, 1].set_xlabel('时间')
        axes[2, 1].set_ylabel('控制输出')
        axes[2, 1].grid(True)
        
        plt.suptitle('静态轨迹规划 vs 动态轨迹跟踪')
        plt.tight_layout()
        plt.show()

def demo_tracking_comparison():
    """演示轨迹跟踪对比"""
    tracker = TrajectoryTracker()
    
    # 1. 静态轨迹规划（示教功能）
    print("=== 演示1：静态轨迹规划（示教功能）===")
    waypoints = [0, 2, -1, 3, 0]  # 示教路径点
    times = [0, 1, 2, 3, 4]       # 时间点
    
    t_static, pos_static, vel_static, acc_static = tracker.static_trajectory_planning(
        waypoints, times
    )
    
    # 模拟静态轨迹执行
    static_data = tracker.simulate_static_execution(t_static, pos_static, vel_static, acc_static)
    
    # 2. 动态轨迹跟踪（人脸追踪）
    print("\n=== 演示2：动态轨迹跟踪（人脸追踪）===")
    
    # 定义目标轨迹函数（模拟人脸运动）
    def target_trajectory(t):
        """模拟人脸运动轨迹"""
        # 正弦运动 + 随机扰动
        base_pos = 2 * np.sin(2 * np.pi * 0.5 * t)  # 基础正弦运动
        random_pos = 0.5 * np.sin(2 * np.pi * 2 * t)  # 快速随机运动
        position = base_pos + random_pos
        
        # 计算速度
        base_vel = 2 * np.pi * 0.5 * 2 * np.cos(2 * np.pi * 0.5 * t)
        random_vel = 0.5 * 2 * np.pi * 2 * np.cos(2 * np.pi * 2 * t)
        velocity = base_vel + random_vel
        
        return position, velocity
    
    # 模拟动态跟踪
    dynamic_data = tracker.simulate_dynamic_tracking(target_trajectory, duration=4.0, dt=0.01)
    
    # 3. 绘制对比图
    tracker.plot_comparison(static_data, dynamic_data)
    
    # 4. 输出性能对比
    print("\n=== 性能对比 ===")
    
    # 静态轨迹性能
    static_tracking_error = np.mean(np.abs(np.array(static_data['position']) - np.array(static_data['target_position'])))
    print(f"静态轨迹平均跟踪误差: {static_tracking_error:.4f}")
    
    # 动态跟踪性能
    dynamic_tracking_error = np.mean(np.abs(np.array(dynamic_data['position']) - np.array(dynamic_data['target_position'])))
    print(f"动态跟踪平均跟踪误差: {dynamic_tracking_error:.4f}")
    
    # 控制输出分析
    control_variance = np.var(dynamic_data['control_output'])
    print(f"动态跟踪控制输出方差: {control_variance:.4f}")
    
    print("\n=== 总结 ===")
    print("1. 静态轨迹规划：适用于预定义路径，跟踪精度高，但无法应对动态目标")
    print("2. 动态轨迹跟踪：适用于移动目标，实时响应，但需要预测算法和鲁棒控制")
    print("3. 实际应用中，两种方法可以结合使用，根据场景选择合适的策略")

if __name__ == "__main__":
    demo_tracking_comparison() 