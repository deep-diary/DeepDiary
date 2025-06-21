"""
PID vs MPC 控制方法对比演示
展示两种不同的动态轨迹跟踪控制策略
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform
from scipy.optimize import minimize
import time

class PIDController:
    """PID控制器"""
    
    def __init__(self, kp=2.0, ki=0.1, kd=0.5):
        self.kp = kp  # 比例增益
        self.ki = ki  # 积分增益
        self.kd = kd  # 微分增益
        
        # 积分项和微分项
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_time = 0.0
        
        # 积分限幅
        self.integral_limit = 10.0
        
    def reset(self):
        """重置控制器状态"""
        self.integral = 0.0
        self.prev_error = 0.0
        self.prev_time = 0.0
    
    def control(self, target, current, current_time):
        """
        PID控制计算
        
        Args:
            target: 目标值
            current: 当前值
            current_time: 当前时间
            
        Returns:
            control_output: 控制输出
        """
        # 计算误差
        error = target - current
        
        # 计算时间间隔
        dt = current_time - self.prev_time if self.prev_time > 0 else 0.01
        
        # 积分项
        self.integral += error * dt
        self.integral = np.clip(self.integral, -self.integral_limit, self.integral_limit)
        
        # 微分项
        derivative = (error - self.prev_error) / dt if dt > 0 else 0
        
        # PID控制输出
        control_output = (self.kp * error + 
                         self.ki * self.integral + 
                         self.kd * derivative)
        
        # 更新状态
        self.prev_error = error
        self.prev_time = current_time
        
        return control_output

class MPCController:
    """模型预测控制器"""
    
    def __init__(self, prediction_horizon=10, control_horizon=5):
        self.prediction_horizon = prediction_horizon  # 预测步数
        self.control_horizon = control_horizon        # 控制步数
        
        # 权重矩阵
        self.Q = 1.0  # 状态误差权重
        self.R = 0.1  # 控制输入权重
        
        # 系统参数（简化的一阶系统）
        self.dt = 0.01  # 时间步长
        self.A = 1.0    # 状态转移矩阵
        self.B = self.dt  # 控制输入矩阵
        
    def predict_system_response(self, current_state, control_sequence):
        """
        预测系统响应
        
        Args:
            current_state: 当前状态
            control_sequence: 控制序列
            
        Returns:
            predicted_states: 预测状态序列
        """
        predicted_states = [current_state]
        state = current_state
        
        for i, control in enumerate(control_sequence):
            # 系统动力学方程（简化模型）
            next_state = self.A * state + self.B * control
            predicted_states.append(next_state)
            state = next_state
            
            # 如果控制序列用完，用最后一个控制值
            if i >= len(control_sequence) - 1:
                for _ in range(self.prediction_horizon - i - 1):
                    next_state = self.A * state + self.B * control
                    predicted_states.append(next_state)
                    state = next_state
                break
        
        return np.array(predicted_states)
    
    def objective_function(self, control_sequence, current_state, target_sequence):
        """
        目标函数（最小化预测误差和控制输入）
        
        Args:
            control_sequence: 控制序列
            current_state: 当前状态
            target_sequence: 目标序列
            
        Returns:
            cost: 总成本
        """
        # 预测系统响应
        predicted_states = self.predict_system_response(current_state, control_sequence)
        
        # 计算状态误差成本
        state_error_cost = 0
        for i, (predicted, target) in enumerate(zip(predicted_states, target_sequence)):
            state_error_cost += self.Q * (predicted - target) ** 2
        
        # 计算控制输入成本
        control_cost = 0
        for control in control_sequence:
            control_cost += self.R * control ** 2
        
        return state_error_cost + control_cost
    
    def control(self, target_sequence, current_state):
        """
        MPC控制计算
        
        Args:
            target_sequence: 目标序列
            current_state: 当前状态
            
        Returns:
            optimal_control: 最优控制输入
        """
        # 初始控制序列猜测
        initial_control = np.zeros(self.control_horizon)
        
        # 优化控制序列
        result = minimize(
            self.objective_function,
            initial_control,
            args=(current_state, target_sequence),
            method='SLSQP',
            bounds=[(-5.0, 5.0)] * self.control_horizon  # 控制输入限幅
        )
        
        if result.success:
            return result.x[0]  # 返回第一个控制输入
        else:
            return 0.0  # 优化失败时返回零控制

class TrajectoryTrackingDemo:
    """轨迹跟踪演示类"""
    
    def __init__(self):
        # 创建控制器
        self.pid_controller = PIDController(kp=2.0, ki=0.1, kd=0.5)
        self.mpc_controller = MPCController(prediction_horizon=10, control_horizon=5)
        
        # 系统状态
        self.pid_position = 0.0
        self.pid_velocity = 0.0
        self.mpc_position = 0.0
        self.mpc_velocity = 0.0
        
        # 数据记录
        self.time_data = []
        self.target_data = []
        self.pid_position_data = []
        self.pid_control_data = []
        self.mpc_position_data = []
        self.mpc_control_data = []
        
    def generate_target_trajectory(self, t):
        """
        生成目标轨迹
        
        Args:
            t: 时间
            
        Returns:
            target_position: 目标位置
        """
        # 复合轨迹：正弦 + 阶跃 + 斜坡
        if t < 2.0:
            # 0-2秒：正弦运动
            target_position = 2.0 * np.sin(2 * np.pi * 0.5 * t)
        elif t < 4.0:
            # 2-4秒：阶跃响应
            target_position = 1.0
        elif t < 6.0:
            # 4-6秒：斜坡运动
            target_position = 1.0 + 0.5 * (t - 4.0)
        else:
            # 6秒后：回到原点
            target_position = 0.0
        
        return target_position
    
    def simulate_tracking(self, duration=8.0, dt=0.01):
        """
        模拟轨迹跟踪
        
        Args:
            duration: 仿真持续时间
            dt: 时间步长
        """
        print("=== PID vs MPC 轨迹跟踪对比演示 ===")
        print(f"仿真时间: {duration}秒")
        print(f"时间步长: {dt}秒")
        
        # 重置控制器
        self.pid_controller.reset()
        
        # 重置数据记录
        self.time_data = []
        self.target_data = []
        self.pid_position_data = []
        self.pid_control_data = []
        self.mpc_position_data = []
        self.mpc_control_data = []
        
        current_time = 0.0
        
        while current_time <= duration:
            # 生成目标轨迹
            target_position = self.generate_target_trajectory(current_time)
            
            # PID控制
            pid_control = self.pid_controller.control(target_position, self.pid_position, current_time)
            self.pid_velocity += pid_control * dt
            self.pid_position += self.pid_velocity * dt
            
            # 限制PID系统状态
            self.pid_velocity = np.clip(self.pid_velocity, -10.0, 10.0)
            self.pid_position = np.clip(self.pid_position, -20.0, 20.0)
            
            # MPC控制
            # 生成目标序列
            target_sequence = []
            for i in range(self.mpc_controller.prediction_horizon):
                future_time = current_time + i * dt
                target_sequence.append(self.generate_target_trajectory(future_time))
            
            # MPC控制计算
            mpc_control = self.mpc_controller.control(target_sequence, self.mpc_position)
            self.mpc_velocity += mpc_control * dt
            self.mpc_position += self.mpc_velocity * dt
            
            # 限制MPC系统状态
            self.mpc_velocity = np.clip(self.mpc_velocity, -10.0, 10.0)
            self.mpc_position = np.clip(self.mpc_position, -20.0, 20.0)
            
            # 记录数据
            self.time_data.append(current_time)
            self.target_data.append(target_position)
            self.pid_position_data.append(self.pid_position)
            self.pid_control_data.append(pid_control)
            self.mpc_position_data.append(self.mpc_position)
            self.mpc_control_data.append(mpc_control)
            
            current_time += dt
        
        print("仿真完成")
    
    def plot_results(self):
        """绘制结果对比图"""
        fig, axes = plt.subplots(3, 2, figsize=(15, 12))
        
        # 位置跟踪对比
        axes[0, 0].plot(self.time_data, self.target_data, 'k--', linewidth=2, label='目标轨迹')
        axes[0, 0].plot(self.time_data, self.pid_position_data, 'b-', linewidth=2, label='PID跟踪')
        axes[0, 0].set_title('PID控制 - 位置跟踪')
        axes[0, 0].set_ylabel('位置')
        axes[0, 0].legend()
        axes[0, 0].grid(True)
        
        axes[0, 1].plot(self.time_data, self.target_data, 'k--', linewidth=2, label='目标轨迹')
        axes[0, 1].plot(self.time_data, self.mpc_position_data, 'r-', linewidth=2, label='MPC跟踪')
        axes[0, 1].set_title('MPC控制 - 位置跟踪')
        axes[0, 1].set_ylabel('位置')
        axes[0, 1].legend()
        axes[0, 1].grid(True)
        
        # 控制输出对比
        axes[1, 0].plot(self.time_data, self.pid_control_data, 'b-', linewidth=2)
        axes[1, 0].set_title('PID控制 - 控制输出')
        axes[1, 0].set_ylabel('控制输出')
        axes[1, 0].grid(True)
        
        axes[1, 1].plot(self.time_data, self.mpc_control_data, 'r-', linewidth=2)
        axes[1, 1].set_title('MPC控制 - 控制输出')
        axes[1, 1].set_ylabel('控制输出')
        axes[1, 1].grid(True)
        
        # 跟踪误差对比
        pid_error = np.array(self.pid_position_data) - np.array(self.target_data)
        mpc_error = np.array(self.mpc_position_data) - np.array(self.target_data)
        
        axes[2, 0].plot(self.time_data, pid_error, 'b-', linewidth=2)
        axes[2, 0].set_title('PID控制 - 跟踪误差')
        axes[2, 0].set_xlabel('时间')
        axes[2, 0].set_ylabel('误差')
        axes[2, 0].grid(True)
        
        axes[2, 1].plot(self.time_data, mpc_error, 'r-', linewidth=2)
        axes[2, 1].set_title('MPC控制 - 跟踪误差')
        axes[2, 1].set_xlabel('时间')
        axes[2, 1].set_ylabel('误差')
        axes[2, 1].grid(True)
        
        plt.suptitle('PID vs MPC 轨迹跟踪控制对比')
        plt.tight_layout()
        plt.show()
    
    def analyze_performance(self):
        """分析控制性能"""
        print("\n=== 性能分析 ===")
        
        # 计算跟踪误差
        pid_error = np.array(self.pid_position_data) - np.array(self.target_data)
        mpc_error = np.array(self.mpc_position_data) - np.array(self.target_data)
        
        # 统计指标
        pid_rmse = np.sqrt(np.mean(pid_error**2))
        mpc_rmse = np.sqrt(np.mean(mpc_error**2))
        
        pid_max_error = np.max(np.abs(pid_error))
        mpc_max_error = np.max(np.abs(mpc_error))
        
        pid_control_variance = np.var(self.pid_control_data)
        mpc_control_variance = np.var(self.mpc_control_data)
        
        print(f"PID控制性能:")
        print(f"  均方根误差 (RMSE): {pid_rmse:.4f}")
        print(f"  最大误差: {pid_max_error:.4f}")
        print(f"  控制输出方差: {pid_control_variance:.4f}")
        
        print(f"\nMPC控制性能:")
        print(f"  均方根误差 (RMSE): {mpc_rmse:.4f}")
        print(f"  最大误差: {mpc_max_error:.4f}")
        print(f"  控制输出方差: {mpc_control_variance:.4f}")
        
        print(f"\n性能对比:")
        if mpc_rmse < pid_rmse:
            improvement = (pid_rmse - mpc_rmse) / pid_rmse * 100
            print(f"  MPC在跟踪精度上优于PID {improvement:.1f}%")
        else:
            improvement = (mpc_rmse - pid_rmse) / mpc_rmse * 100
            print(f"  PID在跟踪精度上优于MPC {improvement:.1f}%")
        
        if mpc_control_variance < pid_control_variance:
            improvement = (pid_control_variance - mpc_control_variance) / pid_control_variance * 100
            print(f"  MPC在控制平滑性上优于PID {improvement:.1f}%")
        else:
            improvement = (mpc_control_variance - pid_control_variance) / mpc_control_variance * 100
            print(f"  PID在控制平滑性上优于MPC {improvement:.1f}%")

def demo_pid_vs_mpc():
    """演示PID vs MPC对比"""
    demo = TrajectoryTrackingDemo()
    
    # 运行仿真
    demo.simulate_tracking(duration=8.0, dt=0.01)
    
    # 绘制结果
    demo.plot_results()
    
    # 分析性能
    demo.analyze_performance()
    
    print("\n=== 控制方法特点总结 ===")
    print("PID控制:")
    print("  ✓ 简单易实现，计算量小")
    print("  ✓ 参数调节相对简单")
    print("  ✗ 无法处理约束条件")
    print("  ✗ 对系统模型依赖较少")
    print("  ✗ 无法预测未来目标变化")
    
    print("\nMPC控制:")
    print("  ✓ 可以处理约束条件")
    print("  ✓ 能够预测未来目标变化")
    print("  ✓ 优化控制性能")
    print("  ✗ 计算复杂度高")
    print("  ✗ 需要系统模型")
    print("  ✗ 参数调节相对复杂")
    
    print("\n=== 应用建议 ===")
    print("1. 简单跟踪任务：推荐使用PID控制")
    print("2. 复杂约束任务：推荐使用MPC控制")
    print("3. 实时性要求高：推荐使用PID控制")
    print("4. 精度要求高：推荐使用MPC控制")

if __name__ == "__main__":
    demo_pid_vs_mpc() 