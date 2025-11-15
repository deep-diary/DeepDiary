"""
Thumbler 不倒翁页面
根据 README.md 需求文档实现
"""

import gradio as gr
from typing import Optional, Any, Dict, Tuple
from queue import Empty, Queue
import time
from deepweb.services.device_communication.mqtt_config import (
    THUMBLER_LED_MODES,
    THUMBLER_MODES
)
from deepweb.services.device_communication.mqtt_config_loader import MQTTConfigLoader


class ThumblerPage:
    """
    Thumbler 不倒翁页面管理类
    
    负责构建 Thumbler 设备的监控和控制界面，包括：
    - 实时视频流显示
    - 设备状态监控（MQTT 接收）
    - 设备控制命令发送（MQTT 发送）
    """

    def __init__(
        self,
        device_id: str = "ATK-DNESP32S3-9888e000ae28",
        host: str = "35.192.64.247",
        mqtt_manager: Optional[object] = None,
        log_manager = None
    ):
        """
        初始化 Thumbler 页面
        
        Args:
            device_id: 设备唯一标识符
            host: 流媒体服务器地址
            mqtt_manager: MQTT 管理器实例
            log_manager: 日志管理器实例（必须）
        """
        if log_manager is None:
            raise ValueError("log_manager 必须提供")
        
        self.device_id = device_id
        self.host = host
        self.mqtt_manager = mqtt_manager
        self.log_manager = log_manager
        self.logger = log_manager.get_logger(__name__)
        
        # MQTT 配置加载器
        self.config_loader = MQTTConfigLoader()
        
        # MQTT 消息队列
        self._mqtt_queue: Queue = Queue(maxsize=1000)
        self._recent_messages: list = []
        
        # 离线判断阈值（秒）
        self._offline_threshold = 30.0
        
        # 设备状态数据（按设备ID存储）
        # 格式: {device_id: {状态字段..., "last_update_time": timestamp}}
        self._device_statuses: Dict[str, Dict[str, Any]] = {}
        
        # 初始化所有设备的状态数据
        for device_id in self.get_device_id():
            self._device_statuses[device_id] = {
                "cur_cam_switch": False,
                "g_acc_x": 0.0,
                "g_acc_y": 0.0,
                "g_acc_z": 0.0,
                "g_acc_g": 0.0,
                "g_pitch": 0.0,
                "g_roll": 0.0,
                "cur_led_mode": 0,
                "cur_led_brightness": 0,
                "cur_led_low_brightness": 0,
                "cur_led_color_red": 0,
                "cur_led_color_green": 0,
                "cur_led_color_blue": 0,
                "cur_led_interval_ms": 0,
                "cur_led_scroll_length": 0,
                "cur_tumbler_mode": 0,
                "is_has_people": False,
                "power_percent": 0,
                "last_update_time": None,  # 最后收到消息的时间戳
            }
        
        # 视频流 URL
        self.rtsp_url = f"rtsp://{host}:8554/{device_id}"
        self.web_stream_url = f"https://www.deep-diary.com/mediamtx/{device_id}"
        
        # 订阅所有设备的 status 主题（只订阅具体设备，不订阅通配符）
        # 注意：MQTT 管理器不再自动订阅通配符主题，改为由页面层根据需要订阅具体设备主题
        # 这样可以只接收特定设备的消息，而不是所有设备的消息
        if self.mqtt_manager:
            self._subscribe_all_devices_status()
        
        self.logger.info(f"ThumblerPage 初始化完成，设备ID: {device_id}")

    def get_device_id(self) -> list:
        """
        获取可用设备ID列表
        
        Returns:
            list: 设备ID列表，暂时返回两个设备，后续通过API获取
        """
        return [
            "ATK-DNESP32S3-9888e000ae28",
            "ATK-DNESP32S3-9888e000ae29"
        ]
    
    def _subscribe_device_status(self, device_id: str) -> bool:
        """
        订阅指定设备的 status 主题
        
        Args:
            device_id: 设备ID
            
        Returns:
            bool: 是否成功
        """
        if not self.mqtt_manager:
            self.logger.warning("MQTT 管理器未初始化，无法订阅主题")
            return False
        
        try:
            # 使用配置加载器格式化主题
            topic = self.config_loader.format_topic_from_config(
                "thumbler_status",
                device_id=device_id
            )
            
            if not topic:
                self.logger.error(f"无法格式化设备 {device_id} 的主题")
                return False
            
            # 订阅主题（QoS=0，根据配置）
            qos = 0
            success = self.mqtt_manager.subscribe(topic, qos, queue_if_disconnected=True)
            
            if success:
                self.logger.info(f"已订阅设备 {device_id} 的状态主题: {topic} (QoS: {qos})")
            else:
                self.logger.warning(f"订阅设备 {device_id} 的状态主题失败: {topic}")
            
            return success
        except Exception as e:
            self.logger.error(f"订阅设备 {device_id} 状态主题时出错: {e}", exc_info=True)
            return False
    
    def _subscribe_all_devices_status(self) -> None:
        """
        订阅所有设备的 status 主题
        """
        if not self.mqtt_manager:
            self.logger.warning("MQTT 管理器未初始化，无法订阅主题")
            return
        
        device_list = self.get_device_id()
        self.logger.info(f"开始订阅 {len(device_list)} 个设备的状态主题")
        
        for device_id in device_list:
            self._subscribe_device_status(device_id)

    def push_mqtt_message(self, topic: str, payload: Any) -> None:
        """
        供外部设备消息处理器调用，写入本页面队列
        
        Args:
            topic: MQTT 主题
            payload: MQTT 消息负载
        """
        try:
            if self._mqtt_queue.full():
                try:
                    _ = self._mqtt_queue.get_nowait()
                except Empty:
                    pass
            self._mqtt_queue.put_nowait({"topic": topic, "payload": payload})
        except Exception as e:
            self.logger.warning(f"MQTT 消息入队失败: {e}")

    def _extract_device_id_from_topic(self, topic: str) -> Optional[str]:
        """
        从 MQTT 主题中提取设备ID
        
        Args:
            topic: MQTT 主题，格式为 "Thumbler/{device_id}/status"
            
        Returns:
            设备ID，如果无法提取则返回 None
        """
        try:
            # 主题格式: Thumbler/{device_id}/status
            if topic.startswith("Thumbler/") and topic.endswith("/status"):
                parts = topic.split("/")
                if len(parts) == 3:
                    return parts[1]  # 返回 device_id
        except Exception as e:
            self.logger.warning(f"从主题提取设备ID失败: {topic}, {e}")
        return None
    
    def _drain_mqtt_messages(self) -> Dict[str, Any]:
        """
        定时器回调函数：从队列中取出消息并更新设备状态
        
        Returns:
            当前选中设备的设备状态字典
        """
        try:
            # 清空队列中的消息
            while True:
                try:
                    item = self._mqtt_queue.get_nowait()
                    self._recent_messages.insert(0, item)
                    
                    # 处理每条消息，更新对应设备的状态
                    topic = item.get("topic", "")
                    payload = item.get("payload", {})
                    
                    # 从主题中提取设备ID
                    device_id = self._extract_device_id_from_topic(topic)
                    if device_id and device_id in self._device_statuses:
                        # 更新对应设备的状态
                        device_status = self._device_statuses[device_id]
                        for key in device_status.keys():
                            if key == "last_update_time":
                                continue  # 跳过时间戳字段，单独处理
                            if key in payload:
                                device_status[key] = payload[key]
                        
                        # 更新最后收到消息的时间
                        device_status["last_update_time"] = time.time()
                        
                except Empty:
                    break
            
            # 保留最新100条消息
            if len(self._recent_messages) > 100:
                self._recent_messages = self._recent_messages[:100]
        
        except Exception as e:
            self.logger.error(f"处理 MQTT 消息时出错: {e}", exc_info=True)
        
        # 返回当前选中设备的状态
        if self.device_id in self._device_statuses:
            return self._device_statuses[self.device_id].copy()
        else:
            # 如果当前设备ID不在状态字典中，返回空状态
            return {}

    def _send_control_command(self, **kwargs) -> Tuple[str, Dict[str, Any]]:
        """
        发送控制命令到设备
        
        Args:
            **kwargs: 控制参数（tar_cam_switch, tar_pitch, tar_roll, tar_led_* 等）
        
        Returns:
            (状态消息, 发送的负载)
        """
        if not self.mqtt_manager:
            return ("❌ 未找到 MQTT 管理器，无法发送", {})
        
        try:
            # 构建控制命令负载
            payload: Dict[str, Any] = {}
            
            # 基础控制字段
            if "tar_cam_switch" in kwargs and kwargs["tar_cam_switch"] is not None:
                payload["tar_cam_switch"] = kwargs["tar_cam_switch"]
            if "tar_pitch" in kwargs and kwargs["tar_pitch"] is not None:
                payload["tar_pitch"] = float(kwargs["tar_pitch"])
            if "tar_roll" in kwargs and kwargs["tar_roll"] is not None:
                payload["tar_roll"] = float(kwargs["tar_roll"])
            if "tar_tumbler_mode" in kwargs and kwargs["tar_tumbler_mode"] is not None:
                payload["tar_tumbler_mode"] = int(kwargs["tar_tumbler_mode"])
            
            # LED 控制字段
            led_fields = [
                "tar_led_mode", "tar_led_brightness", "tar_led_low_brightness",
                "tar_led_color_red", "tar_led_color_green", "tar_led_color_blue",
                "tar_led_color_low_red", "tar_led_color_low_green", "tar_led_color_low_blue",
                "tar_led_interval_ms", "tar_led_scroll_length"
            ]
            for field in led_fields:
                if field in kwargs and kwargs[field] is not None:
                    payload[field] = int(kwargs[field])
            
            # 添加时间戳
            payload["timestamp"] = int(time.time())
            
            # 格式化主题
            topic = self.config_loader.format_topic_from_config("thumbler_cmd", device_id=self.device_id)
            if not topic:
                topic = f"Thumbler/{self.device_id}/cmd"
            
            # 发送消息
            ok = self.mqtt_manager.publish(topic, payload, qos=1, retain=False)
            
            if ok:
                self.logger.info(f"控制命令发送成功: {topic}, payload: {payload}")
                return (f"✅ 发送成功: {topic}", payload)
            else:
                self.logger.warning(f"控制命令发送失败: {topic}")
                return (f"❌ 发送失败: {topic}", payload)
        
        except Exception as e:
            self.logger.error(f"发送控制命令时出错: {e}", exc_info=True)
            return (f"❌ 发送异常: {e}", {})

    def build(self):
        """
        构建页面 UI 组件
        
        Returns:
            构建好的 Gradio 组件
        """
        with gr.Column():
            gr.Markdown(f"## 🎯 Thumbler 不倒翁控制页面")
            
            # 设备选择下拉框
            device_list = self.get_device_id()
            device_selector = gr.Dropdown(
                label="设备选择",
                choices=device_list,
                value=self.device_id,
                interactive=True
            )
            
            # 主要内容区域：左侧状态监控（2），右侧控制面板（1）
            with gr.Row():
                # 左侧：设备状态监控（比例2）
                with gr.Column(scale=2):
                    gr.Markdown("### 📊 设备状态监控")
                    
                    with gr.Row():
                        # 左侧：传感器数据
                        with gr.Column(scale=1):
                            gr.Markdown("#### 传感器数据")
                            with gr.Row():
                                status_acc_x = gr.Textbox(
                                    label="X轴加速度 (m/s²)",
                                    value="0.00",
                                    interactive=False,
                                    scale=1
                                )
                                status_acc_y = gr.Textbox(
                                    label="Y轴加速度 (m/s²)",
                                    value="0.00",
                                    interactive=False,
                                    scale=1
                                )
                            with gr.Row():
                                status_acc_z = gr.Textbox(
                                    label="Z轴加速度 (m/s²)",
                                    value="0.00",
                                    interactive=False,
                                    scale=1
                                )
                                status_acc_g = gr.Textbox(
                                    label="总加速度 (m/s²)",
                                    value="0.00",
                                    interactive=False,
                                    scale=1
                                )
                            with gr.Row():
                                status_pitch = gr.Textbox(
                                    label="俯仰角 (°)",
                                    value="0.00",
                                    interactive=False,
                                    scale=1
                                )
                                status_roll = gr.Textbox(
                                    label="翻滚角 (°)",
                                    value="0.00",
                                    interactive=False,
                                    scale=1
                                )
                            with gr.Row():
                                status_power_text = gr.Textbox(
                                    label="系统电量",
                                    value="0%",
                                    interactive=False,
                                    scale=1
                                )
                                status_led_brightness = gr.Textbox(
                                    label="LED亮度",
                                    value="0",
                                    interactive=False,
                                    scale=1
                                )
                        
                        # 右侧：视频流（铺满区域显示）
                        with gr.Column(scale=1):
                            gr.Markdown("#### 📹 实时视频流")
                            web_player_html = f"""
                            <div style="width: 100%; aspect-ratio: 4/3; margin: 0 auto; background: #000;">
                                <iframe 
                                    src="{self.web_stream_url}/"
                                    style="width: 100%; height: 100%; border: none; background: #000;"
                                    allowfullscreen
                                    allow="autoplay; encrypted-media"
                                ></iframe>
                            </div>
                            """
                            video_player = gr.HTML(
                                value=web_player_html,
                                label=""
                            )
                    
                    # 状态指示器
                    gr.Markdown("#### 状态指示")
                    with gr.Row():
                        status_cam_switch = gr.Textbox(
                            label="摄像头开关状态",
                            value="未知",
                            interactive=False
                        )
                        status_people = gr.Textbox(
                            label="当前是否有人",
                            value="未知",
                            interactive=False
                        )
                        status_led_mode = gr.Textbox(
                            label="当前LED模式",
                            value="未知",
                            interactive=False
                        )
                    with gr.Row():
                        status_tumbler_mode = gr.Textbox(
                            label="当前不倒翁模式",
                            value="未知",
                            interactive=False
                        )
                        status_update_time = gr.Textbox(
                            label="上次更新时间",
                            value="--",
                            interactive=False
                        )
                        status_online = gr.HTML(
                            label="连接状态",
                            value='<div style="padding: 8px; text-align: center; border-radius: 4px; background-color: #4CAF50; color: white; font-weight: bold;">Online</div>'
                        )
                
                # 右侧：控制面板（比例1）
                with gr.Column(scale=1):
                    gr.Markdown("### 🎮 控制面板")
                    
                    # 基础控制
                    with gr.Group():
                        gr.Markdown("#### 基础控制")
                        control_cam_switch = gr.Checkbox(
                            label="摄像头开关",
                            value=False
                        )
                        control_pitch = gr.Slider(
                            label="目标俯仰角 (°)",
                            minimum=-90,
                            maximum=90,
                            value=0,
                            step=0.1
                        )
                        control_roll = gr.Slider(
                            label="目标翻滚角 (°)",
                            minimum=-90,
                            maximum=90,
                            value=0,
                            step=0.1
                        )
                        control_tumbler_mode = gr.Radio(
                            label="不倒翁工作模式",
                            choices=[
                                ("静止", 0),
                                ("左右循环晃动", 1),
                                ("来回旋转", 2),
                                ("充电中", 3)
                            ],
                            value=0,
                            type="value"
                        )
                    
                    # LED 控制
                    with gr.Group():
                        gr.Markdown("#### LED 控制")
                        control_led_mode = gr.Dropdown(
                            label="LED 工作模式",
                            choices=[
                                ("关闭", 0),
                                ("静态颜色", 1),
                                ("闪烁", 2),
                                ("呼吸灯", 3),
                                ("流水灯/滚动", 4),
                                ("系统状态", 5)
                            ],
                            value=0,
                            type="value"
                        )
                        control_led_brightness = gr.Slider(
                            label="LED 默认亮度",
                            minimum=0,
                            maximum=255,
                            value=128,
                            step=1
                        )
                        control_led_low_brightness = gr.Slider(
                            label="LED 低亮度",
                            minimum=0,
                            maximum=255,
                            value=16,
                            step=1
                        )
                        
                        gr.Markdown("**主颜色 (RGB)**")
                        control_led_color_red = gr.Slider(
                            label="红色",
                            minimum=0,
                            maximum=255,
                            value=0,
                            step=1
                        )
                        control_led_color_green = gr.Slider(
                            label="绿色",
                            minimum=0,
                            maximum=255,
                            value=0,
                            step=1
                        )
                        control_led_color_blue = gr.Slider(
                            label="蓝色",
                            minimum=0,
                            maximum=255,
                            value=0,
                            step=1
                        )
                        
                        gr.Markdown("**低颜色 (RGB) - 用于呼吸灯和流水灯**")
                        control_led_color_low_red = gr.Slider(
                            label="低红色",
                            minimum=0,
                            maximum=255,
                            value=0,
                            step=1
                        )
                        control_led_color_low_green = gr.Slider(
                            label="低绿色",
                            minimum=0,
                            maximum=255,
                            value=0,
                            step=1
                        )
                        control_led_color_low_blue = gr.Slider(
                            label="低蓝色",
                            minimum=0,
                            maximum=255,
                            value=0,
                            step=1
                        )
                        
                        control_led_interval_ms = gr.Number(
                            label="动画间隔时间 (毫秒)",
                            value=500,
                            minimum=50,
                            maximum=1000,
                            step=10
                        )
                        control_led_scroll_length = gr.Number(
                            label="滚动长度 (仅流水灯模式)",
                            value=3,
                            minimum=1,
                            maximum=20,
                            step=1
                        )
                    
                    # 发送按钮
                    send_btn = gr.Button("发送控制命令", variant="primary", size="lg")
                    send_status = gr.Textbox(
                        label="发送状态",
                        value="等待发送...",
                        interactive=False
                    )
                    send_payload = gr.JSON(
                        label="发送的负载",
                        value={}
                    )
            
            # 定时器：更新设备状态（必须在所有组件定义之后）
            def update_status():
                """更新设备状态显示"""
                status = self._drain_mqtt_messages()
                
                # 基础状态
                cam_status = "On" if status.get("cur_cam_switch", False) else "Off"
                power = status.get("power_percent", 0)
                people_status = "true" if status.get("is_has_people", False) else "false"
                
                tumbler_mode_map = {
                    0: "静止",
                    1: "左右循环晃动",
                    2: "来回旋转",
                    3: "充电中"
                }
                tumbler_mode = tumbler_mode_map.get(status.get("cur_tumbler_mode", 0), "未知")
                
                # LED 模式
                led_mode_map = {
                    0: "关闭",
                    1: "静态颜色",
                    2: "闪烁",
                    3: "呼吸灯",
                    4: "流水灯",
                    5: "系统状态"
                }
                led_mode = led_mode_map.get(status.get("cur_led_mode", 0), "未知")
                
                # 最后更新时间（从消息中获取，而不是当前时间）
                last_update_time = status.get("last_update_time")
                if last_update_time:
                    from datetime import datetime
                    update_time_str = datetime.fromtimestamp(last_update_time).strftime("%Y-%m-%d %H:%M:%S")
                else:
                    update_time_str = "--"
                
                # 判断在线状态：如果当前时间 - 最后更新时间 > 阈值，则离线
                current_time = time.time()
                is_online = False
                if last_update_time:
                    time_diff = current_time - last_update_time
                    is_online = time_diff <= self._offline_threshold
                
                # 生成带颜色的连接状态HTML
                if is_online:
                    online_status_html = '<div style="padding: 8px; text-align: center; border-radius: 4px; background-color: #4CAF50; color: white; font-weight: bold;">Online</div>'
                else:
                    online_status_html = '<div style="padding: 8px; text-align: center; border-radius: 4px; background-color: #f44336; color: white; font-weight: bold;">Offline</div>'
                
                return (
                    gr.update(value=f"{status.get('g_acc_x', 0.0):.1f}"),
                    gr.update(value=f"{status.get('g_acc_y', 0.0):.1f}"),
                    gr.update(value=f"{status.get('g_acc_z', 0.0):.1f}"),
                    gr.update(value=f"{status.get('g_acc_g', 0.0):.1f}"),
                    gr.update(value=f"{status.get('g_pitch', 0.0):.1f}"),
                    gr.update(value=f"{status.get('g_roll', 0.0):.1f}"),
                    gr.update(value=f"{power}%"),
                    gr.update(value=str(status.get("cur_led_brightness", 0))),
                    gr.update(value=cam_status),
                    gr.update(value=people_status),
                    gr.update(value=led_mode),
                    gr.update(value=tumbler_mode),
                    gr.update(value=update_time_str),
                    gr.update(value=online_status_html)
                )
            
            # 设备选择变更处理
            def on_device_change(selected_device_id):
                """设备选择变更时的处理"""
                if selected_device_id:
                    self.device_id = selected_device_id
                    # 更新视频流URL
                    self.rtsp_url = f"rtsp://{self.host}:8554/{selected_device_id}"
                    self.web_stream_url = f"https://www.deep-diary.com/mediamtx/{selected_device_id}"
                    
                    # 订阅新设备的 status 主题（只订阅具体设备，不订阅通配符）
                    self._subscribe_device_status(selected_device_id)
                    
                    # 更新视频播放器
                    new_web_player_html = f"""
                    <div style="width: 100%; aspect-ratio: 4/3; margin: 0 auto; background: #000;">
                        <iframe 
                            src="{self.web_stream_url}/"
                            style="width: 100%; height: 100%; border: none; background: #000;"
                            allowfullscreen
                            allow="autoplay; encrypted-media"
                        ></iframe>
                    </div>
                    """
                    self.logger.info(f"设备已切换为: {selected_device_id}")
                    
                    # 切换设备后，立即更新状态显示（使用新设备的状态）
                    # 触发一次状态更新
                    status = self._device_statuses.get(selected_device_id, {})
                    
                    # 基础状态
                    cam_status = "On" if status.get("cur_cam_switch", False) else "Off"
                    power = status.get("power_percent", 0)
                    people_status = "true" if status.get("is_has_people", False) else "false"
                    
                    tumbler_mode_map = {
                        0: "静止",
                        1: "左右循环晃动",
                        2: "来回旋转",
                        3: "充电中"
                    }
                    tumbler_mode = tumbler_mode_map.get(status.get("cur_tumbler_mode", 0), "未知")
                    
                    # LED 模式
                    led_mode_map = {
                        0: "关闭",
                        1: "静态颜色",
                        2: "闪烁",
                        3: "呼吸灯",
                        4: "流水灯",
                        5: "系统状态"
                    }
                    led_mode = led_mode_map.get(status.get("cur_led_mode", 0), "未知")
                    
                    # 最后更新时间
                    last_update_time = status.get("last_update_time")
                    if last_update_time:
                        from datetime import datetime
                        update_time_str = datetime.fromtimestamp(last_update_time).strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        update_time_str = "--"
                    
                    # 判断在线状态
                    current_time = time.time()
                    is_online = False
                    if last_update_time:
                        time_diff = current_time - last_update_time
                        is_online = time_diff <= self._offline_threshold
                    
                    # 生成带颜色的连接状态HTML
                    if is_online:
                        online_status_html = '<div style="padding: 8px; text-align: center; border-radius: 4px; background-color: #4CAF50; color: white; font-weight: bold;">Online</div>'
                    else:
                        online_status_html = '<div style="padding: 8px; text-align: center; border-radius: 4px; background-color: #f44336; color: white; font-weight: bold;">Offline</div>'
                    
                    # 返回更新的组件值（包括视频播放器和所有状态组件）
                    return (
                        gr.update(value=new_web_player_html),
                        gr.update(value=f"{status.get('g_acc_x', 0.0):.1f}"),
                        gr.update(value=f"{status.get('g_acc_y', 0.0):.1f}"),
                        gr.update(value=f"{status.get('g_acc_z', 0.0):.1f}"),
                        gr.update(value=f"{status.get('g_acc_g', 0.0):.1f}"),
                        gr.update(value=f"{status.get('g_pitch', 0.0):.1f}"),
                        gr.update(value=f"{status.get('g_roll', 0.0):.1f}"),
                        gr.update(value=f"{power}%"),
                        gr.update(value=str(status.get("cur_led_brightness", 0))),
                        gr.update(value=cam_status),
                        gr.update(value=people_status),
                        gr.update(value=led_mode),
                        gr.update(value=tumbler_mode),
                        gr.update(value=update_time_str),
                        gr.update(value=online_status_html)
                    )
                # 如果没有选择设备，返回所有组件的空更新
                return (
                    gr.update(),
                    gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(), gr.update(), gr.update(), gr.update(),
                    gr.update(), gr.update(), gr.update(),
                    gr.update(), gr.update(), gr.update()
                )
            
            # 发送控制命令（必须在所有组件定义之后）
            def send_command(
                cam_switch=None, pitch=None, roll=None, tumbler_mode=None,
                led_mode=None, led_brightness=None, led_low_brightness=None,
                led_r=None, led_g=None, led_b=None,
                led_low_r=None, led_low_g=None, led_low_b=None,
                led_interval=None, led_scroll_length=None
            ):
                """发送控制命令"""
                # 如果所有参数都是 None，说明是初始化验证，直接返回
                if all(v is None for v in [
                    cam_switch, pitch, roll, tumbler_mode,
                    led_mode, led_brightness, led_low_brightness,
                    led_r, led_g, led_b,
                    led_low_r, led_low_g, led_low_b,
                    led_interval, led_scroll_length
                ]):
                    return (
                        gr.update(value="等待发送..."),
                        gr.update(value={})
                    )
                
                try:
                    # 使用默认值处理 None
                    result_msg, payload = self._send_control_command(
                        tar_cam_switch=cam_switch if cam_switch is not None else False,
                        tar_pitch=pitch if pitch is not None else 0.0,
                        tar_roll=roll if roll is not None else 0.0,
                        tar_tumbler_mode=tumbler_mode if tumbler_mode is not None else 0,
                        tar_led_mode=led_mode if led_mode is not None else 0,
                        tar_led_brightness=led_brightness if led_brightness is not None else 128,
                        tar_led_low_brightness=led_low_brightness if led_low_brightness is not None else 16,
                        tar_led_color_red=led_r if led_r is not None else 0,
                        tar_led_color_green=led_g if led_g is not None else 0,
                        tar_led_color_blue=led_b if led_b is not None else 0,
                        tar_led_color_low_red=led_low_r if led_low_r is not None else 0,
                        tar_led_color_low_green=led_low_g if led_low_g is not None else 0,
                        tar_led_color_low_blue=led_low_b if led_low_b is not None else 0,
                        tar_led_interval_ms=led_interval if led_interval is not None else 500,
                        tar_led_scroll_length=led_scroll_length if led_scroll_length is not None else 3
                    )
                    return (
                        gr.update(value=result_msg),
                        gr.update(value=payload)
                    )
                except Exception as e:
                    self.logger.error(f"发送控制命令时出错: {e}", exc_info=True)
                    return (
                        gr.update(value=f"❌ 发送失败: {e}"),
                        gr.update(value={})
                    )
            
            # 绑定事件（确保所有组件都已定义）
            # 设备选择变更事件（同时更新视频播放器和所有状态组件）
            device_selector.change(
                fn=on_device_change,
                inputs=[device_selector],
                outputs=[
                    video_player,
                    status_acc_x, status_acc_y, status_acc_z, status_acc_g,
                    status_pitch, status_roll, status_power_text, status_led_brightness,
                    status_cam_switch, status_people, status_led_mode,
                    status_tumbler_mode, status_update_time, status_online
                ]
            )
            
            # 发送按钮点击事件
            send_btn.click(
                fn=send_command,
                inputs=[
                    control_cam_switch, control_pitch, control_roll, control_tumbler_mode,
                    control_led_mode, control_led_brightness, control_led_low_brightness,
                    control_led_color_red, control_led_color_green, control_led_color_blue,
                    control_led_color_low_red, control_led_color_low_green, control_led_color_low_blue,
                    control_led_interval_ms, control_led_scroll_length
                ],
                outputs=[send_status, send_payload]
            )
            
            # 定时器：每秒更新一次状态
            status_timer = gr.Timer(1.0, active=True)
            status_timer.tick(
                fn=update_status,
                inputs=None,
                outputs=[
                    status_acc_x, status_acc_y, status_acc_z, status_acc_g,
                    status_pitch, status_roll, status_power_text, status_led_brightness,
                    status_cam_switch, status_people, status_led_mode,
                    status_tumbler_mode, status_update_time, status_online
                ]
            )
        
        self.logger.info("ThumblerPage UI 构建完成")

