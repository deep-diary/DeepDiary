# 定义DashScope通信状态
from enum import Enum
from typing import Dict


class CommunicationSequence(Enum):
    """按通信顺序排列的状态枚举"""
    # 系统启动阶段
    SEQ_01_SYSTEM_START = "01_system_start"
    SEQ_02_SYSTEM_STARTED = "02_system_started"
    
    # 全双工场景 - 对话准备
    SEQ_03_DIALOG_LISTENING = "03_dialog_listening"
    SEQ_04_AUDIO_SILENCE = "04_audio_silence"
    SEQ_05_USER_SPEAK = "05_user_speak"
    SEQ_06_AUDIO_SPEECH = "06_audio_speech"
    
    # 语音识别阶段
    SEQ_07_VAD_ON = "07_vad_on"
    SEQ_08_SPEECH_STARTED = "08_speech_started"
    SEQ_09_SPEECH_CONTENT = "09_speech_content"
    SEQ_10_SPEECH_ENDED = "10_speech_ended"
    
    # 响应准备阶段
    SEQ_11_DIALOG_THINKING = "11_dialog_thinking"
    SEQ_12_RESPONDING_CONTENT = "12_responding_content"
    SEQ_13_DIALOG_RESPONDING = "13_dialog_responding"
    SEQ_14_RESPONDING_STARTED = "14_responding_started"
    SEQ_15_LOCAL_RESPONDING_STARTED = "15_local_responding_started"
    
    # 正常播放场景
    SEQ_16_PLAY_AUDIO = "16_play_audio"
    SEQ_17_RESPONDING_ENDED = "17_responding_ended"
    SEQ_18_LOCAL_RESPONDING_ENDED = "18_local_responding_ended"
    SEQ_19_DIALOG_LISTENING_AGAIN = "19_dialog_listening_again"
    
    # 用户打断场景
    SEQ_20_USER_INTERRUPT = "20_user_interrupt"
    SEQ_21_REQUEST_ACCEPTED = "21_request_accepted"
    SEQ_22_DIALOG_LISTENING_INTERRUPT = "22_dialog_listening_interrupt"
    SEQ_23_SPEECH_STARTED_INTERRUPT = "23_speech_started_interrupt"
    
    # 主动互动场景
    SEQ_24_REQUEST_TO_RESPOND = "24_request_to_respond"
    SEQ_25_DIALOG_RESPONDING_ACTIVE = "25_dialog_responding_active"
    SEQ_26_RESPONDING_STARTED_ACTIVE = "26_responding_started_active"
    SEQ_27_LOCAL_RESPONDING_STARTED_ACTIVE = "27_local_responding_started_active"
    SEQ_28_PLAY_AUDIO_ACTIVE = "28_play_audio_active"
    SEQ_29_RESPONDING_ENDED_ACTIVE = "29_responding_ended_active"
    SEQ_30_LOCAL_RESPONDING_ENDED_ACTIVE = "30_local_responding_ended_active"
    SEQ_31_DIALOG_LISTENING_ACTIVE = "31_dialog_listening_active"
    
    # 系统停止阶段
    SEQ_32_USER_LEAVE = "32_user_leave"
    SEQ_33_SYSTEM_STOP = "33_system_stop"
    SEQ_34_SYSTEM_STOPPED = "34_system_stopped"


class MessageDirection(Enum):
    """消息方向枚举"""
    TO_SERVER = ">>>>>>>>> TO SERVER"
    FROM_SERVER = "<<<<<<<<< FROM SERVER"
    CLIENT_INTERNAL = "CLIENT INTERNAL"
    USER_ACTION = "USER ACTION"


# 通信序列对应的日志文本字典
COMMUNICATION_SEQUENCE_LOGS: Dict[CommunicationSequence, Dict[str, str]] = {
    # 系统启动阶段
    CommunicationSequence.SEQ_01_SYSTEM_START: {
        "direction": MessageDirection.TO_SERVER.value,
        "message": "启动系统通信",
        "details": "客户端向服务器发送启动请求"
    },
    CommunicationSequence.SEQ_02_SYSTEM_STARTED: {
        "direction": MessageDirection.FROM_SERVER.value,
        "message": "系统启动成功",
        "details": "服务器确认系统已启动"
    },
    
    # 全双工场景 - 对话准备
    CommunicationSequence.SEQ_03_DIALOG_LISTENING: {
        "direction": MessageDirection.CLIENT_INTERNAL.value,
        "message": "对话状态: 监听中",
        "details": "客户端进入监听状态，等待用户语音输入"
    },
    CommunicationSequence.SEQ_04_AUDIO_SILENCE: {
        "direction": MessageDirection.TO_SERVER.value,
        "message": "发送静音音频",
        "details": "客户端向服务器发送静音音频流"
    },
    CommunicationSequence.SEQ_05_USER_SPEAK: {
        "direction": MessageDirection.USER_ACTION.value,
        "message": "用户说话",
        "details": "用户开始说话"
    },
    CommunicationSequence.SEQ_06_AUDIO_SPEECH: {
        "direction": MessageDirection.TO_SERVER.value,
        "message": "发送语音音频",
        "details": "客户端向服务器发送用户语音音频流"
    },
    
    # 语音识别阶段
    CommunicationSequence.SEQ_07_VAD_ON: {
        "direction": MessageDirection.FROM_SERVER.value,
        "message": "语音活动检测开启",
        "details": "服务器开启语音活动检测"
    },
    CommunicationSequence.SEQ_08_SPEECH_STARTED: {
        "direction": MessageDirection.FROM_SERVER.value,
        "message": "语音识别开始",
        "details": "服务器确认开始识别用户语音"
    },
    CommunicationSequence.SEQ_09_SPEECH_CONTENT: {
        "direction": MessageDirection.FROM_SERVER.value,
        "message": "语音识别内容",
        "details": "服务器返回识别的语音内容"
    },
    CommunicationSequence.SEQ_10_SPEECH_ENDED: {
        "direction": MessageDirection.FROM_SERVER.value,
        "message": "语音识别结束",
        "details": "服务器确认语音识别完成"
    },
    
    # 响应准备阶段
    CommunicationSequence.SEQ_11_DIALOG_THINKING: {
        "direction": MessageDirection.CLIENT_INTERNAL.value,
        "message": "对话状态: 思考中",
        "details": "客户端进入思考状态，处理用户输入"
    },
    CommunicationSequence.SEQ_12_RESPONDING_CONTENT: {
        "direction": MessageDirection.FROM_SERVER.value,
        "message": "响应内容",
        "details": "服务器返回系统响应内容"
    },
    CommunicationSequence.SEQ_13_DIALOG_RESPONDING: {
        "direction": MessageDirection.CLIENT_INTERNAL.value,
        "message": "对话状态: 响应中",
        "details": "客户端进入响应状态，播放系统回复"
    },
    CommunicationSequence.SEQ_14_RESPONDING_STARTED: {
        "direction": MessageDirection.FROM_SERVER.value,
        "message": "响应开始",
        "details": "服务器确认开始生成响应"
    },
    CommunicationSequence.SEQ_15_LOCAL_RESPONDING_STARTED: {
        "direction": MessageDirection.TO_SERVER.value,
        "message": "本地响应开始",
        "details": "客户端通知服务器本地响应播放开始"
    },
    
    # 正常播放场景
    CommunicationSequence.SEQ_16_PLAY_AUDIO: {
        "direction": MessageDirection.CLIENT_INTERNAL.value,
        "message": "播放音频",
        "details": "客户端播放音频给用户"
    },
    CommunicationSequence.SEQ_17_RESPONDING_ENDED: {
        "direction": MessageDirection.FROM_SERVER.value,
        "message": "响应结束",
        "details": "服务器确认响应生成完成"
    },
    CommunicationSequence.SEQ_18_LOCAL_RESPONDING_ENDED: {
        "direction": MessageDirection.TO_SERVER.value,
        "message": "本地响应结束",
        "details": "客户端通知服务器本地响应播放结束"
    },
    CommunicationSequence.SEQ_19_DIALOG_LISTENING_AGAIN: {
        "direction": MessageDirection.CLIENT_INTERNAL.value,
        "message": "对话状态: 重新监听",
        "details": "客户端重新进入监听状态"
    },
    
    # 用户打断场景
    CommunicationSequence.SEQ_20_USER_INTERRUPT: {
        "direction": MessageDirection.USER_ACTION.value,
        "message": "用户打断",
        "details": "用户在系统响应过程中打断"
    },
    CommunicationSequence.SEQ_21_REQUEST_ACCEPTED: {
        "direction": MessageDirection.FROM_SERVER.value,
        "message": "请求已接受",
        "details": "服务器接受用户打断请求"
    },
    CommunicationSequence.SEQ_22_DIALOG_LISTENING_INTERRUPT: {
        "direction": MessageDirection.CLIENT_INTERNAL.value,
        "message": "对话状态: 监听中(打断后)",
        "details": "用户打断后客户端重新进入监听状态"
    },
    CommunicationSequence.SEQ_23_SPEECH_STARTED_INTERRUPT: {
        "direction": MessageDirection.FROM_SERVER.value,
        "message": "语音识别开始(打断后)",
        "details": "用户打断后服务器重新开始语音识别"
    },
    
    # 主动互动场景
    CommunicationSequence.SEQ_24_REQUEST_TO_RESPOND: {
        "direction": MessageDirection.FROM_SERVER.value,
        "message": "主动响应请求",
        "details": "服务器主动发起响应请求"
    },
    CommunicationSequence.SEQ_25_DIALOG_RESPONDING_ACTIVE: {
        "direction": MessageDirection.CLIENT_INTERNAL.value,
        "message": "对话状态: 响应中(主动)",
        "details": "服务器主动发起响应，客户端进入响应状态"
    },
    CommunicationSequence.SEQ_26_RESPONDING_STARTED_ACTIVE: {
        "direction": MessageDirection.FROM_SERVER.value,
        "message": "响应开始(主动)",
        "details": "服务器主动确认开始生成响应"
    },
    CommunicationSequence.SEQ_27_LOCAL_RESPONDING_STARTED_ACTIVE: {
        "direction": MessageDirection.TO_SERVER.value,
        "message": "本地响应开始(主动)",
        "details": "客户端通知服务器本地响应播放开始(主动)"
    },
    CommunicationSequence.SEQ_28_PLAY_AUDIO_ACTIVE: {
        "direction": MessageDirection.CLIENT_INTERNAL.value,
        "message": "播放音频(主动)",
        "details": "客户端播放服务器主动发起的音频"
    },
    CommunicationSequence.SEQ_29_RESPONDING_ENDED_ACTIVE: {
        "direction": MessageDirection.FROM_SERVER.value,
        "message": "响应结束(主动)",
        "details": "服务器主动响应生成完成"
    },
    CommunicationSequence.SEQ_30_LOCAL_RESPONDING_ENDED_ACTIVE: {
        "direction": MessageDirection.TO_SERVER.value,
        "message": "本地响应结束(主动)",
        "details": "客户端通知服务器本地响应播放结束(主动)"
    },
    CommunicationSequence.SEQ_31_DIALOG_LISTENING_ACTIVE: {
        "direction": MessageDirection.CLIENT_INTERNAL.value,
        "message": "对话状态: 监听中(主动后)",
        "details": "主动互动后客户端重新进入监听状态"
    },
    
    # 系统停止阶段
    CommunicationSequence.SEQ_32_USER_LEAVE: {
        "direction": MessageDirection.USER_ACTION.value,
        "message": "用户离开",
        "details": "用户离开界面或挂断"
    },
    CommunicationSequence.SEQ_33_SYSTEM_STOP: {
        "direction": MessageDirection.TO_SERVER.value,
        "message": "停止系统通信",
        "details": "客户端向服务器发送停止请求"
    },
    CommunicationSequence.SEQ_34_SYSTEM_STOPPED: {
        "direction": MessageDirection.FROM_SERVER.value,
        "message": "系统已停止",
        "details": "服务器确认系统已停止"
    }
}


# 场景分组定义
SCENARIO_GROUPS = {
    "系统启动": [
        CommunicationSequence.SEQ_01_SYSTEM_START,
        CommunicationSequence.SEQ_02_SYSTEM_STARTED
    ],
    "全双工对话": [
        CommunicationSequence.SEQ_03_DIALOG_LISTENING,
        CommunicationSequence.SEQ_04_AUDIO_SILENCE,
        CommunicationSequence.SEQ_05_USER_SPEAK,
        CommunicationSequence.SEQ_06_AUDIO_SPEECH,
        CommunicationSequence.SEQ_07_VAD_ON,
        CommunicationSequence.SEQ_08_SPEECH_STARTED,
        CommunicationSequence.SEQ_09_SPEECH_CONTENT,
        CommunicationSequence.SEQ_10_SPEECH_ENDED,
        CommunicationSequence.SEQ_11_DIALOG_THINKING,
        CommunicationSequence.SEQ_12_RESPONDING_CONTENT,
        CommunicationSequence.SEQ_13_DIALOG_RESPONDING,
        CommunicationSequence.SEQ_14_RESPONDING_STARTED,
        CommunicationSequence.SEQ_15_LOCAL_RESPONDING_STARTED
    ],
    "正常播放": [
        CommunicationSequence.SEQ_16_PLAY_AUDIO,
        CommunicationSequence.SEQ_17_RESPONDING_ENDED,
        CommunicationSequence.SEQ_18_LOCAL_RESPONDING_ENDED,
        CommunicationSequence.SEQ_19_DIALOG_LISTENING_AGAIN
    ],
    "用户打断": [
        CommunicationSequence.SEQ_20_USER_INTERRUPT,
        CommunicationSequence.SEQ_21_REQUEST_ACCEPTED,
        CommunicationSequence.SEQ_22_DIALOG_LISTENING_INTERRUPT,
        CommunicationSequence.SEQ_23_SPEECH_STARTED_INTERRUPT
    ],
    "主动互动": [
        CommunicationSequence.SEQ_24_REQUEST_TO_RESPOND,
        CommunicationSequence.SEQ_25_DIALOG_RESPONDING_ACTIVE,
        CommunicationSequence.SEQ_26_RESPONDING_STARTED_ACTIVE,
        CommunicationSequence.SEQ_27_LOCAL_RESPONDING_STARTED_ACTIVE,
        CommunicationSequence.SEQ_28_PLAY_AUDIO_ACTIVE,
        CommunicationSequence.SEQ_29_RESPONDING_ENDED_ACTIVE,
        CommunicationSequence.SEQ_30_LOCAL_RESPONDING_ENDED_ACTIVE,
        CommunicationSequence.SEQ_31_DIALOG_LISTENING_ACTIVE
    ],
    "系统停止": [
        CommunicationSequence.SEQ_32_USER_LEAVE,
        CommunicationSequence.SEQ_33_SYSTEM_STOP,
        CommunicationSequence.SEQ_34_SYSTEM_STOPPED
    ]
}