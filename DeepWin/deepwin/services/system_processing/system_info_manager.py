#!/usr/bin/env python3
"""
System Info Manager Module

Handles system information retrieval and user account management
"""

import logging
import platform
import socket
import uuid
import psutil
from typing import Dict, Any, Optional
import requests

class SystemInfoManager:
    """系统信息管理器，获取系统信息和用户账户信息"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache = {}
        self.cache_timeout = 300  # 5分钟缓存
    
    def get_system_info(self) -> Dict[str, Any]:
        """获取基本系统信息"""
        try:
            info = {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'architecture': platform.architecture()[0],
                'processor': platform.processor(),
                'hostname': socket.gethostname(),
                'python_version': platform.python_version()
            }
            
            # 获取内存信息
            memory = psutil.virtual_memory()
            info['memory'] = {
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent
            }
            
            # 获取磁盘信息
            disk = psutil.disk_usage('/')
            info['disk'] = {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取系统信息失败: {e}")
            return {}
    
    def get_network_info(self) -> Dict[str, Any]:
        """获取网络信息"""
        try:
            info = {}
            
            # 获取本机IP地址
            hostname = socket.gethostname()
            local_ip = socket.gethostbyname(hostname)
            info['local_ip'] = local_ip
            
            # 获取MAC地址
            mac_address = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                                  for elements in range(0,2*6,2)][::-1])
            info['mac_address'] = mac_address
            
            # 获取网络接口信息
            network_interfaces = psutil.net_if_addrs()
            info['interfaces'] = {}
            for interface, addresses in network_interfaces.items():
                info['interfaces'][interface] = []
                for addr in addresses:
                    info['interfaces'][interface].append({
                        'family': str(addr.family),
                        'address': addr.address,
                        'netmask': addr.netmask
                    })
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取网络信息失败: {e}")
            return {}
    
    def get_location_by_ip(self, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """通过IP地址获取地理位置信息"""
        try:
            if not ip_address:
                # 如果没有提供IP，使用本机IP
                hostname = socket.gethostname()
                ip_address = socket.gethostbyname(hostname)
            
            # 使用免费的IP地理位置API
            url = f"http://ip-api.com/json/{ip_address}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    return {
                        'ip': data.get('query'),
                        'country': data.get('country'),
                        'region': data.get('regionName'),
                        'city': data.get('city'),
                        'latitude': data.get('lat'),
                        'longitude': data.get('lon'),
                        'timezone': data.get('timezone'),
                        'isp': data.get('isp')
                    }
            
            return {}
            
        except Exception as e:
            self.logger.error(f"获取地理位置信息失败: {e}")
            return {}
    
    def get_user_account_info(self) -> Dict[str, Any]:
        """获取用户账户信息"""
        try:
            info = {
                'username': platform.node(),
                'home_directory': str(psutil.users()[0].home) if psutil.users() else None,
                'user_id': psutil.users()[0].name if psutil.users() else None,
                'login_time': str(psutil.users()[0].started) if psutil.users() else None
            }
            
            return info
            
        except Exception as e:
            self.logger.error(f"获取用户账户信息失败: {e}")
            return {}
    
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        try:
            health = {
                'cpu_usage': psutil.cpu_percent(interval=1),
                'memory_usage': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent,
                'network_status': self._check_network_status()
            }
            
            return health
            
        except Exception as e:
            self.logger.error(f"获取系统健康状态失败: {e}")
            return {}
    
    def _check_network_status(self) -> str:
        """检查网络状态"""
        try:
            # 尝试连接Google DNS
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return "online"
        except OSError:
            return "offline"
    
    def get_all_info(self) -> Dict[str, Any]:
        """获取所有系统信息"""
        return {
            'system': self.get_system_info(),
            'network': self.get_network_info(),
            'location': self.get_location_by_ip(),
            'user': self.get_user_account_info(),
            'health': self.get_system_health()
        }
