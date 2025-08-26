# DeepWin 数据目录

## 📁 目录概述

`data/` 目录是 DeepWin 项目的核心数据存储目录，用于存放各种类型的数据库文件、索引文件、备份文件等。

## 🏗️ 目录结构

```
data/
├── sqlite/                    # SQLite 关系型数据库文件
│   ├── deepwin_demo.db       # 主数据库文件
│   └── *.db                  # 其他 SQLite 数据库文件
├── qdrant/                   # Qdrant 向量数据库文件
│   ├── collection/           # 向量集合存储
│   │   ├── memory_embeddings/   # 记忆向量存储
│   │   ├── photo_embeddings/    # 照片向量存储
│   │   └── user_embeddings/     # 用户向量存储
│   └── meta.json             # 数据库元数据
├── faiss/                    # FAISS 向量索引文件
│   ├── index.faiss          # FAISS 索引文件
│   └── index.pkl            # 索引元数据
└── backup/                   # 数据库备份文件
    ├── sqlite/               # SQLite 备份
    ├── qdrant/               # Qdrant 备份
    └── faiss/                # FAISS 备份
```

## 🗄️ 数据库类型说明

### 1. SQLite 数据库 (`sqlite/`)

- **用途**: 存储结构化数据，如用户信息、设备状态、配置信息等
- **特点**: 轻量级、事务支持、ACID 特性
- **文件扩展名**: `.db`
- **管理工具**: SQLite 命令行工具、DB Browser for SQLite

### 2. Qdrant 向量数据库 (`qdrant/`)

- **用途**: 存储高维向量数据，支持相似性搜索
- **应用场景**:
  - 图像特征向量存储
  - 文本嵌入向量存储
  - 用户行为向量存储
- **特点**: 高性能向量搜索、支持多种距离度量
- **存储格式**: 集合式存储，每个集合包含多个向量

### 3. FAISS 索引 (`faiss/`)

- **用途**: 高效的向量相似性搜索和聚类
- **应用场景**:
  - 大规模向量检索
  - 图像相似性搜索
  - 推荐系统
- **特点**: Facebook 开发，性能优异，支持 GPU 加速
- **文件格式**: `.faiss` (索引文件) + `.pkl` (元数据)

### 4. 备份目录 (`backup/`)

- **用途**: 存储各种数据库的定期备份
- **备份策略**: 按数据库类型分类存储
- **恢复方式**: 支持从备份文件恢复数据库

## 🔧 管理工具

### 路径管理器

项目使用统一的 `PathManager` 来管理数据目录：

```python
from deepwin.utils.path_manager import get_path_manager

path_manager = get_path_manager()

# 获取数据库路径
sqlite_path = path_manager.get_database_path('sqlite')
qdrant_path = path_manager.get_database_path('qdrant')
faiss_path = path_manager.get_database_path('faiss')

# 获取备份路径
backup_path = path_manager.get_backup_path('sqlite')
```

### 数据库协调器

通过 `DatabaseCoordinator` 统一管理所有数据库：

```python
from deepwin.data_management.database.database_coordinator import DatabaseCoordinator

coordinator = DatabaseCoordinator()
coordinator.setup_databases()
coordinator.connect_all_databases()
```

## 📊 数据流向

```
用户输入 → 数据预处理 → 特征提取 → 向量化 → 存储
    ↓
数据查询 → 向量检索 → 相似性计算 → 结果返回
```

## 🚀 性能优化

### 1. 向量数据库优化

- 使用适当的距离度量函数
- 合理设置向量维度
- 定期清理无效向量

### 2. SQLite 优化

- 创建必要的索引
- 使用事务批量操作
- 定期 VACUUM 操作

### 3. FAISS 索引优化

- 选择合适的索引类型
- 根据数据规模调整参数
- 考虑 GPU 加速

## 🔒 安全考虑

### 1. 数据备份

- 定期自动备份
- 多版本备份保留
- 备份文件完整性验证

### 2. 访问控制

- 数据库连接权限管理
- 敏感数据加密存储
- 操作日志记录

### 3. 数据恢复

- 支持增量恢复
- 支持时间点恢复
- 恢复过程验证

## 📝 维护指南

### 日常维护

1. **监控磁盘空间**: 定期检查数据目录大小
2. **性能监控**: 监控查询响应时间
3. **错误日志**: 检查数据库错误日志

### 定期维护

1. **数据清理**: 清理过期或无效数据
2. **索引重建**: 重建数据库索引
3. **备份验证**: 验证备份文件完整性

### 故障处理

1. **连接问题**: 检查数据库服务状态
2. **性能问题**: 分析慢查询日志
3. **数据损坏**: 从备份恢复数据

## 🔗 相关链接

- [SQLite 官方文档](https://www.sqlite.org/docs.html)
- [Qdrant 官方文档](https://qdrant.tech/documentation/)
- [FAISS 官方文档](https://github.com/facebookresearch/faiss)
- [DeepWin 项目文档](../docs/)

## 📞 技术支持

如遇到数据相关问题，请：

1. 查看项目日志文件
2. 检查数据库连接状态
3. 联系项目维护团队

---

_最后更新: 2025-08-26_
_维护者: DeepWin 开发团队_
