# deepweb/app_logic/core_manager/handler/mqtt_handler.py
# MQTT 消息处理器
# 处理 MQTT 消息，作为 MQTT 与 UI 的桥梁

import time
from typing import Any, Optional

from ..base_handler import BaseHandler


class MQTTMessageHandler(BaseHandler):
    """
    MQTT 消息处理器（位于 app_logic 层，作为 MQTT 与 UI 的桥梁）：
    - 处理 device_info / device_status[/*] 等主题
    - 将消息转发到 UI（如果可用）
    - 在收到消息时回发一条 control 测试命令到对应设备
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        # 这些属性会在 set_coordinator_dependencies 中设置
        # self.logger
        # self.mqtt_manager
        # self.ui_manager

    def _validate_dependencies(self):
        """验证必需的依赖项"""
        if not self.logger:
            raise ValueError("缺少必需的依赖项: logger")
        if not self.mqtt_manager:
            raise ValueError("缺少必需的依赖项: mqtt_manager")

    def _connect_events(self):
        """连接事件处理器"""
        if self.logger:
            self.logger.debug("MQTTMessageHandler: 连接事件...")
        # 设置 MQTT 消息回调
        if self.mqtt_manager:
            self.mqtt_manager.set_message_callback(self.handle_message)

    # ---- 公共辅助方法 ----
    def _extract_client_id(self, topic: str) -> Optional[str]:
        """从 topic 中提取客户端 ID
        期望 topic: device/{client_id}/...
        """
        try:
            parts = topic.split('/')
            if len(parts) >= 2 and parts[0] == 'device':
                return parts[1]
        except Exception:
            return None
        return None

    def _forward_to_ui(self, topic: str, payload: Any) -> None:
        """将消息转发到 UI（直接调用 mqtt_page 的方法）"""
        if not self.ui_manager:
            if self.logger:
                self.logger.warning(f"UI_FORWARD_ERROR: UI not found, topic={topic}")
            return
        
        # 直接访问 ui_manager 的 _mqtt_page
        if not hasattr(self.ui_manager, '_mqtt_page') or not self.ui_manager._mqtt_page:
            if self.logger:
                self.logger.debug(f"UI_FORWARD_WARNING: MQTT page not initialized yet, topic={topic}")
            return
        
        mqtt_page = self.ui_manager._mqtt_page
        if not hasattr(mqtt_page, 'push_mqtt_message'):
            if self.logger:
                self.logger.warning(f"UI_FORWARD_ERROR: push_mqtt_message not found in mqtt_page, topic={topic}")
            return
        
        if self.logger:
            self.logger.debug(f"UI_FORWARD: topic={topic}")
        try:
            mqtt_page.push_mqtt_message(topic, payload)
        except Exception as e:
            if self.logger:
                self.logger.error(f"UI_FORWARD_ERROR: Failed to push message to mqtt_page: {e}")

    def _send_control_ping(self, client_id: Optional[str]) -> None:
        """发送控制 ping 消息到设备"""
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
            if self.logger:
                self.logger.debug(f"CONTROL_SEND: topic={control_topic}, payload={data}")
            if self.mqtt_manager:
                ok = self.mqtt_manager.publish(control_topic, data, qos=1, retain=False)
                if self.logger:
                    self.logger.debug(f"CONTROL_SEND_RESULT: ok={ok}")
        except Exception as e:
            if self.logger:
                self.logger.error(f"CONTROL_SEND_ERROR: {e}")

    def send_test_topic(self):
        """发送测试主题（用于测试）"""
        if not self.mqtt_manager:
            return
        if self.logger:
            self.logger.info("SEND_TEST_TOPIC: start")
        self.mqtt_manager.publish("test/hello", {"message": "hello"}, qos=0, retain=False)
        while True:
            self.mqtt_manager.publish("test/hello", {"message": "hello"}, qos=0, retain=False)
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
        if self.logger:
            self.logger.debug(f"RECV: {topic}")
        
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
            if self.logger:
                self.logger.warning(f"未知主题，默认处理: {topic}")
            self._forward_to_ui(topic, payload)

    # ---- 具体主题的处理方法 ----
    def on_device_info(self, topic, payload, message):
        """处理设备信息主题"""
        if self.logger:
            self.logger.debug(f"RECV device_info: {topic}")
        self._forward_to_ui(topic, payload)

    def on_device_status(self, topic, payload, message):
        """处理设备状态主题"""
        if self.logger:
            self.logger.debug(f"RECV device_status: {topic}")
        self._forward_to_ui(topic, payload)

    def on_device_status_system(self, topic, payload, message):
        """处理设备系统状态主题"""
        if self.logger:
            self.logger.debug(f"RECV device_status_system: {topic}")
        self._forward_to_ui(topic, payload)

    def on_device_status_sensor(self, topic, payload, message):
        """处理设备传感器状态主题"""
        if self.logger:
            self.logger.debug(f"RECV device_status_sensor: {topic}")
        self._forward_to_ui(topic, payload)

    def on_device_status_actuator(self, topic, payload, message):
        """处理设备执行器状态主题"""
        if self.logger:
            self.logger.debug(f"RECV device_status_actuator: {topic}")
        self._forward_to_ui(topic, payload)

    def on_test(self, topic, payload, message):
        """处理测试主题"""
        if self.logger:
            self.logger.debug(f"RECV test: {topic}")
        self._forward_to_ui(topic, payload)

