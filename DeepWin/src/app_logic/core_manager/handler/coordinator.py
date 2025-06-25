# src/app_logic/core_manager/handler/coordinator.py
# 协调器信号处理器，负责管理协调器向外发出的信号和对应的槽函数

from PySide6.QtCore import Slot, Signal
from src.app_logic.core_manager.base_handler import BaseHandler

class CoordinatorHandler(BaseHandler):
    """
    协调器信号处理器
    负责：
    1. 连接协调器向外发出的信号到UI
    2. 提供统一的信号转发接口
    3. 处理协调器信号的槽函数
    4. 作为其他Handler的信号转发中心
    5. 记录协调器信号的日志
    """
    
    # 定义协调器可以向 UI (或其他监听者) 发射的通用状态信号
    app_status_message = Signal(str) # 应用状态消息（显示在状态栏）
    # 图像处理相关信号 (直接转发给 UI)
    image_processing_started = Signal(str)
    image_processing_finished = Signal(str, str)
    image_processing_error = Signal(str, str)
    # 设备控制相关信号 (直接转发给 UI)
    device_status_updated = Signal(str, dict)
    device_control_response = Signal(str)
    device_control_error = Signal(str)
    # 资源匹配相关信号 (直接转发给 UI)
    resource_matched = Signal(dict)
    resource_match_error = Signal(str)
    # 新增：轨迹执行详细进度信号
    trajectory_execution_progress_detailed = Signal(str, dict) # (device_id, progress_data)
    # 新增：轨迹执行完成和错误信号
    trajectory_execution_finished = Signal(str) # (device_id)
    trajectory_execution_error = Signal(str, str) # (device_id, error_message)

    def __init__(self, parent=None):
        super().__init__(parent)
        # 设置GUI管理器引用（在协调器中设置）
        self.gui_manager = None

    def _validate_dependencies(self):
        """
        验证必需的依赖项是否已设置
        """
        self.logger.info(f"CoordinatorHandler: 验证依赖项开始--------------------------------")
        if not self.logger:
            raise ValueError("缺少必需的依赖项: logger")
        # 信号是类属性，在实例化时总是存在的，不需要检查
        self.logger.info(f"CoordinatorHandler: 验证依赖项结束--------------------------------")
            
    def _connect_signals(self):
        """
        连接协调器信号到UI和其他模块
        """
        self.logger.debug("CoordinatorHandler: 连接协调器信号...")
        
        # 获取协调器实例
        coordinator = self.parent()
        if not coordinator:
            self.logger.error("CoordinatorHandler: 无法获取协调器实例")
            return
        
        # 连接轨迹执行相关信号到UI
        self._connect_trajectory_signals()
        
        # 连接设备控制相关信号到UI
        self._connect_device_signals()
        
        # 连接应用状态信号到UI
        self._connect_app_status_signals()
        
        # 连接图像处理相关信号到UI
        self._connect_image_processing_signals()
        
        # 连接资源匹配相关信号到UI
        self._connect_resource_signals()
        
        self.logger.debug("CoordinatorHandler: 协调器信号连接完成")
        
    def _connect_trajectory_signals(self):
        """连接轨迹执行相关信号"""
        try:
            # 检查GUI管理器是否可用
            if not self.gui_manager or not self.gui_manager.window:
                self.logger.warning("CoordinatorHandler: GUI管理器不可用，跳过轨迹信号连接")
                return
                
            device_interface = self.gui_manager.window.deviceInterface
            
            # 连接轨迹执行进度信号到UI（如果方法存在）
            if hasattr(device_interface, '_handle_trajectory_execution_progress'):
                self.trajectory_execution_progress_detailed.connect(
                    device_interface._handle_trajectory_execution_progress
                )
                # 添加日志记录
                # self.trajectory_execution_progress_detailed.connect(
                #     lambda device_id, progress_data: self.logger.info(f"CoordinatorHandler: 轨迹执行进度: {device_id}, 进度数据: {progress_data}")
                # )
                self.logger.info("CoordinatorHandler: 已连接轨迹执行进度信号")
            else:
                # 暂时屏蔽，只记录日志
                # self.trajectory_execution_progress_detailed.connect(
                #     lambda device_id, progress_data: self.logger.info(f"CoordinatorHandler: 轨迹执行进度: {device_id}, 进度数据: {progress_data}")
                # )
                self.logger.warning("CoordinatorHandler: DeviceInterface缺少_handle_trajectory_execution_progress方法，仅记录日志")
            
            # 连接轨迹执行完成信号到UI（如果方法存在）
            if hasattr(device_interface, '_handle_trajectory_execution_finished'):
                self.trajectory_execution_finished.connect(
                    device_interface._handle_trajectory_execution_finished
                )
                # 添加日志记录
                self.trajectory_execution_finished.connect(
                    lambda device_id: self.logger.info(f"CoordinatorHandler: 轨迹执行完成: {device_id}")
                )
                self.logger.info("CoordinatorHandler: 已连接轨迹执行完成信号")
            else:
                # 暂时屏蔽，只记录日志
                self.trajectory_execution_finished.connect(
                    lambda device_id: self.logger.info(f"CoordinatorHandler: 轨迹执行完成: {device_id}")
                )
                self.logger.warning("CoordinatorHandler: DeviceInterface缺少_handle_trajectory_execution_finished方法，仅记录日志")
            
            # 连接轨迹执行错误信号到UI（如果方法存在）
            if hasattr(device_interface, '_handle_trajectory_execution_error'):
                self.trajectory_execution_error.connect(
                    device_interface._handle_trajectory_execution_error
                )
                # 添加日志记录
                self.trajectory_execution_error.connect(
                    lambda device_id, error_message: self.logger.error(f"CoordinatorHandler: 轨迹执行错误: {device_id}, 错误: {error_message}")
                )
                self.logger.info("CoordinatorHandler: 已连接轨迹执行错误信号")
            else:
                # 暂时屏蔽，只记录日志
                self.trajectory_execution_error.connect(
                    lambda device_id, error_message: self.logger.error(f"CoordinatorHandler: 轨迹执行错误: {device_id}, 错误: {error_message}")
                )
                self.logger.warning("CoordinatorHandler: DeviceInterface缺少_handle_trajectory_execution_error方法，仅记录日志")
            
        except Exception as e:
            self.logger.error(f"CoordinatorHandler: 连接轨迹信号失败: {e}")
            
    def _connect_device_signals(self):
        """连接设备控制相关信号"""
        try:
            # 检查GUI管理器是否可用
            if not self.gui_manager or not self.gui_manager.window:
                self.logger.warning("CoordinatorHandler: GUI管理器不可用，跳过设备信号连接")
                return
                
            device_interface = self.gui_manager.window.deviceInterface
            
            # 连接设备状态更新信号到UI（如果方法存在）
            if hasattr(device_interface, '_handle_device_status_updated'):
                self.device_status_updated.connect(
                    device_interface._handle_device_status_updated
                )
                # 添加日志记录
                self.device_status_updated.connect(
                    lambda device_id, status: self.logger.info(f"CoordinatorHandler: 设备状态更新: {device_id}, 状态: {status}")
                )
            else:
                # 暂时屏蔽，只记录日志
                self.device_status_updated.connect(
                    lambda device_id, status: self.logger.info(f"CoordinatorHandler: 设备状态更新: {device_id}, 状态: {status}")
                )
                self.logger.warning("CoordinatorHandler: DeviceInterface缺少_handle_device_status_updated方法，仅记录日志")
            
            # 连接设备控制响应信号到UI（如果方法存在）
            if hasattr(device_interface, '_handle_device_control_response'):
                self.device_control_response.connect(
                    device_interface._handle_device_control_response
                )
                # 添加日志记录
                self.device_control_response.connect(
                    lambda response: self.logger.info(f"CoordinatorHandler: 设备控制响应: {response}")
                )
            else:
                # 暂时屏蔽，只记录日志
                self.device_control_response.connect(
                    lambda response: self.logger.info(f"CoordinatorHandler: 设备控制响应: {response}")
                )
                self.logger.warning("CoordinatorHandler: DeviceInterface缺少_handle_device_control_response方法，仅记录日志")
            
            # 连接设备控制错误信号到UI（如果方法存在）
            if hasattr(device_interface, '_handle_device_control_error'):
                self.device_control_error.connect(
                    device_interface._handle_device_control_error
                )
                # 添加日志记录
                self.device_control_error.connect(
                    lambda error: self.logger.error(f"CoordinatorHandler: 设备控制错误: {error}")
                )
            else:
                # 暂时屏蔽，只记录日志
                self.device_control_error.connect(
                    lambda error: self.logger.error(f"CoordinatorHandler: 设备控制错误: {error}")
                )
                self.logger.warning("CoordinatorHandler: DeviceInterface缺少_handle_device_control_error方法，仅记录日志")
            
            self.logger.info("CoordinatorHandler: 设备控制信号连接完成")
            
        except Exception as e:
            self.logger.error(f"CoordinatorHandler: 连接设备信号失败: {e}")
            
    def _connect_app_status_signals(self):
        """连接应用状态信号"""
        pass
            
    def _connect_image_processing_signals(self):
        """连接图像处理相关信号"""
        try:
            # 检查GUI管理器是否可用
            if not self.gui_manager or not self.gui_manager.window:
                self.logger.warning("CoordinatorHandler: GUI管理器不可用，跳过图像处理信号连接")
                return
                
            device_interface = self.gui_manager.window.deviceInterface
            
            # 连接图像处理开始信号到UI（如果方法存在）
            if hasattr(device_interface, '_handle_image_processing_started'):
                self.image_processing_started.connect(
                    device_interface._handle_image_processing_started
                )
                # 添加日志记录
                self.image_processing_started.connect(
                    lambda device_id: self.logger.info(f"CoordinatorHandler: 图像处理开始: {device_id}")
                )
            else:
                # 暂时屏蔽，只记录日志
                self.image_processing_started.connect(
                    lambda device_id: self.logger.info(f"CoordinatorHandler: 图像处理开始: {device_id}")
                )
                self.logger.warning("CoordinatorHandler: DeviceInterface缺少_handle_image_processing_started方法，仅记录日志")
            
            # 连接图像处理完成信号到UI（如果方法存在）
            if hasattr(device_interface, '_handle_image_processing_finished'):
                self.image_processing_finished.connect(
                    device_interface._handle_image_processing_finished
                )
                # 添加日志记录
                self.image_processing_finished.connect(
                    lambda device_id, result: self.logger.info(f"CoordinatorHandler: 图像处理完成: {device_id}, 结果: {result}")
                )
            else:
                # 暂时屏蔽，只记录日志
                self.image_processing_finished.connect(
                    lambda device_id, result: self.logger.info(f"CoordinatorHandler: 图像处理完成: {device_id}, 结果: {result}")
                )
                self.logger.warning("CoordinatorHandler: DeviceInterface缺少_handle_image_processing_finished方法，仅记录日志")
            
            # 连接图像处理错误信号到UI（如果方法存在）
            if hasattr(device_interface, '_handle_image_processing_error'):
                self.image_processing_error.connect(
                    device_interface._handle_image_processing_error
                )
                # 添加日志记录
                self.image_processing_error.connect(
                    lambda device_id, error: self.logger.error(f"CoordinatorHandler: 图像处理错误: {device_id}, 错误: {error}")
                )
            else:
                # 暂时屏蔽，只记录日志
                self.image_processing_error.connect(
                    lambda device_id, error: self.logger.error(f"CoordinatorHandler: 图像处理错误: {device_id}, 错误: {error}")
                )
                self.logger.warning("CoordinatorHandler: DeviceInterface缺少_handle_image_processing_error方法，仅记录日志")
            
            self.logger.info("CoordinatorHandler: 图像处理信号连接完成")
            
        except Exception as e:
            self.logger.error(f"CoordinatorHandler: 连接图像处理信号失败: {e}")
            
    def _connect_resource_signals(self):
        """连接资源匹配相关信号"""
        try:
            # 检查GUI管理器是否可用
            if not self.gui_manager or not self.gui_manager.window:
                self.logger.warning("CoordinatorHandler: GUI管理器不可用，跳过资源匹配信号连接")
                return
                
            device_interface = self.gui_manager.window.deviceInterface
            
            # 连接资源匹配成功信号到UI（如果方法存在）
            if hasattr(device_interface, '_handle_resource_matched'):
                self.resource_matched.connect(
                    device_interface._handle_resource_matched
                )
                # 添加日志记录
                self.resource_matched.connect(
                    lambda resource: self.logger.info(f"CoordinatorHandler: 资源匹配成功: {resource}")
                )
            else:
                # 暂时屏蔽，只记录日志
                self.resource_matched.connect(
                    lambda resource: self.logger.info(f"CoordinatorHandler: 资源匹配成功: {resource}")
                )
                self.logger.warning("CoordinatorHandler: DeviceInterface缺少_handle_resource_matched方法，仅记录日志")
            
            # 连接资源匹配错误信号到UI（如果方法存在）
            if hasattr(device_interface, '_handle_resource_match_error'):
                self.resource_match_error.connect(
                    device_interface._handle_resource_match_error
                )
                # 添加日志记录
                self.resource_match_error.connect(
                    lambda error: self.logger.error(f"CoordinatorHandler: 资源匹配错误: {error}")
                )
            else:
                # 暂时屏蔽，只记录日志
                self.resource_match_error.connect(
                    lambda error: self.logger.error(f"CoordinatorHandler: 资源匹配错误: {error}")
                )
                self.logger.warning("CoordinatorHandler: DeviceInterface缺少_handle_resource_match_error方法，仅记录日志")
            
            self.logger.info("CoordinatorHandler: 资源匹配信号连接完成")
            
        except Exception as e:
            self.logger.error(f"CoordinatorHandler: 连接资源匹配信号失败: {e}")
    
    # ==================== 信号转发接口 ====================
    
    def emit_trajectory_execution_progress(self, device_id: str, progress_data: dict):
        """发射轨迹执行进度信号"""
        self.trajectory_execution_progress_detailed.emit(device_id, progress_data)
        self.logger.debug(f"CoordinatorHandler: 发射轨迹执行进度信号 - 设备: {device_id}")
        
    def emit_trajectory_execution_finished(self, device_id: str):
        """发射轨迹执行完成信号"""
        self.trajectory_execution_finished.emit(device_id)
        self.logger.info(f"CoordinatorHandler: 发射轨迹执行完成信号 - 设备: {device_id}")
        
    def emit_trajectory_execution_error(self, device_id: str, error_message: str):
        """发射轨迹执行错误信号"""
        self.trajectory_execution_error.emit(device_id, error_message)
        self.logger.error(f"CoordinatorHandler: 发射轨迹执行错误信号 - 设备: {device_id}, 错误: {error_message}")
        
    def emit_device_status_updated(self, device_id: str, status_data: dict):
        """发射设备状态更新信号"""
        self.device_status_updated.emit(device_id, status_data)
        self.logger.debug(f"CoordinatorHandler: 发射设备状态更新信号 - 设备: {device_id}")
        
    def emit_device_control_response(self, response_message: str):
        """发射设备控制响应信号"""
        self.device_control_response.emit(response_message)
        self.logger.info(f"CoordinatorHandler: 发射设备控制响应信号 - {response_message}")
        
    def emit_device_control_error(self, error_message: str):
        """发射设备控制错误信号"""
        self.device_control_error.emit(error_message)
        self.logger.error(f"CoordinatorHandler: 发射设备控制错误信号 - {error_message}")
        
    def emit_app_status_message(self, status_message: str):
        """发射应用状态消息信号"""
        self.app_status_message.emit(status_message)
        self.logger.info(f"CoordinatorHandler: 发射应用状态消息信号 - {status_message}")
        
    def emit_image_processing_started(self, device_id: str):
        """发射图像处理开始信号"""
        self.image_processing_started.emit(device_id)
        self.logger.info(f"CoordinatorHandler: 发射图像处理开始信号 - 设备: {device_id}")
        
    def emit_image_processing_finished(self, device_id: str, result: str):
        """发射图像处理完成信号"""
        self.image_processing_finished.emit(device_id, result)
        self.logger.info(f"CoordinatorHandler: 发射图像处理完成信号 - 设备: {device_id}, 结果: {result}")
        
    def emit_image_processing_error(self, device_id: str, error: str):
        """发射图像处理错误信号"""
        self.image_processing_error.emit(device_id, error)
        self.logger.error(f"CoordinatorHandler: 发射图像处理错误信号 - 设备: {device_id}, 错误: {error}")
        
    def emit_resource_matched(self, resource_data: dict):
        """发射资源匹配成功信号"""
        self.resource_matched.emit(resource_data)
        self.logger.info(f"CoordinatorHandler: 发射资源匹配成功信号 - {resource_data}")
        
    def emit_resource_match_error(self, error_message: str):
        """发射资源匹配错误信号"""
        self.resource_match_error.emit(error_message)
        self.logger.error(f"CoordinatorHandler: 发射资源匹配错误信号 - {error_message}")

    def set_gui_manager(self, gui_manager):
        """设置GUI管理器"""
        self.gui_manager = gui_manager
        if self.logger:
            self.logger.info("CoordinatorHandler: GUI管理器已设置")
        # 重新连接信号
        self._connect_signals() 