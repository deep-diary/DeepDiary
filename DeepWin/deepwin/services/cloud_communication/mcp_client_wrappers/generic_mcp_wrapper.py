# services/cloud_communication/mcp_client_wrappers/generic_mcp_wrapper.py
import asyncio
from fastmcp.client import Client
from typing import Dict, Any, Optional
from PySide6.QtCore import QObject, Signal, Slot # 导入 QObject, Signal, Slot

class GenericFastMCPClientWrapper(QObject): # 继承 QObject 以便使用信号槽
    response_ready = Signal(str, dict) # (mcp_id, data)
    error = Signal(str, str) # (mcp_id, error_message)

    def __init__(self, mcp_id: str, mcp_url: str, api_key: Optional[str], logger: Any, parent=None):
        super().__init__(parent)
        self.mcp_id = mcp_id
        self.mcp_url = mcp_url
        self.api_key = api_key
        self.logger = logger
        self.client = Client(server_url=mcp_url, api_key=api_key, transport="sse") # fastmcp 客户端实例
        self.logger.info(f"FastMCPClientWrapper for '{mcp_id}' initialized.")

    async def call_tool(self, tool_name: str, *args) -> Dict[str, Any]:
        """调用 MCP 服务的 Tool。"""
        try:
            self.logger.debug(f"Calling tool '{tool_name}' on MCP '{self.mcp_id}' with args: {args}")
            # fastmcp client 的工具调用方法
            # Amap Maps 的 maps_weather 工具期望一个 'city' 参数
            if tool_name == "maps_weather" and len(args) > 0:
                city = args[0]
                result = await self.client.tools.call(tool_name, city=city)
            else:
                # 对于其他通用工具调用
                result = await self.client.tools.call(tool_name, *args) 

            self.response_ready.emit(self.mcp_id, {"tool_name": tool_name, "result": result})
            return result
        except Exception as e:
            error_msg = f"调用 MCP '{self.mcp_id}' 的工具 '{tool_name}' 失败: {e}"
            self.logger.error(error_msg)
            self.error.emit(self.mcp_id, error_msg)
            raise

    async def query_resource(self, resource_name: str, **params) -> Dict[str, Any]:
        """查询 MCP 服务的 Resource。"""
        try:
            self.logger.debug(f"Querying resource '{resource_name}' on MCP '{self.mcp_id}' with params: {params}")
            resource_data = await self.client.resources.query(resource_name, **params)
            self.response_ready.emit(self.mcp_id, {"resource_name": resource_name, "data": resource_data})
            return resource_data
        except Exception as e:
            error_msg = f"查询 MCP '{self.mcp_id}' 的资源 '{resource_name}' 失败: {e}"
            self.logger.error(error_msg)
            self.error.emit(self.mcp_id, error_msg)
            raise

    async def close(self):
        """关闭底层 HTTP 客户端连接 (如果 fastmcp 客户端支持)。"""
        # fastmcp client 通常不需要显式关闭，如果底层是 httpx，可能需要
        if hasattr(self.client, 'http_client') and hasattr(self.client.http_client, 'aclose'):
           await self.client.http_client.aclose()
        self.logger.info(f"FastMCPClientWrapper for '{self.mcp_id}' closed.")