# deepweb/app_logic/device_logic_manager/manager.py
# 设备逻辑管理器核心实现
# Web端版本，不依赖PySide6

import os
import importlib
from typing import Dict, Any, Optional, List

from ...data_management.log_manager import LogManager
from ...config.config_manager import ConfigManager
from .devices.base_device import BaseDevice

# 直接从具体模块导入，避免循环导入


class DeviceLogicManager:
    """
    DeepWeb 应用程序的设备逻辑管理器。
    负责处理与 DeepDevice 设备（如 DeepArm 机械臂和 DeepToy 玩具控制器）相关的复杂业务逻辑。
    
    Web端版本，不依赖PySide6的信号槽机制。
    信号功能通过回调函数实现。

    职责包括：
    1. 接收来自服务层已解析的业务语义数据，并更新设备状态模型。
    2. 基于设备状态实时监控，进行异常检测和告警。
    3. 管理 DeepArm 机械臂的示教轨迹录制、存储和播放。（目前暂时不实现）
    4. 通过回调函数请求 Coordinator 发送抽象控制指令到底层。
    5. 通过回调函数通知 Coordinator 设备状态更新、控制响应或错误。
    
    支持混合架构：
    - 方案3：直接访问核心设备（便捷访问）
    - 方案2：通用能力管理（动态设备）
    """
    
    # Web端：使用回调函数替代信号
    # 这些回调函数由 Coordinator 在初始化时设置
    def __init__(self, log_manager: LogManager, config_manager: ConfigManager):
        """
        初始化设备逻辑管理器
        
        Args:
            log_manager: 日志管理器
            config_manager: 配置管理器
        """
        self.logger = log_manager.get_logger(__name__)
        self.config_manager = config_manager
        # 回调函数（由 Coordinator 设置）
        self._on_device_status_updated = None
        self._on_device_command_response = None
        self._on_device_error = None
        self._on_send_device_abstract_command_requested = None
        
        # 示教轨迹相关回调（目前暂时不使用）
        self._on_teaching_started = None
        self._on_teaching_stopped = None
        self._on_trajectory_playback_started = None
        self._on_trajectory_playback_finished = None
        self._on_trajectory_playback_error = None
        
        # DeepMotor 轨迹执行相关回调
        self._on_trajectory_execution_progress_updated = None
        self._on_trajectory_execution_finished = None
        self._on_trajectory_execution_error = None
        
        # 示教轨迹实时更新回调
        self._on_teaching_trajectory_updated = None
        
        # 维护当前连接的设备实例 (示例：使用字典存储设备ID -> 设备逻辑实例)
        self.managed_devices: Dict[str, BaseDevice] = {}
        
        # 存储最后的命令信息，用于UI显示
        self._last_command_info: Optional[Dict[str, Any]] = None
        
        # 存储设备类型到设备类的映射
        self._device_classes: Dict[str, type] = {}
        
        # === 方案3：核心设备直接访问（延迟初始化）===
        self._deep_motor = None
        self._deep_arm = None
        self._deep_toy = None
        
        # === 方案2：动态设备管理 ===
        self._dynamic_devices = {}  # 动态创建的设备
        
        # 自动发现和注册设备逻辑类
        try:
            self._auto_discover_and_register_devices()
        except Exception as e:
            self.logger.error(f"设备注册过程中发生异常: {e}")
            import traceback
            self.logger.error(f"设备注册异常详情: {traceback.format_exc()}")
        self.logger.info("设备逻辑管理器初始化完成")
    
    def _on_device_status_updated_callback(self, device_id: str, state_dict: Dict[str, Any]):
        """设备状态更新回调函数"""
        if self._on_device_status_updated:
            self._on_device_status_updated(device_id, state_dict)
    
    def _on_device_error_callback(self, device_id: str, error_message: str):
        """设备错误回调函数"""
        if self._on_device_error:
            self._on_device_error(error_message)
    
    def _on_send_device_abstract_command_requested_callback(self, device_id: str, command: str, args: List[Any]):
        """设备命令请求回调函数"""
        if self._on_send_device_abstract_command_requested:
            # 将args转换为dict格式（如果args是list）
            if isinstance(args, list):
                params = args[0] if args else {}
            else:
                params = args
            self._on_send_device_abstract_command_requested(device_id, command, params)
    
    def set_last_command_info(self, command_info: Dict[str, Any]):
        """
        设置最后的命令信息
        :param command_info: 命令信息字典
        """
        self._last_command_info = command_info
        self.logger.debug(f"DeviceLogicManager: 设置命令信息: {command_info}")
    
    def get_last_command_info(self) -> Optional[Dict[str, Any]]:
        """
        获取最后的命令信息
        :return: 命令信息字典，如果没有则返回None
        """
        return self._last_command_info

    def _auto_discover_and_register_devices(self):
        """
        自动发现并注册设备逻辑类。
        根据 devices 目录下的子文件夹名称自动提取设备类型和设备类。
        """
        self.logger.info("开始自动发现设备逻辑类...")
        
        # 获取 devices 目录的绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        devices_dir = os.path.join(current_dir, "devices")
        
        self.logger.info(f"设备目录路径: {devices_dir}")
        
        if not os.path.exists(devices_dir):
            self.logger.error(f"设备目录不存在: {devices_dir}")
            return
        
        # 获取目录内容
        try:
            items = os.listdir(devices_dir)
            self.logger.info(f"设备目录内容: {items}")
        except Exception as e:
            self.logger.error(f"无法读取设备目录: {e}")
            return
        
        # 遍历 devices 目录下的子文件夹
        for item in items:
            item_path = os.path.join(devices_dir, item)
            
            # 只处理目录，跳过文件
            if not os.path.isdir(item_path):
                self.logger.debug(f"跳过文件: {item}")
                continue
                
            # 跳过 __pycache__ 等特殊目录
            if item.startswith('__') or item.startswith('.'):
                self.logger.debug(f"跳过特殊目录: {item}")
                continue
            
            self.logger.info(f"处理设备目录: {item}")
            
            # 根据文件夹名称提取设备类型
            device_type = self._extract_device_type_from_folder_name(item)
            if not device_type:
                self.logger.warning(f"无法从文件夹名称 '{item}' 提取设备类型，跳过")
                continue
            
            self.logger.info(f"提取的设备类型: {device_type}")
            
            # 尝试导入对应的设备逻辑类
            device_class = self._import_device_class(item, device_type)
            if not device_class:
                self.logger.warning(f"无法导入设备 '{device_type}' 的逻辑类，跳过")
                continue
            
            # 注册设备类
            self._device_classes[device_type] = device_class
            self.logger.info(f"成功注册设备逻辑类: {device_type} -> {device_class.__name__}")
        
        registered_devices = list(self._device_classes.keys())
        self.logger.info(f"设备逻辑类注册完成，共注册 {len(registered_devices)} 个设备类型: {registered_devices}")
        
        if not registered_devices:
            self.logger.error("没有成功注册任何设备类型！")

    def _extract_device_type_from_folder_name(self, folder_name: str) -> Optional[str]:
        """
        从文件夹名称提取设备类型。
        规则：将 snake_case 转换为 PascalCase，例如：
        - deep_motor -> DeepMotor
        - deep_arm -> DeepArm
        - my_device -> MyDevice
        """
        # 将 snake_case 转换为 PascalCase
        words = folder_name.split('_')
        device_type = ''.join(word.capitalize() for word in words)
        
        return device_type

    def _import_device_class(self, folder_name: str, device_type: str) -> Optional[type]:
        """
        导入指定设备的逻辑类。
        规则：假设类名为 {DeviceType}
        """
        try:
            # 构建模块路径
            module_path = f"deepweb.app_logic.device_logic_manager.devices.{folder_name}.{folder_name}"
            self.logger.debug(f"尝试导入模块: {module_path}")
            
            # 导入模块
            module = importlib.import_module(module_path)
            self.logger.debug(f"成功导入模块: {module_path}")
            
            # 构建类名
            class_name = device_type
            self.logger.debug(f"查找类: {class_name}")
            
            # 获取类
            device_class = getattr(module, class_name, None)
            
            if device_class is None:
                self.logger.warning(f"模块 {module_path} 中未找到类 {class_name}")
                # 列出模块中可用的类
                available_classes = [name for name in dir(module) if not name.startswith('_')]
                self.logger.debug(f"模块中可用的类: {available_classes}")
                return None
            
            self.logger.debug(f"找到类: {device_class}")
            
            # 验证类是否继承自 BaseDevice
            if not issubclass(device_class, BaseDevice):
                self.logger.warning(f"类 {class_name} 未继承自 BaseDevice")
                return None
            
            self.logger.debug(f"类 {class_name} 验证通过")
            return device_class
            
        except ImportError as e:
            self.logger.warning(f"导入模块失败 {folder_name}: {e}")
            import traceback
            self.logger.debug(f"导入错误详情: {traceback.format_exc()}")
            return None
        except AttributeError as e:
            self.logger.warning(f"获取类失败 {folder_name}: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"导入设备 {device_type} 的逻辑类时发生未知错误: {e}")
            import traceback
            self.logger.debug(f"未知错误详情: {traceback.format_exc()}")
            return None

    def _get_device_type_from_id(self, device_id: str) -> Optional[str]:
        """
        根据设备ID确定设备类型。
        """
        # 调试信息：显示已注册的设备类型
        self.logger.debug(f"尝试识别设备ID: {device_id}")
        self.logger.debug(f"已注册的设备类型: {list(self._device_classes.keys())}")
        
        # 遍历已注册的设备类型，查找匹配的前缀
        for device_type in self._device_classes.keys():
            if device_id.startswith(device_type):
                self.logger.debug(f"找到匹配的设备类型: {device_type}")
                return device_type
        
        self.logger.error(f"无法找到匹配的设备类型，设备ID: {device_id}, 已注册类型: {list(self._device_classes.keys())}")
        return None

    def _get_or_create_device_instance(self, device_id: str) -> Optional[BaseDevice]:
        """
        获取或创建设备逻辑实例。
        :param device_id: 设备的唯一标识符。
        :return: 设备逻辑实例，如果无法创建则返回 None。
        """
        if device_id not in self.managed_devices:
            # 根据设备ID前缀确定设备类型
            device_type = self._get_device_type_from_id(device_id)
            if not device_type:
                self.logger.error(f"无法识别的设备类型或 ID 前缀: {device_id}")
                return None
            
            # 获取对应的设备类
            device_class = self._device_classes.get(device_type)
            if not device_class:
                self.logger.error(f"设备类型 '{device_type}' 的逻辑类未注册")
                return None
            
            try:
                # 实例化设备
                if device_type == "DeepMotor":
                    # DeepMotor 需要额外的 config_manager 参数
                    device_instance = device_class(device_id, self.logger_instance, self.config_manager)
                else:
                    # 其他设备只需要基本的参数
                    device_instance = device_class(device_id, self.logger_instance)
                
                self.managed_devices[device_id] = device_instance
                
                # Web端：使用回调函数替代信号连接
                # 设置设备状态更新回调
                if hasattr(device_instance, '_on_states_updated'):
                    device_instance._on_states_updated = self._on_device_status_updated_callback
                
                # 设置设备错误回调
                if hasattr(device_instance, '_on_error'):
                    device_instance._on_error = self._on_device_error_callback
                
                # 设置设备命令请求回调
                if hasattr(device_instance, '_on_command_to_coordinator'):
                    device_instance._on_command_to_coordinator = self._on_send_device_abstract_command_requested_callback
                
                self.logger.info(f"成功创建设备实例: {device_id} ({device_type})")
                
            except Exception as e:
                self.logger.error(f"创建设备 '{device_id}' 实例失败: {e}")
                return None

        return self.managed_devices[device_id]

    # === 方案3：便捷访问接口（直接访问核心设备）===
    @property
    def deep_motor(self):
        """
        便捷访问：self.device_logic_manager.deep_motor
        延迟初始化，首次访问时创建实例
        """
        if self._deep_motor is None:
            self._deep_motor = self._get_or_create_device_instance("DeepMotor")
        return self._deep_motor
    
    @property
    def deep_arm(self):
        """
        便捷访问：self.device_logic_manager.deep_arm
        延迟初始化，首次访问时创建实例
        """
        if self._deep_arm is None:
            self._deep_arm = self._get_or_create_device_instance("DeepArm")
        return self._deep_arm
    
    @property
    def deep_toy(self):
        """
        便捷访问：self.device_logic_manager.deep_toy
        延迟初始化，首次访问时创建实例
        """
        if self._deep_toy is None:
            self._deep_toy = self._get_or_create_device_instance("DeepToy")
        return self._deep_toy

    # === 方案2：通用管理接口 ===
    def get_device(self, device_id: str):
        """
        通用获取：self.device_logic_manager.get_device("custom_device_001")
        适用于动态设备或非核心设备
        """
        return self._get_or_create_device_instance(device_id)
    
    def call_device_capability(self, device_id: str, capability_name: str, method_name: str, *args, **kwargs):
        """
        通用能力调用接口
        :param device_id: 设备ID
        :param capability_name: 能力名称 (如 'teaching', 'custom_feature')
        :param method_name: 方法名称 (如 'start_teaching', 'execute_custom')
        :param args: 位置参数
        :param kwargs: 关键字参数
        """
        device = self._get_or_create_device_instance(device_id)
        if not device:
            raise ValueError(f"设备 {device_id} 不存在")
        
        if not device.has_capability(capability_name):
            raise ValueError(f"设备 {device_id} 不支持 {capability_name} 能力")
        
        return device.call_capability_method(capability_name, method_name, *args, **kwargs)
    
    def get_device_capabilities(self, device_id: str) -> Dict[str, List[str]]:
        """
        获取设备支持的所有能力和方法
        :param device_id: 设备ID
        :return: 能力名称到方法列表的映射
        """
        device = self._get_or_create_device_instance(device_id)
        if not device:
            return {}
        
        return device.get_all_capabilities()

    def send_command_to_device(self, device_id: str, abstract_command: str) -> str:
        """
        接收来自 Coordinator 的抽象控制指令，并将其转发给对应的设备逻辑实例处理。
        设备逻辑实例将通过信号请求 Coordinator 发送到服务层进行底层协议转换和发送。
        :param device_id: 目标设备的唯一标识符。
        :param abstract_command: 抽象的控制指令字符串，如 "move_to_point(100, 200, 300)"。
        :return: 模拟的设备响应。
        """
        self.logger.info(f"收到抽象指令 '{abstract_command}' for device '{device_id}'")
        device_instance = self._get_or_create_device_instance(device_id)
        if not device_instance:
            error_msg = f"无法找到或创建设备实例 '{device_id}' 来发送命令"
            if self._on_device_error:
                self._on_device_error(error_msg)
            raise ValueError(error_msg)
        try:
            # 设备的逻辑实例负责将抽象命令映射到实际的底层命令请求
            command, params = device_instance.command_parser.parse_command_string(abstract_command)
            if self._on_send_device_abstract_command_requested:
                self._on_send_device_abstract_command_requested(device_id, command, params)
            if self._on_device_command_response:
                self._on_device_command_response(f"命令请求已发送至设备 '{device_id}' 的逻辑实例")
            return "Command request sent to device logic instance."
        except Exception as e:
            error_msg = f"设备 '{device_id}' 处理抽象命令 '{abstract_command}' 失败: {e}"
            self.logger.error(error_msg)
            if self._on_device_error:
                self._on_device_error(error_msg)
            raise

    # Web端：接收来自 DeviceProtocolParser 的业务语义数据（不使用@Slot装饰器）
    def handle_device_semantic_data(self, device_id: str, parsed_semantic_data: Dict[str, Any]):
        """
        处理原始设备数据的解析和状态模型更新。
        接收来自 DeviceProtocolParser（服务层）已解析的业务语义数据，并更新设备状态。
        :param device_id: 发送数据的设备ID。
        :param parsed_semantic_data: 已解析的业务语义数据字典。
        """
        self.logger.debug(f"收到设备 '{device_id}' 的语义数据")
        device_instance = self._get_or_create_device_instance(device_id)
        if not device_instance:
            error_msg = f"无法找到或创建设备实例 '{device_id}' 来处理语义数据"
            if self._on_device_error:
                self._on_device_error(error_msg)
            return

        try:
            # 设备逻辑实例负责更新自身的内部状态模型
            device_instance.update_state_from_semantic_data(parsed_semantic_data)
            
            # 实时更新、异常检测和告警 (由设备逻辑实例自身处理)
            device_instance.check_anomaly() # 假设设备实例内部会发出错误信号

            # 通知 Coordinator 设备状态已更新
            if self._on_device_status_updated:
                self._on_device_status_updated(
                    device_id,
                    device_instance.get_current_state().to_dict() # 获取最新状态字典
                )
            self.logger.debug(f"设备 '{device_id}' 状态已更新")

        except Exception as e:
            error_msg = f"处理设备 '{device_id}' 语义数据失败: {e}"
            self.logger.error(error_msg)
            if self._on_device_error:
                self._on_device_error(error_msg)

    def get_registered_device_types(self) -> List[str]:
        """
        获取已注册的设备类型列表。
        :return: 已注册的设备类型列表。
        """
        return list(self._device_classes.keys())

    def cleanup(self):
        """
        清理设备逻辑管理器占用的资源。
        在应用程序关闭时调用。
        """
        self.logger.info("开始清理设备逻辑管理器")
        for device_id, instance in self.managed_devices.items():
            try:
                instance.cleanup() # 清理各个设备实例
                self.logger.debug(f"已清理设备 '{device_id}' 的实例")
            except Exception as e:
                self.logger.warning(f"清理设备 '{device_id}' 的实例时发生错误: {e}")
        
        self.managed_devices.clear()
        self._device_classes.clear()
        
        # 清理核心设备引用
        self._deep_motor = None
        self._deep_arm = None
        self._deep_toy = None
        
        self.logger.info("设备逻辑管理器清理完成")

    # === 核心管理功能 ===
    # 只保留设备管理和通用能力调用，删除所有具体的业务方法