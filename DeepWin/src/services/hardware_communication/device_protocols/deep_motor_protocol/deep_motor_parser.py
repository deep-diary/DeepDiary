# src/services/hardware_communication/device_protocols/deep_motor_protocol/deep_motor_parser.py
# DeepMotor 协议的具体实现 (现在作为协议适配器)

import struct
import time
import logging
from typing import Dict, Any, List, Union, Optional
from PySide6.QtCore import QObject, Signal

from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager
from src.services.hardware_communication.device_protocols.base_protocol_parser import BaseProtocolParser

# 从新的 protocol 文件导入 DeepMotorProtocol 以及命令/响应对象
from src.services.hardware_communication.device_protocols.deep_motor_protocol.protocol import DeepMotorProtocol


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

    def _setup_protocol_rules(self):
        """
        为 DeepMotor 定义输入/输出协议映射规则。
        这里只需定义业务语义与底层协议（通过 DeepMotorProtocol 暴露的抽象命令）之间的映射。
        实际的低级协议细节已封装在 DeepMotorProtocol 中。
        """
        # DeepMotor 的输入数据映射 (由 DeepMotorProtocol 解析后的语义字段)
        self._input_data_mapping = {
            "position": "position", # 从 motor_status 解码
            "velocity": "velocity", # 从 motor_status 解码
            "torque": "torque",     # 从 motor_status 解码
            "temperature": "temperature", # 从 motor_status 解码
            "error_message": "error_message", # 错误信息
            "response_mode": "response_mode",
            "motor_can_id": "motor_can_id",
            "mode_state": "mode_state",
            "flt_uninitialized": "flt_uninitialized",
            "flt_hall_encoding": "flt_hall_encoding",
            "flt_magnetic_encoding": "flt_magnetic_encoding",
            "flt_over_temperature": "flt_over_temperature",
            "flt_over_current": "flt_over_current",
            "flt_voltage_drop": "flt_voltage_drop"
        }


        # DeepMotor 的输出命令映射 (抽象命令名 -> DeepMotorProtocol 中的对应抽象命令)
        self._output_command_mapping = {
            "enable_motor": "enable_motor",
            "disable_motor": "disable_motor",  # 添加失能电机命令
            "reset_motor": "reset_motor",
            "zero_motor": "zero_motor",
            "set_motor_mode": "set_motor_mode",
            "set_motor_mit_mode": "set_motor_mit_mode",
            "write_motor_param": "write_motor_param",
            "read_motor_param": "read_motor_param",
            "jog_motor": "jog_motor",
            "stop_jog_motor": "stop_jog_motor",
            "init_motor": "init_motor",
            "init_all_motors": "init_all_motors",
            "reset_all_motors": "reset_all_motors",
            "set_motor_position": "set_motor_position",
            "set_all_motors_position": "set_all_motors_position",
            "set_motor_pos_speed": "set_motor_pos_speed",
            "set_all_motors_pos_speed": "set_all_motors_pos_speed"
        }
        self.logger.debug("DeepMotorProtocolParser: 协议规则设置完成 (适配器模式)。")


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
                for proto_key, semantic_key in self._input_data_mapping.items():
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

    def generate_output_command(self, command_name: str, *args) -> Union[bytes, List[bytes]]:
        """
        生成 DeepMotor 的底层命令。
        :param command_name: 抽象命令名称。
        :param args: 命令参数。
        :return: 编码后的命令字节串或字节串列表（多帧命令）。
        """
        try:
            self.logger.debug(f"DeepMotorProtocolParser: 生成 DeepMotor 命令 '{command_name}' 参数: {args}")
            
            # 准备命令参数
            kwargs = {}
            
            # 根据命令类型设置参数
            if command_name == 'enable_motor':
                kwargs['motor_id'] = args[0] if args else 1
            elif command_name == 'disable_motor':
                kwargs['motor_id'] = args[0] if args else 1
            elif command_name == 'reset_motor':
                kwargs['motor_id'] = args[0] if args else 1
            elif command_name == 'zero_motor':
                kwargs['motor_id'] = args[0] if args else 1
            elif command_name == 'set_motor_mode':
                kwargs['motor_id'] = args[0] if args else 1
                kwargs['run_mode'] = args[1] if len(args) > 1 else None
            elif command_name == 'set_motor_mit_mode':
                kwargs['motor_id'] = args[0] if args else 1
                kwargs['torque'] = args[1] if len(args) > 1 else 0.0
                kwargs['position'] = args[2] if len(args) > 2 else 0.0
                kwargs['speed'] = args[3] if len(args) > 3 else 0.0
                kwargs['kp'] = args[4] if len(args) > 4 else 0.0
                kwargs['kd'] = args[5] if len(args) > 5 else 0.0
            elif command_name == 'write_motor_param':
                kwargs['motor_id'] = args[0] if args else 1
                kwargs['index'] = args[1] if len(args) > 1 else None
                kwargs['value'] = args[2] if len(args) > 2 else None
            elif command_name == 'read_motor_param':
                kwargs['motor_id'] = args[0] if args else 1
                kwargs['index'] = args[1] if len(args) > 1 else None
            elif command_name == 'jog_motor':
                kwargs['motor_id'] = args[0] if args else 1
                kwargs['speed'] = args[1] if len(args) > 1 else 0
            elif command_name == 'stop_jog_motor':
                kwargs['motor_id'] = args[0] if args else 1
            elif command_name == 'init_motor':
                kwargs['motor_id'] = args[0] if args else 1
            elif command_name == 'init_all_motors':
                kwargs['motor_ids'] = args[0] if args else []
            elif command_name == 'reset_all_motors':
                kwargs['motor_ids'] = args[0] if args else []
            elif command_name == 'set_motor_position':
                kwargs['motor_id'] = args[0] if args else 1
                kwargs['position'] = args[1] if len(args) > 1 else None
            elif command_name == 'set_all_motors_position':
                kwargs['motor_ids'] = args[0] if args else []
                kwargs['positions'] = args[1] if len(args) > 1 else []
            elif command_name == 'set_motor_pos_speed':
                kwargs['motor_id'] = args[0] if args else 1
                kwargs['position'] = args[1] if len(args) > 1 else None
                kwargs['speed'] = args[2] if len(args) > 2 else None
            elif command_name == 'set_all_motors_pos_speed':
                kwargs['motor_ids'] = args[0] if args else []
                kwargs['positions'] = args[1] if len(args) > 1 else []
                kwargs['speeds'] = args[2] if len(args) > 2 else []

            # 使用 DeepMotorProtocol 生成命令
            command = self.deep_motor_protocol.encode_command(command_name, **kwargs)
            
            if isinstance(command, list):
                self.logger.debug(f"DeepMotorProtocolParser: 已生成命令 '{command_name}' (多帧)。")
                # 确保列表中的每个元素都是字节类型
                return [bytes(cmd) if isinstance(cmd, list) else cmd for cmd in command]
            else:
                self.logger.debug(f"DeepMotorProtocolParser: 已生成命令 '{command_name}': {command.hex()}")
                return command
        except Exception as e:
            raise ValueError(f"生成 DeepMotor 命令 '{command_name}' 失败: {e}")

    def cleanup(self):
        """
        清理 DeepMotorProtocolParser 资源。
        """
        self.logger.info("DeepMotorProtocolParser: 清理完成。")
        super().cleanup()

