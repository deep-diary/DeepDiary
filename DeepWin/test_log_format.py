#!/usr/bin/env python3
"""
测试新的日志格式
验证是否包含文件名和函数名
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from src.data_management.log_manager import LogManager

def test_function():
    """测试函数，用于验证日志格式"""
    logger = LogManager().get_logger(__name__)
    logger.info("这是一条测试日志信息")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    logger.debug("这是一条调试日志")

def another_test_function():
    """另一个测试函数"""
    logger = LogManager().get_logger(__name__)
    logger.info("来自另一个函数的日志")

if __name__ == '__main__':
    print("=== 测试新的日志格式 ===")
    print("日志格式应该包含: 时间 - 模块名 - 级别 - 文件名:函数名:行号 - 消息")
    print("控制台格式应该包含: 级别 - 文件名:函数名 - 消息")
    print()
    
    # 测试日志
    test_function()
    another_test_function()
    
    print("\n=== 测试完成 ===")
    print("请检查控制台输出和logs目录中的日志文件")
    print("日志文件路径:", LogManager().log_file_path)
