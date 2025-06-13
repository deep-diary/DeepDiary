# src/services/hardware_communication/__init__.py
# 本地硬件通信服务包

from .serial_communicator import SerialCommunicator
from .can_bus_communicator import CanBusCommunicator
from .device_protocol_parser import DeviceProtocolParser # 现在是管理器

# 导入设备特定的协议解析器（如果需要直接在外部访问）
from .device_protocols.base_protocol_parser import BaseProtocolParser
from .device_protocols.deep_arm_protocol.deep_arm_parser import DeepArmProtocolParser
from .device_protocols.deep_motor_protocol.deep_motor_parser import DeepMotorProtocolParser

# from .driver_manager import DriverManager # 假设尚未实现或不在此处导出

