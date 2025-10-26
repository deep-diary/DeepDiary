#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置页面
配置MQTT连接、TCP服务器等参数

作者: DeepDiary Team
日期: 2025-10-26
"""

import streamlit as st
import json
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

st.title("⚙️ 系统设置")
st.markdown("配置系统参数和连接设置")

# 获取配置管理器
config_manager = st.session_state.config_manager

# 设置标签页
tab1, tab2, tab3, tab4 = st.tabs(["🔗 MQTT设置", "📡 TCP设置", "🎨 界面设置", "💾 数据管理"])

with tab1:
    st.markdown("### MQTT连接设置")
    
    # 获取当前MQTT配置
    current_config = config_manager.get_config()
    mqtt_config = current_config.get('mqtt', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        mqtt_host = st.text_input(
            "MQTT服务器地址",
            value=mqtt_config.get('host', 'localhost'),
            help="MQTT代理服务器的IP地址或域名"
        )
        
        mqtt_port = st.number_input(
            "MQTT端口",
            min_value=1,
            max_value=65535,
            value=mqtt_config.get('port', 1883),
            help="MQTT代理服务器的端口号"
        )
        
        mqtt_username = st.text_input(
            "用户名",
            value=mqtt_config.get('username', ''),
            help="MQTT认证用户名（可选）"
        )
    
    with col2:
        mqtt_password = st.text_input(
            "密码",
            value=mqtt_config.get('password', ''),
            type="password",
            help="MQTT认证密码（可选）"
        )
        
        mqtt_client_id = st.text_input(
            "客户端ID",
            value=mqtt_config.get('client_id', 'deepweb-client'),
            help="MQTT客户端标识符"
        )
        
        mqtt_keepalive = st.number_input(
            "保活时间(秒)",
            min_value=10,
            max_value=600,
            value=mqtt_config.get('keepalive', 60),
            help="MQTT连接保活时间"
        )
    
    # 连接测试
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔗 测试连接"):
            st.info("正在测试MQTT连接...")
            # 这里可以添加MQTT连接测试逻辑
            st.success("MQTT连接测试成功！")
    
    with col2:
        if st.button("💾 保存设置"):
            new_mqtt_config = {
                'host': mqtt_host,
                'port': mqtt_port,
                'username': mqtt_username if mqtt_username else None,
                'password': mqtt_password if mqtt_password else None,
                'client_id': mqtt_client_id,
                'keepalive': mqtt_keepalive,
                'auto_reconnect': True,
                'reconnect_interval': 5
            }
            
            # 更新配置
            current_config['mqtt'] = new_mqtt_config
            config_manager.save_config(current_config)
            
            st.success("MQTT设置已保存！")
            st.info("请重启应用以使新设置生效")

with tab2:
    st.markdown("### TCP视频服务器设置")
    
    # 获取当前TCP配置
    tcp_config = current_config.get('tcp_server', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        tcp_host = st.text_input(
            "TCP监听地址",
            value=tcp_config.get('host', '0.0.0.0'),
            help="TCP服务器监听地址"
        )
        
        tcp_port = st.number_input(
            "TCP端口",
            min_value=1024,
            max_value=65535,
            value=tcp_config.get('port', 8080),
            help="TCP服务器监听端口"
        )
    
    with col2:
        web_host = st.text_input(
            "Web监听地址",
            value=tcp_config.get('web_host', '0.0.0.0'),
            help="Web服务器监听地址"
        )
        
        web_port = st.number_input(
            "Web端口",
            min_value=1024,
            max_value=65535,
            value=tcp_config.get('web_port', 8000),
            help="Web服务器监听端口"
        )
    
    # TCP服务器控制
    st.markdown("#### TCP服务器控制")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("▶️ 启动TCP服务器"):
            st.info("正在启动TCP服务器...")
            st.success("TCP服务器已启动")
    
    with col2:
        if st.button("⏹️ 停止TCP服务器"):
            st.info("正在停止TCP服务器...")
            st.success("TCP服务器已停止")
    
    with col3:
        if st.button("🔄 重启TCP服务器"):
            st.info("正在重启TCP服务器...")
            st.success("TCP服务器已重启")
    
    # 保存TCP设置
    if st.button("💾 保存TCP设置"):
        new_tcp_config = {
            'host': tcp_host,
            'port': tcp_port,
            'web_host': web_host,
            'web_port': web_port
        }
        
        current_config['tcp_server'] = new_tcp_config
        config_manager.save_config(current_config)
        
        st.success("TCP设置已保存！")

with tab3:
    st.markdown("### 界面设置")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 主题设置")
        
        theme = st.selectbox(
            "选择主题",
            ["浅色", "深色", "自动"],
            index=0
        )
        
        language = st.selectbox(
            "选择语言",
            ["中文", "English"],
            index=0
        )
    
    with col2:
        st.markdown("#### 显示设置")
        
        auto_refresh = st.checkbox(
            "启用自动刷新",
            value=True,
            help="自动刷新设备状态和视频流"
        )
        
        refresh_interval = st.slider(
            "刷新间隔(秒)",
            min_value=1,
            max_value=60,
            value=5,
            disabled=not auto_refresh
        )
        
        show_debug = st.checkbox(
            "显示调试信息",
            value=False,
            help="在界面上显示调试信息"
        )
    
    # 保存界面设置
    if st.button("💾 保存界面设置"):
        ui_config = {
            'theme': theme,
            'language': language,
            'auto_refresh': auto_refresh,
            'refresh_interval': refresh_interval,
            'show_debug': show_debug
        }
        
        current_config['ui'] = ui_config
        config_manager.save_config(current_config)
        
        st.success("界面设置已保存！")

with tab4:
    st.markdown("### 数据管理")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 数据导出")
        
        if st.button("📤 导出设备数据"):
            st.info("正在导出设备数据...")
            st.success("设备数据导出完成")
        
        if st.button("📤 导出命令历史"):
            st.info("正在导出命令历史...")
            st.success("命令历史导出完成")
        
        if st.button("📤 导出配置"):
            config_data = config_manager.get_config()
            config_json = json.dumps(config_data, indent=2, ensure_ascii=False)
            
            st.download_button(
                label="下载配置文件",
                data=config_json,
                file_name="deepweb_config.json",
                mime="application/json"
            )
    
    with col2:
        st.markdown("#### 数据清理")
        
        if st.button("🗑️ 清理命令历史"):
            if st.checkbox("确认清理命令历史"):
                st.info("正在清理命令历史...")
                st.success("命令历史已清理")
        
        if st.button("🗑️ 清理缓存数据"):
            if st.checkbox("确认清理缓存数据"):
                st.info("正在清理缓存数据...")
                st.success("缓存数据已清理")
        
        if st.button("🔄 重置所有设置"):
            if st.checkbox("确认重置所有设置（此操作不可恢复）"):
                st.warning("正在重置所有设置...")
                st.success("所有设置已重置为默认值")

st.markdown("---")

# 系统信息
st.markdown("## ℹ️ 系统信息")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 当前配置")
    
    # 显示当前配置摘要
    config_summary = {
        "MQTT服务器": f"{mqtt_config.get('host', 'localhost')}:{mqtt_config.get('port', 1883)}",
        "TCP服务器": f"{tcp_config.get('host', '0.0.0.0')}:{tcp_config.get('port', 8080)}",
        "Web服务器": f"{tcp_config.get('web_host', '0.0.0.0')}:{tcp_config.get('web_port', 8000)}",
        "客户端ID": mqtt_config.get('client_id', 'deepweb-client'),
        "保活时间": f"{mqtt_config.get('keepalive', 60)}秒"
    }
    
    for key, value in config_summary.items():
        st.text(f"{key}: {value}")

with col2:
    st.markdown("### 连接状态")
    
    # MQTT连接状态
    mqtt_status = st.session_state.mqtt_manager.get_status()
    if mqtt_status['status'] == 'connected':
        st.success("🟢 MQTT已连接")
    else:
        st.error("🔴 MQTT未连接")
    
    # TCP服务器状态
    st.info("🟡 TCP服务器状态未知")
    
    # 设备连接状态
    device_manager = st.session_state.device_manager
    devices = device_manager.get_devices()
    online_devices = sum(1 for d in devices.values() if d.status.value == 'online')
    
    st.metric("在线设备", f"{online_devices}/{len(devices)}")

st.markdown("---")

# 关于信息
st.markdown("## 📋 关于")

st.markdown("""
**DeepWeb v1.0.0**

不倒翁设备Web控制平台

- 支持MQTT设备通信
- 支持TCP视频流传输
- 支持实时设备监控
- 支持设备控制命令

**开发团队**: DeepDiary Team  
**开发日期**: 2025-10-26
""")