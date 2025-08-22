"""
DeepWin Web演示平台主入口
提供基于Streamlit的Web界面，用于演示DeepWin的各项功能
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加项目根目录到路径（修正路径）
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入工具函数
from utils.streamlit_utils import setup_page_config, show_header, show_footer

def main():
    """主函数"""
    # 设置页面配置
    setup_page_config()
    
    # 显示页面头部
    show_header()
    
    # 显示首页内容
    show_home_page()
    
    # 显示页面底部
    show_footer()

def show_home_page():
    """显示首页"""
    st.title("🎉 欢迎使用 DeepWin 功能演示平台")
    st.markdown("---")
    
    # 项目介绍
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🚀 项目简介")
        st.markdown("""
        **DeepWin** 是 DeepDiary 项目的桌面 GUI 应用程序，作为云端与本地设备的桥梁。
        
        ### 主要功能
        - **本地记忆管理**: 多模态记忆的本地管理与追溯
        - **设备桥接与控制**: DeepDevice 与云端 DeepServer 之间的桥梁
        - **云端数据同步**: 本地数据与云端的高效双向同步
        - **智能体宿主**: 为智能体提供运行环境和协调机制
        
        ### 技术特点
        - 支持多种配置格式 (JSON/YAML/TOML/ENV)
        - 强大的测试基类系统
        - 模块化架构设计
        - 完善的错误处理和日志记录
        """)
    
    with col2:
        st.subheader("📊 系统状态")
        
        # 检查核心模块状态
        try:
            from deepwin.config.config_manager import ConfigManager
            st.success("✅ 配置管理器")
        except ImportError:
            st.error("❌ 配置管理器")
        
        try:
            from deepwin.utils.test import TestBase
            st.success("✅ 测试基类")
        except ImportError:
            st.error("❌ 测试基类")
        
        try:
            from deepwin.data_management.log_manager import LogManager
            st.success("✅ 日志管理器")
        except ImportError:
            st.error("❌ 日志管理器")
    
    # 快速开始
    st.subheader("🚀 快速开始")
    st.markdown("""
    1. **选择功能模块**: 在左侧边栏选择要演示的功能
    2. **查看配置**: 了解系统的配置结构和参数
    3. **运行测试**: 执行各种功能测试
    4. **查看结果**: 分析测试结果和性能指标
    """)
    
    # 系统信息
    st.subheader("ℹ️ 系统信息")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Python版本", sys.version.split()[0])
    
    with col2:
        st.metric("Streamlit版本", st.__version__)
    
    with col3:
        st.metric("项目路径", str(project_root))
    
    # 功能模块导航
    st.subheader("🔗 功能模块")
    st.markdown("""
    使用左侧边栏导航到不同的功能模块：
    
    - **🔧 基本测试**: 验证Streamlit基本功能
    - **🧪 简化演示**: 基本交互功能演示
    - **⚙️ 配置管理**: 配置管理功能演示
    - **🧠 记忆处理**: 记忆处理功能演示
    - **🤖 设备控制**: 设备控制功能演示
    - **🤖 AI功能**: AI功能演示
    """)

if __name__ == "__main__":
    main()
