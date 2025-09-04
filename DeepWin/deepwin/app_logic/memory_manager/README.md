# DeepWin 记忆管理模块

## 概述

DeepWin 记忆管理模块基于 `mem0` 库实现，提供了强大的长期记忆存储和检索功能。该模块支持多种类型的记忆，包括语义记忆、情景记忆和程序性记忆。

## 目录结构

```
memory_manager/
├── __init__.py
├── config.py              # 记忆管理配置和示例代码
├── mem0_manager.py        # mem0 库的封装管理器
└── README.md              # 本文档
```

## 主要功能

### 1. 记忆存储

- 支持对话历史记录存储
- 支持元数据标签
- 支持用户 ID 和代理 ID
- 自动向量化和索引

### 2. 记忆检索

- 语义搜索
- 基于关键词的检索
- 支持过滤和排序
- 支持上下文相关搜索

### 3. 记忆类型

- **短期记忆**: 临时存储的对话信息
- **长期记忆**: 持久化的语义和情景信息
- **程序性记忆**: 操作步骤和流程记忆

## 配置说明

### 环境变量

```bash
# 必需的环境变量
DASHSCOPE_API_KEY=your_dashscope_api_key      # 用于文本嵌入
DEEPSEEK_API_KEY=your_deepseek_api_key        # 用于LLM推理
MEM0_API_KEY=your_mem0_api_key                # mem0服务API密钥
```

### 配置结构

```python
config = {
    "vector_store": {
        "provider": "faiss",                    # 向量存储提供商
        "config": {
            "collection_name": "test",          # 集合名称
            "path": "./faiss_db"                # 存储路径
        }
    },
    "llm": {
        "provider": "langchain",                # LLM提供商
        "config": {
            "model": model_instance              # 模型实例
        }
    },
    "embedder": {
        "provider": "langchain",                # 嵌入模型提供商
        "config": {
            "model": embedding_model            # 嵌入模型实例
        }
    },
    "history_db_path": "./history.db",          # 历史数据库路径
    "version": "v1.1"                          # 配置版本
}
```

## 使用方法

### 1. 基本使用

```python
from deepwin.app_logic.memory_manager.config import Memory, create_memory_config

# 创建配置
config = create_memory_config()

# 初始化记忆实例
memory = Memory.from_config(config)

# 添加记忆
messages = [
    {"role": "user", "content": "Hello, how are you?"},
    {"role": "assistant", "content": "I'm doing well, thank you!"}
]

result = memory.add(
    messages=messages,
    user_id="user123",
    metadata={"category": "greeting", "source": "chat"}
)

# 搜索记忆
search_results = memory.search(
    "how are you",
    user_id="user123"
)
```

### 2. 高级功能

```python
# 批量添加记忆
batch_messages = [
    [
        {"role": "user", "content": "What's the weather like?"},
        {"role": "assistant", "content": "It's sunny today."}
    ],
    [
        {"role": "user", "content": "What should I wear?"},
        {"role": "assistant", "content": "Light clothing would be good."}
    ]
]

for i, msg_batch in enumerate(batch_messages):
    memory.add(
        messages=msg_batch,
        user_id="user123",
        metadata={"category": "weather", "batch_id": i}
    )

# 带过滤器的搜索
filtered_results = memory.search(
    "clothing recommendations",
    user_id="user123",
    categories=["weather"],
    metadata={"category": "weather"}
)
```

## 注意事项

### 1. 已知问题

- 当前版本存在一个警告：`Error iterating new_memories_with_actions: 'list' object has no attribute 'get'`
- 这个警告不影响主要功能，但会在日志中显示

### 2. 性能考虑

- 大量记忆存储时，建议使用批量操作
- 定期清理过期的临时记忆
- 监控向量数据库的大小和性能

### 3. 安全考虑

- API 密钥应妥善保管，不要硬编码在代码中
- 用户数据应进行适当的访问控制
- 定期备份重要的记忆数据

## 错误处理

### 常见错误及解决方案

1. **配置错误**

   ```python
   # 错误：缺少必需的API密钥
   # 解决：确保所有必需的环境变量都已设置
   ```

2. **网络错误**

   ```python
   # 错误：API调用失败
   # 解决：检查网络连接和API密钥有效性
   ```

3. **存储错误**
   ```python
   # 错误：向量存储初始化失败
   # 解决：检查存储路径权限和磁盘空间
   ```

## 开发指南

### 1. 扩展功能

- 继承 `Memory` 类添加自定义功能
- 实现自定义的记忆类型
- 添加新的搜索算法

### 2. 测试

```bash
# 运行测试
cd DeepWin
python deepwin/app_logic/memory_manager/config.py
```

### 3. 日志

- 使用 `LogManager` 进行统一的日志管理
- 记录关键操作和错误信息
- 支持不同级别的日志输出

## 依赖项

- `mem0ai>=0.1.116`: 核心记忆管理库
- `langchain`: LLM 集成
- `langchain-community`: 社区模型支持
- `faiss-cpu`: 向量存储
- `sqlalchemy`: 数据库操作

## 版本历史

- **v1.1**: 当前版本，支持基本的记忆存储和检索
- **v1.0**: 初始版本，基础功能实现

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 项目 Issues: [GitHub Issues]
- 邮箱: [项目维护者邮箱]

---

**注意**: 本文档会随着项目的发展持续更新，请定期查看最新版本。
