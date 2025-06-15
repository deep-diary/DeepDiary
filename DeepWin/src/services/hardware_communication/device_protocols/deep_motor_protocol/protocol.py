# src/services/hardware_communication/device_protocols/deep_motor_protocol/protocol.py
# DeepMotor 设备协议的核心实现

from __future__ import division, print_function, absolute_import

import struct
import logging
import sys
from typing import Dict, Any, List, Union, Optional

class DeepMotorProtocol:
    """
    DeepMotor 通信协议实现。
    提供 DeepMotor 无刷电机通信的协议处理功能，包括命令编码和响应解码。
    """
    
    # 协议配置
    _PROTOCOL_CONFIG = {
        "communication": {
            "start_byte": 0xAA,
            "end_byte": 0x55,
            "escape_byte": 0xCC,
            "max_packet_size": 128,
            "timeout": 1.0,
            "use_uart2can": True
        },
        "commands": {
            "motor_control": {"code": 0x01, "parameters": [{"name": "motor_id", "type": "uint8", "description": "电机ID"}, {"name": "angle", "type": "float", "description": "目标角度"}, {"name": "speed", "type": "uint16", "description": "转动速度"}]},
            "get_motor_status": {"code": 0x02, "parameters": [{"name": "motor_id", "type": "uint8", "description": "电机ID"}]},
            "system_reset": {"code": 0x03, "parameters": []},
            "read_sensor": {"code": 0x04, "parameters": [{"name": "sensor_id", "type": "uint8", "description": "传感器ID"}]}
        },
        "responses": {
            "ack": {"code": 0x80, "parameters": [{"name": "command_code", "type": "uint8", "description": "对应的命令代码"}, {"name": "status", "type": "uint8", "description": "状态码（0表示成功）"}]},
            "motor_status": {"code": 0x81, "parameters": [{"name": "motor_id", "type": "uint8", "description": "电机ID"}, {"name": "current_angle", "type": "float", "description": "当前角度"}, {"name": "current_speed", "type": "uint16", "description": "当前速度"}, {"name": "is_moving", "type": "bool", "description": "是否在运动"}]},
            "sensor_data": {"code": 0x82, "parameters": [{"name": "sensor_id", "type": "uint8", "description": "传感器ID"}, {"name": "sensor_value", "type": "float", "description": "传感器值"}]}
        },
        "error_codes": {
            0x00: "成功", 0x01: "命令未知", 0x02: "参数错误", 0x03: "执行失败", 0x04: "设备忙", 0x05: "超时", 0x06: "校验和错误", 0xFF: "未知错误"
        },
        "protocol": {
            "header": "AT",
            "end_bytes": "\r\n",
            "master_id": "0x00fd"
        },
        "motor": {
            "range": {
                "torque": [-10.0, 10.0], "position": [-12.5, 12.5], "velocity": [-65.0, 65.0],
                "kp": [0.0, 500.0], "kd": [0.0, 5.0],
                "joint1": [-3.2, 1.8], "joint2": [-2.4, 0.8], "joint3": [-0.5, 2.0],
                "joint4": [-1.4, 2.4], "joint5": [-1.3, 1.3], "joint6": [-3.14, 3.14]
            },
            "modes": {
                "mit": 0, "position": 1, "velocity": 2, "torque": 3, "zero": 4, "jog": 7
            }
        },
        "index": {
            "RUN_MODE": "0x7005", "IQ_REF": "0x7006", "SPD_REF": "0x700A", "IMIT_TORQUE": "0x700B",
            "CUR_KP": "0x7010", "CUR_KI": "0x7011", "CUR_FILT_GAIN": "0x7014", "LOC_REF": "0x7016",
            "LIMIT_SPD": "0x7017", "LIMIT_CUR": "0x7018", "ARM_LOC_X": "0x8000", "ARM_LOC_Y": "0x8001",
            "CAMERA_ERROR_X": "0x8010", "CAMERA_ERROR_Y": "0x8011", "CAMERA_H_ANGLE": "0x8012",
            "CAMERA_V_ANGLE": "0x8013", "CAMERA_TARGET_DETECTED": "0x8014"
        },
    }

    def __init__(self, log_manager: logging.Logger):
        """
        初始化协议对象。
        :param log_manager: 全局日志管理器实例。
        """
        self.logger = log_manager.get_logger("DeepMotorProtocol")
        
        # 直接使用内联配置
        self.config = self._PROTOCOL_CONFIG 
        
        # 基本协议配置
        protocol_config = self.config.get('protocol', {})
        self.AT_HEADER = protocol_config.get('header', 'AT').encode('ascii')
        self.END_BYTES = protocol_config.get('end_bytes', '\r\n').encode('ascii')
        self.master_id = int(protocol_config.get('master_id', '0x00fd'), 16)

        # 获取参数范围常量
        motor_range = self.config.get('motor', {}).get('range', {})
        self.T_MIN, self.T_MAX = motor_range.get('torque', [-10.0, 10.0])
        self.P_MIN, self.P_MAX = motor_range.get('position', [-12.5, 12.5])
        self.V_MIN, self.V_MAX = motor_range.get('velocity', [-65.0, 65.0])
        self.KP_MIN, self.KP_MAX = motor_range.get('kp', [0.0, 500.0])
        self.KD_MIN, self.KD_MAX = motor_range.get('kd', [0.0, 5.0])

        # 电机参数索引
        self.index = {}
        for key, value in self.config.get('index', {}).items():
            self.index[key] = int(value, 16)
        
        # 运行模式
        self.modes = self.config.get('motor', {}).get('modes', {})
        
        self.logger.info("DeepMotor Protocol 初始化完成。")

    def _create_frame(self, mode: int, motor_id: int, res: int, data: int, payload: Optional[bytes] = None) -> bytes:
        """
        创建通信帧
        
        Args:
            mode: 命令模式
            motor_id: 电机ID
            res: 保留字段
            data: 数据字段
            payload: 负载数据
            
        Returns:
            bytes: 完整的通信帧
        """
        can_id = (res << 29) | (mode << 24) | (data << 8) | motor_id
        if self.config.get('communication', {}).get('use_uart2can', False):
            can_id = (can_id << 3) + 0x04  # 如果需要使用 USB 转 CAN 模块，需要进行转换
        
        frame = bytearray()
        frame.extend(self.AT_HEADER)
        frame.extend(struct.pack('>I', can_id))
        
        if payload:
            frame.append(len(payload))
            frame.extend(payload)
        else:
            frame.append(0)
        
        frame.extend(self.END_BYTES)
        return bytes(frame)

    def _float_to_uint(self, x: float, x_min: float, x_max: float, bits: int) -> int:
        """
        将浮点数转换为无符号整数
        """
        span = x_max - x_min
        offset = x_min
        x = min(max(x, x_min), x_max)
        return int((x - offset) * ((1 << bits) - 1) / span)

    def _uint_to_float(self, uint: int, x_min: float, x_max: float, bits: int) -> float:
        """
        将无符号整数转换为浮点数
        """
        span = x_max - x_min
        offset = x_min
        return uint * span / ((1 << bits) - 1) + offset

    def _limit_position(self, motor_id: int, position: float) -> float:
        """
        限制电机位置在预设范围内
        """
        joint_name = 'joint' + str(motor_id)
        joint_range = self.config.get('motor', {}).get('range', {}).get(joint_name, [-0.5, 0.5])
        position = min(max(position, joint_range[0]), joint_range[1])
        return position

    def encode_command(self, command_type: str, **kwargs) -> Union[bytes, List[bytes]]:
        """
        将命令类型和参数编码为底层协议命令。
        :param command_type: 命令类型。
        :param kwargs: 命令参数字典。
        :return: 编码后的命令字节或命令字节列表。
        """
        self.logger.debug(f"DeepMotorProtocol: 编码命令 '{command_type}' 参数: {kwargs}")
        
        try:
            if command_type == 'enable_motor':
                motor_id = kwargs.get('motor_id', 1)
                return self._create_frame(3, motor_id, 0, self.master_id)
            elif command_type == 'disable_motor':  # 添加失能电机命令
                motor_id = kwargs.get('motor_id', 1)
                return self._create_frame(0x02, motor_id, 0, self.master_id)
            elif command_type == 'reset_motor':
                motor_id = kwargs.get('motor_id', 1)
                return self._create_frame(4, motor_id, 0, self.master_id)
            elif command_type == 'zero_motor':
                motor_id = kwargs.get('motor_id', 1)
                payload = bytearray([0] * 8)
                payload[0] = 1
                payload[1] = 1
                return self._create_frame(6, motor_id, 0, self.master_id, payload)
            elif command_type == 'set_motor_mode':
                motor_id = kwargs.get('motor_id', 1)
                value = kwargs.get('value')
                return self._create_frame(0x12, motor_id, 0, self.master_id, struct.pack('<H', self.index['RUN_MODE']) + struct.pack('<B', value))
            elif command_type == 'set_motor_mit_mode':
                motor_id = kwargs.get('motor_id', 1)
                torque = kwargs.get('torque', 0.0)
                position = kwargs.get('position', 0.0)
                speed = kwargs.get('speed', 0.0)
                kp = kwargs.get('kp', 0.0)
                kd = kwargs.get('kd', 0.0)
                data_val = self._float_to_uint(torque, self.T_MIN, self.T_MAX, 16)
                payload = bytearray(8)
                pos_uint = self._float_to_uint(position, self.P_MIN, self.P_MAX, 16)
                spd_uint = self._float_to_uint(speed, self.V_MIN, self.V_MAX, 16)
                kp_uint = self._float_to_uint(kp, self.KP_MIN, self.KP_MAX, 16)
                kd_uint = self._float_to_uint(kd, self.KD_MIN, self.KD_MAX, 16)
                payload[0:2] = struct.pack('<H', pos_uint)
                payload[2:4] = struct.pack('<H', spd_uint)
                payload[4:6] = struct.pack('<H', kp_uint)
                payload[6:8] = struct.pack('<H', kd_uint)
                return self._create_frame(1, motor_id, 0, data_val, payload)
            elif command_type == 'write_motor_param':
                motor_id = kwargs.get('motor_id', 1)
                index = kwargs.get('index')
                value = kwargs.get('value')
                if index is None or value is None:
                    raise ValueError("write_motor_param 命令必须提供 'index' 和 'value' 参数")
                if isinstance(index, str):
                    index = self.index.get(index)
                    if index is None:
                        raise ValueError("未知的索引名称: %s" % index)
                payload = bytearray(8)
                payload[0:2] = struct.pack('<H', index)
                payload[4:8] = struct.pack('<f', float(value))
                return self._create_frame(0x12, motor_id, 0, self.master_id, payload)
            elif command_type == 'read_motor_param':
                motor_id = kwargs.get('motor_id', 1)
                index = kwargs.get('index')
                if index is None:
                    raise ValueError("read_motor_param 命令必须提供 'index' 参数")
                if isinstance(index, str):
                    index = self.index.get(index)
                    if index is None:
                        raise ValueError("未知的索引名称: %s" % index)
                payload = bytearray(8)
                payload[0:2] = struct.pack('<H', index)
                return self._create_frame(0x11, motor_id, 0, self.master_id, payload)
            elif command_type == 'jog_motor':
                motor_id = kwargs.get('motor_id', 1)
                speed = kwargs.get('speed', 0)
                index_run_mode = self.index['RUN_MODE']
                run_mode = self.modes.get('jog', 7)
                payload = bytearray(8)
                payload[0:2] = struct.pack('<H', index_run_mode)
                payload[4] = run_mode
                payload[5] = 0x01  # 1: 启用 jog
                speed = min(max(speed, -30), 30)
                scaled_speed = int((speed + 30) / 60 * 65535)
                payload[6:8] = struct.pack('>H', scaled_speed)
                return self._create_frame(0x12, motor_id, 0, self.master_id, payload)
            elif command_type == 'stop_jog_motor':
                motor_id = kwargs.get('motor_id', 1)
                index_run_mode = self.index['RUN_MODE']
                run_mode = self.modes.get('jog', 7)
                payload = bytearray(8)
                payload[0:2] = struct.pack('<H', index_run_mode)
                payload[4] = run_mode
                payload[5] = 0x00  # 0: 禁用 jog
                payload[6:8] = struct.pack('>H', 0x7fff) # 将速度设置为中间值以有效停止
                return self._create_frame(0x12, motor_id, 0, self.master_id, payload)
            elif command_type == 'init_motor':
                motor_id = kwargs.get('motor_id', 1)
                frames = [
                    self.AT_HEADER + b'+AT' + self.END_BYTES,
                    self._create_frame(4, motor_id, 0, self.master_id), # Reset
                    self._create_frame(6, motor_id, 0, self.master_id, bytearray([1, 1, 0, 0, 0, 0, 0, 0])), # Zero
                    self._create_frame(3, motor_id, 0, self.master_id), # Enable
                    self.encode_command('set_motor_mode', motor_id=motor_id, value=self.modes.get('position', 1)) # Set Position Mode
                ]
                return frames
            elif command_type == 'init_all_motors':
                motor_ids = kwargs.get('motor_ids', [])
                frames = []
                for motor_id in motor_ids:
                    frames.extend(self.encode_command('init_motor', motor_id=motor_id))
                return frames
            elif command_type == 'reset_all_motors':
                motor_ids = kwargs.get('motor_ids', [])
                return [self._create_frame(4, motor_id, 0, self.master_id) for motor_id in motor_ids]
            elif command_type == 'set_motor_position':
                motor_id = kwargs.get('motor_id', 1)
                position = kwargs.get('position')
                if position is None: raise ValueError("set_motor_position 命令需要 'position' 参数。")
                loc_index = self.index['LOC_REF']
                limited_position = self._limit_position(motor_id, position)
                return self.encode_command('write_motor_param', motor_id=motor_id, index=loc_index, value=limited_position)
            elif command_type == 'set_all_motors_position':
                motor_ids = kwargs.get('motor_ids', [])
                positions = kwargs.get('positions', [])
                if len(motor_ids) != len(positions):
                    raise ValueError("电机ID和位置列表长度必须匹配。")
                frames = []
                for i, motor_id in enumerate(motor_ids):
                    frames.append(self.encode_command('set_motor_position', motor_id=motor_id, position=positions[i]))
                return frames
            elif command_type == 'set_motor_pos_speed':
                motor_id = kwargs.get('motor_id', 1)
                position = kwargs.get('position')
                speed = kwargs.get('speed')
                if position is None or speed is None: raise ValueError("set_motor_pos_speed 命令需要 'position' 和 'speed' 参数。")
                loc_index = self.index['LOC_REF']
                spd_index = self.index['LIMIT_SPD']
                limited_position = self._limit_position(motor_id, position)
                position_frame = self.encode_command('write_motor_param', motor_id=motor_id, index=loc_index, value=limited_position)
                speed_frame = self.encode_command('write_motor_param', motor_id=motor_id, index=spd_index, value=speed)
                return [position_frame, speed_frame]
            elif command_type == 'set_all_motors_pos_speed':
                motor_ids = kwargs.get('motor_ids', [])
                positions = kwargs.get('positions', [])
                speeds = kwargs.get('speeds', [])
                if not (len(motor_ids) == len(positions) == len(speeds)):
                    raise ValueError("电机ID、位置和速度列表长度必须匹配。")
                frames = []
                for i, motor_id in enumerate(motor_ids):
                    frames.extend(self.encode_command('set_motor_pos_speed', motor_id=motor_id, position=positions[i], speed=speeds[i]))
                return frames
            else:
                raise ValueError(f"不支持的命令类型: {command_type}")
        except Exception as e:
            raise ValueError(f"编码命令 '{command_type}' 失败: {e}")

    def decode_response(self, data: bytes) -> Dict[str, Any]:
        """
        将接收到的字节序列解码为响应数据
        
        Args:
            data: 接收到的字节序列
            
        Returns:
            Dict[str, Any]: 解码后的响应数据
        """
        try:
            if not data or len(data) < len(self.AT_HEADER) + 4 + 1 + len(self.END_BYTES):
                self.logger.debug(f"Received data too short or incomplete: {data.hex()}")
                return {'success': False, 'error': "无效的数据帧格式"}
            
            # 检查帧头和帧尾
            if not data.startswith(self.AT_HEADER) or not data.endswith(self.END_BYTES):
                self.logger.debug(f"Invalid frame header or end bytes. Raw: {data.hex()}")
                return {'success': False, 'error': "无效的帧头或帧尾"}
            
            offset = len(self.AT_HEADER)
            can_id_bytes = data[offset : offset + 4]
            can_id = struct.unpack('>I', can_id_bytes)[0]

            # 如果使用 USB 转 CAN 模块，需要进行转换
            if self.config.get('uart', {}).get('use_uart2can', False):
                can_id = can_id >> 3

            offset += 4
            data_length = data[offset]
            offset += 1
            payload = data[offset : offset + data_length]
            
            response_mode = (can_id >> 24) & 0xFF
            motor_id = (can_id >> 8) & 0xFF
            
            response_data = {
                'success': True,
                'motor_id': motor_id,
                'mode': response_mode,
                'data': can_id & 0xFF,
                'raw_payload': payload
            }
            
            # 根据不同的响应模式处理数据
            if response_mode == 0x11:  # 读取参数响应
                if len(payload) >= 8:
                    index = struct.unpack('<H', payload[0:2])[0]
                    value = struct.unpack('<f', payload[4:8])[0]
                    response_data['index'] = index
                    response_data['value'] = value
                    
                    # 尝试查找索引对应的名称
                    for name, idx in self.index.items():
                        if idx == index:
                            response_data['index_name'] = name
                            break
                    
                    return response_data
                else:
                    return {'success': False, 'error': "读取响应数据不完整"}
            
            elif response_mode == 0x19:  # 状态响应
                if len(payload) >= 8:
                    position_raw = struct.unpack('>H', payload[0:2])[0]
                    position = (position_raw - 32767) * (self.P_MAX - self.P_MIN) / (32767 - (-32768)) + self.P_MIN

                    velocity_raw = struct.unpack('>H', payload[2:4])[0]
                    velocity = (velocity_raw - 32767) * (self.V_MAX - self.V_MIN) / (32767 - (-32768)) + self.V_MIN

                    torque_raw = struct.unpack('>H', payload[4:6])[0]
                    torque = (torque_raw - 32767) * (self.T_MAX - self.T_MIN) / (32767 - (-32768)) + self.T_MIN
                    
                    temperature = struct.unpack('>H', payload[6:8])[0] / 10

                    response_data.update({
                        'current_position': position,
                        'current_velocity': velocity,
                        'current_torque': torque,
                        'current_temperature': temperature
                    })
                    return response_data
                else:
                    return {'success': False, 'error': "状态响应数据不完整"}
            
            # 对于其他响应模式，只返回基本信息
            return response_data
            
        except Exception as e:
            self.logger.error(f"解析响应失败: {str(e)}, 原始数据: {data.hex()}")
            return {'success': False, 'error': f"解析响应失败: {str(e)}"}

