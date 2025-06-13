## DeepWin 项目目录结构

DeepWin 桌面 GUI 软件作为 DeepDiary 项目的核心组件之一，其目录结构旨在实现模块化、清晰的职责分离和便捷的维护。以下是经过调整和完善的 DeepWin 应用程序的目录结构：

```
DeepWin/
├── main.py                             # 应用程序入口点，初始化 Coordinator 和 QApplication
├── config.json                         # 全局配置文件 (由 ConfigManager 管理)
├── deeparm.dbc                         # DeepArm 的 CAN 数据库文件示例 (此文件将迁移到 device_protocols/deep_arm_protocol/ 下)
├── requirements.txt                    # 项目依赖库列表
├── README.md                           # 项目说明文档
└── src/
    ├── __init__.py                     # Python 包标识文件
    │
    ├── app_logic/                      # 应用程序业务逻辑层
    │   ├── __init__.py
    │   │
    │   ├── core_manager/               # 核心管理器
    │   │   ├── __init__.py
    │   │   ├── coordinator.py          # 核心协调器 (T类)
    │   │   ├── task_scheduler.py       # 任务调度器 (如定时任务、后台队列)
    │   │   └── workers.py              # 异步任务 worker 封装
    │   │
    │   ├── device_logic_manager/       # 设备逻辑管理器
    │   │   ├── __init__.py
    │   │   ├── manager.py              # 设备逻辑管理器核心实现
    │   │   ├── device_models.py        # 定义所有设备的基类和具体设备的状态数据模型
    │   │   ├── devices/                # 包含具体设备的逻辑实现和命令接口
    │   │   │   ├── __init__.py
    │   │   │   ├── base_device.py      # 定义设备逻辑的基类和通用命令接口
    │   │   │   ├── deep_motor/         # DeepMotor 无刷电机相关实现
    │   │   │   │   ├── __init__.py
    │   │   │   │   └── deep_motor.py   # DeepMotor 逻辑和特定命令
    │   │   │   └── deep_arm/           # DeepArm 机械臂相关实现
    │   │   │       ├── __init__.py
    │   │   │       └── deep_arm.py     # DeepArm 逻辑和特定命令（组合 DeepMotor）
    │   │   └── teaching_trajectory_manager.py # DeepArm 示教轨迹录制、存储和播放管理
    │   │
    │   ├── memory_processing/          # 记忆数据处理模块
    │   │   ├── __init__.py
    │   │   └── image_video_processing/ # 图像/视频处理
    │   │       ├── __init__.py
    │   │       └── processor.py        # 图像/视频处理器
    │   │
    │   ├── resource_demand_manager/    # 资源需求管理器
    │   │   ├── __init__.py
    │   │   └── manager.py              # 资源需求管理器
    │   │
    │   ├── ai_coordinator/             # AI 协调器
    │   │   ├── __init__.py
    │   │   └── coordinator.py          # AI 服务接口协调器
    │   │
    │   └── agents/                     # 智能体模块
    │       ├── __init__.py
    │       └── agent_manager.py        # 智能体管理器
    │
    ├── services/                       # 服务层 (与外部系统或底层硬件交互)
    │   ├── __init__.py
    │   │
    │   ├── cloud_communication/        # 云端通信服务
    │   │   ├── __init__.py
    │   │   └── api_client.py           # 云端 API 客户端
    │   │
    │   └── hardware_communication/     # 本地硬件通信服务
    │       ├── __init__.py
    │       ├── serial_communicator.py  # 串口通信模块
    │       ├── can_bus_communicator.py # CAN 总线通信模块 (含 DBC 解析)
    │       ├── device_protocol_parser.py # 设备协议解析器 (作为管理器和调度器)
    │       ├── driver_manager.py       # 硬件驱动管理器
    │       └── device_protocols/       # 新增：设备特定的协议实现
    │           ├── __init__.py
    │           ├── base_protocol_parser.py # 可选：协议解析器基类
    │           ├── deep_arm_protocol/
    │           │   ├── __init__.py
    │           │   ├── deep_arm_parser.py  # DeepArm 协议的具体实现
    │           │   └── deeparm.dbc         # DeepArm 专用的 DBC 文件
    │           └── deep_motor_protocol/
    │               ├── __init__.py
    │               └── deep_motor_parser.py  # DeepMotor 协议的具体实现
    │
    ├── data_management/                # 数据管理层 (日志、本地数据库、配置)
    │   ├── __init__.py
    │   ├── log_manager.py              # 日志管理器
    │   ├── local_database.py           # 本地数据库管理器 (如 SQLite)
    │   └── config_manager.py           # 配置管理器 (新增)
    │
    └── ui/                             # 用户界面层
        ├── __init__.py
        ├── gui_manager.py              # GUI 界面管理器 (负责窗口、视图切换)
        ├── widgets/                    # 自定义 UI 组件
        │   ├── __init__.py
        │   └── custom_chart_widget.py  # 示例：自定义图表控件
        └── views/                      # 各功能模块的视图 (界面布局和控件)
            ├── __init__.py
            ├── memory_view.py          # 记忆管理视图
            ├── device_control_view.py  # 设备控制视图
            └── settings_view.py        # 设置视图
```
