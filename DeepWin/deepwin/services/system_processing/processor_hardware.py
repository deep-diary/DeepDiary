from .base import SystemProcessorBase
import psutil
import platform
import cpuinfo
import torch

class HardwareProcessor(SystemProcessorBase):
    def process(self):
        # CPU 信息
        cpu_info = cpuinfo.get_cpu_info()
        self.hardware_info['cpu'] = {
            'processor': cpu_info['brand_raw'],
            'cores': psutil.cpu_count(logical=False),
            'threads': psutil.cpu_count(logical=True),
            'frequency': psutil.cpu_freq().current
        }

        # GPU 信息
        self.hardware_info['gpu'] = {
            'available': torch.cuda.is_available(),
            'device_count': torch.cuda.device_count() if torch.cuda.is_available() else 0,
            'device_name': torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
            'cuda_version': torch.version.cuda if torch.cuda.is_available() else None
        }

        # 内存信息
        memory = psutil.virtual_memory()
        self.hardware_info['memory'] = {
            'total': memory.total,
            'available': memory.available,
            'percent': memory.percent
        }

        return self.hardware_info 