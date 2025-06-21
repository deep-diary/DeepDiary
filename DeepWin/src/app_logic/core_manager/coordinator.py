# src/app_logic/core_manager/coordinator.py
# 核心协调器 (T类)
# 负责协调 UI 请求，分派给业务逻辑模块，并处理异步任务和结果回调。
# 完善模块协调和事件分发逻辑。

from PySide6.QtCore import QObject, Signal, Slot, QThreadPool, QTimer
from typing import Dict, Any
import time

# 导入公共的 WorkerRunnable 和 WorkerSignals，以解决循环导入问题
from src.app_logic.core_manager.workers import WorkerRunnable, WorkerSignals

# 导入应用逻辑层的各个管理器/处理器
from src.app_logic.memory_processing.image_video_processing.processor import ImageVideoProcessor
from src.app_logic.resource_demand_manager.manager import ResourceDemandManager
from src.app_logic.device_logic_manager.manager import DeviceLogicManager
from src.app_logic.ai_coordinator.coordinator import AICoordinator
from src.app_logic.agents.agent_manager import AgentManager
from src.app_logic.core_manager.task_scheduler import TaskScheduler # 导入新任务调度器

from src.data_management.local_database import LocalDatabaseManager
from src.data_management.log_manager import LogManager
from src.data_management.config_manager import ConfigManager
from src.ui.gui_manager import GuiManager
from src.services.hardware_communication.serial_communicator import SerialCommunicator
from src.services.hardware_communication.can_bus_communicator import CanBusCommunicator
from src.services.hardware_communication.device_protocol_parser import DeviceProtocolParser
from src.services.cloud_communication.api_client import CloudApiClient
from src.app_logic.mcp_client_manager.mcp_client_manager import MCPClientManager
from src.app_logic.weather_manager import WeatherManager

class Coordinator(QObject):
    """
    DeepWin 应用程序的核心协调器。
    它负责：
    1. 管理和初始化应用逻辑层的各个模块。
    2. 接收来自 UI 或其他模块的请求，并分派给对应的业务逻辑模块。
    3. 管理后台任务的执行（通过 QThreadPool 和 TaskScheduler），确保 UI 保持响应。
    4. 将业务逻辑执行结果或状态更新回调给 UI 或其他相关模块。
    5. 协调智能体层的行为，作为智能体感知和行动的桥梁。
    6. 实现模块间的事件分发和统一协调。
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


    def __init__(self, log_manager: LogManager, parent=None):
        """
        初始化协调器及其所有子模块。
        :param log_manager: 全局日志管理器实例。
        :param parent: QObject 父对象。
        """
        super().__init__(parent)
        self.logger = log_manager.get_logger(__name__)
        self.logger.info("Coordinator: 初始化中...")

        self.thread_pool = QThreadPool.globalInstance()
        # Ensure the thread pool is ready, and we manage its maximum threads
        # self.thread_pool.setMaxThreadCount(QThreadPool.globalInstance().maxThreadCount() - 1) # Moved to main.py
        self.logger.info(f"Coordinator: QThreadPool max thread count: {self.thread_pool.maxThreadCount()}")

        self.device_id_to_port = {} # 新增：设备ID到串口名的映射


        # 实例化配置管理器
        self.config_manager = ConfigManager(log_manager=log_manager)

        # ----------------------------------------------------------------------
        # 1. 初始化应用逻辑层的各个管理器/处理器 (I类)
        # 这些模块专注于各自的业务逻辑，不直接与 UI 交互
        # ----------------------------------------------------------------------
        self.image_video_processor = ImageVideoProcessor(log_manager=log_manager)
        self.resource_demand_manager = ResourceDemandManager(log_manager=log_manager)
        self.device_logic_manager = DeviceLogicManager(log_manager=log_manager, config_manager=self.config_manager)
        self.ai_coordinator = AICoordinator(log_manager=log_manager) # 避免与 Coordinator 类名冲突
        self.agent_manager = AgentManager(log_manager=log_manager) # 智能体管理器需要协调器引用
        self.agent_manager.set_coordinator(self)

        # ----------------------------------------------------------------------
        # 2. 初始化核心服务模块
        # ----------------------------------------------------------------------
        self.task_scheduler = TaskScheduler(log_manager=log_manager, thread_pool=self.thread_pool)
        self.cloud_api_client = CloudApiClient(log_manager=log_manager)
        self.local_database_manager = LocalDatabaseManager(log_manager=log_manager)
        self.gui_manager = GuiManager(log_manager=log_manager, config_manager=self.config_manager) # GUI 管理器用于管理 UI 视图


        # 实例化服务层组件 (真正的服务层实现)
        self.serial_communicator = SerialCommunicator(log_manager=log_manager, config_manager=self.config_manager)
        self.can_bus_communicator = CanBusCommunicator(log_manager=log_manager, config_manager=self.config_manager)
        self.device_protocol_parser = DeviceProtocolParser(log_manager=log_manager, config_manager=self.config_manager)
        self.cloud_api_client = CloudApiClient(log_manager=log_manager) # 云端 API 客户端

        # 实例化 MCPClientManager
        self.mcp_client_manager = MCPClientManager(log_manager=log_manager, config_manager=self.config_manager) # NEW
        # 实例化 WeatherManager，并传入 mcp_client_manager
        self.weather_manager = WeatherManager(mcp_client_manager=self.mcp_client_manager, log_manager=log_manager) # NEW

        # NEW: 存储串口名到设备ID的映射，用于数据接收分发
        self._port_to_device_id_map: Dict[str, str] = {}

        # ----------------------------------------------------------------------
        # 3. 建立信号和槽连接
        # 实现模块协调和事件分发逻辑的关键部分
        # ----------------------------------------------------------------------
        self.logger.info("Coordinator: 正在设置信号和槽连接...")
        self._connect_gui_signals()      # 连接来自 GUI 的请求信号
        self._connect_memory_processing_signals()# 连接业务处理器内部的信号
        self._connect_service_signals()  # 连接服务层的信号
        self._connect_agent_signals()    # 连接智能体层的信号
        self._connect_coordinator_output_signals() # 连接协调器自身的输出信号到GUI
        self._connect_device_logic_signals() # 连接设备逻辑管理器发出的信号
        self._connect_ai_coordinator_signals() # 连接 AI 协调器发出的信号
        self.logger.info("Coordinator: 信号和槽连接设置完成。")

        # ----------------------------------------------------------------------
        # 4. 启动定时任务 (例如：数据同步) TODO: 暂时不启动, 目前代码启动后会异常退出
        # ----------------------------------------------------------------------
        # self._setup_initial_tasks()

        self.logger.info("Coordinator: 初始化完成。")

    def _connect_ai_coordinator_signals(self):
        """
        连接 AI 协调器发出的信号到协调器的方法。
        这些信号通常表示 AI 任务完成、错误或进度更新。
        """
        self.logger.debug("Coordinator: 连接 AI 协调器信号...")
        # AI 协调器
        self.ai_coordinator.ai_service_response.connect(lambda result: self.app_status_message.emit(f"AI 服务响应: {result}"))
        self.ai_coordinator.ai_service_error.connect(lambda error_msg: self.app_status_message.emit(f"AI 服务错误: {error_msg}"))  
        self.logger.debug("Coordinator: AI 协调器信号连接完成。")

    def _connect_device_logic_signals(self):
        """
        连接设备逻辑管理器发出的信号到协调器的方法。
        这些信号通常表示设备状态更新、命令响应或错误。
        """
        self.logger.debug("Coordinator: 连接设备逻辑管理器信号...")
        
        # 设备逻辑管理器 -> Coordinator 的信号
        self.device_logic_manager.device_status_updated.connect(self.handle_device_states_updated)
        self.device_logic_manager.device_command_response.connect(lambda msg: self.app_status_message.emit(f"设备命令响应: {msg}"))
        self.device_logic_manager.device_error.connect(lambda msg: self.app_status_message.emit(f"设备错误: {msg}"))
        self.device_logic_manager.send_device_abstract_command_requested.connect(self._on_device_abstract_command_requested)
        
        # 移除对已删除的 teaching_manager 的引用
        # 轨迹播放相关信号现在由具体的设备实例处理
        # self.device_logic_manager.teaching_manager._trajectory_point_ready.connect(self.handle_trajectory_point_ready)
        # self.device_logic_manager.teaching_manager._trajectory_playback_started.connect(self.handle_trajectory_playback_started)
        # self.device_logic_manager.teaching_manager._trajectory_playback_finished.connect(self.handle_trajectory_playback_finished)
        # self.device_logic_manager.teaching_manager._trajectory_playback_error.connect(self.handle_trajectory_playback_error)
        
        self.logger.debug("Coordinator: 设备逻辑管理器信号连接完成。")

    def handle_device_states_updated(self, device_id: str, data: dict):
        """
        处理来自 DeviceLogicManager 的设备状态更新。
        将数据转发到 UI 和 AI 协调器。
        """
        # 转发到 UI
        if self.gui_manager and self.gui_manager.window:
            if device_id == "DeepMotor":
                self.gui_manager.window.deviceInterface.deep_motor_page.update_motor_data(data)

        # 检查是否需要更新示教轨迹
        if device_id == "DeepMotor":
            current_param = self.gui_manager.window.deviceInterface.deep_motor_page.current_selected_param
            if current_param == 'teaching_trajectory':
                # 自动请求刷新历史数据以更新实时示教曲线
                self.handle_request_history_data(device_id, 'teaching_trajectory')

        # 转发到 AI 协调器
        if self.ai_coordinator:
            self.ai_coordinator.perceive_device_state(device_id, data)

    def _connect_gui_signals(self):
        """
        连接来自 GUI 管理器中各个 UI 视图的请求信号到协调器对应的槽函数。
        这是 UI 层向应用逻辑层发起操作的主要途径。
        """
        self.logger.debug("Coordinator: 连接 GUI 信号...")
        # 记忆管理界面 (memory_manager_view.py)
        # 假设 MainWindow 的 memoryInterface 是一个独立的 QWidget 或 FluentWidget
        self.gui_manager.window.memoryInterface.process_image_request.connect(self.handle_process_image_request)
        # TODO: 连接更多记忆管理相关的 UI 信号
        # self.gui_manager.window.memoryInterface.analyze_diary_request.connect(self.handle_analyze_diary_request)

        # 设备控制界面 (deviceInterface.py)
        self.gui_manager.window.deviceInterface.ui_device_command.connect(self.handle_device_control_request)  # 添加设备命令信号绑定
        self.gui_manager.window.deviceInterface.serial_config.request_ports.connect(self.handle_ports_request) # 连接串口列表请求信号
        self.gui_manager.window.deviceInterface.serial_config.serial_connect_requested.connect(self.handle_serial_connect)  # 添加串口连接信号绑定
        self.gui_manager.window.deviceInterface.serial_config.serial_disconnect_requested.connect(self.handle_serial_disconnect)
        self.gui_manager.window.deviceInterface.deep_motor_page.request_sim_data.connect(self.handle_sim_data_request)
        self.gui_manager.window.deviceInterface.deep_motor_page.request_history_data.connect(self.handle_request_history_data)
        
        # 连接示教相关信号
        self.gui_manager.window.deviceInterface.deep_motor_page.start_teaching_requested.connect(self.handle_start_teaching_request)
        self.gui_manager.window.deviceInterface.deep_motor_page.stop_teaching_requested.connect(self.handle_stop_teaching_request)
        self.gui_manager.window.deviceInterface.deep_motor_page.execute_teaching_requested.connect(self.handle_execute_teaching_request)
        
        # 连接轨迹数据请求信号
        self.gui_manager.window.deviceInterface.deep_motor_page.request_trajectory_data.connect(self.handle_trajectory_data_request)
        
        # 连接轨迹列表请求信号
        self.gui_manager.window.deviceInterface.deep_motor_page.request_trajectory_list.connect(self.handle_trajectory_list_request)

        # 连接测试按钮信号
        self.gui_manager.window.basicInputInterface.test_button_clicked.connect(self.handle_test_button_click)

        self.logger.debug("Coordinator: GUI 信号连接完成。")

    def _connect_memory_processing_signals(self):
        """
        连接业务逻辑处理器内部发出的信号到协调器的方法。
        这些信号通常表示业务逻辑任务的完成、错误或进度更新。
        """
        self.logger.debug("Coordinator: 连接业务处理器信号...")
        # 图像视频处理器
        self.image_video_processor.processing_finished.connect(self._on_image_processing_done)
        self.image_video_processor.processing_error.connect(self._on_image_processing_error)
        self.image_video_processor.processing_progress.connect(self._on_image_processing_progress) # 连接进度信号

        # 资源需求管理器 (如果它有自己的内部信号)
        # self.resource_demand_manager.match_completed.connect(self._on_resource_match_completed)

        # 设备逻辑管理器 (如果它有自己的内部信号)
        # self.device_logic_manager.device_status_changed.connect(self.device_status_updated.emit) # 直接转发设备状态更新
        # self.device_logic_manager.command_executed.connect(self._on_device_command_executed)

        self.logger.debug("Coordinator: 业务处理器信号连接完成。")

    def _connect_service_signals(self):
        """
        连接服务层（如云端通信、本地数据库）发出的信号。
        这些信号通常表示数据同步状态、网络连接状态、数据库操作结果等。
        """
        self.logger.debug("Coordinator: 连接服务层信号...")
        # 云端 API 客户端
        # self.cloud_api_client.sync_finished.connect(self._on_cloud_sync_finished)
        # self.cloud_api_client.connection_status_changed.connect(self._on_cloud_connection_status_changed)

        # 本地数据库管理器
        # self.local_database_manager.data_loaded.connect(self._on_local_data_loaded)
        # self.local_database_manager.data_saved.connect(self._on_local_data_saved)

        # 任务调度器 (任务完成/失败通知)
        self.task_scheduler.task_completed.connect(self._on_scheduled_task_completed)
        self.task_scheduler.task_failed.connect(self._on_scheduled_task_failed)
        # --- 服务层 -> Coordinator -> 设备逻辑管理器的数据流 ---
        # 1. SerialCommunicator 发射解析后的 CAN 帧组件
        # self.serial_communicator.can_frame_components_received.connect(self.can_bus_communicator.process_serial_can_frame)
        self.serial_communicator.serial_error.connect(lambda p, msg: self.app_status_message.emit(f"串口错误 [{p}]: {msg}"))
        
        self.serial_communicator.connection_status_changed.connect(self._on_serial_connection_status_changed)
        self.serial_communicator.raw_frame_received.connect(self._on_raw_serial_frame_received)

        # 2. CanBusCommunicator 发射 DBC 解析后的 CAN 信号数据
        # self.can_bus_communicator.can_parsed_data_received.connect(self.device_protocol_parser.parse_low_level_data)
        # self.can_bus_communicator.can_raw_frame_received.connect(self.device_protocol_parser.parse_low_level_data)
        # self.can_bus_communicator.can_error.connect(lambda ch, msg: self.app_status_message.emit(f"CAN 错误 [{ch}]: {msg}"))
        # self.can_bus_communicator.connection_status_changed.connect(lambda ch, s: self.app_status_message.emit(f"CAN 总线 '{ch}' 连接状态: {'已连接' if s else '已断开'}"))

        # 3. DeviceProtocolParser 发射业务语义数据
        self.device_protocol_parser.device_semantic_data_ready.connect(self.device_logic_manager.handle_device_semantic_data)
        self.device_protocol_parser.protocol_conversion_error.connect(lambda dev_id, msg: self.app_status_message.emit(f"协议转换错误 [{dev_id}]: {msg}"))      

        self.logger.debug("Coordinator: 服务层信号连接完成。")

    def _connect_agent_signals(self):
        """
        连接智能体层内部发出的信号，这些信号表示智能体的感知、决策或行动请求。
        """
        self.logger.debug("Coordinator: 连接智能体信号...")
        # 智能体管理器请求数据
        self.agent_manager.request_memory_data.connect(self.local_database_manager.get_memories)
        self.agent_manager.trigger_device_action.connect(self.device_logic_manager.send_command_to_device)
        self.agent_manager.request_cloud_ai.connect(self.ai_coordinator.request_cloud_ai_service)
        self.agent_manager.send_app_message.connect(self.app_status_message.emit) # 智能体也可能向状态栏发送消息
        # 智能体管理器
        self.agent_manager.agent_status_update.connect(lambda status: self.app_status_message.emit(f"智能体状态: {status}"))
        self.agent_manager.agent_action_requested.connect(self._on_agent_action_requested)
        # TODO: 连接更多智能体发出的特定动作或状态信号
        # self.agent_manager.memory_curation_suggestion.connect(self.gui_manager.window.memoryInterface.display_curation_suggestion)

        self.logger.debug("Coordinator: 智能体信号连接完成。")


    def connection_test(self):  
        print("--------------------------------------------------connection_test")

    def connection_test2(self, state_dict: dict):  
        print("--------------------------------------------------connection_test2")

    def _connect_coordinator_output_signals(self):
        """
        将协调器自身的输出信号连接到 GUI 管理器中相应的 UI 视图。
        这是协调器将处理结果、状态更新传递给 UI 进行展示的主要途径。
        """
        self.logger.debug("Coordinator: 连接协调器输出信号到 GUI...")
        # 图像处理结果连接到记忆管理界面
        # --- 通用应用状态消息 ---
        self.app_status_message.connect(self.gui_manager.window.deviceInterface.status_bar.setText)
        self.image_processing_started.connect(self.gui_manager.window.memoryInterface._on_image_processing_started)
        self.image_processing_finished.connect(self.gui_manager.window.memoryInterface._on_image_processing_finished)
        self.image_processing_error.connect(self.gui_manager.window.memoryInterface._on_image_processing_error)

        # 设备控制结果连接到设备控制界面
        
        # self.device_logic_manager.managed_devices['DeepMotor'].device_status_updated.connect(self.connection_test)
        # self.device_logic_manager.device_status_updated.connect(self.connection_test2)
        # self.device_control_response.connect(self.gui_manager.window.devicesInterface.on_device_control_response)
        # self.device_control_error.connect(self.gui_manager.window.devicesInterface.on_device_control_error)
        # self.device_status_updated.connect(self.gui_manager.window.device
        # 
        # sInterface.on_device_status_updated)

        # # 资源匹配结果连接到资源/需求管理界面
        # self.resource_matched.connect(self.gui_manager.window.resourcesInterface.on_resource_matched)
        # self.resource_match_error.connect(self.gui_manager.window.resourcesInterface.on_resource_match_error)

        # # 通用应用状态消息连接到主窗口状态栏
        # self.app_status_message.connect(self.gui_manager.window.statusBar.showMessage)

        # 日志消息连接到日志显示界面 (假设日志管理器本身就直接输出到日志界面)
        # self.log_manager.new_log_entry.connect(self.gui_manager.window.logsInterface.add_log_entry)

        self.logger.debug("Coordinator: 协调器输出信号连接完成。")


    def _setup_initial_tasks(self):
        """
        设置应用程序启动时需要执行的初始定时任务或后台任务。
        例如：定时数据同步、启动智能体等。
        """
        self.logger.info("Coordinator: 设置初始任务...")
        # 示例：添加一个每隔 30 分钟执行一次的数据同步任务
        self.task_scheduler.add_periodic_task(
            task_id="daily_data_sync",
            task_func=self._perform_daily_data_sync,
            interval_ms=1 * 60 * 1000, # 1分钟
            initial_delay_ms=1000 # 1秒后启动
        )

        # 示例：启动智能体管理器
        # self.agent_manager.start_agents()
        self.logger.info("Coordinator: 初始任务设置完成。")
        
    def start_application(self):
        """启动应用程序"""
        self.logger.info("Coordinator: 启动应用程序...")


        self.agent_manager.start_agents()
        self.logger.info("Coordinator: 应用程序启动完成。")
        self.app_status_message.emit("DeepWin 应用程序启动成功！")


    @Slot(str, int)
    def handle_serial_connect(self, port: str, baud_rate: int):
        """
        处理串口连接请求
        :param port: 串口名称
        :param baud_rate: 波特率
        """
        self.logger.info(f"Coordinator: 收到串口连接请求 - 端口: {port}, 波特率: {baud_rate}")
        try:
            # 尝试打开串口
            self.serial_communicator.open_port(port, baud_rate)
            # 注意：实际的连接状态将通过 serial_communicator 的 connection_status_changed 信号通知
            # CAN总线配置将在收到连接成功的信号后执行
            
        except Exception as e:
            error_msg = f"串口连接失败: {str(e)}"
            self.logger.error(f"Coordinator: {error_msg}")
            self.app_status_message.emit(error_msg)

    # 修改串口连接状态信号的处理
    @Slot(str, bool)
    def _on_serial_connection_status_changed(self, port: str, is_connected: bool):
        device_instance_id = 'DeepMotor'
        if is_connected:
            self.logger.info(f"Coordinator: 串口 {port} 连接成功")
            self.app_status_message.emit(f"串口 {port} 连接成功")
            self._port_to_device_id_map[port] = device_instance_id # 映射串口到设备ID
        else:
            self.logger.info(f"Coordinator: 串口 {port} 已断开")
            self.app_status_message.emit(f"串口 {port} 已断开")
            self._port_to_device_id_map.pop(port)
        self.gui_manager.window.deviceInterface.serial_config.update_connection_status(is_connected)

    @Slot(str, bytes)
    def _on_raw_serial_frame_received(self, port_name: str, raw_frame_data: bytes):
        """
        槽函数：处理从 SerialCommunicator 接收到的原始串口帧数据。
        根据 port_name 映射到 device_id，然后转发给 DeviceProtocolParser。
        :param port_name: 接收到数据的串口名称。
        :param raw_frame_data: 完整的原始串口帧字节串。
        """
        device_id = self._port_to_device_id_map.get(port_name)
        if not device_id:
            self.logger.warning(f"Coordinator: 收到来自未知串口 '{port_name}' 的数据，无法映射到设备ID。数据: {raw_frame_data.hex()}")
            # return
            device_id = "DeepMotor" # for debug
        
        self.logger.debug(f"Coordinator: 收到来自串口 '{port_name}' (设备 '{device_id}') 的原始帧数据: {raw_frame_data.hex()}")
        # 将原始帧数据和对应的 device_id 转发给 DeviceProtocolParser
        self.device_protocol_parser.parse_low_level_data(device_id, raw_frame_data)

    @Slot(str, str)
    def _on_agent_action_requested(self, device_id: str, command: str):
        """
        处理来自智能体层的设备控制请求。
        """
        self.logger.info(f"Coordinator: 收到智能体层的设备控制请求 - 设备: {device_id}, 命令: {command}")
        self.device_logic_manager.send_command_to_device(device_id, command)
        self.app_status_message.emit(f"命令已发送至设备逻辑管理器: {device_id} - {command}")

    @Slot(str, str)
    def handle_device_control_request(self, device_id: str, command: str):
        """
        处理来自 UI 的设备控制请求，分发给 DeviceLogicManager。
        :param device_id: 目标设备的唯一标识符。
        :param command: 要发送的控制命令。
        """
        self.logger.info(f"Coordinator: 收到设备控制请求 - 设备: {device_id}, 命令: {command}")
        
        # 如果命令是列表格式，转换为函数调用格式
        if command.startswith('[') and command.endswith(']'):
            try:
                # 解析参数
                args = eval(command)
                if isinstance(args, list):
                    # 将命令转换为函数调用格式
                    command = f"{device_id}({','.join(map(str, args))})"
            except:
                self.logger.error(f"Coordinator: 命令格式转换失败: {command}")
                return

        # 将抽象命令转发给 DeviceLogicManager
        self.device_logic_manager.send_command_to_device(device_id, command)
        self.app_status_message.emit(f"命令已发送至设备逻辑管理器: {device_id} - {command}")

    @Slot(str, str, list)
    def _on_device_abstract_command_requested(self, device_id: str, abstract_command_name: str, args: list):
        """
        槽函数：处理 DeviceLogicManager 发出的抽象命令发送请求。
        将抽象命令转换为底层协议命令并通过硬件通信服务发送。
        """
        self.logger.info(f"Coordinator: 收到抽象命令发送请求 - 设备: {device_id}, 命令: {abstract_command_name}, 参数: {args}")
        try:
            # 使用 DeviceProtocolParser 将抽象命令转换为底层字节命令（包含 AT 头等）
            low_level_command_bytes = self.device_protocol_parser.generate_low_level_command(
                device_id, abstract_command_name, *args
            )
            
            # 根据设备类型决定通过哪个通信器发送
            # 假设 DeepArm 和 DeepMotor 的底层命令都是通过串口发送的

            target_port_name = None
            # 从 _port_to_device_id_map 反向查找 port_name
            for port, dev_id in self._port_to_device_id_map.items():
                if dev_id == device_id:
                    target_port_name = port
                    break

            if not target_port_name:
                self.logger.warning(f"Coordinator: 无法确定设备 '{device_id}' 对应的串口。")
                raise ValueError(f"无法确定设备 '{device_id}' 对应的串口。")

            # 处理多帧命令
            if isinstance(low_level_command_bytes, list):
                for cmd_bytes in low_level_command_bytes:
                    self.logger.debug(f"Coordinator: 目标串口 '{target_port_name}'，底层命令 (多帧): {cmd_bytes.hex()}")
                    self.serial_communicator.send_bytes(target_port_name, cmd_bytes)
                    time.sleep(0.01) # 短暂延迟，避免连续发送过快导致串口拥堵
            else:
                self.logger.debug(f"Coordinator: 目标串口 '{target_port_name}'，底层命令: {low_level_command_bytes.hex()}")
                self.serial_communicator.send_bytes(target_port_name, low_level_command_bytes)
            
            self.app_status_message.emit(f"已将底层命令发送到串口: {target_port_name}")
        except Exception as e:
            error_msg = f"处理设备抽象命令 '{abstract_command_name}' 失败: {e}"
            self.logger.error(f"Coordinator: {error_msg}")
            self.app_status_message.emit(f"命令发送失败: {error_msg}")
            self.device_logic_manager.device_error.emit(error_msg) # 通知 DeviceLogicManager 错误

    

    def _configure_can_bus(self, port: str):
        """
        配置CAN总线
        :param port: 串口名称
        """
        try:
            deepmotor_can_bustype = CanBusCommunicator.SERIAL_BRIDGE_BUSTYPE
            deepmotor_dbc_name = self.config_manager.get('device_settings.deepmotor_dbc_name')
            deepmotor_device_instance_id = "DeepMotor1"
            
            self.can_bus_communicator.connect_can_interface(
                channel=port,
                bustype=deepmotor_can_bustype,
                dbc_name=deepmotor_dbc_name,
                device_instance_id=deepmotor_device_instance_id
            )
            self.logger.info(f"Coordinator: CAN总线配置完成")
            self.app_status_message.emit(f"CAN总线配置完成")
            
        except Exception as can_error:
            # 如果CAN总线配置失败，关闭已打开的串口
            self.serial_communicator.close_port(port)
            error_msg = f"CAN总线配置失败: {str(can_error)}"
            self.logger.error(f"Coordinator: {error_msg}")
            self.app_status_message.emit(error_msg)

    @Slot(str)
    def handle_serial_disconnect(self, port: str):
        """
        处理串口断开请求
        :param port: 串口名称
        """
        self.logger.info(f"Coordinator: 收到串口断开请求 - 端口: {port}")
        self.serial_communicator.close_port(port)

    def handle_ports_request(self):
        """处理串口列表请求"""
        ports = self.serial_communicator.list_ports()
        # 更新所有设备页面的串口列表
        self.gui_manager.window.deviceInterface.serial_config.update_ports(ports)

    @Slot(str)
    def handle_test_button_click(self, message: str):
        """
        处理测试按钮点击事件
        :param message: 按钮点击消息
        """
        self.logger.info(f"Coordinator: 收到测试按钮点击信号 - {message}")
        self.app_status_message.emit(f"测试按钮被点击: {message}")

    # ----------------------------------------------------------------------
    # UI 请求的槽函数 (Coordinator 接收来自 UI 的请求)
    # 这些方法是 Coordinator 对外暴露的 API，供 UI 调用
    # ----------------------------------------------------------------------
    @Slot(str)
    def handle_process_image_request(self, image_path: str):
        """
        处理来自 UI 的图像处理请求。
        将耗时的图像处理任务提交到线程池执行，不阻塞 UI。
        """
        self.logger.info(f"Coordinator: 收到图像处理请求：{image_path}")
        self.app_status_message.emit(f"正在处理图片：{image_path}...")
        self.image_processing_started.emit(image_path) # 通知 UI 任务开始

        worker = WorkerRunnable(self.image_video_processor.process_image, image_path)
        # WorkerRunnable 的信号直接连接到 Coordinator 的内部槽函数，
        # Coordinator 的内部槽函数再决定如何通过自己的输出信号通知 UI
        worker.signals.finished.connect(self._on_image_processing_done)
        worker.signals.error.connect(self._on_image_processing_error)
        worker.signals.progress.connect(self._on_image_processing_progress) # 连接进度信号

        self.thread_pool.start(worker)

    # @Slot(float, float)
    # def handle_match_resource_request(self, latitude: float, longitude: float):
    #     """
    #     处理来自 UI 的资源匹配请求。
    #     这个可能涉及云端调用，也需要异步处理。
    #     """
    #     self.logger.info(f"Coordinator: 收到资源匹配请求，位置：{latitude}, {longitude}")
    #     self.app_status_message.emit("正在匹配资源...")

    #     worker = WorkerRunnable(self.resource_demand_manager.find_matching_resources, latitude, longitude)
    #     worker.signals.finished.connect(self._on_resource_match_completed)
    #     worker.signals.error.connect(self._on_resource_match_error)
    #     self.thread_pool.start(worker)

    # @Slot(str, str)
    # def handle_device_control_request(self, device_id: str, command: str):
    #     """
    #     处理来自 UI 的设备控制请求。
    #     """
    #     self.logger.info(f"Coordinator: 收到设备控制请求：设备ID={device_id}, 命令={command}")
    #     self.app_status_message.emit(f"正在发送命令到设备 {device_id}...")

    #     worker = WorkerRunnable(self.device_logic_manager.send_command_to_device, device_id, command)
    #     worker.signals.finished.connect(self._on_device_control_completed)
    #     worker.signals.error.connect(self._on_device_control_error)
    #     self.thread_pool.start(worker)

    # @Slot(dict)
    # def handle_data_sync_setting_change(self, settings: dict):
    #     """
    #     处理来自 UI 的数据同步设置变更请求。
    #     :param settings: 包含同步设置的字典，例如 {"auto_sync": True, "interval_minutes": 30}
    #     """
    #     self.logger.info(f"Coordinator: 收到数据同步设置变更请求: {settings}")
    #     # 根据设置更新定时任务
    #     if settings.get("auto_sync"):
    #         interval_ms = settings.get("interval_minutes", 30) * 60 * 1000
    #         self.task_scheduler.update_periodic_task(
    #             task_id="daily_data_sync",
    #             task_func=self._perform_daily_data_sync,
    #             interval_ms=interval_ms
    #         )
    #         self.app_status_message.emit("数据同步已开启并更新设置。")
    #     else:
    #         self.task_scheduler.remove_task("daily_data_sync")
    #         self.app_status_message.emit("数据同步已关闭。")


    # ----------------------------------------------------------------------
    # 内部槽函数 (Coordinator 接收来自业务逻辑/服务层/任务调度器的信号)
    # 这些方法负责处理内部事件，并决定是否通过 Coordinator 的输出信号通知 UI
    # ----------------------------------------------------------------------
    @Slot(str)
    def _on_image_processing_done(self, result: str):
        """
        处理图像处理任务完成的信号。
        由 ImageVideoProcessor 发出 (通过 WorkerRunnable 转发)。
        然后 Coordinator 通过自己的信号通知 UI。
        :param result: 图像处理的结果字符串。
        """
        self.logger.info(f"Coordinator: 图像处理任务完成：{result}")
        # 这里仅作转发，实际可能需要解析 result，提取更多信息
        self.image_processing_finished.emit(result, "成功") # 假设 result 包含路径，这里简化为结果字符串和状态
        self.app_status_message.emit(f"图像处理完成！结果：{result}")

    @Slot(str)
    def _on_image_processing_error(self, error_msg: str):
        """
        处理图像处理任务出错的信号。
        由 ImageVideoProcessor 发出 (通过 WorkerRunnable 转发)。
        然后 Coordinator 通过自己的信号通知 UI。
        :param error_msg: 错误信息字符串。
        """
        self.logger.error(f"Coordinator: 图像处理任务出错：{error_msg}")
        self.image_processing_error.emit("", error_msg) # 假设路径未知，这里只传递错误信息
        self.app_status_message.emit(f"图像处理出错：{error_msg}")

    @Slot(int)
    def _on_image_processing_progress(self, progress: int):
        """
        处理图像处理任务进度更新的信号。
        由 ImageVideoProcessor 发出 (通过 WorkerRunnable 转发)。
        可以考虑转发给 UI 更新进度条。
        :param progress: 进度百分比 (0-100)。
        """
        self.logger.debug(f"Coordinator: 图像处理进度: {progress}%")
        # TODO: 可以在这里发出一个通用的进度信号给 UI，或者让 UI 直接监听 Processor 的 progress 信号


    @Slot(dict)
    def _on_resource_match_completed(self, result: dict):
        """
        处理资源匹配任务完成的信号。
        由 ResourceDemandManager 发出 (通过 WorkerRunnable 转发)。
        :param result: 资源匹配的结果字典。
        """
        self.logger.info(f"Coordinator: 资源匹配完成：{result}")
        self.resource_matched.emit(result)
        self.app_status_message.emit("资源匹配完成！")

    @Slot(str)
    def _on_resource_match_error(self, error_msg: str):
        """
        处理资源匹配任务失败的信号。
        :param error_msg: 错误信息。
        """
        self.logger.error(f"Coordinator: 资源匹配失败：{error_msg}")
        self.resource_match_error.emit(error_msg)
        self.app_status_message.emit(f"资源匹配失败: {error_msg}")


    @Slot(str)
    def _on_device_control_completed(self, response: str):
        """
        处理设备控制命令执行完成的信号。
        由 DeviceLogicManager 发出 (通过 WorkerRunnable 转发)。
        :param response: 设备响应字符串。
        """
        self.logger.info(f"Coordinator: 设备控制命令执行完成：{response}")
        self.device_control_response.emit(response)
        self.app_status_message.emit(f"设备命令执行成功: {response}")

    @Slot(str)
    def _on_device_control_error(self, error_msg: str):
        """
        处理设备控制命令执行出错的信号。
        :param error_msg: 错误信息。
        """
        self.logger.error(f"Coordinator: 设备控制命令出错：{error_msg}")
        self.device_control_error.emit(error_msg)
        self.app_status_message.emit(f"设备命令执行失败: {error_msg}")


    @Slot(str, object)
    def _on_scheduled_task_completed(self, task_id: str, result: Any):
        """
        处理定时任务完成的信号。
        由 TaskScheduler 发出。
        :param task_id: 完成的任务ID。
        :param result: 任务执行结果。
        """
        self.logger.info(f"Coordinator: 定时任务 '{task_id}' 完成。结果: {result}")
        self.app_status_message.emit(f"后台任务 '{task_id}' 完成。")
        # 可以根据 task_id 触发不同的后续逻辑，例如数据同步成功后更新 UI 标志

    @Slot(str, str)
    def _on_scheduled_task_failed(self, task_id: str, error_msg: str):
        """
        处理定时任务失败的信号。
        由 TaskScheduler 发出。
        :param task_id: 失败的任务ID。
        :param error_msg: 错误信息。
        """
        self.logger.error(f"Coordinator: 定时任务 '{task_id}' 失败。错误: {error_msg}")
        self.app_status_message.emit(f"后台任务 '{task_id}' 失败: {error_msg}")


    # ----------------------------------------------------------------------
    # 示例业务逻辑 (可能由定时任务或智能体触发)
    # ----------------------------------------------------------------------
    def _perform_daily_data_sync(self):
        """
        示例：执行每日数据同步的业务逻辑。
        这是一个耗时操作，通常会在后台线程中执行。
        """
        self.logger.info("Coordinator: 开始执行每日数据同步...")
        try:
            # 模拟数据同步过程，可能涉及调用 cloud_api_client 和 local_database_manager
            # 例如：
            # cloud_data = self.cloud_api_client.fetch_latest_data()
            # self.local_database_manager.sync_data(cloud_data)
            time.sleep(5) # 模拟同步 5 秒
            sync_result = "数据同步成功"
            self.logger.info("Coordinator: 每日数据同步完成。")
            return sync_result
        except Exception as e:
            self.logger.error(f"Coordinator: 每日数据同步失败: {e}")
            raise # 抛出异常，让 WorkerRunnable 捕获并报告


    def cleanup(self):
        """
        协调器清理资源的方法。
        在应用程序退出时调用，确保所有子模块的资源被正确释放。
        """
        self.logger.info("Coordinator: 执行清理工作。")
        # 停止所有正在运行的定时任务
        self.task_scheduler.stop_all_tasks()
        self.logger.info("Coordinator: 已停止所有任务调度器任务。")

        # 关闭所有子模块可能打开的资源
        # 定义需要清理的模块列表
        modules_to_cleanup = [
            'image_video_processor',
            'resource_demand_manager', 
            'device_logic_manager',
            'ai_coordinator',
            'agent_manager',
            'cloud_api_client',
            'local_database_manager',
            'gui_manager',
            'serial_communicator',
            'can_bus_communicator',
            'device_protocol_parser'
        ]

        # 循环清理每个模块
        for module_name in modules_to_cleanup:
            if hasattr(self, module_name) and getattr(self, module_name):
                getattr(self, module_name).cleanup()

        self.logger.info("Coordinator: 所有子模块清理完成。")

    def handle_sim_data_request(self, device_name: str):
        """处理模拟数据请求"""
        self.logger.info(f"Coordinator: 收到模拟数据请求，设备: {device_name}")
        if device_name == "DeepMotor":
            # 调用串口通信器的模拟数据方法
            self.serial_communicator.sim_read_serial_data()

    def handle_request_history_data(self, device_name: str, param_name: str):
        """处理历史数据请求"""
        self.logger.info(f"Coordinator: 收到历史数据请求，设备: {device_name}, 参数: {param_name}")
        if device_name == "DeepMotor":
            # 获取历史数据 - 使用新的方法
            history_data = self.device_logic_manager.get_historical_data(device_name, param_name, {})
            if history_data is not None:
                # 发送历史数据到UI
                self.gui_manager.window.deviceInterface.deep_motor_page.update_history_curve(history_data)
        self.logger.info(f"Coordinator: 历史数据请求完成，设备: {device_name}, 参数: {param_name}")

    def handle_can_frame(self, port_name: str, arbitration_id: int, data_bytes: bytes, is_extended_id: bool):
        """处理接收到的CAN帧"""
        try:
            # 解析CAN帧数据
            parsed_data = self.can_bus_communicator.parse_can_frame(arbitration_id, data_bytes, is_extended_id)
            if parsed_data:
                # 更新电机数据显示
                if 'position' in parsed_data and 'speed' in parsed_data and 'torque' in parsed_data and 'temperature' in parsed_data:
                    motor_data = {
                        'position': parsed_data['position'],
                        'velocity': parsed_data['speed'],
                        'torque': parsed_data['torque'],
                        'temperature': parsed_data['temperature']
                    }
                    self.gui_manager.window.deviceInterface.deep_motor_page.update_motor_data(motor_data)
        except Exception as e:
            self.logger.error(f"Coordinator: 处理CAN帧失败: {e}")

    @Slot(str)
    def handle_start_teaching_request(self, device_name: str):
        """处理开始示教请求"""
        self.logger.info(f"Coordinator: 收到开始示教请求，设备: {device_name}")
        
        # 先发送失能命令
        self.device_logic_manager.send_command_to_device(device_name, "disable_motor(1)")
        self.app_status_message.emit(f"电机已失能，开始示教模式")
        
        # 启动示教模式
        self.device_logic_manager.start_teaching(device_name)
        self.app_status_message.emit(f"已开始示教，设备: {device_name}")

    @Slot(str)
    def handle_stop_teaching_request(self, device_name: str):
        """处理停止示教请求"""
        self.logger.info(f"Coordinator: 收到停止示教请求，设备: {device_name}")
        
        # 生成轨迹名称（使用时间戳）
        from datetime import datetime
        trajectory_name = f"trajectory_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 停止示教模式并保存轨迹
        save_success = self.device_logic_manager.stop_teaching(device_name, trajectory_name)
        self.logger.info(f"Coordinator: 轨迹 '{trajectory_name}' 保存成功: {save_success}")
        
        if save_success:
            self.app_status_message.emit(f"轨迹 '{trajectory_name}' 已保存")
            
            # 更新UI中的轨迹列表
            trajectory_list = self.device_logic_manager.get_trajectory_list(device_name)
            self.gui_manager.window.deviceInterface.deep_motor_page.update_trajectory_list(trajectory_list)
            self.logger.info(f"Coordinator: 轨迹列表已更新，共 {len(trajectory_list)} 条轨迹")
            
            # 自动选中新轨迹并显示对比曲线
            if trajectory_name in trajectory_list:
                self.logger.info(f"Coordinator: 轨迹 '{trajectory_name}' 存在于轨迹列表中，开始更新UI")
                page = self.gui_manager.window.deviceInterface.deep_motor_page
                
                # 1. 自动切换参数为轨迹对比模式
                param_text = 'trajectory_both (原始+规划)'
                page.param_combo.setCurrentText(param_text)
                
                # 2. 自动选中新轨迹
                page.trajectory_combo.setCurrentText(trajectory_name)

                # 3. 显式调用处理函数以触发数据刷新
                page.on_param_changed(param_text)
                page.on_trajectory_selection_changed(trajectory_name)

        else:
            self.app_status_message.emit(f"轨迹 '{trajectory_name}' 保存失败")
        
        self.app_status_message.emit(f"已停止示教，设备: {device_name}")

    @Slot(str, str)
    def handle_execute_teaching_request(self, device_name: str, trajectory_name: str):
        """处理执行示教请求"""
        self.logger.info(f"Coordinator: 收到执行示教请求，设备: {device_name}, 轨迹: {trajectory_name}")
        
        try:
            # 执行示教轨迹
            self.device_logic_manager.execute_trajectory(device_name, trajectory_name)
            self.app_status_message.emit(f"正在执行轨迹: {trajectory_name}")
        except Exception as e:
            error_msg = f"执行轨迹失败: {str(e)}"
            self.logger.error(f"Coordinator: {error_msg}")
            self.app_status_message.emit(error_msg)

    @Slot(str, float, float)
    def handle_trajectory_point_ready(self, device_id: str, position: float, velocity: float):
        """处理轨迹点就绪信号"""
        self.logger.debug(f"Coordinator: 轨迹点就绪，设备: {device_id}, 位置: {position:.2f}, 速度: {velocity:.2f}")
        
        # 发送位置控制命令到设备
        command = f"set_motor_position(1, {position:.2f})"
        self.device_logic_manager.send_command_to_device(device_id, command)

    @Slot(str, str)
    def handle_trajectory_playback_started(self, device_id: str, trajectory_name: str):
        """处理轨迹播放开始信号"""
        self.logger.info(f"Coordinator: 轨迹播放开始，设备: {device_id}, 轨迹: {trajectory_name}")
        self.app_status_message.emit(f"轨迹播放开始: {trajectory_name}")

    @Slot(str, str)
    def handle_trajectory_playback_finished(self, device_id: str, trajectory_name: str):
        """处理轨迹播放完成信号"""
        self.logger.info(f"Coordinator: 轨迹播放完成，设备: {device_id}, 轨迹: {trajectory_name}")
        self.app_status_message.emit(f"轨迹播放完成: {trajectory_name}")

    @Slot(str, str)
    def handle_trajectory_playback_error(self, device_id: str, error_message: str):
        """处理轨迹播放错误信号"""
        self.logger.error(f"Coordinator: 轨迹播放错误，设备: {device_id}, 错误: {error_message}")
        self.app_status_message.emit(f"轨迹播放错误: {error_message}")

    @Slot(str, str)
    def handle_trajectory_data_request(self, device_name: str, trajectory_name: str):
        """处理轨迹数据请求"""
        self.logger.info(f"Coordinator: 收到轨迹数据请求，设备: {device_name}, 轨迹: {trajectory_name}")
        
        # 获取当前选择的参数类型
        current_param = self.gui_manager.window.deviceInterface.deep_motor_page.current_selected_param
        
        # 根据参数类型获取轨迹数据
        if current_param.startswith('trajectory_'):
            # 直接使用当前参数
            param_type = current_param
        else:
            # 默认使用轨迹对比
            param_type = "trajectory_both"
        
        trajectory_data = self.device_logic_manager.get_historical_data(
            device_name, 
            param_type, 
            {"trajectory_name": trajectory_name}
        )
        
        if trajectory_data is not None and not trajectory_data.empty:
            self.gui_manager.window.deviceInterface.deep_motor_page.update_history_curve(trajectory_data)
            self.app_status_message.emit(f"轨迹数据已获取并更新到设备: {device_name}")
        else:
            self.app_status_message.emit(f"轨迹数据获取失败，设备: {device_name}")

    @Slot(str)
    def handle_trajectory_list_request(self, device_name: str):
        """处理轨迹列表请求"""
        self.logger.info(f"Coordinator: 收到轨迹列表请求，设备: {device_name}")
        
        # 获取轨迹列表
        trajectory_list = self.device_logic_manager.get_trajectory_list(device_name)
        
        if trajectory_list:
            self.gui_manager.window.deviceInterface.deep_motor_page.update_trajectory_list(trajectory_list)
            self.app_status_message.emit(f"轨迹列表已更新，共 {len(trajectory_list)} 条轨迹")
        else:
            self.app_status_message.emit("暂无轨迹数据")

