# 实现从rtsp://35.192.64.247:8554/mystream 拉流，并显示在UI上， 使用类来管理拉流和显示
# 支持视频和音频同步播放

import cv2
import numpy as np
import gradio as gr
from typing import Optional
import threading
import queue
import time


class RtspPage:
    """
    视频流管理类
    
    负责从 MediaMTX 服务器拉取视频流和音频流，并提供给 Gradio UI 显示和播放。
    使用浏览器 iframe 嵌入 MediaMTX 播放器以获得最佳音视频同步效果。
    """
    
    def __init__(
        self, 
        rtsp_url: str = "rtsp://35.192.64.247:8554/mystream", 
        log_manager = None
    ):
        """
        初始化视频流页面
        
        Args:
            rtsp_url: RTSP 流地址（将自动转换为 HTTP URL）
            log_manager: LogManager 实例（必须）
        """
        if log_manager is None:
            raise ValueError("log_manager 必须提供")
        
        self.rtsp_url = rtsp_url
        self.log_manager = log_manager
        self.logger = log_manager.get_logger(__name__)
        
        # 解析并生成 Web URL
        self._parse_urls()
        
        # RTSP 连接（用于 OpenCV 帧提取）
        self.cap: Optional[cv2.VideoCapture] = None
        self.frame: Optional[np.ndarray] = None
        self.is_connected = False
        self._reconnect_count = 0
        self._max_reconnect = 5
        self._initialized = False
        
        # 音频相关（可选功能）
        self.audio_enabled = False
        self.audio_thread: Optional[threading.Thread] = None
        self.audio_queue: queue.Queue = queue.Queue(maxsize=10)
        self._audio_stop_flag = threading.Event()
        
        # 延迟初始化：不在 __init__ 中立即连接
        # 将在第一次调用 get_frame() 时再连接
    
    def _parse_urls(self):
        """解析 RTSP URL 并生成 Web URL（使用 HTTPS 代理避免混合内容问题）"""
        # 从 RTSP URL 中提取服务器地址和流名称
        # 例如: rtsp://35.192.64.247:8554/mystream
        if "rtsp://" in self.rtsp_url:
            # 解析 RTSP URL
            rtsp_parts = self.rtsp_url.replace("rtsp://", "").split("/")
            host_port = rtsp_parts[0]  # 35.192.64.247:8554
            stream_name = rtsp_parts[-1] if len(rtsp_parts) > 1 else "mystream"
            
            # 提取主机和端口
            if ":" in host_port:
                host, rtsp_port = host_port.split(":")
            else:
                host = host_port
                rtsp_port = "8554"
            
            # 使用 HTTPS 代理 URL（通过 Nginx 代理 MediaMTX 的 HTTP 服务）
            # 这样可以避免混合内容问题（HTTPS 页面加载 HTTP iframe）
            # Nginx 配置了 /mediamtx/ 路径来代理 MediaMTX 的 8888 端口
            self.web_base_url = f"https://www.deep-diary.com/mediamtx"
            self.web_stream_url = f"{self.web_base_url}/{stream_name}"
            
            self.logger.info(f"解析 URL - 主机: {host}, 流名称: {stream_name}")
            self.logger.info(f"Web 播放 URL (HTTPS 代理): {self.web_stream_url}")
            self.logger.info(f"原始 MediaMTX URL: http://{host}:8888/{stream_name}")
        else:
            # 如果不是 RTSP URL，检查是否是 HTTP URL，如果是则转换为 HTTPS 代理
            if self.rtsp_url.startswith("http://"):
                # 提取流名称
                url_parts = self.rtsp_url.rstrip("/").split("/")
                stream_name = url_parts[-1] if url_parts else "mystream"
                self.web_stream_url = f"https://www.deep-diary.com/mediamtx/{stream_name}"
                self.logger.info(f"HTTP URL 已转换为 HTTPS 代理: {self.web_stream_url}")
            else:
                # 假设已经是 HTTPS URL 或相对路径
                self.web_stream_url = self.rtsp_url.rstrip("/")
    
    def _init_capture(self) -> bool:
        """
        初始化视频捕获对象
        
        Returns:
            是否成功初始化
        """
        try:
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass  # 忽略释放时的错误
            
            self.logger.info(f"正在连接 RTSP 流: {self.rtsp_url}")
            
            # 尝试创建 VideoCapture 对象，优先使用 TCP 传输（更可靠）
            rtsp_urls = []
            
            # 1. 尝试 TCP 传输（最可靠）
            if '?' not in self.rtsp_url:
                rtsp_urls.append(f"{self.rtsp_url}?tcp")
            
            # 2. 尝试 UDP 传输
            if '?' not in self.rtsp_url:
                rtsp_urls.append(f"{self.rtsp_url}?udp")
            
            # 3. 原始 URL
            rtsp_urls.append(self.rtsp_url)
            
            last_error = None
            for rtsp_url in rtsp_urls:
                try:
                    self.cap = cv2.VideoCapture(rtsp_url, cv2.CAP_FFMPEG)
                    
                    # 设置缓冲区大小，减少延迟（如果支持）
                    try:
                        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    except Exception:
                        pass  # 某些后端可能不支持此属性
                    
                    # 设置读取超时（如果支持）
                    try:
                        self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)  # 5秒超时
                        self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)  # 5秒读取超时
                    except Exception:
                        pass
                    
                    # 测试连接
                    if self.cap.isOpened():
                        # 尝试读取一帧来验证连接
                        ret, test_frame = self.cap.read()
                        if ret and test_frame is not None:
                            self.is_connected = True
                            self._reconnect_count = 0
                            transport = "TCP" if "?tcp" in rtsp_url else ("UDP" if "?udp" in rtsp_url else "默认")
                            self.logger.info(f"RTSP 流连接成功 (传输方式: {transport})")
                            return True
                        else:
                            self.cap.release()
                            self.cap = None
                except Exception as e:
                    last_error = e
                    if self.cap is not None:
                        try:
                            self.cap.release()
                        except Exception:
                            pass
                        self.cap = None
                    continue
            
            # 所有方式都失败
            self.is_connected = False
            error_msg = str(last_error) if last_error else "未知错误"
            self.logger.warning(f"RTSP 流连接失败: {error_msg}")
            return False
                
        except Exception as e:
            self.is_connected = False
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
                self.cap = None
            self.logger.error(f"初始化 RTSP 捕获时出错: {e}", exc_info=True)
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        获取当前视频帧
        
        Returns:
            当前帧（RGB格式），如果获取失败返回 None
        """
        # 延迟初始化：第一次调用时才尝试连接
        if not self._initialized:
            self._initialized = True
            self._init_capture()
        
        # 如果未连接，尝试重连
        if not self.is_connected or self.cap is None:
            if self._reconnect_count < self._max_reconnect:
                self._reconnect_count += 1
                self.logger.info(f"尝试重连 RTSP 流 ({self._reconnect_count}/{self._max_reconnect})")
                if not self._init_capture():
                    return None
            else:
                return None
        
        try:
            ret, frame = self.cap.read()
            
            if not ret or frame is None:
                # 读取失败，标记为断开连接
                self.is_connected = False
                self.logger.warning("读取 RTSP 帧失败")
                return None
            
            # 将 BGR 转换为 RGB（OpenCV 默认是 BGR，Gradio 需要 RGB）
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            self.frame = frame_rgb
            return frame_rgb
            
        except Exception as e:
            self.logger.error(f"获取 RTSP 帧时出错: {e}")
            self.is_connected = False
            return None
    
    def _get_web_player_html(self) -> str:
        """
        生成浏览器播放器的 HTML 代码（使用 iframe 嵌入 MediaMTX 播放器）
        
        Returns:
            HTML 代码字符串
        """
        html = f"""
        <div style="width: 100%; max-width: 1280px; margin: 0 auto;">
            <iframe 
                src="{self.web_stream_url}/"
                style="width: 100%; height: 720px; border: none; background: #000;"
                allowfullscreen
                allow="autoplay; encrypted-media"
            ></iframe>
        </div>
        """
        return html
    
    def release(self) -> None:
        """释放视频捕获资源"""
        # 停止音频线程
        if self.audio_thread is not None and self.audio_thread.is_alive():
            self._audio_stop_flag.set()
            self.audio_thread.join(timeout=2.0)
            self.audio_thread = None
        
        # 释放视频捕获
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
            self.is_connected = False
            self.logger.info("RTSP 流已释放")
    
    def build(self):
        """
        构建页面 UI 组件
        
        Returns:
            构建好的 Gradio 组件
        """
        with gr.Column():
            gr.Markdown("### 🌐 浏览器播放器（支持音视频同步）")
            
            # 使用 HTML 组件嵌入 MediaMTX 的 Web 播放器
            web_player = gr.HTML(
                value=self._get_web_player_html(),
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
            
            # 流信息显示
            stream_info = gr.Markdown(
                value=f"""
                **流地址信息**:
                - 🎥 Web 播放: [{self.web_stream_url}]({self.web_stream_url})
                - 🔴 RTSP: `{self.rtsp_url}`
                
                **说明**: 浏览器播放器支持完整的音视频同步。OpenCV 帧提取用于 AI 分析等场景。
                """
            )
            
            gr.Markdown("### ⚙️ 流配置")
            
            # 创建状态显示（需要在按钮点击之前定义）
            rtsp_status = gr.Textbox(
                label="连接状态",
                value="浏览器播放器已就绪",
                interactive=False
            )
            
            rtsp_url_input = gr.Textbox(
                label="流地址（RTSP 或 HTTP）",
                value=self.rtsp_url,
                placeholder="例如: rtsp://35.192.64.247:8554/mystream 或 http://35.192.64.247:8888/mystream",
                info="支持 RTSP 和 HTTP URL，会自动解析为 Web 播放 URL"
            )
            
            # 保存 self 引用以便在闭包中使用
            rtsp_page_instance = self
            
            def update_stream_url(url: str):
                """更新流地址"""
                try:
                    rtsp_page_instance.release()
                    # 重新初始化
                    rtsp_page_instance.rtsp_url = url
                    rtsp_page_instance._parse_urls()
                    
                    # 更新播放器 HTML
                    player_html = rtsp_page_instance._get_web_player_html()
                    
                    # 更新流信息
                    new_stream_info = f"""
                    **流地址信息**:
                    - 🎥 Web 播放: [{rtsp_page_instance.web_stream_url}]({rtsp_page_instance.web_stream_url})
                    - 🔴 RTSP: `{rtsp_page_instance.rtsp_url}`
                    
                    **说明**: 浏览器播放器支持完整的音视频同步。OpenCV 帧提取用于 AI 分析等场景。
                    """
                    
                    return (
                        gr.update(value=player_html),
                        gr.update(value="流地址已更新"),
                        gr.update(value=new_stream_info)
                    )
                except Exception as e:
                    rtsp_page_instance.logger.error(f"更新流地址失败: {e}")
                    return (
                        gr.update(),
                        gr.update(value=f"更新失败: {e}"),
                        gr.update()
                    )
            
            update_btn = gr.Button("更新流地址", variant="primary")
            update_btn.click(
                fn=update_stream_url,
                inputs=rtsp_url_input,
                outputs=[web_player, rtsp_status, stream_info]
            )
            
            # OpenCV 帧提取定时器（可选功能，用于图像处理）
            rtsp_timer = gr.Timer(0.1, active=False)  # 默认不启用，按需开启
            
            def toggle_opencv(enabled: bool):
                """切换 OpenCV 帧提取的启用状态"""
                try:
                    if enabled:
                        # 启用 OpenCV 帧提取
                        # 初始化连接（延迟初始化）
                        rtsp_page_instance._initialized = False
                        rtsp_page_instance.logger.info("OpenCV 帧提取已启用")
                        return (
                            gr.update(visible=True),  # 显示图像组件
                            gr.update(visible=True, value="正在连接..."),  # 显示状态
                            gr.update(active=True),  # 启用定时器
                            gr.update(value=True)  # 保持复选框选中
                        )
                    else:
                        # 禁用 OpenCV 帧提取
                        rtsp_page_instance.release()
                        rtsp_page_instance.logger.info("OpenCV 帧提取已禁用")
                        return (
                            gr.update(visible=False),  # 隐藏图像组件
                            gr.update(visible=False, value="未启用"),  # 隐藏状态
                            gr.update(active=False),  # 禁用定时器
                            gr.update(value=False)  # 取消复选框选中
                        )
                except Exception as e:
                    rtsp_page_instance.logger.error(f"切换 OpenCV 状态失败: {e}")
                    return (
                        gr.update(),
                        gr.update(value=f"错误: {e}"),
                        gr.update(active=False),
                        gr.update(value=False)
                    )
            
            def update_rtsp_frame():
                """定时更新 OpenCV 视频帧（用于图像处理等场景）"""
                try:
                    frame = rtsp_page_instance.get_frame()
                    if frame is not None:
                        status = f"✅ OpenCV 已连接 - {rtsp_page_instance.rtsp_url}"
                        return frame, status
                    else:
                        return None, "⏳ OpenCV 正在连接中..."
                except Exception as e:
                    rtsp_page_instance.logger.error(f"更新 OpenCV 帧时出错: {e}")
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
            
            self.logger.info("RTSP 页面已构建，浏览器播放器已就绪")