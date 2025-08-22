# src/services/hardware_communication/device_protocols/example_sensor_protocol/example_sensor_parser.py
# 示例传感器协议解析器 (演示如何添加新设备)

from typing import Dict, Any, Union, List, Optional
from PySide6.QtCore import QObject

from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager
from deepwin.services.hardware_communication.device_protocols.base_protocol_parser import BaseProtocolParser


class ExampleSensorProtocolParser(BaseProtocolParser):
    """
    示例传感器协议解析器。
    这是一个演示如何按照新规则添加新设备的示例。
    文件夹名: example_sensor_protocol
    文件名: example_sensor_parser.py
    类名: ExampleSensorProtocolParser
    设备类型: ExampleSensor
    """
    
    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, parent: Optional[QObject] = None):
        super().__init__(log_manager, config_manager, parent)
        self.logger.info("ExampleSensorProtocolParser: 初始化完成")

    def _setup_protocol_rules(self):
        """
        为示例传感器定义输入/输出协议映射规则。
        """
        # 示例传感器的输入数据映射
        self._input_data_mapping = {
            "temperature": "temperature",
            "humidity": "humidity",
            "pressure": "pressure",
            "light_level": "light_level",
            "sensor_status": "sensor_status",
            "battery_level": "battery_level"
        }

        # 示例传感器的输出命令映射
        self._output_command_mapping = {
            "read_sensor_data": "read_sensor_data",
            "set_sampling_rate": "set_sampling_rate",
            "calibrate_sensor": "calibrate_sensor",
            "reset_sensor": "reset_sensor",
            "get_sensor_info": "get_sensor_info"
        }
        
        self.logger.debug("ExampleSensorProtocolParser: 协议规则设置完成")

    def parse_input_data(self, device_id: str, low_level_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        将示例传感器的低层次数据转换为业务语义数据。
        :param device_id: 传感器设备的唯一标识符。
        :param low_level_data: 原始数据字典。
        :return: 转换后的业务语义数据字典。
        """
        semantic_data: Dict[str, Any] = {"device_id": device_id, "device_type": "ExampleSensor"}
        
        try:
            # 模拟数据解析逻辑
            if isinstance(low_level_data, dict):
                # 直接映射数据字段
                for proto_key, semantic_key in self._input_data_mapping.items():
                    if proto_key in low_level_data:
                        semantic_data[semantic_key] = low_level_data[proto_key]
                
                semantic_data["success"] = True
                self.logger.debug(f"ExampleSensorProtocolParser: 成功解析设备 '{device_id}' 的数据")
            else:
                semantic_data["success"] = False
                semantic_data["error_message"] = "数据格式错误"
                self.protocol_conversion_error.emit(device_id, "数据格式错误")

        except Exception as e:
            error_msg = f"ExampleSensorProtocolParser: 解析数据失败: {e}"
            self.logger.error(error_msg)
            self.protocol_conversion_error.emit(device_id, error_msg)
            semantic_data["success"] = False
            semantic_data["error_message"] = error_msg
        
        return semantic_data

    def generate_output_command(self, command_name: str, *args) -> Union[bytes, List[bytes]]:
        """
        生成示例传感器的底层命令。
        :param command_name: 抽象命令名称。
        :param args: 命令参数。
        :return: 编码后的命令字节串。
        """
        try:
            self.logger.debug(f"ExampleSensorProtocolParser: 生成命令 '{command_name}' 参数: {args}")
            
            # 模拟命令生成逻辑
            if command_name == 'read_sensor_data':
                # 模拟读取传感器数据的命令
                command = b'\x01\x02\x03\x04'  # 示例命令字节
            elif command_name == 'set_sampling_rate':
                rate = args[0] if args else 1000
                command = f"SET_RATE:{rate}".encode()
            elif command_name == 'calibrate_sensor':
                command = b'\x05\x06\x07\x08'  # 校准命令
            elif command_name == 'reset_sensor':
                command = b'\x09\x0A\x0B\x0C'  # 重置命令
            elif command_name == 'get_sensor_info':
                command = b'\x0D\x0E\x0F\x10'  # 获取信息命令
            else:
                raise ValueError(f"不支持的命令: {command_name}")
            
            self.logger.debug(f"ExampleSensorProtocolParser: 已生成命令 '{command_name}': {command.hex()}")
            return command
            
        except Exception as e:
            raise ValueError(f"生成示例传感器命令 '{command_name}' 失败: {e}")

    def cleanup(self):
        """
        清理示例传感器协议解析器资源。
        """
        self.logger.info("ExampleSensorProtocolParser: 清理完成")
        super().cleanup() 