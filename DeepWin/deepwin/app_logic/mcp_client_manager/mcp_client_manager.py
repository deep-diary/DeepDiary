from PySide6.QtCore import QObject, Signal, Slot
from typing import Dict, Any
import asyncio
from deepwin.config.config_manager import ConfigManager
from deepwin.data_management.log_manager import LogManager
from deepwin.services.cloud_communication.mcp_client_wrappers.generic_mcp_wrapper import GenericFastMCPClientWrapper

# mcp_client_manager.py
class MCPClientManager(QObject):
    mcp_response_ready = Signal(str, dict) # (mcp_id, data)
    mcp_error = Signal(str, str) # (mcp_id, error_message)

    def __init__(self, config_manager: ConfigManager, log_manager: LogManager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.logger = log_manager.get_logger("MCPClientManager")
        self._mcp_wrappers: Dict[str, GenericFastMCPClientWrapper] = {}
        self._load_mcp_configurations()

    def _load_mcp_configurations(self):
        # 从 config_manager 加载所有 MCP 配置
        # 例如：app_settings.json 中有一个 "mcp_services" 列表
        mcp_configs = self.config_manager.get('mcp_services', [])
        for config in mcp_configs:
            mcp_id = config.get("id")
            mcp_url = config.get("url")
            mcp_api_key = config.get("api_key") # 可选
            # TODO: 配置文件有问题，或者本地未包含node.js, 暂时屏蔽
            # if mcp_id and mcp_url:
            #     # 直接使用已导入的类
            #     wrapper = GenericFastMCPClientWrapper(
            #         mcp_id, mcp_url, mcp_api_key, self.logger # 传入 logger
            #     )
            #     # 连接 wrapper 的信号到 MCPClientManager 的信号
            #     wrapper.response_ready.connect(self.mcp_response_ready)
            #     wrapper.error.connect(self.mcp_error)
            #     self._mcp_wrappers[mcp_id] = wrapper
            #     self.logger.info(f"MCPClientManager: 已注册 MCP 服务 '{mcp_id}' (URL: {mcp_url})")
            # else:
            #     self.logger.warning(f"MCPClientManager: 无效的 MCP 配置: {config}")

    @Slot(str, str, list)
    async def perform_action(self, mcp_id: str, tool_name: str, args: list) -> Dict[str, Any]:
        """
        向指定 MCP 服务执行 Tool 调用。
        :param mcp_id: 目标 MCP 服务的标识符。
        :param tool_name: 要调用的 Tool 名称。
        :param args: Tool 的参数。
        """
        wrapper = self._mcp_wrappers.get(mcp_id)
        if not wrapper:
            raise ValueError(f"未找到 MCP 服务 '{mcp_id}' 的封装器。")
        return await wrapper.call_tool(tool_name, *args)

    @Slot(str, str, dict)
    async def query_resource(self, mcp_id: str, resource_name: str, params: dict) -> Dict[str, Any]:
        """
        向指定 MCP 服务查询 Resource。
        :param mcp_id: 目标 MCP 服务的标识符。
        :param resource_name: 要查询的 Resource 名称。
        :param params: Resource 的查询参数。
        """
        wrapper = self._mcp_wrappers.get(mcp_id)
        if not wrapper:
            raise ValueError(f"未找到 MCP 服务 '{mcp_id}' 的封装器。")
        return await wrapper.query_resource(resource_name, **params)

    def cleanup(self):
        for wrapper in self._mcp_wrappers.values():
            # 异步关闭 HTTP 客户端，确保所有 await 结束
            try:
                asyncio.run(wrapper.close()) 
            except RuntimeError as e:
                self.logger.warning(f"清理 MCP wrapper 失败: {e}. 可能在非事件循环中调用异步操作.")