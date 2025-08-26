#!/usr/bin/env python3
"""
测试图像处理包的配置管理
"""

import os
import sys

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
sys.path.insert(0, project_root)

def test_config_loading():
    """测试配置加载"""
    try:
        from deepwin.config.config_manager import ConfigManager
        from deepwin.data_management.log_manager import LogManager
        
        print("=== 测试配置加载 ===")
        
        # 初始化日志管理器
        log_manager = LogManager()
        logger = log_manager.get_logger(__name__)
        
        # 初始化配置管理器
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
        return False

def test_image_manager_creation():
    """测试图像管理器创建"""
    try:
        from deepwin.app_logic.memory_processing.image_processing import ImageManager
        from deepwin.config.config_manager import ConfigManager
        from deepwin.data_management.log_manager import LogManager
        
        print("\n=== 测试图像管理器创建 ===")
        
        # 初始化日志和配置管理器
        log_manager = LogManager()
        config_manager = ConfigManager(log_manager)
        
        # 创建图像管理器
        manager = ImageManager(log_manager, config_manager)
        
        # 测试处理器获取
        processors = manager.get_processor_names()
        print(f"✓ 图像管理器创建成功，可用处理器: {processors}")
        
        return True
        
    except Exception as e:
        print(f"✗ 图像管理器测试失败: {e}")
        return False

def test_processor_creation():
    """测试处理器创建"""
    try:
        from deepwin.app_logic.memory_processing.image_processing import ImageManager
        from deepwin.config.config_manager import ConfigManager
        from deepwin.data_management.log_manager import LogManager
        
        print("\n=== 测试处理器创建 ===")
        
        # 初始化日志和配置管理器
        log_manager = LogManager()
        config_manager = ConfigManager(log_manager)
        
        # 创建图像管理器
        manager = ImageManager(log_manager, config_manager)
        
        # 测试人脸检测处理器创建
        face_processor = manager.get_processor('face_detection')
        if face_processor:
            print("✓ 人脸检测处理器创建成功")
            print(f"  处理器类型: {type(face_processor).__name__}")
        else:
            print("✗ 人脸检测处理器创建失败")
            
        return True
        
    except Exception as e:
        print(f"✗ 处理器测试失败: {e}")
        return False

def main():
    """主函数"""
    print("开始测试图像处理包配置管理...")
    
    # 运行测试
    tests = [
        ("配置加载", test_config_loading),
        ("图像管理器创建", test_image_manager_creation),
        ("处理器创建", test_processor_creation)
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
