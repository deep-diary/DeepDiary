"""
机器人轨迹规划模块
替代pyrobotics包，提供轨迹插值、五次多项式规划等功能
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import CubicSpline
import matplotlib.font_manager as fm
import platform
# from matplotlib_config import setup_chinese_font

class RobotTrajectory:
    """机器人轨迹规划类"""
    
    def __init__(self):
        """初始化轨迹规划器"""
        # 移除重复的字体配置，使用全局配置
        # setup_chinese_font()
    
    def quintic_polynomial_trajectory(self, t0, tf, q0, qf, v0=0, vf=0, a0=0, af=0, interp_points=50):
        """
        五次多项式轨迹规划
        
        Args:
            t0: 起始时间
            tf: 结束时间
            q0: 起始位置
            qf: 结束位置
            v0: 起始速度 (默认0)
            vf: 结束速度 (默认0)
            a0: 起始加速度 (默认0)
            af: 结束加速度 (默认0)
            
        Returns:
            tuple: (时间数组, 位置数组, 速度数组, 加速度数组)
        """
        # 构建系数矩阵
        T = tf - t0
        A = np.array([
            [T**5, T**4, T**3, T**2, T, 1],
            [5*T**4, 4*T**3, 3*T**2, 2*T, 1, 0],
            [20*T**3, 12*T**2, 6*T, 2, 0, 0],
            [0, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 1, 0],
            [0, 0, 0, 2, 0, 0]
        ])
        
        b = np.array([qf, vf, af, q0, v0, a0])
        
        # 求解系数
        coeffs = np.linalg.solve(A, b)
        
        # 生成轨迹
        t = np.linspace(t0, tf, interp_points)
        pos = np.zeros_like(t)
        vel = np.zeros_like(t)
        acc = np.zeros_like(t)
        
        for i, ti in enumerate(t):
            dt = ti - t0
            pos[i] = (coeffs[0]*dt**5 + coeffs[1]*dt**4 + coeffs[2]*dt**3 + 
                     coeffs[3]*dt**2 + coeffs[4]*dt + coeffs[5])
            vel[i] = (5*coeffs[0]*dt**4 + 4*coeffs[1]*dt**3 + 3*coeffs[2]*dt**2 + 
                     2*coeffs[3]*dt + coeffs[4])
            acc[i] = (20*coeffs[0]*dt**3 + 12*coeffs[1]*dt**2 + 6*coeffs[2]*dt + 
                     2*coeffs[3])
        
        return t, pos, vel, acc
    
    def cubic_spline_trajectory(self, waypoints, times, bc_type='clamped', interp_points=50):
        """
        三次样条轨迹插值
        
        Args:
            waypoints: 路径点数组
            times: 时间点数组
            bc_type: 边界条件类型 ('natural', 'clamped', 'periodic')
            interp_points: 插值点数
            
        Returns:
            tuple: (时间数组, 位置数组, 速度数组, 加速度数组)
        """
        # 创建三次样条插值器
        if bc_type == 'clamped':
            # 首尾速度为零
            cs = CubicSpline(times, waypoints, bc_type=((1, 0), (1, 0)))
        elif bc_type == 'periodic':
            # 周期性边界条件
            cs = CubicSpline(times, waypoints, bc_type='periodic')
        else:
            # 自然边界条件（默认）
            cs = CubicSpline(times, waypoints)
        
        # 生成插值轨迹
        t_interp = np.linspace(times[0], times[-1], interp_points)
        pos_interp = cs(t_interp)
        vel_interp = cs(t_interp, 1)
        acc_interp = cs(t_interp, 2)
        
        return t_interp, pos_interp, vel_interp, acc_interp
    
    def linear_trajectory_with_parabolic_blends(self, waypoints, times, blend_time=0.1, interp_points=50):
        """
        带抛物线过渡的线性轨迹
        
        Args:
            waypoints: 路径点数组
            times: 时间点数组
            blend_time: 过渡时间
            interp_points: 插值点数
            
        Returns:
            tuple: (时间数组, 位置数组, 速度数组, 加速度数组)
        """
        # 实现带抛物线过渡的线性轨迹
        # 这里简化实现，实际应用中需要更复杂的算法
        return self.cubic_spline_trajectory(waypoints, times, 'clamped', interp_points=interp_points)
    
    def plot_trajectory(self, t, pos, vel, acc, title="轨迹规划结果", original_waypoints=None, original_times=None):
        """
        绘制轨迹图
        
        Args:
            t: 时间数组
            pos: 位置数组
            vel: 速度数组
            acc: 加速度数组
            title: 图表标题
            original_waypoints: 原始轨迹点数组（可选）
            original_times: 原始轨迹点对应的时间数组（可选）
        """
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(10, 8))
        
        # 位置图
        ax1.plot(t, pos, 'b-', linewidth=2, label='规划轨迹')
        if original_waypoints is not None and original_times is not None:
            ax1.plot(original_times, original_waypoints, 'ro', markersize=8, label='原始轨迹点')
            ax1.legend()
        ax1.set_title('位置-时间曲线')
        ax1.set_ylabel('位置')
        ax1.grid(True)
        
        # 速度图
        ax2.plot(t, vel, 'g-', linewidth=2)
        ax2.set_title('速度-时间曲线')
        ax2.set_ylabel('速度')
        ax2.grid(True)
        
        # 加速度图
        ax3.plot(t, acc, 'r-', linewidth=2)
        ax3.set_title('加速度-时间曲线')
        ax3.set_xlabel('时间')
        ax3.set_ylabel('加速度')
        ax3.grid(True)
        
        plt.suptitle(title)
        plt.tight_layout()
        plt.show()
    
    def generate_waypoint_trajectory(self, waypoints, times, stop_in_point=True, interp_points=50):
        """
        生成多路径点轨迹
        
        Args:
            waypoints: 路径点列表
            times: 每个路径点对应的时间点数组
            stop_in_point (bool): 如果为 True, 使用五次多项式在每个路径点停止。
                                  如果为 False, 使用三次样条插值平滑经过路径点。
            interp_points: 插值点数
            
        Returns:
            tuple: (时间数组, 位置数组, 速度数组, 加速度数组)
        """
        n_waypoints = len(waypoints)
        if n_waypoints < 2:
            raise ValueError("至少需要2个路径点")
        if len(waypoints) != len(times):
            raise ValueError("路径点和时间点的数量必须一致")
        
        if stop_in_point:
            # 使用五次多项式在每个点停止 (v=0, a=0)
            all_t, all_pos, all_vel, all_acc = [], [], [], []
            
            for i in range(n_waypoints - 1):
                t, pos, vel, acc = self.quintic_polynomial_trajectory(
                    times[i], times[i+1], 
                    waypoints[i], waypoints[i+1], # v0, vf, a0, af all default to 0
                    interp_points=interp_points # 插值点数
                )
                
                if i < n_waypoints - 2:
                    all_t.extend(t[:-1])
                    all_pos.extend(pos[:-1])
                    all_vel.extend(vel[:-1])
                    all_acc.extend(acc[:-1])
                else:
                    all_t.extend(t)
                    all_pos.extend(pos)
                    all_vel.extend(vel)
                    all_acc.extend(acc)
            
            return np.array(all_t), np.array(all_pos), np.array(all_vel), np.array(all_acc)
        
        else:
            # 使用三次样条插值平滑经过
            return self.cubic_spline_trajectory(waypoints, times, interp_points=interp_points)

def demo_trajectory_planning():
    """演示轨迹规划功能"""
    trajectory = RobotTrajectory()
    
    print("=== 多路径点轨迹规划演示 ===")
    waypoints = [0, 5, -2, 8, 0, 10, 15, 20]
    total_time = 10
    
    # 构造一个时间不均匀的数组来测试
    original_times = np.linspace(0, total_time, len(waypoints))
    original_times[2] = 2.5 # 调整部分时间点
    original_times[4] = 4.5

    # 1. 在每个路径点停止 (stop_in_point=True, 使用五次多项式)
    t_stop, pos_stop, vel_stop, acc_stop = trajectory.generate_waypoint_trajectory(
        waypoints, original_times, stop_in_point=True
    )
    trajectory.plot_trajectory(t_stop, pos_stop, vel_stop, acc_stop, "多路径点轨迹 (在每个点停止 - Quintic)",
                              original_waypoints=waypoints, original_times=original_times)
    
    # 2. 平滑经过路径点 (stop_in_point=False, 使用三次样条)
    t_smooth, pos_smooth, vel_smooth, acc_smooth = trajectory.generate_waypoint_trajectory(
        waypoints, original_times, stop_in_point=False
    )
    trajectory.plot_trajectory(t_smooth, pos_smooth, vel_smooth, acc_smooth, "多路径点轨迹 (平滑经过 - Cubic Spline)",
                              original_waypoints=waypoints, original_times=original_times)

if __name__ == "__main__":
    demo_trajectory_planning() 