# src/services/hardware_communication/device_protocols/base_protocol_parser.py
# 定义设备协议解析器的基类

from abc import ABCMeta, abstractmethod
from typing import Dict, Any, List, Union, Optional
from PySide6.QtCore import QObject, Signal, QMetaObject

from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager


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
        # 移除自动调用_setup_protocol_rules，让子类自己决定何时调用
        # self._setup_protocol_rules() # 在这里调用以允许子类加载其规则
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
    def generate_output_command(self, abstract_command_name: str, params: Dict[str, Any]) -> Union[bytes, str]:
        """
        抽象方法：将高级抽象命令（带参数字典）转换为设备可发送的底层协议命令。
        这是推荐的接口，避免了不必要的参数转换和解析。
        :param abstract_command_name: 抽象命令的名称（如 "move_joint_angles"）。
        :param params: 抽象命令的参数字典，键为参数名，值为参数值。
        :return: 转换后的底层命令（bytes 或 str）。
        :raises ValueError: 如果命令不被支持或参数错误。
        """
        pass

    # ==================== 协议管理层的4个核心任务接口 ====================
    
    def convert_command_to_can_frame(self, command_name: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        核心任务1：将抽象命令转换为CAN帧格式
        子类可以重写此方法实现设备特定的CAN帧转换
        :param command_name: 命令名称
        :param params: 命令参数
        :return: CAN帧数据字典 {arbitration_id, data, is_extended_id} 或 None（不支持）
        """
        # 默认实现：尝试通过通用命令生成器生成，然后转换为CAN帧
        try:
            command_data = self.generate_output_command(command_name, params)
            if isinstance(command_data, bytes):
                # 假设命令数据就是CAN帧数据，需要子类重写以提供正确的CAN ID
                return {
                    'arbitration_id': 0x00000000,  # 子类需要重写
                    'data': command_data,
                    'is_extended_id': True
                }
        except Exception:
            pass
        return None
    
    def convert_command_to_serial_frame(self, command_name: str, params: Dict[str, Any]) -> Optional[bytes]:
        """
        核心任务2：将抽象命令直接转换为串口帧（跳过CAN层）
        子类可以重写此方法实现设备特定的串口帧转换
        :param command_name: 命令名称
        :param params: 命令参数
        :return: 串口帧数据 或 None（不支持）
        """
        # 默认实现：尝试通过通用命令生成器生成
        try:
            command_data = self.generate_output_command(command_name, params)
            if isinstance(command_data, bytes):
                return command_data
        except Exception:
            pass
        return None
    
    def parse_can_frame_to_signals(self, can_frame_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        核心任务3：将CAN帧解析为信号字典
        子类可以重写此方法实现设备特定的CAN帧解析
        :param can_frame_data: CAN帧数据字典 {arbitration_id, data, is_extended_id, frame_type}
        :return: 信号字典 或 None（无法解析）
        """
        # 默认实现：调用旧的解析方法
        try:
            return self.parse_input_data("unknown", can_frame_data)
        except Exception:
            pass
        return None
    
    def parse_serial_frame_to_signals(self, serial_frame_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        核心任务4：将串口帧解析为信号字典
        子类可以重写此方法实现设备特定的串口帧解析
        :param serial_frame_data: 串口帧数据字典 {data, frame_type}
        :return: 信号字典 或 None（无法解析）
        """
        # 默认实现：调用旧的解析方法
        try:
            return self.parse_input_data("unknown", serial_frame_data)
        except Exception:
            pass
        return None

    def cleanup(self):
        """
        清理协议解析器资源。子类可以重写此方法进行特定清理。
        """
        self.logger.info(f"{self.__class__.__name__}: 清理完成。")