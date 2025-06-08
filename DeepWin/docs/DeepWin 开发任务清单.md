# DeepWin 开发任务清单

## 1. 基础架构搭建

- [x] 1.1 项目初始化

  - [x] 创建项目目录结构
  - [x] 设置开发环境（Python、依赖管理）
  - [x] 配置版本控制
  - [x] 编写基础 README

- [x] 1.2 核心框架搭建
  - [x] 实现应用生命周期管理
  - [x] 实现模块协调与事件分发系统
  - [x] 实现任务调度器
  - [x] 配置日志系统

## 2. 数据管理层开发

- [ ] 2.1 数据库设计与实现

  - [ ] 设计 SQLite 数据库架构
  - [ ] 实现 ORM/DAO 层
  - [ ] 实现数据迁移机制

- [ ] 2.2 日志管理系统
  - [ ] 实现日志记录器
  - [ ] 实现日志文件滚动机制
  - [ ] 实现日志搜索和导出功能

## 3. 服务层开发

- [ ] 3.1 云端通信服务

  - [ ] 实现 RESTful API 客户端
  - [ ] 实现 MQTT 客户端
  - [ ] 实现流媒体客户端
  - [ ] 实现数据同步管理器

- [ ] 3.2 本地硬件通信服务
  - [ ] 实现串口通信模块
  - [ ] 实现 CAN 总线通信模块（如需要）
  - [ ] 实现设备协议解析器
  - [ ] 实现驱动管理系统

## 4. 应用逻辑层开发

- [ ] 4.1 记忆处理模块

  - [ ] 实现图像与视频处理
  - [ ] 实现日记与笔记处理
  - [ ] 实现聊天记录处理
  - [ ] 实现 GPS 轨迹处理

- [ ] 4.2 资源/需求管理器

  - [ ] 实现本地资源管理
  - [ ] 实现需求管理
  - [ ] 实现云端同步逻辑

- [ ] 4.3 设备逻辑管理器

  - [ ] 实现设备状态管理
  - [ ] 实现控制指令转换
  - [ ] 实现示教轨迹管理

- [ ] 4.4 AI 功能协调器

  - [ ] 实现本地 AI 功能集成
  - [ ] 实现云端 AI 服务调用
  - [ ] 实现 AI 模型管理

- [ ] 4.5 智能体层
  - [ ] 实现 Agent Manager
  - [ ] 实现 Agent Communication Bus
  - [ ] 实现 Perception Adapters
  - [ ] 实现 Action Dispatchers
  - [ ] 实现核心智能体（MemoryCurator、ResourceMatcher、DeviceSupervisor、UserAssistant）

## 5. 用户界面开发

- [ ] 5.1 主窗口框架

  - [ ] 实现主窗口布局
  - [ ] 实现主题切换
  - [ ] 实现导航栏

- [ ] 5.2 记忆管理界面

  - [ ] 实现照片与视频视图
  - [ ] 实现日记与笔记视图
  - [ ] 实现聊天记录视图
  - [ ] 实现 GPS 轨迹视图

- [ ] 5.3 设备控制界面

  - [ ] 实现设备列表视图
  - [ ] 实现设备控制面板
  - [ ] 实现状态显示

- [ ] 5.4 资源/需求管理界面

  - [ ] 实现资源列表视图
  - [ ] 实现需求列表视图
  - [ ] 实现匹配建议显示

- [ ] 5.5 设置界面

  - [ ] 实现账户管理
  - [ ] 实现数据同步设置
  - [ ] 实现目录管理
  - [ ] 实现通用设置

- [ ] 5.6 其他界面
  - [ ] 实现日志显示界面
  - [ ] 实现语音交互指示

## 6. 测试与优化

- [ ] 6.1 单元测试

  - [ ] 编写核心模块单元测试
  - [ ] 编写服务层单元测试
  - [ ] 编写数据层单元测试

- [ ] 6.2 集成测试

  - [ ] 编写模块间集成测试
  - [ ] 编写端到端测试

- [ ] 6.3 性能优化
  - [ ] 优化启动速度
  - [ ] 优化内存使用
  - [ ] 优化数据处理性能

## 7. 文档编写

- [ ] 7.1 技术文档

  - [ ] 编写架构设计文档
  - [ ] 编写 API 文档
  - [ ] 编写数据库设计文档

- [ ] 7.2 用户文档
  - [ ] 编写用户手册
  - [ ] 编写安装指南
  - [ ] 编写常见问题解答

## 8. 部署与发布

- [ ] 8.1 打包与分发

  - [ ] 实现自动打包脚本
  - [ ] 配置安装程序
  - [ ] 准备发布包

- [ ] 8.2 发布准备
  - [ ] 准备发布说明
  - [ ] 准备更新日志
  - [ ] 准备发布检查清单



# DeepWin 开发任务清单（Gemini 输出 ）

本文档详细列出了 DeepWin 桌面应用程序的开发任务，依据《DeepWin 软件架构文档》和《DeepWin 软件需求文档》进行组织。已完成的初始框架代码部分将被标记。

## 1. 任务优先级说明

- **高 (High / P0-P1)**：核心功能，直接影响系统的基本可用性或用户核心体验，必须优先实现。
- **中 (Medium / P2)**：重要功能，影响用户体验和核心业务流程，需要尽快实现。
- **低 (Low / P3)**：次要功能，可以提升用户体验，但在不影响核心功能的情况下可延后实现。
- **待定 (TBD)**：优先级尚未明确，需要进一步评估。

## 2. 核心模块与任务

### 2.1 应用程序入口 (`main.py`)

- [x]   **初始化 `QApplication`。**
- [x]   **初始化 `LogManager`。**
- [x]   **初始化 `Coordinator`。**
- [x]   **初始化 `MainWindow` 并显示。**
- [x]   **启动 Qt 事件循环。**
- [x]   **实现应用程序退出前的资源清理。**

### 2.2 用户界面层 (`src/ui/`)

#### 2.2.1 主窗口框架 (`src/ui/main_window.py`)

- [x]   **REQ-UI-001**：实现主窗口基本布局 (导航栏、内容区、状态栏)。
- [x]   **REQ-UI-001**：集成 PySide6-Fluent-Widgets `FluentWindow` 和 `NavigationPanel`。
- [ ]   **REQ-UI-001**：实现主题切换（明亮/黑暗模式）和系统主题自适应。
- [ ]   **REQ-UI-001**：实现导航栏的显示/隐藏或布局自定义功能。
- [x]   **REQ-UI-006**：状态栏显示应用程序状态消息 (通过 `Coordinator` 信号)。

#### 2.2.2 记忆管理界面 (`src/ui/memory_manager_view.py`) - `REQ-UI-002`

- [ ]   **REQ-UI-002**：设计并实现记忆管理界面的整体布局 (顶部搜索/筛选区，主内容区)。
- [ ]   **REQ-UI-002.1**：实现照片与视频网格/列表视图 (使用 `GridView` 或 `ListView`)。
- [ ]   **REQ-UI-002.1**：实现缩略图预览和全屏查看/播放功能。
- [ ]   **REQ-UI-002.1**：实现按时间、地点、人物、标签、类型筛选和排序功能 (集成 `SearchBox`, `ComboBox`, `CalendarPicker`)。
- [ ]   **REQ-UI-002.1**：实现照片/视频基础编辑操作 (旋转、裁剪、简单滤镜)。
- [ ]   **REQ-UI-002.1**：实现人脸标注工具和手动命名功能。
- [ ]   **REQ-UI-002.2**：实现日记与笔记视图 (富文本编辑器，Markdown支持)。
- [ ]   **REQ-UI-002.2**：实现日记/笔记的创建、编辑、删除、搜索和过滤。
- [ ]   **REQ-UI-002.3**：实现聊天记录视图和搜索/筛选功能。
- [ ]   **REQ-UI-002.4**：实现 GPS 轨迹地图可视化。
- [ ]   **REQ-UI-002.4**：实现轨迹与记忆事件的关联显示。
- [ ]   **REQ-UI-007**：集成语音交互状态指示。

#### 2.2.3 设备控制界面 (`src/ui/device_control_view.py`) - `REQ-UI-003`

- [ ]   **REQ-UI-003**：设计并实现设备控制界面的整体布局 (左侧设备列表，右侧控制面板)。
- [ ]   **REQ-UI-003**：实现设备列表展示 (使用 `TreeView` 或 `ListView`) 及状态指示。
- [ ]   **REQ-UI-003**：实现设备概览卡片 (`Card`) 展示关键信息。
- [ ]   **REQ-UI-003**：实现实时传感器数据监控区 (使用 `PlotView` 或 `Chart`)。
- [ ]   **REQ-UI-003**：实现 DeepArm 机械臂控制面板 (关节/坐标控制，示教按钮)。
- [ ]   **REQ-UI-003**：实现 DeepToy 外设控制界面 (PWM 舵机、IO 状态)。
- [ ]   **REQ-UI-003**：实现指令输入/输出控制台。

#### 2.2.4 资源/需求管理界面 (`src/ui/resource_demand_view.py`) - `REQ-UI-004`

- [ ]   **REQ-UI-004**：设计并实现资源/需求管理界面的整体布局 (顶部筛选/搜索，选项卡)。
- [ ]   **REQ-UI-004**：实现“我的资源”、“我的需求”、“匹配建议”选项卡 (使用 `Pivot`)。
- [ ]   **REQ-UI-004**：实现资源和需求列表展示 (使用 `ListView`)，包含详细信息。
- [ ]   **REQ-UI-004**：实现资源和需求的创建、编辑、删除功能。
- [ ]   **REQ-UI-004**：展示来自云端 DeepServer 的匹配建议，包含匹配度 (`ProgressBar`)。

#### 2.2.5 设置界面 (`src/ui/settings_view.py`) - `REQ-UI-005`

- [ ]   **REQ-UI-005**：设计并实现设置界面的整体布局 (左侧导航，右侧表单)。
- [ ]   **REQ-UI-005.1**：实现账户管理界面。
- [ ]   **REQ-UI-005.2**：实现数据同步设置 (频率、冲突策略)。
- [ ]   **REQ-UI-005.3**：实现本地目录管理 (记忆数据扫描目录配置)。
- [ ]   **REQ-UI-005.4**：实现通用设置 (主题、语言、通知)。
- [ ]   **REQ-UI-005**：集成 `ToggleSwitch`, `Slider`, `TextBox`, `ComboBox`, `FolderPickerButton` 等组件。

#### 2.2.6 日志显示界面 (`src/ui/log_viewer_view.py`) - `REQ-UI-006`

- [ ]   **REQ-UI-006**：设计并实现日志显示界面的布局。
- [ ]   **REQ-UI-006**：实现日志级别过滤、搜索、清空和导出功能。
- [ ]   **REQ-UI-006**：实现实时日志滚动显示 (使用 `TextEdit`)。

#### 2.2.7 可复用 UI 组件 (`src/ui/components/custom_widgets.py`)

- [ ]   **REQ-UI-001**：定义并实现 DeepWin 特有的可复用 Fluent Design 组件。

### 2.3 应用逻辑层 (`src/app_logic/`)

#### 2.3.1 核心管理器 (`src/app_logic/core_manager/`) - `REQ-AL-001`

- [x]   **REQ-AL-001.1**：`coordinator.py`：实现 `Coordinator` 类及其与 UI、服务层、数据管理层的连接骨架。
- [x]   **REQ-AL-001.2**：`coordinator.py`：实现 `WorkerRunnable` 和 `WorkerSignals` 用于后台任务封装。
- [x]   **REQ-AL-001.3**：`coordinator.py`：利用 `QThreadPool` 管理异步任务分派。
- [x]   **REQ-AL-001.2**：`coordinator.py`：完善模块协调和事件分发逻辑。
- [x]  **REQ-AL-001.3**：`task_scheduler.py`：实现任务调度器（如定时任务、后台大文件处理队列）。

#### 2.3.2 记忆处理模块 (`src/app_logic/memory_processing/`) - `REQ-AL-002`

- [ ]   **REQ-AL-002**：定义记忆处理模块的公共接口和数据模型。
- [ ]   **REQ-AL-002.1**：`image_video_processing/processor.py`：实现图像与视频处理的核心逻辑。
  - [ ]   **REQ-AL-002.1.1**：本地文件扫描与监控。
  - [ ]   **REQ-AL-002.1.2**：元数据提取（EXIF, GPS）。
  - [ ]   **REQ-AL-002.1.3**：AI 信息提取（人脸、物体、场景语义）。
  - [ ]   **REQ-AL-002.1.4**：集成 Immich API 获取已处理数据。
  - [ ]   **REQ-AL-002.1.5**：本地索引构建。
- [ ]   **REQ-AL-002.2**：`diary_note_processing/processor.py`：实现日记与笔记处理逻辑。
  - [ ]   本地日记的创建、编辑、保存、分词、关键词提取、索引。
- [ ]   **REQ-AL-002.3**：`chat_record_processing/processor.py`：实现聊天记录处理逻辑。
  - [ ]   导入和解析微信聊天记录（集成 WeChat-Dump）。
  - [ ]   内容分析和关键信息提取。
- [ ]   **REQ-AL-002.4**：`gps_track_processing/processor.py`：实现 GPS 轨迹处理逻辑。
  - [ ]   导入和解析 GPS 轨迹数据。
  - [ ]   轨迹清洗、优化和可视化数据准备。
  - [ ]   轨迹与记忆事件的关联。

#### 2.3.3 资源/需求管理器 (`src/app_logic/resource_demand_manager/manager.py`) - `REQ-AL-003`

- [x]   `manager.py`：实现管理器骨架和 `find_matching_resources` 示例方法。
- [ ]   **REQ-AL-003**：实现本地资源和需求信息的管理（CRUD）。
- [ ]   **REQ-AL-003**：与云端 DeepServer 的资源/需求数据双向同步逻辑。
- [ ]   **REQ-AL-003**：本地化的资源/需求搜索和过滤。

#### 2.3.4 设备逻辑管理器 (`src/app_logic/device_logic_manager/manager.py`) - `REQ-AL-004`

- [x]   `manager.py`：实现管理器骨架和 `send_command_to_device` 示例方法。
- [ ]   **REQ-AL-004**：实现抽象控制指令到底层命令的转换。
- [ ]   **REQ-AL-004**：处理原始设备数据的解析和状态模型更新。
- [ ]   **REQ-AL-004**：实现设备状态实时更新、异常检测和告警。
- [ ]   **REQ-AL-004**：管理 DeepArm 示教轨迹的录制、存储和播放。

#### 2.3.5 AI 功能协调器 (`src/app_logic/ai_coordinator/coordinator.py`) - `REQ-AL-005`

- [x]   `coordinator.py`：实现协调器骨架和 `request_cloud_ai_service` 示例方法。
- [ ]   **REQ-AL-005**：协调本地 AI 库 (如 OpenCV) 的调用。
- [ ]   **REQ-AL-005**：管理与 DeepServer AI 服务（大模型、高级识别）的交互。
- [ ]   **REQ-AL-005**：实现本地 AI 模型的加载、管理和更新。

#### 2.3.6 智能体层 (`src/app_logic/agents/`) - `REQ-AL-006`

- [x]   `agent_manager.py`：实现智能体管理器骨架，并连接示例信号。
- [ ]   **REQ-AL-006.1**：`agent_manager.py`：完善智能体生命周期管理、注册和发现机制。
- [x]   `agent_comm_bus.py`：实现智能体通信总线（或基于 PySide6 信号实现内部消息队列）。
- [ ]   **REQ-AL-006.3**：`perception_adapters.py`：实现将 DeepWin 内部数据转换为智能体感知信息的适配器。
- [ ]   **REQ-AL-006.4**：`action_dispatchers.py`：实现将智能体行动指令转化为 DeepWin 内部操作的分发器。
- [x]   `base_agent.py`：定义智能体基类。
- [ ]   **REQ-AL-006.5**：`core_agents/`：实现以下核心智能体：
  - [ ]   `memory_curator_agent.py`：记忆策展智能体。
  - [ ]   `resource_matcher_agent.py`：资源匹配智能体。
  - [ ]   `device_supervisor_agent.py`：设备监控智能体。
  - [ ]   `user_assistant_agent.py`：用户助理智能体。

### 2.4 服务层 (`src/services/`)

#### 2.4.1 云端通信服务 (`src/services/cloud_communication/`) - `REQ-SVC-001`

- [x]   `api_client.py`：实现 `CloudApiClient` 骨架。
- [ ]   **REQ-SVC-001.1**：`api_client.py`：封装 DeepServer RESTful API 调用（认证、CRUD）。
- [ ]   **REQ-SVC-001.1**：集成 Immich API、Mem0 API 调用。
- [ ]   **REQ-SVC-001.1**：实现统一错误处理和重试机制。
- [x]   `mqtt_client.py`：实现 MQTT 客户端骨架。
- [ ]   **REQ-SVC-001.2**：实现与 DeepServer (EMQX) 的 MQTT 连接和收发。
- [x]   `streaming_client.py`：实现流媒体客户端骨架。
- [ ]   **REQ-SVC-001.3**：实现接收 DeepDevice 视频流和 LiveKit 语音流。
- [ ]   **REQ-SVC-001.4**：`data_sync_manager.py`：实现本地与云端数据同步的核心逻辑（增量、冲突解决）。

#### 2.4.2 本地硬件通信服务 (`src/services/hardware_communication/`) - `REQ-SVC-002`

- [x]   `serial_communicator.py`：实现串口通信模块骨架。
- [ ]   **REQ-SVC-002.1**：实现与 DeepArm、DeepToy 的串口连接和数据收发。
- [x]   `can_bus_communicator.py`：实现 CAN 总线通信模块骨架。
- [ ]   **REQ-SVC-002.2**：实现 CAN 总线数据交换和 DBC 文件解析。
- [x]   `device_protocol_parser.py`：实现设备协议解析器骨架。
- [ ]   **REQ-SVC-002.3**：实现不同 DeepDevice 私有协议的解析和命令转换。
- [x]   `driver_manager.py`：实现驱动管理模块骨架。
- [ ]   **REQ-SVC-002.4**：实现本地硬件设备驱动的加载/卸载。

### 2.5 数据管理层 (`src/data_management/`)

- [x]   `log_manager.py`：实现统一日志管理功能（文件、控制台输出）。
- [x]   `local_database.py`：实现 `LocalDatabaseManager` 骨架。
- [ ]   **REQ-DM-001**：实现本地 SQLite 数据库的 ORM/DAO 接口。
- [ ]   **REQ-DM-001**：定义本地数据库表结构（与云端 PostgreSQL 保持一致性，但为 SQLite 优化）。
- [ ]   **REQ-DM-001**：实现关键数据的本地加密存储。
- [ ]   **REQ-DM-002**：完善日志文件滚动、搜索和导出功能。

## 3. 辅助/基础设施任务

### 3.1 配置管理 (`config/settings.ini`, `src/utils/config.py`)

- [ ]   定义并实现 `config.py`，用于加载 `settings.ini` 中的配置。
- [ ]   将所有硬编码的配置项（如 API 地址、默认路径）迁移到 `settings.ini`。

### 3.2 实用工具 (`src/utils/`)

- [ ]   `constants.py`：定义项目中使用的常量。
- [ ]   `exceptions.py`：定义自定义异常类。
- [ ]   其他通用工具函数。

### 3.3 文档 (`docs/`)

- [x]   `DeepWin_Software_Architecture.md`：软件架构文档（当前文档已完成）。
- [ ]   `User_Manual_Draft.md`：用户手册草稿。
- [ ]   更新并维护所有文档，确保与代码实现同步。

### 3.4 媒体资源 (`media/`)

- [ ]   收集并组织应用程序图标、UI 元素图片、示例图片等。

### 3.5 模型文件 (`models/`)

- [x]   创建 `models/.gitkeep` 占位符。
- [ ]   根据需要将本地 AI 模型文件放置在此目录。

### 3.6 输出目录 (`output/`)

- [x]   创建 `output/.gitkeep` 占位符。

### 3.7 测试 (`tests/`)

- [x]   创建 `tests/.gitkeep` 占位符。
- [ ]   为各个核心模块编写单元测试。
- [ ]   编写集成测试用例。

### 3.8 依赖管理 (`requirements.txt`)

- [ ]   根据实际使用的库，维护并更新 `requirements.txt`。

### 3.9 环境变量 (`.env.example`)

- [x]   创建 `.env.example` 示例文件。
- [ ]   定义和使用必要的环境变量（如敏感凭证）。

这份清单将作为您在 DeepWin 项目开发过程中的路线图。请按照优先级和模块划分逐步完成各项任务。
