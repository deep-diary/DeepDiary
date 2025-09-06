# src/services/hardware_communication/device_protocols/deep_motor_protocol/deep_motor_parser.py
# DeepMotor 协议的具体实现 (现在作为协议适配器)

import struct
import time
import logging
from typing import Dict, Any, List, Union, Optional
from PySide6.QtCore import QObject, Signal

from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager
from deepwin.services.hardware_communication.device_protocols.base_protocol_parser import BaseProtocolParser

# 从重构的协议文件导入
from .protocol2can import Protocol2Can
from .protocol2serial import Protocol2Serial
from .deep_motor_mapping import DeepMotorMapping

class DeepMotorProtocolParser(BaseProtocolParser):
    """
    DeepMotor 无刷电机的特定协议解析器 (适配器)。
    负责将 DeepMotor 的底层数据转换为业务语义数据，并将抽象命令转换为 DeepMotor 的底层协议命令。
    此模块现在作为 DeepMotorProtocol (低级协议实现) 和上层应用逻辑之间的适配器。
    """
    
    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, parent: Optional[QObject] = None):
        super().__init__(log_manager, config_manager, parent)
        # 实例化重构后的协议实现
        self.protocol2can = Protocol2Can(log_manager=log_manager)
        self.protocol2serial = Protocol2Serial(log_manager=log_manager)
        self.deep_motor_mapping = DeepMotorMapping(log_manager=log_manager, config_manager=config_manager)

    def parse_input_data(self, device_id: str, low_level_data: bytes) -> Dict[str, Any]:
        """
        将 DeepMotor 的低层次数据（原始字节串）转换为业务语义数据。
        :param device_id: DeepMotor 设备的唯一标识符。
        :param low_level_data: 原始字节串。
        :return: 转换后的业务语义数据字典。
        """
        semantic_data: Dict[str, Any] = {"device_id": device_id, "device_type": "DeepMotor"}
        
        try:
            # 调用 Protocol2Serial 进行底层数据解码
            response = self.protocol2serial.decode_response(low_level_data)
            
            if response.get('success', False):
                semantic_data["success"] = True
                # 直接将解码后的数据字段合并到语义数据中
                for proto_key, semantic_key in self.deep_motor_mapping.data_mapping.items():
                    if proto_key in response:
                        semantic_data[semantic_key] = response[proto_key]
            
            else:
                semantic_data["success"] = False
                semantic_data["error_message"] = response.get('error', '未知错误')
                self.protocol_conversion_error.emit(device_id, response.get('error', '未知错误'))

        except Exception as e:
            error_msg = f"DeepMotorProtocolParser: 解析原始数据失败: {e}"
            self.logger.error(error_msg)
            self.protocol_conversion_error.emit(device_id, error_msg)
            semantic_data["success"] = False
            semantic_data["error_message"] = error_msg
        
        return semantic_data

    def generate_output_command(self, command_name: str, params: Dict[str, Any]) -> Union[bytes, List[bytes]]:
        """
        生成 DeepMotor 的底层命令（使用参数字典）。
        这是推荐的接口，避免了参数解析逻辑，直接使用应用层传递的参数字典。
        :param command_name: 抽象命令名称。
        :param params: 命令参数字典，键为参数名，值为参数值。
        :return: 编码后的命令字节串或字节串列表（多帧命令）。
        """
        try:
            self.logger.debug(f"DeepMotorProtocolParser: 生成 DeepMotor 命令 '{command_name}' 参数: {params}")
            
            command = self.deep_motor_mapping.map_and_call(command_name, params)
            return command
        except Exception as e:
            raise ValueError(f"生成 DeepMotor 命令 '{command_name}' 失败: {e}")

    # ==================== 协议管理层的4个核心任务实现 ====================
    
    def convert_command_to_can_frame(self, command_name: str, params: Dict[str, Any]) -> Union[Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]]]:
        """
        核心任务1：将DeepMotor命令转换为CAN帧格式
        支持单帧和多帧命令
        """
        try:
            self.logger.debug(f"DeepMotor: 转换命令 '{command_name}' 为CAN帧")
            
            # 直接调用协议方法生成CAN帧
            motor_id = params.get('motor_id', 1)
            
            if command_name == "motor_set_speed":
                speed = params.get('spd', 0)  # 修正参数名：从'speed'改为'spd'
                return self.protocol2can.create_motor_spd_frame(motor_id, speed)
            elif command_name == "motor_set_pos":
                position = params.get('position', 0)
                return self.protocol2can.create_motor_pos_frame(motor_id, position)
            elif command_name == "motor_set_torque":
                torque = params.get('torque', 0)
                return self.protocol2can.create_motor_torque_frame(motor_id, torque)
            elif command_name == "motor_enable":
                return self.protocol2can.create_motor_enable_frame(motor_id)
            elif command_name == "motor_disable":
                return self.protocol2can.create_motor_reset_frame(motor_id)
            elif command_name == "motor_zero":
                return self.protocol2can.create_motor_zero_frame(motor_id)
            elif command_name == "motor_init":
                # 初始化需要多个帧，返回多帧列表
                return self.protocol2can.create_motor_init_frame(motor_id)
            elif command_name == "motor_init_all":
                # 多电机初始化
                motor_ids = params.get('motor_ids', [motor_id])
                return self.protocol2can.create_motor_init_frame_all(motor_ids)
            elif command_name == "motor_jog":
                spd = params.get('spd', 0)
                return self.protocol2can.create_motor_jog_frame(motor_id, spd)
            elif command_name == "motor_jog_stop":
                return self.protocol2can.create_motor_jog_stop_frame(motor_id)
            else:
                self.logger.warning(f"DeepMotor: 未知命令 '{command_name}'")
                return None
        except Exception as e:
            self.logger.warning(f"DeepMotor: 命令 '{command_name}' 不支持CAN帧转换: {e}")
        
        return None
    
    def convert_command_to_serial_frame(self, command_name: str, params: Dict[str, Any]) -> Optional[bytes]:
        """
        核心任务2：将DeepMotor命令直接转换为串口帧（跳过CAN层）
        """
        try:
            self.logger.debug(f"DeepMotor: 转换命令 '{command_name}' 为串口帧")
            
            # 调用映射器生成命令
            command_data = self.deep_motor_mapping.map_and_call(command_name, params)
            
            if isinstance(command_data, (bytes, bytearray)):
                # 直接返回生成的串口帧（已经包含AT和\r\n）
                return bytes(command_data)
        except Exception as e:
            self.logger.warning(f"DeepMotor: 命令 '{command_name}' 不支持串口帧转换: {e}")
        
        return None
    
    def parse_can_frame_to_signals(self, can_frame_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        核心任务3：将CAN帧解析为DeepMotor信号字典
        """
        try:
            arbitration_id = can_frame_data.get('arbitration_id')
            data = can_frame_data.get('data')
            
            if arbitration_id is None or data is None:
                self.logger.warning(f"DeepMotor: CAN帧数据不完整: {can_frame_data}")
                return None
            
            self.logger.debug(f"DeepMotor: 解析CAN帧 ID=0x{arbitration_id:X}")
            
            # 调用Protocol2Can的CAN帧解码方法
            response = self.protocol2can.decode_can_response(arbitration_id, data)
            
            if response.get('success', False):
                semantic_data = {"success": True}
                # 直接将解码后的数据字段合并到语义数据中
                for proto_key, semantic_key in self.deep_motor_mapping.data_mapping.items():
                    if proto_key in response:
                        semantic_data[semantic_key] = response[proto_key]
                
                # 如果没有映射关系，直接使用原始数据
                if not semantic_data or len(semantic_data) == 1:  # 只有success字段
                    semantic_data.update(response)
                
                return semantic_data
            else:
                self.logger.warning(f"DeepMotor: CAN帧解析失败: {response.get('error', '未知错误')}")
                
        except Exception as e:
            self.logger.warning(f"DeepMotor: CAN帧解析异常: {e}")
        
        return None
    
    def parse_serial_frame_to_signals(self, serial_frame_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        核心任务4：将串口帧解析为DeepMotor信号字典
        """
        try:
            data = serial_frame_data.get('data')
            
            self.logger.debug(f"DeepMotor: 解析串口帧 {data.hex()}")
            
            # 调用Protocol2Serial进行解码
            response = self.protocol2serial.decode_response(data)
            
            if response.get('success', False):
                semantic_data = {"success": True}
                # 直接将解码后的数据字段合并到语义数据中
                for proto_key, semantic_key in self.deep_motor_mapping.data_mapping.items():
                    if proto_key in response:
                        semantic_data[semantic_key] = response[proto_key]
                return semantic_data
            else:
                self.logger.warning(f"DeepMotor: 串口帧解析失败: {response.get('error', '未知错误')}")
                
        except Exception as e:
            self.logger.warning(f"DeepMotor: 串口帧解析异常: {e}")
        
        return None

    def cleanup(self):
        """
        清理 DeepMotorProtocolParser 资源。
        """
        self.logger.info("DeepMotorProtocolParser: 清理完成。")
        super().cleanup()

