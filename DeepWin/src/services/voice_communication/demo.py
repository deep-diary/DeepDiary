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




def main():
    """主函数"""
    print("语音通信模块使用示例")
    print("=" * 50)
    
    try:
        # 运行各种示例
        example_basic_usage()
        
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
        for thread in threading.enumerate():
            if thread != threading.main_thread():
                print(f"等待线程 {thread.name} 结束...")
                thread.join(timeout=1.0)
        print("程序已退出")


if __name__ == "__main__":
    main()
