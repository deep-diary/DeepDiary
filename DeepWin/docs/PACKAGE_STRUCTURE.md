# DeepWin 包结构优化说明

## 优化内容

### 1. 包结构重构

- 将 `src/` 目录重命名为 `deepwin/`
- 删除了多余的 `src/setup.py`
- 保留了根目录的 `setup.py` 并进行了优化

### 2. 导入路径优化

**优化前：**

```python
from deepwin.app_logic.device_logic_manager.devices.deep_motor.command_parser import CommandParser
```

**优化后：**

```python
from deepwin.app_logic.device_logic_manager.devices.deep_motor.command_parser import CommandParser
```

### 3. 包配置优化

根目录 `setup.py` 配置：

```python
packages=find_packages(where="deepwin"),
package_dir={"": "deepwin"},
```

## 使用方法

### 开发模式安装

```bash
pip install -e .
```

### 导入模块

```python
# 导入主包
import deepwin

# 导入具体模块
from deepwin.app_logic.core_manager.coordinator import Coordinator
from deepwin.data_management.log_manager import LogManager
from deepwin.services.hardware_communication import CANBusCommunicator
```

### 相对导入（在包内部）

在 `deepwin` 包内部的模块中，可以使用相对导入：

```python
# 在 deepwin/app_logic/core_manager/coordinator.py 中
from ..device_logic_manager.manager import DeviceLogicManager
from ...services.hardware_communication import CANBusCommunicator
```

## 包结构层次

```
deepwin/                          # 主包
├── __init__.py                  # 包初始化文件
├── app_logic/                   # 应用逻辑层
│   ├── __init__.py
│   ├── agents/                  # 智能体管理
│   ├── ai_coordinator/         # AI协调器
│   ├── core_manager/           # 核心管理器
│   ├── device_logic_manager/   # 设备逻辑管理
│   ├── mcp_client_manager/     # MCP客户端管理
│   ├── memory_processing/      # 内存处理
│   ├── resource_demand_manager/ # 资源需求管理
│   └── weather_manager/        # 天气管理
├── data_management/            # 数据管理层
├── models/                     # 数据模型
├── services/                   # 服务层
├── ui/                        # 用户界面层
└── utils/                     # 工具模块
```

## 优势

1. **导入路径更清晰**：`deepwin` 作为主包名更有意义
2. **包管理更规范**：符合 Python 包管理最佳实践
3. **相对导入支持**：包内部可以使用相对导入，代码更简洁
4. **测试更便利**：每个子包都可以独立测试
5. **部署更简单**：通过 pip 安装后，包会自动添加到 Python 路径中

## 注意事项

1. 安装包后，不再需要手动添加路径到 `sys.path`
2. 在包内部开发时，建议使用相对导入
3. 对外接口建议使用绝对导入，确保稳定性
4. 开发模式下使用 `pip install -e .` 进行安装
