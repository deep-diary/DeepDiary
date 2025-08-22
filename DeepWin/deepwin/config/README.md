# DeepWin 配置管理系统

## 概述

DeepWin 配置管理系统提供了灵活的配置文件管理功能，支持多种配置格式和环境特定的配置。该系统设计为模块化架构，便于扩展和维护。

## 目录结构

```
deepwin/config/
├── __init__.py              # 配置包初始化
├── config_manager.py        # 配置管理器核心类
├── config_validator.py      # 配置验证器
├── config.json             # JSON格式主配置文件
├── config.yaml             # YAML格式配置文件
├── config.env              # 环境变量配置文件
├── demo.py                 # 使用示例
└── README.md               # 本说明文档
```

## 功能特性

### 🚀 **多格式支持**

- **JSON**: 标准配置格式，易于程序处理
- **YAML**: 人类可读格式，支持注释和复杂结构
- **TOML**: 简洁的配置格式，适合配置文件
- **ENV**: 环境变量格式，适合敏感信息

### 🌍 **环境配置**

- 支持开发、测试、生产等不同环境
- 环境特定配置文件自动加载
- 环境变量覆盖支持

### ✅ **配置验证**

- 自动验证配置文件完整性
- 类型检查和业务规则验证
- 详细的错误和警告报告

### 🔧 **配置管理**

- 动态配置加载和重载
- 配置值获取和设置
- 支持点号分隔的键路径

## 核心组件

### 1. ConfigManager (配置管理器)

主要的配置管理类，负责：

- 配置文件加载和解析
- 多格式配置文件支持
- 环境配置管理
- 配置值获取和设置

```python
from deepwin.config.config_manager import ConfigManager

# 创建配置管理器
config_manager = ConfigManager()

# 加载配置
config = config_manager.load_config()

# 获取配置值
theme = config_manager.get_config_value(config, "general.theme")

# 设置配置值
config_manager.set_config_value(config, "general.theme", "dark")
```

### 2. ConfigValidator (配置验证器)

配置验证类，负责：

- 配置文件结构验证
- 数据类型检查
- 业务规则验证
- 错误和警告报告

```python
from deepwin.config.config_validator import ConfigValidator

# 创建验证器
validator = ConfigValidator()

# 验证配置
is_valid, errors, warnings = validator.validate_config(config)

# 获取验证摘要
summary = validator.get_validation_summary()
```

## 配置文件格式

### JSON 格式 (config.json)

```json
{
  "general": {
    "theme": "light",
    "language": "zh_CN"
  },
  "device_settings": {
    "deeparm_serial_port": "COM11"
  }
}
```

### YAML 格式 (config.yaml)

```yaml
general:
  theme: "light"
  language: "zh_CN"

device_settings:
  deeparm:
    serial_port: "COM11"
    baud_rate: 115200
```

### 环境变量格式 (config.env)

```env
# DeepWin 环境配置
APP_ENV=development
DEBUG_MODE=true
DB_HOST=localhost
DB_PASSWORD=your_password

# API密钥配置
LLM_API_KEY=your_llm_api_key_here
VOICE_API_KEY=your_voice_api_key_here
MAPS_API_KEY=your_maps_api_key_here

# 设备配置
DEEPARM_SERIAL_PORT=COM11
DEEPARM_BAUD_RATE=115200
DEEPMOTOR_SERIAL_PORT=COM16
DEEPMOTOR_BAUD_RATE=115200
```

**注意**: `.env` 文件通常包含敏感信息，建议添加到 `.gitignore` 中，避免提交到版本控制系统。

## 环境配置

### 环境变量设置

```bash
# Windows
set DEEPWIN_ENV=production

# Linux/Mac
export DEEPWIN_ENV=production
```

### 环境特定配置文件

系统会自动查找以下配置文件：

1. `config_{env}.json` - 环境特定 JSON 配置
2. `config_{env}.yaml` - 环境特定 YAML 配置
3. `config_{env}.toml` - 环境特定 TOML 配置
4. `config.json` - 默认配置文件

## 使用示例

### 基本使用

```python
from deepwin.config.config_manager import ConfigManager

# 创建配置管理器
config_manager = ConfigManager()

# 加载配置
config = config_manager.load_config()

# 获取配置值
theme = config_manager.get("general.theme")
serial_port = config_manager.get("device_settings.deeparm_serial_port")

# 设置配置值
config_manager.set("general.theme", "dark")

# 获取所有配置
all_config = config_manager.get_all()
```

### 环境配置

```python
# 设置环境
config_manager.set_environment("production")

# 加载特定环境配置
prod_config = config_manager.load_config(env="production")

# 获取当前环境
current_env = config_manager.get_environment_config()

# 重新加载配置
config_manager.reload_config()
```

### 配置验证

```python
from deepwin.config.config_validator import ConfigValidator

# 创建验证器
validator = ConfigValidator()

# 验证配置
is_valid, errors, warnings = validator.validate_config(config)

if is_valid:
    print("配置验证通过")
else:
    print(f"配置验证失败，发现 {len(errors)} 个错误")
    for error in errors:
        print(f"  - {error}")
```

## 最佳实践

### 1. 配置文件组织

- 将敏感信息放在 `.env` 文件中
- 使用环境特定配置文件管理不同环境的配置
- 保持配置文件结构清晰和一致

### 2. 配置验证

- 在应用启动时验证配置
- 使用配置验证器检查配置完整性
- 定期检查配置文件的正确性

### 3. 环境管理

- 使用环境变量控制应用环境
- 为不同环境创建专门的配置文件
- 避免在生产环境中使用开发配置

### 4. 配置更新

- 使用配置管理器的方法更新配置
- 避免直接修改配置文件
- 在更新配置后重新验证

## 扩展开发

### 添加新的配置格式

1. 在 `ConfigManager` 的 `supported_formats` 中添加新格式
2. 实现对应的加载方法
3. 更新配置验证器

### 添加新的验证规则

1. 在 `ConfigValidator` 中添加新的验证方法
2. 更新配置模式定义
3. 在验证流程中调用新规则

## 依赖要求

```bash
# 基本依赖（Python标准库）
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 必需依赖
pip install python-dotenv  # 环境变量支持

# 可选依赖
pip install pyyaml      # YAML支持
pip install toml        # TOML支持
```

## 测试

### 运行测试

```bash
# 运行配置测试演示
cd deepwin/config
python test_demo.py

# 运行基本演示
python demo.py
```

### 测试基类

DeepWin 提供了测试基类 `TestBase` 和 `ConfigTestBase`，位于 `deepwin/utils/test.py`：

```python
from deepwin.utils.test import ConfigTestBase

class MyConfigTest(ConfigTestBase):
    def test_my_config(self):
        # 使用测试基类提供的方法
        self.print_header("我的配置测试")
        self.assert_equal(actual, expected, "值相等检查")
        # ... 更多测试逻辑
```

## 故障排除

### 常见问题

1. **配置文件加载失败**

   - 检查文件路径和权限
   - 验证文件格式是否正确
   - 查看日志文件获取详细错误信息

2. **配置验证失败**

   - 检查配置文件结构
   - 验证必需字段是否存在
   - 检查数据类型是否正确

3. **环境配置不生效**

   - 确认环境变量设置正确
   - 检查环境特定配置文件是否存在
   - 验证环境名称拼写

4. **环境变量加载失败**
   - 确认已安装 `python-dotenv` 库
   - 检查 `.env` 文件格式是否正确
   - 验证文件路径和权限

### 调试技巧

1. **启用详细日志**

   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **使用配置验证器**

   ```python
   validator = ConfigValidator()
   is_valid, errors, warnings = validator.validate_config(config)
   print(validator.get_validation_summary())
   ```

3. **检查配置文件路径**
   ```python
   config_manager = ConfigManager()
   print(f"配置目录: {config_manager.config_dir}")
   ```

## 版本历史

- **v0.1.0**: 初始版本，支持基本配置管理功能
- 支持 JSON、YAML、TOML、ENV 格式
- 环境配置管理
- 配置验证功能

## 维护团队

- **开发团队**: DeepWin Team
- **维护者**: DeepWin 开发团队
- **技术支持**: 通过项目 Issues 或团队联系方式

---

**注意**: 本配置系统遵循 DeepWin 项目的开发规范，如有问题请参考项目文档或联系开发团队。
