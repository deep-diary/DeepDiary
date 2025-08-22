#!/usr/bin/env python3
"""
DeepWin Web演示启动脚本
用于启动Streamlit Web演示界面
"""

import subprocess
import sys
import os
from pathlib import Path

def check_dependencies():
    """检查依赖是否安装"""
    required_packages = ['streamlit', 'plotly', 'pandas', 'numpy']
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

def start_web_demo():
    """启动Web演示"""
    # 获取项目根目录（修正路径）
    project_root = Path(__file__).parent.parent
    web_demo_dir = project_root / "web_demo"
    
    if not web_demo_dir.exists():
        print(f"❌ Web演示目录不存在: {web_demo_dir}")
        return False
    
    # 检查主文件是否存在
    main_file = web_demo_dir / "main.py"
    if not main_file.exists():
        print(f"❌ 主文件不存在: {main_file}")
        return False
    
    print(f"🚀 启动DeepWin Web演示...")
    print(f"📁 工作目录: {web_demo_dir}")
    print(f"📄 主文件: {main_file}")
    
    try:
        # 切换到Web演示目录
        os.chdir(web_demo_dir)
        
        # 启动Streamlit应用
        print("🌐 正在启动Streamlit服务器...")
        print("📱 请在浏览器中访问显示的地址")
        print("⏹️  按 Ctrl+C 停止服务器")
        print("-" * 50)
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "main.py",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False
    
    return True

def main():
    """主函数"""
    print("🚀 DeepWin Web演示启动器")
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
    
    # 启动Web演示
    if start_web_demo():
        print("✅ Web演示启动完成")
        return 0
    else:
        print("❌ Web演示启动失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
