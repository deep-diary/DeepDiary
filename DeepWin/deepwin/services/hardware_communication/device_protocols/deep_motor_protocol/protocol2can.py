# src/services/hardware_communication/device_protocols/deep_motor_protocol/protocol2can.py
# DeepMotor 设备协议的核心实现 - 优化版本，专注于CAN层接口

from __future__ import division, print_function, absolute_import

import struct
import logging
from typing import Dict, Any, List, Union, Optional
from deepwin.data_management.log_manager import LogManager

class Protocol2Can:
    """
    DeepMotor 通信协议实现 - 优化版本。
    专注于CAN层接口，返回CAN帧所需的参数：arbitration_id, data, is_extended_id
    """
    
    # 简化的协议配置
    _PROTOCOL_CONFIG = {
        "communication": {
            "use_uart2can": True
        },
        "protocol": {
            "master_id": 0x00fd
        },
        "motor": {
            "range": {
                "torque": [-10.0, 10.0], 
                "position": [-12.5, 12.5], 
                "velocity": [-65.0, 65.0],
                "kp": [0.0, 500.0], 
                "kd": [0.0, 5.0]
            },
            "modes": {
                "mit": 0, "position": 1, "velocity": 2, "torque": 3, "zero": 4, "jog": 7
            }
        },
        "index": {
            "RUN_MODE": 0x7005, "IQ_REF": 0x7006, "SPD_REF": 0x700A, "IMIT_TORQUE": 0x700B,
            "CUR_KP": 0x7010, "CUR_KI": 0x7011, "CUR_FILT_GAIN": 0x7014, "LOC_REF": 0x7016,
            "LIMIT_SPD": 0x7017, "LIMIT_CUR": 0x7018
        },
    }

    def __init__(self, log_manager: LogManager):
        """
        初始化协议对象。
        :param log_manager: 全局日志管理器实例。
        """
        self.logger = log_manager.get_logger(__name__)
        
        # 直接使用内联配置
        self.config = self._PROTOCOL_CONFIG 
        
        # 基本协议配置
        self.master_id = self.config.get('protocol', {}).get('master_id', 0x00fd)

        # 获取参数范围常量
        motor_range = self.config.get('motor', {}).get('range', {})
        self.T_MIN, self.T_MAX = motor_range.get('torque', [-10.0, 10.0])
        self.P_MIN, self.P_MAX = motor_range.get('position', [-12.5, 12.5])
        self.V_MIN, self.V_MAX = motor_range.get('velocity', [-65.0, 65.0])
        self.KP_MIN, self.KP_MAX = motor_range.get('kp', [0.0, 500.0])
        self.KD_MIN, self.KD_MAX = motor_range.get('kd', [0.0, 5.0])
        
        # 数据转换参数
        self.POSITION_RANGE = (-4 * 3.14159, 4 * 3.14159)  # -4π ~ 4π
        self.VELOCITY_RANGE = (-30, 30)                     # -30rad/s ~ 30rad/s
        self.TORQUE_RANGE = (-12, 12)                      # -12Nm ~ 12Nm

        # 电机参数索引
        self.index = self.config.get('index', {})
        
        # 运行模式
        self.modes = self.config.get('motor', {}).get('modes', {})
        
        self.logger.info("DeepMotor Protocol 初始化完成。")

    def _create_can_frame(self, mode: int, motor_id: int, res: int, data: int, payload: Optional[bytes] = None) -> Dict[str, Any]:
        """
        创建CAN帧参数
        
        Args:
            mode: 命令模式
            motor_id: 电机ID
            res: 保留字段
            data: 数据字段
            payload: 负载数据
            
        Returns:
            Dict[str, Any]: CAN帧参数 {arbitration_id, data, is_extended_id}
        """
        can_id = (res << 29) | (mode << 24) | (data << 8) | motor_id
        
        # 确保数据长度不超过8字节
        if payload is None:
            payload = bytes(8)  # 默认8字节
        elif len(payload) > 8:
            payload = payload[:8]  # 截断到8字节
        elif len(payload) < 8:
            payload = payload + bytes(8 - len(payload))  # 填充到8字节
        
        return {
            'arbitration_id': can_id,
            'data': bytes(payload),
            'is_extended_id': True
        }

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


    def decode_can_response(self, arbitration_id: int, data: bytes) -> Dict[str, Any]:
        """
        将接收到的CAN帧数据解码为响应数据（CAN帧格式）
        
        Args:
            arbitration_id: CAN仲裁ID
            data: CAN帧数据
            
        Returns:
            Dict[str, Any]: 解码后的响应数据
        """
        try:
            return self._decode_can_response(arbitration_id, data)
            
        except Exception as e:
            self.logger.error(f"解析CAN响应失败: {str(e)}, CAN ID: 0x{arbitration_id:X}, 数据: {data.hex()}")
            return {'success': False, 'error': f"解析CAN响应失败: {str(e)}"}

    def _decode_can_response(self, can_id: int, payload: bytes) -> Dict[str, Any]:
        """
        内部方法：解码CAN响应数据
        
        Args:
            can_id: CAN ID
            payload: CAN数据载荷
            
        Returns:
            Dict[str, Any]: 解码后的响应数据
        """
        ext_can_id_info = self._decode_ext_can_id(can_id)
        response_data = self._decode_can_data(payload)
        response_data.update(ext_can_id_info)
        
        # 根据故障信息设置 error_code
        error_code = 0
        if ext_can_id_info.get('flt_uninitialized', 0):
            error_code |= 0x01
        if ext_can_id_info.get('flt_hall_encoding', 0):
            error_code |= 0x02
        if ext_can_id_info.get('flt_magnetic_encoding', 0):
            error_code |= 0x04
        if ext_can_id_info.get('flt_over_temperature', 0):
            error_code |= 0x08
        if ext_can_id_info.get('flt_over_current', 0):
            error_code |= 0x10
        if ext_can_id_info.get('flt_voltage_drop', 0):
            error_code |= 0x20
        
        response_data['error_code'] = error_code
        response_data['success'] = True
        
        return response_data
        

    def _decode_ext_can_id(self, ext_can_id):
        """
        解析 CAN ID
        """
        response_mode = (ext_can_id >> 24) & 0xFF
        motor_can_id = (ext_can_id >> 8) & 0xFF  # Bit8~Bit15: 当前电机CANID
        fault_info = (ext_can_id >> 16) & 0x3F  # Bit21~Bit16: 故障信息
        mode_state = (ext_can_id >> 22) & 0x3  # Bit22~Bit23: 模式状态

        # Parse fault information
        faults = {
            "flt_uninitialized": (fault_info >> 5) & 0x1,
            "flt_hall_encoding": (fault_info >> 4) & 0x1,
            "flt_magnetic_encoding": (fault_info >> 3) & 0x1,
            "flt_over_temperature": (fault_info >> 2) & 0x1,
            "flt_over_current": (fault_info >> 1) & 0x1,
            "flt_voltage_drop": fault_info & 0x1
        }

        # 解析模式状态
        mode_states = {
            0: "ResetMode",
            1: "CaliMode",
            2: "RunMode"
        }
        ext_can_id_info = {
            "response_mode": response_mode,
            "motor_can_id": motor_can_id,
            "mode_state": mode_states[mode_state]
        }
        ext_can_id_info.update(faults)  # 更新故障信息

        # 记录
        self.logger.info(f"DeepMotorProtocol: 解析到 CAN ID: {ext_can_id_info}")


        return ext_can_id_info

    def _decode_can_data(self, data_bytes):
        """
        Update motor position
        
        Args:
            data_bytes: 8-byte feedback data
            
        Raises:
            ValueError: Incorrect data length
        """
        if len(data_bytes) != 8:
            raise ValueError("Feedback data must be 8 bytes")
            
        # Parse position data (Byte 0-1)
        position_raw = struct.unpack('>H', data_bytes[0:2])[0]
        position_raw = position_raw - 32767
        position = self._scale_value(position_raw, -32768, 32767,
                                                self.POSITION_RANGE[0],
                                                self.POSITION_RANGE[1])
        
        # Parse velocity data (Byte 2-3)
        velocity_raw = struct.unpack('>H', data_bytes[2:4])[0]
        velocity_raw = velocity_raw - 32767
        velocity = self._scale_value(velocity_raw, -32768, 32767,
                                               self.VELOCITY_RANGE[0],
                                               self.VELOCITY_RANGE[1])
        
        # Parse torque data (Byte 4-5)
        torque_raw = struct.unpack('>H', data_bytes[4:6])[0]
        torque_raw = torque_raw - 32767
        torque = self._scale_value(torque_raw, -32768, 32767,
                                             self.TORQUE_RANGE[0],
                                             self.TORQUE_RANGE[1])
        
        # Parse temperature data (Byte 6-7)
        temperature = struct.unpack('>H', data_bytes[6:8])[0]
        temperature = temperature / 10

        
        self.logger.debug("Position: %.2f, Velocity: %.2f, Torque: %.2f, Temperature: %.2f" % 
                         (position, velocity, torque, temperature))
        
        response_data = {
            'position': position,
            'velocity': velocity,
            'torque': torque,
            'temperature': temperature
        }
        return response_data
    
    def _scale_value(self, value, in_min, in_max, out_min, out_max):
        """
        Update motor temperature
        
        Args:
            value: Input value
            in_min: Input minimum value
            in_max: Input maximum value
            out_min: Output minimum value
            out_max: Output maximum value
            
        Returns:
            float: Mapped value
        """
        return (value - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

    # ==================== 核心命令方法 - 返回CAN帧参数 ====================

    def create_motor_enable_frame(self, motor_id: int) -> Dict[str, Any]:
        """
        创建电机使能CAN帧 (mode 3)
        
        Args:
            motor_id: 电机ID
            
        Returns:
            Dict[str, Any]: CAN帧参数 {arbitration_id, data, is_extended_id}
        """
        return self._create_can_frame(3, motor_id, 0, self.master_id)

    def create_motor_reset_frame(self, motor_id: int) -> Dict[str, Any]:
        """
        创建电机复位CAN帧 (mode 4)
        
        Args:
            motor_id: 电机ID
            
        Returns:
            Dict[str, Any]: CAN帧参数 {arbitration_id, data, is_extended_id}
        """
        return self._create_can_frame(4, motor_id, 0, self.master_id)

    def create_motor_zero_frame(self, motor_id: int) -> Dict[str, Any]:
        """
        创建电机零点设置CAN帧 (mode 6)
        
        Args:
            motor_id: 电机ID
            
        Returns:
            Dict[str, Any]: CAN帧参数 {arbitration_id, data, is_extended_id}
        """
        payload = bytearray([1, 1] + [0] * 6)  # 前两字节为1，其余为0
        return self._create_can_frame(6, motor_id, 0, self.master_id, payload)

    def create_motor_mode_frame(self, motor_id: int, run_mode: int) -> Dict[str, Any]:
        """
        创建电机模式设置CAN帧 (mode 0x12)
        
        Args:
            motor_id: 电机ID
            run_mode: 运行模式
            
        Returns:
            Dict[str, Any]: CAN帧参数 {arbitration_id, data, is_extended_id}
        """
        index = self.index['RUN_MODE']
        payload = bytearray(8)
        payload[0:2] = struct.pack('<H', index)  # 小端序
        payload[4] = run_mode
        return self._create_can_frame(0x12, motor_id, 0, self.master_id, payload)
    
    def create_motor_jog_frame(self, motor_id: int, jog_speed: float) -> Dict[str, Any]:
        """
        创建电机点动模式CAN帧 (mode 0x12)
        
        Args:
            motor_id: 电机ID
            jog_speed: 点动速度
            
        Returns:
            Dict[str, Any]: CAN帧参数 {arbitration_id, data, is_extended_id}
        """
        index = self.index['RUN_MODE']
        run_mode = self.modes.get('jog', 7)
        payload = bytearray(8)
        payload[0:2] = struct.pack('<H', index)
        payload[4] = run_mode
        payload[5] = 0x01  # 启用点动
        jog_speed = min(max(jog_speed, -30), 30)
        scaled_speed = int((jog_speed + 30) / 60 * 65535)
        payload[6:8] = struct.pack('>H', scaled_speed)
        return self._create_can_frame(0x12, motor_id, 0, self.master_id, payload)
    
    def create_motor_jog_stop_frame(self, motor_id: int) -> Dict[str, Any]:
        """
        创建电机点动停止CAN帧 (mode 0x12)
        
        Args:
            motor_id: 电机ID
            
        Returns:
            Dict[str, Any]: CAN帧参数 {arbitration_id, data, is_extended_id}
        """
        index = self.index['RUN_MODE']
        run_mode = self.modes.get('jog', 7)
        payload = bytearray(8)
        payload[0:2] = struct.pack('<H', index)
        payload[4] = run_mode
        payload[5] = 0x00  # 停止点动
        payload[6:8] = struct.pack('>H', 0x7fff)
        return self._create_can_frame(0x12, motor_id, 0, self.master_id, payload)
    
    def create_motor_write_frame(self, motor_id: int, index: int, value: float) -> Dict[str, Any]:
        """
        创建电机参数写入CAN帧 (mode 0x12)
        
        Args:
            motor_id: 电机ID
            index: 参数索引
            value: 参数值
            
        Returns:
            Dict[str, Any]: CAN帧参数 {arbitration_id, data, is_extended_id}
        """
        payload = bytearray(8)
        payload[0:2] = struct.pack('<H', index)
        payload[4:8] = struct.pack('<f', float(value))
        return self._create_can_frame(0x12, motor_id, 0, self.master_id, payload)
    
    def create_motor_read_frame(self, motor_id: int, index: int) -> Dict[str, Any]:
        """
        创建电机参数读取CAN帧 (mode 0x11)
        
        Args:
            motor_id: 电机ID
            index: 参数索引
            
        Returns:
            Dict[str, Any]: CAN帧参数 {arbitration_id, data, is_extended_id}
        """
        payload = bytearray(8)
        payload[0:2] = struct.pack('<H', index)
        return self._create_can_frame(0x11, motor_id, 0, self.master_id, payload)
    
    def create_motor_mit_mode_frame(self, motor_id: int, torque: float, position: float, speed: float, kp: float, kd: float) -> Dict[str, Any]:
        """
        创建电机MIT模式控制CAN帧 (mode 1)
        
        Args:
            motor_id: 电机ID
            torque: 扭矩值
            position: 目标位置
            speed: 目标速度
            kp: 位置环增益
            kd: 速度环增益
            
        Returns:
            Dict[str, Any]: CAN帧参数 {arbitration_id, data, is_extended_id}
        """
        data = self._float_to_uint(torque, self.T_MIN, self.T_MAX, 16)
        payload = bytearray(8)
        pos_uint = self._float_to_uint(position, self.P_MIN, self.P_MAX, 16)
        spd_uint = self._float_to_uint(speed, self.V_MIN, self.V_MAX, 16)
        kp_uint = self._float_to_uint(kp, self.KP_MIN, self.KP_MAX, 16)
        kd_uint = self._float_to_uint(kd, self.KD_MIN, self.KD_MAX, 16)
        
        payload[0:2] = struct.pack('<H', pos_uint)
        payload[2:4] = struct.pack('<H', spd_uint)
        payload[4:6] = struct.pack('<H', kp_uint)
        payload[6:8] = struct.pack('<H', kd_uint)
        
        return self._create_can_frame(1, motor_id, 0, data, payload)
    
    # ==================== 简化的控制方法 ====================
    
    def create_motor_pos_frame(self, motor_id: int, position: float) -> Dict[str, Any]:
        """
        创建电机位置控制CAN帧
        
        Args:
            motor_id: 电机ID
            position: 目标位置
            
        Returns:
            Dict[str, Any]: CAN帧参数 {arbitration_id, data, is_extended_id}
        """
        loc_index = self.index['LOC_REF']
        return self.create_motor_write_frame(motor_id, loc_index, position)
    
    def create_motor_spd_frame(self, motor_id: int, speed: float) -> Dict[str, Any]:
        """
        创建电机速度控制CAN帧
        
        Args:
            motor_id: 电机ID
            speed: 目标速度
            
        Returns:
            Dict[str, Any]: CAN帧参数 {arbitration_id, data, is_extended_id}
        """
        spd_index = self.index['LIMIT_SPD']
        return self.create_motor_write_frame(motor_id, spd_index, speed)

    def create_motor_torque_frame(self, motor_id: int, torque: float) -> Dict[str, Any]:
        """
        创建电机扭矩控制CAN帧
        
        Args:
            motor_id: 电机ID
            torque: 目标扭矩
            
        Returns:
            Dict[str, Any]: CAN帧参数 {arbitration_id, data, is_extended_id}
        """
        torque_index = self.index['LIMIT_CUR']
        return self.create_motor_write_frame(motor_id, torque_index, torque)
    
    # ==================== 多帧命令方法 ====================
    
    def create_motor_init_frame(self, motor_id: int) -> List[Dict[str, Any]]:
        """
        创建电机初始化多帧命令 (包括复位、零点设置、模式设置、使能)
        
        Args:
            motor_id: 电机ID
            
        Returns:
            List[Dict[str, Any]]: CAN帧参数列表，每个元素为 {arbitration_id, data, is_extended_id}
        """
        return [
            self.create_motor_reset_frame(motor_id),
            self.create_motor_zero_frame(motor_id),
            self.create_motor_mode_frame(motor_id, self.modes.get('position', 1)),
            self.create_motor_enable_frame(motor_id)
        ]
    
    def create_motor_init_frame_all(self, motor_ids: List[int]) -> List[Dict[str, Any]]:
        """
        创建多个电机的初始化多帧命令
        
        Args:
            motor_ids: 电机ID列表
            
        Returns:
            List[Dict[str, Any]]: 所有电机的初始化CAN帧参数列表
        """
        all_frames = []
        for motor_id in motor_ids:
            all_frames.extend(self.create_motor_init_frame(motor_id))
        return all_frames
