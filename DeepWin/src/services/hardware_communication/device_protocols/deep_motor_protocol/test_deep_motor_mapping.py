#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepMotorMapping 测试脚本
测试 map_and_call 函数的各种功能
"""

import sys
import os
import unittest
from unittest.mock import Mock, MagicMock
import tempfile
import shutil

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

class MockLogManager:
    """模拟日志管理器"""
    def __init__(self):
        self.logs = []
    
    def get_logger(self, name):
        return self
    
    def info(self, message):
        self.logs.append(f"INFO: {message}")
        print(f"INFO: {message}")
    
    def error(self, message):
        self.logs.append(f"ERROR: {message}")
        print(f"ERROR: {message}")
    
    def debug(self, message):
        self.logs.append(f"DEBUG: {message}")
        print(f"DEBUG: {message}")
    
    def warning(self, message):
        self.logs.append(f"WARNING: {message}")
        print(f"WARNING: {message}")

class MockConfigManager:
    """模拟配置管理器"""
    def __init__(self):
        self.config = {}
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value

class MockDeepMotorProtocol:
    """模拟DeepMotor协议"""
    def __init__(self):
        self.calls = []
    
    def create_motor_pos_frame(self, motor_id, position):
        self.calls.append(('create_motor_pos_frame', {'motor_id': motor_id, 'position': position}))
        return f"POS_FRAME_{motor_id}_{position}"
    
    def create_motor_spd_frame(self, motor_id, speed):
        self.calls.append(('create_motor_spd_frame', {'motor_id': motor_id, 'speed': speed}))
        return f"SPD_FRAME_{motor_id}_{speed}"
    
    def create_motor_torque_frame(self, motor_id, torque):
        self.calls.append(('create_motor_torque_frame', {'motor_id': motor_id, 'torque': torque}))
        return f"TORQUE_FRAME_{motor_id}_{torque}"
    
    def create_motor_enable_frame(self, motor_id):
        self.calls.append(('create_motor_enable_frame', {'motor_id': motor_id}))
        return f"ENABLE_FRAME_{motor_id}"
    
    def create_motor_reset_frame(self, motor_id):
        self.calls.append(('create_motor_reset_frame', {'motor_id': motor_id}))
        return f"RESET_FRAME_{motor_id}"
    
    def create_motor_zero_frame(self, motor_id):
        self.calls.append(('create_motor_zero_frame', {'motor_id': motor_id}))
        return f"ZERO_FRAME_{motor_id}"
    
    def create_motor_init_frame(self, motor_id):
        self.calls.append(('create_motor_init_frame', {'motor_id': motor_id}))
        return f"INIT_FRAME_{motor_id}"
    
    def create_motor_jog_frame(self, motor_id, jog_speed):
        self.calls.append(('create_motor_jog_frame', {'motor_id': motor_id, 'jog_speed': jog_speed}))
        return f"JOG_FRAME_{motor_id}_{jog_speed}"
    
    def create_motor_jog_stop_frame(self, motor_id):
        self.calls.append(('create_motor_jog_stop_frame', {'motor_id': motor_id}))
        return f"JOG_STOP_FRAME_{motor_id}"

def test_deep_motor_mapping():
    """测试DeepMotorMapping类"""
    print("=" * 60)
    print("开始测试 DeepMotorMapping 类")
    print("=" * 60)
    
    # 创建模拟对象
    log_manager = MockLogManager()
    config_manager = MockConfigManager()
    
    # 创建DeepMotorMapping实例
    try:
        from deep_motor_mapping import DeepMotorMapping
        
        # 替换协议对象为模拟对象
        mapping = DeepMotorMapping(log_manager, config_manager)
        mapping.deep_motor_protocol = MockDeepMotorProtocol()
        
        print("✓ DeepMotorMapping 实例创建成功")
        
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 创建实例失败: {e}")
        return False
    
    # 测试用例
    test_cases = [
        {
            "name": "测试电机使能命令",
            "command": "motor_enable",
            "params": {"motor_id": 1},
            "expected_result": "ENABLE_FRAME_1"
        },
        {
            "name": "测试电机位置设置命令",
            "command": "motor_set_pos",
            "params": {"motor_id": 2, "pos": 90.0},
            "expected_result": "POS_FRAME_2_90.0"
        },
        {
            "name": "测试电机速度设置命令",
            "command": "motor_set_speed",
            "params": {"motor_id": 3, "spd": 25.0},
            "expected_result": "SPD_FRAME_3_25.0"
        },
        {
            "name": "测试电机扭矩设置命令",
            "command": "motor_set_torque",
            "params": {"motor_id": 1, "torque": 5.0},
            "expected_result": "TORQUE_FRAME_1_5.0"
        },
        {
            "name": "测试电机重置命令",
            "command": "motor_reset",
            "params": {"motor_id": 4},
            "expected_result": "RESET_FRAME_4"
        },
        {
            "name": "测试电机零点标定命令",
            "command": "motor_zero",
            "params": {"motor_id": 1},
            "expected_result": "ZERO_FRAME_1"
        },
        {
            "name": "测试电机初始化命令",
            "command": "motor_init",
            "params": {"motor_id": 2},
            "expected_result": "INIT_FRAME_2"
        },
        {
            "name": "测试电机点动命令",
            "command": "motor_jog",
            "params": {"motor_id": 1, "spd": 15.0},
            "expected_result": "JOG_FRAME_1_15.0"
        },
        {
            "name": "测试电机停止点动命令",
            "command": "motor_jog_stop",
            "params": {"motor_id": 1},
            "expected_result": "JOG_STOP_FRAME_1"
        }
    ]
    
    # 执行测试
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        print(f"\n--- {test_case['name']} ---")
        
        try:
            # 调用map_and_call函数
            result = mapping.map_and_call(test_case['command'], test_case['params'])
            
            # 检查结果
            if result == test_case['expected_result']:
                print(f"✓ 测试通过: {test_case['command']}")
                print(f"  参数: {test_case['params']}")
                print(f"  结果: {result}")
                passed += 1
            else:
                print(f"✗ 测试失败: {test_case['command']}")
                print(f"  期望: {test_case['expected_result']}")
                print(f"  实际: {result}")
                failed += 1
                
        except Exception as e:
            print(f"✗ 测试异常: {test_case['command']}")
            print(f"  错误: {e}")
            failed += 1
    
    # 测试错误情况
    print(f"\n--- 测试错误情况 ---")
    
    # 测试未知命令
    try:
        result = mapping.map_and_call("unknown_command", {"motor_id": 1})
        print(f"✗ 应该抛出异常但成功了: unknown_command")
        failed += 1
    except ValueError as e:
        print(f"✓ 正确抛出异常: {e}")
        passed += 1
    
    
    # 测试获取支持的命令列表
    print(f"\n--- 测试辅助功能 ---")
    
    try:
        supported_commands = mapping.get_supported_commands()
        print(f"✓ 支持的命令列表: {supported_commands}")
        passed += 1
    except Exception as e:
        print(f"✗ 获取支持命令失败: {e}")
        failed += 1
    
    # 测试获取命令信息
    try:
        command_info = mapping.get_command_info("motor_enable")
        print(f"✓ 命令信息: {command_info}")
        passed += 1
    except Exception as e:
        print(f"✗ 获取命令信息失败: {e}")
        failed += 1
    
    # 测试动态添加命令映射
    try:
        def mock_function(**kwargs):
            return "MOCK_RESULT"
        
        mapping.add_command_mapping("test_command", mock_function, 
                                  {"test_param": "real_param"}, 
                                  {"test_param": {"type": str}})
        
        # 测试新添加的命令
        result = mapping.map_and_call("test_command", {"test_param": "test_value"})
        if result == "MOCK_RESULT":
            print(f"✓ 动态添加命令成功: test_command")
            passed += 1
        else:
            print(f"✗ 动态添加命令失败: {result}")
            failed += 1
            
    except Exception as e:
        print(f"✗ 动态添加命令失败: {e}")
        failed += 1
    
    # 输出测试结果
    print(f"\n" + "=" * 60)
    print(f"测试完成!")
    print(f"通过: {passed} 个测试")
    print(f"失败: {failed} 个测试")
    print(f"总计: {passed + failed} 个测试")
    
    if failed == 0:
        print(f"🎉 所有测试都通过了!")
        return True
    else:
        print(f"⚠️  有 {failed} 个测试失败，请检查代码")
        return False

def test_parameter_mapping():
    """测试参数映射功能"""
    print(f"\n" + "=" * 60)
    print("测试参数映射功能")
    print("=" * 60)
    
    log_manager = MockLogManager()
    config_manager = MockConfigManager()
    
    try:
        from deep_motor_mapping import DeepMotorMapping
        mapping = DeepMotorMapping(log_manager, config_manager)
        mapping.deep_motor_protocol = MockDeepMotorProtocol()
        
        # 测试参数映射
        test_mappings = [
            {
                "command": "motor_set_pos",
                "input_params": {"motor_id": 1, "pos": 45.0},
                "expected_mapped": {"motor_id": 1, "position": 45.0}
            },
            {
                "command": "motor_set_speed", 
                "input_params": {"motor_id": 2, "spd": 30.0},
                "expected_mapped": {"motor_id": 2, "speed": 30.0}
            }
        ]
        
        for test in test_mappings:
            print(f"\n测试命令: {test['command']}")
            print(f"输入参数: {test['input_params']}")
            
            # 获取参数映射
            param_mapping = mapping._param_mapping.get(test['command'], {})
            print(f"参数映射规则: {param_mapping}")
            
            # 手动执行映射
            mapped_params = {}
            for abstract_param, value in test['input_params'].items():
                actual_param = param_mapping.get(abstract_param, abstract_param)
                mapped_params[actual_param] = value
            
            print(f"映射后参数: {mapped_params}")
            print(f"期望参数: {test['expected_mapped']}")
            
            if mapped_params == test['expected_mapped']:
                print("✓ 参数映射正确")
            else:
                print("✗ 参数映射错误")
        
        return True
        
    except Exception as e:
        print(f"✗ 参数映射测试失败: {e}")
        return False

if __name__ == "__main__":
    print("DeepMotorMapping 测试脚本")
    print("=" * 60)
    
    # 运行主要测试
    main_test_result = test_deep_motor_mapping()
    
    # 运行参数映射测试
    mapping_test_result = test_parameter_mapping()
    
    # 最终结果
    print(f"\n" + "=" * 60)
    print("最终测试结果")
    print("=" * 60)
    
    if main_test_result and mapping_test_result:
        print("🎉 所有测试都通过了!")
        sys.exit(0)
    else:
        print("⚠️  部分测试失败，请检查代码")
        sys.exit(1)
