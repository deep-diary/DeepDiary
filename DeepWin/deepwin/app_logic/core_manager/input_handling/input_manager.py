#!/usr/bin/env python3
"""
Input Manager Module

Handles keyboard input and input event management
"""

import logging
from typing import Dict, Any, Callable, Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QKeyEvent

class InputManager(QObject):
    """输入管理器，处理键盘输入和输入事件"""
    
    # 信号定义
    key_pressed = Signal(str)  # 按键按下信号
    key_released = Signal(str)  # 按键释放信号
    input_sequence = Signal(list)  # 输入序列信号
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.key_handlers: Dict[str, Callable] = {}
        self.input_buffer = []
        self.is_recording = False
        
    def register_key_handler(self, key: str, handler: Callable) -> bool:
        """注册按键处理器"""
        try:
            self.key_handlers[key] = handler
            self.logger.info(f"注册按键处理器: {key}")
            return True
        except Exception as e:
            self.logger.error(f"注册按键处理器失败: {e}")
            return False
    
    def handle_key_event(self, event: QKeyEvent) -> bool:
        """处理按键事件"""
        try:
            key_text = event.text()
            key_code = event.key()
            
            if event.type() == QKeyEvent.Type.KeyPress:
                self.key_pressed.emit(key_text)
                self._process_key_press(key_text, key_code)
            elif event.type() == QKeyEvent.Type.KeyRelease:
                self.key_released.emit(key_text)
            
            return True
            
        except Exception as e:
            self.logger.error(f"处理按键事件失败: {e}")
            return False
    
    def _process_key_press(self, key_text: str, key_code: int):
        """处理按键按下事件"""
        if self.is_recording:
            self.input_buffer.append(key_text)
            if len(self.input_buffer) >= 10:  # 限制缓冲区大小
                self.input_sequence.emit(self.input_buffer.copy())
                self.input_buffer.clear()
        
        # 调用注册的处理器
        if key_text in self.key_handlers:
            try:
                self.key_handlers[key_text]()
            except Exception as e:
                self.logger.error(f"执行按键处理器失败: {e}")
    
    def start_recording(self):
        """开始记录输入"""
        self.is_recording = True
        self.input_buffer.clear()
        self.logger.info("开始记录输入")
    
    def stop_recording(self) -> list:
        """停止记录输入并返回缓冲区内容"""
        self.is_recording = False
        result = self.input_buffer.copy()
        self.input_buffer.clear()
        self.logger.info("停止记录输入")
        return result
    
    def get_input_statistics(self) -> Dict[str, Any]:
        """获取输入统计信息"""
        return {
            'total_keys_pressed': len(self.key_handlers),
            'is_recording': self.is_recording,
            'buffer_size': len(self.input_buffer),
            'registered_handlers': list(self.key_handlers.keys())
        }
