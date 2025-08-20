#!/usr/bin/env python3
"""
清理残留Python线程的脚本
"""

import os
import psutil
import time

def cleanup_python_threads():
    """清理残留的Python线程"""
    print("开始清理残留的Python线程...")
    
    # 查找所有Python进程
    python_processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if 'python' in proc.info['name'].lower():
                cmdline = proc.info['cmdline']
                if cmdline and any('main.py' in arg for arg in cmdline):
                    python_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if not python_processes:
        print("没有找到运行中的Python主程序进程")
        return
    
    print(f"找到 {len(python_processes)} 个Python主程序进程:")
    for proc in python_processes:
        print(f"  PID: {proc.info['pid']}, 命令: {' '.join(proc.info['cmdline'])}")
    
    # 终止进程
    for proc in python_processes:
        try:
            print(f"正在终止进程 PID: {proc.info['pid']}...")
            proc.terminate()
            proc.wait(timeout=5)
            print(f"进程 PID: {proc.info['pid']} 已终止")
        except psutil.TimeoutExpired:
            print(f"进程 PID: {proc.info['pid']} 未能在5秒内终止，强制杀死...")
            proc.kill()
        except Exception as e:
            print(f"终止进程 PID: {proc.info['pid']} 失败: {e}")
    
    print("Python线程清理完成！")

def check_system_resources():
    """检查系统资源使用情况"""
    print("\n系统资源使用情况:")
    
    # CPU使用率
    cpu_percent = psutil.cpu_percent(interval=1)
    print(f"CPU使用率: {cpu_percent}%")
    
    # 内存使用情况
    memory = psutil.virtual_memory()
    print(f"内存使用率: {memory.percent}%")
    print(f"可用内存: {memory.available / (1024**3):.2f} GB")
    
    # 磁盘使用情况
    disk = psutil.disk_usage('/')
    print(f"磁盘使用率: {disk.percent}%")
    print(f"可用磁盘空间: {disk.free / (1024**3):.2f} GB")

if __name__ == "__main__":
    print("=== Python线程清理工具 ===")
    
    # 检查系统资源
    check_system_resources()
    
    # 清理线程
    cleanup_python_threads()
    
    # 再次检查系统资源
    print("\n清理后的系统资源:")
    check_system_resources()
    
    print("\n清理完成！")
