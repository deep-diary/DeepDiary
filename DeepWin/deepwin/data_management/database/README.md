# DeepWin Database Module

DeepWin 数据库模块，提供本地数据库管理功能，支持 SQLite 关系数据库和 Qdrant 向量数据库。

## 🚀 新特性

### 1. 配置管理统一化

- 所有数据库类都使用统一的`ConfigManager`实例
- 配置集中管理，避免重复定义
- 支持动态配置更新

### 2. SQLAlchemy ORM 集成

- 使用 SQLAlchemy ORM 替代原生 SQLite 操作
- 提供更好的类型安全和关系映射
- 支持异步操作和连接池管理

### 3. LangChain 集成优化

- 使用`langchain-qdrant`提供更好的 AI 集成
- 支持向量搜索和语义查询
- 为未来的 LangChain/LangGraph 集成做准备

### 4. 本地文件数据库支持

- Qdrant 支持本地文件存储
- 数据本地化，便于离线使用
- 为未来云端同步预留接口

### 5. 混合方法 (Hybrid Methods) 支持 🆕

- 支持 Python 对象和 SQL 表达式两种调用方式
- 提高查询性能（数据库层面过滤）
- 代码更清晰，逻辑更统一

### 6. 事件监听 (Event Listeners) 支持 🆕

- 自动处理数据变更（如更新时间戳）
- 维护数据一致性
- 支持业务逻辑的自动化

### 7. 关系映射 (Relationships) 支持 🆕

- 支持模型间的关联关系
- 级联删除和更新
- 简化复杂查询操作

### 8. 扩展数据类型支持 🆕

- **EmailType**: 自动验证邮箱格式，支持国际化
- **PhoneNumberType**: 自动验证电话号码，支持国际号码格式
- **CountryType**: 标准国家代码，支持 ISO 3166-1 标准

## 📁 目录结构

```
database/
├── __init__.py              # 包初始化文件
├── base_database.py         # 数据库基类
├── sqlite_manager.py        # SQLite管理器（SQLAlchemy）
├── qdrant_manager.py        # Qdrant管理器（langchain-qdrant）
├── database_factory.py      # 数据库工厂
├── database_coordinator.py  # 数据库协调器
├── models/                  # 数据模型
│   ├── __init__.py
│   ├── base_model.py        # 模型基类
│   ├── user_model.py        # 用户模型
│   ├── need_model.py        # 需求模型
│   ├── resource_model.py    # 资源模型
│   └── photo_model.py       # 照片模型
├── demo.py                  # 演示程序
└── README.md                # 本文档
```

## 🏗️ 架构设计

### 核心组件

1. **BaseMixin**: SQLAlchemy 模型混合类

   - 提供通用功能（id, created_at, updated_at）
   - 支持混合方法和属性
   - 序列化和反序列化支持

2. **BaseModel**: 数据模型基类

   - 继承自 BaseMixin 和 QObject
   - 支持 Qt 信号和事件监听
   - 变更检测和验证

3. **SQLiteManager**: SQLite 数据库管理器

   - 使用 SQLAlchemy ORM
   - 支持事务和连接池
   - 自动表结构管理

4. **QdrantManager**: 向量数据库管理器

   - 集成 langchain-qdrant
   - 支持本地文件存储
   - 向量搜索和元数据过滤

5. **DatabaseFactory**: 数据库工厂

   - 统一创建数据库实例
   - 管理数据库生命周期
   - 支持多种数据库类型

6. **DatabaseCoordinator**: 数据库协调器
   - 管理多个数据库连接
   - 支持跨数据库事务
   - 统一错误处理和日志

### 数据模型

1. **UserModel**: 用户模型

   - 基本信息（用户名、邮箱、电话）
   - 位置信息（国家、城市、公司、行业、职位）
   - 扩展数据类型：EmailType, PhoneNumberType, CountryType
   - 混合方法：`is_complete_profile`, `is_senior_position`, `has_avatar`, `is_international_user`

2. **NeedModel**: 需求模型

   - 需求信息（标题、描述、分类）
   - 优先级和状态管理
   - 混合方法：`is_urgent`, `is_due_soon`, `has_progress`

3. **ResourceModel**: 资源模型

   - 资源类型和状态管理
   - 标签和分类系统
   - 混合方法：`is_type`, `is_status`, `has_tag`

4. **PhotoModel**: 照片模型
   - 文件信息和元数据
   - 位置和时间信息
   - 混合方法：`is_recent_photo`, `is_location`, `is_mime_type`

## ⚙️ 配置说明

### 数据库配置

在 `config.json` 中添加：

```json
{
  "database": {
    "sqlite": {
      "path": "data/deepwin.db",
      "echo": false,
      "pool_size": 10,
      "max_overflow": 20
    },
    "qdrant": {
      "local_path": "data/qdrant",
      "host": "localhost",
      "port": 6333,
      "api_key": null,
      "vector_sizes": {
        "user_embeddings": 1536,
        "photo_embeddings": 512,
        "memory_embeddings": 1536
      }
    }
  }
}
```

## 🚀 快速开始

### 1. 基本使用

```python
from deepwin.data_management.database import DatabaseCoordinator, ConfigManager
from deepwin.data_management.database.models import UserModel, NeedModel

# 初始化
config_manager = ConfigManager(log_manager)
coordinator = DatabaseCoordinator(config_manager)

# 连接数据库
await coordinator.connect_all_databases()

# 创建用户
user = UserModel(
    config_manager=config_manager,
    username="张三",
    email="zhangsan@example.com",
    phone="+86-138-0013-8000",
    country="CN",
    city="北京"
)

# 验证数据（EmailType 和 PhoneNumberType 会自动验证）
if user.validate():
    print("用户数据有效")
```

### 2. 扩展数据类型使用

```python
# 邮箱自动验证
user.email = "invalid-email"  # 会抛出验证错误
user.email = "valid@example.com"  # 正常

# 电话号码自动验证和格式化
user.phone = "13800138000"  # 自动格式化为标准格式
user.phone = "+1-555-123-4567"  # 支持国际号码

# 国家代码
user.country = "CN"  # 中国
user.country = "US"  # 美国
```

### 3. 混合方法使用

```python
# Python 对象调用
if user.is_complete_profile(0.8):
    print("用户资料完整")

if user.is_international_user():
    print("国际用户")

if user.has_valid_contact():
    print("有有效联系方式")

# 数据库查询（更高效）
from sqlalchemy.orm import Session
session = Session()

# 查询资料完整的用户
complete_users = session.query(UserModel).filter(
    UserModel.is_complete_profile(0.8)
).all()

# 查询国际用户
international_users = session.query(UserModel).filter(
    UserModel.is_international_user()
).all()

# 查询有有效联系方式的用户
contact_users = session.query(UserModel).filter(
    UserModel.has_valid_contact()
).all()
```

### 4. 关系查询

```python
# 查询用户及其需求
user = session.query(UserModel).filter(UserModel.id == 1).first()
user_needs = user.needs  # 自动获取关联的需求

# 查询特定用户的高优先级需求
urgent_needs = session.query(NeedModel).filter(
    NeedModel.user_id == user.id,
    NeedModel.is_urgent()
).all()
```

### 5. 事件监听

```python
# 事件会自动触发
@user.model_created.connect
def on_user_created(model_type, model_id):
    print(f"用户 {model_id} 创建成功")

@user.model_updated.connect
def on_user_updated(model_type, model_id):
    print(f"用户 {model_id} 更新成功")
```

## 🔧 高级功能

### 1. 混合方法定义

```python
class UserModel(BaseModel):
    @hybrid_method
    def is_complete_profile(self, min_rate: float = 0.7) -> bool:
        """Python 对象版本"""
        return self.profile_completion_rate >= min_rate

    @is_complete_profile.expression
    def is_complete_profile(cls, min_rate: float = 0.7):
        """数据库表达式版本"""
        return func.coalesce(cls.username, '') != ''
```

### 2. 事件监听器

```python
@event.listens_for(BaseModel, 'before_insert')
def before_insert_listener(mapper, connection, target):
    """插入前事件监听"""
    target.update_timestamps()
    target.model_created.emit(target.__class__.__name__, str(target.id))
```

### 3. 关系定义

```python
class UserModel(BaseModel):
    # 一对多关系
    needs = relationship("NeedModel", back_populates="user", cascade="all, delete-orphan")
    resources = relationship("ResourceModel", back_populates="user", cascade="all, delete-orphan")
    photos = relationship("PhotoModel", back_populates="user", cascade="all, delete-orphan")
```

### 4. 扩展数据类型

```python
from sqlalchemy_utils import EmailType, PhoneNumberType, CountryType

class UserModel(BaseModel):
    email = Column(EmailType, nullable=True, unique=True)
    phone = Column(PhoneNumberType, nullable=True)
    country = Column(CountryType, nullable=True)
```

## 📊 性能优化

### 1. 索引优化

```python
__table_args__ = (
    Index('idx_user_username', 'username'),
    Index('idx_user_email', 'email'),
    Index('idx_user_country', 'country'),
    Index('idx_user_city', 'city'),
)
```

### 2. 混合方法查询

```python
# 使用数据库表达式，避免 Python 层面过滤
recent_users = session.query(UserModel).filter(
    UserModel.is_recent(30)
).all()

# 查询国际用户
international_users = session.query(UserModel).filter(
    UserModel.is_international_user()
).all()
```

### 3. 关系预加载

```python
# 避免 N+1 查询问题
users = session.query(UserModel).options(
    joinedload(UserModel.needs),
    joinedload(UserModel.resources)
).all()
```

## 🧪 测试

### 运行测试

```bash
cd DeepWin
python test_database.py
```

### 运行演示

```bash
cd DeepWin
python deepwin/data_management/database/demo.py
```

## 🔮 未来规划

1. **LangChain/LangGraph 集成**

   - 完整的 AI 工作流支持
   - 智能数据查询和分析

2. **云端同步**

   - 本地数据与云端同步
   - 多设备数据一致性

3. **性能优化**

   - 连接池优化
   - 查询性能调优

4. **更多扩展数据类型**

   - URLType: URL 验证
   - IPAddressType: IP 地址验证
   - ColorType: 颜色值验证

5. **更多混合方法**
   - 复杂业务逻辑的混合方法
   - 自定义 SQL 函数支持

## 📝 注意事项

1. **配置管理**: 所有模型都需要传入 `ConfigManager` 实例
2. **事件监听**: 事件会自动触发，无需手动调用
3. **关系查询**: 使用 `relationship` 定义的关系会自动处理外键
4. **混合方法**: 优先使用数据库表达式版本以提高性能
5. **索引优化**: 根据查询模式合理设置索引
6. **扩展数据类型**: EmailType 和 PhoneNumberType 会自动验证格式
7. **国际化支持**: 支持国际邮箱和电话号码格式

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来改进这个模块！

## 📄 许可证

本项目采用 MIT 许可证。
