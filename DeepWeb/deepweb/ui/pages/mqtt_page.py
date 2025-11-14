import gradio as gr
from typing import Any, Optional, List, Tuple
from queue import Empty, Queue
import json
from deepweb.services.device_communication.mqtt_config_loader import MQTTConfigLoader


class MqttPage:
    """
    MQTT 测试页面 - 用于测试发送和接收原始 MQTT 消息
    
    功能：
    1. 显示收到的任何主题的 MQTT 消息（保留100条）
    2. 从配置文件读取所有主题，支持发送命令和状态主题
    3. 使用 gr.Interface 提供便捷的示例功能
    """

    def __init__(self, mqtt_manager: Optional[object], logger):
        self.mqtt_manager = mqtt_manager
        self.logger = logger
        # 消息队列和缓存
        self._mqtt_queue: Queue = Queue(maxsize=1000)
        self._recent_messages: List[Any] = []
        
        # 默认设备列表（可以从 ThumblerPage 获取或通过API获取）
        self.device_list = [
            "ATK-DNESP32S3-9888e000ae28",
            "ATK-DNESP32S3-9888e000ae29"
        ]
        
        # 从 mqtt_manager 获取配置加载器（如果可用），否则创建新实例
        if mqtt_manager and hasattr(mqtt_manager, 'config_loader'):
            self.config_loader = mqtt_manager.config_loader
            self.logger.debug("使用 mqtt_manager 的 config_loader")
        else:
            self.config_loader = MQTTConfigLoader()
            self.logger.debug("创建新的 config_loader 实例")
        
        # 从配置文件读取主题配置
        self._load_topic_configs()

    def _load_topic_configs(self):
        """从配置文件加载主题配置，按方向分类"""
        # 使用配置加载器的方法获取主题
        self.cmd_topics = self.config_loader.get_topics_by_direction("sub")  # Web发布（命令主题）
        self.status_topics = self.config_loader.get_topics_by_direction("pub")  # 设备发布（状态主题）
        
        self.logger.info(f"加载主题配置: {len(self.cmd_topics)} 个命令主题, {len(self.status_topics)} 个状态主题")
    
    def _get_topic_choices(self, topic_type: str) -> List[Tuple[str, str]]:
        """
        获取主题选择列表（用于UI下拉菜单）
        
        Args:
            topic_type: "cmd" 或 "status"
            
        Returns:
            List[Tuple[str, str]]: [(显示名称, topic_key), ...]
        """
        direction = "sub" if topic_type == "cmd" else "pub"
        return self.config_loader.get_topic_choices_for_ui(direction)
    
    def _send_json_message(self, device_id: str, topic_key: str, json_content: str) -> Tuple[str, dict]:
        """
        发送 JSON 消息到指定主题
        
        Args:
            device_id: 设备ID
            topic_key: 主题配置键名
            json_content: JSON 字符串内容
            
        Returns:
            (状态消息, 发送的payload字典)
        """
        if not self.mqtt_manager:
            return ("❌ MQTT 管理器未初始化", {})
        
        if not device_id or not device_id.strip():
            return ("❌ 设备ID不能为空", {})
        
        if not topic_key or not topic_key.strip():
            return ("❌ 主题不能为空", {})
        
        if not json_content or not json_content.strip():
            return ("❌ JSON 内容不能为空", {})
        
        try:
            # 解析 JSON
            try:
                payload = json.loads(json_content)
            except json.JSONDecodeError as e:
                return (f"❌ JSON 格式错误: {e}", {})
            
            # 格式化主题名称
            topic = self.config_loader.format_topic_from_config(topic_key, device_id=device_id)
            if not topic:
                return (f"❌ 主题格式化失败: {topic_key}", {})
            
            # 获取 QoS
            qos = self.config_loader.get_topic_qos(topic_key)
            
            # 发送消息
            ok = self.mqtt_manager.publish(topic, payload, qos=qos, retain=False)
            
            if ok:
                self.logger.info(f"发送消息成功: {topic} (QoS: {qos}) -> {payload}")
                return (f"✅ 发送成功: {topic} (QoS: {qos})", payload)
            else:
                self.logger.warning(f"发送消息失败: {topic}")
                return (f"❌ 发送失败: {topic}", payload)
                
        except Exception as e:
            self.logger.error(f"发送消息异常: {e}", exc_info=True)
            return (f"❌ 发送异常: {e}", {})

    def _drain_mqtt_messages(self) -> List[Any]:
        """
        定时器回调函数：从队列中取出消息并更新显示
        注意：这个方法会被 Gradio Timer 周期性调用
        
        Returns:
            最近100条消息列表
        """
        try:
            # 从队列中取出所有消息
            while True:
                try:
                    item = self._mqtt_queue.get_nowait()
                    # 将最新消息插入到列表最前面
                    self._recent_messages.insert(0, item)
                except Empty:
                    break
            
            # 保留最新100条消息
            if len(self._recent_messages) > 100:
                self._recent_messages = self._recent_messages[:100]
                
        except Exception as e:
            self.logger.error(f"处理 MQTT 消息时出错: {e}", exc_info=True)

        return self._recent_messages
    
    def _clear_messages(self) -> List[Any]:
        """
        清空消息列表和队列
        
        Returns:
            空列表（用于更新UI）
        """
        try:
            # 清空消息列表
            self._recent_messages.clear()
            
            # 清空队列
            while True:
                try:
                    self._mqtt_queue.get_nowait()
                except Empty:
                    break
            
            self.logger.info("消息列表和队列已清空")
        except Exception as e:
            self.logger.error(f"清空消息时出错: {e}", exc_info=True)
        
        return []

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

    def _get_cmd_examples(self) -> List[List[str]]:
        """获取命令主题的示例"""
        examples = []
        default_device = self.device_list[0] if self.device_list else ""
        
        # 基础控制示例
        examples.append([
            default_device,
            "thumbler_cmd",
            json.dumps({
                "tar_cam_switch": True,
                "tar_pitch": 10.0,
                "tar_roll": -5.0,
                "tar_tumbler_mode": 1,
                "timestamp": 1704067200
            }, ensure_ascii=False, indent=2)
        ])
        
        # LED 静态颜色示例
        examples.append([
            default_device,
            "thumbler_cmd",
            json.dumps({
                "tar_led_mode": 1,
                "tar_led_brightness": 128,
                "tar_led_color_red": 255,
                "tar_led_color_green": 0,
                "tar_led_color_blue": 0,
                "timestamp": 1704067200
            }, ensure_ascii=False, indent=2)
        ])
        
        return examples
    
    def _get_status_examples(self) -> List[List[str]]:
        """获取状态主题的示例（测试用）"""
        examples = []
        default_device = self.device_list[0] if self.device_list else ""
        
        # 状态消息示例
        examples.append([
            default_device,
            "thumbler_status",
            json.dumps({
                "cur_cam_switch": True,
                "g_acc_x": 0.12,
                "g_acc_y": -0.05,
                "g_acc_z": 9.81,
                "g_acc_g": 9.82,
                "g_pitch": 2.5,
                "g_roll": -1.2,
                "cur_led_mode": 2,
                "cur_led_brightness": 128,
                "cur_tumbler_mode": 1,
                "is_has_people": True,
                "power_percent": 85,
                "timestamp": 1704067200
            }, ensure_ascii=False, indent=2)
        ])
        
        return examples
    
    def build(self):
        """
        构建 MQTT 测试页面
        
        Returns:
            mqtt_json: 消息展示组件
        """
        gr.Markdown("## MQTT 测试页面")
        gr.Markdown("用于测试发送和接收原始 MQTT 消息。Thumbler 页面用于具体解析命令和状态内容。")
        
        with gr.Row():
            # 左侧：命令主题发送区域
            with gr.Column(scale=1):
                gr.Markdown("### 📤 发送命令主题")
                if self.cmd_topics:
                    cmd_topic_choices = self._get_topic_choices("cmd")
                    if cmd_topic_choices:
                        cmd_interface = gr.Interface(
                            fn=self._send_json_message,
                            inputs=[
                                gr.Dropdown(
                                    label="设备ID",
                                    choices=self.device_list,
                                    value=self.device_list[0] if self.device_list else "",
                                    info="选择目标设备"
                                ),
                                gr.Dropdown(
                                    label="主题",
                                    choices=cmd_topic_choices,
                                    value=cmd_topic_choices[0][1] if cmd_topic_choices else "",
                                    info="选择要发送的命令主题"
                                ),
                                gr.Textbox(
                                    label="JSON 内容",
                                    placeholder='{"tar_cam_switch": true, "tar_pitch": 10.0, ...}',
                                    lines=10,
                                    info="输入要发送的 JSON 内容"
                                )
                            ],
                            outputs=[
                                gr.Textbox(label="发送状态", lines=2),
                                gr.JSON(label="发送的 Payload")
                            ],
                            title="📤 发送命令",
                            description="发送控制命令到设备",
                            examples=self._get_cmd_examples(),
                            examples_per_page=2
                        )
                    else:
                        gr.Markdown("⚠️ 未找到可用的命令主题配置")
                else:
                    gr.Markdown("⚠️ 未找到可用的命令主题配置")
            
            # 中间：状态主题发送区域
            with gr.Column(scale=1):
                gr.Markdown("### 📤 发送状态主题（测试用）")
                if self.status_topics:
                    status_topic_choices = self._get_topic_choices("status")
                    if status_topic_choices:
                        status_interface = gr.Interface(
                            fn=self._send_json_message,
                            inputs=[
                                gr.Dropdown(
                                    label="设备ID",
                                    choices=self.device_list,
                                    value=self.device_list[0] if self.device_list else "",
                                    info="选择目标设备"
                                ),
                                gr.Dropdown(
                                    label="主题",
                                    choices=status_topic_choices,
                                    value=status_topic_choices[0][1] if status_topic_choices else "",
                                    info="选择要发送的状态主题（通常由设备发布，这里用于测试）"
                                ),
                                gr.Textbox(
                                    label="JSON 内容",
                                    placeholder='{"cur_cam_switch": true, "g_acc_x": 0.12, ...}',
                                    lines=10,
                                    info="输入要发送的 JSON 内容"
                                )
                            ],
                            outputs=[
                                gr.Textbox(label="发送状态", lines=2),
                                gr.JSON(label="发送的 Payload")
                            ],
                            title="📤 发送状态（测试）",
                            description="发送状态消息（通常由设备发布，这里用于测试）",
                            examples=self._get_status_examples(),
                            examples_per_page=1
                        )
                    else:
                        gr.Markdown("⚠️ 未找到可用的状态主题配置")
                else:
                    gr.Markdown("⚠️ 未找到可用的状态主题配置")
            
            # 右侧：接收消息区域
            with gr.Column(scale=1):
                with gr.Row():
                    gr.Markdown("### 📥 接收消息（自动刷新）")
                    clear_btn = gr.Button("清空消息", variant="stop", size="sm", scale=0)
                
                mqtt_json = gr.JSON(
                    label="MQTT 消息（最新100条）",
                    value=[]
                )
                
                # 绑定清空按钮
                clear_btn.click(
                    fn=self._clear_messages,
                    inputs=None,
                    outputs=[mqtt_json]
                )
                
                # 定时器：每秒更新一次消息列表
                timer = gr.Timer(1.0, active=True)
                timer.tick(
                    fn=self._drain_mqtt_messages,
                    inputs=None,
                    outputs=[mqtt_json]
                )
                
                self.logger.info("MQTT 测试页面构建完成")

        return mqtt_json

def build_mqtt_tab(mqtt_manager: Optional[object], logger=None):
    """
    兼容旧接口：保留函数式入口，但内部改为类实现。
    推荐直接使用 MqttPage(ui_manager, logger).build()
    """
    page = MqttPage(mqtt_manager, logger)
    return page.build()