import gradio as gr
from typing import Optional, Any
from datetime import datetime
from deepweb.data_management.log_manager import LogManager


class UIManager:
    """
    UI 管理类
    
    负责构建与启动 Gradio 界面，作为 DeepWeb 的前端展示层。
    
    职责：
    - 构建 Gradio 用户界面
    - 管理 UI 组件和交互逻辑
    - 启动 Gradio Web 服务
    
    用法示例：
        ui = UIManager(log_manager=log_manager, coordinator=coordinator)
        ui.launch()  # launch() 会自动调用 build()
    """

    def __init__(
        self,
        log_manager: LogManager,  # 必须传入有效的 LogManager（主入口保证）
        coordinator: Optional[object] = None,
        host: str = "0.0.0.0",
        port: int = 7860,
        share: bool = False,
    ) -> None:
        """
        初始化 UI 管理器
        
        Args:
            log_manager: 日志管理器实例（必须传入有效的 LogManager）
            coordinator: 核心协调器实例，用于处理业务逻辑请求（可选）
            host: Web 服务器监听地址，默认为 "0.0.0.0"（监听所有网络接口）
            port: Web 服务器端口，默认为 7860
            share: 是否创建公共链接，默认为 False
        """
        self.coordinator = coordinator
        self.log_manager = log_manager
        self.host = host
        self.port = port
        self.share = share

        # 主入口保证传入有效的 LogManager，直接获取 logger
        self.logger = self.log_manager.get_logger(__name__)

        # Gradio Blocks 对象（惰性构建）
        self._demo: Optional[gr.Blocks] = None

        # 子页面实例引用（用于消息桥接）
        self._mqtt_page = None
        self._rtsp_page = None

        # 若由外部传入 Coordinator，可在外部调用 coordinator.attach_ui_manager(self)

    def get_time(self):
        # 返回带毫秒的时间字符串
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:23]

    def update_time(self):
    # 仅更新 Textbox 的 value
        self.logger.warning(f"<<<<<<<<<Testing:UI_UPDATE_TIME: {self.get_time()}")
        return gr.update(value=self.get_time())

    def build(self) -> None:
        """s
        构建 Gradio UI（惰性构建）
        
        如果 UI 已经构建过，直接返回，避免重复构建。
        """
        if self._demo is not None:
            return

        with gr.Blocks() as demo:
            gr.Markdown("# DeepWeb UI")

            with gr.Tabs():
                from deepweb.ui.pages.mqtt_page import MqttPage
                with gr.TabItem("MQTT 通讯"):
                    mqtt_manager = getattr(self.coordinator, "mqtt_manager", None) if self.coordinator else None
                    self._mqtt_page = MqttPage(mqtt_manager, logger=self.logger)
                    mqtt_json = self._mqtt_page.build()
                    # 保存引用，便于回退使用 Blocks.load 方案
                    self._mqtt_json = mqtt_json  # type: ignore[attr-defined]
                
                from deepweb.ui.pages.rtsp_page import RtspPage
                with gr.TabItem("视频流"):
                    # 创建视频流页面实例
                    self._rtsp_page = RtspPage(logger=self.logger, prefer_browser_native=True)
                    
                    # 获取流 URL 信息
                    stream_urls = self._rtsp_page.get_stream_urls()
                    
                    gr.Markdown("### 🌐 浏览器原生播放器（推荐 - 支持音视频同步）")
                    
                    # 使用 HTML 组件嵌入 MediaMTX 的 Web 播放器（最简单可靠）
                    web_player = gr.HTML(
                        value=self._rtsp_page.get_web_player_html("direct"),
                        label="视频流播放器"
                    )
                    
                    gr.Markdown("---")
                    gr.Markdown("### 📹 OpenCV 帧提取模式（用于 AI 图像处理）")
                    
                    # OpenCV 帧提取开关
                    opencv_enable_checkbox = gr.Checkbox(
                        label="启用 OpenCV 帧提取",
                        value=False,
                        info="开启后可以提取视频帧用于 AI 分析、图像处理等场景（会增加 CPU 使用）"
                    )
                    
                    # OpenCV 帧提取模式（用于图像处理等场景）
                    rtsp_video = gr.Image(
                        label="OpenCV 视频帧",
                        type="numpy",
                        interactive=False,
                        visible=False  # 默认隐藏，开启后显示
                    )
                    
                    # OpenCV 状态显示
                    opencv_status = gr.Textbox(
                        label="OpenCV 状态",
                        value="未启用",
                        interactive=False,
                        visible=False
                    )
                    
                    # 创建状态显示
                    rtsp_status = gr.Textbox(
                        label="连接状态",
                        value="浏览器播放器已就绪",
                        interactive=False
                    )
                    
                    # 流信息显示
                    stream_info = gr.Markdown(
                        value=f"""
                        **可用流地址**:
                        - 🎥 直接播放: [{stream_urls['web_direct']}]({stream_urls['web_direct']})
                        - 📡 HLS: `{stream_urls['hls']}`
                        - 🔴 RTSP: `{stream_urls['rtsp']}`
                        - 🌐 WebRTC: `{stream_urls['webrtc']}`
                        
                        **推荐**: 使用浏览器原生播放器（上方），它支持完整的音视频同步。
                        """
                    )
                    
                    gr.Markdown("### ⚙️ 流配置")
                    
                    with gr.Row():
                        rtsp_url_input = gr.Textbox(
                            label="流地址（RTSP 或 HTTP）",
                            value=self._rtsp_page.rtsp_url,
                            placeholder="例如: rtsp://34.172.161.212:8554/mystream 或 http://34.172.161.212:8888/mystream",
                            info="支持 RTSP 和 HTTP URL，会自动解析为多种协议",
                            scale=3
                        )
                        protocol_select = gr.Dropdown(
                            choices=["直接播放（iframe）", "HLS", "WebRTC"],
                            value="直接播放（iframe）",
                            label="播放协议",
                            info="推荐使用直接播放",
                            scale=1
                        )
                    
                    def update_stream_url(url: str, protocol: str):
                        """更新流地址和协议"""
                        try:
                            if self._rtsp_page:
                                self._rtsp_page.release()
                                self._rtsp_page = RtspPage(rtsp_url=url, logger=self.logger)
                                
                                # 根据选择的协议生成播放器 HTML
                                protocol_map = {
                                    "直接播放（iframe）": "direct",
                                    "HLS": "hls",
                                    "WebRTC": "webrtc"
                                }
                                protocol_key = protocol_map.get(protocol, "direct")
                                player_html = self._rtsp_page.get_web_player_html(protocol_key)
                                
                                # 更新流信息
                                new_stream_urls = self._rtsp_page.get_stream_urls()
                                new_stream_info = f"""
                                **可用流地址**:
                                - 🎥 直接播放: [{new_stream_urls['web_direct']}]({new_stream_urls['web_direct']})
                                - 📡 HLS: `{new_stream_urls['hls']}`
                                - 🔴 RTSP: `{new_stream_urls['rtsp']}`
                                - 🌐 WebRTC: `{new_stream_urls['webrtc']}`
                                
                                **推荐**: 使用浏览器原生播放器，它支持完整的音视频同步。
                                """
                                
                                return (
                                    gr.update(value=player_html),
                                    gr.update(value="流地址已更新"),
                                    gr.update(value=new_stream_info)
                                )
                            return (
                                gr.update(),
                                gr.update(value="流页面未初始化"),
                                gr.update()
                            )
                        except Exception as e:
                            self.logger.error(f"更新流地址失败: {e}")
                            return (
                                gr.update(),
                                gr.update(value=f"更新失败: {e}"),
                                gr.update()
                            )
                    
                    update_btn = gr.Button("更新流地址", variant="primary")
                    update_btn.click(
                        fn=update_stream_url,
                        inputs=[rtsp_url_input, protocol_select],
                        outputs=[web_player, rtsp_status, stream_info]
                    )
                    
                    # OpenCV 帧提取定时器（可选功能，用于图像处理）
                    rtsp_timer = gr.Timer(0.1, active=False)  # 默认不启用，按需开启
                    
                    def toggle_opencv(enabled: bool):
                        """切换 OpenCV 帧提取的启用状态"""
                        try:
                            if enabled:
                                # 启用 OpenCV 帧提取
                                if self._rtsp_page:
                                    # 初始化连接（延迟初始化）
                                    self._rtsp_page._initialized = False
                                    self.logger.info("OpenCV 帧提取已启用")
                                    return (
                                        gr.update(visible=True),  # 显示图像组件
                                        gr.update(visible=True, value="正在连接..."),  # 显示状态
                                        gr.update(active=True),  # 启用定时器
                                        gr.update(value="已启用")
                                    )
                                else:
                                    return (
                                        gr.update(visible=True),
                                        gr.update(visible=True, value="流页面未初始化"),
                                        gr.update(active=False),
                                        gr.update(value="已启用（但页面未初始化）")
                                    )
                            else:
                                # 禁用 OpenCV 帧提取
                                if self._rtsp_page:
                                    self._rtsp_page.release()
                                    self.logger.info("OpenCV 帧提取已禁用")
                                return (
                                    gr.update(visible=False),  # 隐藏图像组件
                                    gr.update(visible=False, value="未启用"),  # 隐藏状态
                                    gr.update(active=False),  # 禁用定时器
                                    gr.update(value="未启用")
                                )
                        except Exception as e:
                            self.logger.error(f"切换 OpenCV 状态失败: {e}")
                            return (
                                gr.update(),
                                gr.update(value=f"错误: {e}"),
                                gr.update(active=False),
                                gr.update(value="未启用")
                            )
                    
                    def update_rtsp_frame():
                        """定时更新 OpenCV 视频帧（用于图像处理等场景）"""
                        try:
                            if self._rtsp_page:
                                frame = self._rtsp_page.get_frame()
                                if frame is not None:
                                    status = f"✅ OpenCV 已连接 - {self._rtsp_page.rtsp_url}"
                                    return frame, status
                                else:
                                    return None, "⏳ OpenCV 正在连接中..."
                            return None, "❌ 流页面未初始化"
                        except Exception as e:
                            self.logger.error(f"更新 OpenCV 帧时出错: {e}")
                            return None, f"❌ 错误: {e}"
                    
                    # 绑定 OpenCV 开关事件
                    opencv_enable_checkbox.change(
                        fn=toggle_opencv,
                        inputs=opencv_enable_checkbox,
                        outputs=[rtsp_video, opencv_status, rtsp_timer, opencv_enable_checkbox]
                    )
                    
                    # 使用定时器自动更新 OpenCV 帧（每100ms更新一次，降低 CPU 使用）
                    rtsp_timer.tick(
                        fn=update_rtsp_frame,
                        inputs=None,
                        outputs=[rtsp_video, opencv_status]
                    )
                    
                    self.logger.info("视频流页面已构建，浏览器播放器已就绪")


        self._demo = demo
        self.logger.info("UIManager: UI 构建完成。")
       

    # ---- MQTT <-> UI 桥接 ----
    def push_mqtt_message(self, topic: str, payload: Any) -> None:
        """
        被设备消息处理器调用，将消息推送到 UI 队列。
        当前实现：直接转发给 MQTT 子页面的本地队列。
        """
        self.logger.warning(f"<<<<STP3:UI_QUEUE: topic={topic} payload={payload}")
        try:
            if not self._mqtt_page:
                self.logger.warning(f"<<<<STP3:UI_QUEUE_ERROR: _mqtt_page not found")
                return
            self._mqtt_page.push_mqtt_message(topic, payload)  # type: ignore[attr-defined]
        except Exception as e:
            self.logger.warning(f"<<<<STP3:UI_QUEUE_ERROR: {e}")

    # 页面刷新逻辑由各页面自行注册（如 gr.Timer.tick）

    # 已简化：不再暴露 demo 属性；请使用 launch() 启动（内部会惰性 build）

    def launch(self) -> None:
        """
        启动 Gradio Web 服务
        
        如果 UI 还未构建，会自动调用 build() 进行构建。
        此方法会阻塞当前线程，直到服务停止。
        """
        if self._demo is None:
            self.build()
        self.logger.info(
            f"UIManager: 启动 UI，host={self.host}, port={self.port}, share={self.share}"
        )
        self._demo.launch(server_name=self.host, server_port=self.port, share=self.share)  # type: ignore[union-attr]

    def get_app(self) -> gr.Blocks:
        """
        返回构建好的 Blocks 对象
        
        供外部集成到更复杂的容器中使用（例如多个 UI 组件组合）。
        
        Returns:
            构建好的 Gradio Blocks 对象
        """
        if self._demo is None:
            self.build()
        return self._demo  # type: ignore[return-value]

    
