"""
MQTT管理类使用示例
演示如何使用MQTTManager类进行MQTT通讯
"""

from mqtt_manager import MQTTManager
import time
import json


def main():
    """主函数 - 演示MQTT管理器的使用"""
    
    print("🔧 创建MQTT管理器实例...")
    print("   方式1: 直接指定参数")
    
    # 方式1: 直接创建MQTT管理器实例
    mqtt_manager = MQTTManager(
        host="35.192.64.247",  # MQTT服务器地址
        port=1883,              # MQTT服务器端口
        client_id="test_client", # 客户端ID
        debug=True              # 开启调试模式
    )
    
    # 方式2: 使用配置文件创建（如果可用）
    try:
        print("   方式2: 使用配置文件创建")
        mqtt_manager_config = MQTTManager.from_config(
            server_name="default",
            client_id="config_client",
            debug=False
        )
        print("   ✅ 配置文件方式创建成功")
    except ImportError:
        print("   ⚠️  配置文件不可用，跳过配置文件方式")
        mqtt_manager_config = None
    
    # 定义消息处理回调函数
    def on_device_status(topic, payload, message):
        """处理设备状态消息"""
        print(f"📊 设备状态更新: {topic}")
        print(f"   数据: {payload}")
        
    def on_device_control(topic, payload, message):
        """处理设备控制消息"""
        print(f"🎮 设备控制指令: {topic}")
        print(f"   指令: {payload}")
        
    def on_sensor_data(topic, payload, message):
        """处理传感器数据"""
        print(f"📡 传感器数据: {topic}")
        print(f"   数据: {payload}")
        
    # 添加订阅主题
    print("🔗 添加订阅主题...")
    mqtt_manager.add_subscription(
        name="device_status",
        topic="device/status",
        callback=on_device_status,
        description="设备状态监控",
        qos=1
    )
    
    mqtt_manager.add_subscription(
        name="device_control",
        topic="device/control",
        callback=on_device_control,
        description="设备控制指令",
        qos=1
    )
    
    mqtt_manager.add_subscription(
        name="sensor_data",
        topic="sensor/+/data",  # 使用通配符订阅所有传感器数据
        callback=on_sensor_data,
        description="传感器数据订阅",
        qos=0
    )
    
    # 添加发布主题
    print("📤 添加发布主题...")
    mqtt_manager.add_publish_topic(
        name="device_commands",
        topic="device/commands",
        description="设备命令发布",
        qos=1,
        retain=False
    )
    
    mqtt_manager.add_publish_topic(
        name="system_logs",
        topic="system/logs",
        description="系统日志发布",
        qos=0,
        retain=False
    )
    
    # 连接到MQTT服务器
    print("🚀 连接到MQTT服务器...")
    if mqtt_manager.connect():
        print("✅ 连接成功！")
        
        # 显示连接状态
        status = mqtt_manager.get_status()
        print(f"📋 连接状态: {status['status']}")
        print(f"📊 统计信息: {status['stats']}")
        
        # 发布一些测试消息
        print("\n📤 发布测试消息...")
        
        # 发布简单文本消息
        for i in range(3):
            mqtt_manager.publish("testtopic/demo", f"测试消息 {i+1}")
            time.sleep(1)
            
        # 发布一些测试消息到订阅的主题，验证接收功能
        print("\n📥 发布测试消息到订阅主题...")
        mqtt_manager.publish_json("device/status", {
            "device_id": "device_001",
            "status": "online",
            "battery": 85,
            "timestamp": time.time()
        })
        time.sleep(1)
        
        mqtt_manager.publish_json("device/control", {
            "command": "test_command",
            "device_id": "device_001",
            "timestamp": time.time()
        })
        time.sleep(1)
        
        mqtt_manager.publish_json("sensor/temperature/data", {
            "sensor_id": "temp_001",
            "value": 25.5,
            "unit": "celsius",
            "timestamp": time.time()
        })
        time.sleep(1)
            
        # 发布JSON格式的设备命令
        device_commands = [
            {"command": "start", "device_id": "device_001", "timestamp": time.time()},
            {"command": "stop", "device_id": "device_002", "timestamp": time.time()},
            {"command": "restart", "device_id": "device_003", "timestamp": time.time()}
        ]
        
        for cmd in device_commands:
            mqtt_manager.publish_json("device_commands", cmd)
            time.sleep(1)
            
        # 发布系统日志
        log_messages = [
            {"level": "INFO", "message": "系统启动完成", "module": "main"},
            {"level": "WARNING", "message": "内存使用率较高", "module": "monitor"},
            {"level": "ERROR", "message": "网络连接超时", "module": "network"}
        ]
        
        for log in log_messages:
            mqtt_manager.publish_json("system_logs", log)
            time.sleep(1)
            
        # 显示订阅和发布主题信息
        print("\n📋 订阅主题列表:")
        subscriptions = mqtt_manager.get_subscriptions()
        for name, info in subscriptions.items():
            print(f"   {name}: {info['topic']} (QoS: {info['qos']})")
            
        print("\n📤 发布主题列表:")
        publish_topics = mqtt_manager.get_publish_topics()
        for name, info in publish_topics.items():
            print(f"   {name}: {info['topic']} (QoS: {info['qos']})")
            
        # 等待接收消息
        print("\n⏳ 等待接收消息 (10秒)...")
        mqtt_manager.wait_for_messages(10)
        
        # 动态管理订阅
        print("\n🔧 动态管理订阅...")
        
        # 禁用某个订阅
        print("   禁用设备状态订阅...")
        mqtt_manager.disable_subscription("device_status")
        time.sleep(2)
        
        # 重新启用订阅
        print("   重新启用设备状态订阅...")
        mqtt_manager.enable_subscription("device_status")
        time.sleep(2)
        
        # 移除订阅
        print("   移除传感器数据订阅...")
        mqtt_manager.remove_subscription("sensor_data")
        time.sleep(2)
        
        # 最终状态
        print("\n📊 最终状态:")
        final_status = mqtt_manager.get_status()
        print(f"   连接状态: {final_status['status']}")
        print(f"   发送消息数: {final_status['stats']['messages_sent']}")
        print(f"   接收消息数: {final_status['stats']['messages_received']}")
        print(f"   连接尝试次数: {final_status['stats']['connection_attempts']}")
        
    else:
        print("❌ 连接失败！")
        print(f"   错误信息: {mqtt_manager.last_error}")
        
    # 断开连接
    print("\n🔌 断开连接...")
    mqtt_manager.disconnect()
    print("✅ 已断开连接")


def context_manager_example():
    """上下文管理器使用示例"""
    print("\n🔄 上下文管理器示例...")
    
    # 使用上下文管理器自动管理连接
    with MQTTManager(host="35.192.64.247", port=1883, debug=True) as mqtt:
        # 添加订阅
        mqtt.add_subscription(
            name="test",
            topic="testtopic/#",
            callback=lambda t, p, m: print(f"收到: {t} -> {p}")
        )
        
        # 发布消息
        mqtt.publish("testtopic/context", "上下文管理器测试消息")
        
        # 等待消息
        time.sleep(3)
        
    # 连接会自动断开


if __name__ == "__main__":
    try:
        main()
        context_manager_example()
    except KeyboardInterrupt:
        print("\n⏹️  用户中断程序")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
