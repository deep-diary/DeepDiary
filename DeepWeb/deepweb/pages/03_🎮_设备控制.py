#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备控制页面
发送控制命令到设备

作者: DeepDiary Team
日期: 2025-01-27
"""

import streamlit as st
import time
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入服务模块
from services.cloud_communication.mqtt.mqtt_manager import MQTTManager
from services.simple_video_receiver import get_video_receiver, start_video_service
from app_logic.device_logic_manager import DeviceLogicManager, DeviceCommand
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

# 初始化会话状态
initialize_session_state()

st.title("🎮 设备控制")
st.markdown("发送控制命令到不倒翁设备")

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

# 检查设备状态
if device.status.value != 'online':
    st.error(f"设备 {selected_device_id} 当前状态: {device.status.value}")
    st.info("请确保设备在线后再发送控制命令")
    st.stop()

st.success(f"设备 {selected_device_id} 已连接，可以发送控制命令")

st.markdown("---")

# 创建MQTT服务适配器
mqtt_adapter = st.session_state.mqtt_adapter

# 控制面板
tab1, tab2, tab3, tab4 = st.tabs(["⚙️ 电机控制", "🤖 机械臂控制", "📹 摄像头控制", "💡 LED控制"])

with tab1:
    st.markdown("### 电机控制")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 单个电机控制")
        
        motor_id = st.selectbox("选择电机", [1, 2, 3, 4, 5, 6], key="motor_id")
        
        action = st.selectbox(
            "选择动作",
            ["set_position", "set_speed", "set_torque", "start", "stop"],
            key="motor_action"
        )
        
        if action == "set_position":
            position = st.slider("位置 (度)", -180, 180, 0, key="motor_position")
            speed = st.slider("速度 (rpm)", 0, 100, 50, key="motor_speed")
            duration = st.slider("持续时间 (ms)", 100, 10000, 1000, key="motor_duration")
            
            if st.button("发送位置命令", key="send_position"):
                success = mqtt_adapter.send_motor_command(
                    selected_device_id, motor_id, action,
                    position=position, speed=speed, duration=duration
                )
                if success:
                    st.success(f"电机 {motor_id} 位置命令发送成功")
                else:
                    st.error("命令发送失败")
        
        elif action == "set_speed":
            speed = st.slider("速度 (rpm)", -100, 100, 0, key="motor_speed_set")
            
            if st.button("发送速度命令", key="send_speed"):
                success = mqtt_adapter.send_motor_command(
                    selected_device_id, motor_id, action,
                    speed=speed
                )
                if success:
                    st.success(f"电机 {motor_id} 速度命令发送成功")
                else:
                    st.error("命令发送失败")
        
        elif action == "set_torque":
            torque = st.slider("扭矩 (N·m)", -10, 10, 0, step=0.1, key="motor_torque")
            
            if st.button("发送扭矩命令", key="send_torque"):
                success = mqtt_adapter.send_motor_command(
                    selected_device_id, motor_id, action,
                    torque=torque
                )
                if success:
                    st.success(f"电机 {motor_id} 扭矩命令发送成功")
                else:
                    st.error("命令发送失败")
        
        elif action in ["start", "stop"]:
            if st.button(f"{action.title()} 电机", key=f"motor_{action}"):
                success = mqtt_adapter.send_motor_command(
                    selected_device_id, motor_id, action
                )
                if success:
                    st.success(f"电机 {motor_id} {action} 命令发送成功")
                else:
                    st.error("命令发送失败")
    
    with col2:
        st.markdown("#### 多电机协调控制")
        
        # 预设动作
        preset_actions = {
            "摇摆": {"motors": [1, 2], "action": "set_position", "params": {"position": 30, "speed": 20}},
            "点头": {"motors": [3], "action": "set_position", "params": {"position": 15, "speed": 15}},
            "摇头": {"motors": [4], "action": "set_position", "params": {"position": -15, "speed": 15}},
            "复位": {"motors": [1, 2, 3, 4, 5, 6], "action": "set_position", "params": {"position": 0, "speed": 30}},
        }
        
        selected_preset = st.selectbox("选择预设动作", list(preset_actions.keys()))
        
        if st.button("执行预设动作", key="preset_action"):
            preset = preset_actions[selected_preset]
            success_count = 0
            
            for motor_id in preset["motors"]:
                success = mqtt_adapter.send_motor_command(
                    selected_device_id, motor_id, preset["action"],
                    **preset["params"]
                )
                if success:
                    success_count += 1
            
            if success_count == len(preset["motors"]):
                st.success(f"预设动作 '{selected_preset}' 执行成功")
            else:
                st.warning(f"预设动作 '{selected_preset}' 部分执行成功 ({success_count}/{len(preset['motors'])})")

with tab2:
    st.markdown("### 机械臂控制")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 关节控制")
        
        joint_id = st.selectbox("选择关节", [1, 2, 3, 4, 5, 6], key="joint_id")
        
        joint_action = st.selectbox(
            "选择动作",
            ["set_angle", "set_velocity", "start", "stop"],
            key="joint_action"
        )
        
        if joint_action == "set_angle":
            angle = st.slider("角度 (度)", -180, 180, 0, key="joint_angle")
            velocity = st.slider("速度 (度/秒)", 0, 90, 30, key="joint_velocity")
            
            if st.button("设置关节角度", key="set_joint_angle"):
                success = mqtt_adapter.send_arm_command(
                    selected_device_id, joint_action,
                    joint_id=joint_id, angle=angle, velocity=velocity
                )
                if success:
                    st.success(f"关节 {joint_id} 角度设置成功")
                else:
                    st.error("命令发送失败")
        
        elif joint_action == "set_velocity":
            velocity = st.slider("速度 (度/秒)", -90, 90, 0, key="joint_velocity_set")
            
            if st.button("设置关节速度", key="set_joint_velocity"):
                success = mqtt_adapter.send_arm_command(
                    selected_device_id, joint_action,
                    joint_id=joint_id, velocity=velocity
                )
                if success:
                    st.success(f"关节 {joint_id} 速度设置成功")
                else:
                    st.error("命令发送失败")
    
    with col2:
        st.markdown("#### 末端执行器控制")
        
        ee_action = st.selectbox(
            "选择动作",
            ["set_position", "set_orientation", "grip", "release"],
            key="ee_action"
        )
        
        if ee_action == "set_position":
            col_x, col_y, col_z = st.columns(3)
            
            with col_x:
                x = st.number_input("X (mm)", -200, 200, 0, key="ee_x")
            with col_y:
                y = st.number_input("Y (mm)", -200, 200, 0, key="ee_y")
            with col_z:
                z = st.number_input("Z (mm)", -200, 200, 0, key="ee_z")
            
            if st.button("设置位置", key="set_ee_position"):
                success = mqtt_adapter.send_arm_command(
                    selected_device_id, ee_action,
                    position={"x": x, "y": y, "z": z}
                )
                if success:
                    st.success("末端执行器位置设置成功")
                else:
                    st.error("命令发送失败")
        
        elif ee_action == "set_orientation":
            col_rx, col_ry, col_rz = st.columns(3)
            
            with col_rx:
                rx = st.number_input("Roll X (度)", -180, 180, 0, key="ee_rx")
            with col_ry:
                ry = st.number_input("Pitch Y (度)", -180, 180, 0, key="ee_ry")
            with col_rz:
                rz = st.number_input("Yaw Z (度)", -180, 180, 0, key="ee_rz")
            
            if st.button("设置姿态", key="set_ee_orientation"):
                success = mqtt_adapter.send_arm_command(
                    selected_device_id, ee_action,
                    orientation={"x": rx, "y": ry, "z": rz}
                )
                if success:
                    st.success("末端执行器姿态设置成功")
                else:
                    st.error("命令发送失败")
        
        elif ee_action in ["grip", "release"]:
            if st.button(f"{ee_action.title()} 夹爪", key=f"ee_{ee_action}"):
                success = mqtt_adapter.send_arm_command(
                    selected_device_id, ee_action
                )
                if success:
                    st.success(f"夹爪 {ee_action} 命令发送成功")
                else:
                    st.error("命令发送失败")

with tab3:
    st.markdown("### 摄像头控制")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 图像设置")
        
        resolution = st.selectbox(
            "分辨率",
            ["320x240", "640x480", "800x600", "1024x768"],
            key="camera_resolution"
        )
        
        quality = st.slider("图像质量", 10, 100, 80, key="camera_quality")
        
        fps = st.slider("帧率", 1, 30, 15, key="camera_fps")
        
        if st.button("应用设置", key="apply_camera_settings"):
            width, height = map(int, resolution.split('x'))
            success = mqtt_adapter.send_camera_command(
                selected_device_id, "set_config",
                resolution={"width": width, "height": height},
                quality=quality, fps=fps
            )
            if success:
                st.success("摄像头设置应用成功")
            else:
                st.error("设置应用失败")
    
    with col2:
        st.markdown("#### 控制操作")
        
        camera_action = st.selectbox(
            "选择操作",
            ["start_stream", "stop_stream", "take_photo", "start_recording", "stop_recording"],
            key="camera_action"
        )
        
        if st.button("执行操作", key="execute_camera_action"):
            success = mqtt_adapter.send_camera_command(
                selected_device_id, camera_action
            )
            if success:
                st.success(f"摄像头 {camera_action} 命令发送成功")
            else:
                st.error("命令发送失败")

with tab4:
    st.markdown("### LED控制")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 颜色控制")
        
        led_mode = st.selectbox(
            "LED模式",
            ["solid", "blink", "rainbow", "breathing", "off"],
            key="led_mode"
        )
        
        if led_mode != "off":
            color = st.color_picker("选择颜色", "#00ff00", key="led_color")
            
            if led_mode in ["blink", "breathing"]:
                speed = st.slider("速度", 1, 10, 5, key="led_speed")
            else:
                speed = 5
            
            brightness = st.slider("亮度", 0, 255, 128, key="led_brightness")
            
            if st.button("应用LED设置", key="apply_led"):
                # 转换颜色格式
                rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
                
                success = mqtt_adapter.send_led_command(
                    selected_device_id, "set_mode",
                    mode=led_mode, color=rgb, brightness=brightness, speed=speed
                )
                if success:
                    st.success("LED设置应用成功")
                else:
                    st.error("LED设置失败")
        
        else:
            if st.button("关闭LED", key="turn_off_led"):
                success = mqtt_adapter.send_led_command(
                    selected_device_id, "set_mode",
                    mode="off"
                )
                if success:
                    st.success("LED已关闭")
                else:
                    st.error("LED关闭失败")
    
    with col2:
        st.markdown("#### 预设效果")
        
        preset_effects = {
            "呼吸灯": {"mode": "breathing", "color": (255, 0, 0), "speed": 3},
            "彩虹灯": {"mode": "rainbow", "speed": 5},
            "闪烁": {"mode": "blink", "color": (0, 255, 0), "speed": 2},
            "常亮": {"mode": "solid", "color": (0, 0, 255), "brightness": 200},
        }
        
        selected_effect = st.selectbox("选择预设效果", list(preset_effects.keys()))
        
        if st.button("应用预设效果", key="apply_preset"):
            effect = preset_effects[selected_effect]
            success = mqtt_adapter.send_led_command(
                selected_device_id, "set_mode",
                **effect
            )
            if success:
                st.success(f"预设效果 '{selected_effect}' 应用成功")
            else:
                st.error("预设效果应用失败")

st.markdown("---")

# 命令历史
st.markdown("## 📜 命令历史")

command_history = device_manager.get_command_history(selected_device_id, limit=20)

if command_history:
    history_data = []
    for cmd in command_history:
        history_data.append({
            '时间': time.strftime('%H:%M:%S', time.localtime(cmd.timestamp)),
            '命令ID': cmd.command_id,
            '类型': cmd.command_type,
            '目标': cmd.target,
            '动作': cmd.action,
            '参数': str(cmd.parameters)[:50] + "..." if len(str(cmd.parameters)) > 50 else str(cmd.parameters)
        })
    
    import pandas as pd
    df_history = pd.DataFrame(history_data)
    st.dataframe(df_history, use_container_width=True)
else:
    st.info("暂无命令历史")