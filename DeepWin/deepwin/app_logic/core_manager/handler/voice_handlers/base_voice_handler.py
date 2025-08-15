# base_voice_handler.py
# 基础语音处理器类，提供通用的语音指令处理框架

from typing import Dict, Any, List, Optional
from deepwin.app_logic.core_manager.base_handler import BaseHandler
import logging

class BaseVoiceHandler(BaseHandler):
    """
    基础语音处理器类
    提供语音指令处理的通用框架和接口
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.handler_name = self.__class__.__name__
        self.supported_commands: List[str] = []
        self.command_handlers: Dict[str, callable] = {}
        self.command_params: Dict[str, Dict[str, Any]] = {}
        
    def initialize(self):
        """初始化处理器"""
        super().initialize()
        self._register_command_handlers()
        self.logger.info(f"{self.handler_name}: 初始化完成，支持命令: {self.supported_commands}")
        
    def _register_command_handlers(self):
        """
        注册命令处理器
        子类应该重写此方法来注册支持的命令和对应的处理函数
        如果不重写，将使用默认的空实现
        """
        # 默认实现：子类应该重写此方法
        pass
        
    def can_handle_command(self, command_name: str) -> bool:
        """检查是否可以处理指定的命令"""
        return command_name in self.supported_commands
        
    def handle_command(self, command_data: List[Dict[str, Any]]) -> bool:
        """
        处理语音命令
        :param command_name: 命令名称
        :param params: 命令参数列表
        :return: 是否成功处理
        """
        command_name = command_data.get('name', '')
        params = command_data.get('params', [])

        if not self.can_handle_command(command_name):
            self.logger.warning(f"{self.handler_name}: 不支持的命令: {command_name}")
            return False
            
        try:
            handler = self.command_handlers.get(command_name)
            if handler:
                result = handler(command_data) # 完整命令数据
                self.logger.info(f"{self.handler_name}: 成功处理命令 {command_name}, 结果: {result}")
                return True
            else:
                self.logger.error(f"{self.handler_name}: 命令 {command_name} 的处理器未找到")
                return False
        except Exception as e:
            self.logger.error(f"{self.handler_name}: 处理命令 {command_name} 时发生错误: {e}")
            return False

    def handle_command_with_params(self, command_params: Dict[str, Any]) -> bool:
        """
        处理语音命令
        :param command_params: 命令参数列表
        :return: 是否成功处理
        """
        pass

    def get_supported_commands(self) -> List[str]:
        """获取支持的命令列表"""
        return self.supported_commands.copy()
        
    def get_handler_info(self) -> Dict[str, Any]:
        """获取处理器信息"""
        return {
            'name': self.handler_name,
            'supported_commands': self.supported_commands,
            'command_count': len(self.supported_commands)
        }
