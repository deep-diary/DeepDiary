# 语音通信模块

本模块提供了基于阿里百炼平台的语音对话功能，支持语音识别、语音合成和智能对话。经过优化后，具有更好的错误处理能力和稳定性。

## 模块结构

```
voice_communication/
├── __init__.py                 # 模块初始化文件
├── audio_manager.py            # 语音管理器主类
├── TMultiModalConversation.py # 多模态对话管理类
├── ChatCallback.py            # 对话回调处理器
├── AudioRecorder.py           # 音频录制器
├── B64PCMPlayer.py            # 音频播放器
├── ListeningStateMonitor.py   # 监听状态监控器
├── requirements.txt            # 依赖包列表
├── demo.py                   # 测试脚本
└── README.md                  # 本文件
```

## 主要功能

### 1. VoiceManager (语音管理器)

- 管理语音对话的生命周期
- 处理配置加载和日志记录
- 提供 Qt 信号用于 UI 集成
- 支持多轮对话管理
- 智能错误处理和恢复机制

### 2. TMultiModalConversation (多模态对话)

- 管理与阿里百炼平台的 WebSocket 连接
- 处理音频数据的发送和接收
- 管理对话状态转换
- 支持多种对话模式
- 自动重连和错误恢复

### 3. ChatCallback (对话回调)

- 处理服务器事件回调
- 管理音频播放和录制
- 解析命令和意图
- 监控对话状态变化
- 优雅的错误处理，避免程序崩溃

### 4. AudioRecorder (音频录制器)

- 非阻塞音频录制
- 自动音频流恢复机制
- 多线程安全设计
- 支持实时音频数据回调

### 5. B64PCMPlayer (音频播放器)

- 实时音频流播放
- Base64 编码音频支持
- 多线程解码和播放
- 守护线程设计，支持程序正常退出

### 6. ListeningStateMonitor (状态监控器)

- 监控对话状态变化
- 支持超时等待机制
- 线程安全的状态管理

## 使用方法

### 基本使用

```python
from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager
from src.services.voice_communication.audio_manager import VoiceManager

# 初始化管理器和语音管理器
log_manager = LogManager()
config_manager = ConfigManager(log_manager)
voice_manager = VoiceManager(log_manager, config_manager)

# 开始语音对话
success = voice_manager.start_voice_conversation()
if success:
    print("语音对话已启动")

    # 获取对话状态
    status = voice_manager.get_conversation_status()
    print(f"对话状态: {status}")

    # 停止语音对话
    voice_manager.stop_voice_conversation()
```

### 高级使用

```python
# 自定义对话参数
voice_manager = VoiceManager(log_manager, config_manager)

# 设置对话模式
config_manager.set('voice.conversation_mode', 'push2talk')

# 开始对话并指定对话ID
dialog_id = "custom_dialog_123"
success = voice_manager.start_voice_conversation(dialog_id)

# 监听对话状态变化
voice_manager.voice_state_changed.connect(lambda state: print(f"状态变化: {state}"))
voice_manager.conversation_error.connect(lambda error: print(f"错误: {error}"))
```

### 配置要求

在 `config.json` 中需要配置以下语音相关参数：

```json
{
  "voice": {
    "app_id": "your_app_id",
    "workspace_id": "your_workspace_id",
    "api_key": "your_api_key",
    "voice_name": "longxiaochun_v2",
    "sample_rate": 48000,
    "audio_chunk_size": 3200,
    "websocket_url": "wss://dashscope.aliyuncs.com/api-ws/v1/inference",
    "model_name": "multimodal-dialog",
    "conversation_mode": "duplex"
  }
}
```

### 环境变量

也可以通过环境变量设置，支持多种路径查找：

```bash
# 在 DeepWin/.env 文件中设置
APP_ID="your_app_id"
WORKSPACE_ID="your_workspace_id"
DASHSCOPE_API_KEY="your_api_key"

# 或者在系统环境变量中设置
export APP_ID="your_app_id"
export WORKSPACE_ID="your_workspace_id"
export DASHSCOPE_API_KEY="your_api_key"
```

## 对话模式

支持以下对话模式：

- **duplex**: 全双工模式，支持连续对话
- **push2talk**: 按键通话模式
- **tap2talk**: 点击通话模式

## 音频格式

- **输入**: PCM 格式，16kHz 采样率
- **输出**: PCM 格式，48kHz 采样率
- **块大小**: 3200 字节
- **声道**: 单声道 (mono)

## 错误处理与恢复

### 自动恢复机制

- **音频流异常**: 自动重新初始化音频设备
- **网络连接**: 支持断线重连
- **设备权限**: 优雅处理权限不足情况

### 错误分类

- **配置错误**: 缺少必要参数时提供详细错误信息
- **设备错误**: 音频设备不可用时给出解决建议
- **网络错误**: 连接失败时提供重试选项
- **API 错误**: 认证失败时指导用户检查密钥

## 性能优化

### 线程管理

- 所有音频处理线程设置为守护线程
- 支持程序正常退出时的资源清理
- 线程间通信使用队列，避免阻塞

### 内存管理

- 音频数据流式处理，避免大量内存占用
- 及时释放不需要的音频资源
- 支持音频数据缓冲池

## 测试

### 运行测试

```bash
cd DeepWin/src/services/voice_communication
python demo.py  # 运行测试脚本
```

### 手动测试

```python
# 测试音频设备
from .AudioRecorder import AudioRecorder
import pyaudio

pya = pyaudio.PyAudio()
recorder = AudioRecorder(pya, sample_rate=16000)
print("音频录制器初始化成功")

# 测试音频播放
from .B64PCMPlayer import B64PCMPlayer
player = B64PCMPlayer(pya, sample_rate=48000)
print("音频播放器初始化成功")
```

## 依赖项

### 核心依赖

```txt
# 阿里百炼平台SDK
dashscope>=1.18.0

# 音频处理
pyaudio>=0.2.11

# 环境变量管理
python-dotenv>=1.0.0

# Qt界面框架
PySide6>=6.0.0
```

### 可选依赖

```txt
# 音频处理增强
numpy>=1.21.0
scipy>=1.7.0

# 音频格式支持
soundfile>=0.10.0
```

## 安装说明

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境

```bash
# 复制配置模板
cp config_example.json config.json

# 编辑配置文件
# 填入你的阿里百炼API密钥
```

### 3. 验证安装

```python
# 测试导入
from src.services.voice_communication import VoiceManager
print("模块导入成功")
```

## 注意事项

### 系统要求

1. **操作系统**: Windows 10+, macOS 10.14+, Ubuntu 18.04+
2. **Python 版本**: Python 3.8+
3. **音频设备**: 支持麦克风输入和扬声器输出
4. **网络**: 稳定的互联网连接，支持 WebSocket

### 权限要求

1. **麦克风权限**: 需要访问麦克风进行语音录制
2. **音频输出权限**: 需要访问扬声器进行语音播放
3. **网络权限**: 需要访问互联网连接阿里百炼服务

### 最佳实践

1. **音频质量**: 使用高质量麦克风获得更好的识别效果
2. **网络环境**: 在稳定的网络环境下使用，避免频繁断线
3. **资源管理**: 及时停止不需要的对话，释放系统资源
4. **错误监控**: 定期检查日志文件，及时发现和解决问题

## 故障排除

### 常见问题

#### 1. 导入错误

**症状**: `ModuleNotFoundError` 或 `ImportError`

**解决方案**:

```bash
# 检查Python路径
python -c "import sys; print(sys.path)"

# 确保在正确的目录下运行
cd DeepWin
python -m src.services.voice_communication.audio_manager
```

#### 2. 音频设备错误

**症状**: `OSError: [Errno -9996] Invalid input device`

**解决方案**:

```python
# 检查可用音频设备
import pyaudio
pya = pyaudio.PyAudio()
for i in range(pya.get_device_count()):
    info = pya.get_device_info_by_index(i)
    print(f"设备 {i}: {info['name']}")
```

#### 3. 网络连接失败

**症状**: `WebSocket connection failed`

**解决方案**:

- 检查网络连接
- 验证防火墙设置
- 确认 API 密钥有效
- 检查服务状态

#### 4. API 认证失败

**症状**: `Authentication failed` 或 `Invalid API key`

**解决方案**:

```bash
# 检查环境变量
echo $DASHSCOPE_API_KEY

# 检查配置文件
cat config.json | grep api_key
```

### 调试技巧

#### 1. 启用详细日志

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# 或者在配置中设置
config_manager.set('general.log_level', 'DEBUG')
```

#### 2. 检查音频流状态

```python
# 检查录制器状态
print(f"录制状态: {recorder.status}")
print(f"音频流活跃: {recorder.recorder_stream.is_active()}")

# 检查播放器状态
print(f"播放状态: {player.status}")
print(f"音频流活跃: {player.player_stream.is_active()}")
```

#### 3. 监控网络连接

```python
# 检查WebSocket连接状态
if hasattr(voice_manager, 'conversation'):
    state = voice_manager.conversation.get_dialog_state()
    print(f"对话状态: {state}")
```

## 更新日志

### v1.1.0 (最新)

- ✅ 修复配置文件路径问题
- ✅ 改进错误处理机制，避免程序崩溃
- ✅ 优化线程管理，支持程序正常退出
- ✅ 增强音频设备异常恢复能力
- ✅ 改进环境变量文件路径查找

### v1.0.0

- 🎉 初始版本发布
- 🎯 支持基本的语音对话功能
- 🔧 集成阿里百炼平台
- 📱 提供 Qt 界面集成支持

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进这个模块！

### 开发环境设置

```bash
# 克隆项目
git clone <repository-url>
cd DeepDiary/DeepWin

# 安装开发依赖
pip install -r requirements.txt
pip install -r src/services/voice_communication/requirements.txt

# 运行测试
python -m pytest tests/
```

### 代码规范

- 遵循 PEP 8 代码风格
- 添加适当的类型注解
- 编写清晰的文档字符串
- 确保代码覆盖率

## 许可证

MIT License - 详见 LICENSE 文件

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交 GitHub Issue
- 发送邮件至项目维护者
- 在项目讨论区留言

---

**注意**: 使用本模块需要有效的阿里百炼 API 密钥，请确保遵守相关服务条款和隐私政策。
