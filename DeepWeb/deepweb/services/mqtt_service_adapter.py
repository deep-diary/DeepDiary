#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT服务适配器
将MQTT消息转换为设备逻辑管理器的调用
基于JSON协议动态配置

作者: DeepDiary Team
日期: 2025-01-27
"""

import json
import time
from typing import Dict, Any, Optional
from services.cloud_communication.mqtt.mqtt_manager import MQTTManager
from services.cloud_communication.mqtt.protocol_parser import get_protocol_parser
from app_logic.device_logic_manager import DeviceLogicManager, DeviceCommand

# 保留作为后备的日志函数
def _default_log_message(level: str, message: str):
    """默认的日志输出函数（作为后备）"""
    print(f"[{level.upper()}] {message}")

class MQTTServiceAdapter:
    """MQTT服务适配器"""
    
    def __init__(self, mqtt_manager: MQTTManager, device_manager: DeviceLogicManager, log_manager=None):
        self.mqtt_manager = mqtt_manager
        self.device_manager = device_manager
        
        # 设置日志管理器
        if log_manager:
            self.logger = log_manager.get_logger(__name__)
        else:
            self.logger = None
        
        # 获取协议解析器
        self.protocol_parser = get_protocol_parser()
        
        # 设置MQTT回调（基于协议自动配置）
        self._setup_mqtt_callbacks()
    
    def _log(self, level: str, message: str):
        """统一的日志输出方法"""
        if self.logger:
            if level == "info":
                self.logger.info(message)
            elif level == "warning":
                self.logger.warning(message)
            elif level == "error":
                self.logger.error(message)
            elif level == "debug":
                self.logger.debug(message)
        else:
            _default_log_message(level, message)
    
    def _setup_mqtt_callbacks(self):
        """设置MQTT回调函数（基于协议自动配置）"""
        # 定义处理器函数映射
        handler_funcs = {
            'device_info': self._on_device_info,
            'device_status': self._on_device_status,
            'device_events': self._on_device_events
        }
        
        # 使用协议解析器自动设置订阅
        self.protocol_parser.setup_subscriptions(self.mqtt_manager, handler_funcs)
    
    def _extract_device_id(self, topic: str) -> Optional[str]:
        """从主题中提取设备ID"""
        # 使用协议解析器提取设备ID
        return self.protocol_parser.extract_device_id(topic)
    
    def _on_device_info(self, message_info: Dict[str, Any]):
        """处理设备信息消息（新格式）"""
        topic = message_info['topic']
        payload = message_info['payload']
        device_id = message_info['device_id']
        
        if not device_id:
            self._log("warning", f"无法从主题 {topic} 提取设备ID")
            return
        
        try:
            self._log("info", f"收到设备信息消息: {device_id}")
            self._log("debug", f"原始数据: {payload}")
            
            # 解析设备信息数据（新格式直接包含所有信息）
            device_info = {
                'device_id': payload.get('device_id', device_id),
                'device_type': payload.get('device_type', 'unknown'),
                'firmware_version': payload.get('firmware_version', 'unknown'),
                'mac_address': payload.get('mac_address', ''),
                'chip_model': payload.get('chip_model', ''),
                'chip_revision': payload.get('chip_revision', ''),
                'hardware_capabilities': payload.get('hardware_capabilities', {})
            }
            
            self._log("debug", f"解析后的设备信息: {device_info}")
            
            # 更新设备状态
            self.device_manager.update_device_status(device_id, device_info)
            
            self._log("info", f"设备信息更新成功: {device_id}")
            
        except Exception as e:
            self._log("error", f"处理设备信息消息失败: {e}")
    
    def _on_device_status(self, message_info: Dict[str, Any]):
        """处理设备状态消息"""
        topic = message_info['topic']
        payload = message_info['payload']
        device_id = message_info['device_id']
        
        if not device_id:
            self._log("warning", f"无法从主题 {topic} 提取设备ID")
            return
        
        try:
            self._log("info", f"收到设备状态消息: {device_id}")
            self._log("debug", f"原始数据: {payload}")
            
            # 新协议格式：device_status 包含 categories (system, sensor, actuator)
            status_data = {
                'wifi_ssid': payload.get('system', {}).get('wifi_ssid', ''),
                'ip_address': payload.get('system', {}).get('ip_address', ''),
                'free_heap': payload.get('system', {}).get('free_heap', 0),
                'uptime_seconds': payload.get('system', {}).get('uptime_seconds', 0),
                'cpu_temperature': payload.get('system', {}).get('cpu_temperature', 0.0),
                'network_status': payload.get('system', {}).get('network_status', ''),
                'sensor': payload.get('sensor', {}),
                'actuator': payload.get('actuator', {})
            }
            
            self._log("debug", f"解析后的状态数据: {status_data}")
            
            # 更新设备状态
            self.device_manager.update_device_status(device_id, status_data)
            
            self._log("info", f"设备状态更新成功: {device_id}")
            
        except Exception as e:
            self._log("error", f"处理设备状态消息失败: {e}")
    
    def _on_device_events(self, message_info: Dict[str, Any]):
        """处理设备事件消息"""
        topic = message_info['topic']
        payload = message_info['payload']
        device_id = message_info['device_id']
        
        try:
            event_type = payload.get('event_type', 'unknown')
            event_message = payload.get('event_message', '')
            
            self._log("info", f"收到设备事件: {device_id} -> {event_type}: {event_message}")
            
        except Exception as e:
            self._log("error", f"处理设备事件失败: {e}")
    
    
    def send_device_command(self, device_id: str, command: DeviceCommand) -> bool:
        """发送设备命令"""
        try:
            # 构建MQTT消息
            mqtt_message = {
                "command_id": command.command_id,
                "timestamp": command.timestamp,
                "command_type": command.command_type,
                "target": command.target,
                "action": command.action,
                "parameters": command.parameters,
                "priority": command.priority,
                "timeout": command.timeout
            }
            
            # 构建主题
            topic = f"deepcontroller/{device_id}/command"
            
            # 发送MQTT消息
            success = self.mqtt_manager.publish_json(topic, mqtt_message)
            
            if success:
                # 更新设备管理器
                self.device_manager.send_command(device_id, command)
                self._log("info", f"设备命令发送成功: {device_id} -> {command.action}")
            else:
                self._log("warning", f"设备命令发送失败: {device_id} -> {command.action}")
            
            return success
            
        except Exception as e:
            self._log("error", f"发送设备命令异常: {e}")
            return False
    
    def send_motor_command(self, device_id: str, motor_id: int, action: str, **kwargs) -> bool:
        """发送电机控制命令"""
        command = DeviceCommand(
            command_id=f"{device_id}_motor_{motor_id}_{int(time.time())}",
            command_type="motor_control",
            target="motor",
            action=action,
            parameters={
                "motor_id": motor_id,
                **kwargs
            }
        )
        
        return self.send_device_command(device_id, command)
    
    def send_arm_command(self, device_id: str, action: str, **kwargs) -> bool:
        """发送机械臂控制命令"""
        command = DeviceCommand(
            command_id=f"{device_id}_arm_{int(time.time())}",
            command_type="arm_control",
            target="arm",
            action=action,
            parameters=kwargs
        )
        
        return self.send_device_command(device_id, command)
    
    def send_camera_command(self, device_id: str, action: str, **kwargs) -> bool:
        """发送摄像头控制命令"""
        command = DeviceCommand(
            command_id=f"{device_id}_camera_{int(time.time())}",
            command_type="camera_control",
            target="camera",
            action=action,
            parameters=kwargs
        )
        
        return self.send_device_command(device_id, command)
    
    def send_led_command(self, device_id: str, action: str, **kwargs) -> bool:
        """发送LED控制命令"""
        command = DeviceCommand(
            command_id=f"{device_id}_led_{int(time.time())}",
            command_type="led_control",
            target="led",
            action=action,
            parameters=kwargs
        )
        
        return self.send_device_command(device_id, command)
