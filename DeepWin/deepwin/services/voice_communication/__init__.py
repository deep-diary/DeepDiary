#!/usr/bin/env python3
"""
Voice Communication Package for DeepWin

一个功能完整的语音通信包，支持：
- 文本对话
- 文本转录
- VQA (Visual Question Answering)
- 实时视频流
- 语音识别和合成

采用模块化设计，支持非阻塞运行
"""

__version__ = "0.1.1"
__author__ = "DeepWin Team"
__email__ = "team@deepwin.com"
__description__ = "Voice Communication Package for DeepWin"

# 导出主要类和模块
__all__ = [
    # 主要管理器
    'VoiceManager',
    'CameraManager', 
    'VQAManager',
    'TranscriptManager',
    'LiveStreamManager',
    
    # 工具类
    'AudioRecorder',
    'B64PCMPlayer',
    'ListeningStateMonitor',
    
    # 对话类
    'TMultiModalConversation',
    'ChatCallback',
    
    # 版本信息
    '__version__',
    '__author__',
    '__email__',
    '__description__'
]

# 导入主要类 - 使用相对导入提高兼容性
try:
    # 使用相对导入，这样在包安装后也能正常工作
    from .voice_manager import VoiceManager
    from .camera_manager import CameraManager
    from .vqa_manager import VQAManager
    from .transcript_manager import TranscriptManager
    from .live_stream_manager import LiveStreamManager
    
    # 导入工具类
    from .AudioRecorder import AudioRecorder
    from .B64PCMPlayer import B64PCMPlayer
    from .ListeningStateMonitor import ListeningStateMonitor
    
    # 导入对话类
    from .TMultiModalConversation import TMultiModalConversation
    from .ChatCallback import ChatCallback
    
    print("✅ 所有模块导入成功")
    
except ImportError as e:
    print(f"⚠️  导入模块时出错: {e}")
    print("某些功能可能不可用")
    
    # 尝试延迟导入
    VoiceManager = None
    CameraManager = None
    VQAManager = None
    TranscriptManager = None
    LiveStreamManager = None
    AudioRecorder = None
    B64PCMPlayer = None
    ListeningStateMonitor = None
    TMultiModalConversation = None
    ChatCallback = None

print(f"Voice Communication Module v{__version__} 已加载")
print("支持的功能: 文本对话、转录、VQA、实时视频流")
print("使用方式: from voice_communication import VoiceManager")