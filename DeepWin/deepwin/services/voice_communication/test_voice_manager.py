#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VoiceManager 测试脚本

用于测试优化后的VoiceManager各项功能是否正常工作
"""

import os
import sys
import time
import logging
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入必要的模块
from deepwin.data_management.log_manager import LogManager
from deepwin.data_management.config_manager import ConfigManager
from deepwin.services.voice_communication.voice_manager import VoiceManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class VoiceManagerTester:
    """VoiceManager测试类"""
    
    def __init__(self, log_manager: LogManager, config_manager: ConfigManager):
        """初始化测试器"""
        self.logger = logging.getLogger(__name__)
        self.log_manager = log_manager
        self.config_manager = config_manager
        self.voice_manager = None
        
    def setup(self):
        """设置测试环境"""
        try:
            self.logger.info("开始设置测试环境...")
            
            # 初始化日志管理器
            self.log_manager = LogManager()
            
            # 初始化配置管理器
            self.config_manager = ConfigManager(log_manager=self.log_manager)
            
            # 创建VoiceManager实例
            self.voice_manager = VoiceManager(
                log_manager=self.log_manager,
                config_manager=self.config_manager
            )
            
            self.logger.info("测试环境设置完成")
            return True
            
        except Exception as e:
            self.logger.error(f"设置测试环境失败: {e}")
            return False
    
    def test_basic_functionality(self):
        """测试基本功能"""
        self.logger.info("=== 测试基本功能 ===")
        
        try:
            # 测试状态查询
            status = self.voice_manager.get_conversation_status()
            self.logger.info(f"初始状态: {status}")
            
            # 测试使能状态
            enable_status = self.voice_manager.get_enable_status()
            self.logger.info(f"使能状态: {enable_status}")
            
            # 测试队列状态
            queue_status = self.voice_manager.get_queue_status()
            self.logger.info(f"队列状态: {queue_status}")
            
            self.logger.info("基本功能测试通过")
            return True
            
        except Exception as e:
            self.logger.error(f"基本功能测试失败: {e}")
            return False
    
    def test_text_conversation(self):
        """测试文本对话功能"""
        self.logger.info("=== 测试文本对话功能 ===")
        
        try:
            # 测试开始文本对话
            success = self.voice_manager.start_text_conversation("你好，这是一个测试")
            if success:
                self.logger.info("文本对话启动成功")
                
                # 等待一下
                time.sleep(2)
                
                # 测试发送文本消息
                success = self.voice_manager.send_text_message("继续对话测试")
                if success:
                    self.logger.info("文本消息发送成功")
                else:
                    self.logger.error("文本消息发送失败")
                
                # 测试停止对话
                success = self.voice_manager.stop_conversation()
                if success:
                    self.logger.info("对话停止成功")
                else:
                    self.logger.error("对话停止失败")
            else:
                self.logger.error("文本对话启动失败")
            
            self.logger.info("文本对话功能测试完成")
            return True
            
        except Exception as e:
            self.logger.error(f"文本对话功能测试失败: {e}")
            return False
    
    def test_message_queue(self):
        """测试消息队列功能"""
        self.logger.info("=== 测试消息队列功能 ===")
        
        try:
            # 添加任务到队列
            self.voice_manager.add_task_to_queue('text', text='队列测试任务1')
            self.voice_manager.add_task_to_queue('text', text='队列测试任务2')
            
            # 检查队列状态
            queue_status = self.voice_manager.get_queue_status()
            self.logger.info(f"添加任务后队列状态: {queue_status}")
            
            # 等待工作线程处理
            time.sleep(3)
            
            # 再次检查队列状态
            queue_status = self.voice_manager.get_queue_status()
            self.logger.info(f"处理任务后队列状态: {queue_status}")
            
            self.logger.info("消息队列功能测试完成")
            return True
            
        except Exception as e:
            self.logger.error(f"消息队列功能测试失败: {e}")
            return False
        
    def test_transcript_queue(self):
        """测试转录队列功能"""
        self.logger.info("=== 测试转录队列功能 ===")
    
        # 添加任务到队列
        try:
            self.voice_manager.add_task_to_queue('transcript', text='转录测试任务1')
            self.voice_manager.add_task_to_queue('text', text='队列测试任务1')
            self.voice_manager.add_task_to_queue('transcript', text='转录测试任务2')
            return True
        except Exception as e:
            self.logger.error(f"转录队列功能测试失败: {e}")
            return False
        
    def test_vqa_functionality(self):
        """测试VQA功能"""
        self.logger.info("=== 测试VQA功能 ===")
        try:
            data = {
                'img': 'jpeg-bridge.jpg',
                'prompt': '请描述下这张图片？'
            }
            self.voice_manager.add_task_to_queue('vqa', data=data)
            return True
        except Exception as e:  
            self.logger.error(f"VQA功能测试失败: {e}")
            return False

    
    def test_voice_enabled_control(self):
        """测试语音使能控制"""
        self.logger.info("=== 测试语音使能控制 ===")
        
        try:
            # 测试启用语音
            self.voice_manager.set_voice_enabled(True)
            self.logger.info("语音使能已启用")
            
            # 检查状态
            enable_status = self.voice_manager.get_enable_status()
            self.logger.info(f"启用后状态: {enable_status}")
            
            # 等待一下
            time.sleep(20)
            
            # 测试禁用语音
            self.voice_manager.set_voice_enabled(False)
            self.logger.info("语音使能已禁用")
            
            # 检查状态
            enable_status = self.voice_manager.get_enable_status()
            self.logger.info(f"禁用后状态: {enable_status}")
            
            self.logger.info("语音使能控制测试完成")
            return True
            
        except Exception as e:
            self.logger.error(f"语音使能控制测试失败: {e}")
            return False
    
    def test_live_video_control(self):
        """测试实时视频控制"""
        self.logger.info("=== 测试实时视频控制 ===")
        
        try:
            # 测试启用实时视频
            # 测试启用语音
            self.voice_manager.set_voice_enabled(True)
            self.voice_manager.set_live_video_enabled(True)
            self.logger.info("实时视频使能已启用")
            
            # 检查状态
            enable_status = self.voice_manager.get_enable_status()
            self.logger.info(f"启用后状态: {enable_status}")
            
            # 等待一下
            time.sleep(20)
            
            # 测试禁用实时视频
            self.voice_manager.set_voice_enabled(False)
            self.voice_manager.set_live_video_enabled(False)
            self.logger.info("实时视频使能已禁用")
            
            # 检查状态
            enable_status = self.voice_manager.get_enable_status()
            self.logger.info(f"禁用后状态: {enable_status}")
            
            self.logger.info("实时视频控制测试完成")
            return True
            
        except Exception as e:
            self.logger.error(f"实时视频控制测试失败: {e}")
            return False
        
    def test_combined(self):
        """测试综合功能"""
        self.logger.info("=== 测试综合功能 ===")
        try:
            # self.voice_manager.add_task_to_queue('vqa', data={'img': 'jpeg-bridge.jpg', 'prompt': '请描述下这张图片？'})
            self.voice_manager.add_task_to_queue('transcript', text='转录测试任务1')
            self.voice_manager.add_task_to_queue('transcript', text='转录测试任务2')
            self.voice_manager.add_task_to_queue('text', text='继续对话测试')
            # self.voice_manager.set_voice_enabled(True)
            # self.voice_manager.set_live_video_enabled(True)
            # self.voice_manager.add_task_to_queue('text', text='你好，这是一个测试')
            # self.voice_manager.add_task_to_queue('transcript', text='转录测试任务3')
            # self.voice_manager.add_task_to_queue('transcript', text='转录测试任务4')
            # self.voice_manager.add_task_to_queue('text', text='继续对话测试')

            self.logger.info("实时视频使能已启用")
            return True
        except Exception as e:
            self.logger.error(f"综合功能测试失败: {e}")
            return False
    
    def test_worker_thread(self):
        """测试工作线程功能"""
        self.logger.info("=== 测试工作线程功能 ===")
        
        try:
            # 检查工作线程状态
            status = self.voice_manager.get_conversation_status()
            worker_running = status.get('worker_thread_running', False)
            self.logger.info(f"工作线程运行状态: {worker_running}")
            self.voice_manager.add_task_to_queue('transcript', text='转录测试任务1')
            self.voice_manager.add_task_to_queue('transcript', text='转录测试任务2')
            time.sleep(5)
            # 测试停止工作线程
            self.voice_manager.stop_worker_thread()
            self.logger.info("工作线程已停止")
            self.voice_manager.add_task_to_queue('transcript', text='转录测试任务3')
            self.voice_manager.add_task_to_queue('transcript', text='转录测试任务4')
            
            
            # 等待一下
            time.sleep(1)
            
            # 测试重新启动工作线程
            success = self.voice_manager.start_worker_thread()
            self.voice_manager.add_task_to_queue('transcript', text='转录测试任务5')

            time.sleep(5)
            if success:
                self.logger.info("工作线程重新启动成功")
            else:
                self.logger.error("工作线程重新启动失败")
            
            self.logger.info("工作线程功能测试完成")
            return True
            
        except Exception as e:
            self.logger.error(f"工作线程功能测试失败: {e}")
            return False
    
    def test_cleanup(self):
        """测试资源清理"""
        self.logger.info("=== 测试资源清理 ===")
        
        try:
            # 执行清理
            self.voice_manager.cleanup()
            self.logger.info("资源清理完成")
            
            self.logger.info("资源清理测试完成")
            return True
            
        except Exception as e:
            self.logger.error(f"资源清理测试失败: {e}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        self.logger.info("开始运行VoiceManager测试...")
        
        tests = [
            # ("基本功能", self.test_basic_functionality),
            # ("文本对话功能", self.test_text_conversation),

            # ("消息队列功能", self.test_message_queue),
            # ("转录队列功能", self.test_transcript_queue),
            # ("VQA功能", self.test_vqa_functionality),
            # ("语音使能控制", self.test_voice_enabled_control),
            # ("实时视频控制", self.test_live_video_control),
            ("综合测试", self.test_combined),
            # ("工作线程功能", self.test_worker_thread),
            # ("资源清理", self.test_cleanup),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                self.logger.info(f"\n{'='*50}")
                self.logger.info(f"开始测试: {test_name}")
                success = test_func()
                results.append((test_name, success))
                self.logger.info(f"测试结果: {test_name} - {'通过' if success else '失败'}")
                time.sleep(10)
            except Exception as e:
                self.logger.error(f"测试异常: {test_name} - {e}")
                results.append((test_name, False))
        
        # 输出测试总结
        self.logger.info(f"\n{'='*50}")
        self.logger.info("测试总结:")
        passed = sum(1 for _, success in results if success)
        total = len(results)
        
        for test_name, success in results:
            status = "✓ 通过" if success else "✗ 失败"
            self.logger.info(f"  {test_name}: {status}")
        
        self.logger.info(f"\n总计: {passed}/{total} 个测试通过")
        
        if passed == total:
            self.logger.info("🎉 所有测试通过！VoiceManager工作正常。")
        else:
            self.logger.warning(f"⚠️  有 {total - passed} 个测试失败，请检查代码。")
        
        return passed == total

def main():
    """主函数"""
    print("VoiceManager 测试脚本")
    print("=" * 50)
    log_manager = LogManager()
    config_manager = ConfigManager(log_manager=log_manager)
    
    # 创建测试器
    tester = VoiceManagerTester(log_manager=log_manager, config_manager=config_manager)
    
    try:
        # 设置测试环境
        if not tester.setup():
            print("❌ 测试环境设置失败，退出测试")
            return False
        
        # 运行所有测试
        success = tester.run_all_tests()
        while True:
            time.sleep(1)
        
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        return False
    except Exception as e:
        print(f"❌ 测试过程中发生异常: {e}")
        return False
    finally:
        print("\n测试完成")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
