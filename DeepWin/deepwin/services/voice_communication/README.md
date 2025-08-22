# VoiceManager 语音通信管理器

## 概述

VoiceManager 是一个功能完整的语音通信管理器，基于阿里百炼平台的多模态对话 API，支持文本对话、文本转录、VQA 功能和实时视频流功能。采用模块化设计，支持非阻塞运行，适合集成到上位机应用中。

## 主要特性

### 1. 文本对话功能

- 支持随时发送文本，服务器返回语音文字结果
- 支持连续对话，可发送多条文本消息
- 非阻塞运行，不影响主线程

### 2. 文本转录功能

- 支持随时发送文本，服务器返回对应的语音
- 适用于文本转语音(TTS)场景
- 支持批量转录处理

### 3. VQA 功能

- 支持图片+文本的视觉问答
- 可传递文本提示及图片路径
- 支持等待语音指令作为问题
- 参考官方示例 `run_vqa.py` 实现

### 4. 实时视频流功能

- 支持随时开启、关闭实时视频对话
- 启用电脑摄像头，每隔 500ms 上传一帧图像
- 参考官方示例 `run_live_ai.py` 实现
- 摄像头管理独立封装，支持回调传递

### 5. 非阻塞运行

- 整个运行过程非阻塞
- 适合作为上位机功能的一部分
- 使用 Qt 信号槽机制进行异步通信

### 6. 模块化架构

- 代码结构清晰，功能分离明确
- 各功能独立管理，便于维护和扩展
- 支持单独拆分多个文件

## 架构设计

```
VoiceManager (主管理器)
├── CameraManager (摄像头管理)
├── VQAManager (VQA功能管理)
├── TranscriptManager (转录功能管理)
├── LiveStreamManager (实时视频流管理)
└── TMultiModalConversation (对话实例)
```

## 安装依赖

```bash
pip install -r requirements.txt
```

### 主要依赖包

- `PySide6`: Qt 界面框架
- `opencv-python`: 摄像头和图像处理
- `pyaudio`: 音频处理
- `dashscope`: 阿里百炼平台 SDK
- `python-dotenv`: 环境变量管理

## 使用方法

### 1. 基本初始化

```python
from voice_manager import VoiceManager
from data_management.log_manager import LogManager
from config.config_manager import ConfigManager

# 创建管理器实例
log_manager = LogManager()
config_manager = ConfigManager()
voice_manager = VoiceManager(log_manager, config_manager)
```

### 2. 文本对话

```python
# 启动文本对话
success = voice_manager.start_text_conversation("你好，请介绍一下你自己")

# 发送后续消息
voice_manager.send_text_message("你能帮我写一首诗吗？")

# 停止对话
voice_manager.stop_conversation()
```

### 3. 文本转录

```python
# 启动文本转录
success = voice_manager.start_transcript("这是一段需要转换为语音的文本")

# 发送转录文本
voice_manager.send_transcript_text("新的转录文本")

# 停止转录
voice_manager.stop_conversation()
```

### 4. VQA 功能

```python
# 使用图片启动VQA
success = voice_manager.start_vqa_with_image(
    image_path="path/to/image.jpg",
    prompt="这张图片里有什么？"
)

# 使用base64图片启动VQA
success = voice_manager.start_vqa_with_base64(
    image_base64="base64_encoded_image_data",
    prompt="描述这张图片"
)

# 发送VQA提示
voice_manager.send_vqa_prompt("这是什么颜色？")

# 停止VQA
voice_manager.stop_conversation()
```

### 5. 实时视频流

```python
# 启动实时视频流
success = voice_manager.start_live_stream(camera_index=0)

# 停止实时视频流
voice_manager.stop_live_stream()
```

### 6. 语音对话

```python
# 启动语音对话
success = voice_manager.start_voice_conversation()

# 停止语音对话
voice_manager.stop_conversation()
```

## 信号和槽

VoiceManager 提供了丰富的信号，用于状态监控和事件处理：

### 主要信号

- `conversation_started(dialog_type)`: 对话启动
- `conversation_stopped()`: 对话停止
- `conversation_error(error_message)`: 对话错误
- `voice_command_received(command)`: 语音命令接收
- `voice_state_changed(state_message)`: 语音状态变化

### 功能状态信号

- `text_conversation_started()`: 文本对话启动
- `transcript_started()`: 转录启动
- `vqa_started()`: VQA 启动
- `live_stream_started()`: 实时视频流启动

### 使用示例

```python
# 连接信号
voice_manager.conversation_started.connect(self.on_conversation_started)
voice_manager.conversation_error.connect(self.on_conversation_error)
voice_manager.voice_command_received.connect(self.on_command_received)

# 信号处理函数
def on_conversation_started(self, dialog_type):
    print(f"对话已启动: {dialog_type}")

def on_conversation_error(self, error_msg):
    print(f"对话错误: {error_msg}")

def on_command_received(self, command):
    print(f"收到命令: {command}")
```

## 配置管理

VoiceManager 支持通过配置文件和环境变量进行配置：

### 环境变量

```bash
export APP_ID="your_app_id"
export WORKSPACE_ID="your_workspace_id"
export DASHSCOPE_API_KEY="your_api_key"
```

### 配置文件

```json
{
  "voice": {
    "app_id": "your_app_id",
    "workspace_id": "your_workspace_id",
    "api_key": "your_api_key",
    "voice_name": "longxiaochun_v2",
    "sample_rate": 48000,
    "conversation_mode": "duplex"
  }
}
```

## 状态监控

```python
# 获取对话状态
status = voice_manager.get_conversation_status()
print(f"对话状态: {status}")

# 状态信息包含
# - is_active: 是否活跃
# - current_conversation_type: 当前对话类型
# - dialog_state: 对话状态
# - 各功能管理器的详细状态
```

## 错误处理

VoiceManager 提供了完善的错误处理机制：

```python
# 监听错误信号
voice_manager.conversation_error.connect(self.handle_error)

def handle_error(self, error_msg):
    print(f"处理错误: {error_msg}")
    # 进行错误恢复或用户提示
```

## 资源清理

```python
# 清理资源
voice_manager.cleanup()

# 或在应用退出时
import atexit
atexit.register(voice_manager.cleanup)
```

## 运行示例

```bash
# 运行完整示例
python example_usage.py

# 运行特定功能示例
python -c "
from example_usage import VoiceManagerExample
example = VoiceManagerExample()
example.run_text_conversation_example()
"
```

## 注意事项

1. **环境配置**: 确保正确配置阿里百炼平台的认证信息
2. **摄像头权限**: 实时视频流功能需要摄像头访问权限
3. **网络连接**: 需要稳定的网络连接以访问阿里百炼服务
4. **资源管理**: 及时清理资源，避免内存泄漏
5. **错误处理**: 实现适当的错误处理机制

## 故障排除

### 常见问题

1. **导入错误**: 检查依赖包是否正确安装
2. **认证失败**: 验证 API 密钥和配置信息
3. **摄像头无法访问**: 检查摄像头权限和驱动
4. **网络连接失败**: 检查网络设置和防火墙

### 调试模式

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 扩展开发

VoiceManager 采用模块化设计，便于扩展新功能：

1. 创建新的功能管理器类
2. 继承相应的基类
3. 实现必要的接口方法
4. 在 VoiceManager 中集成新功能

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request 来改进 VoiceManager。

## 联系方式

如有问题或建议，请通过项目仓库提交 Issue。
