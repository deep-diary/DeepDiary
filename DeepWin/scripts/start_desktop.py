#!/usr/bin/env python3
"""
DeepWin 桌面应用启动脚本
用于启动Qt桌面应用
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    required_packages = ['PySide6']  # 可以根据实际使用的Qt库调整
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    return missing_packages

def install_dependencies():
    """安装缺失的依赖"""
    missing_packages = check_dependencies()
    
    if missing_packages:
        print(f"🔍 发现缺失的依赖包: {', '.join(missing_packages)}")
        print("📦 正在安装...")
        
        for package in missing_packages:
            try:
                print(f"正在安装 {package}...")
                subprocess.run([sys.executable, "-m", "pip", "install", package], check=True)
                print(f"✅ {package} 安装成功")
            except subprocess.CalledProcessError as e:
                print(f"❌ {package} 安装失败: {e}")
                return False
        
        print("🎉 所有依赖安装完成！")
        return True
    else:
        print("✅ 所有依赖已安装")
        return True

def start_desktop_app():
    """启动桌面应用"""
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    main_file = project_root / "main.py"
    
    if not main_file.exists():
        print(f"❌ 主文件不存在: {main_file}")
        return False
    
    print(f"🚀 启动DeepWin 桌面应用...")
    print(f"📁 工作目录: {project_root}")
    print(f"📄 主文件: {main_file}")
    
    try:
        # 切换到项目根目录
        os.chdir(project_root)
        
        # 启动桌面应用
        print("🖥️ 正在启动桌面应用...")
        print("⏹️  按 Ctrl+C 停止应用")
        print("-" * 50)
        
        subprocess.run([sys.executable, "main.py"])
        
    except KeyboardInterrupt:
        print("\n🛑 应用已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 DeepWin 桌面应用启动器")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return 1
    
    print(f"🐍 Python版本: {sys.version}")
    
    # 检查并安装依赖
    if not install_dependencies():
        print("❌ 依赖安装失败，无法启动")
        return 1
    
    # 启动桌面应用
    if start_desktop_app():
        print("✅ 桌面应用启动完成")
        return 0
    else:
        print("❌ 桌面应用启动失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
