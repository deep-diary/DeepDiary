from abc import ABC, abstractmethod
import platform
import psutil
import uuid
import socket
import requests
import torch
import os

class SystemProcessorBase(ABC):
    def __init__(self):
        self.system_info = {}
        self.network_info = {}
        self.hardware_info = {}
        self.environment_info = {}

    @abstractmethod
    def process(self):
        """Process system information"""
        pass

    def get_system_info(self):
        """Return collected system information"""
        return self.system_info 