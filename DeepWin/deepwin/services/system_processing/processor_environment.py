from .base import SystemProcessorBase
import os
import platform

class EnvironmentProcessor(SystemProcessorBase):
    def process(self):
        # 操作系统信息
        self.environment_info['os'] = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine()
        }

        # 环境变量
        self.environment_info['env_vars'] = dict(os.environ)

        # Python 版本
        self.environment_info['python'] = {
            'version': platform.python_version(),
            'implementation': platform.python_implementation()
        }

        return self.environment_info 