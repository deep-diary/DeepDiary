# src/services/hardware_communication/device_protocols/base_protocol_parser.py
# 定义设备协议解析器的基类

from abc import ABCMeta, abstractmethod
from typing import Dict, Any, List, Union, Optional
from PySide6.QtCore import QObject, Signal, QMetaObject

from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager


class ProtocolParserMeta(ABCMeta, type(QObject)):
    """
    自定义元类，用于协调 ABCMeta 和 QObject 的元类。
    """
    pass


class BaseProtocolParser(QObject, metaclass=ProtocolParserMeta):
    """
    所有设备协议解析器实现的抽象基类。
    定义了将低级数据转换为业务语义数据，以及将抽象命令转换为底层协议命令的接口。
    """
    protocol_conversion_error = Signal(str, str) # (device_id, error_message)

    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, parent: Optional[QObject] = None):
        """
        初始化 BaseProtocolParser。
        :param log_manager: 全局日志管理器实例。
        :param config_manager: 全局配置管理器实例。
        :param parent: QObject 父对象。
        """
        super().__init__(parent)
        self.logger = log_manager.get_logger(f"{self.__class__.__name__}")
        self.config_manager = config_manager
        self.logger.info(f"{self.__class__.__name__}: 初始化中...")
        self._setup_protocol_rules() # 在这里调用以允许子类加载其规则
        self.logger.info(f"{self.__class__.__name__}: 初始化完成。")

    @abstractmethod
    def _setup_protocol_rules(self):
        """
        抽象方法：子类应在此方法中定义其设备特定的输入/输出协议映射规则。
        """
        pass

    @abstractmethod
    def parse_input_data(self, device_id: str, low_level_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        抽象方法：将低层次的设备数据（如 CAN 信号字典）转换为业务语义数据。
        :param device_id: 设备的唯一标识符。
        :param low_level_data: 来自通信模块的解析数据（如 CAN 信号字典）。
        :return: 转换后的业务语义数据字典。
        """
        pass

    @abstractmethod
    def generate_output_command(self, abstract_command_name: str, *args) -> Union[bytes, str]:
        """
        抽象方法：将高级抽象命令转换为设备可发送的底层协议命令。
        :param abstract_command_name: 抽象命令的名称（如 "move_joint_angles"）。
        :param args: 抽象命令的参数。
        :return: 转换后的底层命令（bytes 或 str）。
        :raises ValueError: 如果命令不被支持或参数错误。
        """
        pass

    def cleanup(self):
        """
        清理协议解析器资源。子类可以重写此方法进行特定清理。
        """
        self.logger.info(f"{self.__class__.__name__}: 清理完成。")