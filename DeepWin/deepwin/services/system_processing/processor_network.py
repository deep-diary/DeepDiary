from .base import SystemProcessorBase
import uuid
import socket
import requests

class NetworkProcessor(SystemProcessorBase):
    def process(self):
        # MAC 地址
        self.network_info['mac'] = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff)
                                           for elements in range(0,2*6,2)][::-1])

        # IP 地址
        hostname = socket.gethostname()
        self.network_info['hostname'] = hostname
        self.network_info['ip'] = socket.gethostbyname(hostname)

        # IP 地理位置信息
        try:
            response = requests.get(f"http://ip-api.com/json/{self.network_info['ip']}")
            if response.status_code == 200:
                location_data = response.json()
                self.network_info['location'] = {
                    'city': location_data.get('city'),
                    'region': location_data.get('regionName'),
                    'country': location_data.get('country'),
                    'lat': location_data.get('lat'),
                    'lon': location_data.get('lon')
                }
        except Exception as e:
            self.network_info['location'] = str(e)

        return self.network_info 