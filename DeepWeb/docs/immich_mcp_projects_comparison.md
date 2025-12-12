# Immich MCP 相关开源项目对比

本文档整理了所有与 Immich MCP (Model Context Protocol) 相关的开源项目。

---

## 主要项目

### 1. immich-mcp (Python 版本)

**项目信息**:
- **GitHub**: [zygou-31/immich-mcp](https://github.com/zygou-31/immich-mcp)
- **PyPI**: https://pypi.org/project/immich-mcp/
- **最新版本**: 0.5.7 (2025年9月3日)
- **语言**: Python
- **框架**: 基于 MCP Python SDK
- **Python 要求**: >= 3.11

**特点**:
- ✅ 轻量级实现
- ✅ 原生异步支持
- ✅ 简单易用
- ✅ 通过 PyPI 安装

**安装**:
```bash
pip install immich-mcp
```

**配置**:
```bash
export IMMICH_BASE_URL="http://127.0.0.1:2283"
export IMMICH_API_KEY="your-api-key"
```

**运行**:
```bash
uv run mcp dev src/immich_mcp/server.py
```

**功能**:
- 相册管理（列表、创建、更新、删除）
- 资产管理（搜索、更新、删除）
- 智能搜索
- 用户管理
- 系统信息

---

### 2. immich-mcp-server (Node.js 版本)

**项目信息**:
- **GitHub**: [pimpmypixel/immich-mcp-server](https://github.com/pimpmypixel/immich-mcp-server)
- **语言**: Node.js/TypeScript
- **框架**: 基于 OpenAPI 3.0 和 NestJS
- **部署**: Docker 支持

**特点**:
- ✅ 基于 OpenAPI 3.0 规范
- ✅ 自动生成工具架构
- ✅ 完整的 Immich 2.0 API 支持
- ✅ 缓存层支持
- ✅ Docker 容器化
- ✅ 生产就绪

**安装**:
```bash
# 克隆仓库
git clone https://github.com/pimpmypixel/immich-mcp-server.git
cd immich-mcp-server

# 使用 Docker
docker build -t immich-mcp-server .
docker run --env-file .env -p 8000:8000 immich-mcp-server

# 或本地开发
npm install
npm run dev
```

**配置** (`.env` 文件):
```env
IMMICH_API_KEY=your_immich_api_key_here
IMMICH_INSTANCE_URL=https://your-immich-instance.com
PORT=8000
LOG_LEVEL=info
CACHE_TTL=300
```

**功能** (更完整):

#### Albums 工具 (`albumsTool`):
- `albums_list` - 列出所有相册（支持筛选）
- `albums_create` - 创建新相册（可选资产）
- `albums_get` - 通过 ID 获取相册详情
- `albums_update` - 更新相册名称或描述
- `albums_delete` - 删除相册
- `albums_add_assets` - 添加资产到相册
- `albums_remove_assets` - 从相册移除资产

#### Assets 工具 (`assetsTool`):
- `assets_list` - 列出资产（支持分页和筛选）
- `assets_get` - 通过 ID 获取资产详情
- `assets_update` - 更新资产属性（收藏、归档等）
- `assets_delete` - 删除资产
- `assets_bulk_update` - 批量更新多个资产
- `assets_get_statistics` - 获取资产统计信息
- `assets_get_random` - 获取随机资产

#### Search 工具 (`searchTool`):
- `search_general` - 通用搜索（所有实体）
- `search_smart` - AI 驱动的图像识别搜索
- `search_metadata` - 基于 EXIF 元数据和位置的搜索
- `search_explore` - 基于检测到的对象、人脸或地点探索

**优势**:
- 更完整的 API 覆盖
- OpenAPI 3.0 自动生成工具
- 更好的生产环境支持
- 缓存机制提升性能

---

## 项目对比

| 特性 | immich-mcp (Python) | immich-mcp-server (Node.js) |
|------|---------------------|----------------------------|
| **语言** | Python | Node.js/TypeScript |
| **框架** | MCP Python SDK | OpenAPI 3.0 + NestJS |
| **Python 版本** | >= 3.11 | N/A |
| **Node.js 版本** | N/A | >= 14.0.0 (推荐 16+) |
| **安装方式** | PyPI (`pip install`) | GitHub (Docker/npm) |
| **Docker 支持** | ❌ | ✅ |
| **OpenAPI 规范** | ❌ | ✅ |
| **缓存支持** | ❌ | ✅ |
| **工具数量** | ~10+ | ~20+ |
| **生产就绪** | ⚠️ 早期开发 | ✅ 是 |
| **文档** | 基础 | 完整 |
| **维护状态** | 活跃 | 活跃 |
| **学习曲线** | 简单 | 中等 |

---

## 功能对比

### 相册管理

| 功能 | immich-mcp | immich-mcp-server |
|------|------------|-------------------|
| 列出相册 | ✅ | ✅ |
| 创建相册 | ✅ | ✅ |
| 获取相册详情 | ✅ | ✅ |
| 更新相册 | ✅ | ✅ |
| 删除相册 | ✅ | ✅ |
| 添加资产到相册 | ✅ | ✅ |
| 从相册移除资产 | ✅ | ✅ |

### 资产管理

| 功能 | immich-mcp | immich-mcp-server |
|------|------------|-------------------|
| 列出资产 | ✅ | ✅ |
| 获取资产详情 | ✅ | ✅ |
| 更新资产 | ✅ | ✅ |
| 删除资产 | ✅ | ✅ |
| 批量更新 | ❌ | ✅ |
| 获取统计信息 | ❌ | ✅ |
| 获取随机资产 | ❌ | ✅ |
| 上传资产 | ⚠️ 可能支持 | ✅ |

### 搜索功能

| 功能 | immich-mcp | immich-mcp-server |
|------|------------|-------------------|
| 智能搜索 | ✅ | ✅ |
| 通用搜索 | ❌ | ✅ |
| 元数据搜索 | ❌ | ✅ |
| 探索搜索 | ❌ | ✅ |

---

## 使用场景建议

### 选择 immich-mcp (Python) 如果：

- ✅ 你的项目主要是 Python 生态
- ✅ 需要快速上手和简单部署
- ✅ 只需要基本功能
- ✅ 喜欢通过 PyPI 安装
- ✅ 不需要 Docker 容器化

### 选择 immich-mcp-server (Node.js) 如果：

- ✅ 你的项目主要是 Node.js 生态
- ✅ 需要完整的 API 覆盖
- ✅ 需要生产环境部署
- ✅ 需要 Docker 容器化
- ✅ 需要缓存机制提升性能
- ✅ 需要批量操作功能
- ✅ 需要更高级的搜索功能

---

## 其他相关项目

### Immich 社区项目（非 MCP，但相关）

#### 1. Immich Power Tools
- **GitHub**: [varun-raj/immich-power-tools](https://github.com/varun-raj/immich-power-tools)
- **功能**: 高级工具套件，用于组织 Immich 库
- **特点**: 
  - 批量编辑元数据
  - 基于标签自动创建相册
  - 重复检测
  - 人物数据批量更新

#### 2. Immich Tools
- **功能**: 修复和维护 Immich 库的脚本集合
- **用途**: 解决 Immich 修复页面中识别的问题

#### 3. Immich Public Proxy
- **功能**: 在不暴露 Immich 实例的情况下共享照片和相册
- **特点**: 作为安全中介，允许受控访问

#### 4. ImmichFrame
- **功能**: 在相框中运行 Immich 幻灯片
- **用途**: 增强媒体显示选项

#### 5. API Album Sync
- **功能**: 将文件夹同步为相册的 Python 脚本
- **用途**: 简化媒体集合的组织

---

## 安装和使用示例

### immich-mcp (Python) 示例

```python
# 配置环境变量
import os
os.environ['IMMICH_BASE_URL'] = 'http://127.0.0.1:2283'
os.environ['IMMICH_API_KEY'] = 'your-api-key'

# 运行服务器
# uv run mcp dev src/immich_mcp/server.py

# 在 Claude Desktop 配置中使用
# {
#   "mcpServers": {
#     "immich": {
#       "command": "uv",
#       "args": ["run", "mcp", "dev", "src/immich_mcp/server.py"],
#       "env": {
#         "IMMICH_BASE_URL": "http://127.0.0.1:2283",
#         "IMMICH_API_KEY": "your-api-key"
#       }
#     }
#   }
# }
```

### immich-mcp-server (Node.js) 示例

```bash
# 1. 克隆仓库
git clone https://github.com/pimpmypixel/immich-mcp-server.git
cd immich-mcp-server

# 2. 创建 .env 文件
cat > .env << EOF
IMMICH_API_KEY=your_immich_api_key_here
IMMICH_INSTANCE_URL=http://127.0.0.1:2283
PORT=8000
LOG_LEVEL=info
CACHE_TTL=300
EOF

# 3. 使用 Docker 运行
docker build -t immich-mcp-server .
docker run --env-file .env -p 8000:8000 immich-mcp-server

# 或本地运行
npm install
npm run dev
```

---

## 获取 API Key

两个项目都需要 Immich API Key，获取方式：

1. 登录 Immich Web 界面
2. 导航到 **Account Settings** → **API Keys**
3. 点击 **Create API Key**
4. 复制生成的 API Key
5. 在配置中使用

---

## 参考资料

### immich-mcp (Python)
- **PyPI**: https://pypi.org/project/immich-mcp/
- **GitHub**: https://github.com/zygou-31/immich-mcp

### immich-mcp-server (Node.js)
- **GitHub**: https://github.com/pimpmypixel/immich-mcp-server
- **LobeHub**: https://lobehub.com/mcp/pimpmypixel-immich-mcp-server

### Immich 官方
- **官网**: https://immich.app/
- **文档**: https://docs.immich.app/
- **API 文档**: https://api.immich.app/
- **社区项目**: https://docs.immich.app/community-projects/

### MCP 相关
- **MCP 官方文档**: https://modelcontextprotocol.io/
- **MCP Python SDK**: https://github.com/modelcontextprotocol/python-sdk
- **MCP TypeScript SDK**: https://github.com/modelcontextprotocol/typescript-sdk

---

## 总结

目前主要有 **两个** Immich MCP 服务器实现：

1. **immich-mcp** (Python) - 轻量级、简单易用
2. **immich-mcp-server** (Node.js) - 功能完整、生产就绪

选择建议：
- **Python 项目** → 选择 `immich-mcp`
- **Node.js 项目** → 选择 `immich-mcp-server`
- **需要完整功能** → 选择 `immich-mcp-server`
- **快速原型** → 选择 `immich-mcp`

两个项目都在积极维护中，可以根据你的具体需求和技术栈选择合适的实现。
