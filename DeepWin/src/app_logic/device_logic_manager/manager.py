

# src/app_logic/device_logic_manager/manager.py
# 设备逻辑管理器核心实现

import time
from PySide6.QtCore import QObject, Signal, Slot
from typing import Dict, Any, Optional, Union, List

from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager
from src.app_logic.device_logic_manager.device_models import BaseDeviceState, DeepArmState, DeepToyState, DeepMotorState, DeviceStatus
from src.app_logic.device_logic_manager.devices.base_device import BaseDevice
from src.app_logic.device_logic_manager.devices.deep_motor.deep_motor import DeepMotor
from src.app_logic.device_logic_manager.devices.deep_arm.deep_arm import DeepArm

# 导入 TeachingTrajectoryManager，但其逻辑在 Manager 中会暂时跳过
from src.app_logic.device_logic_manager.devices.deep_arm.teaching_trajectory_manager import TeachingTrajectoryManager


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
    """

    # 定义设备逻辑管理器可以向 Coordinator 发射的信号
    device_status_updated = Signal(dict)    # 设备状态实时更新，参数为设备ID和状态数据 (dict)
    device_command_response = Signal(str)   # 设备控制命令的响应 (str)
    device_error = Signal(str)              # 设备相关操作发生错误 (str)

    # 新增信号：请求 Coordinator 发送抽象命令
    send_device_abstract_command_requested = Signal(str, str, list) # (device_id, abstract_command_name, args)

    # DeepArm 示教轨迹相关信号 (目前暂时不使用)
    teaching_started = Signal(str)
    teaching_stopped = Signal(str, list)
    trajectory_playback_started = Signal(str, str)
    trajectory_playback_finished = Signal(str, str)
    trajectory_playback_error = Signal(str, str)


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
        self.logger.info("DeviceLogicManager: 初始化中...")

        # 维护当前连接的设备实例 (示例：使用字典存储设备ID -> 设备逻辑实例)
        # 这些实例将负责处理特定设备的命令和状态更新
        self.managed_devices: Dict[str, BaseDevice] = {}

        # 实例化 TeachingTrajectoryManager (逻辑暂时跳过)
        self.teaching_manager = TeachingTrajectoryManager(log_manager=log_manager)

        self.logger.info("DeviceLogicManager: 初始化完成。")

    def _get_or_create_device_instance(self, device_id: str, device_type: Optional[str] = None) -> Optional[BaseDevice]:
        """
        根据设备ID获取或创建对应的设备逻辑实例。
        这是一个内部辅助方法。
        :param device_id: 设备的唯一标识符。
        :param device_type: 可选，明确指定设备类型，用于首次创建。
        :return: 对应的 BaseDevice 实例。
        """
        if device_id not in self.managed_devices:
            # 根据 device_id 或 device_type 推断并创建具体的设备逻辑实例
            # 这里是简化的逻辑，实际可能需要更复杂的设备注册/发现机制
            if device_type == "DeepArm" or device_id.startswith("DeepArm"):
                self.managed_devices[device_id] = DeepArm(device_id, self.logger_instance)
            elif device_type == "DeepMotor" or device_id.startswith("DeepMotor"):
                self.managed_devices[device_id] = DeepMotor(device_id, self.logger_instance)
            elif device_type == "DeepToy" or device_id.startswith("DeepToy"):
                # 假设 DeepToy 也有自己的逻辑类
                # self.managed_devices[device_id] = DeepToy(device_id, self.logger)
                self.logger.warning(f"DeviceLogicManager: DeepToy 逻辑类未实现，使用 BaseDevice 占位 for {device_id}")
                self.managed_devices[device_id] = BaseDevice(device_id, self.logger_instance) # Placeholder
            else:
                self.logger.error(f"DeviceLogicManager: 无法识别的设备类型或 ID 前缀: {device_id}")
                return None
            self.logger.info(f"DeviceLogicManager: 新设备实例 '{device_id}' 创建成功。")
        return self.managed_devices.get(device_id)

    @Slot(str, str)
    def send_command_to_device(self, device_id: str, abstract_command: str) -> str:
        """
        接收来自 Coordinator 的抽象控制指令，并将其转发给对应的设备逻辑实例处理。
        设备逻辑实例将通过信号请求 Coordinator 发送到服务层进行底层协议转换和发送。
        :param device_id: 目标设备的唯一标识符。
        :param abstract_command: 抽象的控制指令字符串，如 "move_to_point(100, 200, 300)"。
        :return: 模拟的设备响应。
        """
        self.logger.info(f"DeviceLogicManager: 收到抽象指令 '{abstract_command}' for device '{device_id}'。")
        device_instance = self._get_or_create_device_instance(device_id)
        if not device_instance:
            error_msg = f"无法找到或创建设备实例 '{device_id}' 来发送命令。"
            self.device_error.emit(error_msg)
            raise ValueError(error_msg)

        try:
            # 解析抽象命令名称和参数
            func_name_start = abstract_command.find("(")
            if func_name_start != -1:
                abstract_command_name = abstract_command[:func_name_start]
                args_str = abstract_command[func_name_start+1:-1]
                args = [arg.strip() for arg in args_str.split(',') if arg.strip()]
                # 尝试转换为数字类型
                parsed_args = []
                for arg in args:
                    try:
                        if '.' in arg:
                            parsed_args.append(float(arg))
                        else:
                            parsed_args.append(int(arg))
                    except ValueError:
                        parsed_args.append(arg) # 如果不是数字，保留为字符串
            else:
                abstract_command_name = abstract_command
                parsed_args = []

            # 设备的逻辑实例负责将抽象命令映射到实际的底层命令请求
            # 这里假设 BaseDevice 或其子类有一个方法来处理这个请求
            # 并通过 emit send_device_abstract_command_requested 信号
            device_instance.execute_abstract_command(
                abstract_command_name, parsed_args, self.send_device_abstract_command_requested
            )
            
            self.device_command_response.emit(f"命令请求已发送至设备 '{device_id}' 的逻辑实例。")
            return "Command request sent to device logic instance."
        except Exception as e:
            error_msg = f"设备 '{device_id}' 处理抽象命令 '{abstract_command}' 失败: {e}"
            self.logger.error(f"DeviceLogicManager: {error_msg}")
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
        self.logger.debug(f"DeviceLogicManager: 收到设备 '{device_id}' 的语义数据: {parsed_semantic_data}")
        self.logger.info(f"DeviceLogicManager: 收到设备 '{device_id}' 的语义数据: {parsed_semantic_data}")
        device_instance = self._get_or_create_device_instance(
            device_id,
            device_type=parsed_semantic_data.get('device_type') # 从数据中尝试获取类型
        )
        if not device_instance:
            self.device_error.emit(f"无法找到或创建设备实例 '{device_id}' 来处理语义数据。")
            return

        try:
            # 设备逻辑实例负责更新自身的内部状态模型
            device_instance.update_state_from_semantic_data(parsed_semantic_data)
            
            # 实时更新、异常检测和告警 (由设备逻辑实例自身处理)
            device_instance.check_anomaly() # 假设设备实例内部会发出错误信号

            # 通知 Coordinator 设备状态已更新
            self.device_status_updated.emit({
                "device_id": device_id,
                "status": device_instance.get_current_state().to_dict() # 获取最新状态字典
            })
            self.logger.debug(f"DeviceLogicManager: 设备 '{device_id}' 状态已更新。")

            # # 示教逻辑（暂时跳过）
            # if self._is_teaching_mode.get(device_id, False) and isinstance(device_instance.get_current_state(), DeepArmState):
            #     self.teaching_manager.record_trajectory_point(device_id, device_instance.get_current_state().get_current_joint_angles())

        except Exception as e:
            error_msg = f"处理设备 '{device_id}' 语义数据失败: {e}"
            self.logger.error(f"DeviceLogicManager: {error_msg}")
            self.device_error.emit(error_msg)

    # # 示教模式相关槽函数 (暂时跳过实现逻辑)
    # @Slot(str)
    # def start_teaching_mode(self, device_id: str):
    #     self.logger.info(f"DeviceLogicManager: 示教模式启动请求 for {device_id} (逻辑暂时跳过)")
    #     self._is_teaching_mode[device_id] = True
    #     self.teaching_started.emit(device_id)

    # @Slot(str, str)
    # def stop_teaching_mode(self, device_id: str, trajectory_name: str):
    #     self.logger.info(f"DeviceLogicManager: 示教模式停止请求 for {device_id} (逻辑暂时跳过)")
    #     self._is_teaching_mode[device_id] = False
    #     self.teaching_stopped.emit(device_id, []) # 模拟空列表
    #     self.device_error.emit(f"机械臂 '{device_id}' 示教模式结束，轨迹 '{trajectory_name}' 已保存。")


    # @Slot(str, str)
    # def play_teaching_trajectory(self, device_id: str, trajectory_name: str):
    #     self.logger.info(f"DeviceLogicManager: 播放轨迹请求 for {device_id} (逻辑暂时跳过)")
    #     self.trajectory_playback_started.emit(device_id, trajectory_name)
    #     self.trajectory_playback_finished.emit(device_id, trajectory_name)
    #     self.device_error.emit(f"机械臂 '{device_id}' 轨迹 '{trajectory_name}' 播放完成。")


    def cleanup(self):
        """
        清理设备逻辑管理器占用的资源。
        在应用程序关闭时调用。
        """
        self.logger.info("DeviceLogicManager: 执行清理工作。")
        for device_id, instance in self.managed_devices.items():
            instance.cleanup() # 清理各个设备实例
        if hasattr(self, 'teaching_manager') and self.teaching_manager:
            self.teaching_manager.cleanup()
        self.logger.info("DeviceLogicManager: 清理完成。")