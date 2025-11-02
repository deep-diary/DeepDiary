import time
from typing import Any, Optional


class DeviceMessageHandler:
    """
    设备消息回调处理类（位于 app_logic 层，作为 MQTT 与 UI 的桥梁）：
    - 处理 device_info / device_status[/*] 等主题
    - 将消息转发到 UI（如果可用）
    - 在收到消息时回发一条 control 测试命令到对应设备
    """

    def __init__(self, *, logger, mqtt_manager, ui_manager: Optional[object] = None) -> None:
        self.logger = logger
        self.mqtt = mqtt_manager
        self.ui = ui_manager

    # ---- 公共辅助 ----
    def _extract_client_id(self, topic: str) -> Optional[str]:
        # 期望 topic: device/{client_id}/...
        try:
            parts = topic.split('/')
            if len(parts) >= 2 and parts[0] == 'device':
                return parts[1]
        except Exception:
            return None
        return None

    def _forward_to_ui(self, topic: str, payload: Any) -> None:
        if not self.ui:
            self.logger.warning(f"<<<<STP2:UI_FORWARD_ERROR: UI not found")
            return
        if not hasattr(self.ui, 'push_mqtt_message'):
            self.logger.warning(f"<<<<STP2:UI_FORWARD_ERROR: push_mqtt_message not found")
            return
        self.logger.warning(f"<<<<STP2:UI_FORWARD: topic={topic}")
        self.ui.push_mqtt_message(topic, payload)

    def _send_control_ping(self, client_id: Optional[str]) -> None:
        if not client_id:
            return
        control_topic = f"device/{client_id}/control"
        data = {
            "type": "ping",
            "target": client_id,
            "action": "echo",
            "parameters": {"ts": time.time()},
        }
        try:
            self.logger.warning(f"<<<<STP3:CONTROL_SEND: topic={control_topic} payload={data}")
            ok = self.mqtt.publish(control_topic, data, qos=1, retain=False)
            self.logger.warning(f"<<<<STP3:CONTROL_SEND_RESULT: ok={ok}")
        except Exception as e:
            self.logger.warning(f"<<<<STP3:CONTROL_SEND_ERROR: {e}")
    
    def send_test_topic(self):
        self.logger.warning(f">>>>>STP1:SEND_TEST_TOPIC: start")
        self.mqtt.publish("test/hello", {"message": "hello"}, qos=0, retain=False)
        while True:
            self.mqtt.publish("test/hello", {"message": "hello"}, qos=0, retain=False)
            time.sleep(5)

    # ---- 统一消息处理（根据topic分发） ----
    def handle_message(self, topic: str, payload: Any, message):
        """
        统一的消息处理函数，根据topic分发到不同的处理方法
        
        Args:
            topic: 消息主题
            payload: 消息内容（已解析）
            message: paho-mqtt的message对象
        """
        self.logger.warning(f"<<<<STP1:RECV: {topic}")
        
        # 根据topic分发消息
        if topic.startswith("test/"):
            self.on_test(topic, payload, message)
        elif "/device_info" in topic or topic.endswith("/info"):
            self.on_device_info(topic, payload, message)
        elif "/device_status" in topic or topic.endswith("/status"):
            self.on_device_status(topic, payload, message)
        elif "/device_status/system" in topic or topic.endswith("/status/system"):
            self.on_device_status_system(topic, payload, message)
        elif "/device_status/sensor" in topic or topic.endswith("/status/sensor"):
            self.on_device_status_sensor(topic, payload, message)
        elif "/device_status/actuator" in topic or topic.endswith("/status/actuator"):
            self.on_device_status_actuator(topic, payload, message)
        else:
            # 未知主题，默认转发到UI
            self.logger.warning(f"未知主题，默认处理: {topic}")
            self._forward_to_ui(topic, payload)
    
    # ---- 具体主题的处理方法 ----
    def on_device_info(self, topic, payload, message):
        self.logger.warning(f"<<<<STP1:RECV device_info: {topic}")
        self._forward_to_ui(topic, payload)
        self._send_control_ping(self._extract_client_id(topic))

    def on_device_status(self, topic, payload, message):
        self.logger.warning(f"<<<<STP1:RECV device_status: {topic}")
        self._forward_to_ui(topic, payload)
        self._send_control_ping(self._extract_client_id(topic))

    def on_device_status_system(self, topic, payload, message):
        self.logger.warning(f"<<<<STP1:RECV device_status_system: {topic}")
        self._forward_to_ui(topic, payload)
        self._send_control_ping(self._extract_client_id(topic))

    def on_device_status_sensor(self, topic, payload, message):
        self.logger.warning(f"<<<<STP1:RECV device_status_sensor: {topic}")
        self._forward_to_ui(topic, payload)
        self._send_control_ping(self._extract_client_id(topic))

    def on_device_status_actuator(self, topic, payload, message):
        self.logger.warning(f"<<<<STP1:RECV device_status_actuator: {topic}")
        self._forward_to_ui(topic, payload)
        self._send_control_ping(self._extract_client_id(topic))

    def on_test(self, topic, payload, message):
        self.logger.warning(f"<<<<STP1:RECV test: {topic}")
        self._forward_to_ui(topic, payload)

    # 允许在运行时注入/更新 UI 引用
    def set_ui_manager(self, ui_manager):
        self.ui = ui_manager


