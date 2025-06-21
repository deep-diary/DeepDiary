from typing import Dict, Any
import time
import pandas as pd

class DeepMotor:
    def __init__(self, device_id, buffer_size, start_time):
        self.device_id = device_id
        self.buffer_size = buffer_size
        self.start_time = start_time
        self.data_buffer = {
            'position': pd.DataFrame(),
            'velocity': pd.DataFrame(),
            'torque': pd.DataFrame(),
            'temperature': pd.DataFrame(),
            'error_code': pd.DataFrame(),
            'motor_can_id': pd.DataFrame(),
            'mode_state': pd.DataFrame(),
            'flt_uninitialized': pd.DataFrame(),
            'flt_hall_encoding': pd.DataFrame(),
            'flt_magnetic_encoding': pd.DataFrame(),
            'flt_over_temperature': pd.DataFrame(),
            'flt_over_current': pd.DataFrame(),
            'flt_voltage_drop': pd.DataFrame()
        }
        self.logger = None  # Assuming a logger is set up
        self.teaching_manager = None  # Assuming a teaching manager is set up

    def update_state_from_semantic_data(self, semantic_data: Dict[str, Any]):
        """
        从业务语义数据更新 DeepMotor 的状态模型。
        """
        # 只保留状态更新的info日志
        super().update_state_from_semantic_data(semantic_data)

        for key, value in semantic_data.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)
        
        current_state_dict = self._state.to_dict()

        # 更新数据缓冲区 - 使用相对时间
        relative_time = time.time() - self._start_time
        
        parameter_mapping = {
            'position': 'position',
            'velocity': 'velocity', 
            'torque': 'torque',
            'temperature': 'temperature',
            'error_code': 'error_code',
            'motor_can_id': 'motor_can_id',
            'mode_state': 'mode_state',
            'flt_uninitialized': 'flt_uninitialized',
            'flt_hall_encoding': 'flt_hall_encoding',
            'flt_magnetic_encoding': 'flt_magnetic_encoding',
            'flt_over_temperature': 'flt_over_temperature',
            'flt_over_current': 'flt_over_current',
            'flt_voltage_drop': 'flt_voltage_drop'
        }
        for semantic_key, buffer_key in parameter_mapping.items():
            if semantic_key in semantic_data:
                value = semantic_data[semantic_key]
                if value is not None:
                    if semantic_key == 'mode_state':
                        new_data = pd.DataFrame([{'time': relative_time, 'value': value}])
                        self.data_buffer[buffer_key] = pd.concat([self.data_buffer[buffer_key], new_data], ignore_index=True)
                    elif isinstance(value, (int, float)):
                        new_data = pd.DataFrame([{'time': relative_time, 'value': value}])
                        self.data_buffer[buffer_key] = pd.concat([self.data_buffer[buffer_key], new_data], ignore_index=True)
                    else:
                        self.logger.warning(f"DeepMotor '{self.device_id}': 参数 {semantic_key} 的值 {value} 不是支持的格式")
        for key in self.data_buffer:
            if len(self.data_buffer[key]) > self.buffer_size:
                self.data_buffer[key] = self.data_buffer[key].iloc[-self.buffer_size:]
        if self.teaching_manager.is_teaching(self.device_id):
            self.teaching_manager.record_trajectory_point(
                device_id=self.device_id,
                position=semantic_data.get('position'),
                velocity=semantic_data.get('velocity')
            )
        self.logger.info(f"DeepMotor '{self.device_id}': 状态已更新")
        self.device_states_updated.emit(self.device_id, current_state_dict)

    # 轨迹数据获取、命令执行等其它方法内，只保留info/warning/error日志，删除debug日志。轨迹点记录只保留info。轨迹播放只保留开始/结束/异常日志。 