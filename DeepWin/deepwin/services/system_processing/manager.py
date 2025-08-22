from .processor_hardware import HardwareProcessor
from .processor_network import NetworkProcessor
from .processor_environment import EnvironmentProcessor

class SystemManager:
    def __init__(self):
        self.processors = {
            'hardware': HardwareProcessor(),
            'network': NetworkProcessor(),
            'environment': EnvironmentProcessor()
        }

    def get_processor(self, processor_name):
        return self.processors.get(processor_name)

    def get_system_info(self):
        """获取所有系统信息"""
        system_info = {}
        for name, processor in self.processors.items():
            system_info[name] = processor.process()
        return system_info

    def get_specific_info(self, processor_name):
        """获取特定类型的系统信息"""
        processor = self.get_processor(processor_name)
        if processor:
            return processor.process()
        raise ValueError(f"Processor '{processor_name}' not found.") 