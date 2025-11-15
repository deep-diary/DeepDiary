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
        host: str = "localhost",
        port: int = 7860,  # 修改默认端口，避免冲突
        share: bool = False,
    ) -> None:
        """
        初始化 UI 管理器
        
        Args:
            log_manager: 日志管理器实例（必须传入有效的 LogManager）
            coordinator: 核心协调器实例，用于处理业务逻辑请求（可选）
            host: Web 服务器监听地址，默认为 "localhost"（监听本地网络接口）
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
        self._thumbler_page = None

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
                    # 创建视频流页面实例并构建 UI
                    self._rtsp_page = RtspPage(log_manager=self.log_manager)
                    self._rtsp_page.build()
                
                from deepweb.ui.pages.thumbler_page import ThumblerPage
                with gr.TabItem("不倒翁"):
                    # 创建不倒翁页面实例并构建 UI
                    mqtt_manager = getattr(self.coordinator, "mqtt_manager", None) if self.coordinator else None
                    self._thumbler_page = ThumblerPage(
                        device_id="ATK-DNESP32S3-9888e000ae28",
                        host="35.192.64.247",
                        mqtt_manager=mqtt_manager,
                        log_manager=self.log_manager
                    )
                    self._thumbler_page.build()


        self._demo = demo
        self.logger.info("UIManager: UI 构建完成。")
       
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
        try:
            # 优化 Gradio 启动配置
            # 设置 inbrowser=False 以便正确处理中断信号
            # 添加 server_name="0.0.0.0" 以确保可以访问
            self._demo.launch(
                server_name="0.0.0.0" if self.host == "localhost" else self.host,
                server_port=self.port,
                share=self.share,
                show_error=True,  # 显示错误以便调试
                inbrowser=False,  # 不自动打开浏览器
            )  # type: ignore[union-attr]
        except KeyboardInterrupt:
            self.logger.info("收到键盘中断信号，正在关闭 UI...")
            raise
        except Exception as e:
            self.logger.error(f"启动 UI 时出错: {e}")
            raise

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

    
