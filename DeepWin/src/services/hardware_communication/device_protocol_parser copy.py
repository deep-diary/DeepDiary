from typing import Dict, Any, Union, Optional
from PySide6.QtCore import QObject, Signal, Slot
from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager

class DeviceProtocolParser(QObject):
    """
    底层设备协议解析器。
    接收来自 SerialCommunicator 或 CanBusCommunicator 的初步解析后的低层次结构化数据，
    并根据 DeepArm、DeepToy 等不同设备的私有通信协议，将其进一步转换为
    应用逻辑层可以直接使用的业务语义数据格式。
    它也负责将应用逻辑层生成的控制命令转换为设备可识别的协议格式。
    """
    device_semantic_data_ready = Signal(str, dict) # 解析出业务语义数据: (device_id, semantic_data_dict)
    protocol_conversion_error = Signal(str, str) # 协议转换错误: (device_id, error_msg)

    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, parent: Optional[QObject] = None):
        """
        初始化 DeviceProtocolParser。
        :param log_manager: 全局日志管理器实例。
        :param parent: QObject 父对象。
        """
        super().__init__(parent)
        self.logger = log_manager.get_logger(__name__)
        self.config_manager = config_manager
        self.logger.info("DeviceProtocolParser: 初始化中...")
        # 实际项目中，这里会加载不同设备的私有协议定义（例如，JSON 规则、自定义二进制帧格式）
        self._device_protocol_rules: Dict[str, Any] = {
            "DeepArm": {
                "input_data_mapping": { # 假设 CAN 总线传来的是 joint_angles, temperature
                    "Joint1Angle": "joint1_angle", # DBC 信号名 -> 业务字段名
                    "Joint2Angle": "joint2_angle",
                    "ArmTemperature": "temperature",
                    "ArmStatusCode": "current_status"
                },
                "output_command_mapping": {
                    # move_joint_angles: 6个关节角度，组装为 AT+CANID+Len+Data+\r\n
                    "move_joint_angles": lambda *angles: f"AT00000106{''.join([f'{int(a):02X}' for a in angles])}\r\n".encode('ascii'),
                    "reset_arm": lambda: b"AT00000101FF\r\n",
                }
            },
            "DeepToy": {
                "input_data_mapping": {
                    "DI_status": "digital_inputs",
                    "Battery": "battery_level"
                },
                "output_command_mapping": {
                    "set_io": lambda pin, state: f"CMD_TOY_IO:{pin},{1 if state else 0}".encode('ascii'),
                }
            },
            "DeepMotor": {
                "input_data_mapping": {
                    "position": "position",
                    "velocity": "velocity",
                    "torque": "torque",
                    "temperature": "temperature"
                },
                "output_command_mapping": {
                    "set_motor_rpm": lambda rpm: f"AT00000202{int(rpm):04X}\r\n".encode('ascii'),
                    "set_rpm": lambda rpm: f"AT00000202{int(rpm):04X}\r\n".encode('ascii'),
                }
            }
        }
        self.logger.info("DeviceProtocolParser: 初始化完成。")

    @Slot(str, dict) # 接收来自 CanBusCommunicator 的解析后的信号字典
    def parse_low_level_data(self, device_id: str, low_level_data: Dict[str, Any]):
        """
        将低层次解析数据（如 CAN 信号字典）转换为业务语义数据。
        :param device_id: 设备的唯一标识符。
        :param low_level_data: 来自 CanBusCommunicator 的解析数据（CAN 信号字典）。
        """
        self.logger.debug(f"DeviceProtocolParser: 收到设备 '{device_id}' 的低层数据: {low_level_data}")
        semantic_data: Dict[str, Any] = {"device_id": device_id}
        device_type = None

        if device_id.startswith("DeepArm"):
            device_type = "DeepArm"
        elif device_id.startswith("DeepToy"):
            device_type = "DeepToy"
        elif device_id.startswith("DeepMotor"):
            device_type = "DeepMotor"
        else:
            self.logger.warning(f"DeviceProtocolParser: 未知设备ID类型: {device_id}")
            self.protocol_conversion_error.emit(device_id, f"未知设备ID类型: {device_id}")
            return

        rules = self._device_protocol_rules.get(device_type)
        if not rules:
            self.logger.warning(f"DeviceProtocolParser: 未找到设备类型 '{device_type}' 的协议解析规则。")
            self.protocol_conversion_error.emit(device_id, f"未找到 '{device_type}' 的解析规则。")
            return

        try:
            input_mapping = rules.get("input_data_mapping", {})
            for low_key, semantic_key in input_mapping.items():
                if low_key in low_level_data:
                    semantic_data[semantic_key] = low_level_data[low_key]
                    self.logger.info(f"DeviceProtocolParser: 设备 '{device_id}' 匹配到低层数据: {low_key} -> {semantic_key}, 值: {low_level_data[low_key]}")
            
            # TODO: 根据设备和协议，进行更复杂的转换逻辑
            # 例如，从关节角度计算末端坐标，或将原始传感器值转换为物理量
            # 这里的示例中，我们假设 low_level_data 已经是 CAN 信号字典，直接映射即可。

            self.logger.debug(f"DeviceProtocolParser: 设备 '{device_id}' 语义数据解析完成: {semantic_data}")
            self.device_semantic_data_ready.emit(device_id, semantic_data)
        except Exception as e:
            error_msg = f"解析设备 '{device_id}' 协议数据失败: {e}"
            self.logger.error(f"DeviceProtocolParser: {error_msg}")
            self.protocol_conversion_error.emit(device_id, error_msg)

    def generate_low_level_command(self, device_id: str, abstract_command_name: str, *args) -> Union[bytes, str]:
        """
        将应用逻辑层的高级抽象命令转换为底层协议可发送的命令。
        :param device_id: 目标设备的唯一标识符。
        :param abstract_command_name: 抽象命令的名称 (如 "move_joint_angles")。
        :param args: 抽象命令的参数。
        :return: 转换后的底层命令 (bytes 或 str)。
        :raises ValueError: 如果设备或命令不被支持。
        """
        self.logger.debug(f"DeviceProtocolParser: 生成设备 '{device_id}' 的底层命令 for '{abstract_command_name}'")
        device_type = None
        if device_id.startswith("DeepArm"):
            device_type = "DeepArm"
        elif device_id.startswith("DeepToy"):
            device_type = "DeepToy"
        elif device_id.startswith("DeepMotor"):
            device_type = "DeepMotor"
        else:
            raise ValueError(f"不支持的设备ID类型: {device_id}")

        rules = self._device_protocol_rules.get(device_type)
        if not rules:
            raise ValueError(f"未找到设备类型 '{device_type}' 的协议转换规则。")

        output_mapping = rules.get("output_command_mapping", {})
        command_func = output_mapping.get(abstract_command_name)
        if not command_func:
            raise ValueError(f"设备类型 '{device_type}' 不支持抽象命令 '{abstract_command_name}'。")

        try:
            low_level_command = command_func(*args)
            if isinstance(low_level_command, str):
                return low_level_command.encode('utf-8') # 默认编码为 bytes
            return low_level_command
        except Exception as e:
            raise ValueError(f"生成底层命令 '{abstract_command_name}' 失败: {e}")

    def cleanup(self):
        """
        清理协议解析器资源。
        """
        self.logger.info("DeviceProtocolParser: 清理完成。")