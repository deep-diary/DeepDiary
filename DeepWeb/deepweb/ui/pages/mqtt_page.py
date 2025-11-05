import gradio as gr
from typing import Any, Tuple, Optional, List
from queue import Empty, Queue
import sys
from pathlib import Path
from typing import Dict

# 导入配置
try:
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    from deepweb.services.device_communication.mqtt_config import (
        CONTROL_TYPES,
        ACTION_TYPES,
        TARGET_DEVICES
    )
except ImportError:
    # 如果导入失败，使用默认值
    CONTROL_TYPES = {
        "led": "led",
        "motor": "motor",
        "arm": "arm",
        "gimbal": "gimbal",
        "camera": "camera",
        "system": "system"
    }
    ACTION_TYPES = {
        "start": "start",
        "stop": "stop",
        "restart": "restart",
        "reboot": "reboot",
        "factory_reset": "factory_reset",
        "update": "update",
        "config": "config"
    }


class MqttPage:
    """
    使用类来管理 MQTT 页面构建与交互，要求外部传入日志管理器。

    依赖：ui_manager 提供 coordinator、_mqtt_queue、_recent_messages、update_time()
    """

    def __init__(self, mqtt_manager: Optional[object], logger):
        self.mqtt_manager = mqtt_manager
        self.logger = logger
        # 子页面自管消息通道与缓存
        self._mqtt_queue: Queue = Queue(maxsize=1000)
        self.active_device_id: str = "ATK-DNESP32S3-9888e000ae28"
        self._recent_messages: List[Any] = []
        self._sensor_data: Dict[str, Any] = {
            "acc_x": 0.0,
            "acc_y": 0.0,
            "acc_z": 0.0,
            "acc_g": 0.0,
            "pitch": 0.0,
            "roll": 0.0,
            "sensor_status": "normal",
        }

    def _send_control(self, client_id: str, cmd_type: str, params_text: str) -> Tuple[str, dict]:
        if not self.mqtt_manager:
            return ("未找到协调器，无法发送", {})
        if not client_id or not client_id.strip():
            return ("Client ID 不能为空", {})
        try:
            import json
            parameters: Any = {}
            if params_text.strip():
                try:
                    parameters = json.loads(params_text)
                except Exception:
                    parameters = {"text": params_text}

            payload = {
                "type": cmd_type or "",
                "parameters": parameters,
            }

            # 优先使用配置加载器构建主题（根据 mqtt_config.py 中的配置）
            topic = ""
            try:
                loader = getattr(self.mqtt_manager, "config_loader", None)
                if loader:
                    topic = loader.format_topic_from_config("control", client_id)
                    if topic:
                        self.logger.debug(f"使用配置加载器生成主题: {topic}")
            except Exception as e:
                self.logger.warning(f"配置加载器失败: {e}")
            
            # 如果配置加载器失败或返回空，使用默认格式
            if not topic:
                topic = f"device/{client_id}/control"
                self.logger.debug(f"使用默认主题格式: {topic}")
            
            # 验证主题不为空
            if not topic or not topic.strip():
                error_msg = f"主题构建失败: client_id={client_id}"
                self.logger.error(error_msg)
                return (f"❌ {error_msg}", {})

            try:
                self.logger.warning(f"<<<<STP0:UI_SEND_CONTROL: topic={topic} payload={payload}")
            except Exception:
                pass
            ok = self.mqtt_manager.publish(topic, payload, qos=1, retain=False)
            try:
                self.logger.warning(f"<<<<STP0:UI_SEND_CONTROL_RESULT: ok={ok}")
            except Exception:
                pass
            status = "发送成功" if ok else "发送失败"
            return (f"{status}: {topic}", payload)
        except Exception as e:
            try:
                self.logger.warning(f"<<<<STP0:UI_SEND_CONTROL_ERROR: {e}")
            except Exception:
                pass
            return (f"发送异常: {e}", {})

    def _drain_mqtt_messages(self) -> Tuple[Any, Any, Any, Any, Any, Any, Any]:
        """
        定时器回调函数：从队列中取出消息并更新显示
        注意：这个方法会被 Gradio Timer 周期性调用
        Args:
            mqtt_json: MQTT消息
            g_acc_x: X轴加速度
            g_acc_y: Y轴加速度
            g_acc_z: Z轴加速度
            g_acc_g: 总加速度
            g_pitch: 俯仰角
            g_roll: 翻滚角
        Returns:
            (MQTT消息, X轴加速度, Y轴加速度, Z轴加速度, 总加速度, 俯仰角, 翻滚角)
        """
        mqtt_json = {}
        try:
            drained = False
            drained_count = 0
            while True:
                try:
                    item = self._mqtt_queue.get_nowait()
                    # 将最新消息插入到列表最前面
                    self._recent_messages.insert(0, item)
                    drained = True
                    drained_count += 1
                    self.logger.warning(f"<<<<STP5:UI_DRAIN_TICK: item={item},drained={drained},drained_count={drained_count},queue_size={self._mqtt_queue.qsize()},messages_size={len(self._recent_messages)}")
                except Empty:
                    break
            if drained and len(self._recent_messages) > 100:
                # 保留前100条消息（最新的100条）
                self._recent_messages = self._recent_messages[:100]
        except Exception as e:
            self.logger.error(f"<<<<STP5:UI_DRAIN_TICK_ERROR: {e}", exc_info=True)

        if self._recent_messages:
            # 最新消息现在在最前面（索引0）
            mqtt_json = self._recent_messages[0]

        # 如果mqtt_json 的topic 包含sensor 字段，则进行解析，否则返回0.0
        if "sensor" in mqtt_json.get("topic", ""):
            payload = mqtt_json.get("payload", {})

            self._sensor_data["acc_x"] = payload.get("acc_x", 0.0)
            self._sensor_data["acc_y"] = payload.get("acc_y", 0.0)
            self._sensor_data["acc_z"] = payload.get("acc_z", 0.0)
            self._sensor_data["acc_g"] = payload.get("acc_g", 0.0)
            self._sensor_data["pitch"] = payload.get("pitch", 0.0)
            self._sensor_data["roll"] = payload.get("roll", 0.0)

            # self.logger.warning(f"<<<<STP6:UI_DRAIN_TICK_SENSOR_DATA: {self._sensor_data}")

        # 明确返回6个传感器数值，保证顺序与UI组件一致
        return (
            self._recent_messages,
            self._sensor_data["acc_x"],
            self._sensor_data["acc_y"],
            self._sensor_data["acc_z"],
            self._sensor_data["acc_g"],
            self._sensor_data["pitch"],
            self._sensor_data["roll"],
        )
        

    def push_mqtt_message(self, topic: str, payload: Any) -> None:
        """供外部设备消息处理器调用，写入本页面队列。"""
        try:
            if self._mqtt_queue.full():
                try:
                    _ = self._mqtt_queue.get_nowait()
                except Empty:
                    pass
            self._mqtt_queue.put_nowait({"topic": topic, "payload": payload})
            self.logger.warning(f"<<<<STP4:UI_QUEUE_RESULT: alreadt push the message to the queue")
        except Exception as e:
            self.logger.warning(f"<<<<STP4:UI_QUEUE_ERROR: {e}")

    def build(self):
        """构建页面，返回右侧消息展示组件，以便外部绑定/引用。"""
        with gr.Row():
            with gr.Column(scale=1):
                # 使用 Interface 类创建控制命令界面
                # 根据 Gradio 文档：https://www.gradio.app/guides/the-interface-class#example-inputs
                mqtt_control_interface = gr.Interface(
                    fn=self._send_control,
                    inputs=[
                        gr.Textbox(
                            label="设备ID (Client ID)",
                            placeholder=f"例如: {self.active_device_id}",
                            value=self.active_device_id,
                            info="目标设备的唯一标识符"
                        ),
                        gr.Dropdown(
                            choices=list(CONTROL_TYPES.values()),
                            value="led",  # 使用有效的默认值
                            label="命令类型 (Type)",
                            info="选择要发送的命令类型"
                        ),
                        gr.Textbox(
                            label="参数 (Parameters)",
                            placeholder='JSON格式，例如: {"enable": true}',
                            lines=5,
                            info="命令参数，支持JSON格式或纯文本"
                        )
                    ],
                    outputs=[
                        gr.Textbox(
                            label="发送结果",
                            lines=2
                        ),
                        gr.JSON(
                            label="实际发送的Payload"
                        )
                    ],
                    title="📤 发送控制命令",
                    description="通过 MQTT 发送控制命令到目标设备。选择命令类型、动作和参数，点击提交发送。",
                    examples=[
                        # 示例格式：[client_id, cmd_type, params_text]
                        [self.active_device_id, "led", '{"color": "red", "brightness": 100, "speed": 1}'],
                        [self.active_device_id, "motor", '{"mode": "position", "target_position": 100, "target_speed": 100, "target_current": 100}'],
                        [self.active_device_id, "gimbal", '{"target_pitch": 100, "target_roll": 100, "speed": 100}'],
                        [self.active_device_id, "camera", '{"enable": true}'],
                        [self.active_device_id, "system", '{"mode": "normal", "reboot": true, "factory_reset": true, "update": true, "config": "example"}'],
                    ],
                    examples_per_page=6,  # 每页显示6个示例
                )

            with gr.Column(scale=2):
                with gr.Blocks():
                    gr.Markdown("### 实时消息（自动刷新）")
                    mqtt_json = gr.JSON(label="MQTT Messages (最新100条)")

                    # 显示传感器反馈消息的UI
                    g_acc_x = gr.Textbox(label="acc_x", value=0.0)
                    g_acc_y = gr.Textbox(label="acc_y", value=0.0)
                    g_acc_z = gr.Textbox(label="acc_z", value=0.0)
                    g_acc_g = gr.Textbox(label="acc_g", value=0.0)
                    g_pitch = gr.Textbox(label="pitch", value=0.0)
                    g_roll = gr.Textbox(label="roll", value=0.0)
                    
                    timer = gr.Timer(1, active=True)
                    timer.tick(fn=self._drain_mqtt_messages, 
                    inputs=None, 
                    outputs=[mqtt_json, g_acc_x, g_acc_y, g_acc_z, g_acc_g, g_pitch, g_roll]
                    )
                    self.logger.info(f"timer registered: interval=1s, active=True, output_component={mqtt_json}")

        return mqtt_json

def build_mqtt_tab(mqtt_manager: Optional[object], logger=None):
    """
    兼容旧接口：保留函数式入口，但内部改为类实现。
    推荐直接使用 MqttPage(ui_manager, logger).build()
    """
    page = MqttPage(mqtt_manager, logger)
    return page.build()