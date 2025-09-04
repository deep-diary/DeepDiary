# deepwin/app_logic/device_logic_manager/manager.py
# 设备逻辑管理器核心实现

import os
import importlib
from PySide6.QtCore import QObject, Signal, Slot
from typing import Dict, Any, Optional, List

from ...data_management.log_manager import LogManager
from ...config.config_manager import ConfigManager
from .devices.base_device import BaseDevice

# 直接从具体模块导入，避免循环导入


class DeviceLogicManager(QObject):
    """
    DeepWin 应用程序的设备逻辑管理器。
    负责处理与 DeepDevice 设备（如 DeepArm 机械臂和 DeepToy 玩具控制器）相关的复杂业务逻辑。

    职责包括：
    1. 接收来自服务层已解析的业务语义数据，并更新设备状态模型。
    2. 基于设备状态实时监控，进行异常检测和告警。
    3. 管理 DeepArm 机械臂的示教轨迹录制、存储和播放。（目前暂时不实现）
    4. 通过信号请求 Coordinator 发送抽象控制指令到底层。
    5. 通过信号通知 Coordinator 设备状态更新、控制响应或错误。
    
    支持混合架构：
    - 方案3：直接访问核心设备（便捷访问）
    - 方案2：通用能力管理（动态设备）
    """

    # 定义设备逻辑管理器可以向 Coordinator 发射的信号
    device_status_updated = Signal(str, dict)    # 设备状态实时更新，参数为设备ID和状态数据 (dict)
    device_command_response = Signal(str)   # 设备控制命令的响应 (str)
    device_error = Signal(str)              # 设备相关操作发生错误 (str)

    # 新增信号：请求 Coordinator 发送抽象命令
    send_device_abstract_command_requested = Signal(str, str, dict) # (device_id, abstract_command_name, args)

    # DeepArm 示教轨迹相关信号 (目前暂时不使用)
    teaching_started = Signal(str)
    teaching_stopped = Signal(str, list)
    trajectory_playback_started = Signal(str, str)
    trajectory_playback_finished = Signal(str, str)
    trajectory_playback_error = Signal(str, str)

    # 新增：DeepMotor 轨迹执行相关信号
    trajectory_execution_progress_updated = Signal(str, dict)  # (device_id, progress_data)
    trajectory_execution_finished = Signal(str, str)  # (device_id, trajectory_name)
    trajectory_execution_error = Signal(str, str)  # (device_id, error_message)

    # 新增：示教轨迹实时更新信号
    teaching_trajectory_updated = Signal(str, list, list)  # 示教轨迹实时更新

    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, parent: Optional[QObject] = None):
        """
        初始化设备逻辑管理器。
        :param log_manager: 全局日志管理器实例。
        :param parent: QObject 父对象。
        """
        super().__init__(parent)
        self.logger_instance = log_manager
        self.config_manager = config_manager
        self.logger = log_manager.get_logger(__name__)
        
        # 维护当前连接的设备实例 (示例：使用字典存储设备ID -> 设备逻辑实例)
        self.managed_devices: Dict[str, BaseDevice] = {}
        
        # 存储设备类型到设备类的映射
        self._device_classes: Dict[str, type] = {}
        
        # === 方案3：核心设备直接访问（延迟初始化）===
        self._deep_motor = None
        self._deep_arm = None
        self._deep_toy = None
        
        # === 方案2：动态设备管理 ===
        self._dynamic_devices = {}  # 动态创建的设备
        
        # 自动发现和注册设备逻辑类
        self._auto_discover_and_register_devices()

    def _auto_discover_and_register_devices(self):
        """
        自动发现并注册设备逻辑类。
        根据 devices 目录下的子文件夹名称自动提取设备类型和设备类。
        """
        self.logger.info("开始自动发现设备逻辑类...")
        
        # 获取 devices 目录的绝对路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        devices_dir = os.path.join(current_dir, "devices")
        
        if not os.path.exists(devices_dir):
            self.logger.error(f"设备目录不存在: {devices_dir}")
            return
        
        # 遍历 devices 目录下的子文件夹
        for item in os.listdir(devices_dir):
            item_path = os.path.join(devices_dir, item)
            
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
            module_path = f"deepwin.app_logic.device_logic_manager.devices.{folder_name}.{folder_name}"
            
            # 导入模块
            module = importlib.import_module(module_path)
            
            # 构建类名
            class_name = device_type
            
            # 获取类
            device_class = getattr(module, class_name, None)
            
            if device_class is None:
                self.logger.warning(f"模块 {module_path} 中未找到类 {class_name}")
                return None
            
            # 验证类是否继承自 BaseDevice
            if not issubclass(device_class, BaseDevice):
                self.logger.warning(f"类 {class_name} 未继承自 BaseDevice")
                return None
            
            return device_class
            
        except ImportError as e:
            self.logger.warning(f"导入模块失败 {folder_name}: {e}")
            return None
        except AttributeError as e:
            self.logger.warning(f"获取类失败 {folder_name}: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"导入设备 {device_type} 的逻辑类时发生未知错误: {e}")
            return None

    def _get_device_type_from_id(self, device_id: str) -> Optional[str]:
        """
        根据设备ID确定设备类型。
        """
        # 遍历已注册的设备类型，查找匹配的前缀
        for device_type in self._device_classes.keys():
            if device_id.startswith(device_type):
                return device_type
        
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
                
                # 绑定设备状态更新信号
                device_instance.device_states_updated.connect(self.device_status_updated)
                
                # 绑定设备向协调器发送命令的信号
                if hasattr(device_instance, 'send_command_request'):
                    device_instance.send_command_request.connect(self.send_device_abstract_command_requested)
                elif hasattr(device_instance, 'command_to_coordinator'):
                    # 兼容旧版本，使用 command_to_coordinator 信号
                    device_instance.command_to_coordinator.connect(self.send_device_abstract_command_requested)
                
                # 绑定轨迹执行相关信号（如果设备支持）
                if hasattr(device_instance, 'trajectory_execution_progress_updated'):
                    device_instance.trajectory_execution_progress_updated.connect(self.trajectory_execution_progress_updated)
                if hasattr(device_instance, 'trajectory_execution_finished'):
                    device_instance.trajectory_execution_finished.connect(self.trajectory_execution_finished)
                if hasattr(device_instance, 'trajectory_execution_error'):
                    device_instance.trajectory_execution_error.connect(self.trajectory_execution_error)
                
                # 绑定示教轨迹实时更新信号（如果设备支持）
                if hasattr(device_instance, 'teaching_trajectory_updated'):
                    device_instance.teaching_trajectory_updated.connect(self.teaching_trajectory_updated)
                
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
            self.device_error.emit(error_msg)
            raise ValueError(error_msg)
        try:
            # 设备的逻辑实例负责将抽象命令映射到实际的底层命令请求
            command, params = device_instance.command_parser.parse_command_string(abstract_command)
            self.send_device_abstract_command_requested.emit(device_id, command, params)
            self.device_command_response.emit(f"命令请求已发送至设备 '{device_id}' 的逻辑实例")
            return "Command request sent to device logic instance."
        except Exception as e:
            error_msg = f"设备 '{device_id}' 处理抽象命令 '{abstract_command}' 失败: {e}"
            self.logger.error(error_msg)
            self.device_error.emit(error_msg)
            raise

    @Slot(str, dict) # 接收来自 DeviceProtocolParser 的业务语义数据
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
            self.device_error.emit(f"无法找到或创建设备实例 '{device_id}' 来处理语义数据")
            return

        try:
            # 设备逻辑实例负责更新自身的内部状态模型
            device_instance.update_state_from_semantic_data(parsed_semantic_data)
            
            # 实时更新、异常检测和告警 (由设备逻辑实例自身处理)
            device_instance.check_anomaly() # 假设设备实例内部会发出错误信号

            # 通知 Coordinator 设备状态已更新
            self.device_status_updated.emit(
                device_id,
                device_instance.get_current_state().to_dict() # 获取最新状态字典
            )
            self.logger.debug(f"设备 '{device_id}' 状态已更新")

        except Exception as e:
            error_msg = f"处理设备 '{device_id}' 语义数据失败: {e}"
            self.logger.error(error_msg)
            self.device_error.emit(error_msg)

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