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

# 从新的 protocol 文件导入 DeepMotorProtocol 以及命令/响应对象
from .protocol import DeepMotorProtocol
from .deep_motor_mapping import DeepMotorMapping

class DeepMotorProtocolParser(BaseProtocolParser):
    """
    DeepMotor 无刷电机的特定协议解析器 (适配器)。
    负责将 DeepMotor 的底层数据转换为业务语义数据，并将抽象命令转换为 DeepMotor 的底层协议命令。
    此模块现在作为 DeepMotorProtocol (低级协议实现) 和上层应用逻辑之间的适配器。
    """
    
    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, parent: Optional[QObject] = None):
        super().__init__(log_manager, config_manager, parent)
        # 实例化真正的低级协议实现
        self.deep_motor_protocol = DeepMotorProtocol(log_manager=log_manager)
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
            # 调用 DeepMotorProtocol 进行底层数据解码
            response = self.deep_motor_protocol.decode_response(low_level_data)
            
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

    def cleanup(self):
        """
        清理 DeepMotorProtocolParser 资源。
        """
        self.logger.info("DeepMotorProtocolParser: 清理完成。")
        super().cleanup()

