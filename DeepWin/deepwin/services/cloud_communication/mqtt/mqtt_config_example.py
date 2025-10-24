"""
使用配置文件的MQTT示例
演示如何使用mqtt_config.py配置文件来管理MQTT连接和主题
"""

from mqtt_manager import MQTTManager
import time
import json


def main():
    """主函数 - 演示配置文件的使用"""
    
    print("🔧 使用配置文件创建MQTT管理器...")
    
    # 方法1: 使用配置文件创建MQTT管理器
    try:
        mqtt_manager = MQTTManager.from_config(
            server_name="default",  # 使用配置文件中的"default"服务器
            client_id="config_client",
            debug=True
        )
        print("✅ 成功从配置文件创建MQTT管理器")
    except ImportError as e:
        print(f"❌ 配置文件不可用: {e}")
        return
    
    # 定义消息处理回调函数
    def on_device_status(topic, payload, message):
        """处理设备状态消息"""
        print(f"📊 设备状态更新: {topic}")
        print(f"   数据: {payload}")
        
    def on_sensor_data(topic, payload, message):
        """处理传感器数据"""
        print(f"📡 传感器数据: {topic}")
        print(f"   数据: {payload}")
        
    # 方法2: 使用主题模板添加订阅
    print("\n🔗 使用主题模板添加订阅...")
    
    # 使用模板添加设备状态订阅
    mqtt_manager.add_subscription_from_template(
        name="device_status_001",
        category="device",
        topic_type="status",
        callback=on_device_status,
        description="设备001状态监控",
        qos=1,
        device_id="device_001"  # 模板参数
    )
    
    # 使用模板添加传感器数据订阅
    mqtt_manager.add_subscription_from_template(
        name="sensor_data",
        category="sensor", 
        topic_type="data",
        callback=on_sensor_data,
        description="传感器数据订阅",
        qos=0,
        sensor_id="+"  # 使用通配符订阅所有传感器
    )
    
    # 方法3: 使用主题模板添加发布主题
    print("\n📤 使用主题模板添加发布主题...")
    
    mqtt_manager.add_publish_topic_from_template(
        name="device_commands_001",
        category="device",
        topic_type="commands",
        description="设备001命令发布",
        qos=1,
        device_id="device_001"
    )
    
    mqtt_manager.add_publish_topic_from_template(
        name="system_logs",
        category="system",
        topic_type="logs",
        description="系统日志发布",
        qos=0
    )
    
    # 连接到MQTT服务器
    print("\n🚀 连接到MQTT服务器...")
    if mqtt_manager.connect():
        print("✅ 连接成功！")
        
        # 显示配置信息
        status = mqtt_manager.get_status()
        print(f"📋 服务器: {status['host']}:{status['port']}")
        print(f"📋 客户端ID: {status['client_id']}")
        
        # 显示订阅和发布主题
        print("\n📋 订阅主题列表:")
        subscriptions = mqtt_manager.get_subscriptions()
        for name, info in subscriptions.items():
            print(f"   {name}: {info['topic']} (QoS: {info['qos']})")
            
        print("\n📤 发布主题列表:")
        publish_topics = mqtt_manager.get_publish_topics()
        for name, info in publish_topics.items():
            print(f"   {name}: {info['topic']} (QoS: {info['qos']})")
        
        # 发布测试消息
        print("\n📤 发布测试消息...")
        
        # 发布设备状态消息
        mqtt_manager.publish_json("device_commands_001", {
            "command": "status_check",
            "device_id": "device_001",
            "timestamp": time.time()
        })
        time.sleep(1)
        
        # 发布系统日志
        mqtt_manager.publish_json("system_logs", {
            "level": "INFO",
            "message": "配置文件集成测试",
            "module": "mqtt_config",
            "timestamp": time.time()
        })
        time.sleep(1)
        
        # 发布一些测试消息到订阅的主题
        print("\n📥 发布测试消息到订阅主题...")
        
        # 发布设备状态
        mqtt_manager.publish_json("device/device_001/status", {
            "device_id": "device_001",
            "status": "online",
            "battery": 90,
            "temperature": 25.5,
            "timestamp": time.time()
        })
        time.sleep(1)
        
        # 发布传感器数据
        mqtt_manager.publish_json("sensor/temperature_001/data", {
            "sensor_id": "temperature_001",
            "data_type": "temperature",
            "value": 23.5,
            "unit": "celsius",
            "timestamp": time.time(),
            "quality": 0.95
        })
        time.sleep(1)
        
        # 等待消息
        print("\n⏳ 等待接收消息 (5秒)...")
        mqtt_manager.wait_for_messages(5)
        
        # 最终统计
        print("\n📊 最终统计:")
        final_status = mqtt_manager.get_status()
        stats = final_status['stats']
        print(f"   发送消息数: {stats['messages_sent']}")
        print(f"   接收消息数: {stats['messages_received']}")
        
    else:
        print("❌ 连接失败！")
        
    # 断开连接
    print("\n🔌 断开连接...")
    mqtt_manager.disconnect()
    print("✅ 已断开连接")


def demonstrate_config_functions():
    """演示配置文件函数的使用"""
    print("\n🔧 演示配置文件函数...")
    
    try:
        from mqtt_config import get_server_config, get_topic_template, format_topic, get_message_schema
        
        # 获取服务器配置
        config = get_server_config("default")
        print(f"📋 默认服务器配置: {config}")
        
        # 获取主题模板
        device_status_template = get_topic_template("device", "status")
        print(f"📋 设备状态主题模板: {device_status_template}")
        
        # 格式化主题
        device_status_topic = format_topic(device_status_template, device_id="device_001")
        print(f"📋 格式化后的主题: {device_status_topic}")
        
        # 获取消息结构
        schema = get_message_schema("device_status")
        print(f"📋 设备状态消息结构: {schema}")
        
    except ImportError as e:
        print(f"❌ 配置文件不可用: {e}")


if __name__ == "__main__":
    try:
        main()
        demonstrate_config_functions()
    except KeyboardInterrupt:
        print("\n⏹️  用户中断程序")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
