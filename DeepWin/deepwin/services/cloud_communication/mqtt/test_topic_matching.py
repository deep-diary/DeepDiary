"""
测试主题匹配功能
验证MQTT通配符匹配逻辑是否正确
"""

from mqtt_manager import MQTTManager


def test_topic_matching():
    """测试主题匹配功能"""
    mqtt = MQTTManager(debug=False)
    
    # 测试用例
    test_cases = [
        # (topic, pattern, expected_result)
        ("device/status", "device/status", True),
        ("device/status", "device/control", False),
        ("device/001/status", "device/+/status", True),
        ("device/002/status", "device/+/status", True),
        ("sensor/temperature/data", "sensor/+/data", True),
        ("sensor/humidity/data", "sensor/+/data", True),
        ("sensor/temperature/data", "sensor/#", True),
        ("sensor/humidity/data", "sensor/#", True),
        ("sensor/temperature/data", "sensor/temperature/#", True),
        ("sensor/humidity/data", "sensor/temperature/#", False),
        ("device/001/status", "device/#", True),
        ("device/001/control", "device/#", True),
        ("system/logs", "system/#", True),
        ("user/123/profile", "user/+/profile", True),
        ("user/456/settings", "user/+/settings", True),
        ("user/123/profile", "user/+/settings", False),
    ]
    
    print("🧪 测试主题匹配功能...")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for topic, pattern, expected in test_cases:
        result = mqtt._topic_matches(topic, pattern)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
            
        print(f"{status} | 主题: {topic:<25} | 模式: {pattern:<20} | 期望: {expected} | 实际: {result}")
    
    print("=" * 60)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("🎉 所有测试通过！")
    else:
        print("⚠️  有测试失败，需要检查主题匹配逻辑")
        
    return failed == 0


if __name__ == "__main__":
    test_topic_matching()
