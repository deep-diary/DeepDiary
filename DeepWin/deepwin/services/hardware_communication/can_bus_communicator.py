# src/services/hardware_communication/can_bus_communicator.py
# CAN 总线通信模块 - 专注于串口转CAN逻辑

import time
from PySide6.QtCore import QObject, Signal, Slot
from typing import Dict, Any, List, Optional
from collections import deque

from deepwin.data_management.log_manager import LogManager
from deepwin.config.config_manager import ConfigManager


class CanBusCommunicator(QObject):
    """
    CAN 总线通信模块 - 专注于串口转CAN逻辑。
    负责：
    1. 串口数据转CAN帧 (ser2can)
    2. CAN帧转串口数据 (can2ser) 
    3. CAN帧列表管理（发送和接收）
    
    注意：此模块不处理DBC解析和端口映射，这些应该在更高层处理。
    """
    # CAN帧相关信号
    can_frame_received = Signal(int, bytes, bool)       # 收到CAN帧: (arbitration_id, data_bytes, is_extended_id)
    can_frame_sent = Signal(int, bytes, bool)           # 发送CAN帧: (arbitration_id, data_bytes, is_extended_id)
    
    # 串口数据相关信号
    serial_data_to_send = Signal(bytes)                 # 需要发送的串口数据: (data_bytes)
    
    # 帧列表管理信号
    can_frame_lists_updated = Signal()                  # CAN帧列表更新信号
    
    # 错误信号
    can_error = Signal(str)                             # CAN错误: (error_msg)

    def __init__(self, log_manager: LogManager, config_manager: ConfigManager, parent: Optional[QObject] = None):
        """
        初始化 CanBusCommunicator。
        :param log_manager: 全局日志管理器实例。
        :param config_manager: 全局配置管理器实例。
        :param parent: QObject 父对象。
        """
        super().__init__(parent)
        self.logger = log_manager.get_logger(__name__)
        self.config_manager = config_manager
        self.logger.info("CanBusCommunicator: 初始化中...")
        
        # CAN帧列表管理
        self._max_can_frame_list_size = 1000  # 默认最大CAN帧列表长度
        self._sent_can_frames: deque = deque(maxlen=self._max_can_frame_list_size)  # 发送的CAN帧列表
        self._received_can_frames: deque = deque(maxlen=self._max_can_frame_list_size)  # 接收的CAN帧列表
        
        self.logger.info("CanBusCommunicator: 初始化完成。")


    @Slot(bytes)
    def process_serial_data(self, data: bytes) -> Optional[Dict[str, Any]]:
        """
        处理从串口接收的原始数据，转换为CAN帧。
        数据格式: CANID(4字节) + Len(1字节) + Data(N字节)
        :param data: 原始串口数据
        :return: CAN帧数据字典，失败时返回None
        """
        self.logger.debug(f"CanBusCommunicator: 收到串口原始数据: {data.hex()}")
        
        # 检查数据长度是否足够（至少需要5字节：4字节CANID + 1字节长度）
        if len(data) < 5:
            self.logger.warning(f"CanBusCommunicator: 串口数据长度不足: {len(data)} 字节")
            return None

        try:
            # 解析CAN ID（4字节），先向右移3位
            arbitration_id = int.from_bytes(data[0:4], byteorder='big') >> 3
            
            # 解析数据长度（1字节）
            data_length = data[4]
            
            # 检查数据长度是否合理
            if data_length > 8:  # CAN 2.0 标准帧最大数据长度为8字节
                self.logger.warning(f"CanBusCommunicator: 数据长度超出范围: {data_length}")
                return None

            # 检查接收到的数据长度是否足够
            expected_length = 5 + data_length  # 5 = 4(CANID) + 1(Len)
            if len(data) < expected_length:
                self.logger.warning(f"CanBusCommunicator: 数据不完整，期望 {expected_length} 字节，实际 {len(data)} 字节")
                return None

            # 提取数据部分
            data_bytes = data[5:5+data_length]
            
            # 假设所有 CAN ID 都是扩展 ID
            is_extended_id = True

            self.logger.info(f"CanBusCommunicator: 解析到 CAN 帧: ID=0x{arbitration_id:X}, Len={data_length}, Data={data_bytes.hex()}")
            
            # 构建CAN帧数据
            can_frame_data = {
                'arbitration_id': arbitration_id,
                'data': data_bytes,
                'is_extended_id': is_extended_id,
                'frame_type': 'can',
                'timestamp': time.time()
            }
            
            # 记录接收的CAN帧
            frame_info = {
                'timestamp': can_frame_data['timestamp'],
                'arbitration_id': arbitration_id,
                'data': data_bytes,
                'data_hex': data_bytes.hex(),
                'is_extended_id': is_extended_id,
                'direction': 'received'
            }
            self._received_can_frames.append(frame_info)
            
            # 发送CAN帧接收信号
            self.can_frame_received.emit(arbitration_id, data_bytes, is_extended_id)
            # 发送帧列表更新信号
            self.can_frame_lists_updated.emit()
            
            return can_frame_data
            
        except Exception as e:
            error_msg = f"处理串口数据失败: {e}"
            self.logger.error(f"CanBusCommunicator: {error_msg}")
            self.can_error.emit(error_msg)
            return None
    
    @Slot(int, bytes, bool, result=object)
    def send_can_frame(self, arbitration_id: int, data: bytes, is_extended_id: bool = True) -> Optional[bytes]:
        """
        发送CAN帧，转换为串口数据格式。
        :param arbitration_id: 仲裁ID
        :param data: 数据字节
        :param is_extended_id: 是否为扩展ID
        :return: 转换后的串口数据，失败时返回None
        """
        try:
            # 检查数据长度
            if len(data) > 8:
                self.logger.warning(f"CanBusCommunicator: CAN帧数据长度超出范围: {len(data)} 字节")
                return None
            
            # 构建串口数据格式: CANID(4字节) + Len(1字节) + Data(N字节)
            # CAN ID需要左移3位（与解析时的右移3位对应）
            arbitration_id = (arbitration_id << 3) + 0x04  # 如果需要使用 USB 转 CAN 模块，需要进行转换
            can_id_bytes = arbitration_id.to_bytes(4, byteorder='big')
            length_byte = len(data).to_bytes(1, byteorder='big')
            
            serial_data = b'AT' + can_id_bytes + length_byte + data + b'\r\n'
            
            self.logger.info(f"CanBusCommunicator: 发送CAN帧: ID=0x{arbitration_id:X}, Data={data.hex()}, 串口数据={serial_data.hex()}")
            
            # 记录发送的CAN帧
            frame_info = {
                'timestamp': time.time(),
                'arbitration_id': arbitration_id,
                'data': data,
                'data_hex': data.hex(),
                'is_extended_id': is_extended_id,
                'direction': 'sent'
            }
            self._sent_can_frames.append(frame_info)
            
            # 发送CAN帧发送信号
            self.can_frame_sent.emit(arbitration_id, data, is_extended_id)
            # 发送串口数据信号
            self.serial_data_to_send.emit(serial_data)
            # 发送帧列表更新信号
            self.can_frame_lists_updated.emit()
            
            # 返回转换后的串口数据
            return serial_data
            
        except Exception as e:
            error_msg = f"发送CAN帧失败: {e}"
            self.logger.error(f"CanBusCommunicator: {error_msg}")
            self.can_error.emit(error_msg)
            return None
    

    # CAN帧列表管理方法
    def clear_can_frame_lists(self):
        """
        清空发送和接收CAN帧列表
        """
        self._sent_can_frames.clear()
        self._received_can_frames.clear()
        self.logger.info("CanBusCommunicator: 已清空发送和接收CAN帧列表")
        # 发送帧列表更新信号
        self.can_frame_lists_updated.emit()
    
    def get_sent_can_frames(self) -> List[Dict[str, Any]]:
        """
        获取发送CAN帧列表
        :return: 发送CAN帧列表的副本
        """
        return list(self._sent_can_frames)
    
    def get_received_can_frames(self) -> List[Dict[str, Any]]:
        """
        获取接收CAN帧列表
        :return: 接收CAN帧列表的副本
        """
        return list(self._received_can_frames)
    
    def get_can_frame_lists_info(self) -> Dict[str, Any]:
        """
        获取CAN帧列表信息
        :return: 包含CAN帧列表统计信息的字典
        """
        return {
            'sent_can_frames_count': len(self._sent_can_frames),
            'received_can_frames_count': len(self._received_can_frames),
            'max_list_size': self._max_can_frame_list_size,
            'sent_can_frames': list(self._sent_can_frames),
            'received_can_frames': list(self._received_can_frames)
        }
    
    def set_max_can_frame_list_size(self, size: int):
        """
        设置CAN帧列表的最大长度
        :param size: 新的最大长度
        """
        if size <= 0:
            self.logger.warning(f"CanBusCommunicator: 无效的CAN帧列表大小: {size}")
            return
        
        self._max_can_frame_list_size = size
        # 重新创建deque以应用新的maxlen
        old_sent = list(self._sent_can_frames)
        old_received = list(self._received_can_frames)
        
        self._sent_can_frames = deque(old_sent, maxlen=size)
        self._received_can_frames = deque(old_received, maxlen=size)
        
        self.logger.info(f"CanBusCommunicator: CAN帧列表最大长度已设置为: {size}")
        # 发送帧列表更新信号
        self.can_frame_lists_updated.emit()
    

    def cleanup(self):
        """
        清理所有资源。
        """
        self.logger.info("CanBusCommunicator: 清理中...")
        
        # 清理CAN帧列表
        self._sent_can_frames.clear()
        self._received_can_frames.clear()
        
        self.logger.info("CanBusCommunicator: 清理完成。")
