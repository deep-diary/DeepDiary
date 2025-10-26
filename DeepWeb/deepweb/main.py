#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepWeb 主程序入口
基于Streamlit的不倒翁设备Web控制界面

作者: DeepDiary Team
日期: 2025-10-26
"""

import streamlit as st
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
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
    
    # 初始化MQTT服务适配器
    if 'mqtt_adapter' not in st.session_state:
        from services.mqtt_service_adapter import MQTTServiceAdapter
        st.session_state.mqtt_adapter = MQTTServiceAdapter(
            st.session_state.mqtt_manager,
            st.session_state.device_manager
        )

def show_sidebar():
    """显示侧边栏"""
    with st.sidebar:
        st.title("🤖 DeepWeb")
        st.markdown("不倒翁设备控制平台")
        st.markdown("---")
        
        # 连接状态
        mqtt_status = st.session_state.mqtt_manager.get_status()
        if mqtt_status['status'] == 'connected':
            st.success("🟢 MQTT已连接")
        else:
            st.error("🔴 MQTT未连接")
        
        # 设备信息
        st.markdown("### 设备信息")
        devices = st.session_state.device_manager.get_devices()
        online_devices = sum(1 for d in devices.values() if d.status.value == 'online')
        st.info(f"在线设备: {online_devices}/{len(devices)}")
        
        # 视频流状态
        video_receiver = st.session_state.video_receiver
        if video_receiver.get_frame_count() > 0:
            st.success(f"🟢 视频流正常 ({video_receiver.get_frame_count()} 帧)")
        else:
            st.warning("🟡 等待视频流连接")
        
        st.markdown("---")
        
        # 快速操作
        st.markdown("### 快速操作")
        if st.button("🔄 刷新状态", use_container_width=True):
            st.rerun()
        
        if st.button("📹 摄像头监控", use_container_width=True):
            st.switch_page("pages/04_📹_摄像头监控.py")
        
        if st.button("🎮 设备控制", use_container_width=True):
            st.switch_page("pages/03_🎮_设备控制.py")

def main():
    """主程序入口"""
    # 设置页面配置
    st.set_page_config(
        page_title="DeepWeb - 不倒翁设备控制",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # 初始化会话状态
    initialize_session_state()
    
    # 显示侧边栏
    show_sidebar()
    
    # 主页面内容
    st.title("🏠 DeepWeb 控制中心")
    st.markdown("欢迎使用不倒翁设备控制平台")
    
    # 系统概览
    st.markdown("## 📊 系统概览")
    
    # 获取设备统计信息
    device_manager = st.session_state.device_manager
    stats = device_manager.get_device_statistics()
    
    # 显示统计卡片
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="总设备数",
            value=stats['total_devices'],
            delta=None
        )
    
    with col2:
        st.metric(
            label="在线设备",
            value=stats['online_devices'],
            delta=None
        )
    
    with col3:
        st.metric(
            label="离线设备",
            value=stats['offline_devices'],
            delta=None
        )
    
    with col4:
        st.metric(
            label="总命令数",
            value=stats['total_commands'],
            delta=None
        )
    
    st.markdown("---")
    
    # 设备列表
    st.markdown("## 🤖 设备列表")
    
    devices = device_manager.get_devices()
    
    if devices:
        for device_id, device in devices.items():
            with st.expander(f"{device_id} - {device.status.value.upper()}"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown(f"**设备类型**: {device.device_type}")
                    st.markdown(f"**固件版本**: {device.firmware_version}")
                    st.markdown(f"**IP地址**: {device.ip_address}")
                    st.markdown(f"**最后在线**: {device.last_seen if device.last_seen > 0 else '从未在线'}")
                
                with col2:
                    st.markdown(f"**可用堆内存**: {device.free_heap:,} bytes")
                    st.markdown(f"**运行时间**: {device.uptime_seconds:,} 秒")
                    st.markdown(f"**CPU温度**: {device.cpu_temperature:.1f}°C")
                    
                    # 组件状态
                    st.markdown("**组件状态**:")
                    for comp_name, comp_status in device.components.items():
                        status_emoji = "✅" if comp_status.value == "available" else "❌"
                        st.markdown(f"  {status_emoji} {comp_name}: {comp_status.value}")
    else:
        st.info("暂无设备连接")
    
    st.markdown("---")
    
    # 系统信息
    st.markdown("## ℹ️ 系统信息")
    
    mqtt_status = st.session_state.mqtt_manager.get_status()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**MQTT连接状态**")
        if mqtt_status['status'] == 'connected':
            st.success(f"🟢 已连接到 {mqtt_status['host']}:{mqtt_status['port']}")
        else:
            st.error(f"🔴 连接失败: {mqtt_status.get('last_error', 'Unknown error')}")
        
        st.markdown(f"**订阅主题数**: {mqtt_status['subscriptions_count']}")
        st.markdown(f"**发布主题数**: {mqtt_status['publish_topics_count']}")
        st.markdown(f"**发送消息数**: {mqtt_status['stats']['messages_sent']}")
        st.markdown(f"**接收消息数**: {mqtt_status['stats']['messages_received']}")
    
    with col2:
        st.markdown("**视频流状态**")
        video_receiver = st.session_state.video_receiver
        if video_receiver.get_frame_count() > 0:
            st.success(f"🟢 视频流正常 (已接收 {video_receiver.get_frame_count()} 帧)")
            if video_receiver.get_client_info():
                st.markdown(f"**客户端**: {video_receiver.get_client_info()}")
            if video_receiver.get_last_update():
                from datetime import datetime
                last_update = datetime.fromtimestamp(video_receiver.get_last_update())
                st.markdown(f"**最后更新**: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            st.warning("🟡 等待视频流连接")

if __name__ == "__main__":
    main()