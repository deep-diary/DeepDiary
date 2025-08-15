# command_test.py
# 测试 CommandParser 类的功能函数

from .command_parser import CommandParser
from .command_description import MotorSetSpeedCommand, MotorJogCommand

def test_basic_functionality():
    """测试基本功能"""
    print("=== 测试 CommandParser 基本功能 ===")
    
    # 1. 测试获取所有命令描述
    print("\n1. 测试获取所有命令描述:")
    all_commands = CommandParser.get_all_command_descriptions()
    print(f"✓ 总命令数量: {len(all_commands)}")
    
    # 2. 测试获取特定命令描述
    print("\n2. 测试获取特定命令描述:")
    cmd_desc = CommandParser.get_command_description("motor_set_speed")
    if cmd_desc:
        print(f"✓ 成功获取 motor_set_speed 描述: {cmd_desc['description']}")
        print(f"  示例: {cmd_desc['example']}")
        print(f"  语音提示: {cmd_desc['voice_prompt']}")
    else:
        print("✗ 获取 motor_set_speed 描述失败")

def test_model_functionality():
    """测试模型相关功能"""
    print("\n=== 测试模型相关功能 ===")
    
    # 1. 测试获取命令模型
    print("\n1. 测试获取命令模型:")
    model_class = CommandParser.get_command_model("motor_set_speed")
    if model_class:
        print(f"✓ 成功获取模型类: {model_class.__name__}")
        
        # 测试模型实例化
        try:
            instance = model_class()
            print(f"✓ 成功创建模型实例: {instance}")
        except Exception as e:
            print(f"✗ 创建模型实例失败: {e}")
    else:
        print("✗ 获取模型类失败")
    
    # 2. 测试获取所有命令名称
    print("\n2. 测试获取所有命令名称:")
    command_names = CommandParser.get_all_command_names()
    print(f"✓ 总命令名称数量: {len(command_names)}")
    print(f"  前5个命令: {command_names[:5]}")

def test_validation_functionality():
    """测试验证功能"""
    print("\n=== 测试验证功能 ===")
    
    # 1. 测试命令参数验证
    print("\n1. 测试命令参数验证:")
    try:
        params = {"spd": 2.0, "motor_id": 1}
        validated_cmd = CommandParser.validate_command("motor_set_speed", params)
        print(f"✓ 命令验证成功: {validated_cmd}")
    except Exception as e:
        print(f"✗ 命令验证失败: {e}")
    
    # 2. 测试无效命令验证
    print("\n2. 测试无效命令验证:")
    try:
        params = {"spd": 2.0}
        validated_cmd = CommandParser.validate_command("unknown_command", params)
        print(f"✗ 应该失败但成功了: {validated_cmd}")
    except Exception as e:
        print(f"✓ 正确捕获错误: {e}")

def test_string_parsing():
    """测试字符串解析功能"""
    print("\n=== 测试字符串解析功能 ===")
    
    # 测试各种命令字符串
    test_commands = [
        "motor_set_speed(2.0, 1)",
        "motor_jog(1, 1.5)",
        "motor_set_pos(1, 1.0)",
        "motor_enable(1)"
    ]
    
    for cmd_str in test_commands:
        try:
            result = CommandParser.parse_command_string(cmd_str)
            print(f"✓ 解析成功: {cmd_str}")
            print(f"  命令名: {result['command_name']}")
            print(f"  参数: {result['params']}")
        except Exception as e:
            print(f"✗ 解析失败: {cmd_str} - {e}")

def test_dashscope_parsing():
    """测试百炼平台命令字符串解析功能"""
    print("\n=== 测试百炼平台命令字符串解析功能 ===")
    
    # 测试各种命令字符串
    test_commands = [
        {"name": "motor_set_speed", "params": [{"name": "spd", "value": "1.5", "normValue": "1.5"}]},
        {"name": "motor_jog", "params": [{"name": "spd", "value": "1.5", "normValue": "1.5"}]},
        {"name": "motor_set_pos", "params": [{"name": "pos", "value": "1.0", "normValue": "1.0"}]},
        {"name": "motor_enable", "params": []}
    ]
    
    for cmd_str in test_commands:   
        try:
            command_name, params = CommandParser.parse_command_dashscope(cmd_str)
            print(f"✓ 解析成功: {command_name}")
            print(f"  参数: {params}")
        except Exception as e:
            print(f"✗ 解析失败: {cmd_str} - {e}")

def test_schema_generation():
    """测试Schema生成功能"""
    print("\n=== 测试Schema生成功能 ===")
    
    # 1. 测试单个命令Schema
    print("\n1. 测试单个命令Schema:")
    schema = CommandParser.get_command_schema("motor_set_speed")
    if schema:
        print(f"✓ 成功生成 motor_set_speed 的Schema")
        print(f"  标题: {schema.get('title', 'N/A')}")
        print(f"  属性数量: {len(schema.get('properties', {}))}")
    else:
        print("✗ Schema生成失败")
    
    # 2. 测试所有命令Schema
    print("\n2. 测试所有命令Schema:")
    all_schemas = CommandParser.get_all_schemas()
    print(f"✓ 成功生成所有命令的Schema，共 {len(all_schemas)} 个")

def test_category_filtering():
    """测试类别过滤功能"""
    print("\n=== 测试类别过滤功能 ===")
    
    # 获取特定类别的命令
    deep_motor_commands = CommandParser.get_commands_by_category("DeepMotor")
    print(f"✓ DeepMotor 类别命令数量: {len(deep_motor_commands)}")
    
    # 显示前几个命令
    for i, cmd in enumerate(deep_motor_commands[:3]):
        print(f"  {i+1}. {cmd['name']}: {cmd['description']}")

def test_voice_prompts():
    """测试语音提示功能"""
    print("\n=== 测试语音提示功能 ===")
    
    # 获取所有语音提示
    all_prompts = CommandParser.get_all_voice_prompts()
    print(f"✓ 总语音提示数量: {len(all_prompts)}")
    
    # 显示几个命令的语音提示
    for cmd_name, prompts in list(all_prompts.items())[:3]:
        print(f"  {cmd_name}: {prompts}")

def test_command_help():
    """测试命令帮助功能"""
    print("\n=== 测试命令帮助功能 ===")
    
    # 获取命令帮助信息
    help_info = CommandParser.get_command_help()
    print(f"✓ 帮助信息命令数量: {len(help_info)}")
    
    # 显示一个命令的完整帮助信息
    if "motor_set_speed" in help_info:
        cmd_help = help_info["motor_set_speed"]
        print(f"  motor_set_speed 帮助:")
        print(f"    描述: {cmd_help['description']}")
        print(f"    示例: {cmd_help['example']}")
        print(f"    语音提示: {cmd_help['voice_prompts']}")
        print(f"    类别: {cmd_help['category']}")

def test_command_search():
    """测试命令搜索功能"""
    print("\n=== 测试命令搜索功能 ===")
    
    # 测试关键词搜索
    search_keywords = ["转速", "位置", "电机", "设置"]
    
    for keyword in search_keywords:
        results = CommandParser.search_commands(keyword)
        print(f"✓ 搜索 '{keyword}' 找到 {len(results)} 个命令:")
        for result in results[:2]:  # 只显示前2个结果
            print(f"    - {result['name']}: {result['description']}")

def test_convenience_functions():
    """测试便捷函数"""
    print("\n=== 测试便捷函数 ===")
    
    # 导入便捷函数
    from command_parser import (
        get_command_model, 
        validate_command_params, 
        parse_command_string,
        get_all_command_names,
        get_command_schemas
    )
    
    # 测试便捷函数
    print("\n1. 测试便捷函数 - 获取模型:")
    model = get_command_model("motor_jog")
    if model:
        print(f"✓ 便捷函数获取模型成功: {model.__name__}")
    
    print("\n2. 测试便捷函数 - 验证参数:")
    try:
        cmd = validate_command_params("motor_jog", {"motor_id": 1, "spd": 1.5})
        print(f"✓ 便捷函数验证成功: {cmd}")
    except Exception as e:
        print(f"✗ 便捷函数验证失败: {e}")
    
    print("\n3. 测试便捷函数 - 解析字符串:")
    try:
        result = parse_command_string("motor_set_speed(2.0)")
        print(f"✓ 便捷函数解析成功: {result['command_name']}")
    except Exception as e:
        print(f"✗ 便捷函数解析失败: {e}")
    
    print("\n4. 测试便捷函数 - 获取命令名称:")
    names = get_all_command_names()
    print(f"✓ 便捷函数获取命令名称成功: {len(names)} 个")
    
    print("\n5. 测试便捷函数 - 获取Schema:")
    schemas = get_command_schemas()
    print(f"✓ 便捷函数获取Schema成功: {len(schemas)} 个")

def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")
    
    # 1. 测试未知命令
    print("\n1. 测试未知命令:")
    try:
        result = CommandParser.get_command_description("unknown_command")
        if result is None:
            print("✓ 正确处理未知命令，返回 None")
        else:
            print("✗ 未知命令应该返回 None")
    except Exception as e:
        print(f"✗ 处理未知命令时发生异常: {e}")
    
    # 2. 测试无效参数验证 - 修复版本
    print("\n2. 测试无效参数验证:")
    
    # 2.1 测试类型错误（应该失败）
    try:
        validated_cmd = CommandParser.validate_command("motor_set_speed", {"motor_id": "invalid_string", "spd": 2.0})
        print(f"✗ 类型错误应该失败但成功了: {validated_cmd}")
    except Exception as e:
        print(f"✓ 正确捕获类型验证错误: {e}")
    
    # 2.2 测试范围错误（应该失败）
    try:
        validated_cmd = CommandParser.validate_command("motor_set_speed", {"motor_id": 1, "spd": 100.0})  # 超过最大值50
        print(f"✗ 范围错误应该失败但成功了: {validated_cmd}")
    except Exception as e:
        print(f"✓ 正确捕获范围验证错误: {e}")
    
    # 2.3 测试缺失必需参数（应该使用默认值）
    try:
        validated_cmd = CommandParser.validate_command("motor_set_speed", {})  # 空参数
        print(f"✓ 缺失参数时使用默认值: {validated_cmd}")
        print(f"  这是正常行为，Pydantic 使用默认值填充缺失字段")
    except Exception as e:
        print(f"✗ 缺失参数时发生异常: {e}")
    
    # 2.4 测试未知字段（应该被忽略）
    try:
        validated_cmd = CommandParser.validate_command("motor_set_speed", {"motor_id": 1, "spd": 2.0, "unknown_field": "value"})
        print(f"✓ 未知字段被忽略: {validated_cmd}")
        print(f"  这是正常行为，Pydantic 忽略未知字段")
    except Exception as e:
        print(f"✗ 未知字段处理时发生异常: {e}")
    
    # 3. 测试无效字符串解析
    print("\n3. 测试无效字符串解析:")
    try:
        result = CommandParser.parse_command_string("invalid_command_string")
        print(f"✓ 解析无效字符串成功: {result}")
    except Exception as e:
        print(f"✗ 解析无效字符串时发生异常: {e}")

def test_pydantic_behavior_differences():
    """测试 Pydantic 不同配置下的行为差异"""
    print("\n=== 测试 Pydantic 行为差异 ===")
    
    # 定义两个不同的模型来对比行为
    from pydantic import BaseModel, Field, ConfigDict
    
    class WithDefaults(BaseModel):
        """有默认值的模型"""
        motor_id: int = Field(default=1, ge=1)
        spd: float = Field(default=1.5, ge=0, le=50)
    
    class WithoutDefaults(BaseModel):
        """无默认值的模型"""
        motor_id: int = Field(ge=1)
        spd: float = Field(ge=0, le=50)
    
    class StrictModel(BaseModel):
        """严格模式模型 - 不允许未知字段"""
        model_config = ConfigDict(extra='forbid')  # 禁止额外字段
        
        motor_id: int = Field(ge=1)
        spd: float = Field(ge=0, le=50)
    
    print("\n1. 测试有默认值的模型:")
    try:
        # 测试缺失参数
        cmd1 = WithDefaults()
        print(f"✓ 缺失参数时使用默认值: {cmd1}")
        
        # 测试未知字段
        cmd2 = WithDefaults(motor_id=2, spd=3.0, unknown_field="value")
        print(f"✓ 未知字段被忽略: {cmd2}")
        
    except Exception as e:
        print(f"✗ 有默认值模型异常: {e}")
    
    print("\n2. 测试无默认值的模型:")
    try:
        # 测试缺失参数（应该失败）
        cmd3 = WithoutDefaults()
        print(f"✗ 缺失参数应该失败但成功了: {cmd3}")
    except Exception as e:
        print(f"✓ 缺失参数时正确失败: {e}")
    
    try:
        # 测试未知字段（默认行为：被忽略）
        cmd4 = WithoutDefaults(motor_id=2, spd=3.0, unknown_field="value")
        print(f"✓ 未知字段被忽略（默认行为）: {cmd4}")
        
    except Exception as e:
        print(f"✗ 未知字段处理异常: {e}")
    
    print("\n3. 测试严格模式模型:")
    try:
        # 测试缺失参数（应该失败）
        cmd5 = StrictModel()
        print(f"✗ 缺失参数应该失败但成功了: {cmd5}")
    except Exception as e:
        print(f"✓ 缺失参数时正确失败: {e}")
    
    try:
        # 测试未知字段（应该失败）
        cmd6 = StrictModel(motor_id=2, spd=3.0, unknown_field="value")
        print(f"✗ 未知字段应该失败但成功了: {cmd6}")
    except Exception as e:
        print(f"✓ 未知字段时正确失败: {e}")
    
    print("\n4. 行为总结:")
    print("  - 有默认值: 宽松模式，自动填充缺失字段，忽略未知字段")
    print("  - 无默认值: 中等模式，必须提供所有字段，但忽略未知字段")
    print("  - 严格模式: 最严格，必须提供所有字段，不允许未知字段")
    print("\n5. 关键发现:")
    print("  - 默认情况下，Pydantic 总是忽略未知字段")
    print("  - 需要显式配置 ConfigDict(extra='forbid') 来禁止未知字段")
    print("  - 默认值只影响缺失字段的处理，不影响未知字段的处理")

def test_model_vs_instance_differences():
    """测试模型类和模型实例的区别"""
    print("\n=== 测试模型类和模型实例的区别 ===")
    
    from command_parser import CommandParser
    
    # 获取模型类
    model_class = CommandParser.get_command_model("motor_jog")
    print(f"\n1. 模型类信息:")
    print(f"  类型: {type(model_class)}")
    print(f"  名称: {model_class.__name__}")
    print(f"  模块: {model_class.__module__}")
    print(f"  是否为类: {isinstance(model_class, type)}")
    
    # 创建模型实例
    instance = model_class(motor_id=2, spd=3.0)
    print(f"\n2. 模型实例信息:")
    print(f"  类型: {type(instance)}")
    print(f"  是否为实例: {isinstance(instance, model_class)}")
    print(f"  数据内容: {instance}")
    
    # 对比区别
    print(f"\n3. 主要区别:")
    print(f"  模型类 vs 模型实例: {model_class} vs {instance}")
    print(f"  类型不同: {type(model_class)} vs {type(instance)}")
    print(f"  内容不同: 类定义 vs 具体数据")
    
    # 演示模型类的功能
    print(f"\n4. 模型类的功能:")
    print(f"  字段定义: {list(model_class.model_fields.keys())}")
    print(f"  Schema: {model_class.model_json_schema()['title']}")
    
    # 演示模型实例的功能
    print(f"\n5. 模型实例的功能:")
    print(f"  访问字段: motor_id = {instance.motor_id}")
    print(f"  访问字段: spd = {instance.spd}")
    print(f"  转换为字典: {instance.model_dump()}")
    print(f"  转换为JSON: {instance.model_dump_json()}")

if __name__ == "__main__":
    print("开始测试 CommandParser 类的所有功能...\n")
    
    # test_basic_functionality()
    # test_model_functionality()
    # test_validation_functionality()
    # test_string_parsing()
    # test_schema_generation()
    # test_category_filtering()
    # test_voice_prompts()
    # test_command_help()
    # test_command_search()
    # test_convenience_functions()
    # test_error_handling()
    # test_pydantic_behavior_differences()
    test_dashscope_parsing()
    # test_model_vs_instance_differences()
    
    print("\n🎉 所有测试完成！")
