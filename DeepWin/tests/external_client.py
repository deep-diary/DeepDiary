import asyncio
from fastmcp import Client
import os

async def main():
    # 配置环境变量（与服务器一致）
    os.environ["AMAP_MAPS_API_KEY"] = "fd18a18f74ff824346df1d1c7185f07f"  # 替换为实际 API 密钥

    # 方案1：使用单服务器模式直接连接远程 MCP 服务器
    server_url = "https://mcp.so/server/amap-maps/amap"
    api_key = os.environ["AMAP_MAPS_API_KEY"]
    
    # 使用单服务器模式
    async with Client(server_url) as client:
        # 列出可用工具
        tools = await client.list_tools()
        print(f"可用工具: {tools}")

        # 尝试调用天气工具
        try:
            weather_result = await client.call_tool("maps_weather", {"city": "北京"})
            print(f"天气查询结果: {weather_result}")
        except Exception as e:
            print(f"调用天气工具失败: {e}")

    # 方案2：使用多服务器配置（需要本地 Node.js）
    # config = {
    #     "mcpServers": {
    #         "amap-maps": {
    #             "command": "npx",
    #             "args": ["-y", "@amap/amap-maps-mcp-server"],
    #             "env": {"AMAP_MAPS_API_KEY": os.environ["AMAP_MAPS_API_KEY"]}
    #         }
    #     }
    # }
    # async with Client(config) as client:
    #     # 多服务器模式下工具名需要加前缀
    #     weather_result = await client.call_tool("maps_weather", {"city": "北京"})
    #     print(f"天气查询结果: {weather_result}")

# 运行客户端
if __name__ == "__main__":
    asyncio.run(main())