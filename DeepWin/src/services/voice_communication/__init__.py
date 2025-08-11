"""
语音通信模块

提供语音输入输出功能，包括：
- 语音识别和合成
- 与阿里百炼平台的通信
- 语音对话管理
- 守护进程管理
"""

from .audio_manager import VoiceManager
from .TMultiModalConversation import TMultiModalConversation
from .ChatCallback import ChatCallback

__all__ = [
    'VoiceManager',
    'TMultiModalConversation',
    'ChatCallback',
]
