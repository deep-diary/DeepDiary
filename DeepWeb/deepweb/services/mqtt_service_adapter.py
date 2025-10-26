#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT服务适配器
将MQTT消息转换为设备逻辑管理器的调用

作者: DeepDiary Team
日期: 2025-01-27
"""

import json
import time
from typing import Dict, Any, Optional
from services.cloud_communication.mqtt.mqtt_manager import MQTTManager
from app_logic.device_logic_manager import DeviceLogicManager, DeviceCommand

class MQTTServiceAdapter:
    """MQTT服务适配器"""
    
    def __init__(self, mqtt_manager: MQTTManager, device_manager: DeviceLogicManager):
        self.mqtt_manager = mqtt_manager
        self.device_manager = device_manager
        
        # 设置MQTT回调
        self._setup_mqtt_callbacks()
    
    def _setup_mqtt_callbacks(self):
        """设置MQTT回调函数"""
        # 设备状态回调
        self.mqtt_manager.add_subscription(
            name="device_status",
            topic="deepcontroller/+/status",
            callback=self._on_device_status,
            description="设备状态消息"
        )
        
        # 传感器数据回调
        self.mqtt_manager.add_subscription(
            name="sensor_data",
            topic="deepcontroller/+/sensor",
            callback=self._on_sensor_data,
            description="传感器数据"
        )
        
        # 电机状态回调
        self.mqtt_manager.add_subscription(
            name="motor_data",
            topic="deepcontroller/+/motor",
            callback=self._on_motor_data,
            description="电机状态数据"
        )
        
        # 机械臂状态回调
        self.mqtt_manager.add_subscription(
            name="arm_data",
            topic="deepcontroller/+/arm",
            callback=self._on_arm_data,
            description="机械臂状态数据"
        )
        
        # 摄像头状态回调
        self.mqtt_manager.add_subscription(
            name="camera_data",
            topic="deepcontroller/+/camera",
            callback=self._on_camera_data,
            description="摄像头状态数据"
        )
        
        # 系统信息回调
        self.mqtt_manager.add_subscription(
            name="system_data",
            topic="deepcontroller/+/system",
            callback=self._on_system_data,
            description="系统信息数据"
        )
        
        # 告警信息回调
        self.mqtt_manager.add_subscription(
            name="alarm_data",
            topic="deepcontroller/+/alarm",
            callback=self._on_alarm_data,
            description="告警信息"
        )
    
    def _extract_device_id(self, topic: str) -> Optional[str]:
        """从主题中提取设备ID"""
        try:
            # 主题格式: deepcontroller/{device_id}/{message_type}
            parts = topic.split('/')
            if len(parts) >= 2 and parts[0] == 'deepcontroller':
                return parts[1]
        except Exception as e:
            print(f"提取设备ID失败: {e}")
        return None
    
    def _on_device_status(self, topic: str, payload: Dict[str, Any], message):
        """处理设备状态消息"""
        device_id = self._extract_device_id(topic)
        if not device_id:
            return
        
        try:
            # 解析状态数据
            status_data = {
                'status': payload.get('data', {}).get('device_type', 'offline'),
                'system_info': {
                    'free_heap': payload.get('data', {}).get('free_heap', 0),
                    'uptime_seconds': payload.get('data', {}).get('uptime_seconds', 0),
                    'cpu_temperature': payload.get('data', {}).get('cpu_temperature', 0.0)
                },
                'components': payload.get('data', {}).get('components', {})
            }
            
            # 更新设备状态
            self.device_manager.update_device_status(device_id, status_data)
            
            print(f"设备状态更新: {device_id} -> {status_data['status']}")
            
        except Exception as e:
            print(f"处理设备状态消息失败: {e}")
    
    def _on_sensor_data(self, topic: str, payload: Dict[str, Any], message):
        """处理传感器数据消息"""
        device_id = self._extract_device_id(topic)
        if not device_id:
            return
        
        try:
            sensor_data = payload.get('data', {})
            self.device_manager.update_sensor_data(device_id, sensor_data)
            
            print(f"传感器数据更新: {device_id}")
            
        except Exception as e:
            print(f"处理传感器数据失败: {e}")
    
    def _on_motor_data(self, topic: str, payload: Dict[str, Any], message):
        """处理电机数据消息"""
        device_id = self._extract_device_id(topic)
        if not device_id:
            return
        
        try:
            motor_data = payload.get('data', {})
            self.device_manager.update_motor_data(device_id, motor_data)
            
            print(f"电机数据更新: {device_id}")
            
        except Exception as e:
            print(f"处理电机数据失败: {e}")
    
    def _on_arm_data(self, topic: str, payload: Dict[str, Any], message):
        """处理机械臂数据消息"""
        device_id = self._extract_device_id(topic)
        if not device_id:
            return
        
        try:
            arm_data = payload.get('data', {})
            self.device_manager.update_arm_data(device_id, arm_data)
            
            print(f"机械臂数据更新: {device_id}")
            
        except Exception as e:
            print(f"处理机械臂数据失败: {e}")
    
    def _on_camera_data(self, topic: str, payload: Dict[str, Any], message):
        """处理摄像头数据消息"""
        device_id = self._extract_device_id(topic)
        if not device_id:
            return
        
        try:
            camera_data = payload.get('data', {})
            # 摄像头数据可以用于更新设备状态
            print(f"摄像头数据更新: {device_id} -> {camera_data}")
            
        except Exception as e:
            print(f"处理摄像头数据失败: {e}")
    
    def _on_system_data(self, topic: str, payload: Dict[str, Any], message):
        """处理系统信息消息"""
        device_id = self._extract_device_id(topic)
        if not device_id:
            return
        
        try:
            system_data = payload.get('data', {})
            status_data = {
                'status': 'online',
                'system_info': {
                    'free_heap': system_data.get('memory', {}).get('free_heap', 0),
                    'uptime_seconds': 0,  # 系统信息中可能没有uptime
                    'cpu_temperature': 0.0  # 系统信息中可能没有温度
                }
            }
            
            self.device_manager.update_device_status(device_id, status_data)
            
            print(f"系统信息更新: {device_id}")
            
        except Exception as e:
            print(f"处理系统信息失败: {e}")
    
    def _on_alarm_data(self, topic: str, payload: Dict[str, Any], message):
        """处理告警信息消息"""
        device_id = self._extract_device_id(topic)
        if not device_id:
            return
        
        try:
            alarm_data = payload.get('data', {})
            print(f"设备告警: {device_id} -> {alarm_data.get('description', 'Unknown alarm')}")
            
        except Exception as e:
            print(f"处理告警信息失败: {e}")
    
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
                print(f"设备命令发送成功: {device_id} -> {command.action}")
            else:
                print(f"设备命令发送失败: {device_id} -> {command.action}")
            
            return success
            
        except Exception as e:
            print(f"发送设备命令异常: {e}")
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
