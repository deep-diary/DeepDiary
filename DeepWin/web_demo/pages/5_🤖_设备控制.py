"""
设备控制演示页面
展示DeepWin设备控制系统的各项功能
"""

import streamlit as st
import json
import time
from datetime import datetime

st.set_page_config(
    page_title="设备控制 - DeepWin",
    page_icon="🤖",
    layout="wide"
)

st.header("🤖 设备控制演示")
st.markdown("---")

# 页面标签页
tab1, tab2, tab3, tab4 = st.tabs([
    "🔌 设备连接", 
    "🎮 设备控制", 
    "📊 设备状态", 
    "📈 轨迹规划"
])

with tab1:
    st.subheader("🔌 设备连接")
    
    # 设备类型选择
    device_type = st.selectbox(
        "选择设备类型",
        ["DeepArm机械臂", "摄像头", "麦克风", "GPS模块", "其他设备"],
        index=0
    )
    
    if device_type == "DeepArm机械臂":
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**连接设置**")
            serial_port = st.selectbox(
                "串口选择",
                ["COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9", "COM10", "COM11"],
                index=10
            )
            baud_rate = st.selectbox(
                "波特率",
                ["9600", "19200", "38400", "57600", "115200"],
                index=4
            )
            
            if st.button("🔌 连接设备", type="primary"):
                with st.spinner("正在连接..."):
                    time.sleep(2)  # 模拟连接过程
                    st.success(f"✅ DeepArm机械臂已连接到 {serial_port}")
                    st.session_state.device_connected = True
        
        with col2:
            st.write("**连接状态**")
            if st.session_state.get('device_connected', False):
                st.success("🟢 已连接")
                st.info(f"串口: {serial_port}")
                st.info(f"波特率: {baud_rate}")
            else:
                st.error("🔴 未连接")
    
    elif device_type == "摄像头":
        st.info("📷 摄像头连接功能开发中...")
        camera_index = st.number_input("摄像头索引", min_value=0, max_value=10, value=0)
        if st.button("📷 连接摄像头"):
            st.success("✅ 摄像头连接成功")
    
    elif device_type == "GPS模块":
        st.info("📍 GPS模块连接功能开发中...")
        gps_port = st.text_input("GPS端口", value="/dev/ttyUSB0")
        if st.button("📍 连接GPS"):
            st.success("✅ GPS模块连接成功")

with tab2:
    st.subheader("🎮 设备控制")
    
    if not st.session_state.get('device_connected', False):
        st.warning("⚠️ 请先连接设备")
    else:
        # 控制模式选择
        control_mode = st.selectbox(
            "选择控制模式",
            ["手动控制", "轨迹执行", "自动模式", "示教模式"],
            index=0
        )
        
        if control_mode == "手动控制":
            st.write("**关节控制**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                joint1 = st.slider("关节1", -180.0, 180.0, 0.0, 1.0)
                joint2 = st.slider("关节2", -180.0, 180.0, 0.0, 1.0)
            
            with col2:
                joint3 = st.slider("关节3", -180.0, 180.0, 0.0, 1.0)
                joint4 = st.slider("关节4", -180.0, 180.0, 0.0, 1.0)
            
            with col3:
                joint5 = st.slider("关节5", -180.0, 180.0, 0.0, 1.0)
                joint6 = st.slider("关节6", -180.0, 180.0, 0.0, 1.0)
            
            if st.button("🎯 移动到指定位置"):
                joint_positions = [joint1, joint2, joint3, joint4, joint5, joint6]
                st.info(f"🎯 目标位置: {joint_positions}")
                with st.spinner("正在移动..."):
                    time.sleep(1)
                    st.success("✅ 移动完成")
        
        elif control_mode == "轨迹执行":
            st.write("**轨迹执行**")
            
            trajectory_file = st.file_uploader("选择轨迹文件", type=['json', 'yaml', 'csv'])
            if trajectory_file:
                st.success(f"📁 已选择轨迹文件: {trajectory_file.name}")
                
                if st.button("▶️ 执行轨迹"):
                    with st.spinner("正在执行轨迹..."):
                        time.sleep(3)
                        st.success("✅ 轨迹执行完成")
        
        elif control_mode == "示教模式":
            st.write("**示教模式**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📝 记录当前位置"):
                    current_pos = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]  # 模拟当前位置
                    st.session_state.taught_positions = st.session_state.get('taught_positions', [])
                    st.session_state.taught_positions.append({
                        "position": current_pos,
                        "timestamp": datetime.now().isoformat()
                    })
                    st.success("✅ 位置已记录")
            
            with col2:
                if st.button("🎯 回到示教位置"):
                    if st.session_state.get('taught_positions'):
                        st.success("✅ 已回到示教位置")
                    else:
                        st.warning("⚠️ 没有示教位置")

with tab3:
    st.subheader("📊 设备状态")
    
    if not st.session_state.get('device_connected', False):
        st.warning("⚠️ 请先连接设备")
    else:
        # 状态概览
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("运行状态", "运行中")
            st.metric("错误代码", "0")
        
        with col2:
            st.metric("关节温度", "45°C")
            st.metric("电机电流", "2.1A")
        
        with col3:
            st.metric("关节1角度", "0.0°")
            st.metric("关节2角度", "0.0°")
        
        with col4:
            st.metric("关节3角度", "0.0°")
            st.metric("关节4角度", "0.0°")
        
        # 实时状态监控
        st.write("**实时状态监控**")
        
        # 模拟实时数据
        try:
            import plotly.graph_objects as go
            import numpy as np
            
            # 生成模拟数据
            time_points = np.linspace(0, 10, 100)
            joint1_data = np.sin(time_points) * 30
            joint2_data = np.cos(time_points) * 20
            
            # 创建图表
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=time_points, y=joint1_data, name="关节1", line=dict(color='blue')))
            fig.add_trace(go.Scatter(x=time_points, y=joint2_data, name="关节2", line=dict(color='red')))
            
            fig.update_layout(
                title="关节角度变化",
                xaxis_title="时间 (秒)",
                yaxis_title="角度 (度)",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.info("📊 图表功能需要安装 plotly 和 numpy")
            st.code("pip install plotly numpy")

with tab4:
    st.subheader("📈 轨迹规划")
    
    # 轨迹类型
    trajectory_type = st.selectbox(
        "选择轨迹类型",
        ["直线轨迹", "圆弧轨迹", "样条轨迹", "自定义轨迹"],
        index=0
    )
    
    if trajectory_type == "直线轨迹":
        st.write("**起点和终点设置**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("起点坐标")
            start_x = st.number_input("X", value=0.0, format="%.2f")
            start_y = st.number_input("Y", value=0.0, format="%.2f")
            start_z = st.number_input("Z", value=0.0, format="%.2f")
        
        with col2:
            st.write("终点坐标")
            end_x = st.number_input("X", value=100.0, format="%.2f")
            end_y = st.number_input("Y", value=100.0, format="%.2f")
            end_z = st.number_input("Z", value=50.0, format="%.2f")
        
        # 轨迹参数
        velocity = st.slider("速度 (mm/s)", 10, 100, 50)
        acceleration = st.slider("加速度 (mm/s²)", 100, 1000, 500)
        
        if st.button("📐 生成直线轨迹"):
            st.success("✅ 直线轨迹已生成")
            
            # 显示轨迹信息
            trajectory_info = {
                "类型": "直线轨迹",
                "起点": [start_x, start_y, start_z],
                "终点": [end_x, end_y, end_z],
                "速度": f"{velocity} mm/s",
                "加速度": f"{acceleration} mm/s²",
                "距离": f"{((end_x-start_x)**2 + (end_y-start_y)**2 + (end_z-start_z)**2)**0.5:.2f} mm"
            }
            
            st.json(trajectory_info)
    
    elif trajectory_type == "圆弧轨迹":
        st.info("🔄 圆弧轨迹功能开发中...")
        center_x = st.number_input("圆心X", value=50.0)
        center_y = st.number_input("圆心Y", value=50.0)
        radius = st.number_input("半径", value=30.0)
        
        if st.button("🔄 生成圆弧轨迹"):
            st.success("✅ 圆弧轨迹已生成")
    
    elif trajectory_type == "自定义轨迹":
        st.info("✏️ 自定义轨迹功能开发中...")
        uploaded_file = st.file_uploader("上传轨迹文件", type=['csv', 'json'])
        if uploaded_file:
            st.success(f"📁 轨迹文件已上传: {uploaded_file.name}")

# 显示示教位置
if st.session_state.get('taught_positions'):
    st.markdown("---")
    st.subheader("📚 示教位置")
    
    for i, pos in enumerate(st.session_state.taught_positions):
        with st.expander(f"示教位置 {i+1}"):
            st.write(f"**位置**: {pos['position']}")
            st.write(f"**时间**: {pos['timestamp']}")
            
            if st.button(f"🗑️ 删除位置 {i+1}", key=f"delete_pos_{i}"):
                st.session_state.taught_positions.pop(i)
                st.success("✅ 示教位置已删除")
                st.rerun()
