"""
简化演示页面
用于测试基本功能是否正常
"""

import streamlit as st

st.set_page_config(
    page_title="简化演示 - DeepWin",
    page_icon="🧪",
    layout="wide"
)

st.header("🧪 简化演示页面")
st.markdown("---")

st.write("这是一个简化的演示页面，用于测试基本功能。")

# 基本交互测试
st.subheader("基本交互测试")

# 按钮测试
if st.button("点击我", type="primary"):
    st.success("✅ 按钮点击成功！")

# 输入测试
user_input = st.text_input("输入一些文字", placeholder="在这里输入...")
if user_input:
    st.write(f"你输入了: {user_input}")

# 选择测试
option = st.selectbox("选择一个选项", ["选项1", "选项2", "选项3"])
st.write(f"你选择了: {option}")

# 滑块测试
value = st.slider("选择一个数值", 0, 100, 50)
st.write(f"滑块值: {value}")

# 列布局测试
st.subheader("列布局测试")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("指标1", "100", "↑ 10%")

with col2:
    st.metric("指标2", "200", "↓ 5%")

with col3:
    st.metric("指标3", "300", "→ 0%")

# 标签页测试
st.subheader("标签页测试")
tab1, tab2, tab3 = st.tabs(["标签1", "标签2", "标签3"])

with tab1:
    st.write("这是第一个标签页的内容")
    st.info("标签页功能正常")

with tab2:
    st.write("这是第二个标签页的内容")
    st.warning("标签页功能正常")

with tab3:
    st.write("这是第三个标签页的内容")
    st.success("标签页功能正常")

# 状态显示测试
st.subheader("状态显示测试")

st.success("✅ 成功消息")
st.error("❌ 错误消息")
st.warning("⚠️ 警告消息")
st.info("ℹ️ 信息消息")

# 代码显示测试
st.subheader("代码显示测试")

code = """
def hello_world():
    print("Hello, World!")
    return "Success"
"""
st.code(code, language="python")

# 数据展示测试
st.subheader("数据展示测试")

try:
    import pandas as pd
    import numpy as np
    
    # 创建示例数据
    data = {
        '姓名': ['张三', '李四', '王五', '赵六'],
        '年龄': [25, 30, 35, 28],
        '部门': ['技术', '产品', '设计', '运营'],
        '薪资': [15000, 18000, 16000, 12000]
    }
    
    df = pd.DataFrame(data)
    st.write("**员工信息表**")
    st.dataframe(df)
    
    # 图表测试
    st.subheader("图表测试")
    
    try:
        import plotly.express as px
        
        # 创建柱状图
        fig = px.bar(df, x='姓名', y='薪资', title='员工薪资分布')
        st.plotly_chart(fig, use_container_width=True)
        
    except ImportError:
        st.info("📊 图表功能需要安装 plotly")
        st.code("pip install plotly")
        
except ImportError:
    st.info("📊 数据功能需要安装 pandas 和 numpy")
    st.code("pip install pandas numpy")

st.success("🎉 简化演示页面测试完成！")
