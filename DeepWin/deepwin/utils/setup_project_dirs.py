#!/usr/bin/env python3
"""
设置项目目录结构

根据配置文件创建必要的目录结构，确保所有路径都存在。
"""

import os
import sys

# 添加项目路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

def setup_project_directories():
    """设置项目目录结构"""
    try:
        print("=== 设置项目目录结构 ===")
        
        # 导入路径管理器
        from deepwin.utils.path_manager import get_path_manager
        from deepwin.config.config_manager import ConfigManager
        from deepwin.data_management.log_manager import LogManager
        
        # 初始化配置管理器
        log_manager = LogManager()
        config_manager = ConfigManager(log_manager)
        
        # 获取路径管理器
        path_manager = get_path_manager(config_manager, project_root)
        
        print(f"项目根目录: {project_root}")
        
        # 确保所有基础目录存在
        print("\n创建基础目录:")
        directories = [
            ('output', '输出目录'),
            ('models', '模型目录'),
            ('data', '数据目录'),
            ('logs', '日志目录'),
            ('temp', '临时目录'),
            ('userdata', '用户数据目录'),
            ('configs', '配置目录'),
            ('resources', '资源目录')
        ]
        
        for dir_key, dir_name in directories:
            path = path_manager.get_path(dir_key, create=True)
            print(f"  ✓ {dir_name}: {path}")
        
        # 创建图像处理输出目录
        print("\n创建图像处理输出目录:")
        image_output = path_manager.get_image_processing_output_path(create=True)
        print(f"  ✓ 基础输出: {image_output}")
        
        # 创建各处理器的输出目录
        processors = ['face_detection', 'face_recognition', 'face_mesh', 'pose', 
                     'hand_gesture', 'ocr', 'qr_code', 'yolo']
        
        for processor in processors:
            processor_path = path_manager.get_image_processing_output_path(processor, create=True)
            print(f"  ✓ {processor}: {processor_path}")
        
        # 创建数据库相关目录
        print("\n创建数据库目录:")
        db_types = ['sqlite', 'qdrant', 'faiss']
        for db_type in db_types:
            db_path = path_manager.get_database_path(db_type, create=True)
            print(f"  ✓ {db_type}: {db_path}")
        
        # 创建备份目录
        backup_path = path_manager.get_backup_path(create=True)
        print(f"  ✓ 备份目录: {backup_path}")
        
        # 创建数据库备份子目录
        for db_type in db_types:
            db_backup_path = path_manager.get_backup_path(db_type, create=True)
            print(f"  ✓ {db_type}备份: {db_backup_path}")
        
        print("\n🎉 项目目录结构设置完成！")
        return True
        
    except Exception as e:
        print(f"✗ 设置项目目录结构失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_directories():
    """验证目录结构"""
    try:
        print("\n=== 验证目录结构 ===")
        
        from deepwin.utils.path_manager import get_path_manager
        from deepwin.config.config_manager import ConfigManager
        from deepwin.data_management.log_manager import LogManager
        
        # 初始化配置管理器
        log_manager = LogManager()
        config_manager = ConfigManager(log_manager)
        
        # 获取路径管理器
        path_manager = get_path_manager(config_manager, project_root)
        
        # 验证关键目录
        key_directories = [
            ('output', '输出目录'),
            ('models', '模型目录'),
            ('data', '数据目录'),
            ('logs', '日志目录')
        ]
        
        all_exist = True
        for dir_key, dir_name in key_directories:
            path = path_manager.get_path(dir_key, create=False)
            exists = path.exists()
            status = "✓" if exists else "✗"
            print(f"  {status} {dir_name}: {path} {'(存在)' if exists else '(不存在)'}")
            if not exists:
                all_exist = False
        
        # 验证图像处理输出目录
        image_output = path_manager.get_image_processing_output_path(create=False)
        exists = image_output.exists()
        status = "✓" if exists else "✗"
        print(f"  {status} 图像处理输出: {image_output} {'(存在)' if exists else '(不存在)'}")
        if not exists:
            all_exist = False
        
        if all_exist:
            print("\n🎉 所有关键目录验证通过！")
        else:
            print("\n❌ 部分目录验证失败，请检查权限或重新运行设置")
        
        return all_exist
        
    except Exception as e:
        print(f"✗ 验证目录结构失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始设置项目目录结构...")
    
    # 设置目录
    setup_success = setup_project_directories()
    
    if setup_success:
        # 验证目录
        verify_success = verify_directories()
        
        if verify_success:
            print("\n🎉 项目目录结构设置和验证全部完成！")
        else:
            print("\n⚠️ 目录设置完成，但验证失败，请检查权限")
    else:
        print("\n❌ 目录设置失败")

if __name__ == "__main__":
    main()
