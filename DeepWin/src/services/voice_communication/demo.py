#!/usr/bin/env python3
"""
语音通信模块使用示例

展示如何使用VoiceManager和VoiceDaemonManager
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.services.voice_communication import VoiceManager
from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager


def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")
    
    voice_manager = None
    try:
        # 初始化
        log_manager = LogManager()
        config_manager = ConfigManager(log_manager=log_manager)
        voice_manager = VoiceManager(log_manager, config_manager)
        
        print("✓ 语音管理器初始化成功")
        
        # 连接信号
        voice_manager.conversation_started.connect(lambda dialog_id: print(f"对话开始: {dialog_id}"))
        voice_manager.conversation_stopped.connect(lambda: print("对话结束"))
        voice_manager.conversation_error.connect(lambda error: print(f"错误: {error}"))
        voice_manager.command_parsed.connect(lambda commands: print(f"命令: {commands}"))
        
        # 启动语音对话
        success = voice_manager.start_voice_conversation()
        if success:
            print("✓ 语音对话启动成功")
            
            # 等待一段时间
            print("等待10秒...")
            time.sleep(10)
            
            # 获取状态
            status = voice_manager.get_conversation_status()
            print(f"对话状态: {status}")
            
            # 停止语音对话
            print("正在停止语音对话...")
            voice_manager.stop_voice_conversation()
            print("✓ 语音对话已停止")
        else:
            print("✗ 语音对话启动失败")
        
    except Exception as e:
        print(f"基本使用示例出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保资源被清理
        if voice_manager:
            print("正在清理资源...")
            try:
                voice_manager.cleanup()
                print("✓ 资源清理完成")
            except Exception as e:
                print(f"✗ 资源清理失败: {e}")
        
        # 等待一下确保线程完全退出
        time.sleep(1)
        print("示例运行完成")

def example_text_usage():
    """文本对话示例"""
    print("=== 文本对话示例 ===")
    voice_manager = None
    try:
        # 初始化
        log_manager = LogManager()
        config_manager = ConfigManager(log_manager=log_manager)
        voice_manager = VoiceManager(log_manager, config_manager)
        
        print("✓ 语音管理器初始化成功")
        
        # 检查对话实例是否创建成功
        if not voice_manager.conversation:
            print("✗ 对话实例创建失败")
            return
            
        print("✓ 对话实例创建成功")
        
        # 连接信号
        voice_manager.conversation_started.connect(lambda dialog_id: print(f"对话开始: {dialog_id}"))
        voice_manager.conversation_stopped.connect(lambda: print("对话结束"))

        # 启动文本对话
        success = voice_manager.start_text_conversation()
        if success:
            print("✓ 文本对话启动成功")
        else:
            print("✗ 文本对话启动失败")
            
    except Exception as e:
        print(f"文本对话示例出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保资源被清理
        if voice_manager:
            print("正在清理资源...")
            try:
                voice_manager.cleanup()
                print("✓ 资源清理完成")
            except Exception as e:
                print(f"✗ 资源清理失败: {e}")
                
        # 等待一下确保线程完全退出
        time.sleep(1)
        print("示例运行完成")

def main():
    """主函数"""
    print("语音通信模块使用示例")
    print("=" * 50)
    
    try:
        # 先运行基本初始化测试
        # test_basic_initialization()
        
        print("\n" + "=" * 50)
        
        # 如果基本测试通过，再运行完整示例
        # example_basic_usage()
        example_text_usage()
        
        print("\n" + "=" * 50)
        print("所有示例运行完成！")
        
    except KeyboardInterrupt:
        print("\n用户中断程序")
        print("正在清理资源...")
    except Exception as e:
        print(f"\n程序运行出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 确保程序完全退出
        print("程序退出中...")
        # 强制清理所有线程
        import threading
        active_threads = [t for t in threading.enumerate() if t != threading.main_thread()]
        if active_threads:
            print(f"发现 {len(active_threads)} 个活跃线程，正在清理...")
            
            # 第一轮：等待线程自然结束
            for thread in active_threads:
                print(f"等待线程 {thread.name} ({thread.ident}) 结束...")
                thread.join(timeout=1.0)
                if thread.is_alive():
                    print(f"警告: 线程 {thread.name} 未能在超时时间内结束")
            
            # 第二轮：检查还有哪些线程活着
            remaining_threads = [t for t in threading.enumerate() if t != threading.main_thread() and t.is_alive()]
            if remaining_threads:
                print(f"仍有 {len(remaining_threads)} 个线程未结束:")
                for thread in remaining_threads:
                    print(f"  - {thread.name} ({thread.ident}) - {'守护线程' if thread.daemon else '非守护线程'}")
                
                # 对于非守护线程，尝试强制中断（如果可能）
                for thread in remaining_threads:
                    if not thread.daemon:
                        print(f"尝试强制中断非守护线程: {thread.name}")
                        # 注意：Python中无法强制杀死线程，只能等待
            else:
                print("所有线程已成功清理")
        else:
            print("没有发现活跃线程")
        print("程序已退出")

def test_basic_initialization():
    """测试基本初始化功能"""
    print("=== 基本初始化测试 ===")
    try:
        log_manager = LogManager()
        config_manager = ConfigManager(log_manager=log_manager)
        voice_manager = VoiceManager(log_manager, config_manager)
        
        print("✓ 语音管理器初始化成功")
        print(f"✓ 对话实例: {'已创建' if voice_manager.conversation else '未创建'}")
        print(f"✓ 配置加载: {'成功' if voice_manager.app_id else '失败'}")
        
        voice_manager.cleanup()
        print("✓ 资源清理成功")
        
    except Exception as e:
        print(f"✗ 基本初始化测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
