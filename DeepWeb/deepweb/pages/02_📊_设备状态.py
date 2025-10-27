#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备状态页面
显示详细的设备状态信息和实时数据

作者: DeepDiary Team
日期: 2025-01-27
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import time
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入服务模块
from services.cloud_communication.mqtt.mqtt_manager import MQTTManager
from services.simple_video_receiver import get_video_receiver, start_video_service
from app_logic.device_logic_manager import DeviceLogicManager
from config.config_manager import ConfigManager

def initialize_session_state():
    """初始化会话状态"""
    # 初始化配置管理器
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = ConfigManager()
    
    # 初始化MQTT管理器
    if 'mqtt_manager' not in st.session_state:
        config = st.session_state.config_manager.get_config()
        mqtt_config = config.get('mqtt', {})
        st.session_state.mqtt_manager = MQTTManager(
            host=mqtt_config.get('host', 'localhost'),
            port=mqtt_config.get('port', 1883),
            username=mqtt_config.get('username'),
            password=mqtt_config.get('password'),
            debug=True
        )
    
    # 初始化设备逻辑管理器
    if 'device_manager' not in st.session_state:
        st.session_state.device_manager = DeviceLogicManager()
    
    # 初始化视频接收器
    if 'video_receiver' not in st.session_state:
        st.session_state.video_receiver = get_video_receiver()
        # 启动视频服务
        start_video_service()

# 初始化会话状态
initialize_session_state()

st.title("📊 设备状态监控")
st.markdown("实时监控设备状态和传感器数据")

# 获取设备管理器
device_manager = st.session_state.device_manager
devices = device_manager.get_devices()

if not devices:
    st.warning("暂无设备连接")
    st.stop()

# 设备选择
device_ids = list(devices.keys())
selected_device_id = st.selectbox("选择设备", device_ids)

if not selected_device_id:
    st.stop()

device = devices[selected_device_id]

# 刷新按钮
col1, col2, col3 = st.columns([1, 1, 8])
with col1:
    if st.button("🔄 刷新"):
        st.rerun()
with col2:
    auto_refresh = st.checkbox("自动刷新", value=False)

if auto_refresh:
    time.sleep(2)
    st.rerun()

st.markdown("---")

# 设备基本信息
st.markdown("## 📋 设备基本信息")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="设备状态",
        value=device.status.value.upper(),
        delta=None
    )

with col2:
    st.metric(
        label="可用内存",
        value=f"{device.free_heap:,} bytes",
        delta=None
    )

with col3:
    st.metric(
        label="运行时间",
        value=f"{device.uptime_seconds:,} 秒",
        delta=None
    )

with col4:
    st.metric(
        label="CPU温度",
        value=f"{device.cpu_temperature:.1f}°C",
        delta=None
    )

# 组件状态
st.markdown("## 🔧 组件状态")

components_data = []
for comp_name, comp_status in device.components.items():
    components_data.append({
        'Component': comp_name,
        'Status': comp_status.value,
        'Available': comp_status.value == 'available'
    })

if components_data:
    df_components = pd.DataFrame(components_data)
    
    # 创建组件状态图表
    fig = px.bar(
        df_components, 
        x='Component', 
        y='Available',
        color='Status',
        title="组件可用性状态",
        color_discrete_map={
            'available': '#28a745',
            'unavailable': '#dc3545',
            'error': '#ffc107'
        }
    )
    fig.update_layout(yaxis_title="Available", showlegend=True)
    st.plotly_chart(fig, width="stretch")

st.markdown("---")

# 传感器数据
if device.sensor_data:
    st.markdown("## 📡 传感器数据")
    
    sensor_data = device.sensor_data
    
    # 加速度数据
    if 'acceleration' in sensor_data:
        acc_data = sensor_data['acceleration']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 加速度 (m/s²)")
            
            # 加速度仪表盘
            fig_acc = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = acc_data.get('total', 0),
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "总加速度"},
                delta = {'reference': 9.81},
                gauge = {
                    'axis': {'range': [None, 20]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 9.81], 'color': "lightgray"},
                        {'range': [9.81, 15], 'color': "yellow"},
                        {'range': [15, 20], 'color': "red"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 15
                    }
                }
            ))
            fig_acc.update_layout(height=300)
            st.plotly_chart(fig_acc, width="stretch")
        
        with col2:
            st.markdown("### 三轴加速度")
            
            # 三轴加速度柱状图
            axes = ['X', 'Y', 'Z']
            values = [acc_data.get('x', 0), acc_data.get('y', 0), acc_data.get('z', 0)]
            
            fig_axes = go.Figure(data=[
                go.Bar(x=axes, y=values, marker_color=['red', 'green', 'blue'])
            ])
            fig_axes.update_layout(
                title="三轴加速度",
                xaxis_title="轴",
                yaxis_title="加速度 (m/s²)",
                height=300
            )
            st.plotly_chart(fig_axes, width="stretch")
    
    # 姿态数据
    if 'orientation' in sensor_data:
        st.markdown("### 姿态角度")
        
        orientation_data = sensor_data['orientation']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("俯仰角 (Pitch)", f"{orientation_data.get('pitch', 0):.2f}°")
        
        with col2:
            st.metric("横滚角 (Roll)", f"{orientation_data.get('roll', 0):.2f}°")

st.markdown("---")

# 电机数据
if device.motor_data:
    st.markdown("## ⚙️ 电机状态")
    
    motor_data = device.motor_data
    
    if 'motors' in motor_data and isinstance(motor_data['motors'], list):
        motors = motor_data['motors']
        
        # 电机状态表格
        motor_df_data = []
        for motor in motors:
            motor_df_data.append({
                'ID': motor.get('id', 'N/A'),
                'Position': f"{motor.get('position', 0):.2f}°",
                'Velocity': f"{motor.get('velocity', 0):.2f} rpm",
                'Torque': f"{motor.get('torque', 0):.2f} N·m",
                'Temperature': f"{motor.get('temperature', 0):.1f}°C",
                'Status': motor.get('status', 'unknown')
            })
        
        if motor_df_data:
            motor_df = pd.DataFrame(motor_df_data)
            st.dataframe(motor_df, width="stretch")
            
            # 电机位置图表
            if len(motors) > 0:
                motor_ids = [m.get('id', 0) for m in motors]
                positions = [m.get('position', 0) for m in motors]
                
                fig_motors = go.Figure(data=[
                    go.Bar(x=[f"Motor {mid}" for mid in motor_ids], y=positions)
                ])
                fig_motors.update_layout(
                    title="电机位置",
                    xaxis_title="电机",
                    yaxis_title="位置 (°)",
                    height=400
                )
                st.plotly_chart(fig_motors, width="stretch")

st.markdown("---")

# 机械臂数据
if device.arm_data:
    st.markdown("## 🤖 机械臂状态")
    
    arm_data = device.arm_data
    
    if 'joints' in arm_data and isinstance(arm_data['joints'], list):
        joints = arm_data['joints']
        
        # 关节状态表格
        joint_df_data = []
        for joint in joints:
            joint_df_data.append({
                'Joint ID': joint.get('joint_id', 'N/A'),
                'Angle': f"{joint.get('angle', 0):.2f}°",
                'Velocity': f"{joint.get('velocity', 0):.2f} rad/s",
                'Torque': f"{joint.get('torque', 0):.2f} N·m",
                'Status': joint.get('status', 'unknown')
            })
        
        if joint_df_data:
            joint_df = pd.DataFrame(joint_df_data)
            st.dataframe(joint_df, width="stretch")
    
    # 末端执行器位置
    if 'end_effector' in arm_data:
        ee_data = arm_data['end_effector']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 末端执行器位置 (mm)")
            if 'position' in ee_data:
                pos = ee_data['position']
                st.metric("X", f"{pos.get('x', 0):.2f}")
                st.metric("Y", f"{pos.get('y', 0):.2f}")
                st.metric("Z", f"{pos.get('z', 0):.2f}")
        
        with col2:
            st.markdown("### 末端执行器姿态 (°)")
            if 'orientation' in ee_data:
                ori = ee_data['orientation']
                st.metric("X", f"{ori.get('x', 0):.2f}")
                st.metric("Y", f"{ori.get('y', 0):.2f}")
                st.metric("Z", f"{ori.get('z', 0):.2f}")

st.markdown("---")

# 系统资源使用情况
st.markdown("## 💻 系统资源")

# 内存使用情况
if device.free_heap > 0:
    total_memory = 327680  # ESP32-S3 总内存 (假设)
    used_memory = total_memory - device.free_heap
    memory_usage = (used_memory / total_memory) * 100
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("内存使用率", f"{memory_usage:.1f}%")
    
    with col2:
        st.metric("可用内存", f"{device.free_heap:,} bytes")
    
    # 内存使用饼图
    fig_memory = go.Figure(data=[
        go.Pie(
            labels=['Used', 'Free'],
            values=[used_memory, device.free_heap],
            hole=0.3
        )
    ])
    fig_memory.update_layout(title="内存使用情况")
    st.plotly_chart(fig_memory, width="stretch")

# 最后更新时间
st.markdown("---")
if device.last_seen > 0:
    last_update = datetime.fromtimestamp(device.last_seen)
    st.info(f"最后更新: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
else:
    st.warning("设备从未在线")