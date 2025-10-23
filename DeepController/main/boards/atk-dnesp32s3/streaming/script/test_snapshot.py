#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试截图功能的脚本
"""

import requests
import time
import os
from datetime import datetime

def test_snapshot(web_port=8001):
    """测试截图功能"""
    url = f"http://localhost:{web_port}/snapshot"
    
    print(f"测试截图功能: {url}")
    print("=" * 50)
    
    try:
        # 发送截图请求
        print("发送截图请求...")
        start_time = time.time()
        
        response = requests.get(url, timeout=10)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"响应时间: {duration:.2f} 秒")
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            # 保存截图
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"test_snapshot_{timestamp}.jpg"
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            
            file_size = len(response.content)
            print(f"✅ 截图成功保存: {filename}")
            print(f"文件大小: {file_size} 字节")
            
            # 检查文件是否有效
            if file_size > 1000:  # JPEG文件应该至少1KB
                print("✅ 文件大小正常")
            else:
                print("⚠️  文件大小异常，可能不是有效的JPEG")
                
        else:
            print(f"❌ 截图失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败，请确保服务器正在运行")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

def test_status(web_port=8001):
    """测试状态接口"""
    url = f"http://localhost:{web_port}/status"
    
    print(f"\n测试状态接口: {url}")
    print("=" * 50)
    
    try:
        response = requests.get(url, timeout=5)
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            import json
            status = response.json()
            print("✅ 状态信息:")
            for key, value in status.items():
                print(f"  {key}: {value}")
        else:
            print(f"❌ 状态获取失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 状态测试失败: {e}")

if __name__ == "__main__":
    import sys
    
    web_port = 8001
    if len(sys.argv) > 1:
        web_port = int(sys.argv[1])
    
    print(f"ESP32 截图功能测试工具")
    print(f"Web端口: {web_port}")
    print("=" * 50)
    
    # 测试状态
    test_status(web_port)
    
    # 测试截图
    test_snapshot(web_port)
    
    print("\n测试完成！")
