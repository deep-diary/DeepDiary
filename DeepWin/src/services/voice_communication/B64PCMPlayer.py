import contextlib
import time
import pyaudio
import threading
import queue
import base64

class B64PCMPlayer:
    """
    Base64编码的PCM音频播放器
    支持实时音频流播放，使用多线程处理音频解码和播放
    """
    
    def __init__(self, pya: pyaudio.PyAudio, sample_rate=24000, chunk_size_ms=100, save_file=False):
        '''
        初始化音频播放器
        
        参数:
        pya: pyaudio.PyAudio - PyAudio实例
        sample_rate: int - 音频采样率，默认24000Hz
        chunk_size_ms: int - 音频块大小（毫秒），影响取消延迟
        save_file: bool - 是否保存音频文件，默认False
        '''

        self.pya = pya
        self.sample_rate = sample_rate
        # 计算每个音频块的字节数：采样率 * 2字节(16位) * 时间(毫秒) / 1000
        self.chunk_size_bytes = chunk_size_ms * sample_rate *2 // 1000
        
        # 初始化PyAudio输出流，用于播放音频
        self.player_stream = pya.open(format=pyaudio.paInt16,
                channels=1,  # 单声道
                rate=sample_rate,  # 采样率
                output=True)  # 输出模式

        # 创建两个队列用于线程间通信
        self.raw_audio_buffer: queue.Queue = queue.Queue()  # 存储解码后的原始音频数据
        self.b64_audio_buffer: queue.Queue = queue.Queue()  # 存储Base64编码的音频数据
        
        # 线程锁，用于保护状态变量
        self.status_lock = threading.Lock()
        self.status = 'playing'  # 播放状态：playing/stop
        
        # 创建解码线程和播放线程
        self.decoder_thread = threading.Thread(target=self.decoder_loop, daemon=True)
        self.player_thread = threading.Thread(target=self.player_loop, daemon=True)
        
        # 启动线程
        self.decoder_thread.start()
        self.player_thread.start()
        
        # 完成事件，用于同步
        self.complete_event = threading.Event()
        
        # 文件保存相关
        self.save_file = save_file
        if self.save_file:
            self.out_file = open('result.pcm', 'wb')

    def decoder_loop(self):
        """
        解码循环线程
        从Base64队列获取数据，解码后放入原始音频队列
        """
        while self.status != 'stop':
            recv_audio_b64 = None
            
            # 使用contextlib.suppress抑制queue.Empty异常
            # 当队列为空时，get(timeout=0.1)会抛出queue.Empty异常
            # suppress会捕获这个异常并继续执行，而不是让程序崩溃
            with contextlib.suppress(queue.Empty):
                recv_audio_b64 = self.b64_audio_buffer.get(timeout=0.1)
            
            if recv_audio_b64 is None:
                continue
                
            # Base64解码音频数据
            recv_audio_raw = base64.b64decode(recv_audio_b64)
            
            # 将解码后的音频数据按块大小分割并放入队列
            for i in range(0, len(recv_audio_raw), self.chunk_size_bytes):
                chunk = recv_audio_raw[i:i + self.chunk_size_bytes]
                
                # 如果最后一个块不完整，用零填充到完整大小
                if len(chunk) < self.chunk_size_bytes:
                    # chunk = chunk + b'\x00' * (self.chunk_size_bytes - len(chunk))
                    print(f"decoder_loop chunk: {len(chunk)}")
                
                self.raw_audio_buffer.put(chunk)
                if self.save_file:
                    self.out_file.write(chunk)

    def player_loop(self):
        """
        播放循环线程
        从原始音频队列获取数据并播放
        """
        while self.status != 'stop':
            recv_audio_raw = None
            
            # 同样使用suppress处理队列为空的情况
            with contextlib.suppress(queue.Empty):
                recv_audio_raw = self.raw_audio_buffer.get(timeout=0.1)
                
            if recv_audio_raw is None:
                # 如果没有更多数据且设置了完成事件，则设置事件
                if self.complete_event:
                    self.complete_event.set()
                continue
                
            # 将音频块写入PyAudio播放流，等待播放完成
            self.player_stream.write(recv_audio_raw)

    def cancel_playing(self):
        """
        取消播放
        清空所有音频队列
        """
        self.b64_audio_buffer.queue.clear()
        self.raw_audio_buffer.queue.clear()

    def add_data(self, data):
        """
        添加Base64编码的音频数据到队列
        
        参数:
        data: str - Base64编码的音频数据
        """
        self.b64_audio_buffer.put(data)

    def add_byte_data(self, byte_data):
        """
        直接添加字节流音频数据到原始音频队列
        跳过Base64解码步骤，提高处理效率
        
        参数:
        byte_data: bytes - 原始音频字节数据
        """
        # 将字节数据按块大小分割并直接放入原始音频队列
        for i in range(0, len(byte_data), self.chunk_size_bytes):
            chunk = byte_data[i:i + self.chunk_size_bytes]
            
            # 如果最后一个块不完整，用零填充到完整大小
            # 这样可以确保所有数据都被处理，不会丢失
            if len(chunk) < self.chunk_size_bytes:
                # 用零填充最后一个不完整的块
                # chunk = chunk + b'\x00' * (self.chunk_size_bytes - len(chunk))
                print(f"add_byte_data chunk: {len(chunk)}")
            
            self.raw_audio_buffer.put(chunk)
            
            # 如果启用了文件保存，也保存到文件
            if self.save_file:
                self.out_file.write(chunk)

    def wait_for_complete(self):
        """
        等待播放完成
        创建一个事件对象，等待播放线程完成
        """
        self.complete_event = threading.Event()
        self.complete_event.wait()  # 阻塞直到事件被设置
        self.complete_event = None

    def shutdown(self):
        """
        关闭播放器
        停止所有线程并释放资源
        """
        self.status = 'stop'
        
        # self.decoder_thread.join() 的含义：
        # join()方法会阻塞当前线程，直到被调用的线程执行完毕
        # 这里等待解码线程和播放线程完全结束，确保所有资源都被正确释放
        # 如果不调用join()，主线程可能会在子线程还在运行时退出，导致资源泄漏
        self.decoder_thread.join()
        self.player_thread.join()
        
        # 关闭音频流
        self.player_stream.close()
        
        # 如果启用了文件保存，关闭文件
        if self.save_file:
            self.out_file.close()