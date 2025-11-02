"""
paho-mqtt 回调函数参数详解示例
演示 userdata, flags, properties 的使用
"""
import paho.mqtt.client as mqtt
import json


# ========== 1. userdata 参数 ==========
# userdata 是在创建客户端时传递的用户自定义数据
# 可以在所有回调函数中访问，用于传递上下文信息

# 示例：传递自定义数据
class MyContext:
    def __init__(self):
        self.device_id = "device_001"
        self.user_name = "user123"
        self.callback_count = 0

context = MyContext()

def on_connect_with_userdata(client, userdata, flags, reason_code, properties):
    """连接回调 - 使用 userdata"""
    print(f"=== 连接回调 ===")
    print(f"userdata 类型: {type(userdata)}")
    
    # 访问 userdata 中的自定义数据
    if userdata:
        print(f"设备ID: {userdata.device_id}")
        print(f"用户名: {userdata.user_name}")
        userdata.callback_count += 1
        print(f"回调计数: {userdata.callback_count}")
    
    print(f"连接结果码: {reason_code}")


# 创建客户端并设置 userdata
# client = mqtt.Client(
#     client_id="test",
#     callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
#     userdata=context  # 设置 userdata
# )
# client.on_connect = on_connect_with_userdata


# ========== 2. flags 参数 ==========
# flags 是一个字典，包含服务器返回的连接标志信息
# 主要包含 "session present" 标志（MQTT 3.1.1 和 5.0 都有）

def on_connect_with_flags(client, userdata, flags, reason_code, properties):
    """连接回调 - 使用 flags"""
    print(f"=== 连接回调 ===")
    print(f"flags 类型: {type(flags)}")
    print(f"flags 内容: {flags}")
    
    # flags 是一个字典，主要包含：
    # - 'session present': bool - 表示服务器是否保留了之前的会话
    if isinstance(flags, dict):
        session_present = flags.get('session present', False)
        print(f"会话是否保留: {session_present}")
        
        if session_present:
            print("✓ 服务器保留了之前的会话（包括订阅信息）")
        else:
            print("✗ 这是一个新会话")


# ========== 3. properties 参数 ==========
# properties 是 MQTT 5.0 协议的新特性
# 包含连接的属性信息（仅 MQTT 5.0 可用，MQTT 3.1.1 为 None）

def on_connect_with_properties(client, userdata, flags, reason_code, properties):
    """连接回调 - 使用 properties (MQTT 5.0)"""
    print(f"=== 连接回调 ===")
    print(f"properties 类型: {type(properties)}")
    
    if properties:
        print(f"✓ 这是 MQTT 5.0 连接，properties 可用")
        print(f"properties 对象: {properties}")
        
        # properties 是 Properties 对象，包含：
        # - session_expiry_interval: 会话过期时间
        # - receive_maximum: 最大接收数量
        # - maximum_qos: 最大 QoS 等级
        # - retain_available: 是否支持保留消息
        # - maximum_packet_size: 最大数据包大小
        # - assigned_client_identifier: 服务器分配的客户端ID
        # - server_keep_alive: 服务器建议的 keepalive
        # - response_information: 响应信息
        # - server_reference: 服务器参考
        # - authentication_method: 认证方法
        # - authentication_data: 认证数据
        
        # 示例：检查会话过期时间
        if hasattr(properties, 'session_expiry_interval'):
            expiry = properties.session_expiry_interval
            if expiry is not None:
                print(f"会话过期时间: {expiry} 秒")
        
        # 示例：检查最大 QoS
        if hasattr(properties, 'maximum_qos'):
            max_qos = properties.maximum_qos
            print(f"服务器支持的最大 QoS: {max_qos}")
    else:
        print("✗ 这是 MQTT 3.1.1 连接，properties 为 None")


# ========== 4. reason_code 参数 ==========
# reason_code 表示连接或断开的原因（MQTT 5.0）
# MQTT 3.1.1 中使用 rc (整数返回码)

def on_connect_reason_code(client, userdata, flags, reason_code, properties):
    """连接回调 - 使用 reason_code"""
    print(f"=== 连接回调 ===")
    
    # reason_code 是 ReasonCode 对象（MQTT 5.0）或整数（MQTT 3.1.1）
    print(f"reason_code 类型: {type(reason_code)}")
    print(f"reason_code 值: {reason_code}")
    
    # 检查是否成功
    if hasattr(reason_code, 'is_failure'):
        # MQTT 5.0
        if reason_code.is_failure:
            print(f"✗ 连接失败: {reason_code}")
        else:
            print(f"✓ 连接成功: {reason_code}")
    else:
        # MQTT 3.1.1 (rc 是整数，0 表示成功)
        if reason_code == 0:
            print("✓ 连接成功")
        else:
            print(f"✗ 连接失败，返回码: {reason_code}")


def on_disconnect_reason_code(client, userdata, flags, reason_code, properties):
    """断开回调 - 使用 reason_code"""
    print(f"=== 断开回调 ===")
    print(f"reason_code: {reason_code}")
    
    if hasattr(reason_code, 'getName'):
        print(f"断开原因名称: {reason_code.getName()}")
        print(f"断开原因值: {reason_code.value}")
    
    # 常见的断开原因：
    # - 0: 正常断开（客户端调用 disconnect()）
    # - 1: 意外断开（网络问题、服务器关闭等）


# ========== 完整示例 ==========
def complete_example():
    """完整的回调函数示例"""
    
    # 创建自定义上下文
    class ConnectionContext:
        def __init__(self):
            self.device_id = "device_001"
            self.reconnect_count = 0
            self.last_connect_time = None
    
    context = ConnectionContext()
    
    def on_connect_complete(client, userdata, flags, reason_code, properties):
        """完整的连接回调示例"""
        print("\n" + "="*50)
        print("连接回调触发")
        print("="*50)
        
        # 1. 使用 userdata
        if userdata:
            import time
            userdata.last_connect_time = time.time()
            print(f"设备ID (from userdata): {userdata.device_id}")
            print(f"重连次数: {userdata.reconnect_count}")
            userdata.reconnect_count += 1
        
        # 2. 使用 flags
        if flags and 'session present' in flags:
            if flags['session present']:
                print("✓ 服务器保留了会话（之前的订阅仍然有效）")
            else:
                print("✗ 新会话（需要重新订阅）")
        
        # 3. 使用 reason_code
        if hasattr(reason_code, 'is_failure'):
            if not reason_code.is_failure:
                print(f"✓ 连接成功: {reason_code}")
            else:
                print(f"✗ 连接失败: {reason_code}")
        else:
            if reason_code == 0:
                print("✓ 连接成功")
            else:
                print(f"✗ 连接失败，返回码: {reason_code}")
        
        # 4. 使用 properties (MQTT 5.0)
        if properties:
            print(f"MQTT 5.0 属性:")
            if hasattr(properties, 'session_expiry_interval'):
                print(f"  - 会话过期时间: {properties.session_expiry_interval}")
            if hasattr(properties, 'maximum_qos'):
                print(f"  - 最大 QoS: {properties.maximum_qos}")
        
        print("="*50 + "\n")
    
    # 创建客户端（需要时才取消注释）
    # client = mqtt.Client(
    #     client_id="example_client",
    #     callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
    #     userdata=context  # 传递自定义数据
    # )
    # client.on_connect = on_connect_complete
    # 
    # client.connect("localhost", 1883)
    # client.loop_start()


if __name__ == "__main__":
    import time
    
    print("paho-mqtt 回调函数参数说明:")
    print("\n1. userdata: 用户自定义数据，可在回调中访问")
    print("2. flags: 连接标志字典，包含 'session present' 等信息")
    print("3. properties: MQTT 5.0 属性对象（MQTT 3.1.1 为 None）")
    print("4. reason_code: 连接/断开原因码")
    
    # complete_example()
