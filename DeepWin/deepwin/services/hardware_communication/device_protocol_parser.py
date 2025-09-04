# src/services/hardware_communication/device_protocol_parser.py
# 设备协议解析器 (作为管理器和调度器)

import os
import importlib
import re
from typing import Dict, Any, Optional, Union, List
from PySide6.QtCore import QObject, Signal, Slot

from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager

# 导入基础协议解析器
from deepwin.services.hardware_communication.device_protocols.base_protocol_parser import BaseProtocolParser


class DeviceProtocolParser(QObject):
    """
    协议管理层 - 统一的协议转换和路由中心。
    
    核心职责：
    1. 命令 → CAN帧：将抽象命令转换为CAN帧格式
    2. 命令 → 串口帧：将抽象命令直接转换为串口帧（跳过CAN层）
    3. CAN帧 → 信号字典：将CAN帧解析为信号字典
    4. 串口帧 → 信号字典：将串口帧解析为信号字典
    
    设计原则：
    - 协议管理层代码尽可能不动，新增设备只需在设备协议子层添加代码
    - 支持CAN协议和串口协议的统一处理
    - 提供灵活的协议路由和转换机制
    """
    # 输出信号
    device_semantic_data_ready = Signal(str, dict)  # 设备语义数据就绪
    can_frame_ready = Signal(int, bytes, bool)      # CAN帧就绪 (arbitration_id, data, is_extended_id)
    serial_frame_ready = Signal(bytes)              # 串口帧就绪 (data)
    
    # 错误信号
    protocol_conversion_error = Signal(str, str)    # 协议转换错误 (device_id, error_msg)

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

    # ==================== 协议管理层的4个核心任务 ====================
    
    @Slot(str, str, dict, result=object)
    def convert_command_to_can_frame(self, device_id: str, command_name: str, params: Dict[str, Any]) -> Union[Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]]]:
        """
        核心任务1：将抽象命令转换为CAN帧格式
        支持单帧和多帧命令
        :param device_id: 设备ID
        :param command_name: 命令名称
        :param params: 命令参数
        """
        try:
            self.logger.debug(f"协议管理层: 将命令 '{command_name}' 转换为CAN帧 (设备: {device_id})")
            
            # 获取设备协议解析器
            device_type = self._get_device_type_from_id(device_id)
            if not device_type:
                raise ValueError(f"未找到设备ID '{device_id}' 对应的协议解析器")
            
            device_parser = self._device_parsers.get(device_type)
            if not device_parser:
                raise ValueError(f"设备类型 '{device_type}' 的协议解析器未注册")
            
            # 调用设备特定的命令转换方法
            can_frame_data = device_parser.convert_command_to_can_frame(command_name, params)
            
            if can_frame_data:
                # 检查是否为多帧命令
                if isinstance(can_frame_data, list):
                    # 多帧命令：发送所有帧并返回第一帧
                    self.logger.info(f"协议管理层: 命令 '{command_name}' 已转换为 {len(can_frame_data)} 个CAN帧")
                    for i, frame in enumerate(can_frame_data):
                        arbitration_id = frame.get('arbitration_id')
                        data = frame.get('data')
                        is_extended_id = frame.get('is_extended_id', True)
                        self.logger.debug(f"协议管理层: 发送第 {i+1} 帧 CAN ID=0x{arbitration_id:X}")
                        self.can_frame_ready.emit(arbitration_id, data, is_extended_id)
                    return can_frame_data  # 返回完整的帧列表
                else:
                    # 单帧命令
                    arbitration_id = can_frame_data.get('arbitration_id')
                    data = can_frame_data.get('data')
                    is_extended_id = can_frame_data.get('is_extended_id', True)
                    
                    self.logger.info(f"协议管理层: 命令 '{command_name}' 已转换为CAN帧 ID=0x{arbitration_id:X}")
                    self.can_frame_ready.emit(arbitration_id, data, is_extended_id)
                    
                    # 返回CAN帧数据
                    return can_frame_data
            else:
                raise ValueError(f"设备 '{device_id}' 不支持命令 '{command_name}' 的CAN帧转换")
                
        except Exception as e:
            error_msg = f"转换命令 '{command_name}' 为CAN帧失败: {e}"
            self.logger.error(f"协议管理层: {error_msg}")
            self.protocol_conversion_error.emit(device_id, error_msg)
            return None
    
    @Slot(str, str, dict)
    def convert_command_to_serial_frame(self, device_id: str, command_name: str, params: Dict[str, Any]):
        """
        核心任务2：将抽象命令直接转换为串口帧（跳过CAN层）
        :param device_id: 设备ID
        :param command_name: 命令名称
        :param params: 命令参数
        """
        try:
            self.logger.debug(f"协议管理层: 将命令 '{command_name}' 转换为串口帧 (设备: {device_id})")
            
            # 获取设备协议解析器
            device_type = self._get_device_type_from_id(device_id)
            if not device_type:
                raise ValueError(f"未找到设备ID '{device_id}' 对应的协议解析器")
            
            device_parser = self._device_parsers.get(device_type)
            if not device_parser:
                raise ValueError(f"设备类型 '{device_type}' 的协议解析器未注册")
            
            # 调用设备特定的串口帧转换方法
            serial_frame_data = device_parser.convert_command_to_serial_frame(command_name, params)
            
            if serial_frame_data:
                self.logger.info(f"协议管理层: 命令 '{command_name}' 已转换为串口帧")
                self.serial_frame_ready.emit(serial_frame_data)
            else:
                raise ValueError(f"设备 '{device_id}' 不支持命令 '{command_name}' 的串口帧转换")
                
        except Exception as e:
            error_msg = f"转换命令 '{command_name}' 为串口帧失败: {e}"
            self.logger.error(f"协议管理层: {error_msg}")
            self.protocol_conversion_error.emit(device_id, error_msg)
    
    @Slot(str, int, bytes, bool)
    def parse_can_frame_to_signals(self, device_id: str, arbitration_id: int, data: bytes, is_extended_id: bool=True):
        """
        核心任务3：将CAN帧解析为信号字典
        :param device_id: 设备ID
        :param arbitration_id: CAN仲裁ID
        :param data: CAN数据
        :param is_extended_id: 是否为扩展ID
        """
        try:
            self.logger.debug(f"协议管理层: 解析CAN帧 ID=0x{arbitration_id:X} (设备: {device_id})")
            
            # 获取设备协议解析器
            device_type = self._get_device_type_from_id(device_id)
            if not device_type:
                raise ValueError(f"未找到设备ID '{device_id}' 对应的协议解析器")
            
            device_parser = self._device_parsers.get(device_type)
            if not device_parser:
                raise ValueError(f"设备类型 '{device_type}' 的协议解析器未注册")
            
            # 构建CAN帧数据字典
            can_frame_data = {
                'arbitration_id': arbitration_id,
                'data': data,
                'is_extended_id': is_extended_id,
                'frame_type': 'can'
            }
            
            # 调用设备特定的CAN帧解析方法
            semantic_data = device_parser.parse_can_frame_to_signals(can_frame_data)
            
            if semantic_data:
                semantic_data['device_id'] = device_id
                semantic_data['device_type'] = device_type
                self.logger.info(f"协议管理层: CAN帧 ID=0x{arbitration_id:X} 已解析为信号字典")
                self.device_semantic_data_ready.emit(device_id, semantic_data)
            else:
                self.logger.warning(f"协议管理层: 设备 '{device_id}' 无法解析CAN帧 ID=0x{arbitration_id:X}")
                
        except Exception as e:
            error_msg = f"解析CAN帧 ID=0x{arbitration_id:X} 失败: {e}"
            self.logger.error(f"协议管理层: {error_msg}")
            self.protocol_conversion_error.emit(device_id, error_msg)
    
    def parse_serial_frame_to_signals(self, device_id: str, data: bytes) -> Optional[Dict[str, Any]]:
        """
        核心任务4：将串口帧解析为信号字典
        :param device_id: 设备ID
        :param data: 串口数据
        :return: 信号字典，失败时返回None
        """
        try:
            self.logger.debug(f"协议管理层: 解析串口帧 (设备: {device_id}, 数据: {data.hex()})")
            
            # 获取设备协议解析器
            device_type = self._get_device_type_from_id(device_id)
            if not device_type:
                raise ValueError(f"未找到设备ID '{device_id}' 对应的协议解析器")
            
            device_parser = self._device_parsers.get(device_type)
            if not device_parser:
                raise ValueError(f"设备类型 '{device_type}' 的协议解析器未注册")
            
            # 构建串口帧数据字典
            serial_frame_data = {
                'data': data,
                'frame_type': 'serial'
            }
            
            # 调用设备特定的串口帧解析方法
            semantic_data = device_parser.parse_serial_frame_to_signals(serial_frame_data)
            
            if semantic_data:
                semantic_data['device_id'] = device_id
                semantic_data['device_type'] = device_type
                self.logger.info(f"协议管理层: 串口帧已解析为信号字典")
                # 发送信号（保持向后兼容）
                self.device_semantic_data_ready.emit(device_id, semantic_data)
                return semantic_data
            else:
                self.logger.warning(f"协议管理层: 设备 '{device_id}' 无法解析串口帧")
                return None
                
        except Exception as e:
            error_msg = f"解析串口帧失败: {e}"
            self.logger.error(f"协议管理层: {error_msg}")
            self.protocol_conversion_error.emit(device_id, error_msg)
            return None
    
    # ==================== 兼容性方法（保持向后兼容） ====================
    
    @Slot(str, dict)
    def parse_low_level_data(self, device_id: str, low_level_data: Dict[str, Any]):
        """
        将低层次解析数据转换为业务语义数据。
        
        支持两种数据格式：
        1. 带 frame_type 的新格式：根据 frame_type 路由到对应的解析方法
        2. 旧格式：直接调用设备解析器的 parse_input_data 方法（向后兼容）
        
        :param device_id: 设备的唯一标识符
        :param low_level_data: 低层次数据字典，可能包含：
            - frame_type: 'can' 或 'serial'（新格式）
            - arbitration_id, data, is_extended_id（CAN帧数据）
            - data（串口帧数据）
            - 或其他旧格式数据
        """
        # 根据数据类型路由到对应的解析方法
        if low_level_data.get('frame_type') == 'can':
            arbitration_id = low_level_data.get('arbitration_id')
            data = low_level_data.get('data')
            is_extended_id = low_level_data.get('is_extended_id', True)
            self.parse_can_frame_to_signals(device_id, arbitration_id, data, is_extended_id)
        elif low_level_data.get('frame_type') == 'serial':
            data = low_level_data.get('data')
            self.parse_serial_frame_to_signals(device_id, data)
        else:
            # 兼容旧的调用方式
            self._legacy_parse_low_level_data(device_id, low_level_data)
    
    def _legacy_parse_low_level_data(self, device_id: str, low_level_data: Dict[str, Any]):
        """
        旧的解析方法（保持向后兼容）
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
        兼容性方法：生成底层命令（保持向后兼容）
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

