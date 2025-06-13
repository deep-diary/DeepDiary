# src/services/hardware_communication/device_protocol_parser.py
# 设备协议解析器 (作为管理器和调度器)

import time
from PySide6.QtCore import QObject, Signal, Slot
from typing import Dict, Any, Optional, Union, List

from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager

# 导入具体的设备协议解析器
from src.services.hardware_communication.device_protocols.base_protocol_parser import BaseProtocolParser
from src.services.hardware_communication.device_protocols.deep_arm_protocol.deep_arm_parser import DeepArmProtocolParser
from src.services.hardware_communication.device_protocols.deep_motor_protocol.deep_motor_parser import DeepMotorProtocolParser


class DeviceProtocolParser(QObject):
    """
    底层设备协议解析器管理器。
    负责管理和调度不同设备的具体协议解析器。
    它接收来自 SerialCommunicator 或 CanBusCommunicator 的初步解析后的低层次结构化数据，
    根据设备类型将其转发给对应的设备协议解析器，转换为业务语义数据。
    它也负责将应用逻辑层生成的抽象控制命令转发给对应的设备协议解析器，转换为设备可识别的协议格式。
    """
    device_semantic_data_ready = Signal(str, dict)
    protocol_conversion_error = Signal(str, str) # 由具体的协议解析器发出，这里连接

    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, parent: Optional[QObject] = None):
        """
        初始化 DeviceProtocolParser 管理器。
        :param log_manager: 全局日志管理器实例。
        :param config_manager: 全局配置管理器实例。
        :param parent: QObject 父对象。
        """
        super().__init__(parent)
        self.logger = log_manager.get_logger(__name__)
        self.config_manager = config_manager
        self.logger.info("DeviceProtocolParser Manager: 初始化中...")
        
        # 存储设备ID前缀到具体协议解析器实例的映射
        self._device_parsers: Dict[str, BaseProtocolParser] = {}
        self._initialize_device_parsers(log_manager, config_manager)

        self.logger.info("DeviceProtocolParser Manager: 初始化完成。")

    def _initialize_device_parsers(self, log_manager: LogManager, config_manager: ConfigManager):
        """
        初始化所有支持的设备协议解析器。
        """
        self.logger.info("DeviceProtocolParser Manager: 正在初始化设备协议解析器...")
        # 实例化 DeepArm 协议解析器
        deep_arm_parser = DeepArmProtocolParser(log_manager=log_manager, config_manager=config_manager)
        self._device_parsers["DeepArm"] = deep_arm_parser
        # 连接 DeepArm 协议解析器的错误信号到本管理器的错误信号
        deep_arm_parser.protocol_conversion_error.connect(self.protocol_conversion_error)

        # 实例化 DeepMotor 协议解析器
        deep_motor_parser = DeepMotorProtocolParser(log_manager=log_manager, config_manager=config_manager)
        self._device_parsers["DeepMotor"] = deep_motor_parser
        # 连接 DeepMotor 协议解析器的错误信号
        deep_motor_parser.protocol_conversion_error.connect(self.protocol_conversion_error)

        # 可以在这里添加更多设备类型
        self.logger.info("DeviceProtocolParser Manager: 设备协议解析器初始化完成。")


    @Slot(str, dict)
    def parse_low_level_data(self, device_id: str, low_level_data: Dict[str, Any]):
        """
        将低层次解析数据（如 CAN 信号字典或原始串口数据字典）转换为业务语义数据。
        管理器根据 device_id 路由到对应的具体协议解析器。
        :param device_id: 设备的唯一标识符。
        :param low_level_data: 来自 SerialCommunicator 或 CanBusCommunicator 的解析数据。
                                对于 DeepArm，通常是 CAN 信号字典。
                                对于 DeepMotor，可能是原始串口数据解析后的字典。
        """
        self.logger.debug(f"DeviceProtocolParser Manager: 收到设备 '{device_id}' 的低层数据: {low_level_data}")
        
        device_type = None
        # 根据 device_id 前缀确定设备类型，以便路由到正确的解析器
        if device_id.startswith("DeepArm"):
            device_type = "DeepArm"
        elif device_id.startswith("DeepMotor"):
            device_type = "DeepMotor"
        # 可以在这里添加更多设备类型的判断

        device_parser = self._device_parsers.get(device_type)
        if not device_parser:
            error_msg = f"DeviceProtocolParser Manager: 未找到设备ID '{device_id}' (类型: {device_type}) 对应的协议解析器。"
            self.logger.warning(error_msg)
            self.protocol_conversion_error.emit(device_id, error_msg)
            return

        try:
            # 调用具体设备解析器的方法进行解析
            semantic_data = device_parser.parse_input_data(device_id, low_level_data)
            self.logger.debug(f"DeviceProtocolParser Manager: 设备 '{device_id}' 语义数据解析完成: {semantic_data}")
            self.device_semantic_data_ready.emit(device_id, semantic_data)
        except Exception as e:
            error_msg = f"DeviceProtocolParser Manager: 解析设备 '{device_id}' 协议数据失败: {e}"
            self.logger.error(f"DeviceProtocolParser Manager: {error_msg}")
            self.protocol_conversion_error.emit(device_id, error_msg)

    def generate_low_level_command(self, device_id: str, abstract_command_name: str, *args) -> Union[bytes, str]:
        """
        将应用逻辑层的高级抽象命令转发给对应的具体协议解析器，转换为底层协议可发送的命令。
        :param device_id: 目标设备的唯一标识符。
        :param abstract_command_name: 抽象命令的名称 (如 "move_joint_angles", "set_motor_rpm")。
        :param args: 抽象命令的参数。
        :return: 转换后的底层命令 (bytes 或 str)。
        :raises ValueError: 如果设备或命令不被支持。
        """
        self.logger.debug(f"DeviceProtocolParser Manager: 生成设备 '{device_id}' 的底层命令 for '{abstract_command_name}'")
        
        device_type = None
        if device_id.startswith("DeepArm"):
            device_type = "DeepArm"
        elif device_id.startswith("DeepMotor"):
            device_type = "DeepMotor"

        device_parser = self._device_parsers.get(device_type)
        if not device_parser:
            raise ValueError(f"DeviceProtocolParser Manager: 未找到设备ID '{device_id}' (类型: {device_type}) 对应的命令生成器。")

        try:
            # 调用具体设备解析器的方法生成命令
            low_level_command = device_parser.generate_output_command(abstract_command_name, *args)
            self.logger.debug(f"DeviceProtocolParser Manager: 已生成底层命令: {low_level_command.hex() if isinstance(low_level_command, bytes) else low_level_command}")
            return low_level_command
        except Exception as e:
            raise ValueError(f"DeviceProtocolParser Manager: 生成设备 '{device_id}' 命令 '{abstract_command_name}' 失败: {e}")

    def cleanup(self):
        """
        清理协议解析器管理器及其管理的具体协议解析器资源。
        """
        self.logger.info("DeviceProtocolParser Manager: 执行清理工作。")
        for parser in self._device_parsers.values():
            parser.cleanup()
        self.logger.info("DeviceProtocolParser Manager: 清理完成。")

