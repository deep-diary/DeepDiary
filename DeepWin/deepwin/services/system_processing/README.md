# System Processing Package

## 简介

系统信息处理包,用于获取和监控系统硬件信息、网络状态等。

## 主要功能

### 1. 硬件信息

```python
from system_processing.manager import SystemManager

manager = SystemManager()

# 获取CPU信息
cpu_info = manager.get_specific_info('hardware')['cpu']
print(f"CPU: {cpu_info['processor']}")
print(f"Cores: {cpu_info['cores']}")

# 获取GPU信息
gpu_info = manager.get_specific_info('hardware')['gpu']
print(f"GPU: {gpu_info['device_name']}")

# 获取内存信息
memory_info = manager.get_specific_info('hardware')['memory']
print(f"Total Memory: {memory_info['total']} GB")
```

### 2. 网络信息

```python
# 获取网络状态
network_info = manager.get_specific_info('network')
print(f"IP: {network_info['ip']}")
print(f"MAC: {network_info['mac']}")
```

### 3. 环境信息

```python
# 获取系统环境信息
env_info = manager.get_specific_info('environment')
print(f"OS: {env_info['os']['system']}")
print(f"Python: {env_info['python']['version']}")
```

## 返回信息格式

### 硬件信息

```python
{
    'cpu': {
        'processor': str,
        'cores': int,
        'threads': int,
        'frequency': float
    },
    'gpu': {
        'available': bool,
        'device_count': int,
        'device_name': str,
        'cuda_version': str
    },
    'memory': {
        'total': int,
        'available': int,
        'percent': float
    }
}
```

### 网络信息

```python
{
    'ip': str,
    'mac': str,
    'hostname': str,
    'location': {
        'city': str,
        'region': str,
        'country': str,
        'lat': float,
        'lon': float
    }
}
```

## 配置说明

```json
{
  "hardware": {
    "cpu": {
      "show_details": true,
      "monitor_frequency": 1.0
    },
    "gpu": {
      "show_details": true,
      "monitor_memory": true
    }
  },
  "network": {
    "ip_location": {
      "enable": true,
      "timeout": 5
    }
  }
}
```

## 注意事项

1. GPU 信息需要 CUDA 支持
2. 网络定位需要联网
3. 部分信息需要管理员权限
