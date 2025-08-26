#!/usr/bin/env python3
"""
测试路径管理器功能
"""

import os
import sys

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

def test_path_manager():
    """测试路径管理器"""
    try:
        print("=== 测试路径管理器 ===")
        
        # 导入路径管理器
        from deepwin.utils.path_manager import PathManager, get_path_manager
        print("✓ 路径管理器导入成功")
        
        # 测试基本路径管理器
        pm = PathManager()
        print("✓ 基本路径管理器创建成功")
        
        # 列出所有路径
        paths = pm.list_paths()
        print("默认路径配置:")
        for key, path in paths.items():
            print(f"  {key}: {path}")
        
        # 测试各种路径获取
        print(f"\n输出目录: {pm.get_output_path()}")
        print(f"模型目录: {pm.get_models_path()}")
        print(f"数据目录: {pm.get_data_path()}")
        print(f"日志目录: {pm.get_logs_path()}")
        
        # 测试子目录
        print(f"\n图像处理输出: {pm.get_image_processing_output_path()}")
        print(f"人脸检测输出: {pm.get_image_processing_output_path('face_detection')}")
        print(f"数据库SQLite路径: {pm.get_database_path('sqlite')}")
        print(f"备份路径: {pm.get_backup_path()}")
        
        return True
        
    except Exception as e:
        print(f"✗ 路径管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_path_manager_with_config():
    """测试带配置的路径管理器"""
    try:
        print("\n=== 测试带配置的路径管理器 ===")
        
        # 导入配置管理器
        from deepwin.config.config_manager import ConfigManager
        from deepwin.data_management.log_manager import LogManager
        from deepwin.utils.path_manager import PathManager
        
        # 初始化配置管理器
        log_manager = LogManager()
        config_manager = ConfigManager(log_manager)
        
        # 创建带配置的路径管理器
        pm = PathManager(config_manager)
        print("✓ 带配置的路径管理器创建成功")
        
        # 列出配置的路径
        paths = pm.list_paths()
        print("配置的路径:")
        for key, path in paths.items():
            print(f"  {key}: {path}")
        
        # 测试图像处理输出路径
        print(f"\n图像处理输出: {pm.get_image_processing_output_path()}")
        print(f"人脸检测输出: {pm.get_image_processing_output_path('face_detection')}")
        print(f"人脸识别输出: {pm.get_image_processing_output_path('face_recognition')}")
        
        # 测试数据库路径
        print(f"\n数据库路径:")
        print(f"  SQLite: {pm.get_database_path('sqlite')}")
        print(f"  Qdrant: {pm.get_database_path('qdrant')}")
        print(f"  FAISS: {pm.get_database_path('faiss')}")
        
        return True
        
    except Exception as e:
        print(f"✗ 带配置的路径管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_directory_creation():
    """测试目录创建功能"""
    try:
        print("\n=== 测试目录创建功能 ===")
        
        from deepwin.utils.path_manager import get_path_manager
        
        # 获取路径管理器
        pm = get_path_manager()
        
        # 测试创建各种目录
        output_path = pm.get_output_path('test_output', create=True)
        print(f"✓ 测试输出目录创建: {output_path}")
        
        models_path = pm.get_models_path('test_models', create=True)
        print(f"✓ 测试模型目录创建: {models_path}")
        
        data_path = pm.get_data_path('test_data', create=True)
        print(f"✓ 测试数据目录创建: {data_path}")
        
        # 清理测试目录
        import shutil
        if output_path.exists():
            shutil.rmtree(output_path)
            print("✓ 测试输出目录已清理")
        if models_path.exists():
            shutil.rmtree(models_path)
            print("✓ 测试模型目录已清理")
        if data_path.exists():
            shutil.rmtree(data_path)
            print("✓ 测试数据目录已清理")
        
        return True
        
    except Exception as e:
        print(f"✗ 目录创建测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始测试路径管理器...")
    
    # 运行测试
    tests = [
        ("基本路径管理器", test_path_manager),
        ("带配置的路径管理器", test_path_manager_with_config),
        ("目录创建功能", test_directory_creation)
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
