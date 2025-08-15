"""
测试pytrajectory工具包功能并实现梯形和S型曲线
"""

import time
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import platform

class TrajectoryGenerator:
    """轨迹生成器类，实现梯形和S型曲线"""
    
    def __init__(self):
        # 移除重复的字体配置，使用全局配置
        # self.setup_chinese_font()
        pass
    
    def trapezoidal_trajectory(self, q0, q1, v_max, a_max):
        """
        梯形速度曲线轨迹规划
        
        Args:
            q0: 起始位置
            q1: 结束位置
            v_max: 最大速度
            a_max: 最大加速度
            
        Returns:
            tuple: (时间数组, 位置数组, 速度数组, 加速度数组)
        """
        # 计算总位移
        delta_q = q1 - q0
        
        # 计算梯形曲线的时间参数
        # 加速时间
        t_acc = v_max / a_max
        # 匀速时间
        t_const = (delta_q - 0.5 * a_max * t_acc**2) / v_max
        # 总时间
        t_total = 2 * t_acc + t_const
        
        # 如果匀速时间为负，说明无法达到最大速度
        if t_const < 0:
            # 三角形速度曲线
            t_acc = np.sqrt(delta_q / a_max)
            t_const = 0
            t_total = 2 * t_acc
            v_max = a_max * t_acc
        
        # 生成时间数组
        t = np.linspace(0, t_total, 100)
        pos = np.zeros_like(t)
        vel = np.zeros_like(t)
        acc = np.zeros_like(t)
        
        for i, ti in enumerate(t):
            if ti <= t_acc:
                # 加速段
                acc[i] = a_max
                vel[i] = a_max * ti
                pos[i] = q0 + 0.5 * a_max * ti**2
            elif ti <= t_acc + t_const:
                # 匀速段
                acc[i] = 0
                vel[i] = v_max
                pos[i] = q0 + 0.5 * a_max * t_acc**2 + v_max * (ti - t_acc)
            else:
                # 减速段
                acc[i] = -a_max
                vel[i] = v_max - a_max * (ti - t_acc - t_const)
                pos[i] = q1 - 0.5 * a_max * (t_total - ti)**2
        
        return t, pos, vel, acc
    
    def s_curve_trajectory(self, q0, q1, v_max, a_max, j_max):
        """
        S型曲线轨迹规划（7段式）
        
        Args:
            q0: 起始位置
            q1: 结束位置
            v_max: 最大速度
            a_max: 最大加速度
            j_max: 最大加加速度
            
        Returns:
            tuple: (时间数组, 位置数组, 速度数组, 加速度数组)
        """
        # 计算S型曲线的时间参数
        t_j = a_max / j_max  # 加加速度时间
        t_a = v_max / a_max  # 加速度时间
        
        # 如果t_a < 2*t_j，说明无法达到最大加速度
        if t_a < 2 * t_j:
            t_j = np.sqrt(v_max / j_max)
            t_a = 2 * t_j
            a_max = j_max * t_j
        
        # 计算总时间
        t_total = 4 * t_j + 2 * (t_a - 2 * t_j) + (q1 - q0) / v_max
        
        # 生成时间数组
        t = np.linspace(0, t_total, 100)
        pos = np.zeros_like(t)
        vel = np.zeros_like(t)
        acc = np.zeros_like(t)
        
        for i, ti in enumerate(t):
            if ti <= t_j:
                # 第1段：加加速度段
                acc[i] = j_max * ti
                vel[i] = 0.5 * j_max * ti**2
                pos[i] = q0 + (1/6) * j_max * ti**3
            elif ti <= t_a - t_j:
                # 第2段：恒加速度段
                acc[i] = a_max
                vel[i] = 0.5 * j_max * t_j**2 + a_max * (ti - t_j)
                pos[i] = q0 + (1/6) * j_max * t_j**3 + 0.5 * j_max * t_j**2 * (ti - t_j) + 0.5 * a_max * (ti - t_j)**2
            elif ti <= t_a:
                # 第3段：减加速度段
                dt = ti - (t_a - t_j)
                acc[i] = a_max - j_max * dt
                vel[i] = v_max - 0.5 * j_max * (t_j - dt)**2
                pos[i] = q0 + v_max * ti - (1/6) * j_max * (t_j - dt)**3
            elif ti <= t_total - t_a:
                # 第4段：匀速段
                acc[i] = 0
                vel[i] = v_max
                pos[i] = q0 + v_max * ti
            elif ti <= t_total - t_a + t_j:
                # 第5段：减加速度段
                dt = ti - (t_total - t_a)
                acc[i] = -j_max * dt
                vel[i] = v_max - 0.5 * j_max * dt**2
                pos[i] = q1 - v_max * (t_total - ti) + (1/6) * j_max * (t_total - ti)**3
            elif ti <= t_total - t_j:
                # 第6段：恒减速度段
                dt = ti - (t_total - t_a + t_j)
                acc[i] = -a_max
                vel[i] = v_max - 0.5 * j_max * t_j**2 - a_max * dt
                pos[i] = q1 - 0.5 * a_max * (t_total - ti)**2
            else:
                # 第7段：加减速度段
                dt = ti - (t_total - t_j)
                acc[i] = -a_max + j_max * dt
                vel[i] = 0.5 * j_max * (t_j - dt)**2
                pos[i] = q1 - (1/6) * j_max * (t_j - dt)**3
        
        return t, pos, vel, acc
    
    def plot_trajectory_comparison(self, t1, pos1, vel1, acc1, t2, pos2, vel2, acc2, 
                                 title1="梯形曲线", title2="S型曲线"):
        """绘制轨迹对比图"""
        fig, axes = plt.subplots(3, 2, figsize=(15, 10))
        
        # 梯形曲线
        axes[0, 0].plot(t1, pos1, 'b-', linewidth=2)
        axes[0, 0].set_title(f'{title1} - 位置')
        axes[0, 0].set_ylabel('位置')
        axes[0, 0].grid(True)
        
        axes[1, 0].plot(t1, vel1, 'g-', linewidth=2)
        axes[1, 0].set_title(f'{title1} - 速度')
        axes[1, 0].set_ylabel('速度')
        axes[1, 0].grid(True)
        
        axes[2, 0].plot(t1, acc1, 'r-', linewidth=2)
        axes[2, 0].set_title(f'{title1} - 加速度')
        axes[2, 0].set_xlabel('时间')
        axes[2, 0].set_ylabel('加速度')
        axes[2, 0].grid(True)
        
        # S型曲线
        axes[0, 1].plot(t2, pos2, 'b-', linewidth=2)
        axes[0, 1].set_title(f'{title2} - 位置')
        axes[0, 1].set_ylabel('位置')
        axes[0, 1].grid(True)
        
        axes[1, 1].plot(t2, vel2, 'g-', linewidth=2)
        axes[1, 1].set_title(f'{title2} - 速度')
        axes[1, 1].set_ylabel('速度')
        axes[1, 1].grid(True)
        
        axes[2, 1].plot(t2, acc2, 'r-', linewidth=2)
        axes[2, 1].set_title(f'{title2} - 加速度')
        axes[2, 1].set_xlabel('时间')
        axes[2, 1].set_ylabel('加速度')
        axes[2, 1].grid(True)
        
        plt.suptitle('轨迹规划对比')
        plt.tight_layout()
        plt.show()

def test_trajectory_generation():
    """测试轨迹生成功能"""
    # 移除重复的字体配置，使用全局配置
    # setup_chinese_font()
    
    print("=== 测试轨迹生成功能 ===")
    
    generator = TrajectoryGenerator()
    
    # 创建梯形速度曲线
    print("创建梯形速度曲线...")
    start_time = time.time()
    t_trap, pos_trap, vel_trap, acc_trap = generator.trapezoidal_trajectory(
        q0=0, q1=10, v_max=2, a_max=1
    )
    trap_time = time.time() - start_time
    print(f"梯形曲线创建时间: {trap_time:.6f}秒")
    
    # 创建S型曲线
    print("创建S型曲线...")
    start_time = time.time()
    t_s, pos_s, vel_s, acc_s = generator.s_curve_trajectory(
        q0=0, q1=10, v_max=2, a_max=1, j_max=4
    )
    s_curve_time = time.time() - start_time
    print(f"S型曲线创建时间: {s_curve_time:.6f}秒")
    
    # 绘制对比图
    generator.plot_trajectory_comparison(
        t_trap, pos_trap, vel_trap, acc_trap,
        t_s, pos_s, vel_s, acc_s
    )
    
    # 输出轨迹信息
    print(f"\n梯形曲线信息:")
    print(f"  总时间: {t_trap[-1]:.3f}秒")
    print(f"  最大速度: {np.max(vel_trap):.3f}")
    print(f"  最大加速度: {np.max(acc_trap):.3f}")
    
    print(f"\nS型曲线信息:")
    print(f"  总时间: {t_s[-1]:.3f}秒")
    print(f"  最大速度: {np.max(vel_s):.3f}")
    print(f"  最大加速度: {np.max(acc_s):.3f}")
    print(f"  最大加加速度: {np.max(np.abs(np.diff(acc_s))):.3f}")
    
    return trap_time, s_curve_time

if __name__ == "__main__":
    test_trajectory_generation() 