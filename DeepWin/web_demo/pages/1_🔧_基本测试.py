"""
基本测试页面
最简单的测试页面，不依赖任何外部模块
"""

import streamlit as st
import sys
from datetime import datetime

st.set_page_config(
    page_title="基本测试 - DeepWin",
    page_icon="🔧",
    layout="wide"
)

st.header("🔧 基本测试页面")
st.markdown("---")

st.write("这是一个最基本的测试页面，用于验证Streamlit是否正常工作。")

# 基本文本显示
st.subheader("文本显示测试")
st.write("这是普通文本")
st.markdown("**这是粗体文本**")
st.markdown("*这是斜体文本*")
st.markdown("`这是代码文本`")

# 基本交互元素
st.subheader("交互元素测试")

# 按钮
if st.button("测试按钮"):
    st.success("按钮点击成功！")

# 文本输入
text_input = st.text_input("输入框", "默认值")
st.write(f"输入的内容: {text_input}")

# 选择框
select_option = st.selectbox("选择框", ["选项A", "选项B", "选项C"])
st.write(f"选择的选项: {select_option}")

# 滑块
slider_value = st.slider("滑块", 0, 100, 50)
st.write(f"滑块值: {slider_value}")

# 复选框
checkbox_value = st.checkbox("复选框")
st.write(f"复选框状态: {checkbox_value}")

# 单选按钮
radio_option = st.radio("单选按钮", ["选项1", "选项2", "选项3"])
st.write(f"单选按钮选择: {radio_option}")

# 文件上传
st.subheader("文件上传测试")
uploaded_file = st.file_uploader("选择文件", type=['txt', 'pdf', 'png'])
if uploaded_file is not None:
    st.write(f"文件名: {uploaded_file.name}")
    st.write(f"文件大小: {uploaded_file.size} bytes")

# 列布局
st.subheader("布局测试")
col1, col2 = st.columns(2)

with col1:
    st.write("左列内容")
    st.button("左列按钮")

with col2:
    st.write("右列内容")
    st.button("右列按钮")

# 标签页
st.subheader("标签页测试")
tab1, tab2, tab3 = st.tabs(["标签1", "标签2", "标签3"])

with tab1:
    st.write("第一个标签页")
    st.info("标签页1内容")

with tab2:
    st.write("第二个标签页")
    st.warning("标签页2内容")

with tab3:
    st.write("第三个标签页")
    st.success("标签页3内容")

# 状态消息
st.subheader("状态消息测试")
st.success("成功消息")
st.error("错误消息")
st.warning("警告消息")
st.info("信息消息")

# 进度条
st.subheader("进度条测试")
progress_bar = st.progress(0)
for i in range(100):
    progress_bar.progress(i + 1)

# 指标显示
st.subheader("指标显示测试")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("温度", "25°C", "↑ 2°C")

with col2:
    st.metric("湿度", "60%", "↓ 5%")

with col3:
    st.metric("压力", "1013 hPa", "→ 0 hPa")

# 代码块
st.subheader("代码显示测试")
code = '''
def hello_world():
    print("Hello, World!")
    return "Success"

# 调用函数
result = hello_world()
print(result)
'''
st.code(code, language="python")

# 表格
st.subheader("表格显示测试")
data = {
    "姓名": ["张三", "李四", "王五"],
    "年龄": [25, 30, 35],
    "城市": ["北京", "上海", "广州"]
}

try:
    import pandas as pd
    df = pd.DataFrame(data)
    st.dataframe(df)
except ImportError:
    st.info("📊 表格功能需要安装 pandas")
    st.code("pip install pandas")

# 完成提示
st.success("🎉 基本测试页面完成！所有功能正常。")

# 调试信息
st.subheader("调试信息")
st.write(f"Streamlit版本: {st.__version__}")
st.write(f"Python版本: {sys.version}")
st.write(f"当前时间: {datetime.now()}")
