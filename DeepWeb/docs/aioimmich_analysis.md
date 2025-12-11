# aioimmich 库详细分析

## 概述

`aioimmich` 是一个**异步 Python 库**，用于与 Immich 照片管理系统交互。它主要设计用于 Home Assistant 集成，但也可以用于其他异步 Python 应用。

## 基本信息

- **最新版本**: 0.11.1 (2025年7月23日发布)
- **Python 要求**: Python 3.11 或更高版本
- **主要依赖**: 
  - `aiohttp` - 异步 HTTP 客户端
  - `aiofiles` - 异步文件操作
  - `mashumaro` - 数据序列化
- **开发状态**: 早期开发阶段，可能有破坏性变更

## 核心特性

### 1. **完全异步**
- 使用 `asyncio` 和 `aiohttp` 实现非阻塞操作
- 所有 API 调用都是异步的，使用 `async/await` 语法

### 2. **API 模块结构**

根据测试，`aioimmich` 提供以下 API 模块：

```
Immich
├── albums      # 相册管理
├── api         # 通用 API 调用
├── assets      # 资产管理
├── people      # 人物管理
├── search      # 搜索功能
├── server      # 服务器信息
├── tags        # 标签管理
└── users       # 用户管理
```

### 3. **Search 模块功能**

**当前支持的搜索方法**：
- `async_get_all()` - 获取所有搜索结果
- `async_get_all_by_person_ids()` - 根据人物 ID 搜索
- `async_get_all_by_tag_ids()` - 根据标签 ID 搜索

**❌ 不直接支持智能搜索 (smart_search)**

## 智能搜索支持情况

### 测试结果

经过实际测试，`aioimmich` **目前不直接支持智能搜索功能**：

1. ✅ **连接测试成功** - 可以正常连接到 Immich 服务器
2. ✅ **基本搜索可用** - `async_get_all()` 等方法可以正常工作
3. ❌ **没有 `async_smart_search()` 方法** - Search 模块中没有智能搜索方法
4. ⚠️ **可能有间接方式** - 通过 `search.api.async_do_request()` 可能可以调用，但需要进一步测试

### 可能的解决方案

#### 方案1：使用通用 API 调用方法

```python
# 理论上可以通过 async_do_request 调用，但需要正确的参数格式
# 需要查看源代码确定正确的调用方式
result = await immich.search.api.async_do_request(
    method="POST",
    endpoint="/search/smart",  # 可能需要不同的参数名
    data={...}
)
```

#### 方案2：直接使用 aiohttp

```python
async with aiohttp.ClientSession() as session:
    async with session.post(
        f"{base_url}/api/search/smart",
        headers={"x-api-key": api_key},
        json={"query": "red clothes", ...}
    ) as response:
        result = await response.json()
```

#### 方案3：等待库更新

`aioimmich` 还在早期开发阶段，未来可能会添加智能搜索支持。

## 与 immich_python_sdk 对比

| 特性 | aioimmich | immich_python_sdk |
|------|-----------|-------------------|
| **异步支持** | ✅ 原生异步 | ❌ 同步（可用 asyncio.to_thread 包装） |
| **智能搜索** | ❌ 不直接支持 | ✅ 支持 (`search_smart`) |
| **类型安全** | ⚠️ 部分支持 | ✅ 完整 Pydantic 模型 |
| **API 完整性** | ⚠️ 部分实现 | ✅ 完整实现 |
| **Python 版本** | 3.11+ | 3.7+ |
| **主要用途** | Home Assistant 集成 | 通用 Python 应用 |
| **开发状态** | 早期开发 | 稳定版本 |

## 使用示例

### 基本使用

```python
import asyncio
import aiohttp
from aioimmich import Immich

async def main():
    async with aiohttp.ClientSession() as session:
        # 创建客户端
        immich = Immich(
            session,
            api_key="your-api-key",
            host="127.0.0.1",
            port=2283,
            use_ssl=False
        )
        
        # 获取服务器信息
        about = await immich.server.async_get_about_info()
        print(f"版本: {about.version}")
        
        # 获取所有相册
        albums = await immich.albums.async_get_all_albums()
        for album in albums:
            print(f"相册: {album.name}")
        
        # 搜索资产
        assets = await immich.search.async_get_all()
        print(f"找到 {len(assets)} 个资产")

asyncio.run(main())
```

### 下载资产

```python
async def download_asset(immich, asset_id):
    asset_bytes = await immich.assets.async_view_asset(
        asset_id,
        size="fullsize"  # 或 "thumbnail", "preview"
    )
    with open("image.jpg", "wb") as f:
        f.write(asset_bytes)
```

## 结论和建议

### 对于你的项目

1. **如果主要需要智能搜索**：
   - ❌ **不建议使用 aioimmich** - 目前不支持智能搜索
   - ✅ **建议使用 immich_python_sdk + asyncio.to_thread** - 有完整的智能搜索支持

2. **如果需要完全异步且不需要智能搜索**：
   - ✅ **可以考虑 aioimmich** - 原生异步，性能更好
   - ⚠️ **但要注意** - 功能可能不完整，需要自己实现部分功能

3. **最佳方案（混合）**：
   - 使用 `immich_python_sdk` 进行智能搜索（用 `asyncio.to_thread` 包装）
   - 使用 `aioimmich` 或 `aiohttp` 进行文件下载等 I/O 密集型操作
   - 或者继续使用现有的 `immich_client.py`（已经实现得很好）

### 未来展望

- `aioimmich` 可能会在未来版本中添加智能搜索支持
- 可以关注其 GitHub 仓库（如果公开）或 PyPI 页面获取更新
- 如果急需智能搜索，可以考虑向 `aioimmich` 项目贡献代码

## 参考资料

- PyPI: https://pypi.org/project/aioimmich/
- Libraries.io: https://libraries.io/pypi/aioimmich
- Immich API 文档: https://api.immich.app/
- Immich 智能搜索文档: https://docs.immich.app/features/smart-search/
