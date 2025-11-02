import gradio as gr
from typing import Any, Tuple, Optional, List
from queue import Empty, Queue


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
        self._recent_messages: List[Any] = []

    def _send_control(self, client_id: str, cmd_type: str, action: str, params_text: str) -> Tuple[str, dict]:
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
                "target": client_id or "",
                "action": action or "",
                "parameters": parameters,
            }

            topic = f"device/{client_id}/control"
            try:
                loader = getattr(self.mqtt_manager, "config_loader", None)
                if loader:
                    topic = loader.format_topic_from_config("control", client_id)
            except Exception:
                pass

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

    def _drain_mqtt_messages(self) -> Any:
        self.logger.warning(f"<<<<STP5:UI_DRAIN_TICK: start")
        drained = False
        while True:
            try:
                item = self._mqtt_queue.get_nowait()
                self._recent_messages.append(item)
                drained = True
            except Empty:
                break
        if drained and len(self._recent_messages) > 100:
            self._recent_messages = self._recent_messages[-100:]
        try:
            self.logger.warning(
                f"<<<<STP5:UI_DRAIN_TICK: drained={drained} size={len(self._recent_messages)}"
            )
        except Exception:
            pass
        return self._recent_messages

    def push_mqtt_message(self, topic: str, payload: Any) -> None:
        """供外部设备消息处理器调用，写入本页面队列。"""
        try:
            if self._mqtt_queue.full():
                try:
                    _ = self._mqtt_queue.get_nowait()
                except Empty:
                    pass
            self._mqtt_queue.put_nowait({"topic": topic, "payload": payload})
        except Exception as e:
            try:
                self.logger.warning(f"<<<<STP4:UI_QUEUE_ERROR: {e}")
            except Exception:
                pass

    def build(self):
        """构建页面，返回右侧消息展示组件，以便外部绑定/引用。"""
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 发送控制命令")
                client_id = gr.Textbox(label="Client ID", placeholder="目标设备ID，如 device_001")
                cmd_type = gr.Textbox(label="Type", value="ping")
                action = gr.Textbox(label="Action", value="echo")
                params_text = gr.Textbox(label="Parameters(JSON)", placeholder='例如 {"speed": 1}', lines=5)
                send_btn = gr.Button("发送控制命令")
                result = gr.Textbox(label="发送结果")
                sent_payload = gr.JSON(label="实际发送Payload")
                send_btn.click(
                    fn=self._send_control,
                    inputs=[client_id, cmd_type, action, params_text],
                    outputs=[result, sent_payload],
                )
            with gr.Column(scale=1):
                gr.Markdown("### 实时消息（自动刷新）")
                mqtt_json = gr.JSON(label="MQTT Messages (最新100条)")
                timer = gr.Timer(0.2, active=True)
                # 定时刷新右侧消息
                timer.tick(fn=self._drain_mqtt_messages, inputs=None, outputs=mqtt_json)

        return mqtt_json


def build_mqtt_tab(mqtt_manager: Optional[object], logger=None):
    """
    兼容旧接口：保留函数式入口，但内部改为类实现。
    推荐直接使用 MqttPage(ui_manager, logger).build()
    """
    page = MqttPage(mqtt_manager, logger)
    return page.build()