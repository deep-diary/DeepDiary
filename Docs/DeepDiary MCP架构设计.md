# DeepDiary 项目 MCP 客户端模块架构设计与集成方案 (基于 Model Context Protocol)

## 1. 引言

在 DeepDiary 项目中，我们引入 **MCP (Model Context Protocol)** 的概念。MCP 是一种标准化协议，旨在以安全、统一的方式向大型语言模型（LLM）应用程序公开数据和功能。它被形象地比喻为 **“AI 的 USB-C 接口”**，提供了一种通用的方式来连接 LLM 与它们可以利用的资源。

**`fastmcp`** 是一个 Python 库，提供了构建、管理和与 MCP 服务器交互的高级接口。通过 `fastmcp`，DeepDiary 能够：

1. **作为 MCP 服务提供方 (在 DeepServer 端):** 将自身的核心数据（记忆、资源、用户资料等）暴露为 **“资源 (Resources)”**，将内部操作（如机械臂控制、记忆管理、资源匹配）暴露为 **“工具 (Tools)”**，从而使外部 LLM 应用程序（如 Dify 中的 AI Agent）能够安全、高效地调用这些能力。
2. **作为 MCP 客户端 (在 DeepWin 端):** 连接到 DeepServer 上部署的 MCP 服务，以及 **其他外部的、符合 MCP 规范的第三方服务**，从而利用这些服务的强大功能。

**MCP 客户端模块** 的目标是作为 DeepWin 桌面应用程序（以及未来可能扩展到其他客户端）与这些基于 MCP 的服务进行通信的桥梁。它将封装底层的通信细节和协议转换，向上层业务逻辑提供清晰、统一的接口，从而实现智能化的记忆管理、资源匹配和设备控制功能。

## 2. MCP 客户端模块架构设计

### 2.1 模块定位

MCP 客户端模块将作为 **DeepWin 桌面 GUI 软件 (`DeepWin`)** 中的一个重要组成部分。它不直接处理原始硬件通信（这由 `SerialCommunicator` 和 `DeviceProtocolParser` 完成），也不直接实现核心业务逻辑（这由 `DeviceLogicManager` 等模块负责）。相反，它充当 DeepWin 内部业务逻辑与 **DeepServer 上部署的 MCP 服务** 以及 **其他可能存在的外部 MCP 服务** 之间的**适配层**。

在 `Coordinator` 的数据流中，`Coordinator` 会负责实例化和管理 MCP 客户端模块，并将其与 `DeviceLogicManager` 等业务模块连接起来。

### 2.2 模块组成

MCP 客户端模块（主要指 DeepWin 侧的 MCP 客户端逻辑）可以设计为以下几个核心组件：

- **`MCPClientManager` (MCP 客户端管理器):**
  - **职责:** 作为 DeepWin 中 MCP 客户端功能的入口点，统一管理和调度与**所有** MCP 服务的连接（包括 DeepServer 的 MCP 服务和外部第三方 MCP 服务）以及请求分发。它将作为 `fastmcp` 客户端实例的协调者。
  - **功能:**
    - **服务注册与管理:** 维护一个注册表，记录 DeepWin 需要连接的所有 MCP 服务（包括其 URL、认证信息等）。这些服务可以在启动时加载，或通过用户配置动态添加。
    - **连接生命周期管理:** 负责建立、维护和关闭与各个 MCP 服务的连接。
    - **请求路由:** 根据上层业务模块（如 `DeviceLogicManager`、`MemoryManager`）发出的请求，将请求路由到正确的 `FastMCPClientWrapper` 实例，由其向目标 MCP 服务发起 Resource 查询或 Tool 调用。
  - **集成点:** `Coordinator` 将持有 `MCPClientManager` 的实例。
- **`FastMCPClientWrapper` (FastMCP 客户端封装):**
  - **职责:** 封装 `fastmcp` 库提供的客户端功能，向上层提供更符合 DeepDiary 业务语义的接口，并处理与单个特定 MCP 服务的交互。
  - **功能:**
    - **FastMCP 客户端实例:** 每个 `FastMCPClientWrapper` 实例内部包含一个或多个 `fastmcp.client.Client` 实例，负责与一个具体的 MCP 服务 URL 进行通信。
    - **请求转换:** 将 DeepWin 业务请求映射到 `fastmcp` 定义的 Resource 查询和 Tool 调用格式。
    - **响应解析:** 接收 `fastmcp` 客户端的响应，并进行初步的错误处理和数据结构转换。
    - **认证处理:** 管理与特定 MCP 服务的认证凭证（如 API Key、Token）。
  - **通信机制:** 内部使用 `fastmcp` 定义的通信机制（通常基于 HTTP/HTTPS）。
  - **集成点:** 由 `MCPClientManager` 实例化和管理多个 `FastMCPClientWrapper` 实例。
- **`MCPDataAdapters` (MCP 数据适配器):**
  - **职责:** 将 `FastMCPClientWrapper` 从 MCP 服务接收到的原始数据（无论是 Resource 返回的数据还是 Tool 执行结果）转换为 DeepDiary 内部统一的数据模型，确保数据一致性和易用性。
  - **功能:** 数据类型转换、字段映射、单位转换、数据验证等。这部分逻辑可以内置在 `FastMCPClientWrapper` 中（针对特定 MCP 的适配），也可以作为独立的辅助类（针对通用数据模型的转换）。

### 2.3 通信机制

MCP 客户端 (`FastMCPClientWrapper`) 与 DeepServer 上部署的 MCP 服务以及其他外部 MCP 服务之间的通信将遵循 **Model Context Protocol** 定义。`fastmcp` 库底层通常会基于 **HTTP/HTTPS** 实现这些交互。

## 2.4 与现有架构的集成

1. **`Coordinator`:**
   - 将在初始化时实例化 `MCPClientManager`。
   - **请求转发:** 负责将 `DeviceLogicManager`、`MemoryManager` 等业务模块发出的与高级智能服务相关的抽象请求，统一转发给 `MCPClientManager`。`Coordinator` 不再区分请求是针对 DeepServer 还是外部 MCP，这由 `MCPClientManager` 内部逻辑决定。
   - **响应处理:** 监听 `MCPClientManager` (通过 `FastMCPClientWrapper` 间接发出) 返回的数据响应和错误信号，并转发给相应的下游处理模块（如 `DeviceLogicManager` 或 `GuiManager` 更新状态栏）。
2. **`DeviceLogicManager` (及其他业务逻辑模块，如 `MemoryManager`, `ResourceDemandManager`):**
   - 继续处理应用层的业务逻辑。
   - 当需要与外部 LLM 友好的服务交互，或需要利用 LLM 驱动的工具和资源时，它将通过 `Coordinator` 调用 `MCPClientManager` 暴露的抽象接口（例如 `mcp_client_manager.perform_action("deeparm_mcp", "move_arm_to_coordinates", x, y, z)` 或 `mcp_client_manager.query_resource("news_mcp", "latest_headlines", topic="AI")`）。
   - 接收来自 `Coordinator` 转发的 MCP 响应数据（已通过 `MCPDataAdapters` 转换为 DeepDiary 内部格式），并更新设备状态、记忆数据或执行其他业务操作。
3. **外部 MCP 服务的集成 (重点):**
   - DeepWin 的 `MCPClientManager` 可以在启动时加载配置（例如，来自 `config_manager` 或用户设置），其中包含需要连接的外部 MCP 服务的 URL 和认证信息。
   - 例如，用户可以在设置中配置一个新闻 MCP 服务的 URL，`MCPClientManager` 会实例化一个对应的 `FastMCPClientWrapper`。
   - 当 DeepWin 业务逻辑需要获取“最新 AI 新闻”时，它会向 `MCPClientManager` 发出请求。`MCPClientManager` 识别到这是一个针对“新闻”的请求，并将其路由给已注册的新闻 MCP 服务的 `FastMCPClientWrapper`，由其调用该 MCP 服务暴露的 `get_latest_news(topic="AI")` Resource。
   - 这种设计使得 DeepWin 能够灵活地集成和利用市面上符合 MCP 规范的各类服务，**站在巨人的肩膀上** 快速扩展功能，而无需为每个外部服务单独开发复杂的 API 封装。

## 3. DeepDiary 项目中 MCP (Model Context Protocol) 的应用与功能实现

在 DeepDiary 项目中，`fastmcp` 将主要在 **DeepServer 端** 部署，负责将 DeepDiary 的核心功能和数据以 Resources 和 Tools 的形式暴露给 LLM 应用程序（如 Dify 中的 Agent）。DeepWin 客户端则通过其 MCP 客户端模块与 DeepServer 上的 MCP 服务以及其他第三方 MCP 服务进行交互。

以下是与项目高度契合的 MCP 类型（即 DeepServer 能够通过 `fastmcp` 暴露的服务），以及它们能够实现的功能：

### 3.1 DeepArm 机械臂控制 MCP (`DeepArmControlMCP`)

DeepArm 机械臂本身通过串口桥接 CAN 与 DeepWin 通信，其底层控制由 `DeviceProtocolParser` 和 `DeviceLogicManager` 处理。为了让 LLM 能够理解和控制机械臂，我们可以在 DeepServer 上部署一个 **`fastmcp` 服务**，将机械臂的控制能力暴露为 MCP 的 **Tools**。DeepWin 将作为客户端连接此 MCP 服务。

- **MCP 类型:** **DeepServer 暴露的 `fastmcp` 服务 (Tool 集合)**。
- **具体 MCP Tool 示例及功能:**
  - **`move_arm_to_coordinates(x, y, z)` 工具:** 允许 LLM 发布命令，将机械臂末端移动到指定的三维坐标。
    - **功能实现:** LLM 发送此 Tool 调用后，DeepServer 上的 `DeepArmControlMCP` 服务会接收请求，并通过内部逻辑（可能调用 `DeviceLogicManager` 的接口）将此高层级命令转化为机械臂能够执行的底层控制序列，然后通过 DeepWin 转发给机械臂。
  - **`grab_object(object_type, location_hint)` 工具:** 允许 LLM 命令机械臂抓取特定类型的物体。
    - **功能实现:** LLM 提供物体类型和位置提示，MCP 服务将协调视觉识别模块确认物体位置，并生成抓取轨迹。
  - **`get_arm_status()` 工具:** （也可作为 Resource，这里作为工具为例）允许 LLM 查询机械臂的当前状态（位置、模式、错误）。
    - **功能实现:** MCP 服务查询 `DeviceLogicManager` 获取机械臂实时状态，并返回给 LLM。
  - **`teach_arm_trajectory(trajectory_id)` 工具:** 允许 LLM 触发机械臂进入示教模式或执行预设轨迹。
    - **功能实现:** MCP 服务协调机械臂进入示教录制/回放状态。

### 3.2 记忆与资源追溯 MCP (`MemoryResourceMCP`)

DeepServer 存储着 DeepDiary 的核心记忆和资源数据。通过 `fastmcp`，可以将这些数据和相关的操作暴露为 MCP 的 **Resources** 和 **Tools**，供 LLM 进行智能查询和管理。DeepWin 将作为客户端连接此 MCP 服务。

- **MCP 类型:** **DeepServer 暴露的 `fastmcp` 服务 (Resource & Tool 集合)**。
- **具体 MCP Resource/Tool 示例及功能:**
  - **`query_memories(query_text, filters)` Resource:** 允许 LLM 查询用户的记忆。
    - **功能实现:** LLM 可以发起自然语言查询（如“去年夏天我和谁一起去了海边？”），MCP 服务利用 DeepServer 的记忆检索能力（向量搜索、知识图谱），返回相关的记忆片段或摘要。
  - **`get_user_resources(user_id, resource_type)` Resource:** 允许 LLM 查询指定用户的资源。
    - **功能实现:** LLM 可以查询“张三有哪些技能？”，MCP 服务返回张三的资源列表。
  - **`match_resources(demand_text, user_id)` Tool:** 允许 LLM 触发资源匹配。
    - **功能实现:** LLM 提供需求描述，MCP 服务调用 DeepServer 的资源匹配引擎，返回匹配结果。
  - **`add_memory(type, content, metadata)` Tool:** 允许 LLM 向记忆库中添加新的记忆。
    - **功能实现:** LLM 可以根据对话内容，生成新的日记条目或事件记录，MCP 服务将其写入 DeepServer。
  - **`get_memory_location(memory_id)` Resource:** 允许 LLM 查询特定记忆发生的位置。
    - **功能实现:** 返回记忆对应的 GPS 坐标或地点名称。

### 3.3 AI Agent 协调 MCP (`AIAgentCoordinationMCP`)

Dify 作为 DeepDiary 的大模型 Agent 工作流平台，将成为 MCP 服务的主要消费方。DeepServer 通过 `fastmcp` 暴露的 Resources 和 Tools，将直接被 Dify 中的 Agent 调用，从而赋予 Agent 访问 DeepDiary 内部能力的能力。DeepWin 将不直接连接此 MCP，而是作为 Dify Agent 调用其暴露的工具和资源的下游执行者。

- **MCP 类型:** **DeepServer 暴露的 `fastmcp` 服务 (被 Dify Agent 消费)**。
- **`DifyAIAgent` (在 Dify 中配置的 Agent):**
  - **自然语言理解与工具选择:** Dify Agent 接收用户自然语言指令后，通过大模型理解意图，并根据自身能力选择调用 DeepServer 暴露的 MCP Tool 或 Resource。
  - **MCP Tool 调用:** 例如，当用户说“帮我把机械臂移到桌子旁边”，Dify Agent 识别到“移动机械臂”的意图，便会调用 DeepServer 上 `DeepArmControlMCP` 服务中的 `move_arm_to_coordinates` 工具，并传递相应的参数。
  - **MCP Resource 查询:** 例如，当用户问“我上周在哪里拍过那张有猫的照片？”，Dify Agent 会调用 DeepServer 上 `MemoryResourceMCP` 服务中的 `query_memories` 资源，获取相关记忆。
  - **任务自动化:** Dify Agent 可以编排多个 MCP Resource/Tool 调用，实现复杂的自动化任务，如“查找特定时间段内发生的所有旅行记忆，然后让机械臂根据旅行照片摆出相应的姿态。”

### 3.4 外部 MCP 服务集成示例 (DeepWin 客户端功能扩展)

除了 DeepServer 自身暴露的 MCP 服务外，DeepWin 作为 MCP 客户端，还可以通过 `fastmcp` 连接并利用外部公共或私有的 MCP 服务，从而快速集成多样化的功能，**站在巨人的肩膀上** 进行开发。

- **MCP 类型:** **外部 `fastmcp` 服务** (例如 `mcp.so` 上的服务)。
- **具体 MCP Resource/Tool 示例及功能 (通过 DeepWin 客户端连接):**
  - **`NewsFeedMCP` (新闻订阅 MCP):**
    - **`get_latest_news(topic, limit)` Resource:** 允许 DeepWin 查询指定主题的最新新闻。
      - **功能实现:** DeepWin 用户可以通过语音或文本命令查询“今天的 AI 新闻”，`MCPClientManager` 会路由此请求给已配置的 `NewsFeedMCP` 服务的 `FastMCPClientWrapper`，该 MCP 服务将从外部新闻源获取数据并以 MCP Resource 格式返回给 DeepWin。
    - **`search_articles(keywords, date_range)` Resource:** 允许 DeepWin 搜索新闻文章。
      - **功能实现:** 用户可以搜索特定关键词的新闻，例如“关于量子计算的最新文章”。
  - **`CalendarEventMCP` (日历事件 MCP):**
    - **`get_upcoming_events(user_id, days_ahead)` Resource:** 允许 DeepWin 查询用户未来几天的日程事件。
      - **功能实现:** DeepWin 可以展示用户日历中的即将到来的事件，甚至在 DeepGlass 中通过语音提醒用户。
    - **`create_event(title, start_time, end_time, attendees)` Tool:** 允许 DeepWin 创建新的日历事件。
      - **功能实现:** 用户通过 DeepWin 语音或文本指令创建会议，`MCPClientManager` 将此转换为 MCP Tool 调用。
  - **`SmartHomeControlMCP` (智能家居控制 MCP):**
    - **`set_light_state(room, state)` Tool:** 允许 DeepWin 控制智能家居灯光。
      - **功能实现:** 用户通过 DeepWin 语音控制“打开客厅灯”，DeepWin 的 `MCPClientManager` 调用已配置的智能家居 MCP 服务。
    - **`get_temperature(room)` Resource:** 允许 DeepWin 查询房间温度。
      - **功能实现:** DeepWin 可以显示智能家居设备的实时温度数据。

## 5. 总结

通过在 DeepServer 上部署 `fastmcp` 服务，将 DeepDiary 的核心功能和数据抽象为标准化、LLM 友好的 **Resources** 和 **Tools**。更重要的是，DeepWin 桌面客户端通过其 `MCPClientManager` 和 `FastMCPClientWrapper`，**能够灵活地连接并利用这些在 DeepServer 上的 MCP 服务，同时也能集成和消费来自其他外部（如 `mcp.so`）的 MCP 服务。**

这种双重客户端/服务提供者角色使 DeepDiary 能够：

- **赋能 LLM:** 让外部 AI Agent（如 Dify 中的 Agent）能够直接理解和利用 DeepDiary 的内部能力，实现更智能的交互。
- **统一接口:** 为 DeepDiary 提供了与多种 LLM 应用和外部服务集成的通用“接口”，避免了为每个服务单独适配 API。
- **职责分离:** 将 LLM 的推理和决策与 DeepDiary 的业务逻辑和数据管理清晰分离。
- **无限扩展:** DeepWin 可以通过简单配置连接新的 MCP 服务，快速集成外部世界的各种功能，极大地提升了系统的可扩展性和功能丰富度。

此架构将使 DeepDiary 在 AI 驱动的未来中更具竞争力，为用户提供前所未有的智能体验。
