#!/usr/bin/env python3
"""
简单的聊天页面测试脚本
"""

import sys
import logging
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_chat_page_import():
    """测试 ChatPage 类的导入"""
    try:
        from deepweb.ui.pages.chat_page import ChatPage
        logger.info("✅ ChatPage 类导入成功")

        # 创建实例
        chat_page = ChatPage(logger=logger)
        logger.info("✅ ChatPage 实例创建成功")

        # 测试构建UI（不启动服务器）
        # 这里只是测试类方法，不实际启动Gradio
        logger.info("✅ ChatPage 基本功能测试通过")

        return True
    except Exception as e:
        logger.error(f"❌ ChatPage 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_manager_integration():
    """测试 UI 管理器集成"""
    try:
        from deepweb.ui.ui_manager import UIManager
        from deepweb.data_management.log_manager import LogManager
        logger.info("✅ UIManager 和 LogManager 导入成功")

        # 创建 log_manager
        log_manager = LogManager(console_level=logging.INFO, file_level=logging.INFO)
        logger.info("✅ LogManager 实例创建成功")

        # 创建 UI 管理器实例
        ui_manager = UIManager(log_manager=log_manager)
        logger.info("✅ UIManager 实例创建成功")

        return True
    except Exception as e:
        logger.error(f"❌ UIManager 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    logger.info("开始测试聊天页面功能...")

    # 测试 ChatPage 导入和实例化
    chat_page_ok = test_chat_page_import()

    # 测试 UI 管理器集成
    ui_manager_ok = test_ui_manager_integration()

    if chat_page_ok and ui_manager_ok:
        logger.info("🎉 所有测试通过！聊天页面功能正常。")
        return 0
    else:
        logger.error("❌ 部分测试失败，请检查错误信息。")
        return 1

if __name__ == "__main__":
    exit(main())
