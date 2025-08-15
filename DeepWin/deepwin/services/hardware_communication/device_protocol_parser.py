# src/services/hardware_communication/device_protocol_parser.py
# 设备协议解析器 (作为管理器和调度器)

import os
import importlib
import re
from typing import Dict, Any, Optional, Union, List
from PySide6.QtCore import QObject, Signal, Slot

from deepwin.data_management.log_manager import LogManager
from deepwin.data_management.config_manager import ConfigManager

# 导入基础协议解析器
from deepwin.services.hardware_communication.device_protocols.base_protocol_parser import BaseProtocolParser


class DeviceProtocolParser(QObject):
    """
    底层设备协议解析器管理器。
    负责自动发现、管理和调度不同设备的具体协议解析器。
    它接收来自 SerialCommunicator 或 CanBusCommunicator 的初步解析后的低层次结构化数据，
    根据设备类型将其转发给对应的设备协议解析器，转换为业务语义数据。
    它也负责将应用逻辑层生成的抽象控制命令转发给对应的设备协议解析器，转换为设备可识别的协议格式。
    """
    device_semantic_data_ready = Signal(str, dict)
    protocol_conversion_error = Signal(str, str)  # 由具体的协议解析器发出，这里连接

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
        
        # 存储设备ID前缀到具体协议解析器实例的映射
        self._device_parsers: Dict[str, BaseProtocolParser] = {}
        self._device_type_mapping: Dict[str, str] = {}  # device_id_prefix -> device_type
        
        # 自动发现和注册设备协议解析器
        self._auto_discover_and_register_parsers(log_manager, config_manager)

    def _auto_discover_and_register_parsers(self, log_manager: LogManager, config_manager: ConfigManager):
        """
        自动发现并注册设备协议解析器。
        根据 device_protocols 目录下的子文件夹名称自动提取设备类型和解析器类。
        """
        self.logger.info("开始自动发现设备协议解析器...")
        
        # 获取 device_protocols 目录的绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        protocols_dir = os.path.join(current_dir, "device_protocols")
        
        if not os.path.exists(protocols_dir):
            self.logger.error(f"设备协议目录不存在: {protocols_dir}")
            return
        
        # 遍历 device_protocols 目录下的子文件夹
        for item in os.listdir(protocols_dir):
            item_path = os.path.join(protocols_dir, item)
            
            # 只处理目录，跳过文件
            if not os.path.isdir(item_path):
                continue
                
            # 跳过 __pycache__ 等特殊目录
            if item.startswith('__') or item.startswith('.'):
                continue
            
            # 根据文件夹名称提取设备类型
            device_type = self._extract_device_type_from_folder_name(item)
            if not device_type:
                self.logger.warning(f"无法从文件夹名称 '{item}' 提取设备类型，跳过")
                continue
            
            # 尝试导入对应的协议解析器
            parser_class = self._import_parser_class(item, device_type)
            if not parser_class:
                self.logger.warning(f"无法导入设备 '{device_type}' 的协议解析器类，跳过")
                continue
            
            # 实例化协议解析器
            try:
                parser_instance = parser_class(log_manager=log_manager, config_manager=config_manager)
                self._device_parsers[device_type] = parser_instance
                
                # 连接错误信号
                parser_instance.protocol_conversion_error.connect(self.protocol_conversion_error)
                
                # 建立设备ID前缀到设备类型的映射
                self._device_type_mapping[device_type] = device_type
                
                self.logger.info(f"成功注册设备协议解析器: {device_type} -> {parser_class.__name__}")
                
            except Exception as e:
                self.logger.error(f"实例化设备 '{device_type}' 的协议解析器失败: {e}")
        
        registered_devices = list(self._device_parsers.keys())
        self.logger.info(f"设备协议解析器注册完成，共注册 {len(registered_devices)} 个设备: {registered_devices}")

    def _extract_device_type_from_folder_name(self, folder_name: str) -> Optional[str]:
        """
        从文件夹名称提取设备类型。
        规则：将 snake_case 转换为 PascalCase，例如：
        - deep_motor_protocol -> DeepMotor
        - deep_arm_protocol -> DeepArm
        - my_device_protocol -> MyDevice
        """
        # 移除 _protocol 后缀
        if folder_name.endswith('_protocol'):
            folder_name = folder_name[:-9]  # 移除 '_protocol'
        
        # 将 snake_case 转换为 PascalCase
        words = folder_name.split('_')
        device_type = ''.join(word.capitalize() for word in words)
        
        return device_type

    def _import_parser_class(self, folder_name: str, device_type: str) -> Optional[type]:
        """
        导入指定设备的协议解析器类。
        规则：假设类名为 {DeviceType}ProtocolParser
        """
        try:
            # 构建模块路径
            module_path = f"deepwin.services.hardware_communication.device_protocols.{folder_name}.{folder_name.replace('_protocol', '_parser')}"
            
            # 导入模块
            module = importlib.import_module(module_path)
            
            # 构建类名
            class_name = f"{device_type}ProtocolParser"
            
            # 获取类
            parser_class = getattr(module, class_name, None)
            
            if parser_class is None:
                self.logger.warning(f"模块 {module_path} 中未找到类 {class_name}")
                return None
            
            # 验证类是否继承自 BaseProtocolParser
            if not issubclass(parser_class, BaseProtocolParser):
                self.logger.warning(f"类 {class_name} 未继承自 BaseProtocolParser")
                return None
            
            return parser_class
            
        except ImportError as e:
            self.logger.warning(f"导入模块失败 {folder_name}: {e}")
            return None
        except AttributeError as e:
            self.logger.warning(f"获取类失败 {folder_name}: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"导入设备 {device_type} 的协议解析器时发生未知错误: {e}")
            return None

    def _get_device_type_from_id(self, device_id: str) -> Optional[str]:
        """
        根据设备ID确定设备类型。
        """
        # 遍历已注册的设备类型，查找匹配的前缀
        for device_type in self._device_parsers.keys():
            if device_id.startswith(device_type):
                return device_type
        
        return None

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
        self.logger.debug(f"收到设备 '{device_id}' 的低层数据")
        
        # 根据 device_id 确定设备类型
        device_type = self._get_device_type_from_id(device_id)
        if not device_type:
            error_msg = f"未找到设备ID '{device_id}' 对应的协议解析器"
            self.logger.warning(error_msg)
            self.protocol_conversion_error.emit(device_id, error_msg)
            return

        device_parser = self._device_parsers.get(device_type)
        if not device_parser:
            error_msg = f"设备类型 '{device_type}' 的协议解析器未注册"
            self.logger.error(error_msg)
            self.protocol_conversion_error.emit(device_id, error_msg)
            return

        try:
            # 调用具体设备解析器的方法进行解析
            semantic_data = device_parser.parse_input_data(device_id, low_level_data)
            self.logger.debug(f"设备 '{device_id}' 语义数据解析完成")
            self.device_semantic_data_ready.emit(device_id, semantic_data)
        except Exception as e:
            error_msg = f"解析设备 '{device_id}' 协议数据失败: {e}"
            self.logger.error(error_msg)
            self.protocol_conversion_error.emit(device_id, error_msg)

    def generate_low_level_command(self, device_id: str, abstract_command_name: str, params: Dict[str, Any]) -> Union[bytes, str]:
        """
        将应用逻辑层的高级抽象命令（带参数字典）转发给对应的具体协议解析器，转换为底层协议可发送的命令。
        这是推荐的接口，避免了不必要的参数转换。
        :param device_id: 目标设备的唯一标识符。
        :param abstract_command_name: 抽象命令的名称 (如 "move_joint_angles", "set_motor_rpm")。
        :param params: 抽象命令的参数字典，键为参数名，值为参数值。
        :return: 转换后的底层命令 (bytes 或 str)。
        :raises ValueError: 如果设备或命令不被支持。
        """
        self.logger.debug(f"生成设备 '{device_id}' 的底层命令: {abstract_command_name} 参数: {params}")
        
        # 根据 device_id 确定设备类型
        device_type = self._get_device_type_from_id(device_id)
        if not device_type:
            raise ValueError(f"未找到设备ID '{device_id}' 对应的命令生成器")

        device_parser = self._device_parsers.get(device_type)
        if not device_parser:
            raise ValueError(f"设备类型 '{device_type}' 的命令生成器未注册")

        try:
            # 调用具体设备解析器的方法生成命令（使用新的字典参数接口）
            low_level_command = device_parser.generate_output_command(abstract_command_name, params)
            
            self.logger.debug(f"已生成设备 '{device_id}' 的底层命令")
            return low_level_command
        except Exception as e:
            raise ValueError(f"生成设备 '{device_id}' 命令 '{abstract_command_name}' 失败: {e}")

    def get_registered_devices(self) -> List[str]:
        """
        获取已注册的设备类型列表。
        :return: 已注册的设备类型列表。
        """
        return list(self._device_parsers.keys())

    def cleanup(self):
        """
        清理协议解析器管理器及其管理的具体协议解析器资源。
        """
        self.logger.info("开始清理设备协议解析器管理器")
        for device_type, parser in self._device_parsers.items():
            try:
                parser.cleanup()
                self.logger.debug(f"已清理设备 '{device_type}' 的协议解析器")
            except Exception as e:
                self.logger.warning(f"清理设备 '{device_type}' 的协议解析器时发生错误: {e}")
        
        self._device_parsers.clear()
        self._device_type_mapping.clear()
        self.logger.info("设备协议解析器管理器清理完成")

