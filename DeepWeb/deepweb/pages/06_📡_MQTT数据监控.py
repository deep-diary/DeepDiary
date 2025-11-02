#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的MQTT数据监控页面
基于简化的MQTT管理器，大幅简化代码逻辑

作者: DeepDiary Team
日期: 2025-01-27
"""

import streamlit as st
import time
import json
from datetime import datetime
from typing import Dict, Any, List
import plotly.graph_objects as go
import plotly.express as px

# 导入简化的MQTT管理器和配置
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../services/cloud_communication/mqtt'))
from simple_mqtt_manager import SimpleMQTTManager, MQTTMessage
from mqtt_config import get_message_type_mapping, get_topic_fields
from data_management.log_manager import LogManager

# 初始化日志
logger = LogManager().get_logger(__name__)

def extract_device_id(topic: str) -> str:
    """从主题中提取设备ID"""
    try:
        parts = topic.split('/')
        if len(parts) >= 2 and parts[0] == 'device':
            return parts[1]
    except Exception:
        pass
    return "unknown"

def initialize_session_state():
    """初始化会话状态"""
    if 'mqtt_data' not in st.session_state:
        st.session_state.mqtt_data = {
            'device_info': [],
            'device_status': [],
            'device_system': [],
            'device_sensor': [],
            'device_actuator': [],
            'control': []
        }
    
    if 'mqtt_devices' not in st.session_state:
        st.session_state.mqtt_devices = set()
    
    if 'mqtt_manager' not in st.session_state:
        st.session_state.mqtt_manager = None

def mqtt_message_handler(message: MQTTMessage):
    """MQTT消息处理函数（线程安全版本）"""
    try:
        # 使用全局变量存储消息，避免 session_state 多进程问题
        if 'global_mqtt_messages' not in globals():
            globals()['global_mqtt_messages'] = []
        
        # 获取消息类型映射
        message_type_mapping = get_message_type_mapping()
        storage_key = message_type_mapping.get(message.message_type, message.message_type)
        
        # 添加消息到全局列表
        message_data = {
            'device_id': message.device_id,
            'topic': message.topic,
            'data': message.payload,
            'timestamp': message.timestamp,
            'message_type': storage_key,
            'received_at': datetime.now().isoformat()
        }
        
        globals()['global_mqtt_messages'].append(message_data)
        
        # 限制消息数量
        if len(globals()['global_mqtt_messages']) > 1000:
            globals()['global_mqtt_messages'] = globals()['global_mqtt_messages'][-1000:]
        
        logger.debug(f"消息已存储: {message.topic} -> {storage_key}")
    
    except Exception as e:
        logger.error(f"处理MQTT消息失败: {e}")

def process_global_messages():
    """处理全局消息队列"""
    if 'global_mqtt_messages' not in globals():
        return
    
    messages = globals()['global_mqtt_messages']
    if not messages:
        return
    
    # 处理消息
    processed_count = 0
    for message_data in messages:
        try:
            storage_key = message_data['message_type']
            
            if storage_key in st.session_state.mqtt_data:
                # 存储数据
                st.session_state.mqtt_data[storage_key].append({
                    'device_id': message_data['device_id'],
                    'topic': message_data['topic'],
                    'data': message_data['data'],
                    'timestamp': message_data['timestamp']
                })
                
                # 限制数据量
                if len(st.session_state.mqtt_data[storage_key]) > 100:
                    st.session_state.mqtt_data[storage_key] = st.session_state.mqtt_data[storage_key][-100:]
                
                # 更新设备集合
                if message_data['device_id'] != "unknown":
                    st.session_state.mqtt_devices.add(message_data['device_id'])
                
                processed_count += 1
            else:
                logger.warning(f"未知的消息类型: {storage_key}")
        
        except Exception as e:
            logger.error(f"处理消息失败: {e}")
    
    # 清空已处理的消息
    if processed_count > 0:
        globals()['global_mqtt_messages'] = []
        logger.info(f"处理了 {processed_count} 条MQTT消息")

def setup_mqtt_connection():
    """设置MQTT连接"""
    if st.session_state.mqtt_manager is None:
        try:
            st.session_state.mqtt_manager = SimpleMQTTManager(message_callback=mqtt_message_handler)
            st.session_state.mqtt_manager.connect()
            logger.info("MQTT连接已建立")
        except Exception as e:
            logger.error(f"建立MQTT连接失败: {e}")
            st.error(f"MQTT连接失败: {e}")

def display_device_info(data_list: List[Dict]):
    """显示设备信息"""
    if not data_list:
        st.info("暂无设备信息")
        return
    
    # 获取最新数据
    latest_data = data_list[-1]['data']
    
    st.markdown("#### 📱 设备基本信息")
    
    # 基本信息
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("设备ID", latest_data.get('device_id', 'N/A'))
        st.metric("设备类型", latest_data.get('device_type', 'N/A'))
        st.metric("固件版本", latest_data.get('firmware_version', 'N/A'))
    
    with col2:
        st.metric("MAC地址", latest_data.get('mac_address', 'N/A'))
        st.metric("芯片型号", latest_data.get('chip_model', 'N/A'))
        st.metric("芯片版本", latest_data.get('chip_revision', 'N/A'))
    
    # 硬件能力
    st.markdown("#### 🔧 硬件能力")
    capabilities = latest_data.get('hardware_capabilities', {})
    
    cols = st.columns(4)
    capability_items = [
        ('camera', '📷 摄像头'),
        ('can_bus', '🚌 CAN总线'),
        ('led_strip', '💡 LED灯带'),
        ('gimbal', '📹 云台'),
        ('arm', '🦾 机械臂'),
        ('motor', '⚙️ 电机'),
        ('sensor', '📡 传感器')
    ]
    
    for i, (key, label) in enumerate(capability_items):
        with cols[i % 4]:
            status = "✅" if capabilities.get(key, False) else "❌"
            st.write(f"{status} {label}")

def display_sensor_data(data_list: List[Dict]):
    """显示传感器数据"""
    if not data_list:
        st.info("暂无传感器数据")
        return
    
    # 获取最新数据
    latest_data = data_list[-1]['data']
    
    # 获取字段配置
    fields_config = get_topic_fields('device_status_sensor')
    
    st.markdown("#### 📊 传感器数值")
    
    # 按列显示字段
    if fields_config:
        cols = st.columns(max(1, min(3, len(fields_config))))
        col_idx = 0
        
        for field_name, field_config in fields_config.items():
            field_value = latest_data.get(field_name, 'N/A')
            field_desc = field_config.get('description', field_name)
            
            with cols[col_idx % len(cols)]:
                if isinstance(field_value, (int, float)):
                    st.metric(field_desc, f"{field_value:.2f}")
                else:
                    st.metric(field_desc, str(field_value))
            
            col_idx += 1
    
    # 加速度图表
    if any(key in latest_data for key in ['acc_x', 'acc_y', 'acc_z']):
        st.markdown("#### 📈 加速度趋势")
        
        # 准备数据
        chart_data = []
        for item in data_list[-20:]:  # 最近20条数据
            data = item['data']
            chart_data.append({
                '时间': datetime.fromtimestamp(data.get('timestamp', 0)).strftime('%H:%M:%S'),
                'X轴': data.get('acc_x', 0),
                'Y轴': data.get('acc_y', 0),
                'Z轴': data.get('acc_z', 0)
            })
        
        if chart_data:
            df = pd.DataFrame(chart_data)
            fig = px.line(df, x='时间', y=['X轴', 'Y轴', 'Z轴'], title='加速度变化趋势')
            st.plotly_chart(fig, use_container_width=True)

def display_actuator_data(data_list: List[Dict]):
    """显示执行器数据"""
    if not data_list:
        st.info("暂无执行器数据")
        return
    
    # 获取最新数据
    latest_data = data_list[-1]['data']
    
    st.markdown("#### ⚙️ 执行器状态")
    
    # 机械臂状态
    st.markdown("##### 🦾 机械臂")
    arm_data = latest_data.get('arm', {})
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = "✅ 已连接" if arm_data.get('connected', False) else "❌ 未连接"
        st.metric("连接状态", status)
    
    with col2:
        st.metric("电机数量", arm_data.get('motor_count', 0))
    
    with col3:
        st.metric("状态", arm_data.get('status', 'N/A'))
    
    # 电机状态
    st.markdown("##### ⚙️ 电机")
    motor_data = latest_data.get('motor', {})
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = "✅ 已连接" if motor_data.get('connected', False) else "❌ 未连接"
        st.metric("连接状态", status)
    
    with col2:
        st.metric("电机数量", motor_data.get('motor_count', 0))
    
    with col3:
        st.metric("状态", motor_data.get('status', 'N/A'))

def display_system_data(data_list: List[Dict]):
    """显示系统数据"""
    if not data_list:
        st.info("暂无系统数据")
        return
    
    # 获取最新数据
    latest_data = data_list[-1]['data']
    
    # 获取字段配置
    fields_config = get_topic_fields('device_status_system')
    
    st.markdown("#### 💻 系统状态")
    
    # 网络信息
    st.markdown("##### 🌐 网络信息")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("WiFi名称", latest_data.get('wifi_ssid', 'N/A'))
        st.metric("IP地址", latest_data.get('ip_address', 'N/A'))
    
    with col2:
        network_status = latest_data.get('network_status', 'N/A')
        status_color = "🟢" if network_status == "connected" else "🔴"
        st.metric("网络状态", f"{status_color} {network_status}")
    
    # 系统资源
    st.markdown("##### 📊 系统资源")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        free_heap = latest_data.get('free_heap', 0)
        st.metric("可用内存", f"{free_heap:,} 字节")
    
    with col2:
        uptime = latest_data.get('uptime_seconds', 0)
        hours = uptime // 3600
        minutes = (uptime % 3600) // 60
        st.metric("运行时间", f"{hours}小时{minutes}分钟")
    
    with col3:
        temp = latest_data.get('cpu_temperature', 0)
        st.metric("CPU温度", f"{temp}°C")

def main():
    """主函数"""
    st.set_page_config(
        page_title="MQTT数据监控",
        page_icon="📡",
        layout="wide"
    )
    
    st.title("📡 MQTT数据监控")
    st.markdown("实时监控MQTT主题数据，基于简化的架构")
    
    # 初始化
    initialize_session_state()
    
    # 设置MQTT连接
    setup_mqtt_connection()
    
    # 处理全局消息
    process_global_messages()
    
    # 数据统计
    total_messages = sum(len(data) for data in st.session_state.mqtt_data.values())
    device_count = len(st.session_state.mqtt_devices)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("设备数量", device_count)
    with col2:
        st.metric("总消息数", total_messages)
    with col3:
        status = "🟢 已连接" if st.session_state.mqtt_manager and st.session_state.mqtt_manager.is_connected() else "🔴 未连接"
        st.metric("MQTT状态", status)
    
    # 标签页
    tab1, tab2, tab3, tab4 = st.tabs(["📊 设备信息", "💻 系统状态", "📡 传感器数据", "⚙️ 执行器状态"])
    
    with tab1:
        display_device_info(st.session_state.mqtt_data['device_info'])
    
    with tab2:
        display_system_data(st.session_state.mqtt_data['device_system'])
    
    with tab3:
        display_sensor_data(st.session_state.mqtt_data['device_sensor'])
    
    with tab4:
        display_actuator_data(st.session_state.mqtt_data['device_actuator'])
    
    # 自动刷新
    time.sleep(1)
    st.rerun()

if __name__ == "__main__":
    main()