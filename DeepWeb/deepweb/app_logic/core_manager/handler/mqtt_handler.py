# deepweb/app_logic/core_manager/handler/mqtt_handler.py
# MQTT 消息处理器
# 处理 MQTT 消息，作为 MQTT 与 UI 的桥梁

from typing import Any

from ..base_handler import BaseHandler


class MQTTMessageHandler(BaseHandler):
    """
    MQTT 消息处理器（位于 app_logic 层，作为 MQTT 与 UI 的桥梁）：
    - 处理 Thumbler 设备相关主题
    - 将消息转发到 UI（mqtt_page 和 thumbler_page）
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

    def _forward_to_ui(self, topic: str, payload: Any) -> None:
        """将消息转发到 UI（推送给 mqtt_page 和 thumbler_page）"""
        if not self.ui_manager:
            if self.logger:
                self.logger.warning(f"UI_FORWARD_ERROR: UI not found, topic={topic}")
            return
        
        # 转发到 mqtt_page（显示所有原始消息）
        if hasattr(self.ui_manager, '_mqtt_page') and self.ui_manager._mqtt_page:
            mqtt_page = self.ui_manager._mqtt_page
            if hasattr(mqtt_page, 'push_mqtt_message'):
                try:
                    mqtt_page.push_mqtt_message(topic, payload)
                except Exception as e:
                    if self.logger:
                        self.logger.error(f"UI_FORWARD_ERROR: Failed to push message to mqtt_page: {e}")
        
        # 如果是 Thumbler 相关主题，也转发到 thumbler_page
        if topic.startswith("Thumbler/") and topic.endswith("/status"):
            if hasattr(self.ui_manager, '_thumbler_page') and self.ui_manager._thumbler_page:
                thumbler_page = self.ui_manager._thumbler_page
                if hasattr(thumbler_page, 'push_mqtt_message'):
                    try:
                        thumbler_page.push_mqtt_message(topic, payload)
                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"UI_FORWARD_ERROR: Failed to push message to thumbler_page: {e}")

    # ---- 统一消息处理 ----
    def handle_message(self, topic: str, payload: Any, message):
        """
        统一的消息处理函数
        
        Args:
            topic: 消息主题
            payload: 消息内容（已解析）
            message: paho-mqtt的message对象
        """
        if self.logger:
            self.logger.debug(f"RECV: {topic}")
        
        # 处理 Thumbler 设备状态主题
        if topic.startswith("Thumbler/") and topic.endswith("/status"):
            if self.logger:
                self.logger.debug(f"RECV thumbler_status: {topic}")
        
        # 所有消息都转发到UI（mqtt_page 显示所有消息，thumbler_page 只接收 Thumbler 状态）
        self._forward_to_ui(topic, payload)

