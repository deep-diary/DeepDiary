# src/services/hardware_communication/device_protocols/deep_arm_protocol/deep_arm_parser.py
# DeepArm 协议的具体实现

import os
import can
from can.listener import Listener
import cantools # 导入 cantools 库以加载 DBC 文件
from typing import Dict, Any, List, Union, Optional
from PySide6.QtCore import QObject

from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager
from src.services.hardware_communication.device_protocols.base_protocol_parser import BaseProtocolParser


class DeepArmProtocolParser(BaseProtocolParser):
    """
    DeepArm 机械臂的特定协议解析器。
    负责将 DeepArm 的 CAN 信号转换为业务语义数据，并将抽象命令转换为 DeepArm 的底层协议命令。
    """
    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, parent: Optional[QObject] = None):
        super().__init__(log_manager, config_manager, parent)
        self.db = None # 用于存储加载的 DBC 数据库

    def _setup_protocol_rules(self):
        """
        为 DeepArm 定义输入/输出协议映射规则。
        这里会加载 DeepArm 专用的 DBC 文件，并定义语义转换规则。
        """
        dbc_path = self.config_manager.get('device_settings.deeparm_dbc_path')
        # 确保 DBC 文件路径是相对于当前文件的正确路径
        current_dir = os.path.dirname(__file__)
        full_dbc_path = os.path.join(current_dir, os.path.basename(dbc_path))

        if not os.path.exists(full_dbc_path):
            self.logger.error(f"DeepArmProtocolParser: DBC 文件不存在于 {full_dbc_path}")
            # 可以在这里发出信号通知 Coordinator
            return

        try:
            self.db = cantools.database.load_file(full_dbc_path)
            self.logger.info(f"DeepArmProtocolParser: 已加载 DeepArm DBC 文件: {full_dbc_path}")
        except Exception as e:
            self.logger.error(f"DeepArmProtocolParser: 加载 DBC 文件 '{full_dbc_path}' 失败: {e}")
            self.protocol_conversion_error.emit("DeepArm", f"加载 DBC 失败: {e}")

        # DeepArm 的输入数据映射 (DBC 信号名 -> 业务语义字段名)
        self._input_data_mapping = {
            "Joint1Angle": "joint1_angle",
            "Joint2Angle": "joint2_angle",
            "Joint3Angle": "joint3_angle",
            "Joint4Angle": "joint4_angle",
            "Joint5Angle": "joint5_angle",
            "Joint6Angle": "joint6_angle",
            "ArmTemperature": "temperature",
            "ArmStatusCode": "current_status",
            # 示例：更复杂的转换，假设DBC中温度是原始值，需要转换为摄氏度
            # "RawTemperatureSensor": {"semantic_key": "temperature_celsius", "transform": lambda raw_val: (raw_val * 0.01) - 50 }
        }

        # DeepArm 的输出命令映射 (抽象命令名 -> 编码函数)
        # 编码函数接收抽象命令的参数，返回底层字节串
        self._output_command_mapping = {
            "move_joint_angles": self._encode_move_joint_angles_command,
            "reset_arm": self._encode_reset_arm_command,
        }
        self.logger.debug("DeepArmProtocolParser: 协议规则设置完成。")

    def parse_input_data(self, device_id: str, low_level_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将 DeepArm 的低层次数据（DBC 解析后的信号字典）转换为业务语义数据。
        :param device_id: DeepArm 设备的唯一标识符。
        :param low_level_data: 来自 CanBusCommunicator 的解析数据（CAN 信号字典）。
                                例如: {"Joint1Angle": 170, "ArmTemperature": 75}
        :return: 转换后的业务语义数据字典。
                 例如: {"device_type": "DeepArm", "joint1_angle": 170, "temperature": 75}
        """
        semantic_data: Dict[str, Any] = {"device_id": device_id, "device_type": "DeepArm"}
        
        for low_key, semantic_key_info in self._input_data_mapping.items():
            if low_key in low_level_data:
                if isinstance(semantic_key_info, dict):
                    # 处理复杂转换
                    target_key = semantic_key_info.get("semantic_key")
                    transform_func = semantic_key_info.get("transform")
                    map_values = semantic_key_info.get("map_values")

                    if target_key:
                        value = low_level_data[low_key]
                        if transform_func:
                            semantic_data[target_key] = transform_func(value)
                        elif map_values:
                            semantic_data[target_key] = map_values.get(value, value)
                        else:
                            semantic_data[target_key] = value # 默认直传
                    else:
                        self.logger.warning(f"DeepArmProtocolParser: 复杂映射 '{low_key}' 缺少 'semantic_key'。")
                else:
                    # 简单直传或重命名
                    semantic_data[semantic_key_info] = low_level_data[low_key]
            else:
                self.logger.debug(f"DeepArmProtocolParser: 低级数据中未找到键: {low_key}")

        return semantic_data

    def generate_output_command(self, abstract_command_name: str, *args) -> Union[bytes, str]:
        """
        将高级抽象命令转换为 DeepArm 可发送的底层协议命令。
        :param abstract_command_name: 抽象命令的名称（如 "move_joint_angles"）。
        :param args: 抽象命令的参数。
        :return: 转换后的底层命令（bytes）。
        :raises ValueError: 如果命令不被支持或参数错误。
        """
        command_func = self._output_command_mapping.get(abstract_command_name)
        if not command_func:
            raise ValueError(f"DeepArm 协议不支持抽象命令 '{abstract_command_name}'。")
        
        try:
            low_level_command = command_func(*args)
            self.logger.debug(f"DeepArmProtocolParser: 已生成命令 '{abstract_command_name}': {low_level_command.hex()}")
            return low_level_command
        except Exception as e:
            raise ValueError(f"生成 DeepArm 命令 '{abstract_command_name}' 失败: {e}")

    # --- 内部命令编码函数 ---
    def _encode_move_joint_angles_command(self, *angles) -> bytes:
        """
        编码 'move_joint_angles' 命令。
        假设 DeepArm 的关节角度命令通过 CAN ID 0x101 发送，数据长度 6 字节。
        每个角度为 0-255 的整数。
        """
        if len(angles) != 6:
            raise ValueError("move_joint_angles 命令需要 6 个关节角度参数。")
        
        # 示例：将浮点角度转换为 0-255 范围内的整数（实际需要根据机械臂的真实范围和精度进行调整）
        encoded_angles = [max(0, min(255, int(a))) for a in angles]
        data_bytes = bytes(encoded_angles)

        # 假设 CAN ID 0x101，长度 6，数据为关节角度字节
        can_id = 0x101
        data_len = 6
        # 组装成 "AT" + CANID (hex) + Len (hex) + Data (hex) + "\r\n"
        return f"AT{can_id:08X}{data_len:02X}{data_bytes.hex()}\r\n".encode('ascii')

    def _encode_reset_arm_command(self) -> bytes:
        """
        编码 'reset_arm' 命令。
        假设 DeepArm 的复位命令通过 CAN ID 0x102 发送，数据为 0xFF。
        """
        can_id = 0x102
        data_len = 1
        data_byte = 0xFF
        return f"AT{can_id:08X}{data_len:02X}{data_byte:02X}\r\n".encode('ascii')

    def cleanup(self):
        """
        清理 DeepArmProtocolParser 资源。
        """
        self.logger.info("DeepArmProtocolParser: 清理完成。")
        super().cleanup()