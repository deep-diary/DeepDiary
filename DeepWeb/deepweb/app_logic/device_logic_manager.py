#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备逻辑管理器
管理不倒翁设备的状态、控制和数据

作者: DeepDiary Team
日期: 2025-01-27
"""

import time
import threading
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import json

class DeviceStatus(Enum):
    """设备状态枚举"""
    OFFLINE = "offline"
    ONLINE = "online"
    ERROR = "error"
    BUSY = "busy"

class ComponentStatus(Enum):
    """组件状态枚举"""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    ERROR = "error"

@dataclass
class DeviceInfo:
    """设备信息"""
    device_id: str
    device_type: str = "ATK-DNESP32S3"
    firmware_version: str = "1.0.0"
    ip_address: str = ""
    status: DeviceStatus = DeviceStatus.OFFLINE
    last_seen: float = 0.0
    components: Dict[str, ComponentStatus] = field(default_factory=dict)
    
    # 系统信息
    free_heap: int = 0
    uptime_seconds: int = 0
    cpu_temperature: float = 0.0
    
    # 传感器数据
    sensor_data: Dict[str, Any] = field(default_factory=dict)
    
    # 电机状态
    motor_data: Dict[str, Any] = field(default_factory=dict)
    
    # 机械臂状态
    arm_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DeviceCommand:
    """设备命令"""
    command_id: str
    command_type: str
    target: str
    action: str
    parameters: Dict[str, Any]
    priority: str = "normal"
    timeout: int = 10000
    timestamp: float = field(default_factory=time.time)

class DeviceLogicManager:
    """设备逻辑管理器"""
    
    def __init__(self):
        self.devices: Dict[str, DeviceInfo] = {}
        self.command_history: List[DeviceCommand] = []
        self.status_callbacks: List[callable] = []
        self.command_callbacks: List[callable] = []
        self._lock = threading.Lock()
        
        # 初始化默认设备
        self._init_default_devices()
    
    def _init_default_devices(self):
        """初始化默认设备"""
        default_device = DeviceInfo(
            device_id="ATK-DNESP32S3-ESP32-S3-12345678",
            device_type="ATK-DNESP32S3",
            firmware_version="1.0.0",
            ip_address="192.168.1.100",
            status=DeviceStatus.OFFLINE,
            components={
                "camera": ComponentStatus.AVAILABLE,
                "can_bus": ComponentStatus.AVAILABLE,
                "led_strip": ComponentStatus.AVAILABLE,
                "gimbal": ComponentStatus.AVAILABLE,
                "sensor": ComponentStatus.AVAILABLE
            }
        )
        self.devices[default_device.device_id] = default_device
    
    def add_device(self, device_info: DeviceInfo):
        """添加设备"""
        with self._lock:
            self.devices[device_info.device_id] = device_info
            self._notify_status_callbacks(device_info.device_id, device_info)
    
    def remove_device(self, device_id: str):
        """移除设备"""
        with self._lock:
            if device_id in self.devices:
                del self.devices[device_id]
    
    def update_device_status(self, device_id: str, status_data: Dict[str, Any]):
        """更新设备状态"""
        with self._lock:
            if device_id not in self.devices:
                return
            
            device = self.devices[device_id]
            device.status = DeviceStatus(status_data.get('status', 'offline'))
            device.last_seen = time.time()
            
            # 更新系统信息
            if 'system_info' in status_data:
                system_info = status_data['system_info']
                device.free_heap = system_info.get('free_heap', 0)
                device.uptime_seconds = system_info.get('uptime_seconds', 0)
                device.cpu_temperature = system_info.get('cpu_temperature', 0.0)
            
            # 更新组件状态
            if 'components' in status_data:
                for comp_name, comp_status in status_data['components'].items():
                    device.components[comp_name] = ComponentStatus(comp_status)
            
            self._notify_status_callbacks(device_id, device)
    
    def update_sensor_data(self, device_id: str, sensor_data: Dict[str, Any]):
        """更新传感器数据"""
        with self._lock:
            if device_id not in self.devices:
                return
            
            device = self.devices[device_id]
            device.sensor_data.update(sensor_data)
            device.last_seen = time.time()
            
            self._notify_status_callbacks(device_id, device)
    
    def update_motor_data(self, device_id: str, motor_data: Dict[str, Any]):
        """更新电机数据"""
        with self._lock:
            if device_id not in self.devices:
                return
            
            device = self.devices[device_id]
            device.motor_data.update(motor_data)
            device.last_seen = time.time()
            
            self._notify_status_callbacks(device_id, device)
    
    def update_arm_data(self, device_id: str, arm_data: Dict[str, Any]):
        """更新机械臂数据"""
        with self._lock:
            if device_id not in self.devices:
                return
            
            device = self.devices[device_id]
            device.arm_data.update(arm_data)
            device.last_seen = time.time()
            
            self._notify_status_callbacks(device_id, device)
    
    def send_command(self, device_id: str, command: DeviceCommand) -> bool:
        """发送设备命令"""
        with self._lock:
            if device_id not in self.devices:
                return False
            
            # 添加到命令历史
            self.command_history.append(command)
            
            # 限制命令历史长度
            if len(self.command_history) > 1000:
                self.command_history = self.command_history[-500:]
            
            # 通知命令回调
            self._notify_command_callbacks(device_id, command)
            
            return True
    
    def get_device(self, device_id: str) -> Optional[DeviceInfo]:
        """获取设备信息"""
        with self._lock:
            return self.devices.get(device_id)
    
    def get_devices(self) -> Dict[str, DeviceInfo]:
        """获取所有设备"""
        with self._lock:
            return self.devices.copy()
    
    def get_device_status(self, device_id: str) -> Optional[DeviceStatus]:
        """获取设备状态"""
        device = self.get_device(device_id)
        return device.status if device else None
    
    def get_command_history(self, device_id: Optional[str] = None, limit: int = 100) -> List[DeviceCommand]:
        """获取命令历史"""
        with self._lock:
            if device_id:
                history = [cmd for cmd in self.command_history if cmd.command_id.startswith(device_id)]
            else:
                history = self.command_history.copy()
            
            return history[-limit:] if limit > 0 else history
    
    def add_status_callback(self, callback: callable):
        """添加状态更新回调"""
        self.status_callbacks.append(callback)
    
    def add_command_callback(self, callback: callable):
        """添加命令回调"""
        self.command_callbacks.append(callback)
    
    def _notify_status_callbacks(self, device_id: str, device: DeviceInfo):
        """通知状态回调"""
        for callback in self.status_callbacks:
            try:
                callback(device_id, device)
            except Exception as e:
                print(f"状态回调执行错误: {e}")
    
    def _notify_command_callbacks(self, device_id: str, command: DeviceCommand):
        """通知命令回调"""
        for callback in self.command_callbacks:
            try:
                callback(device_id, command)
            except Exception as e:
                print(f"命令回调执行错误: {e}")
    
    def get_device_statistics(self) -> Dict[str, Any]:
        """获取设备统计信息"""
        with self._lock:
            total_devices = len(self.devices)
            online_devices = sum(1 for d in self.devices.values() if d.status == DeviceStatus.ONLINE)
            offline_devices = sum(1 for d in self.devices.values() if d.status == DeviceStatus.OFFLINE)
            error_devices = sum(1 for d in self.devices.values() if d.status == DeviceStatus.ERROR)
            
            return {
                'total_devices': total_devices,
                'online_devices': online_devices,
                'offline_devices': offline_devices,
                'error_devices': error_devices,
                'total_commands': len(self.command_history)
            }
