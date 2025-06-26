# src/app_logic/device_logic_manager/devices/base_device.py
# 定义设备逻辑的基类和通用命令接口

from abc import ABC, abstractmethod
from PySide6.QtCore import QObject, Signal
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
import time
from enum import Enum

from src.data_management.log_manager import LogManager


class DeviceStatus(Enum):
    """设备连接和运行状态的枚举。"""
    DISCONNECTED = "Disconnected"
    CONNECTED = "Connected"
    IDLE = "Idle"
    WORKING = "Working"
    ERROR = "Error"
    WARNING = "Warning"
    TEACHING = "Teaching"
    PLAYING = "Playing"


@dataclass
class BaseDeviceState:
    """所有设备状态的基类。"""
    device_id: str
    connection_status: DeviceStatus = DeviceStatus.DISCONNECTED
    last_active_time: float = field(default_factory=time.time)
    firmware_version: str = "Unknown"
    is_online: bool = False # 简化判断，实际可基于 connection_status

    def to_dict(self) -> Dict[str, Any]:
        """将设备状态转换为字典，便于传输或日志记录。"""
        # 注意：枚举类型需要转换为其值，否则无法序列化
        return {
            "device_id": self.device_id,
            "connection_status": self.connection_status.value,
            "last_active_time": self.last_active_time,
            "firmware_version": self.firmware_version,
            "is_online": self.is_online
        }

    def update_from_dict(self, data: Dict[str, Any]):
        """从字典更新设备状态。"""
        for key, value in data.items():
            if hasattr(self, key):
                # 尝试转换枚举
                if key == "connection_status" and isinstance(value, str):
                    try:
                        self.connection_status = DeviceStatus(value)
                    except ValueError:
                        pass # 保持原值或记录错误
                else:
                    setattr(self, key, value)
        self.last_active_time = time.time() # 任何更新都视为活跃


class DeviceCapability:
    """设备能力基类（普通类，无ABCMeta）"""
    def get_capability_name(self) -> str:
        raise NotImplementedError
    def get_supported_methods(self) -> dict:
        raise NotImplementedError


class BaseDevice(QObject):
    """
    所有设备逻辑实现的基类。
    提供了设备通用的属性、状态管理和命令执行接口。
    支持能力管理，允许设备动态添加和移除功能能力。
    """
    # 定义设备实例可以向 DeviceLogicManager 反馈的信号
    # 注意：这些信号的连接通常在 DeviceLogicManager 内部处理
    # 例如：device_error 信号用于报告设备内部发生的错误
    device_error = Signal(str, str) # (device_id, error_message)
    device_states_updated = Signal(str, dict) # (device_id, new_state_dict)
    
    # 新增：设备实例向协调器发送命令请求的信号
    command_to_coordinator = Signal(str, str, list) # (device_id, command_name, args)

    def __init__(self, device_id: str, log_manager: LogManager, parent: Optional[QObject] = None):
        """
        初始化 BaseDevice。
        :param device_id: 设备的唯一标识符。
        :param log_manager: 全局日志管理器实例。
        :param parent: QObject 父对象。
        """
        super().__init__(parent)
        self.device_id = device_id
        # self.logger = log_manager.get_logger(__name__)
        self.logger = log_manager.get_logger(f"{self.__class__.__name__}.{device_id}")
        self._state: BaseDeviceState = BaseDeviceState(device_id=device_id)
        
        # 能力管理
        self._capabilities: Dict[str, DeviceCapability] = {}
        
        self.logger.info(f"BaseDevice '{device_id}': 初始化完成。")

    def add_capability(self, capability: DeviceCapability):
        """
        动态添加能力
        :param capability: 设备能力实例
        """
        capability_name = capability.get_capability_name()
        self._capabilities[capability_name] = capability
        self.logger.info(f"BaseDevice '{self.device_id}': 添加能力 '{capability_name}'")

    def has_capability(self, capability_name: str) -> bool:
        """
        检查设备是否支持指定能力
        :param capability_name: 能力名称
        :return: 是否支持
        """
        return capability_name in self._capabilities

    def get_capability_methods(self, capability_name: str) -> Dict[str, Callable]:
        """
        获取能力支持的所有方法
        :param capability_name: 能力名称
        :return: 方法映射字典
        """
        if not self.has_capability(capability_name):
            return {}
        return self._capabilities[capability_name].get_supported_methods()

    def call_capability_method(self, capability_name: str, method_name: str, *args, **kwargs):
        """
        调用能力方法
        :param capability_name: 能力名称
        :param method_name: 方法名称
        :param args: 位置参数
        :param kwargs: 关键字参数
        :return: 方法执行结果
        """
        if not self.has_capability(capability_name):
            raise ValueError(f"设备 '{self.device_id}' 不支持能力 '{capability_name}'")
        
        methods = self.get_capability_methods(capability_name)
        if method_name not in methods:
            raise ValueError(f"能力 '{capability_name}' 不支持方法 '{method_name}'")
        
        return methods[method_name](*args, **kwargs)

    def get_all_capabilities(self) -> Dict[str, List[str]]:
        """
        获取设备支持的所有能力和方法
        :return: 能力名称到方法列表的映射
        """
        capabilities = {}
        for capability_name in self._capabilities.keys():
            methods = self.get_capability_methods(capability_name)
            capabilities[capability_name] = list(methods.keys())
        return capabilities

    def get_current_state(self) -> BaseDeviceState:
        """
        获取当前设备的实时状态模型。
        :return: 设备的当前状态模型实例。
        """
        return self._state

    def update_state_from_semantic_data(self, semantic_data: Dict[str, Any]):
        """
        从业务语义数据更新设备状态模型。
        这是由 DeviceLogicManager 调用的核心方法。
        :param semantic_data: 来自 DeviceProtocolParser 的业务语义数据字典。
        """
        # self.logger.debug(f"Device '{self.device_id}': 收到语义数据更新: {semantic_data}")
        # 更新基类状态
        self._state.update_from_dict(semantic_data)
        self._state.is_online = True # 收到数据表明在线
        self._state.connection_status = DeviceStatus.CONNECTED
        # self.logger.debug(f"Device '{self.device_id}': 状态已更新。")
        self.device_states_updated.emit(self.device_id, self._state.to_dict())

    def execute_abstract_command(self,
                                 command_name: str,
                                 args: List[Any],
                                 send_request_signal: Callable[[str, str, List[Any]], Any]):
        """
        执行一个抽象的设备命令。
        子类应重写此方法以处理特定设备的命令。
        :param command_name: 抽象命令的名称。
        :param args: 命令的参数列表。
        :param send_request_signal: 一个回调函数/信号发射器，用于请求 Coordinator 发送底层命令。
                                     签名应为: (device_id, abstract_command_name, args)
        """
        self.logger.warning(f"Device '{self.device_id}': 抽象命令 '{command_name}' 未被子类实现。")
        self.device_error.emit(self.device_id, f"抽象命令 '{command_name}' 未实现。")

    def get_supported_commands(self) -> List[str]:
        """
        获取当前设备支持的抽象命令列表。
        子类应重写此方法。
        """
        return ["get_status"]

    def check_anomaly(self):
        """
        执行设备内部的异常检测逻辑。
        子类应重写此方法。
        如果检测到异常，应发射 device_error 信号。
        """
        self.logger.debug(f"Device '{self.device_id}': 正在进行通用异常检测。")
        if self._state.connection_status == DeviceStatus.ERROR:
            self.device_error.emit(self.device_id, f"设备 '{self.device_id}' 报告错误状态。")
        # 更多通用异常检测，如长时间无数据更新等。

    def cleanup(self):
        """
        清理设备实例占用的资源。
        """
        # 清理所有能力
        for capability_name, capability in self._capabilities.items():
            if hasattr(capability, 'cleanup'):
                try:
                    capability.cleanup()
                except Exception as e:
                    self.logger.warning(f"清理能力 '{capability_name}' 时出错: {e}")
        
        self._capabilities.clear()
        self.logger.info(f"Device '{self.device_id}': 清理完成。")