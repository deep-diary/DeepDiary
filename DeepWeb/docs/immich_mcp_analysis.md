# Immich-MCP 详细分析

## 概述

`immich-mcp` 是一个 **Model Context Protocol (MCP) 服务器**，用于将 Immich 照片管理系统与 AI 模型（如 Claude、GPT 等）集成。它允许 AI 助手通过标准化的工具和接口与 Immich 进行交互。

### 什么是 MCP？

**Model Context Protocol (MCP)** 是由 Anthropic 在 2024 年 11 月开发的开源标准，用于：
- 在大型语言模型（LLM）和外部数据源、工具、服务之间建立安全、实时的交互
- 提供标准化的客户端-服务器架构
- 使 AI 应用能够无缝访问和集成外部信息

### 基本信息

- **PyPI 包名**: `immich-mcp`
- **最新版本**: 0.5.7 (2025年9月3日发布)
- **Python 要求**: Python >= 3.11
- **GitHub 仓库**: [zygou-31/immich-mcp](https://github.com/zygou-31/immich-mcp)
- **PyPI 页面**: https://pypi.org/project/immich-mcp/

---

## 核心功能

根据搜索结果和 MCP 标准，`immich-mcp` 提供以下主要功能：

### 1. **相册管理 (Album Management)**

- **列出相册**: 获取所有相册列表，支持筛选共享或私有相册
- **创建相册**: 创建新的相册
- **管理相册**: 更新、删除相册信息

**示例工具调用**:
```json
{
  "tool": "albums_list",
  "arguments": {
    "shared": false
  }
}
```

### 2. **资产管理 (Asset Operations)**

- **搜索资产**: 智能搜索照片和视频
- **获取资产详情**: 获取特定资产的详细信息
- **更新资产**: 更新资产属性（如标记为收藏、添加标签等）
- **删除资产**: 删除资产
- **上传资产**: 上传新的照片或视频

**示例工具调用**:
```json
{
  "tool": "search_smart",
  "arguments": {
    "query": "beach sunset",
    "type": "IMAGE",
    "size": 10
  }
}
```

```json
{
  "tool": "assets_update",
  "arguments": {
    "assetId": "asset-uuid-here",
    "isFavorite": true
  }
}
```

### 3. **智能搜索 (Smart Search)**

- **语义搜索**: 使用自然语言查询搜索照片
- **类型筛选**: 按照片或视频类型筛选
- **结果限制**: 控制返回结果数量
- **元数据搜索**: 基于 EXIF、标签、人物等元数据搜索

### 4. **用户管理 (User Management)**

- **用户认证**: 处理用户登录和认证
- **用户授权**: 管理用户权限
- **用户资料**: 获取和更新用户信息

### 5. **系统信息 (System Information)**

- **服务器状态**: 获取服务器运行状态
- **版本信息**: 获取 Immich 服务器版本
- **系统指标**: 获取系统统计信息

---

## 安装和配置

### 安装

```bash
# 推荐使用虚拟环境
pip install immich-mcp

# 开发模式安装（包含开发依赖）
pip install -e ".[dev]"
```

### 配置

需要设置以下环境变量：

```bash
# Immich 服务器地址（不需要包含 /api，会自动添加）
export IMMICH_BASE_URL="http://immich.local:2283"
# 或
export IMMICH_BASE_URL="http://127.0.0.1:2283"

# Immich API 密钥
export IMMICH_API_KEY="your-api-key-here"
```

### 运行服务器

推荐使用 `uv` 工具运行：

```bash
# 安装 uv
pip install uv

# 运行开发服务器
uv run mcp dev src/immich_mcp/server.py
```

---

## 使用场景

### 场景1: AI 助手集成

通过 MCP，AI 助手（如 Claude Desktop）可以直接与 Immich 交互：

```
用户: "帮我找一下去年夏天在海边拍的照片"
AI: [调用 search_smart 工具]
    "找到了 15 张去年夏天在海边的照片，需要我展示给你看吗？"
```

### 场景2: 自动化照片管理

AI 可以自动执行照片管理任务：

```
用户: "把所有包含我女朋友的照片标记为收藏"
AI: [调用 search_smart 找到相关照片]
    [调用 assets_update 批量标记为收藏]
    "已成功将 23 张照片标记为收藏"
```

### 场景3: 智能相册创建

AI 可以根据照片内容自动创建相册：

```
用户: "帮我创建一个包含所有宠物照片的相册"
AI: [调用 search_smart 搜索宠物照片]
    [调用 albums_create 创建相册]
    [调用 albums_add_assets 添加照片]
    "已创建'宠物照片'相册，包含 45 张照片"
```

---

## 与现有项目的对比

### immich-mcp vs immich_python_sdk

| 特性 | immich-mcp | immich_python_sdk |
|------|------------|-------------------|
| **用途** | MCP 服务器，用于 AI 集成 | Python SDK，用于程序化访问 |
| **目标用户** | AI 应用、AI 助手 | Python 开发者 |
| **接口** | MCP 协议（标准化工具调用） | Python API（函数调用） |
| **异步支持** | ✅ 原生支持（MCP 协议） | ❌ 同步（可用 asyncio.to_thread） |
| **AI 集成** | ✅ 专为 AI 设计 | ⚠️ 需要额外封装 |
| **使用场景** | Claude Desktop、AI 助手 | Python 脚本、Web 应用 |

### immich-mcp vs 你的 immich_client.py

| 特性 | immich-mcp | immich_client.py |
|------|------------|------------------|
| **协议** | MCP 协议 | 直接 HTTP 调用 |
| **异步** | ✅ 原生异步 | ✅ 原生异步 |
| **AI 集成** | ✅ 专为 AI 设计 | ❌ 需要额外封装 |
| **功能完整性** | ⚠️ 可能不完整 | ✅ 完整实现 |
| **维护** | 社区维护 | 自己维护 |

---

## 实际应用示例

### 示例1: 在 Claude Desktop 中使用

1. **配置 Claude Desktop**:
```json
{
  "mcpServers": {
    "immich": {
      "command": "uv",
      "args": [
        "run",
        "mcp",
        "dev",
        "src/immich_mcp/server.py"
      ],
      "env": {
        "IMMICH_BASE_URL": "http://127.0.0.1:2283",
        "IMMICH_API_KEY": "your-api-key"
      }
    }
  }
}
```

2. **在 Claude Desktop 中对话**:
```
你: "帮我找一下红色衣服的照片"
Claude: [自动调用 search_smart 工具]
        "找到了 12 张包含红色衣服的照片，需要我展示详细信息吗？"
```

### 示例2: 在 Python 应用中使用

```python
# 注意：这需要 MCP 客户端库
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def use_immich_mcp():
    # 连接到 MCP 服务器
    server_params = StdioServerParameters(
        command="uv",
        args=["run", "mcp", "dev", "src/immich_mcp/server.py"],
        env={
            "IMMICH_BASE_URL": "http://127.0.0.1:2283",
            "IMMICH_API_KEY": "your-api-key"
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 初始化
            await session.initialize()
            
            # 调用工具
            result = await session.call_tool(
                "search_smart",
                arguments={
                    "query": "red clothes",
                    "size": 10
                }
            )
            
            print(result)
```

---

## 优势和使用建议

### 优势

1. **标准化**: 使用 MCP 标准，可以与任何支持 MCP 的 AI 应用集成
2. **AI 友好**: 专为 AI 模型设计，工具调用语义清晰
3. **异步支持**: 原生异步，性能好
4. **易于集成**: 配置简单，只需环境变量

### 使用建议

1. **如果你需要 AI 集成**:
   - ✅ **推荐使用 immich-mcp**
   - 特别适合与 Claude Desktop、GPTs 等 AI 应用集成

2. **如果你需要程序化访问**:
   - ✅ **推荐使用 immich_python_sdk** 或你的 `immich_client.py`
   - 更适合 Python 脚本、Web 应用等

3. **混合方案**:
   - 使用 `immich-mcp` 处理 AI 相关的交互
   - 使用 `immich_python_sdk` 或 `immich_client.py` 处理程序化任务

---

## 功能列表（推测）

基于 MCP 标准和 Immich API，`immich-mcp` 可能提供以下工具：

### 相册相关
- `albums_list` - 列出相册
- `albums_get` - 获取相册详情
- `albums_create` - 创建相册
- `albums_update` - 更新相册
- `albums_delete` - 删除相册
- `albums_add_assets` - 添加资产到相册
- `albums_remove_assets` - 从相册移除资产

### 资产相关
- `assets_get` - 获取资产详情
- `assets_search` - 搜索资产
- `search_smart` - 智能搜索
- `assets_update` - 更新资产
- `assets_delete` - 删除资产
- `assets_upload` - 上传资产
- `assets_download` - 下载资产

### 人物相关
- `people_list` - 列出人物
- `people_get` - 获取人物详情
- `people_search` - 搜索人物
- `people_update` - 更新人物信息

### 标签相关
- `tags_list` - 列出标签
- `tags_create` - 创建标签
- `tags_update` - 更新标签
- `tags_delete` - 删除标签

### 系统相关
- `server_info` - 获取服务器信息
- `server_stats` - 获取服务器统计
- `server_version` - 获取版本信息

---

## 参考资料

- **PyPI 页面**: https://pypi.org/project/immich-mcp/
- **MCP 官方文档**: https://modelcontextprotocol.io/
- **Immich API 文档**: https://api.immich.app/
- **GitHub 仓库**: https://github.com/zygou-31/immich-mcp (根据 PyPI 信息推测)

---

## 总结

`immich-mcp` 是一个强大的工具，特别适合：
- ✅ 与 AI 助手（如 Claude Desktop）集成
- ✅ 通过自然语言与 Immich 交互
- ✅ 自动化照片管理任务
- ✅ 智能照片搜索和组织

如果你的项目需要 AI 集成功能，`immich-mcp` 是一个很好的选择。如果主要是程序化访问，现有的 `immich_python_sdk` 或 `immich_client.py` 可能更合适。
