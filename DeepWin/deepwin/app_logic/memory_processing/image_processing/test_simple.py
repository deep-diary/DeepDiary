#!/usr/bin/env python3
"""
简单的配置测试脚本
"""

import os
import sys

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
sys.path.insert(0, project_root)

def test_basic_config():
    """测试基本配置加载"""
    try:
        from deepwin.config.config_manager import ConfigManager
        from deepwin.data_management.log_manager import LogManager
        
        print("=== 测试基本配置加载 ===")
        
        # 初始化日志管理器
        log_manager = LogManager()
        
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
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("开始简单配置测试...")
    success = test_basic_config()
    
    if success:
        print("🎉 配置测试通过！")
    else:
        print("❌ 配置测试失败")
