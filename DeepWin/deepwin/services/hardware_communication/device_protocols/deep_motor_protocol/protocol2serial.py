# src/services/hardware_communication/device_protocols/deep_motor_protocol/protocol2serial.py
# DeepMotor 设备协议的核心实现 - 串口版本

from __future__ import division, print_function, absolute_import

import struct
import logging
from typing import Dict, Any, List, Union, Optional
from deepwin.data_management.log_manager import LogManager

class Protocol2Serial:
    """
    DeepMotor 通信协议实现 - 串口版本。
    提供 DeepMotor 无刷电机通信的协议处理功能，专注于串口帧格式。
    """
    
    # 简化的协议配置
    _PROTOCOL_CONFIG = {
        "communication": {
            "use_uart2can": True
        },
        "protocol": {
            "header": "AT",
            "end_bytes": "\r\n",
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
        protocol_config = self.config.get('protocol', {})
        self.AT_HEADER = protocol_config.get('header', 'AT').encode('ascii')
        self.END_BYTES = protocol_config.get('end_bytes', '\r\n').encode('ascii')
        self.master_id = protocol_config.get('master_id', 0x00fd)

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
        
        self.logger.info("DeepMotor Protocol2Serial 初始化完成。")

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


    def decode_response(self, data: bytes) -> Dict[str, Any]:
        """
        将接收到的字节序列解码为响应数据
        
        Args:
            data: 接收到的字节序列
            
        Returns:
            Dict[str, Any]: 解码后的响应数据
        """
        try:
            can_id, payload = self._ser2can(data)
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
            
            # 对于其他响应模式，只返回基本信息
            return response_data
            
        except Exception as e:
            self.logger.error(f"解析响应失败: {str(e)}, 原始数据: {data.hex()}")
            return {'success': False, 'error': f"解析响应失败: {str(e)}"}
        
    def _ser2can(self, frame_bytes: bytes):
        """
        将串口数据解析为 CAN 帧组件。
        """
        # 解析CAN ID（4字节），先向右移3位, 具体根据协议决定
        arbitration_id = int.from_bytes(frame_bytes[0:4], byteorder='big')

        # 如果使用 USB 转 CAN 模块，需要进行转换
        if self.config.get('communication', {}).get('use_uart2can', True):
            arbitration_id = arbitration_id >> 3
        
        # 解析数据长度（1字节）
        data_length = frame_bytes[4]
        
        # 检查数据长度是否合理
        if data_length > 8:  # CAN 2.0 标准帧最大数据长度为8字节
            self.logger.warning(f"DeepMotorProtocol: 数据长度超出范围: {data_length}")
            return

        # 检查接收到的数据长度是否足够
        expected_length = 5 + data_length  # 5 = 4(CANID) + 1(Len)
        if len(frame_bytes) < expected_length:
            self.logger.warning(f"DeepMotorProtocol: 数据不完整，期望 {expected_length} 字节，实际 {len(frame_bytes)} 字节")
            return

        # 提取数据部分
        data_bytes = frame_bytes[5:5+data_length]


        # # 假设所有 CAN ID 都是标准 ID (非扩展 ID)，实际项目中需要根据 CANID 范围判断
        # is_extended_id = True

        self.logger.info(f"DeepMotorProtocol: 解析到 CAN 帧: ID=0x{arbitration_id:X}, Len={data_length}, Data={data_bytes.hex()}")
        # 发射解析后的 CAN 帧组件，CanBusCommunicator 将会接收并进一步处理
        return arbitration_id, data_bytes

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

    def create_AT_frame(self):
        """创建AT测试帧"""
        frame = [0x41, 0x54, 0x2B, 0x41, 0x54, 0x0D, 0x0A]
        return frame

    def create_motor_enable_frame(self, motor_id):
        """
        Create a motor enable frame (mode 3)
        
        Args:
            motor_id: Motor ID
            
        Returns:
            bytearray: Communication frame
        """
        return self._create_frame(3, motor_id, 0, self.master_id)

    def create_motor_reset_frame(self, motor_id):
        """
        Create a motor reset frame (mode 4)
        
        Args:
            motor_id: Motor ID
            
        Returns:
            bytearray: Communication frame
        """
        return self._create_frame(4, motor_id, 0, self.master_id)

    def create_motor_zero_frame(self, motor_id):
        """
        Create a motor zero frame (mode 6)
        
        Args:
            motor_id: Motor ID
            
        Returns:
            bytearray: Communication frame
        """
        payload = bytearray([0] * 8)
        payload[0] = 1
        payload[1] = 1
        return self._create_frame(6, motor_id, 0, self.master_id, payload)

    def create_motor_mode_frame(self, motor_id, run_mode):
        """
        Create a motor mode setting frame (mode 0x12)
        
        Args:
            motor_id: Motor ID
            index: Parameter index
            run_mode: Operating mode
            
        Returns:
            bytearray: Communication frame
        """
        index = self.index['RUN_MODE']
        payload = bytearray(8)
        payload[0:2] = [index & 0xFF, (index >> 8) & 0xFF]
        payload[4] = run_mode
        return self._create_frame(0x12, motor_id, 0, self.master_id, payload)
    
    def create_motor_jog_frame(self, motor_id, jog_speed):
        """
        Create a motor jog mode setting frame (mode 0x12)
        
        Args:
            motor_id: Motor ID
            jog_speed: Jog speed
            
        Returns:
            bytearray: Communication frame
        """
        index = self.index['RUN_MODE']    # write
        run_mode = self.modes.get('jog', 7)  # jog mode
        payload = bytearray(8)
        payload[0:2] = struct.pack('<H', index)
        payload[4] = run_mode
        payload[5] = 0x01  # 1: enable jog, 0: disable jog
        jog_speed = min(max(jog_speed, -30), 30)
        scaled_speed = int((jog_speed + 30) / 60 * 65535)
        payload[6:8] = struct.pack('>H', scaled_speed)
        return self._create_frame(0x12, motor_id, 0, self.master_id, payload)
    
    def create_motor_jog_stop_frame(self, motor_id):
        """
        Create a motor jog mode stop frame (mode 0x12)
        
        Args:
            motor_id: Motor ID
            
        Returns:
            bytearray: Communication frame
        """
        index = self.index['RUN_MODE']    # write
        run_mode = self.modes.get('jog', 7)  # jog mode
        payload = bytearray(8)
        payload[0:2] = struct.pack('<H', index)
        payload[4] = run_mode
        payload[5] = 0x00  # 1: enable jog, 0: disable jog
        payload[6:8] = struct.pack('>H', 0x7fff)
        return self._create_frame(0x12, motor_id, 0, self.master_id, payload)
    
    def create_motor_write_frame(self, motor_id, index, value):
        """
        Create a motor parameter write frame (mode 0x12)
        
        Args:
            motor_id: Motor ID
            index: Parameter index
            value: Parameter value
            
        Returns:
            bytearray: Communication frame
        """
        payload = bytearray(8)
        payload[0:2] = struct.pack('<H', index)
        payload[4:8] = struct.pack('<f', float(value))
        return self._create_frame(0x12, motor_id, 0, self.master_id, payload)
    
    def create_motor_read_frame(self, motor_id, index):
        """
        Create a motor parameter read frame (mode 0x11)
        
        Args:
            motor_id: Motor ID
            index: Parameter index
            
        Returns:
            bytearray: Communication frame
        """
        payload = bytearray(8)
        payload[0:2] = struct.pack('<H', index)
        return self._create_frame(0x11, motor_id, 0, self.master_id, payload)
    
    def create_motor_mit_mode_frame(self, motor_id, torque, position, speed, kp, kd):
        """
        Create a motor MIT mode control frame (mode 1)
        
        Args:
            motor_id: Motor ID
            torque: Torque value
            position: Target position
            speed: Target speed
            kp: Position loop gain
            kd: Velocity loop gain
            
        Returns:
            bytearray: Communication frame
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
        
        return self._create_frame(1, motor_id, 0, data, payload)
    
    
    # ==================== 简化的控制方法 ====================
    
    def create_motor_pos_frame(self, motor_id, position):
        """创建电机位置控制串口帧"""
        loc_index = self.index['LOC_REF']
        return self.create_motor_write_frame(motor_id, loc_index, position)
    
    def create_motor_spd_frame(self, motor_id, speed):
        """创建电机速度控制串口帧"""
        spd_index = self.index['LIMIT_SPD']
        return self.create_motor_write_frame(motor_id, spd_index, speed)

    def create_motor_torque_frame(self, motor_id, torque):
        """创建电机扭矩控制串口帧"""
        torque_index = self.index['LIMIT_CUR']
        return self.create_motor_write_frame(motor_id, torque_index, torque)
    
    # ==================== 多帧命令方法 ====================
    
    def create_motor_init_frame(self, motor_id):
        """
        创建电机初始化多帧命令 (包括复位、零点设置、模式设置、使能)
        
        Args:
            motor_id: 电机ID
            
        Returns:
            list: 串口帧列表
        """
        return [
            self.create_motor_reset_frame(motor_id),
            self.create_motor_zero_frame(motor_id),
            self.create_motor_mode_frame(motor_id, self.modes.get('position', 1)),
            self.create_motor_enable_frame(motor_id)
        ]
    
    def create_motor_init_frame_all(self, motor_ids):
        """
        创建多个电机的初始化多帧命令
        
        Args:
            motor_ids: 电机ID列表
            
        Returns:
            list: 所有电机的初始化串口帧列表
        """
        all_frames = []
        for motor_id in motor_ids:
            all_frames.extend(self.create_motor_init_frame(motor_id))
        return all_frames
    

