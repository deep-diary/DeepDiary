# src/app_logic/device_logic_manager/devices/base_device.py
# 定义设备逻辑的基类和通用命令接口

from PySide6.QtCore import QObject, Signal
from typing import Dict, Any, List, Callable, Optional

from src.data_management.log_manager import LogManager
from src.app_logic.device_logic_manager.device_models import BaseDeviceState, DeviceStatus


class BaseDevice(QObject):
    """
    所有设备逻辑实现的基类。
    提供了设备通用的属性、状态管理和命令执行接口。
    """
    # 定义设备实例可以向 DeviceLogicManager 反馈的信号
    # 注意：这些信号的连接通常在 DeviceLogicManager 内部处理
    # 例如：device_error 信号用于报告设备内部发生的错误
    device_error = Signal(str, str) # (device_id, error_message)
    device_state_updated = Signal(str, dict) # (device_id, new_state_dict)

    def __init__(self, device_id: str, log_manager: LogManager, parent: Optional[QObject] = None):
        """
        初始化 BaseDevice。
        :param device_id: 设备的唯一标识符。
        :param log_manager: 全局日志管理器实例。
        :param parent: QObject 父对象。
        """
        super().__init__(parent)
        self.device_id = device_id
        self.logger = log_manager.get_logger(f"{self.__class__.__name__}.{device_id}")
        self._state: BaseDeviceState = BaseDeviceState(device_id=device_id)
        self.logger.info(f"BaseDevice '{device_id}': 初始化完成。")

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
        self.logger.debug(f"Device '{self.device_id}': 收到语义数据更新: {semantic_data}")
        # 更新基类状态
        self._state.update_from_dict(semantic_data)
        self._state.is_online = True # 收到数据表明在线
        self._state.connection_status = DeviceStatus.CONNECTED
        self.logger.debug(f"Device '{self.device_id}': 状态已更新。")
        self.device_state_updated.emit(self.device_id, self._state.to_dict())


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
        self.logger.info(f"Device '{self.device_id}': 清理完成。")