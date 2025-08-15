# src/services/hardware_communication/device_protocols/deep_motor_protocol/deep_motor_mapping.py
# DeepMotor 协议的具体实现 (现在作为协议适配器)
from .protocol import DeepMotorProtocol
from typing import Dict, Any, Callable, Optional

# 为了测试，我们使用类型提示而不是实际导入
from deepwin.data_management.log_manager import LogManager
from deepwin.data_management.config_manager import ConfigManager

class DeepMotorMapping():
    def __init__(self, log_manager: LogManager, config_manager: ConfigManager):
        self.log_manager = log_manager
        self.config_manager = config_manager
        # 创建DeepMotorProtocol实例，用于调用底层函数
        self.deep_motor_protocol = DeepMotorProtocol(log_manager=log_manager)
        
        """
        为 DeepMotor 定义输入/输出协议映射规则。
        这里只需定义业务语义与底层协议（通过 DeepMotorProtocol 暴露的抽象命令）之间的映射。
        实际的低级协议细节已封装在 DeepMotorProtocol 中。
        """
        
        # DeepMotor 的输入数据映射 (由 DeepMotorProtocol 解析后的语义字段)
        self.data_mapping = {
            "position": "position", # 从 motor_status 解码
            "velocity": "velocity", # 从 motor_status 解码
            "torque": "torque",     # 从 motor_status 解码
            "temperature": "temperature", # 从 motor_status 解码
            "error_code": "error_code", # 错误码
            "error_message": "error_message", # 错误信息
            "response_mode": "response_mode",
            "motor_can_id": "motor_can_id",
            "mode_state": "mode_state",
            "flt_uninitialized": "flt_uninitialized",
            "flt_hall_encoding": "flt_hall_encoding",
            "flt_magnetic_encoding": "flt_magnetic_encoding",
            "flt_over_temperature": "flt_over_temperature",
            "flt_over_current": "flt_over_current",
            "flt_voltage_drop": "flt_voltage_drop"
        }

        # 命令映射：抽象命令 -> 底层函数
        # 移除对self.deep_motor_protocol的引用，改为字符串映射
        self._command_mapping = {
            "motor_set_pos": "create_motor_pos_frame",
            "motor_set_speed": "create_motor_spd_frame",
            "motor_set_pos_speed": "create_motor_pos_spd_frame",
            "motor_set_torque": "create_motor_torque_frame",
            "motor_enable": "create_motor_enable_frame",
            "motor_disable": "create_motor_reset_frame",
            "motor_reset": "create_motor_reset_frame",
            "motor_zero": "create_motor_zero_frame",
            "motor_init": "create_motor_init_frame",
            "motor_jog": "create_motor_jog_frame",
            "motor_jog_stop": "create_motor_jog_stop_frame",
        }

        # 参数映射：抽象参数 -> 底层参数
        self._param_mapping = {
            "motor_set_pos": {
                "motor_id": "motor_id",
                "pos": "position"
            },
            "motor_set_speed": {
                "motor_id": "motor_id", 
                "spd": "speed"
            },
            "motor_set_torque": {
                "motor_id": "motor_id",
                "torque": "torque"
            },
            "motor_enable": {
                "motor_id": "motor_id"
            },
            "motor_disable": {
                "motor_id": "motor_id"
            },
            "motor_reset": {
                "motor_id": "motor_id"
            },
            "motor_zero": {
                "motor_id": "motor_id"
            },
            "motor_init": {
                "motor_id": "motor_id"
            },
            "motor_jog": {
                "motor_id": "motor_id",
                "spd": "jog_speed"
            },
            "motor_jog_stop": {
                "motor_id": "motor_id"
            },
            "motor_set_pos_speed": {
                "motor_id": "motor_id",
                "position": "position",
                "speed": "speed"
            }
        }

        # 参数验证规则
        self._param_validation = {
            "motor_set_pos": {
                "position": {"type": float, "min": -180, "max": 180},
                "motor_id": {"type": int, "min": 1, "max": 8}
            },
            "motor_set_speed": {
                "speed": {"type": float, "min": 0, "max": 50},
                "motor_id": {"type": int, "min": 1, "max": 8}
            }
        }

    def _validate_params(self, command_name: str, params: dict) -> bool:
        """验证参数是否符合规则"""
        if command_name not in self._param_validation:
            return True  # 没有验证规则的命令直接通过
        
        validation_rules = self._param_validation[command_name]
        
        for param_name, value in params.items():
            if param_name in validation_rules:
                rule = validation_rules[param_name]
                
                # 类型检查
                if "type" in rule and not isinstance(value, rule["type"]):
                    raise ValueError(f"参数 {param_name} 类型错误，期望 {rule['type']}，实际 {type(value)}")
                
                # 范围检查
                if "min" in rule and value < rule["min"]:
                    raise ValueError(f"参数 {param_name} 值过小，最小值为 {rule['min']}")
                
                if "max" in rule and value > rule["max"]:
                    raise ValueError(f"参数 {param_name} 值过大，最大值为 {rule['max']}")
        
        return True

    def map_and_call(self, command_name: str, params: dict):
        """
        映射并调用底层函数
        
        Args:
            command_name: 抽象命令名称
            params: 参数字典
            
        Returns:
            底层函数的返回值
            
        Raises:
            ValueError: 命令不存在或参数错误
        """
        try:
            # 1. 检查命令是否存在
            if command_name not in self._command_mapping:
                raise ValueError(f"未知命令: {command_name}")
            
            # 2. 获取底层函数名称
            func_name = self._command_mapping[command_name]
            
            # 3. 获取参数映射
            param_mapping = self._param_mapping.get(command_name, {})
            
            # 4. 转换参数
            mapped_params = {}
            for abstract_param, value in params.items():
                actual_param = param_mapping.get(abstract_param, abstract_param)
                mapped_params[actual_param] = value
            
            # 5. 参数验证
            # self._validate_params(command_name, mapped_params)  # 应用层验证
            
            # 6. 调用底层函数 - 从DeepMotorProtocol中获取实际函数并调用
            logger = self.log_manager.get_logger(__name__)
            logger.info(f"执行命令: {command_name}, 参数: {mapped_params}")
            
            # 获取DeepMotorProtocol中对应的方法
            if hasattr(self.deep_motor_protocol, func_name):
                method = getattr(self.deep_motor_protocol, func_name)
                if callable(method):
                    # 调用底层函数
                    result = method(**mapped_params)
                    logger.info(f"命令 {command_name} 执行成功，返回: {result}")
                    return result
                else:
                    raise ValueError(f"方法 {func_name} 不可调用")
            else:
                raise ValueError(f"DeepMotorProtocol 中未找到方法 {func_name}")
            
        except Exception as e:
            error_msg = f"执行命令 {command_name} 失败: {str(e)}"
            # 使用logger而不是直接调用log_manager
            logger = self.log_manager.get_logger(__name__)
            logger.error(error_msg)
            raise ValueError(error_msg)
            

    def get_supported_commands(self) -> list:
        """获取支持的命令列表"""
        return list(self._command_mapping.keys())

    def get_command_info(self, command_name: str) -> Optional[Dict[str, Any]]:
        """获取命令的详细信息"""
        if command_name not in self._command_mapping:
            return None
        
        return {
            "function": self._command_mapping[command_name].__name__,
            "param_mapping": self._param_mapping.get(command_name, {}),
            "validation_rules": self._param_validation.get(command_name, {})
        }

    def add_command_mapping(self, command_name: str, function: Callable, 
                           param_mapping: dict = None, validation_rules: dict = None):
        """动态添加命令映射"""
        self._command_mapping[command_name] = function
        
        if param_mapping:
            self._param_mapping[command_name] = param_mapping
        
        if validation_rules:
            self._param_validation[command_name] = validation_rules
        
        logger = self.log_manager.get_logger(__name__)
        logger.info(f"已添加命令映射: {command_name}")

