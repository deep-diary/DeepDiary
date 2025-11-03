# 实现从rtsp://34.172.161.212:8554/mystream 拉流，并显示在UI上， 使用类来管理拉流和显示
# 支持视频和音频同步播放

import cv2
import numpy as np
from typing import Optional, Tuple
import logging
import threading
import queue
import time


class RtspPage:
    """
    视频流管理类（支持多种协议：RTSP、HLS、WebRTC 等）
    
    负责从 MediaMTX 服务器拉取视频流和音频流，并提供给 Gradio UI 显示和播放。
    优先使用浏览器原生支持的协议（HLS/WebRTC）以获得最佳音视频同步效果。
    """
    
    def __init__(
        self, 
        rtsp_url: str = "rtsp://34.172.161.212:8554/mystream", 
        logger: Optional[logging.Logger] = None,
        prefer_browser_native: bool = True
    ):
        """
        初始化视频流页面
        
        Args:
            rtsp_url: RTSP 流地址（将自动转换为其他协议 URL）
            logger: 日志记录器（可选）
            prefer_browser_native: 是否优先使用浏览器原生协议（HLS/WebRTC）
        """
        self.rtsp_url = rtsp_url
        self.logger = logger or logging.getLogger(__name__)
        self.prefer_browser_native = prefer_browser_native
        
        # 解析并生成各种协议 URL
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
        """解析 RTSP URL 并生成各种协议的 URL"""
        # 从 RTSP URL 中提取服务器地址和流名称
        # 例如: rtsp://34.172.161.212:8554/mystream
        if "rtsp://" in self.rtsp_url:
            # 解析 RTSP URL
            rtsp_parts = self.rtsp_url.replace("rtsp://", "").split("/")
            host_port = rtsp_parts[0]  # 34.172.161.212:8554
            stream_name = rtsp_parts[-1] if len(rtsp_parts) > 1 else "mystream"
            
            # 提取主机和端口
            if ":" in host_port:
                host, rtsp_port = host_port.split(":")
            else:
                host = host_port
                rtsp_port = "8554"
            
            # 生成 MediaMTX 的 Web 接口 URL
            # MediaMTX 默认 HTTP 端口是 8888
            self.web_base_url = f"http://{host}:8888"
            self.web_stream_url = f"{self.web_base_url}/{stream_name}"
            self.hls_url = f"{self.web_stream_url}/hls.m3u8"
            self.webrtc_url = f"{self.web_stream_url}/webrtc"
            
            self.logger.info(f"解析 URL - 主机: {host}, 流名称: {stream_name}")
            self.logger.info(f"HLS URL: {self.hls_url}")
            self.logger.info(f"WebRTC URL: {self.webrtc_url}")
        else:
            # 如果不是 RTSP URL，假设是 HTTP URL
            self.web_stream_url = self.rtsp_url
            self.hls_url = f"{self.rtsp_url}/hls.m3u8" if not self.rtsp_url.endswith("/") else f"{self.rtsp_url}hls.m3u8"
            self.webrtc_url = f"{self.rtsp_url}/webrtc" if not self.rtsp_url.endswith("/") else f"{self.rtsp_url}webrtc"
    
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
    
    def get_web_player_html(self, protocol: str = "direct") -> str:
        """
        生成浏览器原生播放器的 HTML 代码
        
        Args:
            protocol: 使用的协议 ('direct', 'hls', 'webrtc')
        
        Returns:
            HTML 代码字符串
        """
        if protocol == "hls":
            # 使用 HLS.js 播放 HLS 流（需要加载库）
            html = f"""
            <div style="width: 100%; max-width: 1280px; margin: 0 auto;">
                <video 
                    id="hls-video-{int(time.time())}" 
                    controls 
                    autoplay 
                    muted 
                    style="width: 100%; background: #000; min-height: 480px;"
                    playsinline
                >
                    您的浏览器不支持 HTML5 视频播放。
                </video>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
            <script>
                (function() {{
                    const videoId = 'hls-video-{int(time.time())}';
                    const video = document.getElementById(videoId);
                    const hlsUrl = '{self.hls_url}';
                    
                    if (!video) {{
                        console.error('找不到视频元素:', videoId);
                        return;
                    }}
                    
                    // 检查是否原生支持 HLS (Safari/iOS)
                    if (video.canPlayType('application/vnd.apple.mpegurl')) {{
                        video.src = hlsUrl;
                        video.play().catch(e => console.error('播放失败:', e));
                        console.log('✅ 使用原生 HLS 支持 (Safari)');
                    }} else if (typeof Hls !== 'undefined' && Hls.isSupported()) {{
                        // 使用 HLS.js 库（Chrome/Firefox/Edge）
                        const hls = new Hls({{
                            enableWorker: true,
                            lowLatencyMode: false
                        }});
                        hls.loadSource(hlsUrl);
                        hls.attachMedia(video);
                        hls.on(Hls.Events.MANIFEST_PARSED, function() {{
                            video.play().catch(e => console.error('播放失败:', e));
                            console.log('✅ 使用 HLS.js 库播放');
                        }});
                        hls.on(Hls.Events.ERROR, function(event, data) {{
                            console.error('HLS 错误:', data);
                            if (data.fatal) {{
                                // 致命错误，尝试回退到直接播放
                                console.warn('HLS 播放失败，回退到直接播放');
                                video.src = '{self.web_stream_url}/';
                                video.play().catch(e => console.error('回退播放失败:', e));
                            }}
                        }});
                    }} else {{
                        // 不支持 HLS，回退到直接播放
                        console.warn('浏览器不支持 HLS，使用直接播放');
                        video.src = '{self.web_stream_url}/';
                        video.play().catch(e => console.error('播放失败:', e));
                    }}
                    
                    video.addEventListener('error', function(e) {{
                        console.error('视频播放错误:', video.error);
                        // 错误时显示提示
                        if (video.error) {{
                            const errorMsg = '播放错误: ' + video.error.message;
                            video.parentElement.innerHTML = '<div style="padding: 20px; text-align: center; color: #f00;">' + errorMsg + '<br>请尝试使用"直接播放"模式</div>';
                        }}
                    }});
                }})();
            </script>
            """
        elif protocol == "webrtc":
            # WebRTC 使用 MediaMTX 的 WebRTC 播放器（通过 iframe 嵌入）
            # MediaMTX 的 WebRTC 播放器通常在 /webrtc 路径
            html = f"""
            <div style="width: 100%; max-width: 1280px; margin: 0 auto;">
                <iframe 
                    src="{self.webrtc_url}"
                    style="width: 100%; height: 720px; border: none; background: #000;"
                    allowfullscreen
                    allow="autoplay; encrypted-media"
                >
                    您的浏览器不支持 iframe 或 WebRTC。
                </iframe>
                <p style="text-align: center; color: #666; margin-top: 10px;">
                    ⚠️ WebRTC 需要浏览器支持，如果无法播放请使用"直接播放"模式
                </p>
            </div>
            """
        else:
            # 默认使用 MediaMTX 的直接播放（最简单可靠）
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
    
    def get_stream_urls(self) -> dict:
        """
        获取所有可用的流 URL
        
        Returns:
            包含各种协议 URL 的字典
        """
        return {
            "rtsp": self.rtsp_url,
            "web_direct": self.web_stream_url,  # MediaMTX 直接播放（推荐）
            "hls": self.hls_url,
            "webrtc": self.webrtc_url,
            "note": "推荐使用 web_direct 或 hls，它们在浏览器中支持音视频同步"
        }
    
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