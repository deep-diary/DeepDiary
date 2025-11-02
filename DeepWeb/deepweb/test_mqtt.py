"""
MQTT 管理器测试脚本
使用 MQTTManager 进行基本功能测试
"""
import time
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from deepweb.services.device_communication.mqtt_manager import MQTTManager


def on_message(topic: str, payload, message):
    """消息接收回调"""
    print(f"\n[收到消息]")
    print(f"  主题: {topic}")
    print(f"  内容: {payload}")
    print(f"  QoS: {message.qos}")
    print()


def main():
    """主测试函数"""
    print("=" * 60)
    print("MQTT Manager 基本功能测试")
    print("=" * 60)
    
    # 创建 MQTT 管理器（禁用自动重连，避免测试时不断重连）
    print("\n1. 创建 MQTT 管理器...")
    manager = MQTTManager.from_config(
        server_name="default",
        client_id="test_client_python",
        auto_reconnect=False  # 禁用自动重连
    )
    
    # 设置消息回调
    print("\n2. 设置消息回调...")
    manager.set_message_callback(on_message)
    
    # 检查连接状态（因为 from_config 默认会 auto_connect=True）
    print("\n3. 检查连接状态...")
    status = manager.get_status()
    if status['status'] == 'connected':
        print("✓ 已连接（自动连接成功）")
    else:
        print("✗ 未连接，尝试手动连接...")
        result = manager.connect(wait_for_connection=True, timeout=5.0)
        if result:
            print("✓ 连接成功")
        else:
            print("✗ 连接失败")
            return
    
    # 订阅主题
    print("\n4. 订阅测试主题...")
    if manager.subscribe("test/hello", qos=0):
        print("✓ 订阅成功: test/hello")
    else:
        print("✗ 订阅失败")
    
    if manager.subscribe("test/#", qos=0):
        print("✓ 订阅成功: test/#")
    else:
        print("✗ 订阅失败")
    
    # 发布消息
    print("\n5. 发布测试消息...")
    for i in range(3):
        topic = "test/hello"
        message = f"Hello from Python test client - Message {i+1}"
        
        if manager.publish(topic, message, qos=0):
            print(f"✓ 发布成功 [{i+1}/3]: {topic} -> {message}")
        else:
            print(f"✗ 发布失败 [{i+1}/3]")
        
        time.sleep(1)
    
    # 等待接收消息
    print("\n6. 等待接收消息（10秒）...")
    print("   可以手动发送消息到 test/hello 主题来测试接收功能")
    print("   或者等待刚才发布的消息...")
    
    try:
        for i in range(10):
            time.sleep(1)
            status = manager.get_status()
            if status['status'] == 'connected':
                print(f"  等待中... {i+1}/10 (连接状态: 已连接)")
            else:
                print(f"  等待中... {i+1}/10 (连接状态: {status['status']})")
    except KeyboardInterrupt:
        print("\n   用户中断等待")
    
    # 显示状态信息
    print("\n7. 连接状态信息:")
    status = manager.get_status()
    print(f"   状态: {status['status']}")
    print(f"   主机: {status['host']}:{status['port']}")
    print(f"   客户端ID: {status['client_id']}")
    print(f"   统计信息:")
    print(f"     - 连接尝试次数: {status['stats']['connection_attempts']}")
    print(f"     - 发送消息数: {status['stats']['messages_sent']}")
    print(f"     - 接收消息数: {status['stats']['messages_received']}")
    
    # 断开连接
    print("\n8. 断开连接...")
    manager.disconnect()
    print("✓ 已断开连接")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试出错: {e}")
        import traceback
        traceback.print_exc()
