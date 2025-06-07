# DeepWin 软件架构文档

## 1. 引言

### 1.1 编写目的

本文档旨在详细描述 DeepWin 桌面应用程序的软件架构，为开发团队提供清晰的系统结构、模块划分、技术选型和交互机制等方面的指导。通过本文档，开发人员可以快速理解 DeepWin 的设计理念和实现细节，从而高效地进行开发、测试和维护工作。特别地，本文档将着重阐述如何构建一个具备良好可扩展性的架构，以支持未来智能体（Agent）功能的平滑集成。

### 1.2 目标读者

本文档的目标读者包括：

- 系统架构师
- 软件开发工程师
- 测试工程师
- 运维工程师

### 1.3 术语和缩写

- **DeepWin**：DeepDiary 项目的桌面 GUI 应用程序。
- **DeepServer**：DeepDiary 项目的云端服务器，负责数据存储、API 服务、AI 处理等。
- **DeepDevice**：DeepDiary 项目的硬件设备端，包括 DeepGlass、DeepArm、DeepToy。
- **GUI**：图形用户界面（Graphical User Interface）。
- **API**：应用程序编程接口（Application Programming Interface）。
- **MQTT**：消息队列遥测传输协议（Message Queuing Telemetry Transport）。
- **ORM**：对象关系映射（Object Relational Mapping）。
- **IPC**：进程间通信（Inter-Process Communication）。
- **FOC**：磁场定向控制（Field Oriented Control）。
- **DBC**：数据库文件（CAN bus database file），用于描述 CAN 总线上的消息。
- **Agent（智能体）**：具备感知（Perceive）、推理（Reason）、行动（Act）和通信（Communicate）能力的自主软件实体。
- **MAS（Multi-Agent System）**：多智能体系统。
- **ACP（Agent Communication Protocol）**：智能体通信协议。

## 2. 总体架构

### 2.1 架构概述

DeepWin 应用程序采用**分层架构**与**智能体就绪（Agent-Ready）设计**，旨在实现清晰的职责分离、高内聚低耦合和良好的可维护性。它作为连接用户、本地设备和云端 DeepServer 的关键枢纽，核心定位是**“云端与串口设备的中间桥梁”**，并逐步演变为一个能够**托管和协调智能体**的平台。

DeepWin 的主要职责包括：

1. **本地记忆管理**：管理用户的数字化记忆（照片、视频、日记、聊天记录等）和社会人脉资源，并支持与云端同步。
2. **本地设备交互**：通过串口、USB 等方式与 DeepArm、DeepToy 等嵌入式设备进行通信，实现设备控制、数据接收和指令解析。
3. **云端服务对接**：与 DeepServer 进行数据同步、API 调用、MQTT 消息处理和流媒体接收。
4. **用户界面呈现**：提供直观友好的 GUI 界面，方便用户进行各项操作和数据查看。
5. **本地 AI 处理**：执行部分本地化的图像处理、相机管理和辅助 AI 功能。
6. **智能体托管与协作**：为智能体的运行提供环境，并协调智能体间的通信与任务执行，从而实现主动式的智能服务。

### 2.2 总体架构图

```
@startuml
skinparam handwritten true
skinparam style plain
skinparam defaultFontName "Cascadia Code"
skinparam defaultFontSize 14

package "DeepWin 桌面应用程序" {
  [用户界面层 (UI)] as UI
  package "应用逻辑层 (Application Logic)" {
    [业务逻辑模块] as BusinessLogic
    [智能体层 (Agent Layer)] as AgentLayer
  }
  package "服务层 (Service Layer)" {
    [云端通信服务] as CloudSvc
    [本地硬件通信服务] as HardwareSvc
  }
  [数据管理层 (Data Management)] as DataMgr
}

actor 用户
cloud "DeepServer 云平台" as Server
folder "本地嵌入式设备" as Device {
  [DeepArm]
  [DeepToy]
  [其他串口设备]
}

用户 --> UI : 交互
UI --> BusinessLogic : 用户操作/事件
BusinessLogic --> CloudSvc : 请求云端数据/操作
BusinessLogic --> HardwareSvc : 请求设备数据/控制
BusinessLogic --> DataMgr : 本地数据存储/检索
BusinessLogic --> AgentLayer : 触发智能体行为/提供环境信息

AgentLayer <--> BusinessLogic : 智能体决策/行动反馈
AgentLayer --> CloudSvc : 智能体请求云端服务
AgentLayer --> HardwareSvc : 智能体控制设备
AgentLayer --> DataMgr : 智能体读写本地数据

CloudSvc <--> Server : REST API, MQTT, Streaming
HardwareSvc <--> Device : 串口, CAN, USB

DataMgr <--> [本地 SQLite 数据库] : 数据存储

@enduml
```

### 2.3 架构描述

DeepWin 的分层架构和智能体就绪设计如下：

- **用户界面层 (UI Layer)**：直接与用户交互，负责界面元素的展示、用户输入处理和事件传递。
- **应用逻辑层 (Application Logic Layer)**：DeepWin 的核心，包含业务逻辑模块和智能体层。
  - **业务逻辑模块**：处理传统的、由用户操作驱动的业务流程。
  - **智能体层**：承载 DeepWin 内部的智能体实例，负责智能体的生命周期管理、内部通信和与业务逻辑模块的交互，实现主动式智能。
- **服务层 (Service Layer)**：封装了与外部系统（云端 DeepServer）和本地硬件设备（DeepDevice）的通信细节，对外提供统一的服务接口。
  - **云端通信服务**：负责所有与 DeepServer 的网络通信。
  - **本地硬件通信服务**：负责所有与本地物理设备的通信。
- **数据管理层 (Data Management Layer)**：管理 DeepWin 本地的数据存储（SQLite 数据库）和日志记录，提供数据持久化和访问接口。

## 3. 模块划分与职责

### 3.1 用户界面层 (UI Layer)

- **职责**：负责 DeepWin 的视觉呈现、用户交互（如点击、输入、拖拽）的捕获与传递，以及应用逻辑层返回的数据展示。
- **技术栈**：PySide6-Fluent-Widgets (基于 PySide6)。
- **主要组件**：
  - **主窗口框架**：包括导航栏、内容区、状态栏等，提供应用整体布局。
  - **记忆管理界面**：照片墙、视频播放器、日记编辑器、聊天记录视图等，用于展示和管理用户的多模态记忆。
  - **设备控制界面**：显示连接的 DeepDevice 列表、设备状态、控制面板（如机械臂运动控制、玩具外设控制）。
  - **资源/需求管理界面**：展示用户及其好友的资源和需求列表，支持录入、编辑、搜索。
  - **设置界面**：用户账户管理、数据同步配置、主题设置等。
  - **日志显示界面**：实时显示 DeepWin 运行日志。
- **与应用逻辑层交互**：通过信号/槽机制或事件回调将用户操作传递给应用逻辑层；接收应用逻辑层更新的数据进行界面刷新。

### 3.2 应用逻辑层 (Application Logic Layer)

- **职责**：DeepWin 的大脑，包含核心业务逻辑。它处理来自 UI 层的用户请求，协调服务层与数据管理层完成任务，并执行本地的数据处理和 AI 辅助功能。此外，它还包含智能体层，实现 DeepWin 的主动智能。
- **技术栈**：Python。
- **主要子模块**：
  - **核心管理器 (Core Manager)**：
    - 协调器：负责模块间的调度和数据流转。
    - 任务调度器：管理后台任务（如大文件处理、数据同步）。
  - **记忆处理模块 (Memory Processing)**：
    - **图像与视频处理**：
      - 本地目录扫描与文件解析：扫描用户指定目录，识别图像和视频文件。
      - 元数据提取：从图像 (如 EXIF) 和视频中提取 GPS、时间、长宽、拍摄设备等元数据。
      - AI 信息提取：利用本地或云端 AI (如 Immich API) 提取图像中的人脸数据、物体信息、场景语义信息。
      - 本地索引构建：为照片和视频创建本地索引，方便快速检索。
      - 图像/视频预览与编辑：提供基本预览、剪辑和后期处理功能。
      - 人脸/物体标注与识别：辅助用户对图像中的人脸和物体进行命名和管理。
      - **集成 Immich API**：通过 Immich 提供的 API 获取其处理结果 (如向量化特征、标签、分类)，避免重复开发。
    - **日记与笔记处理**：
      - 文本解析与存储：管理本地日记和笔记的创建、编辑、保存。
      - 关键词提取与索引：对文本内容进行关键词提取，构建本地搜索索引。
    - **聊天记录处理**：
      - 微信聊天记录导入与解析 (利用 WeChat-Dump)：解密和解析本地微信数据库，提取聊天内容、图片、语音等。
      - 内容分析与摘要：对聊天记录进行初步分析，提取关键信息。
    - **GPS 轨迹处理**：
      - 轨迹数据导入与解析：处理来自 DeepGlass 或其他设备的 GPS 轨迹数据。
      - 轨迹可视化：在本地地图组件上展示轨迹。
  - **资源/需求管理器 (Resource/Demand Manager)**：
    - 管理本地存储的用户资源和需求信息。
    - 提供资源/需求录入、编辑、搜索功能。
    - 与云端 DeepServer 进行资源/需求数据的同步。
  - **设备逻辑管理器 (Device Logic Manager)**：
    - 处理与 DeepDevice 设备的复杂业务逻辑。
    - 解析来自硬件通信服务的原始设备数据。
    - 根据用户指令生成设备控制命令。
    - 处理设备状态的实时更新和告警逻辑。
  - **AI 功能协调器 (AI Coordinator)**：
    - 协调本地 AI 库的调用 (如 OpenCV 用于基础图像处理)。
    - 管理与 DeepServer AI 服务的交互，例如调用大模型进行复杂自然语言理解、知识问答。
  - **智能体层 (Agent Layer)**：
    - **Agent Manager (智能体管理器)**：
      - 负责 DeepWin 内部智能体的生命周期管理（实例化、启动、停止、销毁）。
      - 提供智能体注册和发现机制。
      - 协调智能体间的任务分配和优先级。
    - **Agent Communication Bus (智能体通信总线)**：
      - 提供智能体之间进行消息传递的机制（内部消息队列或事件总线）。
      - 支持智能体发送和接收消息。
      - 可以作为与外部智能体（如 DeepServer 上的 Agent）进行通信的代理。
    - **Perception Adapters (感知适配器)**：
      - 将 DeepWin 内部数据（来自数据管理层、服务层、业务逻辑模块）转换为智能体可感知的“世界状态”或“事件”。
      - 例如：新的记忆导入事件、设备状态变化、用户操作日志、云端通知等。
    - **Action Dispatchers (行动分发器)**：
      - 将智能体做出的决策或行动指令，转化为 DeepWin 内部可执行的操作。
      - 例如：调用设备逻辑管理器控制设备、调用数据管理层更新数据、触发云端通信服务发送请求。
    - **Core Agents (核心智能体)**：
      - **MemoryCuratorAgent（记忆策展智能体）**：主动分析新旧记忆，发现关联，建议标签，提醒回顾。
      - **ResourceMatcherAgent（资源匹配智能体）**：分析用户行为和需求，主动推荐潜在资源或发起匹配。
      - **DeviceSupervisorAgent（设备监控智能体）**：监控设备状态，预警故障，建议维护，智能调整设备行为。
      - **UserAssistantAgent（用户助理智能体）**：根据用户上下文提供主动帮助、信息查询、个性化推荐。
      - 每个智能体都将具备自己的感知、推理（可能调用 AI 协调器）、决策和行动逻辑。

### 3.3 服务层 (Service Layer)

- **职责**：提供与外部世界交互的统一接口，封装底层通信协议和数据传输细节。

#### 3.3.1 云端通信服务 (Cloud Communication Service)

- **职责**：负责 DeepWin 与 DeepServer 之间的所有网络通信。
- **技术栈**：Python (`httpx` for HTTP/REST, `paho-mqtt` for MQTT, `LiveKit client` for WebRTC/realtime voice/video)。
- **主要子模块**：
  - **API 客户端**：
    - 封装 DeepServer 提供的 RESTful API 调用，包括用户认证、数据CRUD操作（记忆、资源、需求、设备信息等）。
    - **集成 Immich API、Mem0 API 等**：直接调用这些第三方 API，获取其处理后的数据，并将其整合到 DeepDiary 的本地数据库或应用逻辑中。
    - 错误处理和重试机制。
  - **MQTT 客户端**：
    - 建立并维护与 DeepServer (EMQX) 的 MQTT 连接。
    - 订阅设备状态更新、远程控制指令等主题。
    - 发布 DeepWin 本地数据同步状态、日志等消息。
    - **Agent 间通信桥梁**：可作为 DeepWin 内部智能体与 DeepServer 外部智能体之间通信的底层传输。
  - **流媒体客户端**：
    - 接收来自 DeepDevice (通过 MediaMTX 转发) 的实时视频流。
    - 接收来自 LiveKit 的实时语音流，并发送本地语音数据。
    - 处理流媒体数据的解码和播放。
  - **数据同步管理器**：
    - 负责协调本地 SQLite 数据库与云端 PostgreSQL 数据库之间的数据同步。
    - 实现增量同步、冲突解决策略（例如时间戳优先、用户选择、合并等）。
    - 支持定时同步和手动同步。

#### 3.3.2 本地硬件通信服务 (Local Hardware Communication Service)

- **职责**：负责 DeepWin 与本地连接的 DeepDevice 设备的底层通信，处理协议解析和数据传输。
- **技术栈**：Python (`pyserial` for serial communication), 针对 CAN bus 可能需要特定的 Python CAN 库。
- **主要子模块**：
  - **串口通信模块**：
    - 建立、维护和管理与 DeepArm、DeepToy 等设备的串口连接。
    - 发送和接收原始串口数据。
    - 处理串口数据的编解码。
  - **CAN 总线通信模块**：
    - 如果 DeepArm 或 DeepToy 通过 CAN 总线与 DeepWin 通信，则需要此模块。
    - 解析 DBC 文件：根据 DBC (Database CAN) 文件解析 CAN 报文，将其转换为可理解的数据。
    - 封装 CAN 帧的发送和接收。
  - **设备协议解析器**：
    - 根据 DeepArm、DeepToy 等不同设备的私有通信协议，解析接收到的原始数据。
    - 将解析后的数据传递给应用逻辑层。
    - 将应用逻辑层生成的控制命令转换为设备可识别的协议格式。
  - **驱动管理**：管理本地硬件设备的驱动加载和卸载。

### 3.4 数据管理层 (Data Management Layer)

- **职责**：负责 DeepWin 本地数据的持久化存储、访问和管理。
- **技术栈**：Python (`sqlite3` for local database interaction), Django ORM (如果 DeepWin 的本地数据库也基于 Django Model 设计)。

#### 3.4.1 本地数据库 (Local Database)

- **数据库类型**：SQLite3 (轻量级嵌入式数据库)。
- **职责**：
  - 存储 DeepWin 本地缓存的记忆数据 (照片、视频、日记、聊天记录的元数据和部分内容)。
  - 存储本地的用户配置、应用设置。
  - 存储设备配置、示教轨迹等。
  - 作为云端数据同步的本地副本。
- **核心表**：
  - **`LocalUsers`**：存储本地登录用户的信息。
  - **`LocalMemories`**：存储本地记忆的元数据和索引，关联到本地文件路径。
    - `local_path` (TEXT): 本地文件路径。
    - `synced_to_cloud` (BOOLEAN): 标识是否已同步到云端。
  - **`LocalResources` / `LocalDemands`**：本地缓存的资源和需求信息。
  - **`LocalDevices`**：本地发现和连接的设备信息、配置。
  - **`LocalFaceRecognitions`**：本地人脸识别的临时结果或缓存。
  - **`LocalSettings`**：应用配置参数。
- **与应用逻辑层交互**：应用逻辑层通过此层提供的 ORM 或 DAO (Data Access Object) 接口进行数据存取。

#### 3.4.2 日志管理 (Log Management)

- **职责**：记录 DeepWin 应用程序的运行日志、错误信息、警告和调试信息。
- **技术栈**：Python `logging` 模块。
- **日志存储**：
  - 本地文件：将日志写入到本地文件，方便本地查看和排查问题。
  - 云端同步：重要日志（如错误、告警）可以定期或实时同步到 DeepServer 的日志服务。

### 3.5 辅助/资源层 (Auxiliary/Resource Layer)

- **职责**：存放非代码逻辑性的辅助文件和资源。
- **主要目录**：
  - **`Docs`**：项目相关文档，例如本架构文档、用户手册草稿等。
  - **`Media`**：应用所需的图片、图标、音频等媒体资源。
  - **`Models`**：本地 AI 模型文件，例如用于轻量级人脸检测或特征提取的模型。
  - **`Output`**：应用程序运行过程中生成的输出文件，如导出的报告、处理后的图像等。
  - **`README.md`**：项目介绍文件。

## 4. 关键技术栈与集成

- **桌面 GUI**：**PySide6-Fluent-Widgets**。提供现代化、流畅的界面体验。
- **本地数据库**：**SQLite3**。轻量级、嵌入式，适合本地数据存储。
- **云端通信**：**httpx** (异步 HTTP/REST 请求)、**paho-mqtt** (MQTT 客户端)、**LiveKit client SDK** (实时语音/视频)。
- **本地硬件通信**：**pyserial** (串口通信)，可能需要额外的 **python-can** 库进行 CAN 总线通信。
- **图像处理**：**OpenCV-Python** (基础图像操作、人脸检测等)，并集成 **Immich API** 获取其高级处理结果。
- **AI 协调**：通过 **DeepServer API Client** 调用云端 AI 服务（如大模型、高级识别服务）。
- **微信聊天记录**：利用 **WeChat-Dump** 等工具进行数据提取和解析。
- **智能体框架（未来扩展）**：Python 提供的异步编程能力 (`asyncio`) 和轻量级事件/消息队列机制，将是构建内部智能体通信的基础。

## 5. 数据流与交互

### 5.1 DeepWin 内部数据流

- **UI <-> 业务逻辑**：用户操作通过 UI 组件事件触发业务逻辑模块的对应方法；业务逻辑模块更新数据后通知 UI 层进行界面刷新。
- **业务逻辑 <-> 服务层**：业务逻辑模块调用服务层的方法发起网络请求或设备操作，服务层返回数据或操作结果。
- **业务逻辑 <-> 数据管理层**：业务逻辑模块通过数据管理层接口读写本地数据库，或写入日志。
- **业务逻辑 <-> 智能体层**：业务逻辑模块提供感知数据给智能体层，并根据智能体的决策执行相应行动。
- **智能体层内部**：智能体通过 Agent Communication Bus 进行消息传递和协作。
- **智能体层 <-> 服务层/数据管理层**：智能体通过 Action Dispatchers 驱动服务层和数据管理层执行操作，通过 Perception Adapters 获取感知信息。

### 5.2 DeepWin 与 DeepServer 的数据同步

- **同步机制**：采用周期性同步和事件触发同步相结合的方式。
  - **定时同步**：DeepWin 定期（如每小时或每天）将本地新增/修改的数据同步到 DeepServer。
  - **事件触发同步**：当用户执行关键操作（如手动备份、上传重要记忆）时，立即触发同步。
- **数据一致性**：
  - **版本控制**：为同步的数据添加版本号或时间戳，以便在发生冲突时进行判断和解决。
  - **冲突解决**：
    - **乐观并发控制**：在提交更新时检查数据版本，如果版本不一致则提示冲突。
    - **最后写入者胜 (Last-Writer-Wins)**：以时间戳最新的数据为准。
    - **用户介入**：当冲突无法自动解决时，提示用户手动选择或合并。
- **传输协议**：通过 RESTful API 进行数据同步（POST/PUT/GET）。大批量数据或文件传输可能通过特定协议（如分块上传）。

### 5.3 DeepWin 与 DeepDevice 的通信

- **协议**：主要通过串口通信，并支持 CAN 总线协议（如果 DeepArm/DeepToy 使用 CAN）。
- **数据流向**：
  - **控制指令**：DeepWin 应用逻辑层（包括智能体层）生成控制命令，通过本地硬件通信服务，经串口/CAN 发送给 DeepDevice。
  - **状态反馈**：DeepDevice 实时发送传感器数据、状态信息，通过本地硬件通信服务，被 DeepWin 应用逻辑层（包括智能体层）接收并更新到 UI 或本地数据库。
- **协议解析**：本地硬件通信服务负责解析不同设备的私有协议和 DBC 文件，将原始字节流转换为结构化数据，供应用逻辑层处理。

## 6. 非功能性考虑

### 6.1 性能

- **启动速度**：DeepWin 应快速启动，提供良好的用户体验。
- **响应速度**：界面操作、本地数据查询应在毫秒级响应；与云端同步和设备交互的延迟应控制在可接受范围内。
- **资源占用**：合理控制 CPU、内存和磁盘占用，避免对用户系统造成过大负担。
- **图像/视频处理效率**：对于大量图像和视频的本地处理，应采用多线程或异步处理，避免 UI 卡顿。
- **智能体运行效率**：确保智能体在后台运行时，不会显著影响DeepWin的主体性能和用户体验。

### 6.2 可靠性

- **错误处理**：完善的异常捕获和错误处理机制，提供友好的错误提示，避免程序崩溃。
- **数据持久化**：确保本地数据在应用程序关闭或意外退出后不丢失。
- **同步容错**：数据同步过程中，应对网络中断、服务器无响应等情况进行重试和错误记录。
- **设备连接稳定性**：确保与本地设备的连接稳定可靠，断线后能自动重连。
- **智能体鲁棒性**：智能体应能处理异常情况并从错误中恢复，避免陷入死循环或错误状态。

### 6.3 可维护性

- **模块化设计**：清晰的模块边界和接口定义，降低模块间耦合，便于独立开发和维护。
- **代码规范**：遵循统一的 Python 编码规范（如 PEP 8），提高代码可读性。
- **日志记录**：详细的日志记录，方便问题诊断和追踪。
- **配置管理**：支持配置文件管理，方便修改应用程序参数。
- **智能体管理**：提供工具或界面，方便管理和监控智能体的运行状态。

### 6.4 可扩展性

- **插件化机制**：考虑引入插件机制，方便未来扩展新的 DeepDevice 类型或第三方服务集成。
- **协议抽象**：抽象本地硬件通信协议层，便于增加新的通信协议支持。
- **AI 模型更新**：支持本地 AI 模型的在线更新机制。
- **智能体扩展**：架构应允许轻松添加新的智能体类型，并扩展现有智能体的能力，无需对核心架构进行重大更改。
- **通信协议升级**：智能体通信协议（ACP）的设计应具备灵活性，以便于未来升级或支持更复杂的协议。

### 6.5 安全性

- **本地数据加密**：对存储在本地 SQLite 中的敏感数据（如用户凭证、私密记忆）进行加密。
- **通信加密**：与 DeepServer 的通信应使用 HTTPS 和 TLS/SSL 进行加密。
- **设备认证**：确保 DeepWin 只与授权的 DeepDevice 设备进行通信。
- **智能体权限控制**：未来可考虑对智能体执行的操作进行权限控制，限制其对敏感数据和功能的访问。

## 7. 总结

DeepWin 作为 DeepDiary 平台的重要组成部分，其软件架构的设计至关重要。本文档详细阐述了 DeepWin 的分层架构、核心模块职责、关键技术栈、内外交互机制以及非功能性考量，并重点强调了为未来智能体功能集成所做的准备。通过遵循这些设计原则和方案，我们将能够构建一个功能强大、稳定可靠、易于扩展且用户体验优良的桌面应用程序，为 DeepDiary 项目的成功奠定坚实基础。

## 8. 软件开发项目目录结构

以下是 DeepWin 项目的建议目录结构，它反映了上述架构设计：

```
DeepWin 软件架构文档
1. 引言
1.1 编写目的
本文档旨在详细描述 DeepWin 桌面应用程序的软件架构，为开发团队提供清晰的系统结构、模块划分、技术选型和交互机制等方面的指导。通过本文档，开发人员可以快速理解 DeepWin 的设计理念和实现细节，从而高效地进行开发、测试和维护工作。特别地，本文档将着重阐述如何构建一个具备良好可扩展性的架构，以支持未来智能体（Agent）功能的平滑集成。

1.2 目标读者
本文档的目标读者包括：

系统架构师

软件开发工程师

测试工程师

运维工程师

1.3 术语和缩写
DeepWin：DeepDiary 项目的桌面 GUI 应用程序。

DeepServer：DeepDiary 项目的云端服务器，负责数据存储、API 服务、AI 处理等。

DeepDevice：DeepDiary 项目的硬件设备端，包括 DeepGlass、DeepArm、DeepToy。

GUI：图形用户界面（Graphical User Interface）。

API：应用程序编程接口（Application-Programming Interface）。

MQTT：消息队列遥测传输协议（Message Queuing Telemetry Transport）。

ORM：对象关系映射（Object Relational Mapping）。

IPC：进程间通信（Inter-Process Communication）。

FOC：磁场定向控制（Field Oriented Control）。

DBC：数据库文件（CAN bus database file），用于描述 CAN 总线上的消息。

Agent（智能体）：具备感知（Perceive）、推理（Reason）、行动（Act）和通信（Communicate）能力的自主软件实体。

MAS（Multi-Agent System）：多智能体系统。

ACP（Agent Communication Protocol）：智能体通信协议。

2. 总体架构
2.1 架构概述
DeepWin 应用程序采用分层架构与智能体就绪（Agent-Ready）设计，旨在实现清晰的职责分离、高内聚低耦合和良好的可维护性。它作为连接用户、本地设备和云端 DeepServer 的关键枢纽，核心定位是**“云端与串口设备的中间桥梁”，并逐步演变为一个能够托管和协调智能体**的平台。

DeepWin 的主要职责包括：

本地记忆管理：管理用户的数字化记忆（照片、视频、日记、聊天记录等）和社会人脉资源，并支持与云端同步。

本地设备交互：通过串口、USB 等方式与 DeepArm、DeepToy 等嵌入式设备进行通信，实现设备控制、数据接收和指令解析。

云端服务对接：与 DeepServer 进行数据同步、API 调用、MQTT 消息处理和流媒体接收。

用户界面呈现：提供直观友好的 GUI 界面，方便用户进行各项操作和数据查看。

本地 AI 处理：执行部分本地化的图像处理、相机管理和辅助 AI 功能。

智能体托管与协作：为智能体的运行提供环境，并协调智能体间的通信与任务执行，从而实现主动式的智能服务。

2.2 总体架构图
@startuml
skinparam handwritten true
skinparam style plain
skinparam defaultFontName "Cascadia Code"
skinparam defaultFontSize 14

package "DeepWin 桌面应用程序" {
  [用户界面层 (UI)] as UI
  package "应用逻辑层 (Application Logic)" {
    [业务逻辑模块] as BusinessLogic
    [智能体层 (Agent Layer)] as AgentLayer
  }
  package "服务层 (Service Layer)" {
    [云端通信服务] as CloudSvc
    [本地硬件通信服务] as HardwareSvc
  }
  [数据管理层 (Data Management)] as DataMgr
}

actor 用户
cloud "DeepServer 云平台" as Server
folder "本地嵌入式设备" as Device {
  [DeepArm]
  [DeepToy]
  [其他串口设备]
}

用户 --> UI : 交互
UI --> BusinessLogic : 用户操作/事件
BusinessLogic --> CloudSvc : 请求云端数据/操作
BusinessLogic --> HardwareSvc : 请求设备数据/控制
BusinessLogic --> DataMgr : 本地数据存储/检索
BusinessLogic --> AgentLayer : 触发智能体行为/提供环境信息

AgentLayer <--> BusinessLogic : 智能体决策/行动反馈
AgentLayer --> CloudSvc : 智能体请求云端服务
AgentLayer --> HardwareSvc : 智能体控制设备
AgentLayer --> DataMgr : 智能体读写本地数据

CloudSvc <--> Server : REST API, MQTT, Streaming
HardwareSvc <--> Device : 串口, CAN, USB

DataMgr <--> [本地 SQLite 数据库] : 数据存储

@enduml


2.3 架构描述
DeepWin 的分层架构和智能体就绪设计如下：

用户界面层 (UI Layer)：直接与用户交互，负责界面元素的展示、用户输入处理和事件传递。

应用逻辑层 (Application Logic Layer)：DeepWin 的核心，包含业务逻辑模块和智能体层。

业务逻辑模块：处理传统的、由用户操作驱动的业务流程。

智能体层：承载 DeepWin 内部的智能体实例，负责智能体的生命周期管理、内部通信和与业务逻辑模块的交互，实现主动式智能。

服务层 (Service Layer)：封装了与外部系统（云端 DeepServer）和本地硬件设备（DeepDevice）的通信细节，对外提供统一的服务接口。

云端通信服务：负责所有与 DeepServer 的网络通信。

本地硬件通信服务：负责所有与本地物理设备的通信。

数据管理层 (Data Management Layer)：管理 DeepWin 本地的数据存储（SQLite 数据库）和日志记录，提供数据持久化和访问接口。

3. 模块划分与职责
3.1 用户界面层 (UI Layer)
职责：负责 DeepWin 的视觉呈现、用户交互（如点击、输入、拖拽）的捕获与传递，以及应用逻辑层返回的数据展示。

技术栈：PySide6-Fluent-Widgets (基于 PySide6)。

主要组件：

主窗口框架：包括导航栏、内容区、状态栏等，提供应用整体布局。

记忆管理界面：照片墙、视频播放器、日记编辑器、聊天记录视图等，用于展示和管理用户的多模态记忆。

设备控制界面：显示连接的 DeepDevice 列表、设备状态、控制面板（如机械臂运动控制、玩具外设控制）。

资源/需求管理界面：展示用户及其好友的资源和需求列表，支持录入、编辑、搜索。

设置界面：用户账户管理、数据同步配置、主题设置等。

日志显示界面：实时显示 DeepWin 运行日志。

与应用逻辑层交互：通过信号/槽机制或事件回调将用户操作传递给应用逻辑层；接收应用逻辑层更新的数据进行界面刷新。

3.2 应用逻辑层 (Application Logic Layer)
职责：DeepWin 的大脑，包含核心业务逻辑。它处理来自 UI 层的用户请求，协调服务层与数据管理层完成任务，并执行本地的数据处理和 AI 辅助功能。此外，它还包含智能体层，实现 DeepWin 的主动智能。

技术栈：Python。

主要子模块：

核心管理器 (Core Manager)：

协调器：负责模块间的调度和数据流转。

任务调度器：管理后台任务（如大文件处理、数据同步）。

记忆处理模块 (Memory Processing)：

图像与视频处理：

本地目录扫描与文件解析：扫描用户指定目录，识别图像和视频文件。

元数据提取：从图像 (如 EXIF) 和视频中提取 GPS、时间、长宽、拍摄设备等元数据。

AI 信息提取：利用本地或云端 AI (如 Immich API) 提取图像中的人脸数据、物体信息、场景语义信息。

本地索引构建：为照片和视频创建本地索引，方便快速检索。

图像/视频预览与编辑：提供基本预览、剪辑和后期处理功能。

人脸/物体标注与识别：辅助用户对图像中的人脸和物体进行命名和管理。

集成 Immich API：通过 Immich 提供的 API 获取其处理结果 (如向量化特征、标签、分类)，避免重复开发。

日记与笔记处理：

文本解析与存储：管理本地日记和笔记的创建、编辑、保存。

关键词提取与索引：对文本内容进行关键词提取，构建本地搜索索引。

聊天记录处理：

微信聊天记录导入与解析 (利用 WeChat-Dump)：解密和解析本地微信数据库，提取聊天内容、图片、语音等。

内容分析与摘要：对聊天记录进行初步分析，提取关键信息。

GPS 轨迹处理：

轨迹数据导入与解析：处理来自 DeepGlass 或其他设备的 GPS 轨迹数据。

轨迹可视化：在本地地图组件上展示轨迹。

资源/需求管理器 (Resource/Demand Manager)：

管理本地存储的用户资源和需求信息。

提供资源/需求录入、编辑、搜索功能。

与云端 DeepServer 进行资源/需求数据的同步。

设备逻辑管理器 (Device Logic Manager)：

处理与 DeepDevice 设备的复杂业务逻辑。

解析来自硬件通信服务的原始设备数据。

根据用户指令生成设备控制命令。

处理设备状态的实时更新和告警逻辑。

AI 功能协调器 (AI Coordinator)：

协调本地 AI 库的调用 (如 OpenCV 用于基础图像处理)。

管理与 DeepServer AI 服务的交互，例如调用大模型进行复杂自然语言理解、知识问答。

智能体层 (Agent Layer)：

Agent Manager (智能体管理器)：

负责 DeepWin 内部智能体的生命周期管理（实例化、启动、停止、销毁）。

提供智能体注册和发现机制。

协调智能体间的任务分配和优先级。

Agent Communication Bus (智能体通信总线)：

提供智能体之间进行消息传递的机制（内部消息队列或事件总线）。

支持智能体发送和接收消息。

可以作为与外部智能体（如 DeepServer 上的 Agent）进行通信的代理。

Perception Adapters (感知适配器)：

将 DeepWin 内部数据（来自数据管理层、服务层、业务逻辑模块）转换为智能体可感知的“世界状态”或“事件”。

例如：新的记忆导入事件、设备状态变化、用户操作日志、云端通知等。

Action Dispatchers (行动分发器)：

将智能体做出的决策或行动指令，转化为 DeepWin 内部可执行的操作。

例如：调用设备逻辑管理器控制设备、调用数据管理层更新数据、触发云端通信服务发送请求。

Core Agents (核心智能体)：

MemoryCuratorAgent（记忆策展智能体）：主动分析新旧记忆，发现关联，建议标签，提醒回顾。

ResourceMatcherAgent（资源匹配智能体）：分析用户行为和需求，主动推荐潜在资源或发起匹配。

DeviceSupervisorAgent（设备监控智能体）：监控设备状态，预警故障，建议维护，智能调整设备行为。

UserAssistantAgent（用户助理智能体）：根据用户上下文提供主动帮助、信息查询、个性化推荐。

每个智能体都将具备自己的感知、推理（可能调用 AI 协调器）、决策和行动逻辑。

3.3 服务层 (Service Layer)
职责：提供与外部世界交互的统一接口，封装底层通信协议和数据传输细节。

3.3.1 云端通信服务 (Cloud Communication Service)
职责：负责 DeepWin 与 DeepServer 之间的所有网络通信。

技术栈：Python (httpx for HTTP/REST, paho-mqtt for MQTT, LiveKit client for WebRTC/realtime voice/video)。

主要子模块：

API 客户端：

封装 DeepServer 提供的 RESTful API 调用，包括用户认证、数据CRUD操作（记忆、资源、需求、设备信息等）。

集成 Immich API、Mem0 API 等：直接调用这些第三方 API，获取其处理后的数据，并将其整合到 DeepDiary 的本地数据库或应用逻辑中。

错误处理和重试机制。

MQTT 客户端：

建立并维护与 DeepServer (EMQX) 的 MQTT 连接。

订阅设备状态更新、远程控制指令等主题。

发布 DeepWin 本地数据同步状态、日志等消息。

Agent 间通信桥梁：可作为 DeepWin 内部智能体与 DeepServer 外部智能体之间通信的底层传输。

流媒体客户端：

接收来自 DeepDevice (通过 MediaMTX 转发) 的实时视频流。

接收来自 LiveKit 的实时语音流，并发送本地语音数据。

处理流媒体数据的解码和播放。

数据同步管理器：

负责协调本地 SQLite 数据库与云端 PostgreSQL 数据库之间的数据同步。

实现增量同步、冲突解决策略（例如时间戳优先、用户选择、合并等）。

支持定时同步和手动同步。

3.3.2 本地硬件通信服务 (Local Hardware Communication Service)
职责：负责 DeepWin 与本地连接的 DeepDevice 设备的底层通信，处理协议解析和数据传输。

技术栈：Python (pyserial for serial communication), 针对 CAN bus 可能需要特定的 Python CAN 库。

主要子模块：

串口通信模块：

建立、维护和管理与 DeepArm、DeepToy 等设备的串口连接。

发送和接收原始串口数据。

处理串口数据的编解码。

CAN 总线通信模块：

如果 DeepArm 或 DeepToy 通过 CAN 总线与 DeepWin 通信，则需要此模块。

解析 DBC 文件：根据 DBC (Database CAN) 文件解析 CAN 报文，将其转换为可理解的数据。

封装 CAN 帧的发送和接收。

设备协议解析器：

根据 DeepArm、DeepToy 等不同设备的私有通信协议，解析接收到的原始数据。

将解析后的数据传递给应用逻辑层。

将应用逻辑层生成的控制命令转换为设备可识别的协议格式。

驱动管理：管理本地硬件设备的驱动加载和卸载。

3.4 数据管理层 (Data Management Layer)
职责：负责 DeepWin 本地数据的持久化存储、访问和管理。

技术栈：Python (sqlite3 for local database interaction), Django ORM (如果 DeepWin 的本地数据库也基于 Django Model 设计)。

3.4.1 本地数据库 (Local Database)
数据库类型：SQLite3 (轻量级嵌入式数据库)。

职责：

存储 DeepWin 本地缓存的记忆数据 (照片、视频、日记、聊天记录的元数据和部分内容)。

存储本地的用户配置、应用设置。

存储设备配置、示教轨迹等。

作为云端数据同步的本地副本。

核心表：

LocalUsers：存储本地登录用户的信息。

LocalMemories：存储本地记忆的元数据和索引，关联到本地文件路径。

local_path (TEXT): 本地文件路径。

synced_to_cloud (BOOLEAN): 标识是否已同步到云端。

LocalResources / LocalDemands：本地缓存的资源和需求信息。

LocalDevices：本地发现和连接的设备信息、配置。

LocalFaceRecognitions：本地人脸识别的临时结果或缓存。

LocalSettings：应用配置参数。

与应用逻辑层交互：应用逻辑层通过此层提供的 ORM 或 DAO (Data Access Object) 接口进行数据存取。

3.4.2 日志管理 (Log Management)
职责：记录 DeepWin 应用程序的运行日志、错误信息、警告和调试信息。

技术栈：Python logging 模块。

日志存储：

本地文件：将日志写入到本地文件，方便本地查看和排查问题。

云端同步：重要日志（如错误、告警）可以定期或实时同步到 DeepServer 的日志服务。

3.5 辅助/资源层 (Auxiliary/Resource Layer)
职责：存放非代码逻辑性的辅助文件和资源。

主要目录：

Docs：项目相关文档，例如本架构文档、用户手册草稿等。

Media：应用所需的图片、图标、音频等媒体资源。

Models：本地 AI 模型文件，例如用于轻量级人脸检测或特征提取的模型。

Output：应用程序运行过程中生成的输出文件，如导出的报告、处理后的图像等。

README.md：项目介绍文件。

4. 关键技术栈与集成
桌面 GUI：PySide6-Fluent-Widgets。提供现代化、流畅的界面体验。

本地数据库：SQLite3。轻量级、嵌入式，适合本地数据存储。

云端通信：httpx (异步 HTTP/REST 请求)、paho-mqtt (MQTT 客户端)、LiveKit client SDK (实时语音/视频)。

本地硬件通信：pyserial (串口通信)，可能需要额外的 python-can 库进行 CAN 总线通信。

图像处理：OpenCV-Python (基础图像操作、人脸检测等)，并集成 Immich API 获取其高级处理结果。

AI 协调：通过 DeepServer API Client 调用云端 AI 服务（如大模型、高级识别服务）。

微信聊天记录：利用 WeChat-Dump 等工具进行数据提取和解析。

智能体框架（未来扩展）：Python 提供的异步编程能力 (asyncio) 和轻量级事件/消息队列机制，将是构建内部智能体通信的基础。

5. 数据流与交互
5.1 DeepWin 内部数据流
UI <-> 业务逻辑：用户操作通过 UI 组件事件触发业务逻辑模块的对应方法；业务逻辑模块更新数据后通知 UI 层进行界面刷新。

业务逻辑 <-> 服务层：业务逻辑模块调用服务层的方法发起网络请求或设备操作，服务层返回数据或操作结果。

业务逻辑 <-> 数据管理层：业务逻辑模块通过数据管理层接口读写本地数据库，或写入日志。

业务逻辑 <-> 智能体层：业务逻辑模块提供感知数据给智能体层，并根据智能体的决策执行相应行动。

智能体层内部：智能体通过 Agent Communication Bus 进行消息传递和协作。

智能体层 <-> 服务层/数据管理层：智能体通过 Action Dispatchers 驱动服务层和数据管理层执行操作，通过 Perception Adapters 获取感知信息。

5.2 DeepWin 与 DeepServer 的数据同步
同步机制：采用周期性同步和事件触发同步相结合的方式。

定时同步：DeepWin 定期（如每小时或每天）将本地新增/修改的数据同步到 DeepServer。

事件触发同步：当用户执行关键操作（如手动备份、上传重要记忆）时，立即触发同步。

数据一致性：

版本控制：为同步的数据添加版本号或时间戳，以便在发生冲突时进行判断和解决。

冲突解决：

乐观并发控制：在提交更新时检查数据版本，如果版本不一致则提示冲突。

最后写入者胜 (Last-Writer-Wins)：以时间戳最新的数据为准。

用户介入：当冲突无法自动解决时，提示用户手动选择或合并。

传输协议：通过 RESTful API 进行数据同步（POST/PUT/GET）。大批量数据或文件传输可能通过特定协议（如分块上传）。

5.3 DeepWin 与 DeepDevice 的通信
协议：主要通过串口通信，并支持 CAN 总线协议（如果 DeepArm/DeepToy 使用 CAN）。

数据流向：

控制指令：DeepWin 应用逻辑层（包括智能体层）生成控制命令，通过本地硬件通信服务，经串口/CAN 发送给 DeepDevice。

状态反馈：DeepDevice 实时发送传感器数据、状态信息，通过本地硬件通信服务，被 DeepWin 应用逻辑层（包括智能体层）接收并更新到 UI 或本地数据库。

协议解析：本地硬件通信服务负责解析不同设备的私有协议和 DBC 文件，将原始字节流转换为结构化数据，供应用逻辑层处理。

6. 非功能性考虑
6.1 性能
启动速度：DeepWin 应快速启动，提供良好的用户体验。

响应速度：界面操作、本地数据查询应在毫秒级响应；与云端同步和设备交互的延迟应控制在可接受范围内。

资源占用：合理控制 CPU、内存和磁盘占用，避免对用户系统造成过大负担。

图像/视频处理效率：对于大量图像和视频的本地处理，应采用多线程或异步处理，避免 UI 卡顿。

智能体运行效率：确保智能体在后台运行时，不会显著影响DeepWin的主体性能和用户体验。

6.2 可靠性
错误处理：完善的异常捕获和错误处理机制，提供友好的错误提示，避免程序崩溃。

数据持久化：确保本地数据在应用程序关闭或意外退出后不丢失。

同步容错：数据同步过程中，应对网络中断、服务器无响应等情况进行重试和错误记录。

设备连接稳定性：确保与本地设备的连接稳定可靠，断线后能自动重连。

智能体鲁棒性：智能体应能处理异常情况并从错误中恢复，避免陷入死循环或错误状态。

6.3 可维护性
模块化设计：清晰的模块边界和接口定义，降低模块间耦合，便于独立开发和维护。

代码规范：遵循统一的 Python 编码规范（如 PEP 8），提高代码可读性。

日志记录：详细的日志记录，方便问题诊断和追踪。

配置管理：支持配置文件管理，方便修改应用程序参数。

智能体管理：提供工具或界面，方便管理和监控智能体的运行状态。

6.4 可扩展性
插件化机制：考虑引入插件机制，方便未来扩展新的 DeepDevice 类型或第三方服务集成。

协议抽象：抽象本地硬件通信协议层，便于增加新的通信协议支持。

AI 模型更新：支持本地 AI 模型的在线更新机制。

智能体扩展：架构应允许轻松添加新的智能体类型，并扩展现有智能体的能力，无需对核心架构进行重大更改。

通信协议升级：智能体通信协议（ACP）的设计应具备灵活性，以便于未来升级或支持更复杂的协议。

6.5 安全性
本地数据加密：对存储在本地 SQLite 中的敏感数据（如用户凭证、私密记忆）进行加密。

通信加密：与 DeepServer 的通信应使用 HTTPS 和 TLS/SSL 进行加密。

设备认证：确保 DeepWin 只与授权的 DeepDevice 设备进行通信。

智能体权限控制：未来可考虑对智能体执行的操作进行权限控制，限制其对敏感数据和功能的访问。

7. 总结
DeepWin 作为 DeepDiary 平台的重要组成部分，其软件架构的设计至关重要。本文档详细阐述了 DeepWin 的分层架构、核心模块职责、关键技术栈、内外交互机制以及非功能性考量，并重点强调了为未来智能体功能集成所做的准备。通过遵循这些设计原则和方案，我们将能够构建一个功能强大、稳定可靠、易于扩展且用户体验优良的桌面应用程序，为 DeepDiary 项目的成功奠定坚实基础。

8. 软件开发项目目录结构
以下是 DeepWin 项目的建议目录结构，它反映了上述架构设计：

DeepWin/
├── src/                                  # 源代码根目录
│   ├── __init__.py                       # Python 包标识
│   ├── main.py                           # DeepWin 应用程序入口
│   │
│   ├── ui/                               # 用户界面层
│   │   ├── __init__.py
│   │   ├── main_window.py                # 主窗口框架，包含导航、布局等
│   │   ├── memory_manager_view.py        # 记忆管理界面（照片墙、日记等）
│   │   ├── device_control_view.py        # 设备控制界面
│   │   ├── resource_demand_view.py       # 资源/需求管理界面
│   │   ├── settings_view.py              # 设置界面
│   │   ├── log_viewer_view.py            # 日志显示界面
│   │   └── components/                   # 可复用 UI 组件
│   │       ├── __init__.py
│   │       └── custom_widgets.py
│   │
│   ├── app_logic/                        # 应用逻辑层
│   │   ├── __init__.py
│   │   ├── core_manager/                 # 核心协调器与任务调度
│   │   │   ├── __init__.py
│   │   │   ├── coordinator.py
│   │   │   └── task_scheduler.py
│   │   │
│   │   ├── memory_processing/            # 记忆处理子模块
│   │   │   ├── __init__.py
│   │   │   ├── image_video_processing/   # 图像与视频处理逻辑
│   │   │   │   ├── __init__.py
│   │   │   │   └── processor.py
│   │   │   ├── diary_note_processing/    # 日记与笔记处理逻辑
│   │   │   │   ├── __init__.py
│   │   │   │   └── processor.py
│   │   │   ├── chat_record_processing/   # 聊天记录处理逻辑
│   │   │   │   ├── __init__.py
│   │   │   │   └── processor.py
│   │   │   └── gps_track_processing/     # GPS轨迹处理逻辑
│   │   │       ├── __init__.py
│   │   │       └── processor.py
│   │   │
│   │   ├── resource_demand_manager/      # 资源/需求业务逻辑处理
│   │   │   ├── __init__.py
│   │   │   └── manager.py
│   │   │
│   │   ├── device_logic_manager/         # 设备高级逻辑处理
│   │   │   ├── __init__.py
│   │   │   └── manager.py
│   │   │
│   │   ├── ai_coordinator/               # 本地及云端AI服务协调
│   │   │   ├── __init__.py
│   │   │   └── coordinator.py
│   │   │
│   │   └── agents/                       # **智能体层 (Agent Layer)**
│   │       ├── __init__.py
│   │       ├── agent_manager.py          # 智能体管理器
│   │       ├── agent_comm_bus.py         # 智能体通信总线
│   │       ├── perception_adapters.py    # 感知适配器
│   │       ├── action_dispatchers.py     # 行动分发器
│   │       ├── core_agents/              # 核心智能体实现
│   │       │   ├── __init__.py
│   │       │   ├── memory_curator_agent.py   # 记忆策展智能体
│   │       │   ├── resource_matcher_agent.py # 资源匹配智能体
│   │       │   ├── device_supervisor_agent.py# 设备监控智能体
│   │       │   └── user_assistant_agent.py   # 用户助理智能体
│   │       └── base_agent.py             # 智能体基类或接口定义
│   │
│   ├── services/                         # 服务层
│   │   ├── __init__.py
│   │   ├── cloud_communication/          # 云端通信服务
│   │   │   ├── __init__.py
│   │   │   ├── api_client.py             # RESTful API 客户端 (DeepServer & Immich/Mem0等)
│   │   │   ├── mqtt_client.py            # MQTT 客户端
│   │   │   ├── streaming_client.py       # 流媒体客户端 (LiveKit等)
│   │   │   └── data_sync_manager.py      # 数据同步管理
│   │   │
│   │   └── hardware_communication/       # 本地硬件通信服务
│   │       ├── __init__.py
│   │       ├── serial_communicator.py    # 串口通信模块 (pyserial)
│   │       ├── can_bus_communicator.py   # CAN 总线通信模块 (python-can)
│   │       ├── device_protocol_parser.py # 设备协议解析器
│   │       └── driver_manager.py         # 驱动管理
│   │
│   └── data_management/                  # 数据管理层
│       ├── __init__.py
│       ├── local_database.py             # 本地 SQLite 数据库操作 (ORM/DAO)
│       └── log_manager.py                # 日志管理
│
├── docs/                                 # 项目文档
│   ├── DeepWin_Software_Architecture.md  # 本文档
│   └── User_Manual_Draft.md
│
├── media/                                # 媒体资源
│   ├── icons/
│   └── images/
│
├── models/                               # 本地AI模型文件 (例如用于轻量级人脸检测)
│   └── .gitkeep
│
├── output/                               # 应用程序运行输出，如导出的报告、处理后的图像
│   └── .gitkeep
│
├── config/                               # 配置文件
│   └── settings.ini
│
├── tests/                                # 单元测试、集成测试
│   └── .gitkeep
│
├── requirements.txt                      # Python 依赖列表
├── README.md                             # 项目总览 README
└── .env.example                          # 环境变量示例文件

```
