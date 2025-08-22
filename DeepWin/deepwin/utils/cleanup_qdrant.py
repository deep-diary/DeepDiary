#!/usr/bin/env python3
"""
清理Qdrant数据库文件夹冲突的脚本
"""

import os
import shutil
import time

def cleanup_qdrant_folders():
    """清理Qdrant数据库文件夹"""
    print("开始清理Qdrant数据库文件夹...")
    
    # 可能的Qdrant数据库路径
    qdrant_paths = [
        "database/qdrant/demo",
        "database/qdrant/test", 
        "database/qdrant/quick_test",
        "database/qdrant/old"
    ]
    
    for path in qdrant_paths:
        if os.path.exists(path):
            try:
                print(f"删除文件夹: {path}")
                shutil.rmtree(path)
                print(f"成功删除: {path}")
            except Exception as e:
                print(f"删除失败 {path}: {e}")
        else:
            print(f"文件夹不存在: {path}")
    
    print("Qdrant数据库文件夹清理完成！")

if __name__ == "__main__":
    cleanup_qdrant_folders()
