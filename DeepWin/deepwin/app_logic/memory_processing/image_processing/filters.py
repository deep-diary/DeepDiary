import numpy as np
from collections import deque
from filterpy.kalman import KalmanFilter
from filterpy.common import Q_discrete_white_noise
from scipy.signal import butter, filtfilt
from abc import ABC, abstractmethod

class SignalFilter(ABC):
    """信号滤波器基类"""
    def __init__(self):
        pass
    
    @abstractmethod
    def update(self, value):
        """更新并返回滤波后的值"""
        pass
    
    @abstractmethod
    def reset(self):
        """重置滤波器状态"""
        pass

class MeanFilter(SignalFilter):
    """均值滤波器"""
    def __init__(self, window_size=3):
        super().__init__()
        self.window_size = window_size
        self.values = deque(maxlen=window_size)
        
    def update(self, value):
        if value is None:
            return None
        self.values.append(float(value))
        return np.mean(self.values)
    
    def reset(self):
        self.values.clear()

class MedianFilter(SignalFilter):
    """中值滤波器"""
    def __init__(self, window_size=3):
        super().__init__()
        self.window_size = window_size
        self.values = deque(maxlen=window_size)
        
    def update(self, value):
        if value is None:
            return None
        self.values.append(float(value))
        return np.median(self.values)
    
    def reset(self):
        self.values.clear()

class KalmanFilter1D(SignalFilter):
    """一维卡尔曼滤波器"""
    def __init__(self, process_variance=0.1, measurement_variance=1.0):
        super().__init__()
        self.kf = KalmanFilter(dim_x=2, dim_z=1)  # 状态：[位置, 速度]
        self.kf.x = np.array([0., 0.])  # 初始状态
        self.kf.F = np.array([[1., 1.],  # 状态转移矩阵
                             [0., 1.]])
        self.kf.H = np.array([[1., 0.]])  # 测量矩阵
        self.kf.P *= 1000.  # 初始协方差
        self.kf.R = measurement_variance  # 测量噪声
        self.kf.Q = Q_discrete_white_noise(2, dt=1., var=process_variance)  # 过程噪声
        self.initialized = False
        
    def update(self, value):
        if value is None:
            return None
            
        if not self.initialized:
            self.kf.x[0] = value
            self.initialized = True
            return value
            
        self.kf.predict()
        self.kf.update(value)
        return float(self.kf.x[0])
    
    def reset(self):
        self.kf.x = np.array([0., 0.])
        self.kf.P *= 1000.
        self.initialized = False

class LowPassFilter(SignalFilter):
    """低通滤波器"""
    def __init__(self, cutoff_freq=0.5, fs=30.0, order=2):
        super().__init__()
        nyq = fs * 0.5
        normal_cutoff = cutoff_freq / nyq
        self.b, self.a = butter(order, normal_cutoff, btype='low', analog=False)
        self.values = deque(maxlen=max(len(self.a), len(self.b)) * 2)
        
    def update(self, value):
        if value is None:
            return None
        self.values.append(float(value))
        if len(self.values) >= 3:  # 至少需要3个点
            return filtfilt(self.b, self.a, list(self.values))[-1]
        return value
    
    def reset(self):
        self.values.clear()

class FilterChain:
    """滤波器链，可以组合多个滤波器"""
    def __init__(self, filters=None):
        self.filters = filters or []
    
    def add_filter(self, filter_obj):
        self.filters.append(filter_obj)
    
    def update(self, value):
        for filter_obj in self.filters:
            value = filter_obj.update(value)
        return value
    
    def reset(self):
        for filter_obj in self.filters:
            filter_obj.reset() 