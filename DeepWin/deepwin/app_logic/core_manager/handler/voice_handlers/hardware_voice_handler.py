# hardware_voice_handler.py
# 硬件控制语音处理器，专门处理电机、机械臂等硬件设备的语音指令

from typing import Dict, Any, List
from .base_voice_handler import BaseVoiceHandler
from deepwin.app_logic.device_logic_manager.devices.deep_motor.command_parser import CommandParser
DEFAULT_MOTOR_ID = 255

class HardwareVoiceHandler(BaseVoiceHandler):
    """硬件控制语音处理器"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._default_pos_step = 0.1
        self.motor_cmd_parser = CommandParser()
        
        
    def _validate_dependencies(self):
        super()._validate_dependencies()
        if not self.device_logic_manager:
            raise ValueError("缺少必需的依赖项: device_logic_manager")
            
        try:
            self._default_pos_step = self.config_manager.get(
                'device_settings.deepmotor_default_pos_step', 0.1
            )
        except Exception as e:
            self.logger.warning(f"读取默认位置步长配置失败，使用默认值0.1: {e}")
            self._default_pos_step = 0.1
            
    def _register_command_handlers(self):
        # 电机控制命令
        self.supported_commands.extend([
            'motor_set_pos', 'motor_increase_pos', 'motor_decrease_pos',
            'motor_increase_pos_default', 'motor_decrease_pos_default',
            'motor_set_speed', 'motor_start', 'motor_stop', 'motor_reset'
        ])
        
        # 机械臂控制命令
        self.supported_commands.extend([
            'arm_move_to', 'arm_grab', 'arm_release', 'arm_home',
            'arm_set_speed', 'arm_stop', 'arm_reset'
        ])
        
        # 玩具控制命令
        self.supported_commands.extend([
            'toy_activate', 'toy_deactivate', 'toy_set_mode', 'toy_reset'
        ])
        
        # 注册命令处理器
        self.command_handlers.update({
            'motor_set_pos': self._handle_motor_set_pos,
            'motor_increase_pos': self._handle_motor_increase_pos,
            'motor_decrease_pos': self._handle_motor_decrease_pos,
            'motor_increase_pos_default': self._handle_motor_increase_pos_default,
            'motor_decrease_pos_default': self._handle_motor_decrease_pos_default,
            'motor_set_speed': self._handle_motor_set_speed,
            'motor_start': self._handle_motor_start,
            'motor_stop': self._handle_motor_stop,
            'motor_reset': self._handle_motor_reset,
        })
        
        
    def _handle_motor_set_pos(self, params: List[Dict[str, Any]]) -> bool:
        command_name, params_valid = self.motor_cmd_parser.parse_command_dashscope(params)
        if params_valid['motor_id'] == DEFAULT_MOTOR_ID:
            params_valid['motor_id'] = self._get_current_motor_id()
        self.device_logic_manager.send_device_abstract_command_requested.emit('DeepMotor', command_name, params_valid)
        return True
        
    def _handle_motor_increase_pos(self, params: List[Dict[str, Any]]) -> bool:
        command_name, params_valid = self.motor_cmd_parser.parse_command_dashscope(params)
        current_pos = self._get_current_position(params_valid['motor_id'])
        params_valid['pos'] = current_pos + params_valid['pos']

        if params_valid['motor_id'] == DEFAULT_MOTOR_ID:
            params_valid['motor_id'] = self._get_current_motor_id()
        self.device_logic_manager.send_device_abstract_command_requested.emit('DeepMotor', 'motor_set_pos', params_valid)
        return True
        
    def _handle_motor_decrease_pos(self, params: List[Dict[str, Any]]) -> bool:
        command_name, params_valid = self.motor_cmd_parser.parse_command_dashscope(params)
        current_pos = self._get_current_position(params_valid['motor_id'])
        params_valid['pos'] = current_pos - params_valid['pos']
        if params_valid['motor_id'] == DEFAULT_MOTOR_ID:
            params_valid['motor_id'] = self._get_current_motor_id()
        self.device_logic_manager.send_device_abstract_command_requested.emit('DeepMotor', 'motor_set_pos', params_valid)
        return True
        
    def _handle_motor_increase_pos_default(self, params: List[Dict[str, Any]]) -> bool:
        command_name, params_valid = self.motor_cmd_parser.parse_command_dashscope(params)
        current_pos = self._get_current_position(params_valid['motor_id'])
        params_valid['pos'] = current_pos + self._default_pos_step
        if params_valid['motor_id'] == DEFAULT_MOTOR_ID:
            params_valid['motor_id'] = self._get_current_motor_id()
        self.device_logic_manager.send_device_abstract_command_requested.emit('DeepMotor', 'motor_set_pos', params_valid)
        return True
        
    def _handle_motor_decrease_pos_default(self, params: List[Dict[str, Any]]) -> bool:
        command_name, params_valid = self.motor_cmd_parser.parse_command_dashscope(params)
        current_pos = self._get_current_position(params_valid['motor_id'])
        params_valid['pos'] = current_pos - self._default_pos_step
        if params_valid['motor_id'] == DEFAULT_MOTOR_ID:
            params_valid['motor_id'] = self._get_current_motor_id()
        self.device_logic_manager.send_device_abstract_command_requested.emit('DeepMotor', 'motor_set_pos', params_valid)
        return True
        
    def _handle_motor_set_speed(self, params: List[Dict[str, Any]]) -> bool:
        command_name, params_valid = self.motor_cmd_parser.parse_command_dashscope(params)
        if params_valid['motor_id'] == DEFAULT_MOTOR_ID:
            params_valid['motor_id'] = self._get_current_motor_id()
        self.device_logic_manager.send_device_abstract_command_requested.emit('DeepMotor', 'motor_set_speed', params_valid)
        return True
        
    def _handle_motor_start(self, params: List[Dict[str, Any]]) -> bool:
        command_name, params_valid = self.motor_cmd_parser.parse_command_dashscope(params)
        self.device_logic_manager.send_device_abstract_command_requested.emit('DeepMotor', 'motor_start', params_valid)
        return True
        
    def _handle_motor_stop(self, params: List[Dict[str, Any]]) -> bool:
        command_name, params_valid = self.motor_cmd_parser.parse_command_dashscope(params)
        self.device_logic_manager.send_device_abstract_command_requested.emit('DeepMotor', 'motor_stop', params_valid)
        return True
        
    def _handle_motor_reset(self, params: List[Dict[str, Any]]) -> bool:
        command_name, params_valid = self.motor_cmd_parser.parse_command_dashscope(params)
        self.device_logic_manager.send_device_abstract_command_requested.emit('DeepMotor', 'motor_reset', params_valid)
        return True
        
    def _get_current_position(self, motor_id: int) -> float:
        try:
            motor_device = self.device_logic_manager.get_device_by_id('DeepMotor')
            return motor_device.get_parameter_statistics('position')['latest']
        except Exception as e:
            self.logger.warning(f"获取电机 {motor_id} 当前位置失败，使用默认值0: {e}")
            return 0.0
        
    def _get_current_motor_id(self) -> int:
        try:
            motor_device = self.device_logic_manager.get_device_by_id('DeepMotor')
            return motor_device.get_parameter_statistics('motor_id')['latest']
        except Exception as e:
            self.logger.warning(f"获取电机ID失败，使用默认值1: {e}")
            return 1
        