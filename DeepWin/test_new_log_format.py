#!/usr/bin/env python3
"""
测试新的日志格式
验证是否包含文件名和函数名
"""

import sys
import os
import logging

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def test_new_log_format():
    """测试新的日志格式"""
    # 创建新的日志配置，不使用单例LogManager
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(funcName)s:%(lineno)d - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('test_new_format.log', encoding='utf-8')
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    print("=== 测试新的日志格式 ===")
    print("格式: 时间 - 模块名 - 级别 - 文件名:函数名:行号 - 消息")
    print()
    
    # 测试不同级别的日志
    logger.info("这是一条测试日志信息")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    logger.debug("这是一条调试日志")
    
    print("\n=== 测试完成 ===")
    print("请检查控制台输出和 test_new_format.log 文件")

if __name__ == '__main__':
    test_new_log_format()
