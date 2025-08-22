"""
配置管理演示页面
展示DeepWin配置管理系统的各项功能
"""

import streamlit as st
import sys
import os
from pathlib import Path
import json

st.set_page_config(
    page_title="配置管理 - DeepWin",
    page_icon="⚙️",
    layout="wide"
)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

st.header("⚙️ 配置管理演示")
st.markdown("---")

# 页面标签页
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 配置查看", 
    "🧪 配置测试", 
    "🔧 环境变量", 
    "📊 配置分析"
])

with tab1:
    st.subheader("📋 配置查看")
    
    # 配置格式选择
    config_format = st.selectbox(
        "选择配置格式",
        ["JSON", "环境变量"],
        index=0
    )
    
    if config_format == "JSON":
        st.write("**JSON格式配置**")
        
        # 尝试加载DeepWin配置
        try:
            from deepwin.config.config_manager import ConfigManager
            config_manager = ConfigManager()
            config_data = config_manager.get_all()
            
            json_str = json.dumps(config_data, indent=2, ensure_ascii=False)
            st.code(json_str, language="json")
            
            # 下载按钮
            st.download_button(
                label="📥 下载JSON配置",
                data=json_str,
                file_name="config.json",
                mime="application/json"
            )
            
        except Exception as e:
            st.error(f"❌ 配置加载失败: {str(e)}")
            st.info("请确保DeepWin核心模块已正确安装")
            
            # 显示示例配置
            st.write("**示例配置结构**")
            example_config = {
                "general": {
                    "theme": "light",
                    "language": "zh-CN"
                },
                "device_settings": {
                    "deeparm_serial_port": "COM11",
                    "deeparm_baud_rate": 115200
                },
                "api": {
                    "llm_api_key": "your_api_key_here"
                }
            }
            st.json(example_config)
    
    else:
        st.write("**环境变量配置**")
        
        # 获取环境变量
        env_vars = {}
        for key, value in os.environ.items():
            if key.startswith(('DEEPWIN_', 'LLM_', 'DEEPARM_')):
                env_vars[key] = value
        
        if env_vars:
            for key, value in env_vars.items():
                st.code(f"{key}={value}")
            
            # 生成.env文件内容
            env_content = "\n".join([f"{key}={value}" for key, value in env_vars.items()])
            
            # 下载按钮
            st.download_button(
                label="📥 下载.env文件",
                data=env_content,
                file_name="config.env",
                mime="text/plain"
            )
        else:
            st.info("ℹ️ 未找到相关的环境变量")
            st.write("**提示**: 可以创建 `.env` 文件来配置环境变量")

with tab2:
    st.subheader("🧪 配置测试")
    
    # 测试类型选择
    test_type = st.selectbox(
        "选择测试类型",
        ["基本配置加载", "配置验证", "环境变量加载"],
        index=0
    )
    
    if st.button("🚀 运行测试", type="primary"):
        with st.spinner("正在运行测试..."):
            if test_type == "基本配置加载":
                st.success("✅ 基本配置加载测试完成")
                st.info("这是模拟的测试结果，实际功能需要DeepWin模块")
                
            elif test_type == "配置验证":
                st.success("✅ 配置验证测试完成")
                st.info("这是模拟的测试结果，实际功能需要DeepWin模块")
                
            else:
                st.success("✅ 环境变量加载测试完成")
                st.info("这是模拟的测试结果，实际功能需要DeepWin模块")

with tab3:
    st.subheader("🔧 环境变量管理")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.write("**当前环境变量**")
        
        # 显示环境变量列表
        env_vars = {}
        for key, value in os.environ.items():
            if key.startswith(('DEEPWIN_', 'LLM_', 'DEEPARM_')):
                env_vars[key] = value
        
        if env_vars:
            for key, value in env_vars.items():
                st.code(f"{key}={value}")
        else:
            st.info("未找到相关的环境变量")
    
    with col2:
        st.write("**添加/修改环境变量**")
        
        # 环境变量编辑表单
        new_key = st.text_input("环境变量名", placeholder="例如: DEEPWIN_API_KEY")
        new_value = st.text_input("环境变量值", placeholder="例如: your_api_key_here")
        
        if st.button("➕ 添加环境变量"):
            if new_key and new_value:
                os.environ[new_key] = new_value
                st.success(f"✅ 环境变量 {new_key} 已设置")
                st.rerun()
            else:
                st.warning("⚠️ 请填写完整的环境变量名和值")

with tab4:
    st.subheader("📊 配置分析")
    
    # 定义辅助函数
    def count_config_keys(config, prefix=""):
        """递归计算配置键的数量"""
        count = 0
        if isinstance(config, dict):
            for key, value in config.items():
                current_key = f"{prefix}.{key}" if prefix else key
                count += 1
                if isinstance(value, (dict, list)):
                    count += count_config_keys(value, current_key)
        elif isinstance(config, list):
            for i, item in enumerate(config):
                current_key = f"{prefix}[{i}]"
                count += 1
                if isinstance(item, (dict, list)):
                    count += count_config_keys(item, current_key)
        return count

    def show_config_tree(config, level=0):
        """显示配置结构树"""
        indent = "  " * level
        
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, (dict, list)):
                    st.text(f"{indent}📁 {key}")
                    show_config_tree(value, level + 1)
                else:
                    st.text(f"{indent}📄 {key}: {str(value)[:50]}{'...' if len(str(value)) > 50 else ''}")
        elif isinstance(config, list):
            for i, item in enumerate(config):
                if isinstance(item, (dict, list)):
                    st.text(f"{indent}📁 [{i}]")
                    show_config_tree(item, level + 1)
                else:
                    st.text(f"{indent}📄 [{i}]: {str(item)[:50]}{'...' if len(str(item)) > 50 else ''}")
    
    try:
        # 尝试获取配置数据
        from deepwin.config.config_manager import ConfigManager
        config_manager = ConfigManager()
        all_config = config_manager.get_all()
        
        # 配置统计
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_keys = count_config_keys(all_config)
            st.metric("配置项总数", total_keys)
        
        with col2:
            config_size = len(json.dumps(all_config, ensure_ascii=False))
            st.metric("配置大小", f"{config_size} 字符")
        
        with col3:
            sections = len(all_config.keys()) if isinstance(all_config, dict) else 0
            st.metric("配置节数", sections)
        
        # 配置结构树
        st.write("**配置结构树**")
        show_config_tree(all_config)
        
    except Exception as e:
        st.error(f"❌ 配置分析失败: {str(e)}")
        st.info("请确保DeepWin核心模块已正确安装")
        
        # 显示示例分析
        st.write("**示例配置分析**")
        example_config = {
            "general": {"theme": "light", "language": "zh-CN"},
            "device_settings": {"serial_port": "COM11", "baud_rate": 115200},
            "api": {"key": "example"}
        }
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("配置项总数", "6")
        with col2:
            st.metric("配置大小", "约 150 字符")
        with col3:
            st.metric("配置节数", "3")
        
        st.write("**示例配置结构**")
        show_config_tree(example_config)
