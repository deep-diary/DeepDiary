#!/usr/bin/env python3
"""
重构后的串口转CAN架构演示脚本

展示新的架构设计：
1. SerialCommunicator: 专注于串口通信和帧列表管理
2. CanBusCommunicator: 专注于串口转CAN逻辑和CAN帧列表管理
3. 清晰的信号传递机制
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
from deepwin.services.hardware_communication.can_bus_communicator import CanBusCommunicator


class RefactoredArchitectureDemo:
    """重构后架构演示类"""
    
    def __init__(self):
        """初始化演示"""
        self.app = QCoreApplication(sys.argv)
        
        # 初始化日志和配置管理器
        self.log_manager = LogManager()
        self.config_manager = ConfigManager()
        
        # 创建通信模块实例
        self.serial_comm = SerialCommunicator(
            log_manager=self.log_manager,
            config_manager=self.config_manager
        )
        
        self.can_comm = CanBusCommunicator(
            log_manager=self.log_manager,
            config_manager=self.config_manager
        )
        
        # 连接信号 - 串口到CAN
        self.serial_comm.raw_frame_received.connect(self.on_serial_data_received)
        
        # 连接信号 - CAN到串口
        self.can_comm.serial_data_to_send.connect(self.on_serial_data_to_send)
        
        # 连接帧列表更新信号
        self.serial_comm.frame_lists_updated.connect(self.on_serial_frame_lists_updated)
        self.can_comm.can_frame_lists_updated.connect(self.on_can_frame_lists_updated)
        
        # 连接CAN帧信号
        self.can_comm.can_frame_received.connect(self.on_can_frame_received)
        self.can_comm.can_frame_sent.connect(self.on_can_frame_sent)
        
        # 设置定时器用于演示
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.run_demo)
        self.demo_timer.setSingleShot(True)
        
        print("重构后的串口转CAN架构演示")
        print("=" * 50)
        
    def on_serial_frame_lists_updated(self):
        """串口帧列表更新回调"""
        info = self.serial_comm.get_frame_lists_info()
        print(f"串口帧列表更新 - 发送: {info['sent_frames_count']}, 接收: {info['received_frames_count']}")
        
    def on_can_frame_lists_updated(self):
        """CAN帧列表更新回调"""
        info = self.can_comm.get_can_frame_lists_info()
        print(f"CAN帧列表更新 - 发送: {info['sent_can_frames_count']}, 接收: {info['received_can_frames_count']}")
        
    def on_serial_data_received(self, port_name: str, data: bytes):
        """串口数据接收回调"""
        print(f"串口数据接收 - 端口: {port_name}, 数据: {data.hex()}")
        # 转发给CAN通信器处理
        self.can_comm.process_serial_data(data)
        
    def on_serial_data_to_send(self, data: bytes):
        """需要发送串口数据的回调"""
        print(f"需要发送串口数据: {data.hex()}")
        # 这里可以转发给具体的串口发送
        
    def on_can_frame_received(self, arbitration_id: int, data: bytes, is_extended_id: bool):
        """CAN帧接收回调"""
        print(f"CAN帧接收 - ID: 0x{arbitration_id:X}, 数据: {data.hex()}, 扩展ID: {is_extended_id}")
        
    def on_can_frame_sent(self, arbitration_id: int, data: bytes, is_extended_id: bool):
        """CAN帧发送回调"""
        print(f"CAN帧发送 - ID: 0x{arbitration_id:X}, 数据: {data.hex()}, 扩展ID: {is_extended_id}")
        
    def run_demo(self):
        """运行演示"""
        print("\n1. 演示串口数据转CAN帧")
        # 模拟串口接收数据（去掉AT头和\r\n尾的格式）
        test_serial_data = [
            b'\x14\x00\x37\xEC\x08\x80\xFF\x82\x0F\x81\x51\x01\x36',  # 完整的CAN帧数据
            b'\x14\x00\x37\xED\x04\x11\x22\x33\x44',  # 另一个CAN帧
        ]
        
        for i, data in enumerate(test_serial_data):
            print(f"处理串口数据 {i+1}: {data.hex()}")
            # 直接调用CAN通信器的处理方法
            self.can_comm.process_serial_data(data)
            time.sleep(0.1)
        
        print("\n2. 演示CAN帧转串口数据")
        # 发送CAN帧
        test_can_frames = [
            (0x140037EC, b'\x80\xFF\x82\x0F\x81\x51\x01\x36'),
            (0x140037ED, b'\x11\x22\x33\x44'),
        ]
        
        for i, (can_id, data) in enumerate(test_can_frames):
            print(f"发送CAN帧 {i+1}: ID=0x{can_id:X}, Data={data.hex()}")
            self.can_comm.send_can_frame(can_id, data)
            time.sleep(0.1)
        
        print("\n3. 显示帧列表统计信息")
        serial_info = self.serial_comm.get_frame_lists_info()
        can_info = self.can_comm.get_can_frame_lists_info()
        
        print(f"串口帧统计:")
        print(f"  发送帧: {serial_info['sent_frames_count']}")
        print(f"  接收帧: {serial_info['received_frames_count']}")
        
        print(f"CAN帧统计:")
        print(f"  发送帧: {can_info['sent_can_frames_count']}")
        print(f"  接收帧: {can_info['received_can_frames_count']}")
        
        print("\n4. 演示清空列表功能")
        self.serial_comm.clear_frame_lists()
        self.can_comm.clear_can_frame_lists()
        
        print("\n5. 演示设置最大列表长度")
        self.serial_comm.set_max_frame_list_size(5)
        self.can_comm.set_max_can_frame_list_size(5)
        
        print("\n6. 测试先进先出机制")
        print("添加10个CAN帧，最大长度为5...")
        for i in range(10):
            can_id = 0x14000000 + i
            data = bytes([i, i+1, i+2, i+3])
            self.can_comm.send_can_frame(can_id, data)
            time.sleep(0.01)
        
        final_can_info = self.can_comm.get_can_frame_lists_info()
        print(f"最终CAN发送帧数量: {final_can_info['sent_can_frames_count']} (应该为5)")
        
        # 显示最后5个帧的数据
        print("最后5个CAN帧的数据:")
        for i, frame in enumerate(final_can_info['sent_can_frames']):
            print(f"  {i+1}: ID=0x{frame['arbitration_id']:X}, Data={frame['data_hex']}")
        
        print("\n演示完成！")
        print("\n简化后的架构优势:")
        print("1. 职责分离: SerialCommunicator专注串口，CanBusCommunicator专注CAN转换")
        print("2. 抽象化: CAN层不处理硬件相关的端口映射和DBC管理")
        print("3. 信号驱动: 通过Qt信号实现模块间通信")
        print("4. 帧列表管理: 每个模块独立管理自己的帧列表")
        print("5. 易于扩展: 可以轻松添加新的通信协议")
        print("6. 高层处理: DBC解析和端口映射在更高层处理")
        
        self.app.quit()
        
    def start_demo(self):
        """开始演示"""
        # 延迟1秒开始演示
        QTimer.singleShot(1000, self.run_demo)
        return self.app.exec()


def main():
    """主函数"""
    demo = RefactoredArchitectureDemo()
    return demo.start_demo()


if __name__ == "__main__":
    sys.exit(main())
