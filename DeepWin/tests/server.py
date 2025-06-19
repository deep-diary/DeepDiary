from fastmcp import FastMCP

# 创建一个 MCP 服务器实例
mcp = FastMCP("LocalDemoServer")

# 定义一个工具：相加两个数字
@mcp.tool
def add(a: int, b: int) -> int:
    """相加两个数字"""
    return a + b

# 定义一个资源：动态问候
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """返回个性化问候"""
    return f"Hello, {name}!"

# 运行服务器，使用默认的 Stdio 传输
if __name__ == "__main__":
    mcp.run(transport="stdio")