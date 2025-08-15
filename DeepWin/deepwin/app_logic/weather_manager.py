# src/app_logic/weather_manager.py
import asyncio
from PySide6.QtCore import QObject, Signal, Slot
from typing import Dict, Any

# NEW: 导入 MCPClientManager 和 WeatherDataAdapter
from deepwin.app_logic.mcp_client_manager.mcp_client_manager import MCPClientManager
from deepwin.services.cloud_communication.mcp_client_wrappers.data_adapters import WeatherDataAdapter
from deepwin.data_management.log_manager import LogManager # 假设有LogManager

class WeatherManager(QObject):
    weather_info_ready = Signal(dict) # 信号：天气信息已准备好 (adapted_data)
    weather_error = Signal(str)      # 信号：天气查询错误 (error_message)

    def __init__(self, mcp_client_manager: MCPClientManager, log_manager: LogManager, parent=None):
        super().__init__(parent)
        self.mcp_client_manager = mcp_client_manager
        self.logger = log_manager.get_logger("WeatherManager")

        # 连接 MCPClientManager 的通用错误信号，用于捕获来自 MCP 的错误
        self.mcp_client_manager.mcp_error.connect(self._handle_mcp_error)
        # 对于特定响应，也可以连接 mcp_response_ready 并根据 mcp_id 过滤
        # 但这里我们将直接在 perform_weather_query 中处理结果

    @Slot(str)
    def query_city_weather(self, city_name: str):
        """
        根据城市名称查询天气。
        这个方法是一个槽，可以从 UI 线程调用。
        它将启动一个异步任务来执行 MCP 调用。
        """
        self.logger.info(f"WeatherManager: 收到查询城市 '{city_name}' 天气的请求。")
        # 在 PyQt 中，直接在槽函数中调用 asyncio.run() 是不推荐的
        # 更好的方式是使用 QThreadPool 或 QThread 来运行异步代码
        # 简化起见，这里直接使用 asyncio.create_task (假定已有运行中的事件循环)
        # 或者通过一个 WorkerRunnable 来桥接

        # 实际应用中，你可能需要一个 QThreadPool 来运行异步任务
        # from deepwin.app_logic.core_manager.coordinator import WorkerRunnable # 假设WorkerRunnable可用
        # worker = WorkerRunnable(self._async_query_weather, city_name)
        # self.thread_pool.start(worker) # 需要在 __init__ 中注入 thread_pool

        # 假设当前环境支持直接调用异步函数 (例如通过 PySide6-Asyncio)
        asyncio.create_task(self._async_query_weather(city_name))

    async def _async_query_weather(self, city_name: str):
        """异步执行天气查询逻辑。"""
        try:
            # 调用 MCPClientManager 发起 Tool 调用
            # Amap Maps MCP 的 ID 为 "amap_maps_mcp"，工具名为 "maps_weather"
            # 参数为 city 名称
            self.logger.debug(f"WeatherManager: 调用 Amap Maps MCP 的 maps_weather 工具，城市: {city_name}")
            raw_weather_data = await self.mcp_client_manager.perform_action(
                "amap_maps_mcp", "maps_weather", [city_name]
            )
            self.logger.debug(f"WeatherManager: 收到原始天气数据: {raw_weather_data}")

            # 使用数据适配器转换数据
            adapted_weather = WeatherDataAdapter.adapt(raw_weather_data)
            self.logger.info(f"WeatherManager: 已获取并适配天气数据: {adapted_weather}")
            self.weather_info_ready.emit(adapted_weather)

        except Exception as e:
            error_message = f"查询城市 '{city_name}' 天气失败: {e}"
            self.logger.error(f"WeatherManager: {error_message}")
            self.weather_error.emit(error_message)

    @Slot(str, str)
    def _handle_mcp_error(self, mcp_id: str, error_msg: str):
        """处理来自 MCPClientManager 的通用错误。"""
        self.logger.error(f"WeatherManager: 来自 MCP '{mcp_id}' 的错误: {error_msg}")
        # 如果是天气相关的错误，可以进一步处理或发出特定信号
        if mcp_id == "amap_maps_mcp":
            self.weather_error.emit(f"高德地图天气服务错误: {error_msg}")