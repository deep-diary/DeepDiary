# src/services/hardware_communication/device_protocols/deep_motor_protocol/deep_motor_parser.py
# DeepMotor 协议的具体实现

from typing import Dict, Any, List, Union, Optional

from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager
from src.services.hardware_communication.device_protocols.base_protocol_parser import BaseProtocolParser
from PySide6.QtCore import QObject


class DeepMotorProtocolParser(BaseProtocolParser):
    """
    DeepMotor 无刷电机的特定协议解析器。
    负责将 DeepMotor 的底层数据转换为业务语义数据，并将抽象命令转换为 DeepMotor 的底层协议命令。
    假设 DeepMotor 有自己的简单串口协议，不使用 CAN 或 DBC。
    """
    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, parent: Optional[QObject] = None):
        super().__init__(log_manager, config_manager, parent)

    def _setup_protocol_rules(self):
        """
        为 DeepMotor 定义输入/输出协议映射规则。
        假设 DeepMotor 使用简单的自定义串口协议。
        """
        self._input_data_mapping = {
            # 假设 DeepMotor 原始数据是字典 {"rpm_raw": 1000, "current_mv": 500, "temp_c": 45, "err_code": 0}
            "rpm_raw": "motor_rpm",
            "current_mv": {"semantic_key": "motor_current", "transform": lambda mv: mv / 1000.0}, # 毫伏转换为安培
            "temp_c": "motor_temperature",
            "err_code": "error_code"
        }

        self._output_command_mapping = {
            # 假设设置 RPM 命令格式为 "SET_RPM:VALUE\r\n"
            "set_motor_rpm": lambda rpm: f"SET_RPM:{int(rpm)}\r\n".encode('ascii'),
            # 假设获取状态命令格式为 "GET_STATUS\r\n"
            "get_motor_status": lambda: b"GET_STATUS\r\n"
        }
        self.logger.debug("DeepMotorProtocolParser: 协议规则设置完成。")

    def parse_input_data(self, device_id: str, low_level_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将 DeepMotor 的低层次数据转换为业务语义数据。
        :param device_id: DeepMotor 设备的唯一标识符。
        :param low_level_data: 来自通信模块的解析数据（例如，从串口读取并初步解析的字典）。
                                例如: {"rpm_raw": 1000, "current_mv": 500}
        :return: 转换后的业务语义数据字典。
                 例如: {"device_type": "DeepMotor", "motor_rpm": 1000, "motor_current": 0.5}
        """
        semantic_data: Dict[str, Any] = {"device_id": device_id, "device_type": "DeepMotor"}
        
        for low_key, semantic_key_info in self._input_data_mapping.items():
            if low_key in low_level_data:
                if isinstance(semantic_key_info, dict):
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
                            semantic_data[target_key] = value
                    else:
                        self.logger.warning(f"DeepMotorProtocolParser: 复杂映射 '{low_key}' 缺少 'semantic_key'。")
                else:
                    semantic_data[semantic_key_info] = low_level_data[low_key]
            else:
                self.logger.debug(f"DeepMotorProtocolParser: 低级数据中未找到键: {low_key}")

        return semantic_data

    def generate_output_command(self, abstract_command_name: str, *args) -> Union[bytes, str]:
        """
        将高级抽象命令转换为 DeepMotor 可发送的底层协议命令。
        :param abstract_command_name: 抽象命令的名称（如 "set_motor_rpm"）。
        :param args: 抽象命令的参数。
        :return: 转换后的底层命令（bytes）。
        :raises ValueError: 如果命令不被支持或参数错误。
        """
        command_func = self._output_command_mapping.get(abstract_command_name)
        if not command_func:
            raise ValueError(f"DeepMotor 协议不支持抽象命令 '{abstract_command_name}'。")
        
        try:
            low_level_command = command_func(*args)
            self.logger.debug(f"DeepMotorProtocolParser: 已生成命令 '{abstract_command_name}': {low_level_command.hex() if isinstance(low_level_command, bytes) else low_level_command}")
            return low_level_command
        except Exception as e:
            raise ValueError(f"生成 DeepMotor 命令 '{abstract_command_name}' 失败: {e}")

    def cleanup(self):
        """
        清理 DeepMotorProtocolParser 资源。
        """
        self.logger.info("DeepMotorProtocolParser: 清理完成。")
        super().cleanup()
