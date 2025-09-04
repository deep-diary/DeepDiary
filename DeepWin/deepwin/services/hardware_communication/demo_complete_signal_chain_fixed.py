#!/usr/bin/env python3
"""
完整的信号传递链路演示脚本 - 修复版本

展示新的协议管理层架构：
1. 协议管理层的4个核心任务
2. 完整的信号传递链路
3. 支持CAN协议和串口协议的统一处理
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
from deepwin.services.hardware_communication.device_protocol_parser import DeviceProtocolParser


class CompleteSignalChainDemo:
    """完整信号传递链路演示类"""
    
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
        
        self.protocol_parser = DeviceProtocolParser(
            log_manager=self.log_manager,
            config_manager=self.config_manager
        )
        
        # 建立完整的信号传递链路
        self._setup_signal_chain()
        
        # 设置定时器用于演示
        self.demo_timer = QTimer()
        self.demo_timer.timeout.connect(self.run_demo)
        self.demo_timer.setSingleShot(True)
        
        # 用于存储测试结果的变量
        self.test_can_frame = None
        self.test_serial_frame = None
        
        print("完整信号传递链路演示")
        print("=" * 50)
        
    def _setup_signal_chain(self):
        """建立完整的信号传递链路"""
        
        # ==================== 接收链路（硬件 → 应用） ====================
        
        # 串口 → CAN通信器（需要包装信号以提取数据部分）
        self.serial_comm.raw_frame_received.connect(self._on_serial_to_can)
        
        # CAN通信器 → 协议管理层
        self.can_comm.can_frame_received.connect(self.on_can_frame_received)
        
        # 串口 → 协议管理层（直接路径）
        self.serial_comm.raw_frame_received.connect(self.on_serial_frame_received)
        
        # 协议管理层 → 上层应用
        self.protocol_parser.device_semantic_data_ready.connect(self.on_device_semantic_data)
        
        # ==================== 发送链路（应用 → 硬件） ====================
        
        # 协议管理层 → CAN通信器（需要包装信号）
        self.protocol_parser.can_frame_ready.connect(self._on_can_frame_to_send)
        
        # 协议管理层 → 串口通信器
        self.protocol_parser.serial_frame_ready.connect(self.on_serial_frame_to_send)
        
        # CAN通信器 → 串口通信器
        self.can_comm.serial_data_to_send.connect(self.on_can_to_serial_data)
        
        # ==================== 错误处理链路 ====================
        
        # 各层错误信号
        self.serial_comm.serial_error.connect(self.on_serial_error)
        self.can_comm.can_error.connect(self.on_can_error)
        self.protocol_parser.protocol_conversion_error.connect(self.on_protocol_error)
        
        # ==================== 帧列表更新链路 ====================
        
        # 帧列表更新信号
        self.serial_comm.frame_lists_updated.connect(self.on_serial_frame_lists_updated)
        self.can_comm.can_frame_lists_updated.connect(self.on_can_frame_lists_updated)
        
    def _on_serial_to_can(self, port_name: str, data: bytes):
        """串口到CAN的包装方法"""
        self.can_comm.process_serial_data(data)
        
    def _on_can_frame_to_send(self, arbitration_id: int, data: bytes, is_extended_id: bool):
        """CAN帧发送的包装方法"""
        # 存储测试结果
        self.test_can_frame = {
            'arbitration_id': arbitration_id,
            'data': data,
            'is_extended_id': is_extended_id
        }
        print(f"收到CAN帧: ID=0x{arbitration_id:X}, 数据={data.hex()}")
        
        # 发送到CAN通信器
        self.can_comm.send_can_frame(arbitration_id, data, is_extended_id)
        
    def on_can_frame_received(self, arbitration_id: int, data: bytes, is_extended_id: bool):
        """CAN帧接收回调"""
        print(f"CAN帧接收 - ID: 0x{arbitration_id:X}, 数据: {data.hex()}, 扩展ID: {is_extended_id}")
        
        # 转发给协议管理层解析（假设设备ID为DeepMotor1）
        device_id = "DeepMotor1"
        self.protocol_parser.parse_can_frame_to_signals(device_id, arbitration_id, data, is_extended_id)
        
    def on_serial_frame_received(self, port_name: str, data: bytes):
        """串口帧接收回调"""
        print(f"串口帧接收 - 端口: {port_name}, 数据: {data.hex()}")
        
        # 转发给协议管理层解析（假设设备ID为DeepMotor1）
        device_id = "DeepMotor1"
        self.protocol_parser.parse_serial_frame_to_signals(device_id, data)
        
    def on_device_semantic_data(self, device_id: str, semantic_data: dict):
        """设备语义数据回调"""
        print(f"设备语义数据 - 设备: {device_id}, 数据: {semantic_data}")
        
    def on_serial_frame_to_send(self, data: bytes):
        """需要发送串口帧的回调"""
        print(f"需要发送串口帧: {data.hex()}")
        # 这里可以转发给具体的串口发送
        # self.serial_comm.send_bytes(port_name, data)
        
    def on_can_to_serial_data(self, data: bytes):
        """CAN转串口数据回调"""
        # 存储测试结果
        self.test_serial_frame = data
        print(f"CAN转串口数据: {data.hex()}")
        # 这里可以转发给具体的串口发送
        # self.serial_comm.send_bytes(port_name, data)
        
    def on_serial_error(self, port_name: str, error_msg: str):
        """串口错误回调"""
        print(f"串口错误 - 端口: {port_name}, 错误: {error_msg}")
        
    def on_can_error(self, error_msg: str):
        """CAN错误回调"""
        print(f"CAN错误: {error_msg}")
        
    def on_protocol_error(self, device_id: str, error_msg: str):
        """协议错误回调"""
        print(f"协议错误 - 设备: {device_id}, 错误: {error_msg}")
        
    def on_serial_frame_lists_updated(self):
        """串口帧列表更新回调"""
        info = self.serial_comm.get_frame_lists_info()
        print(f"串口帧列表更新 - 发送: {info['sent_frames_count']}, 接收: {info['received_frames_count']}")
        
    def on_can_frame_lists_updated(self):
        """CAN帧列表更新回调"""
        info = self.can_comm.get_can_frame_lists_info()
        print(f"CAN帧列表更新 - 发送: {info['sent_can_frames_count']}, 接收: {info['received_can_frames_count']}")
        
    def run_demo(self):
        """运行演示"""
        print("\n1. 演示协议管理层的4个核心任务")
        
        # 任务1：命令 → CAN帧
        print("\n任务1：命令 → CAN帧")
        device_id = "DeepMotor1"
        command_name = "motor_set_speed"  # 使用正确的命令名
        params = {"speed": 1000, "motor_id": 1}  # 添加必需的motor_id参数
        
        print(f"发送命令: {command_name}, 参数: {params}")
        
        # 清空之前的测试结果
        self.test_can_frame = None
        self.test_serial_frame = None
        
        # 通过信号发送命令（这是正确的方式）
        self.protocol_parser.convert_command_to_can_frame(device_id, command_name, params)
        
        # 等待信号处理完成
        time.sleep(0.2)
        
        # 检查结果
        if self.test_can_frame:
            print(f"✅ CAN帧生成成功: ID=0x{self.test_can_frame['arbitration_id']:X}, 数据={self.test_can_frame['data'].hex()}")
        else:
            print("❌ CAN帧生成失败")
            
        if self.test_serial_frame:
            print(f"✅ 串口帧生成成功: {self.test_serial_frame.hex()}")
        else:
            print("❌ 串口帧生成失败")
        
        print("\n演示完成！")
        print("\n新架构优势:")
        print("1. 协议管理层统一处理4个核心任务")
        print("2. 完整的信号传递链路")
        print("3. 支持CAN协议和串口协议的统一处理")
        print("4. 新增设备只需在设备协议子层添加代码")
        print("5. 协议管理层代码尽可能不动")
        
        self.app.quit()
        
    def start_demo(self):
        """开始演示"""
        # 延迟1秒开始演示
        QTimer.singleShot(1000, self.run_demo)
        return self.app.exec()


def main():
    """主函数"""
    demo = CompleteSignalChainDemo()
    return demo.start_demo()


if __name__ == "__main__":
    sys.exit(main())
