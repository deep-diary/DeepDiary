#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT连接测试脚本
用于测试MQTT连接和数据接收

作者: DeepDiary Team
日期: 2025-10-26
"""

import sys
import time
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.cloud_communication.mqtt.mqtt_manager import MQTTManager
from config.config_manager import ConfigManager

def test_mqtt_connection():
    """测试MQTT连接"""
    print("🔧 初始化MQTT连接测试...")
    
    # 获取配置
    config_manager = ConfigManager()
    config = config_manager.get_config()
    mqtt_config = config.get('mqtt', {})
    
    print(f"📡 MQTT配置: {mqtt_config}")
    
    # 创建MQTT管理器
    mqtt_manager = MQTTManager(
        host=mqtt_config.get('host', 'localhost'),
        port=mqtt_config.get('port', 1883),
        username=mqtt_config.get('username'),
        password=mqtt_config.get('password'),
        debug=True
    )
    
    # 消息计数器
    message_count = 0
    
    def on_test_message(topic, payload, message):
        nonlocal message_count
        message_count += 1
        print(f"📨 收到消息 #{message_count}")
        print(f"   主题: {topic}")
        print(f"   内容: {payload}")
        print(f"   QoS: {message.qos}")
        print("---")
    
    # 添加订阅（支持新的设备主题格式）
    topics = [
        "device/+/info",  # 新的设备信息主题
        "device/+/status",  # 新的设备状态主题
        "device/+/sensor",  # 新的传感器主题
        "device/+/motor",  # 新的电机主题
        "device/+/arm",  # 新的机械臂主题
        "device/+/camera",  # 新的摄像头主题
        "device/+/system",  # 新的系统主题
        "device/+/alarm",  # 新的告警主题
        "device/+/log",  # 新的日志主题
        # 保留原有格式作为备用
        "deepcontroller/+/status",
        "deepcontroller/+/sensor", 
        "deepcontroller/+/motor",
        "deepcontroller/+/arm",
        "deepcontroller/+/camera",
        "deepcontroller/+/system",
        "deepcontroller/+/alarm",
        "deepcontroller/+/log"
    ]
    
    for i, topic in enumerate(topics):
        mqtt_manager.add_subscription(
            name=f"test_subscription_{i}",
            topic=topic,
            callback=on_test_message,
            description=f"测试订阅 {topic}"
        )
    
    # 连接MQTT
    print("🔌 连接到MQTT代理...")
    if mqtt_manager.connect():
        print("✅ MQTT连接成功!")
        
        # 等待消息
        print("⏳ 等待MQTT消息 (30秒)...")
        print("💡 提示: 如果有设备在发送数据，应该能看到消息")
        
        start_time = time.time()
        timeout = 30
        
        while time.time() - start_time < timeout:
            time.sleep(1)
            if message_count > 0:
                print(f"📊 已收到 {message_count} 条消息")
        
        if message_count == 0:
            print("⚠️  30秒内未收到任何消息")
            print("🔍 可能的原因:")
            print("   1. 没有设备连接到MQTT代理")
            print("   2. 设备没有发送数据")
            print("   3. 主题模式不匹配")
            print("   4. 网络连接问题")
        else:
            print(f"🎉 测试完成! 总共收到 {message_count} 条消息")
        
        # 断开连接
        mqtt_manager.disconnect()
        print("🔌 MQTT连接已断开")
        
    else:
        print("❌ MQTT连接失败!")
        print("🔍 请检查:")
        print("   1. MQTT代理服务器是否运行")
        print("   2. 网络连接是否正常")
        print("   3. 用户名密码是否正确")
        print("   4. 防火墙设置")

if __name__ == "__main__":
    test_mqtt_connection()
