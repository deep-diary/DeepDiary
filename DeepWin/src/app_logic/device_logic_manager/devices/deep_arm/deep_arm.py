
# DeepArm 机械臂相关实现

from typing import Dict, Any, List, Callable, Optional

from src.data_management.log_manager import LogManager
from src.app_logic.device_logic_manager.devices.base_device import BaseDevice
from src.app_logic.device_logic_manager.device_models import DeepArmState, DeviceStatus
from src.app_logic.device_logic_manager.devices.deep_motor.deep_motor import DeepMotor # 导入 DeepMotor 逻辑类
from PySide6.QtCore import QObject, Signal, Slot


class DeepArm(BaseDevice):
    """
    DeepArm 机械臂的逻辑实现。
    它管理多个 DeepMotor 实例，并提供更高层次的机械臂控制和状态管理。
    """
    def __init__(self, device_id: str, log_manager: LogManager, parent: Optional[QObject] = None):
        super().__init__(device_id, log_manager, parent)
        self._state: DeepArmState = DeepArmState(device_id=device_id) # 使用 DeepArmState
        self.logger.info(f"DeepArm '{device_id}': 初始化中...")

        # DeepArm 包含 6 个 DeepMotor
        self.motors: Dict[str, DeepMotor] = {}
        for i in range(1, 7):
            motor_id = f"{device_id}_Motor{i}"
            # 这里的 DeepMotor 实例仅用于管理和提供其逻辑，不会直接与实际硬件通信
            # 实际硬件通信仍通过 Coordinator -> ProtocolParser -> SerialCommunicator 进行
            self.motors[motor_id] = DeepMotor(motor_id, log_manager)
            # 可以连接 DeepMotor 的内部信号，例如用于聚合错误或状态
            self.motors[motor_id].device_error.connect(
                lambda dev_id, err_msg: self.device_error.emit(self.device_id, f"子电机 '{dev_id}' 错误: {err_msg}")
            )
            self.motors[motor_id].device_state_updated.connect(
                lambda dev_id, state_dict: self.logger.debug(f"DeepArm '{self.device_id}': 子电机 '{dev_id}' 状态更新: {state_dict['motor_temperature']}")
            )

        self.logger.info(f"DeepArm '{device_id}': 初始化完成，包含 {len(self.motors)} 个 DeepMotor。")

    def get_current_state(self) -> DeepArmState:
        """重写以返回 DeepArmState。"""
        return self._state

    def update_state_from_semantic_data(self, semantic_data: Dict[str, Any]):
        """
        从业务语义数据更新 DeepArm 的状态模型。
        :param semantic_data: 语义数据字典，例如包含 joint_angles, temperature 等。
        """
        self.logger.debug(f"DeepArm '{self.device_id}': 收到语义数据更新: {semantic_data}")
        # 调用基类更新通用状态
        super().update_state_from_semantic_data(semantic_data)

        # 更新 DeepArm 独有的状态
        if 'joint1_angle' in semantic_data: self._state.joint1_angle = float(semantic_data['joint1_angle'])
        if 'joint2_angle' in semantic_data: self._state.joint2_angle = float(semantic_data['joint2_angle'])
        if 'joint3_angle' in semantic_data: self._state.joint3_angle = float(semantic_data['joint3_angle'])
        if 'joint4_angle' in semantic_data: self._state.joint4_angle = float(semantic_data['joint4_angle'])
        if 'joint5_angle' in semantic_data: self._state.joint5_angle = float(semantic_data['joint5_angle'])
        if 'joint6_angle' in semantic_data: self._state.joint6_angle = float(semantic_data['joint6_angle'])
        
        # 示例：聚合电机温度，假设 DeepArmTemperature 在 DBC 中是聚合的
        if 'temperature' in semantic_data:
            self._state.temperature = float(semantic_data['temperature'])
        # 也可以遍历子电机更新其状态，但这里假设语义数据直接针对 DeepArm
        # For example, if individual motor temperatures come in semantic_data as well:
        # for motor_id, motor_instance in self.motors.items():
        #    if f'{motor_id}_temperature' in semantic_data:
        #        motor_instance.update_state_from_semantic_data({
        #            'motor_temperature': semantic_data[f'{motor_id}_temperature']
        #        })

        self.logger.debug(f"DeepArm '{self.device_id}': 特定状态更新完成。")
        self.device_state_updated.emit(self.device_id, self._state.to_dict())

    def execute_abstract_command(self,
                                 command_name: str,
                                 args: List[Any],
                                 send_request_signal: Callable[[str, str, List[Any]], Any]):
        """
        执行 DeepArm 特定的抽象命令。
        :param command_name: 抽象命令的名称 (如 "move_joint_angles", "set_end_effector_pos")。
        :param args: 命令的参数列表。
        :param send_request_signal: 用于请求 Coordinator 发送底层命令的信号发射器。
        """
        self.logger.info(f"DeepArm '{self.device_id}': 收到命令 '{command_name}' with args {args}")
        if command_name == "move_joint_angles":
            if len(args) == 6 and all(isinstance(a, (int, float)) for a in args):
                # DeepArm 的命令将直接发送给 ProtocolParser，而不是分解到每个 DeepMotor
                # ProtocolParser 会知道如何将 "move_joint_angles" 转换为 DeepArm 的底层协议
                self.logger.debug(f"DeepArm '{self.device_id}': 请求移动关节到 {args}")
                send_request_signal(self.device_id, "move_joint_angles", args)
                self.logger.info(f"DeepArm '{self.device_id}': 已请求移动关节。")
            else:
                self.device_error.emit(self.device_id, "move_joint_angles 命令需要 6 个数字参数。")
        elif command_name == "get_arm_status":
             self.logger.info(f"DeepArm '{self.device_id}': 返回当前状态: {self._state.to_dict()}")
        elif command_name == "reset_arm":
            self.logger.info(f"DeepArm '{self.device_id}': 请求复位机械臂。")
            send_request_signal(self.device_id, "reset_arm", [])
        else:
            super().execute_abstract_command(command_name, args, send_request_signal) # 转发到基类处理未知命令

    def get_supported_commands(self) -> List[str]:
        """
        获取 DeepArm 支持的抽象命令列表。
        """
        return super().get_supported_commands() + ["move_joint_angles", "get_arm_status", "reset_arm"]

    def check_anomaly(self):
        """
        执行 DeepArm 特定的异常检测。
        """
        super().check_anomaly() # 先执行通用检测

        if self._state.temperature > 85:
            self.device_error.emit(self.device_id, f"DeepArm '{self.device_id}' 整体温度过高 ({self._state.temperature}°C)！")
            self._state.connection_status = DeviceStatus.WARNING

        # 示例：检查所有子电机是否有错误
        for motor_id, motor_instance in self.motors.items():
            motor_instance.check_anomaly() # 内部会发射其自身的 error 信号

        if self._state.current_status == 2: # 假设 2 为错误状态
            self.device_error.emit(self.device_id, f"DeepArm '{self.device_id}' 报告内部错误状态！")
            self._state.connection_status = DeviceStatus.ERROR


    def cleanup(self):
        """
        清理 DeepArm 实例和其包含的 DeepMotor 实例资源。
        """
        self.logger.info(f"DeepArm '{self.device_id}': 清理中...")
        for motor_id, motor_instance in self.motors.items():
            motor_instance.cleanup()
        self.logger.info(f"DeepArm '{self.device_id}': 清理完成。")
        super().cleanup()