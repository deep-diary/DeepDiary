#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多帧命令演示脚本
演示如何使用新的多帧命令功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QCoreApplication, QTimer
from deepwin.data_management.log_manager import LogManager
from deepwin.services.hardware_communication.device_protocols.deep_motor_protocol.protocol2can import Protocol2Can
from deepwin.services.hardware_communication.device_protocols.deep_motor_protocol.protocol2serial import Protocol2Serial
from deepwin.services.hardware_communication.device_protocols.deep_motor_protocol.deep_motor_parser import DeepMotorProtocolParser
from deepwin.config.config_manager import ConfigManager
class MultiFrameDemo:
    """多帧命令演示类"""
    
    def __init__(self):
        """初始化演示"""
        # 初始化日志管理器
        self.log_manager = LogManager()
        self.logger = self.log_manager.get_logger(__name__)

        self.config_manager = ConfigManager(log_manager=self.log_manager)
        
        # 初始化协议解析器
        self.protocol2can = Protocol2Can(log_manager=self.log_manager)
        self.protocol2serial = Protocol2Serial(log_manager=self.log_manager)
        self.deep_motor_parser = DeepMotorProtocolParser(log_manager=self.log_manager, config_manager=self.config_manager)
        
        self.logger.info("多帧命令演示初始化完成")
    
    def demo_single_frame_commands(self):
        """演示单帧命令"""
        self.logger.info("=" * 50)
        self.logger.info("演示单帧命令")
        self.logger.info("=" * 50)
        
        # 测试单帧命令
        single_frame_commands = [
            ("motor_set_speed", {"motor_id": 1, "speed": 1000}),
            ("motor_set_pos", {"motor_id": 1, "position": 1.5}),
            ("motor_set_torque", {"motor_id": 1, "torque": 2.0}),
            ("motor_enable", {"motor_id": 1}),
            ("motor_disable", {"motor_id": 1}),
            ("motor_zero", {"motor_id": 1}),
        ]
        
        for command_name, params in single_frame_commands:
            self.logger.info(f"\n测试单帧命令: {command_name}")
            self.logger.info(f"参数: {params}")
            
            # 测试CAN帧转换
            can_frame = self.deep_motor_parser.convert_command_to_can_frame(command_name, params)
            if can_frame:
                self.logger.info(f"CAN帧转换成功: ID=0x{can_frame['arbitration_id']:X}, Data={can_frame['data'].hex()}")
            else:
                self.logger.error(f"CAN帧转换失败")
            
            # 测试串口帧转换
            serial_frame = self.deep_motor_parser.convert_command_to_serial_frame(command_name, params)
            if serial_frame:
                self.logger.info(f"串口帧转换成功: {serial_frame.hex()}")
            else:
                self.logger.error(f"串口帧转换失败")
    
    def demo_multi_frame_commands(self):
        """演示多帧命令"""
        self.logger.info("=" * 50)
        self.logger.info("演示多帧命令")
        self.logger.info("=" * 50)
        
        # 测试多帧命令
        multi_frame_commands = [
            ("motor_init", {"motor_id": 1}),
            ("motor_init_all", {"motor_ids": [1, 2, 3]}),
        ]
        
        for command_name, params in multi_frame_commands:
            self.logger.info(f"\n测试多帧命令: {command_name}")
            self.logger.info(f"参数: {params}")
            
            # 测试CAN帧转换
            can_frames = self.deep_motor_parser.convert_command_to_can_frame(command_name, params)
            if can_frames:
                if isinstance(can_frames, list):
                    self.logger.info(f"多帧CAN转换成功: 共 {len(can_frames)} 帧")
                    for i, frame in enumerate(can_frames):
                        self.logger.info(f"  第 {i+1} 帧: ID=0x{frame['arbitration_id']:X}, Data={frame['data'].hex()}")
                else:
                    self.logger.info(f"单帧CAN转换成功: ID=0x{can_frames['arbitration_id']:X}, Data={can_frames['data'].hex()}")
            else:
                self.logger.error(f"CAN帧转换失败")
            
            # 测试串口帧转换
            serial_frames = self.deep_motor_parser.convert_command_to_serial_frame(command_name, params)
            if serial_frames:
                if isinstance(serial_frames, list):
                    self.logger.info(f"多帧串口转换成功: 共 {len(serial_frames)} 帧")
                    for i, frame in enumerate(serial_frames):
                        self.logger.info(f"  第 {i+1} 帧: {frame.hex()}")
                else:
                    self.logger.info(f"单帧串口转换成功: {serial_frames.hex()}")
            else:
                self.logger.error(f"串口帧转换失败")
    
    def demo_direct_protocol_calls(self):
        """演示直接调用协议方法"""
        self.logger.info("=" * 50)
        self.logger.info("演示直接调用协议方法")
        self.logger.info("=" * 50)
        
        # 直接调用Protocol2Can的方法
        self.logger.info("\n直接调用Protocol2Can方法:")
        
        # 单帧命令
        single_can_frame = self.protocol2can.create_motor_enable_frame(1)
        self.logger.info(f"单帧CAN: ID=0x{single_can_frame['arbitration_id']:X}, Data={single_can_frame['data'].hex()}")
        
        # 多帧命令
        multi_can_frames = self.protocol2can.create_motor_init_frame(1)
        self.logger.info(f"多帧CAN: 共 {len(multi_can_frames)} 帧")
        for i, frame in enumerate(multi_can_frames):
            self.logger.info(f"  第 {i+1} 帧: ID=0x{frame['arbitration_id']:X}, Data={frame['data'].hex()}")
        
        # 多电机初始化
        all_can_frames = self.protocol2can.create_motor_init_frame_all([1, 2])
        self.logger.info(f"多电机CAN: 共 {len(all_can_frames)} 帧")
        for i, frame in enumerate(all_can_frames):
            self.logger.info(f"  第 {i+1} 帧: ID=0x{frame['arbitration_id']:X}, Data={frame['data'].hex()}")
        
        # 直接调用Protocol2Serial的方法
        self.logger.info("\n直接调用Protocol2Serial方法:")
        
        # 单帧命令
        single_serial_frame = self.protocol2serial.create_motor_enable_frame(1)
        self.logger.info(f"单帧串口: {single_serial_frame.hex()}")
        
        # 多帧命令
        multi_serial_frames = self.protocol2serial.create_motor_init_frame(1)
        self.logger.info(f"多帧串口: 共 {len(multi_serial_frames)} 帧")
        for i, frame in enumerate(multi_serial_frames):
            self.logger.info(f"  第 {i+1} 帧: {frame.hex()}")
        
        # 多电机初始化
        all_serial_frames = self.protocol2serial.create_motor_init_frame_all([1, 2])
        self.logger.info(f"多电机串口: 共 {len(all_serial_frames)} 帧")
        for i, frame in enumerate(all_serial_frames):
            self.logger.info(f"  第 {i+1} 帧: {frame.hex()}")
    
    def run_demo(self):
        """运行完整演示"""
        self.logger.info("开始多帧命令演示")
        
        try:
            # 演示单帧命令
            self.demo_single_frame_commands()
            
            # 演示多帧命令
            self.demo_multi_frame_commands()
            
            # 演示直接协议调用
            self.demo_direct_protocol_calls()
            
            self.logger.info("=" * 50)
            self.logger.info("多帧命令演示完成")
            self.logger.info("=" * 50)
            
        except Exception as e:
            self.logger.error(f"演示过程中发生错误: {e}")
            import traceback
            self.logger.error(traceback.format_exc())

def main():
    """主函数"""
    # 创建Qt应用程序
    app = QCoreApplication(sys.argv)
    
    # 创建演示实例
    demo = MultiFrameDemo()
    
    # 运行演示
    demo.run_demo()
    
    # 退出应用程序
    app.quit()

if __name__ == "__main__":
    main()
