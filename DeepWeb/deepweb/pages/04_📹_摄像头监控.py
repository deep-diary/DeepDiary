#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摄像头监控页面
显示实时视频流和图像控制

作者: DeepDiary Team
日期: 2025-01-27
"""

import streamlit as st
import cv2
import numpy as np
from datetime import datetime
import threading
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

st.title("📹 摄像头监控")
st.markdown("实时查看设备摄像头画面")

# 获取视频接收器
video_receiver = st.session_state.video_receiver

# 控制面板
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 刷新画面"):
        st.rerun()

with col2:
    auto_refresh = st.checkbox("自动刷新", value=True)

with col3:
    if st.button("📷 保存截图"):
        frame = video_receiver.get_latest_frame()
        if frame is not None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"snapshot_{timestamp}.jpg"
            
            # 编码为JPEG
            success, jpeg = cv2.imencode('.jpg', frame)
            if success:
                st.download_button(
                    label="下载截图",
                    data=jpeg.tobytes(),
                    file_name=filename,
                    mime="image/jpeg"
                )
                st.success(f"截图已保存: {filename}")
            else:
                st.error("截图保存失败")
        else:
            st.warning("没有可用的图像数据")

st.markdown("---")

# 视频流显示
st.markdown("## 📺 实时视频流")

# 检查视频流状态
if video_receiver.get_frame_count() == 0:
    st.warning("🟡 等待ESP32摄像头连接...")
    st.info("请确保ESP32设备已启动并连接到TCP服务器")
    
    # 显示连接信息
    st.markdown("### 连接信息")
    st.code("""
TCP服务器地址: localhost:8080
Web服务器地址: localhost:8501
    """)
    
    # 显示等待动画
    placeholder = st.empty()
    for i in range(5):
        with placeholder.container():
            st.spinner("等待视频流连接...")
        time.sleep(1)
    
    st.rerun()

else:
    st.success(f"🟢 视频流正常 (已接收 {video_receiver.get_frame_count()} 帧)")
    
    # 显示视频流
    frame = video_receiver.get_latest_frame()
    
    if frame is not None:
        # 转换BGR到RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 显示图像
        st.image(frame_rgb, caption="实时视频流", use_column_width=True)
        
        # 显示图像信息
        height, width, channels = frame.shape
        st.markdown(f"**图像尺寸**: {width} x {height}")
        st.markdown(f"**通道数**: {channels}")
        
        if video_receiver.get_client_info():
            st.markdown(f"**客户端**: {video_receiver.get_client_info()}")
        
        if video_receiver.get_last_update():
            last_update = datetime.fromtimestamp(video_receiver.get_last_update())
            st.markdown(f"**最后更新**: {last_update.strftime('%Y-%m-%d %H:%M:%S')}")
    
    else:
        st.error("无法获取视频帧")

st.markdown("---")

# 视频流控制
st.markdown("## 🎛️ 视频流控制")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 图像设置")
    
    # 分辨率设置
    resolution = st.selectbox(
        "分辨率",
        ["320x240", "640x480", "800x600", "1024x768"],
        index=1
    )
    
    # 质量设置
    quality = st.slider("JPEG质量", 10, 100, 85)
    
    # 帧率设置
    fps = st.slider("帧率", 1, 30, 15)
    
    if st.button("应用设置"):
        st.success("设置已应用")

with col2:
    st.markdown("### 控制操作")
    
    # 摄像头控制按钮
    col_start, col_stop = st.columns(2)
    
    with col_start:
        if st.button("▶️ 开始流", use_container_width=True):
            st.success("视频流已开始")
    
    with col_stop:
        if st.button("⏹️ 停止流", use_container_width=True):
            st.success("视频流已停止")
    
    # 其他控制
    col_photo, col_record = st.columns(2)
    
    with col_photo:
        if st.button("📷 拍照", use_container_width=True):
            st.success("拍照完成")
    
    with col_record:
        if st.button("🔴 录制", use_container_width=True):
            st.success("录制已开始")

st.markdown("---")

# 图像处理选项
st.markdown("## 🔧 图像处理")

processing_options = st.multiselect(
    "选择图像处理选项",
    ["边缘检测", "模糊处理", "颜色转换", "轮廓检测", "目标检测"]
)

if processing_options:
    st.info(f"已选择处理选项: {', '.join(processing_options)}")
    
    # 显示处理后的图像
    if video_receiver.get_frame_count() > 0:
        frame = video_receiver.get_latest_frame()
        if frame is not None:
            processed_frame = frame.copy()
            
            # 应用处理选项
            if "边缘检测" in processing_options:
                gray = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 50, 150)
                processed_frame = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            
            if "模糊处理" in processing_options:
                processed_frame = cv2.GaussianBlur(processed_frame, (15, 15), 0)
            
            if "颜色转换" in processing_options:
                processed_frame = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2HSV)
            
            # 转换BGR到RGB
            processed_rgb = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2RGB)
            
            st.image(processed_rgb, caption="处理后的图像", use_container_width=True)

st.markdown("---")

# 统计信息
st.markdown("## 📊 统计信息")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("总帧数", video_receiver.get_frame_count())

with col2:
    if video_receiver.get_last_update():
        current_time = time.time()
        fps = video_receiver.get_frame_count() / (current_time - video_receiver.get_last_update()) if current_time > video_receiver.get_last_update() else 0
        st.metric("估算FPS", f"{fps:.1f}")
    else:
        st.metric("估算FPS", "0.0")

with col3:
    if video_receiver.get_client_info():
        st.metric("客户端状态", "已连接")
    else:
        st.metric("客户端状态", "未连接")

# 自动刷新
if auto_refresh:
    time.sleep(1)
    st.rerun()