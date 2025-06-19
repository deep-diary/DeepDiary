import asyncio
from fastmcp import Client
import ffprint

async def main():
    # 连接到本地服务器（通过 Stdio 传输）
    async with Client("server.py") as client:
        # 列出可用工具
        tools = await client.list_tools()
        print(f"可用工具: {tools}")

        # 调用 add 工具
        result = await client.call_tool("add", {"a": 5, "b": 3})
        
        # print(f"5 + 3 = {result.text}")
        for rst in result:
            print(rst)
            print(f"5 + 3 = {rst.text}")

        # 访问 greeting 资源
        greeting = await client.read_resource("greeting://Alice")
        for rst in greeting:
            print(rst)
            print(f"问候: {rst.text}")
        # ffprint(greeting)
        # print(f"问候: {greeting.text}")

# 运行客户端
if __name__ == "__main__":
    asyncio.run(main())