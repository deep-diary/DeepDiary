# src/app_logic/core_manager/handler/voice_communication_handler.py
# 语音通信处理器，负责处理语音服务发出的信号连接和事件处理

from PySide6.QtCore import Slot, Signal
from src.app_logic.core_manager.base_handler import BaseHandler
import json
import logging

class VoiceCommunicationHandler(BaseHandler):
    """
    语音通信处理器
    负责处理语音服务发出的信号连接和事件处理，包括：
    1. 接收语音命令信号
    2. 解析commands并转发到协调器
    3. 处理语音相关的状态更新
    4. 作为语音服务与其他模块的桥梁
    """
    
    # 定义语音通信相关的信号
    voice_command_received = Signal(dict)  # 语音命令接收信号 (command_data)
    voice_status_updated = Signal(str, dict)  # 语音状态更新信号 (status_type, status_data)
    voice_error_occurred = Signal(str, str)  # 语音错误信号 (error_type, error_message)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        
    def _validate_dependencies(self):
        """
        验证必需的依赖项是否已设置
        """
        # 检查基础依赖项
        if not self.logger:
            raise ValueError("缺少必需的依赖项: logger")
        if not self.coordinator_handler:
            raise ValueError("缺少必需的依赖项: coordinator_handler")
        if not self.device_logic_manager:
            raise ValueError("缺少必需的依赖项: device_logic_manager")
            
    def _connect_signals(self):
        """
        连接语音通信层相关的信号
        """
        self.logger.debug("VoiceCommunicationHandler: 连接语音通信层信号...")
        
        # 连接语音命令接收信号到协调器
        self.voice_command_received.connect(self._on_voice_command_received)
        
        # 连接语音状态更新信号到协调器
        self.voice_status_updated.connect(self._on_voice_status_updated)
        
        # 连接语音错误信号到协调器
        self.voice_error_occurred.connect(self._on_voice_error_occurred)
        
        # 连接VoiceManager的语音命令信号
        if hasattr(self, 'voice_manager') and self.voice_manager:
            self.voice_manager.voice_command_received.connect(self._on_voice_command_received)
            self.logger.info("VoiceCommunicationHandler: 已连接VoiceManager信号")
        
        self.logger.debug("VoiceCommunicationHandler: 语音通信层信号连接完成")
        
    @Slot(dict)
    def _on_voice_command_received(self, command_data: dict):
        """
        处理语音命令接收事件
        """
        self.logger.info(f"VoiceCommunicationHandler: 收到语音命令: {command_data}")
        
        try:
            # 记录命令到协调器状态
            self.coordinator_handler.app_status_message.emit(f"收到语音命令: {command_data.get('name', 'unknown')}")
            
            # 转发命令到设备逻辑管理器
            self._forward_command_to_device(command_data)
            
        except Exception as e:
            error_msg = f"处理语音命令时发生错误: {str(e)}"
            self.logger.error(error_msg)
            self.voice_error_occurred.emit("command_processing_error", error_msg)
            
    @Slot(str, dict)
    def _on_voice_status_updated(self, status_type: str, status_data: dict):
        """
        处理语音状态更新事件
        """
        self.logger.info(f"VoiceCommunicationHandler: 语音状态更新 - 类型: {status_type}, 数据: {status_data}")
        
        # 转发状态更新到协调器
        self.coordinator_handler.app_status_message.emit(f"语音状态更新: {status_type}")
        
    @Slot(str, str)
    def _on_voice_error_occurred(self, error_type: str, error_message: str):
        """
        处理语音错误事件
        """
        self.logger.error(f"VoiceCommunicationHandler: 语音错误 - 类型: {error_type}, 消息: {error_message}")
        
        # 转发错误到协调器
        self.coordinator_handler.app_status_message.emit(f"语音错误: {error_message}")
        
    def _forward_command_to_device(self, command_data: dict):
        """
        将语音命令转发到设备逻辑管理器
        command: {'name': 'motor_set_pos', 'params': [{'name': 'pos', 'value': '1', 'normValue': '1'}]}
        """
        try:
            command_name = command_data.get('name', '')
            params = command_data.get('params', [])
            
            self.logger.info(f"VoiceCommunicationHandler: 转发命令到设备 - 名称: {command_name}, 参数: {params}")
            
            # 根据命令类型转发到相应的设备模块
            if command_name.startswith('motor_'):
                # 电机相关命令
                self._handle_motor_command(command_name, params)
            elif command_name.startswith('arm_'):
                # 机械臂相关命令
                self._handle_arm_command(command_name, params)
            elif command_name.startswith('toy_'):
                # 玩具相关命令
                self._handle_toy_command(command_name, params)
            else:
                # 通用命令
                self._handle_generic_command(command_name, params)
                
        except Exception as e:
            error_msg = f"转发命令到设备时发生错误: {str(e)}"
            self.logger.error(error_msg)
            self.voice_error_occurred.emit("device_forward_error", error_msg)
            
    def _handle_motor_command(self, command_name: str, params: list):
        """
        处理电机相关命令
        """
        self.logger.info(f"VoiceCommunicationHandler: 处理电机命令: {command_name}")
        
        # 这里可以添加具体的电机命令处理逻辑
        # 例如：调用设备逻辑管理器中的相应方法
        
        # 发送设备状态更新信号
        # self.coordinator_handler.device_status_updated.emit("motor", {
        #     "command": command_name,
        #     "params": params,
        #     "status": "executing"
        # })
        
    def _handle_arm_command(self, command_name: str, params: list):
        """
        处理机械臂相关命令
        """
        self.logger.info(f"VoiceCommunicationHandler: 处理机械臂命令: {command_name}")
        
        # 这里可以添加具体的机械臂命令处理逻辑
        
        # 发送设备状态更新信号
        self.coordinator_handler.device_status_updated.emit("arm", {
            "command": command_name,
            "params": params,
            "status": "executing"
        })
        
    def _handle_toy_command(self, command_name: str, params: list):
        """
        处理玩具相关命令
        """
        self.logger.info(f"VoiceCommunicationHandler: 处理玩具命令: {command_name}")
        
        # 这里可以添加具体的玩具命令处理逻辑
        
        # 发送设备状态更新信号
        self.coordinator_handler.device_status_updated.emit("toy", {
            "command": command_name,
            "params": params,
            "status": "executing"
        })
        
    def _handle_generic_command(self, command_name: str, params: list):
        """
        处理通用命令
        """
        self.logger.info(f"VoiceCommunicationHandler: 处理通用命令: {command_name}")
        
        # 这里可以添加通用命令的处理逻辑
        
        # 发送设备状态更新信号
        self.coordinator_handler.device_status_updated.emit("generic", {
            "command": command_name,
            "params": params,
            "status": "executing"
        })
        
    def process_voice_response(self, payload: dict):
        """
        处理语音响应内容，提取commands并发送信号
        这个方法可以从外部调用，例如从ChatCallback中调用
        """
        try:
            if not payload or "output" not in payload:
                self.logger.warning("VoiceCommunicationHandler: 无效的语音响应payload")
                return
                
            output = payload["output"]
            extra_info = output.get("extra_info", {})
            commands_str = extra_info.get("commands", "[]")
            
            self.logger.info(f"VoiceCommunicationHandler: 处理语音响应，commands: {commands_str}")
            
            # 解析commands
            commands_list = json.loads(commands_str)
            
            for command in commands_list:
                self.logger.info(f"VoiceCommunicationHandler: 处理命令: {command}")
                
                # 发送语音命令接收信号
                self.voice_command_received.emit(command)
                
        except json.JSONDecodeError as e:
            error_msg = f"解析commands JSON时发生错误: {str(e)}"
            self.logger.error(error_msg)
            self.voice_error_occurred.emit("json_parse_error", error_msg)
        except Exception as e:
            error_msg = f"处理语音响应时发生错误: {str(e)}"
            self.logger.error(error_msg)
            self.voice_error_occurred.emit("response_processing_error", error_msg)
            
    def emit_voice_command_received(self, command_data: dict):
        """
        发射语音命令接收信号
        """
        self.voice_command_received.emit(command_data)
        
    def emit_voice_status_updated(self, status_type: str, status_data: dict):
        """
        发射语音状态更新信号
        """
        self.voice_status_updated.emit(status_type, status_data)
        
    def emit_voice_error_occurred(self, error_type: str, error_message: str):
        """
        发射语音错误信号
        """
        self.voice_error_occurred.emit(error_type, error_message)
    
    def set_voice_manager(self, voice_manager):
        """设置VoiceManager引用并连接信号"""
        self.voice_manager = voice_manager
        if voice_manager:
            voice_manager.voice_command_received.connect(self._on_voice_command_received)
            self.logger.info("VoiceCommunicationHandler: 已设置VoiceManager并连接信号")
