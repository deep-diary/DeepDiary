# src/app_logic/device_logic_manager/devices/example_sensor/example_sensor.py
# 示例传感器设备逻辑实现 (演示如何添加新设备)

from typing import Dict, Any, List, Optional
import time
import pandas as pd
from PySide6.QtCore import QObject, Signal

from deepwin.data_management.log_manager import LogManager
from deepwin.data_management.config_manager import ConfigManager
from deepwin.app_logic.device_logic_manager.devices.base_device import BaseDevice
from deepwin.app_logic.device_logic_manager.devices.base_device import DeviceStatus


class ExampleSensor(BaseDevice):
    """
    示例传感器设备逻辑实现。
    这是一个演示如何按照新规则添加新设备的示例。
    文件夹名: example_sensor
    文件名: example_sensor.py
    类名: ExampleSensor
    设备类型: ExampleSensor
    """
    
    def __init__(self, device_id: str, log_manager: LogManager, parent: Optional[QObject] = None):
        super().__init__(device_id, log_manager, parent)
        self.logger.info(f"ExampleSensor '{device_id}': 初始化完成")
        
        # 初始化数据缓冲区
        self.data_buffer = {
            "temperature": pd.DataFrame(columns=['time', 'value']),
            "humidity": pd.DataFrame(columns=['time', 'value']),
            "pressure": pd.DataFrame(columns=['time', 'value']),
            "light_level": pd.DataFrame(columns=['time', 'value'])
        }
        self.buffer_size = 1000
        self._start_time = time.time()

    def update_state_from_semantic_data(self, semantic_data: Dict[str, Any]):
        """
        从业务语义数据更新示例传感器的状态。
        """
        self.logger.debug(f"ExampleSensor '{self.device_id}': 收到语义数据更新")
        super().update_state_from_semantic_data(semantic_data)
        
        # 更新数据缓冲区
        relative_time = time.time() - self._start_time
        
        # 存储历史数据
        for key in ['temperature', 'humidity', 'pressure', 'light_level']:
            if key in semantic_data and semantic_data[key] is not None:
                if isinstance(semantic_data[key], (int, float)):
                    new_data = pd.DataFrame([{'time': relative_time, 'value': semantic_data[key]}])
                    self.data_buffer[key] = pd.concat([self.data_buffer[key], new_data], ignore_index=True)
                    
                    # 限制缓冲区大小
                    if len(self.data_buffer[key]) > self.buffer_size:
                        self.data_buffer[key] = self.data_buffer[key].iloc[-self.buffer_size:]
        
        # 发出状态更新信号
        current_state = self.get_current_state()
        self.device_states_updated.emit(self.device_id, current_state.to_dict())

    def execute_abstract_command(self, command_name: str, args: List[Any], send_request_signal: Signal):
        """
        执行示例传感器特定的抽象命令。
        """
        self.logger.info(f"ExampleSensor '{self.device_id}': 收到命令 '{command_name}' with args {args}")
        
        if command_name == "read_sensor_data":
            self.logger.debug(f"ExampleSensor '{self.device_id}': 请求读取传感器数据")
            send_request_signal.emit(self.device_id, "read_sensor_data", [])
            
        elif command_name == "set_sampling_rate":
            rate = args[0] if args else 1000
            self.logger.debug(f"ExampleSensor '{self.device_id}': 请求设置采样率为 {rate}")
            send_request_signal.emit(self.device_id, "set_sampling_rate", [rate])
            
        elif command_name == "calibrate_sensor":
            self.logger.debug(f"ExampleSensor '{self.device_id}': 请求校准传感器")
            send_request_signal.emit(self.device_id, "calibrate_sensor", [])
            
        elif command_name == "reset_sensor":
            self.logger.debug(f"ExampleSensor '{self.device_id}': 请求重置传感器")
            send_request_signal.emit(self.device_id, "reset_sensor", [])
            
        elif command_name == "get_sensor_info":
            self.logger.debug(f"ExampleSensor '{self.device_id}': 请求获取传感器信息")
            send_request_signal.emit(self.device_id, "get_sensor_info", [])
            
        else:
            # 转发到基类处理未知命令
            super().execute_abstract_command(command_name, args, send_request_signal)

    def get_supported_commands(self) -> List[str]:
        """
        获取示例传感器支持的抽象命令列表。
        """
        return super().get_supported_commands() + [
            "read_sensor_data",
            "set_sampling_rate", 
            "calibrate_sensor",
            "reset_sensor",
            "get_sensor_info"
        ]

    def check_anomaly(self):
        """
        执行示例传感器特定的异常检测。
        """
        super().check_anomaly()
        
        # 检查温度是否过高
        if hasattr(self._state, 'temperature') and self._state.temperature > 80:
            self.device_error.emit(self.device_id, f"ExampleSensor '{self.device_id}' 温度过高 ({self._state.temperature}°C)")
            self._state.connection_status = DeviceStatus.WARNING
            
        # 检查湿度是否异常
        if hasattr(self._state, 'humidity') and self._state.humidity > 95:
            self.device_error.emit(self.device_id, f"ExampleSensor '{self.device_id}' 湿度过高 ({self._state.humidity}%)")
            self._state.connection_status = DeviceStatus.WARNING

    def get_historical_data(self, parameter: str, options: dict = {}) -> Dict[str, Any]:
        """
        获取指定参数的历史数据。
        """
        if parameter in self.data_buffer:
            self.logger.debug(f"ExampleSensor '{self.device_id}': 正在获取参数 '{parameter}' 的历史数据")
            return {'data': self.data_buffer[parameter].copy()}
        else:
            self.logger.warning(f"ExampleSensor '{self.device_id}': 请求了未知的历史数据参数 '{parameter}'")
            return {'data': pd.DataFrame(columns=['time', 'value'])}

    def cleanup(self):
        """
        清理示例传感器资源。
        """
        self.logger.info(f"ExampleSensor '{self.device_id}': 清理完成")
        super().cleanup() 