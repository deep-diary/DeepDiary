import gradio as gr
import asyncio
import websockets
import json
import threading
from typing import List, Dict, Any, Optional
from queue import Queue, Empty
import time
import base64
import tempfile
import os
from pathlib import Path

# 导入 Immich client
try:
    from deepweb.services.cloud_communication.immich_client import ImmichClient
except ImportError as e:
    ImmichClient = None
    import logging
    logging.getLogger(__name__).warning(f"无法导入 ImmichClient: {e}")


class ChatPage:
    """
    聊天页面 - 连接到 xiaozhi-server 的 WebSocket 客户端

    功能：
    1. WebSocket 连接到 xiaozhi-server
    2. 实时显示聊天记录（用户消息、AI回复、视觉识别结果）
    3. 左右布局：左侧聊天界面，右侧记忆显示区
    4. 支持设备ID和客户端ID配置
    5. 消息转发机制，从 ESP32 设备到网页
    """

    def __init__(self, logger, config_manager=None):
        """
        初始化聊天页面

        Args:
            logger: 日志记录器
            config_manager: 配置管理器（可选，用于获取 Immich 配置）
        """
        self.logger = logger
        self.config_manager = config_manager

        # WebSocket 连接相关
        self.websocket_url = "ws://localhost:8000/xiaozhi/v1/"
        self.websocket = None
        self.is_connected = False

        # 设备配置
        self.device_id = "web_chat_client"
        self.client_id = "gradio-client"

        # 消息队列和缓存
        self.message_queue = Queue(maxsize=1000)
        self.chat_history: List[Dict[str, str]] = []
        self.memory_markdown = "# 记忆显示区\n\n待开发功能..."

        # WebSocket 监听线程
        self.ws_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()

        # 界面更新队列
        self.ui_update_queue = Queue(maxsize=100)

        # LLM流式响应合并：存储当前正在接收的消息
        self.current_llm_message: Dict[str, Any] = {}  # {session_id: {"role": "assistant", "content": "", "index": -1}}

        # 临时文件管理：存储 base64 图片转换的临时文件
        self.temp_dir = tempfile.mkdtemp(prefix="chat_images_")
        self.temp_files: List[str] = []  # 存储临时文件路径，用于后续清理

        # Immich 客户端（用于从 Immich 服务器获取图片）
        self.immich_client: Optional[ImmichClient] = None
        self._init_immich_client()

    def build(self):
        """
        构建 Gradio UI 界面
        """
        with gr.Column() as chat_interface:
            # 标题
            gr.Markdown("# 🤖 小智智能聊天助手")

            # 连接配置区域
            with gr.Accordion("连接配置", open=False):
                with gr.Row():
                    device_id_input = gr.Textbox(
                        label="设备ID (Device ID)",
                        value=self.device_id,
                        placeholder="web_chat_client",
                        interactive=True
                    )
                    client_id_input = gr.Textbox(
                        label="客户端ID (Client ID)",
                        value=self.client_id,
                        placeholder="gradio-client",
                        interactive=True
                    )
                    websocket_url_input = gr.Textbox(
                        label="WebSocket URL",
                        value=self.websocket_url,
                        placeholder="ws://localhost:8000/xiaozhi/v1/",
                        interactive=True
                    )

                with gr.Row():
                    connect_btn = gr.Button("🔗 连接", variant="primary")
                    disconnect_btn = gr.Button("❌ 断开连接", variant="secondary")
                    status_text = gr.Textbox(
                        label="连接状态",
                        value="未连接",
                        interactive=False
                    )

            # 主要聊天区域 - 左右布局
            with gr.Row():
                # 左侧：聊天界面
                with gr.Column(scale=2):
                    gr.Markdown("### 💬 聊天记录")

                    # 聊天历史显示
                    chatbot = gr.Chatbot(
                        label="对话历史",
                        value=self.chat_history,
                        height=500,
                        show_label=False,
                        bubble_full_width=False,
                        type="messages",  # 使用新的消息格式
                        avatar_images=(None, "🤖")  # 用户头像，AI头像
                    )

                    # 消息输入区域
                    with gr.Row():
                        msg_input = gr.Textbox(
                            label="输入消息",
                            placeholder="输入消息与小智对话...",
                            scale=4,
                            interactive=True
                        )
                        send_btn = gr.Button("发送", scale=1, variant="primary")

                    # 清除聊天记录按钮
                    clear_btn = gr.Button("🗑️ 清除聊天记录", size="sm")

                # 右侧：记忆显示区
                with gr.Column(scale=1):
                    gr.Markdown("### 📚 记忆显示区")

                    memory_display = gr.Markdown(
                        value=self.memory_markdown,
                        label="记忆内容",
                        height=500,
                        show_label=False
                    )

                    # 记忆操作按钮
                    with gr.Row():
                        refresh_memory_btn = gr.Button("🔄 刷新记忆", size="sm")
                        clear_memory_btn = gr.Button("🗑️ 清除记忆", size="sm")

            # 事件绑定

            # 连接配置相关
            connect_btn.click(
                fn=self.connect_websocket,
                inputs=[device_id_input, client_id_input, websocket_url_input],
                outputs=[status_text]
            ).then(
                fn=lambda: gr.update(interactive=False),
                inputs=[],
                outputs=[connect_btn]
            ).then(
                fn=lambda: gr.update(interactive=True),
                inputs=[],
                outputs=[disconnect_btn]
            )

            disconnect_btn.click(
                fn=self.disconnect_websocket,
                inputs=[],
                outputs=[status_text]
            ).then(
                fn=lambda: gr.update(interactive=True),
                inputs=[],
                outputs=[connect_btn]
            ).then(
                fn=lambda: gr.update(interactive=False),
                inputs=[],
                outputs=[disconnect_btn]
            )

            # 消息发送相关
            send_btn.click(
                fn=self.send_message,
                inputs=[msg_input],
                outputs=[]
            ).then(
                fn=lambda: "",  # 清空输入框
                inputs=[],
                outputs=[msg_input]
            )

            msg_input.submit(
                fn=self.send_message,
                inputs=[msg_input],
                outputs=[]
            ).then(
                fn=lambda: "",  # 清空输入框
                inputs=[],
                outputs=[msg_input]
            )

            # 聊天记录操作
            clear_btn.click(
                fn=self.clear_chat_history,
                inputs=[],
                outputs=[chatbot]
            )

            # 记忆操作
            refresh_memory_btn.click(
                fn=self.refresh_memory,
                inputs=[],
                outputs=[memory_display]
            )

            clear_memory_btn.click(
                fn=self.clear_memory,
                inputs=[],
                outputs=[memory_display]
            )

            # 定时更新聊天记录和记忆显示（每秒更新一次）
            timer = gr.Timer(1.0)
            timer.tick(
                fn=self.update_ui,
                inputs=[],
                outputs=[chatbot, memory_display, status_text]
            )

        return chat_interface

    def connect_websocket(self, device_id: str, client_id: str, websocket_url: str) -> str:
        """
        连接到 WebSocket 服务器

        Args:
            device_id: 设备ID
            client_id: 客户端ID
            websocket_url: WebSocket URL

        Returns:
            连接状态消息
        """
        try:
            # 更新配置
            self.device_id = device_id
            self.client_id = client_id
            self.websocket_url = websocket_url

            # 断开现有连接
            if self.is_connected:
                self.disconnect_websocket()

            # 启动 WebSocket 监听线程
            self.stop_event.clear()
            self.ws_thread = threading.Thread(target=self._websocket_listener, daemon=True)
            self.ws_thread.start()

            self.logger.info(f"正在连接到 WebSocket: {websocket_url}")
            return "正在连接..."

        except Exception as e:
            self.logger.error(f"连接 WebSocket 时出错: {e}")
            return f"连接失败: {str(e)}"

    def disconnect_websocket(self) -> str:
        """
        断开 WebSocket 连接

        Returns:
            断开状态消息
        """
        try:
            self.stop_event.set()
            self.is_connected = False

            if self.ws_thread and self.ws_thread.is_alive():
                self.ws_thread.join(timeout=2.0)

            self.logger.info("WebSocket 连接已断开")
            return "已断开连接"

        except Exception as e:
            self.logger.error(f"断开 WebSocket 时出错: {e}")
            return f"断开失败: {str(e)}"

    def _websocket_listener(self):
        """
        WebSocket 监听线程
        """
        while not self.stop_event.is_set():
            try:
                # 构建 WebSocket URL，包含查询参数
                ws_url = f"{self.websocket_url}?device-id={self.device_id}&client-id={self.client_id}"

                self.logger.info(f"尝试连接 WebSocket: {ws_url}")

                async def listen():
                    try:
                        async with websockets.connect(ws_url) as websocket:
                            self.websocket = websocket
                            self.is_connected = True
                            self.ui_update_queue.put({"type": "status", "status": "已连接"})

                            self.logger.info("WebSocket 连接成功")

                            while not self.stop_event.is_set():
                                try:
                                    # 设置超时时间
                                    message = await asyncio.wait_for(
                                        websocket.recv(),
                                        timeout=1.0
                                    )

                                    # 处理接收到的消息
                                    self._handle_websocket_message(message)

                                except asyncio.TimeoutError:
                                    # 超时，继续监听
                                    continue
                                except websockets.exceptions.ConnectionClosed:
                                    self.logger.warning("WebSocket 连接被关闭")
                                    break

                    except Exception as e:
                        self.logger.error(f"WebSocket 连接出错: {e}")
                        self.ui_update_queue.put({"type": "status", "status": f"连接失败: {str(e)}"})
                        await asyncio.sleep(5)  # 等待5秒后重试

                # 运行异步监听
                asyncio.run(listen())

            except Exception as e:
                self.logger.error(f"WebSocket 监听线程出错: {e}")
                if not self.stop_event.is_set():
                    time.sleep(5)  # 等待5秒后重试

            finally:
                self.is_connected = False
                self.websocket = None

    def _init_immich_client(self):
        """初始化 Immich 客户端"""
        if ImmichClient is None:
            self.logger.warning("ImmichClient 未导入，图片获取功能将被禁用")
            return
        
        try:
            # 从 config_manager 获取 Immich 配置
            if self.config_manager:
                # 使用 get_config() 获取完整配置，然后获取 immich 部分
                all_config = self.config_manager.get_config()
                immich_config = all_config.get("immich", {})
                self.logger.info(f"从 config_manager 获取 Immich 配置: api_url={immich_config.get('api_url')}, "
                               f"has_api_key={bool(immich_config.get('api_key'))}, "
                               f"has_email={bool(immich_config.get('email'))}")
            else:
                # 如果没有 config_manager，尝试从环境变量获取（降级方案）
                import os
                immich_config = {
                    "api_url": os.getenv("IMMICH_API_URL", "http://127.0.0.1:2283/api"),
                    "api_key": os.getenv("IMMICH_API_KEY", ""),
                    "email": os.getenv("IMMICH_EMAIL", ""),
                    "password": os.getenv("IMMICH_PASSWORD", ""),
                    "timeout": int(os.getenv("IMMICH_TIMEOUT", "30"))
                }
                self.logger.info(f"从环境变量获取 Immich 配置: api_url={immich_config.get('api_url')}")
            
            # 如果配置了 API key 或 email+password，创建客户端
            has_api_key = bool(immich_config.get("api_key"))
            has_email_password = bool(immich_config.get("email") and immich_config.get("password"))
            
            if has_api_key or has_email_password:
                self.logger.info(f"创建 Immich 客户端: api_url={immich_config.get('api_url')}, "
                              f"auth_method={'api_key' if has_api_key else 'email+password'}")
                self.immich_client = ImmichClient(immich_config)
                if self.immich_client.enabled:
                    self.logger.info(f"Immich 客户端初始化成功: api_url={self.immich_client.api_url}")
                else:
                    self.logger.warning("Immich 客户端初始化失败，将使用降级方案")
                    self.immich_client = None
            else:
                self.logger.info("Immich 配置未设置（缺少 api_key 或 email+password），将使用降级方案（base64 图片）")
        except Exception as e:
            self.logger.error(f"初始化 Immich 客户端失败: {e}")
            self.immich_client = None

    async def _download_immich_image(self, asset_id: str) -> Optional[str]:
        """
        从 Immich 服务器下载图片
        
        Args:
            asset_id: Immich 资产 ID
            
        Returns:
            下载的图片文件路径，如果下载失败返回 None
        """
        self.logger.info(f"开始下载 Immich 图片: asset_id={asset_id}")
        
        if not self.immich_client:
            self.logger.warning("Immich client 未初始化")
            return None
        
        if not self.immich_client.enabled:
            self.logger.warning("Immich client 未启用")
            return None
        
        try:
            self.logger.info(f"调用 Immich client.download_asset({asset_id})")
            # 尝试下载图片
            image_path = await self.immich_client.download_asset(asset_id)
            
            if image_path:
                # 检查文件是否存在
                if os.path.exists(image_path):
                    file_size = os.path.getsize(image_path)
                    # 记录临时文件，用于后续清理
                    self.temp_files.append(image_path)
                    self.logger.info(f"成功从 Immich 下载图片: asset_id={asset_id}, path={image_path}, size={file_size} bytes")
                    return image_path
                else:
                    self.logger.error(f"下载的图片文件不存在: {image_path}")
                    return None
            else:
                self.logger.warning(f"从 Immich 下载图片失败，返回 None: asset_id={asset_id}")
                return None
        except Exception as e:
            import traceback
            self.logger.error(f"从 Immich 下载图片异常: {e}, traceback: {traceback.format_exc()}")
            return None

    def _save_base64_image(self, image_data_uri: str) -> Optional[str]:
        """
        将 base64 data URI 转换为临时文件

        Args:
            image_data_uri: base64 data URI 格式的图片数据

        Returns:
            临时文件路径，如果转换失败返回 None
        """
        try:
            # 解析 data URI: data:image/jpeg;base64,/9j/4AAQ...
            if not image_data_uri.startswith("data:image/"):
                self.logger.warning(f"无效的图片 data URI 格式: {image_data_uri[:50]}...")
                return None

            # 提取 MIME 类型和 base64 数据
            header, encoded = image_data_uri.split(",", 1)
            mime_type = header.split(";")[0].split(":")[1]  # image/jpeg

            # 确定文件扩展名
            ext_map = {
                "image/jpeg": ".jpg",
                "image/png": ".png",
                "image/gif": ".gif",
                "image/bmp": ".bmp",
                "image/webp": ".webp"
            }
            ext = ext_map.get(mime_type, ".jpg")

            # 解码 base64 数据
            image_data = base64.b64decode(encoded)

            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(
                dir=self.temp_dir,
                suffix=ext,
                delete=False
            )
            temp_file.write(image_data)
            temp_file.close()

            # 记录临时文件路径，用于后续清理
            self.temp_files.append(temp_file.name)

            self.logger.debug(f"已将 base64 图片保存为临时文件: {temp_file.name}")
            return temp_file.name

        except Exception as e:
            self.logger.error(f"保存 base64 图片失败: {e}")
            return None

    def _handle_websocket_message(self, message: str):
        """
        处理接收到的 WebSocket 消息

        Args:
            message: 接收到的消息字符串
        """
        try:
            data = json.loads(message)
            message_type = data.get("type", "")

            self.logger.info(f"收到 WebSocket 消息: type={message_type}, data_keys={list(data.keys())}")
            
            # 对于 vision 消息，记录详细信息
            if message_type == "vision":
                self.logger.info(f"Vision 消息详情: {json.dumps({k: v for k, v in data.items() if k != 'image'}, ensure_ascii=False)[:500]}")

            # 根据消息类型处理
            if message_type == "stt":
                # 用户语音转文字消息
                text = data.get("text", "")
                session_id = data.get("session_id", "")
                speaker = data.get("speaker", None)
                
                # 检查是否是JSON格式的文本
                try:
                    if text.strip().startswith("{") and text.strip().endswith("}"):
                        parsed = json.loads(text)
                        if isinstance(parsed, dict) and "content" in parsed:
                            text = parsed["content"]
                            if "speaker" in parsed:
                                speaker = parsed["speaker"]
                except (json.JSONDecodeError, TypeError):
                    pass
                
                # 构建消息对象
                message_obj = {
                    "type": "chat",
                    "role": "user",
                    "content": text,
                    "session_id": session_id
                }
                if speaker:
                    message_obj["speaker"] = speaker
                
                self.ui_update_queue.put(message_obj)

            elif message_type == "llm":
                # AI 回复消息（流式响应片段）
                # 注意：由于我们已经使用 llm_sentence 按句子显示，这里不再显示流式片段
                # 避免重复显示和混乱
                text = data.get("text", "")
                session_id = data.get("session_id", "")
                
                # 只记录日志，不显示（因为 llm_sentence 会显示完整句子）
                self.logger.debug(f"收到 LLM 流式响应片段: text_length={len(text)}, session_id={session_id}")
                
                # 不再合并显示流式响应，等待 llm_sentence 消息
                # 这样可以避免重复显示，每个句子会通过 llm_sentence 独立显示

            elif message_type == "llm_sentence":
                # AI 回复消息（完整句子，作为独立消息显示）
                text = data.get("text", "")
                session_id = data.get("session_id", "")
                
                # 清除该 session_id 的流式消息缓存（如果有），避免冲突
                if session_id in self.current_llm_message:
                    self.logger.debug(f"清除 session_id {session_id} 的流式消息缓存，因为收到完整句子")
                    del self.current_llm_message[session_id]
                
                text_cleaned = text.strip()  # 去除首尾空白
                self.logger.info(f"收到完整句子消息: text_length={len(text_cleaned)}, session_id={session_id}, "
                               f"text_preview={text_cleaned[:50]}..., current_history_length={len(self.chat_history)}")
                
                # 直接作为新的 assistant 消息添加（不合并，每个句子独立显示）
                # 添加 _is_sentence 标记，确保总是作为新消息添加
                self.ui_update_queue.put({
                    "type": "chat",
                    "role": "assistant",
                    "content": text_cleaned,
                    "session_id": session_id,
                    "_is_sentence": True  # 标记为句子消息，确保独立显示
                })

            elif message_type == "vision":
                # 视觉识别结果
                result = data.get("result", "")
                people = data.get("people", [])
                session_id = data.get("session_id", "")
                asset_id = data.get("asset_id", None)  # Immich asset ID（最优先）
                image_url = data.get("image_url", None)  # Immich 图片 URL（已废弃，因为需要认证）
                image_data_uri = data.get("image", None)  # base64 图片（降级方案）

                # 添加详细日志
                self.logger.info(f"收到 vision 消息: session_id={session_id}, asset_id={asset_id}, "
                               f"has_image_url={image_url is not None}, has_image_data_uri={image_data_uri is not None}, "
                               f"result_length={len(result) if result else 0}, people={people}")
                self.logger.info(f"Immich client 状态: enabled={self.immich_client.enabled if self.immich_client else False}, "
                               f"client_exists={self.immich_client is not None}")

                # 构建文本内容
                text_content = result
                if people:
                    text_content += f"\n\n识别到的人物：{', '.join(people)}"

                # 构建显示内容
                # Gradio 的 messages 格式：content 可以是字符串或列表 [image_path_or_url, "text"]
                if asset_id and self.immich_client and self.immich_client.enabled:
                    # 最优先：使用 asset_id 通过 Immich client 下载图片
                    # 由于下载是异步的，先显示文本，然后异步下载图片
                    self.logger.info(f"收到 asset_id，将通过 Immich client 下载图片: {asset_id}")
                    
                    # 先显示文本内容，并保存消息索引用于后续更新
                    # 记录当前消息索引
                    current_index = len(self.chat_history)
                    self.ui_update_queue.put({
                        "type": "chat",
                        "role": "assistant",
                        "content": text_content,
                        "session_id": session_id,
                        "_vision_index": current_index  # 保存索引用于后续更新
                    })
                    
                    # 创建异步任务下载图片
                    def download_and_update():
                        """在后台线程中下载图片并更新消息"""
                        self.logger.info(f"后台线程开始下载图片: asset_id={asset_id}, expected_index={current_index}")
                        try:
                            # 创建新的事件循环（因为在线程中）
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                            # 下载图片
                            self.logger.info(f"调用 _download_immich_image({asset_id})")
                            image_path = loop.run_until_complete(self._download_immich_image(asset_id))
                            
                            if image_path:
                                self.logger.info(f"图片下载成功，开始更新消息: image_path={image_path}, text_content_length={len(text_content)}, expected_index={current_index}")
                                
                                # 等待一小段时间，确保消息已经添加到历史记录
                                import time
                                time.sleep(0.1)
                                
                                # 尝试使用保存的索引更新消息
                                found = False
                                if current_index < len(self.chat_history):
                                    msg = self.chat_history[current_index]
                                    if (msg.get("role") == "assistant" and 
                                        isinstance(msg.get("content"), str)):
                                        # 更新消息，添加图片
                                        msg["content"] = [image_path, text_content]
                                        # 通知 UI 更新
                                        self.ui_update_queue.put({
                                            "type": "chat_update",
                                            "index": current_index,
                                            "content": [image_path, text_content]
                                        })
                                        self.logger.info(f"已更新消息索引 {current_index}，添加图片: {image_path}")
                                        found = True
                                
                                # 如果索引不匹配，尝试通过内容匹配
                                if not found:
                                    self.logger.warning(f"索引 {current_index} 不匹配，尝试通过内容匹配，chat_history 长度: {len(self.chat_history)}")
                                    for i in range(len(self.chat_history) - 1, -1, -1):
                                        msg = self.chat_history[i]
                                        msg_content = msg.get("content", "")
                                        # 检查是否是匹配的消息（可能是字符串或列表）
                                        if (msg.get("role") == "assistant" and 
                                            isinstance(msg_content, str) and 
                                            msg_content == text_content):
                                            # 更新消息，添加图片
                                            msg["content"] = [image_path, text_content]
                                            # 通知 UI 更新
                                            self.ui_update_queue.put({
                                                "type": "chat_update",
                                                "index": i,
                                                "content": [image_path, text_content]
                                            })
                                            self.logger.info(f"已通过内容匹配更新消息索引 {i}，添加图片: {image_path}")
                                            found = True
                                            break
                                
                                if not found:
                                    self.logger.warning(f"未找到匹配的消息进行更新，chat_history 长度: {len(self.chat_history)}")
                                    # 打印最后几条消息用于调试
                                    for idx, msg in enumerate(self.chat_history[-3:]):
                                        actual_idx = len(self.chat_history) - 3 + idx
                                        self.logger.warning(f"消息 {actual_idx}: role={msg.get('role')}, content_type={type(msg.get('content'))}, content_preview={str(msg.get('content'))[:100]}")
                                    # 如果还是找不到，直接添加新消息
                                    self.logger.info("未找到匹配消息，直接添加新消息（包含图片）")
                                    self.chat_history.append({
                                        "role": "assistant",
                                        "content": [image_path, text_content]
                                    })
                                    self.ui_update_queue.put({
                                        "type": "chat",
                                        "role": "assistant",
                                        "content": [image_path, text_content],
                                        "session_id": session_id
                                    })
                            else:
                                self.logger.warning(f"从 Immich 下载图片失败，将使用降级方案: asset_id={asset_id}")
                                # 如果下载失败，尝试使用 base64
                                if image_data_uri:
                                    self.logger.info("尝试使用 base64 图片作为降级方案")
                                    image_path = self._save_base64_image(image_data_uri)
                                    if image_path:
                                        for i in range(len(self.chat_history) - 1, -1, -1):
                                            msg = self.chat_history[i]
                                            if (msg.get("role") == "assistant" and 
                                                isinstance(msg.get("content"), str) and 
                                                msg.get("content") == text_content):
                                                msg["content"] = [image_path, text_content]
                                                self.ui_update_queue.put({
                                                    "type": "chat_update",
                                                    "index": i,
                                                    "content": [image_path, text_content]
                                                })
                                                self.logger.info(f"已使用 base64 图片更新消息索引 {i}")
                                                break
                                else:
                                    self.logger.warning("没有可用的降级方案（base64 图片）")
                        except Exception as e:
                            import traceback
                            self.logger.error(f"下载 Immich 图片时出错: {e}, traceback: {traceback.format_exc()}")
                        finally:
                            loop.close()
                            self.logger.info("后台下载线程结束")
                    
                    # 在后台线程中执行下载
                    download_thread = threading.Thread(target=download_and_update, daemon=True)
                    download_thread.start()
                    
                elif image_data_uri:
                    # 降级方案：将 base64 data URI 转换为临时文件
                    image_path = self._save_base64_image(image_data_uri)
                    
                    if image_path:
                        # 使用列表格式：[图片路径, 文本字符串]
                        content = [image_path, text_content]
                    else:
                        # 转换失败，只显示文本
                        content = text_content
                    
                    # 将识别结果作为assistant消息显示
                    self.ui_update_queue.put({
                        "type": "chat",
                        "role": "assistant",
                        "content": content,
                        "session_id": session_id
                    })
                else:
                    # 没有图片时，只显示文本
                    content = text_content
                    
                    # 将识别结果作为assistant消息显示
                    self.ui_update_queue.put({
                        "type": "chat",
                        "role": "assistant",
                        "content": content,
                        "session_id": session_id
                    })

            elif message_type == "memory_markdown":
                # 记忆内容（Markdown格式）
                content = data.get("content", "")
                session_id = data.get("session_id", "")
                self.ui_update_queue.put({
                    "type": "memory",
                    "content": content,
                    "session_id": session_id
                })

            elif message_type == "memory_images":
                # 记忆图片
                images = data.get("images", [])
                session_id = data.get("session_id", "")

                # 将图片URL转换为Markdown格式
                if images:
                    image_markdown = "\n".join([f"![相关照片]({img})" for img in images[:6]])
                    self.ui_update_queue.put({
                        "type": "memory_append",
                        "content": f"\n\n## 相关照片\n\n{image_markdown}",
                        "session_id": session_id
                    })

            elif message_type == "tts":
                # TTS 状态消息（可选显示）
                pass

            else:
                # 其他类型的消息
                self.logger.debug(f"未处理的 WebSocket 消息类型: {message_type}")

        except json.JSONDecodeError as e:
            self.logger.error(f"解析 WebSocket 消息失败: {e}, 消息内容: {message}")
        except Exception as e:
            self.logger.error(f"处理 WebSocket 消息时出错: {e}")

    def send_message(self, message: str):
        """
        发送消息到 WebSocket 服务器

        Args:
            message: 要发送的消息
        """
        if not message or not message.strip():
            return

        if not self.is_connected or not self.websocket:
            self.logger.warning("WebSocket 未连接，无法发送消息")
            return

        try:
            # 构建消息
            ws_message = {
                "type": "hello",
                "content": message.strip()
            }

            # 在新的事件循环中发送消息
            async def send():
                try:
                    await self.websocket.send(json.dumps(ws_message))
                    self.logger.debug(f"发送消息成功: {message}")
                except Exception as e:
                    self.logger.error(f"发送消息失败: {e}")

            # 运行异步发送
            asyncio.run(send())

        except Exception as e:
            self.logger.error(f"发送消息时出错: {e}")

    def update_ui(self) -> tuple:
        """
        更新 UI 界面（定时调用）

        Returns:
            (chat_history, memory_markdown, status_text) 的更新
        """
        # 处理消息队列
        updated = False
        while True:
            try:
                update_data = self.ui_update_queue.get_nowait()

                if update_data["type"] == "chat":
                    # 更新聊天记录 (使用 messages 格式)
                    role = update_data["role"]
                    content = update_data["content"]
                    speaker = update_data.get("speaker", None)
                    session_id = update_data.get("session_id", "")
                    is_sentence = update_data.get("_is_sentence", False)  # 标记是否为句子消息

                    # 如果是新的用户消息，清除之前的LLM流式消息缓存
                    if role == "user" and session_id in self.current_llm_message:
                        del self.current_llm_message[session_id]

                    # 构建消息对象
                    message_obj = {"role": role, "content": content}
                    
                    # 处理说话人信息
                    if speaker:
                        if isinstance(content, str):
                            # 字符串格式：直接添加说话人前缀
                            message_obj["content"] = f"[{speaker}] {content}"
                        elif isinstance(content, list):
                            # 列表格式：[图片URI, 文本字符串]
                            # Gradio 期望的格式是 [image_path_or_uri, "text_string"]
                            if len(content) >= 2 and isinstance(content[1], str):
                                # 在文本字符串前添加说话人信息
                                content[1] = f"[{speaker}] {content[1]}"
                            elif len(content) == 1 and isinstance(content[0], str):
                                # 只有图片，添加文本
                                content.append(f"[{speaker}]")
                            message_obj["content"] = content
                        else:
                            # 其他格式，保持原样
                            message_obj["content"] = content
                    else:
                        # 没有说话人信息，直接使用原内容
                        message_obj["content"] = content

                    if role == "user":
                        self.chat_history.append(message_obj)
                        self.logger.debug(f"添加用户消息: content_length={len(str(content))}")
                    elif role == "assistant":
                        # 对于 assistant 消息，总是作为新消息添加（不合并）
                        # 特别是句子消息（llm_sentence），必须独立显示
                        # 创建新的消息对象，确保不会与之前的消息合并
                        new_message = {
                            "role": "assistant",
                            "content": message_obj["content"]
                        }
                        self.chat_history.append(new_message)
                        self.logger.info(f"✅ 添加新的 assistant 消息: is_sentence={is_sentence}, "
                                       f"content_length={len(str(content))}, "
                                       f"content_preview={str(content)[:50]}..., "
                                       f"chat_history_length={len(self.chat_history)}, "
                                       f"last_message_index={len(self.chat_history) - 1}")
                    elif role == "system":
                        self.chat_history.append(message_obj)

                    updated = True

                elif update_data["type"] == "llm_stream":
                    # LLM流式响应更新（消息已在历史记录中，只需标记更新）
                    updated = True

                elif update_data["type"] == "chat_update":
                    # 更新已存在的聊天消息（例如：添加图片）
                    index = update_data.get("index", -1)
                    content = update_data.get("content")
                    
                    self.logger.info(f"收到 chat_update: index={index}, content_type={type(content)}, "
                                   f"chat_history_length={len(self.chat_history)}")
                    
                    if 0 <= index < len(self.chat_history):
                        old_content = self.chat_history[index].get("content")
                        self.chat_history[index]["content"] = content
                        self.logger.info(f"已更新消息索引 {index}: old_content_type={type(old_content)}, "
                                       f"new_content_type={type(content)}")
                        if isinstance(content, list) and len(content) > 0:
                            self.logger.info(f"新内容为列表: 第一个元素类型={type(content[0])}, "
                                           f"第二个元素类型={type(content[1]) if len(content) > 1 else 'N/A'}")
                        updated = True
                    else:
                        self.logger.warning(f"chat_update: 无效的消息索引: {index}, chat_history_length={len(self.chat_history)}")

                elif update_data["type"] == "memory":
                    # 更新记忆内容
                    self.memory_markdown = update_data["content"]
                    updated = True

                elif update_data["type"] == "memory_append":
                    # 追加记忆内容
                    self.memory_markdown += update_data["content"]
                    updated = True

                elif update_data["type"] == "status":
                    # 状态更新
                    status = update_data["status"]
                    return self.chat_history, self.memory_markdown, status

            except Empty:
                break

        # 返回当前状态
        status = "已连接" if self.is_connected else "未连接"
        return self.chat_history, self.memory_markdown, status

    def _cleanup_temp_files(self):
        """
        清理临时文件
        """
        try:
            for temp_file in self.temp_files:
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        self.logger.debug(f"已删除临时文件: {temp_file}")
                except Exception as e:
                    self.logger.warning(f"删除临时文件失败: {temp_file}, 错误: {e}")
            
            self.temp_files.clear()
            
            # 尝试删除临时目录（如果为空）
            try:
                if os.path.exists(self.temp_dir) and not os.listdir(self.temp_dir):
                    os.rmdir(self.temp_dir)
            except Exception as e:
                self.logger.debug(f"删除临时目录失败（可能不为空）: {e}")
                
        except Exception as e:
            self.logger.error(f"清理临时文件时出错: {e}")

    def clear_chat_history(self) -> List:
        """
        清除聊天记录

        Returns:
            清空后的聊天历史
        """
        self.chat_history = []
        self.current_llm_message = {}  # 清除流式消息缓存
        self._cleanup_temp_files()  # 清理临时文件
        self.logger.info("聊天记录已清除")
        return self.chat_history

    def refresh_memory(self) -> str:
        """
        刷新记忆显示区

        Returns:
            记忆内容
        """
        # 这里可以添加从服务器获取最新记忆的逻辑
        # 暂时保持不变
        self.logger.info("记忆已刷新")
        return self.memory_markdown

    def clear_memory(self) -> str:
        """
        清除记忆显示区

        Returns:
            清空后的记忆内容
        """
        self.memory_markdown = "# 记忆显示区\n\n待开发功能..."
        self.logger.info("记忆显示区已清除")
        return self.memory_markdown
