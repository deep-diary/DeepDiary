import json
import httpx
from typing import Any
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="../../../../.env", override=True) 

OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
DeepSeek_API_KEY = os.getenv("DEEPSEEK_API_KEY")
print(f"OPENWEATHER_API_KEY: {OPENWEATHER_API_KEY}")
print(f"DeepSeek_API_KEY: {DeepSeek_API_KEY}")  # 可以通过打印查看

# 初始化 MCP 服务器
mcp = FastMCP("WriteServer")
USER_AGENT = "write-app/1.0"

@mcp.tool()
async def write_file(content: str) -> str:
    """
    将指定内容写入本地文件。
    :param content: 必要参数，字符串类型，用于表示需要写入文档的具体内容。
    :return：是否成功写入
    """
    return "已成功写入本地文件。"

if __name__ == "__main__":
    # 以标准 I/O 方式运行 MCP 服务器
    mcp.run(transport='stdio')