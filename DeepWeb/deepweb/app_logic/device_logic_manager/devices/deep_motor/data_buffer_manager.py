# src/app_logic/device_logic_manager/devices/deep_motor/data_buffer_manager.py
# DeepMotor 数据缓冲区管理

import pandas as pd
import time
from typing import Dict, Any, Optional
from deepweb.config.config_manager import ConfigManager
from deepweb.data_management.log_manager import LogManager

class DeepMotorDataBufferManager:
    """DeepMotor 数据缓冲区管理器"""
    
    # 定义所有支持的参数类型
    PARAMETER_TYPES = {
        "device_type": "str",     # 设备ID
        "motor_id": "int",      # 电机ID

        # 基础运动参数
        "position": "float",      # 位置
        "velocity": "float",      # 速度
        "torque": "float",        # 扭矩
        
        # 状态参数
        "temperature": "float",   # 温度
        "error_code": "int",      # 错误码
        "motor_can_id": "int",    # CAN ID
        "mode_state": "str",      # 模式状态
        "response_mode": "int",   # 响应模式
        "success": "bool",        # 成功标志
        
        # 故障标志 (协议中返回的是 int 0/1，不是 bool)
        "flt_uninitialized": "int",        # 未初始化故障
        "flt_hall_encoding": "int",        # 霍尔编码故障
        "flt_magnetic_encoding": "int",    # 磁编码故障
        "flt_over_temperature": "int",     # 过温故障
        "flt_over_current": "int",         # 过流故障
        "flt_voltage_drop": "int"          # 电压跌落故障
    }
    
    def __init__(self, config_manager: ConfigManager, log_manager: LogManager):
        """
        初始化数据缓冲区管理器
        :param config_manager: 配置管理器
        :param log_manager: 统一的日志管理器
        """
        self.config_manager = config_manager
        self.log_manager = log_manager
        self.buffer_size = config_manager.get("device_settings.deepmotor_history_length", 1000)
        self._start_time = time.time()
        
        # 使用统一的日志管理器
        self.logger = log_manager.get_logger(__name__)
        
        # 初始化所有数据缓冲区
        self.data_buffers = self._initialize_buffers()
        
    def _initialize_buffers(self) -> Dict[str, pd.DataFrame]:
        """初始化所有数据缓冲区"""
        buffers = {}
        for param_name in self.PARAMETER_TYPES.keys():
            buffers[param_name] = pd.DataFrame(columns=['time', 'value'])
        return buffers
    
    def add_data_point(self, parameter: str, value: Any) -> bool:
        """
        添加数据点 - 优化版本，减少频繁操作
        :param parameter: 参数名称
        :param value: 参数值
        :return: 是否成功添加
        """
        if parameter not in self.PARAMETER_TYPES:
            # 改为调试级别，避免警告日志
            self.logger.debug(f"参数 '{parameter}' 不在支持的参数列表中，跳过存储")
            return False
            
        # 验证数据类型
        expected_type = self.PARAMETER_TYPES[parameter]
        if not self._validate_data_type(value, expected_type):
            return False
            
        # 计算相对时间
        relative_time = time.time() - self._start_time
        
        # 优化：使用更高效的方式添加数据点
        buffer = self.data_buffers[parameter]
        
        # 如果缓冲区已满，先删除最老的数据
        if len(buffer) >= self.buffer_size:
            buffer.drop(buffer.index[0], inplace=True)
        
        # 添加新数据点 - 使用优化的方法避免FutureWarning
        new_data = {'time': relative_time, 'value': value}
        
        if buffer.empty:
            # 如果缓冲区为空，直接创建新的DataFrame
            self.data_buffers[parameter] = pd.DataFrame([new_data])
        else:
            # 使用pd.concat但添加sort=False参数避免FutureWarning
            new_row = pd.DataFrame([new_data])
            # 确保新行与现有DataFrame有相同的列顺序和数据类型
            new_row = new_row.reindex(columns=buffer.columns, fill_value=0)
            self.data_buffers[parameter] = pd.concat([buffer, new_row], ignore_index=True, sort=False)
        
        # 减少日志记录频率，只在缓冲区满时记录
        if len(self.data_buffers[parameter]) % 100 == 0:
            self.logger.debug(f"参数 '{parameter}' 缓冲区大小: {len(self.data_buffers[parameter])}")
            
        return True
    
    def _validate_data_type(self, value: Any, expected_type: str) -> bool:
        """验证数据类型"""
        if value is None:
            return False
            
        if expected_type == "float":
            return isinstance(value, (int, float))
        elif expected_type == "int":
            return isinstance(value, int)
        elif expected_type == "str":
            return isinstance(value, str)
        elif expected_type == "bool":
            return isinstance(value, bool)
        
        return True
    
    def get_historical_data(self, parameter: str, options: dict = {}) -> Optional[Dict[str, Any]]:
        """
        获取历史数据
        :param parameter: 参数名称
        :param options: 选项（如时间范围）
        :return: 历史数据字典
        """
        if parameter not in self.data_buffers:
            return None
            
        data = self.data_buffers[parameter].copy()
        
        # 应用时间范围过滤（如果指定）
        if 'start_time' in options and 'end_time' in options:
            data = data[(data['time'] >= options['start_time']) & (data['time'] <= options['end_time'])]
        
        return {
            'data': data,
            'parameter': parameter,
            'data_type': self.PARAMETER_TYPES[parameter],
            'total_points': len(data),
            'buffer_size': self.buffer_size
        }
    
    def get_all_parameters(self) -> Dict[str, Any]:
        """获取所有参数的当前状态"""
        current_state = {}
        for param_name in self.PARAMETER_TYPES.keys():
            if len(self.data_buffers[param_name]) > 0:
                current_state[param_name] = self.data_buffers[param_name].iloc[-1]['value']
            else:
                current_state[param_name] = None
        return current_state
    
    def get_buffer_info(self) -> Dict[str, Any]:
        """获取缓冲区信息"""
        info = {}
        for param_name, buffer in self.data_buffers.items():
            info[param_name] = {
                'data_points': len(buffer),
                'data_type': self.PARAMETER_TYPES[param_name],
                'has_data': len(buffer) > 0
            }
        return info
    
    def clear_buffer(self, parameter: Optional[str] = None):
        """
        清空缓冲区
        :param parameter: 特定参数，如果为None则清空所有
        """
        if parameter:
            if parameter in self.data_buffers:
                self.data_buffers[parameter] = pd.DataFrame(columns=['time', 'value'])
        else:
            self.data_buffers = self._initialize_buffers()
    
    def resize_buffer(self, new_size: int):
        """
        调整缓冲区大小
        :param new_size: 新的缓冲区大小
        """
        self.buffer_size = new_size
        
        # 调整所有缓冲区
        for param_name in self.data_buffers:
            if len(self.data_buffers[param_name]) > new_size:
                self.data_buffers[param_name] = self.data_buffers[param_name].iloc[-new_size:]
    
    def get_statistics(self, parameter: str) -> Optional[Dict[str, Any]]:
        """
        获取参数统计信息
        :param parameter: 参数名称
        :return: 统计信息
        """
        if parameter not in self.data_buffers or len(self.data_buffers[parameter]) == 0:
            return None
            
        data = self.data_buffers[parameter]['value']
        
        stats = {
            'count': len(data),
            'min': float(data.min()),
            'max': float(data.max()),
            'mean': float(data.mean()),
            'std': float(data.std()),
            'latest': float(data.iloc[-1]) if len(data) > 0 else None
        }
        
        return stats 