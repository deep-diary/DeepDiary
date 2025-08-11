import sounddevice as sd
import numpy as np
import soundfile as sf

# 采样率
fs = 44100
# 持续时间（秒）
duration = 5

# # 回调函数
# def callback(indata, outdata, frames, time, status):
#     if status:
#         print(status)
#     # 在此处处理音频数据
#     outdata[:] = indata  # 直接将输入数据复制到输出数据中，形成回声

# # 打开音频流
# with sd.Stream(callback=callback, samplerate=fs, channels=2) as stream:
#     # 准备开始录制五秒音频
#     sd.sleep(int(duration * 1000))  # 暂停主线程，允许音频流处理音频数据


#--------------------------------------------------------
# # 回调函数处理录音数据
# def callback(indata, frames, time, status):
#     if status:
#         print(status)
#     print(time.currentTime,frames) # ['currentTime', 'inputBufferAdcTime', 'outputBufferDacTime']

# # 创建 InputStream 对象
# stream = sd.InputStream(callback=callback)

# # 开始录音
# with stream:
#     sd.sleep(5000)  # 录音 5 秒钟


#--------------------------------------------------------
# 生成一秒钟的随机噪音
# fs = 44100  # 采样率
# duration = 5  # 持续时间（秒）
# # 生成一秒钟的随机噪音，并确保数据类型为 float32 以避免 dtype mismatch 错误
# data = np.random.uniform(-1, 1, fs*duration).astype(np.float32)

# # 创建输出流
# stream = sd.OutputStream(samplerate=fs, channels=1)

# # 启动输出流并播放数据
# with stream:
#     stream.write(data)


#--------------------------------------------------------
# fs = 44100  # 采样率
# f = 100     # 频率, Hz
# seconds = 1 # 持续时间秒
# dataList = []
# # 生成7个不同频率的正弦波，并将其拼接在一起
# for i in range(7):
#     t = np.linspace(0, seconds, int(fs*seconds), endpoint=False)
#     data = np.sin(2 * np.pi * f * t).astype(np.float32)
#     dataList.append(data)
#     f=f*2

# data = np.concatenate(dataList)
# sd.play(data, samplerate=fs)
# sd.wait()  # 等待直到数据播放完成

#--------------------------------------------------------
# 录制
# print('开始录制')
# myrecording = sd.rec(int(duration * fs), samplerate=fs, channels=2, dtype='float32')
# sd.wait()
# print('录制完成')
# sd.play(myrecording, samplerate=fs)
# sd.wait()
# print('播放完成')

#--------------------------------------------------------
# frequency = 440  # 频率（Hz）
# samples = (np.sin(2 * np.pi * np.arange(fs * duration) * frequency / fs)).astype(np.float32)

# # 播放并录制音频
# myrecording = sd.playrec(samples, samplerate=fs, channels=2, dtype='float32')
# sd.wait()  # 等待直到数据播放和录制完成

#--------------------------------------------------------
# devices = sd.query_devices()
# print(devices)

# default_output_device = sd.query_devices(kind='output')
# print(f'default_output_device:{default_output_device}\n')

# default_input_device = sd.query_devices(kind='input')
# print(f'default_input_device:{default_input_device}\n')

# hostapis = sd.query_hostapis()
# print(f'hostapis:{hostapis}\n')

# default_hostapi = sd.query_hostapis(sd.default.hostapi)
# print(f'default_hostapi:{default_hostapi}\n')

# print(f'default_output_device:{dir(sd.default)}\n')

# print(f'default_device:{sd.default.device}\n')
# print(f'default_blocksize:{sd.default.blocksize}\n')
# print(f'default_channels:{sd.default.channels}\n')
# print(f'default_samplerate:{sd.default.samplerate}\n')
# print(f'default_hostapi:{sd.default.hostapi}\n')

#--------------------------------------------------------
# 
import numpy as np
import sounddevice as sd
from scipy.io import wavfile

# 音符频率映射（国际标准音高）
note_freq = {
    'C4': 261.63, 'C#4': 277.18, 'D4': 293.66, 'D#4': 311.13,
    'E4': 329.63, 'F4': 349.23, 'F#4': 369.99, 'G4': 392.00,
    'G#4': 415.30, 'A4': 440.00, 'A#4': 466.16, 'B4': 493.88,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'F5': 698.46,
    'G5': 783.99, 'A5': 880.00
}

# 青花瓷完整钢琴谱（简谱转音名）
melody = [
    ('D4',0.3), ('C4',0.3), ('A4',0.3), ('C4',0.6),  # 前奏
    ('C4',0.2), ('A4',0.2), ('C4',0.2), ('A4',0.2), ('G4',0.6),
    ('E4',0.4), ('G4',0.4), ('E4',0.4), ('D4',0.4),  # 主歌
    ('C4',0.8), ('D4',0.4), ('E4',0.4), ('G4',0.8),
    ('A4',0.4), ('G4',0.4), ('E4',0.4), ('D4',0.8),
    ('C4',0.4), ('D4',0.4), ('E4',0.4), ('G4',0.4),
    ('A4',0.8), ('G5',0.4), ('E5',0.4), ('D5',0.8),  # 副歌
    ('C5',0.4), ('A4',0.4), ('G4',0.4), ('E4',0.4),
    ('D4',0.8), ('C4',0.4), ('D4',0.4), ('E4',0.4)
]

def generate_note(note, duration, fs=44100):
    t = np.linspace(0, duration, int(fs*duration), False)
    wave = 0.3 * np.sin(2*np.pi*note_freq[note]*t)  # 主音
    wave += 0.1 * np.sin(2*np.pi*note_freq[note]*2*t)  # 泛音
    return wave * np.hanning(len(wave))  # 加窗函数

def play_melody():
    fs = 44100
    audio = np.array([], dtype=np.float32)
    
    for note, duration in melody:
        wave = generate_note(note, duration, fs)
        audio = np.concatenate((audio, wave))
    
    # 添加淡出效果
    fade_samples = 2000
    audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    
    # 播放并保存
    sd.play(audio, fs)
    sd.wait()
    # wavfile.write('qinghuaci.wav', fs, audio)
    sf.write('qinghuaci.wav', audio, fs)

if __name__ == "__main__":
    play_melody()







