# DeepWin

DeepWin 是 DeepDiary 项目的桌面 GUI 应用程序，作为云端与本地设备的桥梁，提供强大的多模态记忆管理和设备控制功能。

## 🚀 功能特点

- **本地记忆管理**: 提供强大、便捷的多模态记忆（照片、视频、日记、聊天记录等）本地管理与追溯能力
- **设备桥接与控制**: 作为 DeepDevice 与云端 DeepServer 之间的桥梁
- **云端数据同步**: 确保本地数据与云端 DeepServer 之间高效、可靠的双向同步
- **智能体宿主**: 为 DeepWin 内部的智能体提供运行环境和协调机制
- **多格式配置支持**: 支持 JSON、YAML、TOML、ENV 等多种配置格式
- **环境配置管理**: 支持开发、测试、生产等不同环境的配置管理

## 🛠️ 开发环境要求

- **Python**: 3.10 或更高版本
- **操作系统**: Windows 10/11
- **依赖库**: 见 `requirements.txt`

## 📦 安装说明

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/DeepDiary.git
cd DeepDiary/DeepWin
```

### 2. 创建虚拟环境

```bash
python -m venv venv
.\venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 安装可选依赖（推荐）

```bash
# 配置管理支持
pip install python-dotenv pyyaml toml

# 其他可选依赖
pip install PySide6  # Qt界面支持
```

## 🏗️ 项目架构

```
DeepWin/
├── main.py                    # 应用程序入口点
├── deepwin/                   # 主要代码包
│   ├── __init__.py           # 包初始化
│   ├── config/               # 配置管理系统
│   │   ├── config_manager.py # 配置管理器
│   │   ├── config_validator.py # 配置验证器
│   │   ├── config.json       # 主配置文件
│   │   ├── config.yaml       # YAML配置
│   │   ├── config.env        # 环境变量
│   │   └── tests/            # 配置测试
│   ├── utils/                # 工具类
│   │   ├── test.py           # 测试基类
│   │   ├── exceptions.py     # 异常定义
│   │   └── constants.py      # 常量定义
│   ├── app_logic/            # 应用逻辑层
│   │   ├── core_manager/     # 核心管理器
│   │   ├── device_logic_manager/ # 设备逻辑管理
│   │   ├── memory_processing/ # 记忆处理
│   │   └── ai_coordinator/   # AI协调器
│   ├── services/             # 服务层
│   │   ├── cloud_communication/ # 云端通信
│   │   ├── hardware_communication/ # 硬件通信
│   │   ├── voice_communication/ # 语音通信
│   │   └── system_processing/ # 系统处理
│   ├── data_management/      # 数据管理层
│   │   ├── database/         # 数据库管理
│   │   ├── log_manager.py    # 日志管理器
│   │   └── config_manager.py # 数据配置管理
│   ├── ui/                   # 用户界面
│   │   ├── app/              # Qt应用
│   │   └── gui_manager.py    # GUI管理器
│   └── tests/                # 测试代码
├── userdata/                  # 用户数据目录
│   ├── img/                  # 图片文件
│   ├── video/                # 视频文件
│   ├── audio/                # 音频文件
│   ├── gps/                  # GPS轨迹
│   ├── wechat/               # 微信数据
│   └── rag/                  # RAG数据
├── database/                  # 数据库文件
├── docs/                      # 项目文档
├── requirements.txt           # 项目依赖
├── setup.py                   # 安装配置
└── README.md                  # 项目说明
```

## 🧪 测试指南

### 运行配置测试

```bash
# 运行配置测试演示
cd deepwin/config
python test_demo.py

# 运行基本演示
python demo.py
```

### 使用测试基类

DeepWin 提供了强大的测试基类 `TestBase` 和 `ConfigTestBase`：

```python
from deepwin.utils.test import ConfigTestBase

class MyConfigTest(ConfigTestBase):
    def test_my_config(self):
        # 使用测试基类提供的方法
        self.print_header("我的配置测试")
        self.assert_equal(actual, expected, "值相等检查")
        # ... 更多测试逻辑
```

## ⚙️ 配置管理

### 配置文件格式

- **JSON**: 标准配置格式，易于程序处理
- **YAML**: 人类可读格式，支持注释和复杂结构
- **TOML**: 简洁的配置格式，适合配置文件
- **ENV**: 环境变量格式，适合敏感信息

### 环境配置

```bash
# 设置环境变量
set DEEPWIN_ENV=production  # Windows
export DEEPWIN_ENV=production  # Linux/Mac
```

### 配置使用示例

```python
from deepwin.config.config_manager import ConfigManager

# 创建配置管理器
config_manager = ConfigManager()

# 获取配置值
theme = config_manager.get("general.theme")
serial_port = config_manager.get("device_settings.deeparm_serial_port")

# 设置配置值
config_manager.set("general.theme", "dark")

# 获取所有配置
all_config = config_manager.get_all()
```

## 🚀 快速开始

### 1. 启动应用程序

```bash
python main.py
```

### 2. 配置环境

- 复制 `deepwin/config/config.env.example` 为 `deepwin/config/config.env`
- 根据你的环境修改配置值

### 3. 运行测试

```bash
# 运行所有测试
python -m pytest deepwin/tests/

# 运行特定测试
python deepwin/config/test_demo.py
```

## 📝 开发指南

### 代码风格

- 遵循 **PEP 8** 规范
- 使用 **类型提示** (Type Hints)
- 编写详细的 **docstrings**
- 使用 **Black** 进行代码格式化

### 提交规范

- 使用语义化提交信息
- 每个功能创建独立分支
- 提交前进行代码审查
- 保持提交的原子性

### 测试规范

- 编写单元测试，保持高覆盖率
- 使用提供的测试基类
- 运行所有测试确保通过
- 测试新功能前先编写测试用例

## 🔧 故障排除

### 常见问题

1. **配置加载失败**: 检查配置文件路径和格式
2. **依赖安装失败**: 确保 Python 版本和虚拟环境正确
3. **测试运行失败**: 检查导入路径和依赖库

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 使用配置验证器
from deepwin.config.config_validator import ConfigValidator
validator = ConfigValidator()
is_valid, errors, warnings = validator.validate_config(config)
```

## 📚 相关文档

- [DeepWin 软件架构文档](docs/DeepWin%20软件架构文档.md)
- [DeepWin 开发任务清单](docs/DeepWin%20开发任务清单.md)
- [DeepWin 完整数据链路流程](docs/DeepWin%20完整数据链路流程.md)

## 📄 许可证

[待定]

## 🤝 联系方式

[待定]

## 🆕 更新日志

### v0.1.0 (当前版本)

- ✅ 重构配置管理系统，支持多格式配置
- ✅ 创建测试基类系统，提供丰富的测试工具
- ✅ 优化项目架构，统一代码组织
- ✅ 支持环境变量配置管理
- ✅ 完善错误处理和日志记录
