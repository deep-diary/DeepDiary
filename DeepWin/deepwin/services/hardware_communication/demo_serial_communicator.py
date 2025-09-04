#!/usr/bin/env python3
"""
SerialCommunicator 优化功能演示脚本

演示新增的帧列表管理功能：
1. 发送和接收帧的列表管理
2. 先进先出机制
3. 清空列表功能
4. 信号发送机制
"""

import sys
import os
import time
from PySide6.QtCore import QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager
from deepwin.services.hardware_communication.serial_communicator import SerialCommunicator


class SerialCommunicatorDemo:
    """SerialCommunicator 演示类"""
    
    def __init__(self):
        """初始化演示"""
        self.app = QCoreApplication(sys.argv)
        
        # 初始化日志和配置管理器
        self.log_manager = LogManager()
        self.config_manager = ConfigManager()
        
        # 创建 SerialCommunicator 实例
        self.serial_comm = SerialCommunicator(
            log_manager=self.log_manager,
            config_manager=self.config_manager
        )
        
        # 连接信号
        self.serial_comm.frame_lists_updated.connect(self.on_frame_lists_updated)
        self.serial_comm.raw_frame_send.connect(self.on_frame_sent)
        self.serial_comm.raw_frame_received.connect(self.on_frame_received)
        
        # 设置定时器用于演示
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.run_demo)
        self.demo_timer.setSingleShot(True)
        
        print("SerialCommunicator 优化功能演示")
        print("=" * 50)
        
    def on_frame_lists_updated(self):
        """帧列表更新回调"""
        info = self.serial_comm.get_frame_lists_info()
        print(f"帧列表更新 - 发送: {info['sent_frames_count']}, 接收: {info['received_frames_count']}")
        
    def on_frame_sent(self, port_name: str, data: bytes):
        """帧发送回调"""
        print(f"发送帧: {port_name} -> {data.hex()}")
        
    def on_frame_received(self, port_name: str, data: bytes):
        """帧接收回调"""
        print(f"接收帧: {port_name} <- {data.hex()}")
        
    def run_demo(self):
        """运行演示"""
        print("\n1. 演示发送帧记录功能")
        # 模拟发送一些数据
        test_data = [
            b'\x01\x02\x03\x04',
            b'\x05\x06\x07\x08',
            b'\x09\x0A\x0B\x0C'
        ]
        
        for i, data in enumerate(test_data):
            print(f"发送测试数据 {i+1}: {data.hex()}")
            # 注意：这里只是演示记录功能，实际发送需要打开串口
            # 我们直接调用内部方法来演示记录功能
            frame_info = {
                'timestamp': time.time(),
                'port_name': 'COM1',
                'data': data,
                'data_hex': data.hex()
            }
            self.serial_comm._sent_frames.append(frame_info)
            self.serial_comm.frame_lists_updated.emit()
            time.sleep(0.1)
        
        print("\n2. 演示接收帧记录功能")
        # 模拟接收一些数据
        received_data = [
            b'\x10\x11\x12\x13',
            b'\x14\x15\x16\x17',
            b'\x18\x19\x1A\x1B'
        ]
        
        for i, data in enumerate(received_data):
            print(f"接收测试数据 {i+1}: {data.hex()}")
            frame_info = {
                'timestamp': time.time(),
                'port_name': 'COM1',
                'data': data,
                'data_hex': data.hex()
            }
            self.serial_comm._received_frames.append(frame_info)
            self.serial_comm.frame_lists_updated.emit()
            time.sleep(0.1)
        
        print("\n3. 显示当前帧列表信息")
        info = self.serial_comm.get_frame_lists_info()
        print(f"发送帧数量: {info['sent_frames_count']}")
        print(f"接收帧数量: {info['received_frames_count']}")
        print(f"最大列表长度: {info['max_list_size']}")
        
        print("\n4. 演示清空列表功能")
        self.serial_comm.clear_frame_lists()
        
        print("\n5. 演示设置最大列表长度")
        self.serial_comm.set_max_frame_list_size(5)
        
        # 添加更多数据来测试先进先出机制
        print("\n6. 测试先进先出机制（添加10个帧，最大长度为5）")
        for i in range(10):
            frame_info = {
                'timestamp': time.time(),
                'port_name': 'COM1',
                'data': bytes([i, i+1, i+2, i+3]),
                'data_hex': bytes([i, i+1, i+2, i+3]).hex()
            }
            self.serial_comm._sent_frames.append(frame_info)
            time.sleep(0.01)
        
        final_info = self.serial_comm.get_frame_lists_info()
        print(f"最终发送帧数量: {final_info['sent_frames_count']} (应该为5)")
        
        # 显示最后5个帧的数据
        print("最后5个帧的数据:")
        for i, frame in enumerate(final_info['sent_frames']):
            print(f"  {i+1}: {frame['data_hex']}")
        
        print("\n演示完成！")
        self.app.quit()
        
    def start_demo(self):
        """开始演示"""
        # 延迟1秒开始演示
        QTimer.singleShot(1000, self.run_demo)
        return self.app.exec()


def main():
    """主函数"""
    demo = SerialCommunicatorDemo()
    return demo.start_demo()


if __name__ == "__main__":
    sys.exit(main())
