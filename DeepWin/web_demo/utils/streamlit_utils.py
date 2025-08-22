"""
Streamlit工具函数
提供常用的Streamlit界面工具
"""

import streamlit as st
from datetime import datetime

def setup_page_config():
    """设置页面配置"""
    st.set_page_config(
        page_title="DeepWin 功能演示平台",
        page_icon="🚀",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/your-username/DeepDiary',
            'Report a bug': 'https://github.com/your-username/DeepDiary/issues',
            'About': 'DeepWin 是 DeepDiary 项目的桌面 GUI 应用程序'
        }
    )

def show_header():
    """显示页面头部"""
    # 自定义CSS样式
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: bold;
    }
    .main-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.9;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 显示头部信息
    st.markdown("""
    <div class="main-header">
        <h1>🚀 DeepWin 功能演示平台</h1>
        <p>体验强大的多模态记忆管理和设备控制功能</p>
    </div>
    """, unsafe_allow_html=True)

def show_footer():
    """显示页面底部"""
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**📚 相关文档**")
        st.markdown("- [项目架构](docs/architecture.md)")
        st.markdown("- [开发指南](docs/development.md)")
        st.markdown("- [API文档](docs/api.md)")
    
    with col2:
        st.markdown("**🔗 快速链接**")
        st.markdown("- [GitHub仓库](https://github.com/your-username/DeepDiary)")
        st.markdown("- [问题反馈](https://github.com/your-username/DeepDiary/issues)")
        st.markdown("- [功能请求](https://github.com/your-username/DeepDiary/discussions)")
    
    with col3:
        st.markdown("**ℹ️ 系统信息**")
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.markdown(f"- 当前时间: {current_time}")
        st.markdown("- 版本: v0.1.0")
        st.markdown("- 状态: 开发中")
    
    # 版权信息
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center; color: #666;'>"
        "© 2024 DeepDiary Project. All rights reserved."
        "</div>",
        unsafe_allow_html=True
    )

def show_success_message(message: str, icon: str = "✅"):
    """显示成功消息"""
    st.success(f"{icon} {message}")

def show_error_message(message: str, icon: str = "❌"):
    """显示错误消息"""
    st.error(f"{icon} {message}")

def show_warning_message(message: str, icon: str = "⚠️"):
    """显示警告消息"""
    st.warning(f"{icon} {message}")

def show_info_message(message: str, icon: str = "ℹ️"):
    """显示信息消息"""
    st.info(f"{icon} {message}")

def create_metric_card(title: str, value: str, delta: str = None, delta_color: str = "normal"):
    """创建指标卡片"""
    if delta:
        st.metric(label=title, value=value, delta=delta, delta_color=delta_color)
    else:
        st.metric(label=title, value=value)

def create_status_indicator(status: str, color: str = "green"):
    """创建状态指示器"""
    if color == "green":
        st.success(f"🟢 {status}")
    elif color == "red":
        st.error(f"🔴 {status}")
    elif color == "yellow":
        st.warning(f"🟡 {status}")
    elif color == "blue":
        st.info(f"🔵 {status}")
    else:
        st.write(f"⚪ {status}")

def create_progress_bar(label: str, value: float, max_value: float = 100):
    """创建进度条"""
    progress = value / max_value
    st.progress(progress)
    st.caption(f"{label}: {value:.1f}/{max_value:.1f} ({progress*100:.1f}%)")

def create_expandable_section(title: str, content: str, expanded: bool = False):
    """创建可展开的章节"""
    with st.expander(title, expanded=expanded):
        st.markdown(content)
