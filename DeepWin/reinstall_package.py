#!/usr/bin/env python3
"""
重新安装DeepWin包的脚本
"""

import subprocess
import sys
from pathlib import Path

def reinstall_deepwin():
    """重新安装DeepWin包"""
    
    print("开始重新安装 DeepWin 包...")
    print("=" * 50)
    
    # 获取当前目录
    current_dir = Path(__file__).parent.resolve()
    print(f"当前目录: {current_dir}")
    
    # 检查是否在正确的目录
    if not (current_dir / "setup.py").exists():
        print("❌ 错误: 请在DeepWin根目录下运行此脚本")
        return False
    
    try:
        # 先卸载旧版本（如果存在）
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "uninstall", "deepwin", "-y"
            ])
            print("✅ 旧版本卸载成功")
        except:
            pass
        
        # 重新安装
        print("重新安装DeepWin包...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-e", str(current_dir)
        ])
        
        print("✅ DeepWin包安装成功")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 包安装失败: {e}")
        return False
    
    # 验证安装
    print("\n验证安装...")
    try:
        # 测试导入
        import src
        print(f"✅ src包导入成功: {deepwin.__file__}")
        
        # 测试子模块导入
        from src import services, data_management
        print("✅ 子模块导入成功")
        
        # 测试具体功能
        from deepwin.data_management.log_manager import LogManager
        print("✅ LogManager导入成功")
        
    except ImportError as e:
        print(f"❌ 包验证失败: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 DeepWin包安装完成！")
    print("\n现在您可以使用以下方式导入:")
    print("  import src")
    print("  from src import services, data_management")
    print("  from deepwin.data_management.log_manager import LogManager")
    
    return True

def main():
    """主函数"""
    return reinstall_deepwin()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
