#!/usr/bin/env python3
"""
DeepWin 爬虫服务配置示例
展示如何配置环境变量和参数
"""

import os

# 环境变量配置示例
ENV_CONFIG = {
    # Unsplash API 配置
    "UNSPLASH_ACCESS_KEY": "your_unsplash_api_key_here",
    
    # 爬虫配置
    "CRAWLER_MAX_WORKERS": "5",
    "CRAWLER_DELAY": "1.0",
    "CRAWLER_TIMEOUT": "30",
    
    # 输出目录配置
    "CRAWLER_OUTPUT_DIR": "../../output/crawler_images"
}

def setup_environment():
    """设置环境变量（示例）"""
    print("🔧 设置环境变量示例:")
    for key, value in ENV_CONFIG.items():
        print(f"  {key}={value}")
    
    print("\n💡 使用方法:")
    print("1. 在系统环境变量中设置这些值")
    print("2. 或在 .env 文件中设置")
    print("3. 或在代码中动态设置")
    
    # 示例：动态设置环境变量
    # os.environ["UNSPLASH_ACCESS_KEY"] = "your_actual_key"

def show_current_config():
    """显示当前配置"""
    print("\n📋 当前环境变量:")
    for key in ENV_CONFIG.keys():
        value = os.getenv(key, "未设置")
        status = "✅" if value != "未设置" else "❌"
        print(f"{status} {key}: {value}")

def create_env_file():
    """创建 .env 文件内容"""
    env_content = """# DeepWin 爬虫服务环境变量配置
# 复制此内容到 .env 文件并填入实际值

# Unsplash API 配置
UNSPLASH_ACCESS_KEY=your_unsplash_api_key_here

# 爬虫配置
CRAWLER_MAX_WORKERS=5
CRAWLER_DELAY=1.0
CRAWLER_TIMEOUT=30

# 输出目录配置
CRAWLER_OUTPUT_DIR=../../output/crawler_images
"""
    
    print("\n📝 .env 文件内容示例:")
    print("=" * 50)
    print(env_content)
    print("=" * 50)
    
    return env_content

if __name__ == "__main__":
    print("🚀 DeepWin 爬虫服务配置示例")
    print("=" * 50)
    
    setup_environment()
    show_current_config()
    create_env_file()
    
    print("\n🎯 下一步:")
    print("1. 获取 Unsplash API 密钥: https://unsplash.com/developers")
    print("2. 设置环境变量或创建 .env 文件")
    print("3. 运行 demo.py 测试功能")
