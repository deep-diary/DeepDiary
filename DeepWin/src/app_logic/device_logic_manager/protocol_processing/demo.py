#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
协议处理示例代码
展示如何使用协议管理器处理不同设备的协议
"""

import os
import sys
import time
import logging
import argparse
from threading import Event

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '../../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from app_logic.device_logic_manager.protocol_processing.protocol_manager import ProtocolManager
from app_logic.device_logic_manager.protocol_processing.devices import DeepArmProtocol, TemplateProtocol
from app_logic.device_logic_manager.serial_comm import SerialManager
from app_logic.device_logic_manager.protocol_processing.devices.deep_arm.motor import Motor

class DeepArmDemo:
    """Deep Arm 机械臂演示类"""
    
    def __init__(self, config_file=None):
        """初始化演示程序"""
        # 初始化日志
        self._setup_logging()
        
        # 初始化协议
        self.protocol = DeepArmProtocol(config_file)
        
        # 创建串口管理器
        self.serial_manager = SerialManager(callback=self.data_callback)
        
        # 响应事件
        self.response_received = Event()
        self.last_response = None
        
        # 电机对象
        self.motors = {}
        
        # 初始化电机
        self.initialize_motors([1,2,3,4,5,6])
        
        # 活动电机ID
        self.active_motor_id = 1
        
        self.logger.info("Deep Arm demo program initialized")
    
    def _setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        )
        self.logger = logging.getLogger('DeepArmDemo')
    
    def set_active_motor_id(self, motor_id):
        """设置活动电机ID"""
        self.active_motor_id = motor_id
        self.logger.info(f"Current active motor ID has been set to: {motor_id}")
    
    def data_callback(self, data, source):
        """数据接收回调函数"""
        if source == 'data' and isinstance(data, bytearray):
            try:
                # 解析数据帧
                parsed = self.protocol.format_frame(data)
                motor_id = parsed['motor_id']
                
                # 自动创建电机对象
                if motor_id not in self.motors:
                    self.logger.info(f"Automatically creating motor {motor_id} object")
                    self.motors[motor_id] = Motor(motor_id)
                
                # 更新电机状态
                self.motors[motor_id].update_from_feedback(parsed['payload'])
                self._log_motor_status(motor_id)
                
            except Exception as e:
                self.logger.error(f"Frame parsing failed: {e}")
    
    def _log_motor_status(self, motor_id):
        """记录电机状态"""
        try:
            motor_state = self.motors[motor_id].get_status()
            if motor_state:
                motor_state_str = '\n'.join([f"{key}: {value}" for key, value in motor_state.items()])
                self.logger.info(f"Motor {motor_id} status: {motor_state_str}")
            else:
                self.logger.warning(f"Motor {motor_id} status is empty")
        except Exception as e:
            self.logger.error(f"Failed to get motor {motor_id} status: {e}")
    
    def get_status(self, motor_ids=None):
        """获取电机状态"""
        if motor_ids is None:
            motor_ids = [self.active_motor_id]
            
        self.logger.info(f"get_status: Motor IDs: {motor_ids}")
        
        status = {
            'ids': [],
            'positions': [],
            'velocities': [],
            'effort': [],
            'temperature': []
        }
        
        for motor_id in motor_ids:
            motor_state = self.motors[motor_id].get_status()
            status['ids'].append(motor_id)
            status['positions'].append(motor_state['current_position'])
            status['velocities'].append(motor_state['current_velocity'])
            status['effort'].append(motor_state['current_torque'])
            status['temperature'].append(motor_state['current_temperature'])
        
        self._log_status(status)
        return status
    
    def _log_status(self, status):
        """记录状态信息"""
        self.logger.info("All motors status:")
        for key, value in status.items():
            self.logger.info(f"{key}: {value}")
    
    def send_frame(self, frame):
        """发送通信帧"""
        if not self.serial_manager or not self.serial_manager.is_connected():
            self.logger.error("Not connected to the serial port")
            return False
        
        try:
            hex_frame = ' '.join([f'{b:02X}' for b in frame])
            self.logger.info(f"Sending data: {hex_frame}")
            self.serial_manager.write(frame)
            return True
        except Exception as e:
            self.logger.error(f"Sending failed: {e}")
            return False
    
    def send_command(self, command_type, **parameters):
        """发送命令"""
        try:
            if 'motor_id' not in parameters:
                parameters['motor_id'] = self.active_motor_id
            
            command = self.protocol.create_command(command_type, **parameters)
            self.logger.info(f'Command: {command}')
            
            frame = self.protocol.encode_command(command)
            self.logger.info(f'Frame: {frame}')
            
            hex_frame = ' '.join([f'{b:02X}' for b in frame])
            self.logger.info(f"Encoded command ({command_type}): {hex_frame}")
            
            return self.send_frame(frame)
            
        except Exception as e:
            self.logger.error(f"Failed to send command: {e}")
            return False
    
    def send_frames(self, frames, delay=0.02):
        """发送多个通信帧"""
        success = True
        for frame in frames:
            if not self.send_frame(frame):
                success = False
            time.sleep(delay)
        return success
    
    def initialize_motors(self, motor_ids=None):
        """初始化电机"""
        if motor_ids is None:
            motor_ids = [self.active_motor_id]
        
        for motor_id in motor_ids:
            if motor_id not in self.motors:
                self.motors[motor_id] = Motor(motor_id)
        
        init_frames = self.protocol.create_motor_init_frame_all(motor_ids)
        success = self.send_frames(init_frames)
        
        if success:
            self.logger.info(f"Motors initialized: {motor_ids}")
            for motor_id in motor_ids:
                self.motors[motor_id].is_enabled = True
        else:
            self.logger.error("Motor initialization failed")
        
        return success
    
    def reset_motors(self, motor_ids=None):
        """重置电机"""
        if motor_ids is None:
            motor_ids = [self.active_motor_id]
        
        reset_frames = self.protocol.create_motor_reset_frame_all(motor_ids)
        success = self.send_frames(reset_frames)
        
        if success:
            self.logger.info(f"Motors reset: {motor_ids}")
            for motor_id in motor_ids:
                if motor_id in self.motors:
                    self.motors[motor_id].is_enabled = False
        else:
            self.logger.error("Motor reset failed")
        
        return success


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Deep Arm robotic arm control demo')
    parser.add_argument('-p', '--port', help='Serial port device name')
    parser.add_argument('-l', '--list', action='store_true', help='List available serial ports')
    parser.add_argument('-c', '--config', help='Configuration file path')
    parser.add_argument('-m', '--motor', type=int, default=1, help='Active motor ID')
    parser.add_argument('-t', '--test', action='store_true', help='Run protocol test')
    args = parser.parse_args()
    
    if args.list:
        args.port = 'list'
    
    demo = DeepArmDemo(args.config)
    
    if args.motor:
        demo.set_active_motor_id(args.motor)
    
    if args.test:
        if demo.serial_manager.connect(args.port):
            demo.run_protocol_test()
            demo.serial_manager.disconnect()
    else:
        demo.run_demo(args.port)

if __name__ == "__main__":
    main()
