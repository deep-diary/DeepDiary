#!/usr/bin/env python3
"""
简化的图像处理包配置测试
"""

import os
import sys

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
sys.path.insert(0, project_root)

def test_basic_imports():
    """测试基本导入"""
    try:
        print("=== 测试基本导入 ===")
        
        # 测试配置管理器导入
        from deepwin.config.config_manager import ConfigManager
        print("✓ ConfigManager 导入成功")
        
        # 测试日志管理器导入
        from deepwin.data_management.log_manager import LogManager
        print("✓ LogManager 导入成功")
        
        # 测试图像管理器导入（不创建实例）
        from deepwin.app_logic.memory_processing.image_processing.manager import ImageManager
        print("✓ ImageManager 导入成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 基本导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_loading():
    """测试配置加载"""
    try:
        print("\n=== 测试配置加载 ===")
        
        # 初始化日志管理器
        from deepwin.data_management.log_manager import LogManager
        log_manager = LogManager()
        
        # 初始化配置管理器
        from deepwin.config.config_manager import ConfigManager
        config_manager = ConfigManager(log_manager)
        
        # 测试图像处理配置
        image_config = config_manager.get('image_processing')
        if image_config:
            print("✓ 图像处理配置加载成功")
            print(f"  显示配置: {image_config.get('display', {})}")
            print(f"  追踪配置: {image_config.get('tracking', {})}")
            print(f"  处理器数量: {len(image_config.get('processors', {}))}")
        else:
            print("✗ 图像处理配置加载失败")
            
        # 测试处理器配置
        face_detection_config = config_manager.get('image_processing.processors.face_detection')
        if face_detection_config:
            print("✓ 人脸检测处理器配置加载成功")
            print(f"  配置内容: {face_detection_config}")
        else:
            print("✗ 人脸检测处理器配置加载失败")
            
        return True
        
    except Exception as e:
        print(f"✗ 配置测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_manager_class():
    """测试管理器类（不创建实例）"""
    try:
        print("\n=== 测试管理器类 ===")
        
        # 导入管理器类
        from deepwin.app_logic.memory_processing.image_processing.manager import ImageManager
        
        # 检查类属性
        print(f"✓ ImageManager 类导入成功")
        print(f"  类名: {ImageManager.__name__}")
        print(f"  基类: {ImageManager.__bases__}")
        
        # 检查方法
        methods = [method for method in dir(ImageManager) if not method.startswith('_')]
        print(f"  公共方法: {methods[:5]}...")  # 只显示前5个
        
        return True
        
    except Exception as e:
        print(f"✗ 管理器类测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始简化配置测试...")
    
    # 运行测试
    tests = [
        ("基本导入", test_basic_imports),
        ("配置加载", test_config_loading),
        ("管理器类", test_manager_class)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} 测试异常: {e}")
            results.append((test_name, False))
    
    # 显示测试结果
    print("\n=== 测试结果汇总 ===")
    success_count = 0
    for test_name, result in results:
        status = "成功" if result else "失败"
        print(f"{test_name}: {status}")
        if result:
            success_count += 1
    
    print(f"\n总测试数: {len(results)}, 成功: {success_count}, 失败: {len(results) - success_count}")
    
    if success_count == len(results):
        print("🎉 所有测试通过！")
    else:
        print("❌ 部分测试失败，请检查配置")

if __name__ == "__main__":
    main()
