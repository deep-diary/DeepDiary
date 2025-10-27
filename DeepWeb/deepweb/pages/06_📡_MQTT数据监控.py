#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MQTT数据监控页面
根据MQTT协议文档订阅主题并格式化显示数据

作者: DeepDiary Team
日期: 2025-10-26
"""

import streamlit as st
import json
import time
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import threading
from queue import Queue

# 使用Streamlit的缓存机制创建全局单例队列
@st.cache_resource
def get_global_message_queue():
    """获取全局消息队列（单例）"""
    return Queue()

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入服务模块
from services.cloud_communication.mqtt.mqtt_manager import MQTTManager
from config.config_manager import ConfigManager

# 初始化日志管理器
try:
    from data_management.log_manager import LogManager
    log_manager = LogManager()
    logger = log_manager.get_logger(__name__)
except Exception as e:
    logger = None
    print(f"日志管理器初始化失败: {e}")

def log_debug(message: str):
    """调试日志"""
    if logger:
        logger.debug(message)
    print(f"[DEBUG] {message}")

def log_info(message: str):
    """信息日志"""
    if logger:
        logger.info(message)
    print(f"[INFO] {message}")

def log_warning(message: str):
    """警告日志"""
    if logger:
        logger.warning(message)
    print(f"[WARNING] {message}")

def log_error(message: str):
    """错误日志"""
    if logger:
        logger.error(message)
    print(f"[ERROR] {message}")

def initialize_session_state():
    """初始化会话状态"""
    # 获取日志管理器
    try:
        from main import get_log_manager
        log_manager = get_log_manager()
    except:
        log_manager = None
    
    # 初始化配置管理器
    if 'config_manager' not in st.session_state:
        st.session_state.config_manager = ConfigManager()
    
    # 初始化MQTT管理器（传递log_manager）
    if 'mqtt_manager' not in st.session_state:
        config = st.session_state.config_manager.get_config()
        mqtt_config = config.get('mqtt', {})
        st.session_state.mqtt_manager = MQTTManager(
            host=mqtt_config.get('host', 'localhost'),
            port=mqtt_config.get('port', 1883),
            username=mqtt_config.get('username'),
            password=mqtt_config.get('password'),
            debug=True,
            log_manager=log_manager
        )
    
    # 初始化MQTT数据存储
    if 'mqtt_data' not in st.session_state:
        st.session_state.mqtt_data = {
            'device_info': [],
            'device_status': [],
            'device_sensor': [],
            'device_motor': [],
            'device_arm': [],
            'device_camera': [],
            'device_system': [],
            'device_alarm': [],
            'device_log': [],
            # 保留原有格式
            'legacy_status': [],
            'legacy_sensor': [],
            'legacy_motor': [],
            'legacy_arm': [],
            'legacy_camera': [],
            'legacy_system': [],
            'legacy_alarm': [],
            'legacy_log': []
            
        }
    
    # 初始化设备列表
    if 'mqtt_devices' not in st.session_state:
        st.session_state.mqtt_devices = set()

def setup_mqtt_subscriptions():
    """设置MQTT订阅"""
    mqtt_manager = st.session_state.mqtt_manager
    
    # 根据实际设备发送的主题格式定义订阅
    message_types = {
        'device_info': 'device/+/info',  # 设备信息主题
        'device_status': 'device/+/status',  # 设备状态主题
        'device_sensor': 'device/+/sensor',  # 传感器数据主题
        'device_motor': 'device/+/motor',  # 电机数据主题
        'device_arm': 'device/+/arm',  # 机械臂数据主题
        'device_camera': 'device/+/camera',  # 摄像头数据主题
        'device_system': 'device/+/system',  # 系统信息主题
        'device_alarm': 'device/+/alarm',  # 告警信息主题
        'device_log': 'device/+/log',  # 日志信息主题
        # 保留原有的deepcontroller格式作为备用
        'legacy_status': 'deepcontroller/+/status',
        'legacy_sensor': 'deepcontroller/+/sensor',
        'legacy_motor': 'deepcontroller/+/motor',
        'legacy_arm': 'deepcontroller/+/arm',
        'legacy_camera': 'deepcontroller/+/camera',
        'legacy_system': 'deepcontroller/+/system',
        'legacy_alarm': 'deepcontroller/+/alarm',
        'legacy_log': 'deepcontroller/+/log'
    }
    
    # 为每种消息类型设置回调
    for msg_type, topic_pattern in message_types.items():
        def create_callback(msg_type):
            return lambda topic, payload, message: on_mqtt_message(topic, payload, message, msg_type)
        
        success = mqtt_manager.add_subscription(
            name=f"{msg_type}_subscription",
            topic=topic_pattern,
            callback=create_callback(msg_type),
            description=f"{msg_type}数据订阅"
        )
        
        if success:
            log_debug(f"订阅成功: {topic_pattern} -> {msg_type}")
        else:
            log_error(f"订阅失败: {topic_pattern}")

def on_mqtt_message(topic: str, payload: Dict[str, Any], message, message_type: str):
    """MQTT消息回调函数（线程安全版本）"""
    # 强制打印，确保能看出回调是否被调用
    print(f"[MQTT CALLBACK] 收到MQTT消息 - 主题: {topic}, 类型: {message_type}")
    
    try:
        # 获取全局队列实例
        global_queue = get_global_message_queue()
        
        # 详细日志记录
        log_debug(f"收到消息 - 主题: {topic}, 类型: {message_type}")
        log_debug(f"消息内容: {payload}")
        
        # 提取设备ID
        device_id = extract_device_id(topic)
        if device_id:
            log_debug(f"提取到设备ID: {device_id}")
        else:
            log_debug(f"警告: 无法从主题 {topic} 提取设备ID")
        
        # 添加时间戳
        payload['_received_time'] = time.time()
        payload['_device_id'] = device_id
        payload['_topic'] = topic
        
        # 将消息放入队列（线程安全）
        message_info = {
            'topic': topic,
            'payload': payload,
            'message_type': message_type,
            'device_id': device_id
        }
        
        # 使用全局线程安全队列
        global_queue.put(message_info)
        queue_size = global_queue.qsize()
        print(f"[MQTT CALLBACK] 消息已加入队列，队列大小: {queue_size}")
        log_debug("消息已加入全局处理队列")
        
    except Exception as e:
        log_error(f"处理MQTT消息失败: {e}")

def extract_device_id(topic: str) -> str:
    """从主题中提取设备ID"""
    try:
        parts = topic.split('/')
        # 支持两种主题格式:
        # device/{device_id}/info
        # deepcontroller/{device_id}/status
        if len(parts) >= 2:
            if parts[0] == 'device':
                return parts[1]
            elif parts[0] == 'deepcontroller':
                return parts[1]
    except Exception:
        pass
    return "unknown"

def format_timestamp(timestamp: float) -> str:
    """格式化时间戳"""
    try:
        return datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
    except:
        return "N/A"

def display_device_info_data(data: List[Dict[str, Any]]):
    """显示设备信息数据（新的统一格式）"""
    if not data:
        st.info("暂无设备信息数据")
        return
    
    latest_data = data[-1]
    
    # 调试信息：显示数据统计
    log_debug(f"设备信息数据量: {len(data)}, 最新数据: {latest_data.get('device_id', 'N/A')}")
    
    st.markdown("### 📊 设备信息概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**设备ID**")
        st.text(latest_data.get('device_id', 'N/A'))
    
    with col2:
        st.markdown("**设备类型**")
        st.text(latest_data.get('device_type', 'N/A'))
    
    with col3:
        st.markdown("**固件版本**")
        st.text(latest_data.get('firmware_version', 'N/A'))
    
    with col4:
        st.markdown("**IP地址**")
        st.text(latest_data.get('ip_address', 'N/A') or '未获取')
    
    # 系统信息
    st.markdown("#### 💻 系统信息")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("**可用内存**")
        st.text(f"{latest_data.get('free_heap', 0):,} bytes")
    
    with col2:
        st.markdown("**运行时间**")
        st.text(f"{latest_data.get('uptime_seconds', 0):,} 秒")
    
    with col3:
        st.markdown("**CPU温度**")
        st.text(f"{latest_data.get('cpu_temperature', 0):.1f}°C")
    
    with col4:
        st.markdown("**WiFi网络**")
        st.text(latest_data.get('wifi_ssid', 'N/A'))
    
    # 组件状态
    st.markdown("#### 🔧 组件状态")
    
    components = {
        'camera_available': '摄像头',
        'can_bus_available': 'CAN总线',
        'led_strip_available': 'LED灯带',
        'gimbal_available': '云台'
    }
    
    comp_data = []
    for comp_key, comp_name in components.items():
        comp_data.append({
            'Component': comp_name,
            'Status': '可用' if latest_data.get(comp_key, False) else '不可用',
            'Available': latest_data.get(comp_key, False)
        })
    
    if comp_data:
        df_comp = pd.DataFrame(comp_data)
        st.dataframe(df_comp, width="stretch")
    
    # 电机和机械臂状态
    st.markdown("#### ⚙️ 电机和机械臂状态")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**电机状态**")
        motor_info = latest_data.get('motor', {})
        st.markdown(f"- 连接状态: {'已连接' if motor_info.get('connected', False) else '未连接'}")
        st.markdown(f"- 电机数量: {motor_info.get('motor_count', 0)}")
        st.markdown(f"- 状态: {motor_info.get('status', 'unknown')}")
    
    with col2:
        st.markdown("**机械臂状态**")
        arm_info = latest_data.get('arm', {})
        st.markdown(f"- 连接状态: {'已连接' if arm_info.get('connected', False) else '未连接'}")
        st.markdown(f"- 电机数量: {arm_info.get('motor_count', 0)}")
        st.markdown(f"- 状态: {arm_info.get('status', 'unknown')}")

def display_status_data(data: List[Dict[str, Any]]):
    """显示设备状态数据（兼容旧格式）"""
    if not data:
        st.info("暂无设备状态数据")
        return
    
    latest_data = data[-1]
    
    st.markdown("### 📊 设备状态概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("设备类型", latest_data.get('data', {}).get('device_type', 'N/A'))
    
    with col2:
        st.metric("固件版本", latest_data.get('data', {}).get('firmware_version', 'N/A'))
    
    with col3:
        st.metric("IP地址", latest_data.get('data', {}).get('ip_address', 'N/A'))
    
    with col4:
        st.metric("运行时间", f"{latest_data.get('data', {}).get('uptime_seconds', 0):,} 秒")
    
    # 组件状态
    components = latest_data.get('data', {}).get('components', {})
    if components:
        st.markdown("#### 🔧 组件状态")
        comp_data = []
        for comp_name, comp_status in components.items():
            comp_data.append({
                'Component': comp_name,
                'Status': comp_status,
                'Available': comp_status == True
            })
        
        if comp_data:
            df_comp = pd.DataFrame(comp_data)
            st.dataframe(df_comp, width="stretch")

def display_sensor_data(data: List[Dict[str, Any]]):
    """显示传感器数据"""
    if not data:
        st.info("暂无传感器数据")
        return
    
    latest_data = data[-1]
    sensor_data = latest_data.get('data', {})
    
    st.markdown("### 📡 传感器数据")
    
    # 加速度数据
    if 'acceleration' in sensor_data:
        acc_data = sensor_data['acceleration']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 加速度 (m/s²)")
            acc_df = pd.DataFrame([
                {'Axis': 'X', 'Value': acc_data.get('x', 0)},
                {'Axis': 'Y', 'Value': acc_data.get('y', 0)},
                {'Axis': 'Z', 'Value': acc_data.get('z', 0)},
                {'Axis': 'Total', 'Value': acc_data.get('total', 0)}
            ])
            
            fig_acc = px.bar(acc_df, x='Axis', y='Value', 
                           title="三轴加速度", color='Axis')
            st.plotly_chart(fig_acc, width="stretch")
        
        with col2:
            st.markdown("#### 加速度仪表")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=acc_data.get('total', 0),
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "总加速度"},
                gauge={
                    'axis': {'range': [None, 20]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 9.81], 'color': "lightgray"},
                        {'range': [9.81, 15], 'color': "yellow"},
                        {'range': [15, 20], 'color': "red"}
                    ]
                }
            ))
            st.plotly_chart(fig_gauge, width="stretch")
    
    # 姿态数据
    if 'orientation' in sensor_data:
        st.markdown("#### 姿态角度")
        ori_data = sensor_data['orientation']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("俯仰角 (Pitch)", f"{ori_data.get('pitch', 0):.2f}°")
        with col2:
            st.metric("横滚角 (Roll)", f"{ori_data.get('roll', 0):.2f}°")

def display_motor_data(data: List[Dict[str, Any]]):
    """显示电机数据"""
    if not data:
        st.info("暂无电机数据")
        return
    
    latest_data = data[-1]
    motor_data = latest_data.get('data', {})
    
    st.markdown("### ⚙️ 电机状态")
    
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
                motor_ids = [f"Motor {m.get('id', 0)}" for m in motors]
                positions = [m.get('position', 0) for m in motors]
                
                fig_motors = go.Figure(data=[
                    go.Bar(x=motor_ids, y=positions, marker_color='lightblue')
                ])
                fig_motors.update_layout(
                    title="电机位置",
                    xaxis_title="电机",
                    yaxis_title="位置 (°)",
                    height=400
                )
                st.plotly_chart(fig_motors, width="stretch")

def display_arm_data(data: List[Dict[str, Any]]):
    """显示机械臂数据"""
    if not data:
        st.info("暂无机械臂数据")
        return
    
    latest_data = data[-1]
    arm_data = latest_data.get('data', {})
    
    st.markdown("### 🤖 机械臂状态")
    
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
            st.markdown("#### 末端执行器位置 (mm)")
            if 'position' in ee_data:
                pos = ee_data['position']
                st.metric("X", f"{pos.get('x', 0):.2f}")
                st.metric("Y", f"{pos.get('y', 0):.2f}")
                st.metric("Z", f"{pos.get('z', 0):.2f}")
        
        with col2:
            st.markdown("#### 末端执行器姿态 (°)")
            if 'orientation' in ee_data:
                ori = ee_data['orientation']
                st.metric("X", f"{ori.get('x', 0):.2f}")
                st.metric("Y", f"{ori.get('y', 0):.2f}")
                st.metric("Z", f"{ori.get('z', 0):.2f}")

def display_camera_data(data: List[Dict[str, Any]]):
    """显示摄像头数据"""
    if not data:
        st.info("暂无摄像头数据")
        return
    
    latest_data = data[-1]
    camera_data = latest_data.get('data', {})
    
    st.markdown("### 📹 摄像头状态")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("状态", "在线" if camera_data.get('camera_available', False) else "离线")
    
    with col2:
        st.metric("流媒体", "开启" if camera_data.get('streaming', False) else "关闭")
    
    with col3:
        st.metric("帧率", f"{camera_data.get('fps', 0)} FPS")
    
    # 分辨率信息
    if 'resolution' in camera_data:
        res = camera_data['resolution']
        st.markdown(f"**分辨率**: {res.get('width', 0)} x {res.get('height', 0)}")
    
    st.markdown(f"**格式**: {camera_data.get('format', 'N/A')}")
    st.markdown(f"**质量**: {camera_data.get('quality', 0)}%")

def display_system_data(data: List[Dict[str, Any]]):
    """显示系统数据"""
    if not data:
        st.info("暂无系统数据")
        return
    
    latest_data = data[-1]
    system_data = latest_data.get('data', {})
    
    st.markdown("### 💻 系统信息")
    
    # 内存信息
    if 'memory' in system_data:
        memory = system_data['memory']
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("可用堆内存", f"{memory.get('free_heap', 0):,} bytes")
        
        with col2:
            st.metric("最小堆内存", f"{memory.get('min_free_heap', 0):,} bytes")
        
        with col3:
            st.metric("总内部RAM", f"{memory.get('total_internal_ram', 0):,} bytes")
        
        # SPIRAM信息
        if 'free_spiram' in memory and 'total_spiram' in memory:
            col4, col5 = st.columns(2)
            
            with col4:
                st.metric("可用SPIRAM", f"{memory.get('free_spiram', 0):,} bytes")
            
            with col5:
                st.metric("总SPIRAM", f"{memory.get('total_spiram', 0):,} bytes")
    
    # 芯片信息
    if 'chip' in system_data:
        chip = system_data['chip']
        st.markdown(f"**芯片型号**: {chip.get('model', 'N/A')}")
        st.markdown(f"**芯片版本**: {chip.get('revision', 'N/A')}")
        st.markdown(f"**芯片特性**: {chip.get('features', 'N/A')}")
    
    st.markdown(f"**Flash**: {system_data.get('flash', 'N/A')}")
    st.markdown(f"**PSRAM**: {system_data.get('psram', 'N/A')}")

def display_alarm_data(data: List[Dict[str, Any]]):
    """显示告警数据"""
    if not data:
        st.info("暂无告警数据")
        return
    
    st.markdown("### 🚨 告警信息")
    
    # 显示最近的告警
    recent_alarms = data[-5:] if len(data) > 5 else data
    
    for alarm in reversed(recent_alarms):
        alarm_data = alarm.get('data', {})
        
        alarm_level = alarm_data.get('alarm_level', 'unknown')
        alarm_type = alarm_data.get('alarm_type', 'unknown')
        description = alarm_data.get('description', 'N/A')
        
        # 根据告警级别设置颜色
        if alarm_level == 'critical':
            st.error(f"🔴 **{alarm_level.upper()}**: {description}")
        elif alarm_level == 'error':
            st.error(f"🟠 **{alarm_level.upper()}**: {description}")
        elif alarm_level == 'warning':
            st.warning(f"🟡 **{alarm_level.upper()}**: {description}")
        else:
            st.info(f"ℹ️ **{alarm_level.upper()}**: {description}")
        
        st.markdown(f"**类型**: {alarm_type}")
        st.markdown(f"**组件**: {alarm_data.get('component', 'N/A')}")
        st.markdown(f"**时间**: {format_timestamp(alarm.get('_received_time', 0))}")
        st.markdown("---")

def display_log_data(data: List[Dict[str, Any]]):
    """显示日志数据"""
    if not data:
        st.info("暂无日志数据")
        return
    
    st.markdown("### 📝 日志信息")
    
    # 显示最近的日志
    recent_logs = data[-10:] if len(data) > 10 else data
    
    for log in reversed(recent_logs):
        log_data = log.get('data', {})
        
        st.markdown(f"**时间**: {format_timestamp(log.get('_received_time', 0))}")
        st.markdown(f"**设备**: {log.get('_device_id', 'N/A')}")
        st.markdown(f"**内容**: {log_data}")
        st.markdown("---")

# 初始化会话状态
initialize_session_state()

# 处理MQTT消息队列（从全局队列中读取，在线程安全的主线程中处理）
global_queue = get_global_message_queue()
processed_messages = []
queue_size = 0
try:
    queue_size = global_queue.qsize()
except:
    pass

log_debug(f"队列大小: {queue_size}")

while not global_queue.empty():
    try:
        message_info = global_queue.get_nowait()
        
        # 提取设备ID
        device_id = message_info.get('device_id')
        message_type = message_info.get('message_type')
        
        log_debug(f"处理消息 - 设备: {device_id}, 类型: {message_type}")
        
        if device_id and device_id != "unknown":
            st.session_state.mqtt_devices.add(device_id)
        
        # 存储数据
        payload = message_info.get('payload')
        
        if message_type in st.session_state.mqtt_data:
            st.session_state.mqtt_data[message_type].append(payload)
            log_debug(f"数据已存储到 {message_type}，记录数: {len(st.session_state.mqtt_data[message_type])}")
            
            # 保持最近100条记录
            if len(st.session_state.mqtt_data[message_type]) > 100:
                st.session_state.mqtt_data[message_type] = st.session_state.mqtt_data[message_type][-100:]
            
            processed_messages.append(message_info)
        else:
            log_warning(f"未知的消息类型: {message_type}")
    except Exception as e:
        log_error(f"处理消息队列失败: {e}")

# 如果有新消息被处理，触发重新运行
if processed_messages:
    log_info(f"成功处理了 {len(processed_messages)} 条MQTT消息")
    st.rerun()
else:
    log_debug("队列为空，无新消息")

st.title("📡 MQTT数据监控")
st.markdown("实时监控MQTT主题数据，根据DeepController协议显示格式化信息")

# 调试信息：显示session_state中的数据
total_data_count = sum(len(data) for data in st.session_state.mqtt_data.values())
log_debug(f"页面加载 - 总数据量: {total_data_count}, 设备数: {len(st.session_state.mqtt_devices)}")
log_debug(f"设备信息数据: {len(st.session_state.mqtt_data['device_info'])} 条")

# 获取MQTT管理器
mqtt_manager = st.session_state.mqtt_manager

# 连接状态检查
mqtt_status = mqtt_manager.get_status()
if mqtt_status['status'] != 'connected':
    st.error(f"🔴 MQTT未连接: {mqtt_status.get('last_error', 'Unknown error')}")
    if st.button("🔄 重新连接"):
        if mqtt_manager.connect():
            st.success("✅ MQTT连接成功")
            setup_mqtt_subscriptions()
            st.rerun()
        else:
            st.error("❌ MQTT连接失败")
    st.stop()
else:
    st.success("🟢 MQTT已连接")
    
    # 设置订阅（如果还没有设置）
    if not mqtt_manager.subscriptions:
        setup_mqtt_subscriptions()
        st.info("📡 已设置MQTT主题订阅")
    
    # 调试信息：显示订阅状态（稍后在控制面板中显示）

# 控制面板
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🔄 刷新数据"):
        st.rerun()

with col2:
    auto_refresh = st.checkbox("自动刷新", value=True)

with col3:
    if st.button("🗑️ 清空数据"):
        for key in st.session_state.mqtt_data:
            st.session_state.mqtt_data[key] = []
        st.session_state.mqtt_devices.clear()
        st.rerun()

with col4:
    show_debug = st.checkbox("显示调试信息", value=False)

# 添加重新连接按钮
if st.button("🔌 重新连接MQTT"):
    mqtt_manager.disconnect()
    time.sleep(1)
    if mqtt_manager.connect():
        st.success("✅ MQTT重新连接成功")
        setup_mqtt_subscriptions()
        st.rerun()
    else:
        st.error("❌ MQTT重新连接失败")

# 设备选择
if st.session_state.mqtt_devices:
    selected_device = st.selectbox("选择设备", list(st.session_state.mqtt_devices))
    st.info(f"已选择设备: {selected_device}")
else:
    st.warning("暂无设备数据")
    selected_device = None

# 调试信息显示
if show_debug:
    st.markdown("---")
    st.markdown("## 🔍 调试信息")
    
    debug_col1, debug_col2 = st.columns(2)
    
    with debug_col1:
        st.markdown("### MQTT连接状态")
        st.json({
            "status": mqtt_status['status'],
            "host": mqtt_status['host'],
            "port": mqtt_status['port'],
            "subscriptions_count": mqtt_status['subscriptions_count'],
            "messages_sent": mqtt_status['stats']['messages_sent'],
            "messages_received": mqtt_status['stats']['messages_received']
        })
    
    with debug_col2:
        st.markdown("### 订阅的主题")
        for name, config in mqtt_manager.subscriptions.items():
            st.markdown(f"- `{config.topic}` ({config.description})")
    
    st.markdown("### 数据统计")
    debug_data = {}
    for msg_type, data_list in st.session_state.mqtt_data.items():
        debug_data[msg_type] = len(data_list)
    st.json(debug_data)
    
    st.markdown("### 最近接收的消息")
    recent_messages = []
    for msg_type, data_list in st.session_state.mqtt_data.items():
        if data_list:
            latest = data_list[-1]
            recent_messages.append({
                "type": msg_type,
                "device_id": latest.get('_device_id', 'N/A'),
                "topic": latest.get('_topic', 'N/A'),
                "timestamp": format_timestamp(latest.get('_received_time', 0)),
                "data_keys": list(latest.get('data', {}).keys()) if isinstance(latest.get('data'), dict) else 'N/A'
            })
    
    if recent_messages:
        st.json(recent_messages[-5:])  # 显示最近5条消息
    else:
        st.info("暂无接收到的消息")

st.markdown("---")

# 数据显示标签页
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📊 设备信息", "📊 设备状态", "📡 传感器", "⚙️ 电机", "🤖 机械臂", 
    "📹 摄像头", "💻 系统", "🚨 告警", "📝 日志"
])

with tab1:
    # 调试信息
    device_info_count = len(st.session_state.mqtt_data['device_info'])
    log_debug(f"显示设备信息标签页，数据量: {device_info_count}")
    display_device_info_data(st.session_state.mqtt_data['device_info'])

with tab2:
    display_status_data(st.session_state.mqtt_data['device_status'])

with tab3:
    display_sensor_data(st.session_state.mqtt_data['device_sensor'])

with tab4:
    display_motor_data(st.session_state.mqtt_data['device_motor'])

with tab5:
    display_arm_data(st.session_state.mqtt_data['device_arm'])

with tab6:
    display_camera_data(st.session_state.mqtt_data['device_camera'])

with tab7:
    display_system_data(st.session_state.mqtt_data['device_system'])

with tab8:
    display_alarm_data(st.session_state.mqtt_data['device_alarm'])

with tab9:
    display_log_data(st.session_state.mqtt_data['device_log'])

# 统计信息
st.markdown("---")
st.markdown("## 📈 数据统计")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("设备数量", len(st.session_state.mqtt_devices))

with col2:
    total_messages = sum(len(data) for data in st.session_state.mqtt_data.values())
    st.metric("总消息数", total_messages)

with col3:
    st.metric("MQTT连接状态", mqtt_status['status'])

with col4:
    st.metric("订阅主题数", len(mqtt_manager.subscriptions))

# 自动刷新
if auto_refresh:
    time.sleep(2)
    st.rerun()
