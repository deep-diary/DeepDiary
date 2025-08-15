# DeepWin MCP 客户端架构设计

## 1. 引言

在 DeepDiary 项目中，DeepWin 桌面应用程序扮演着关键的角色，它不仅是用户管理记忆和资源的核心界面，也是与硬件设备交互的桥梁。随着大型语言模型（LLM）的日益普及，我们引入 **Model Context Protocol (MCP)** 及其 `fastmcp` 库，旨在以标准化、LLM 友好的方式扩展 DeepWin 的功能，使其能够无缝连接到多种智能服务。

本设计文档旨在详细阐述 DeepWin 中 MCP 客户端模块的架构，指导开发人员和 AI 编辑器如何利用 `fastmcp` 集成外部 MCP 服务，以及如何实现与这些服务的安全、高效通信，从而赋能 DeepWin 具备更强大的智能交互和功能扩展能力。

## 2. MCP 客户端模块架构总览

DeepWin 的 MCP 客户端模块定位于 DeepWin 内部业务逻辑与外部 MCP 服务之间的**适配层**。它不直接处理硬件通信（由 `SerialCommunicator` 等负责），也不直接实现核心业务逻辑（由 `DeviceLogicManager` 等负责）。其核心职责是封装 `fastmcp` 客户端的调用细节，并向上层提供统一、简洁的接口。

**总体架构定位：**

- DeepWin 既可以作为 **MCP 的客户端** (连接 DeepServer 上部署的 MCP 服务，以及外部第三方 MCP 服务)，消费它们暴露的 Resources 和 Tools。
- DeepWin 也可以作为 **LLM 的用户界面**，将用户的自然语言请求发送给 DeepServer 上的 LLM Agent (例如 Dify)，由 LLM Agent 协调 MCP 调用，并将结果反馈给 DeepWin。

_图 1: DeepWin MCP 客户端架构概览_

## 3. DeepWin 可集成的外部 MCP 服务

DeepWin 的 MCP 客户端模块设计具有高度的灵活性和可扩展性，使其不仅能够连接 DeepServer 自身暴露的 MCP 服务，还能够集成各种符合 MCP 规范的外部第三方服务。这使得 DeepWin 能够“站在巨人的肩膀上”，快速引入丰富的外部功能。

以下是 DeepWin 可以集成的一些典型外部 MCP 服务类型及其功能示例：

### 3.1 信息查询类 MCP (Resources)

这类 MCP 服务主要提供各类公开或授权的信息查询能力，DeepWin 可以通过调用其 Resources 来获取数据并展示给用户。

- **新闻聚合 MCP (e.g., `NewsFeedMCP`)**
  - **功能：** 获取实时新闻、特定主题新闻、历史新闻文章。
  - **DeepWin 功能实现：**
    - **个性化新闻推送：** 用户在 DeepWin 中配置感兴趣的新闻主题，DeepWin 定期调用 `get_latest_news(topic)` Resource，获取新闻摘要并在 UI 中展示。
    - **新闻搜索：** 用户输入关键词搜索新闻文章，DeepWin 调用 `search_articles(keywords)` Resource，在搜索结果界面显示相关新闻。
    - **记忆上下文：** 在回顾某个记忆（如照片）时，DeepWin 自动查询当时（日期、地点）的热点新闻，丰富记忆背景。
  - **潜在 MCP URL 示例：** `https://api.some-news-mcp.com/v1`
- **天气信息 MCP (e.g., `WeatherMCP`)**
  - **功能：** 获取实时天气、天气预报、历史天气数据。
  - **DeepWin 功能实现：**
    - **实时天气显示：** DeepWin 根据用户当前位置或常用位置，调用 `get_current_weather(latitude, longitude)` Resource，在状态栏或特定天气组件中显示天气信息。
    - **记忆上下文：** 在查看某个记忆时（如旅行照片），DeepWin 调用 `get_historical_weather(location, date)` Resource，显示当时的天气情况。
  - **潜在 MCP URL 示例：** `https://api.some-weather-mcp.com/v1`
- **通用知识查询 MCP (e.g., `WikipediaMCP`)**
  - **功能：** 查询百科词条、获取摘要、相关概念。
  - **DeepWin 功能实现：**
    - **智能搜索辅助：** 用户在 DeepWin 中搜索某个不熟悉的术语或概念，DeepWin 调用 `get_summary(title)` Resource，快速显示维基百科摘要。
    - **记忆扩展：** 当记忆中提到某个历史事件或人物时，DeepWin 可以自动查询并显示相关背景知识。
  - **潜在 MCP URL 示例：** `https://api.some-wiki-mcp.com/v1`

### 3.2 功能调用类 MCP (Tools)

这类 MCP 服务主要提供执行特定操作的能力，DeepWin 可以通过调用其 Tools 来触发外部系统的行为或复杂计算。

- **日历管理 MCP (e.g., `CalendarMCP`)**
  - **功能：** 创建事件、查询日程、删除事件。
  - **DeepWin 功能实现：**
    - **日程同步：** DeepWin 调用 `get_upcoming_events()` Resource，在日历组件中展示用户日程。
    - **语音创建日程：** 用户通过 DeepWin 语音输入“明天下午三点开会”，DeepWin 业务逻辑识别后，调用 `create_event(title, start_time)` Tool，在用户日历中创建事件。
  - **潜在 MCP URL 示例：** `https://api.some-calendar-mcp.com/v1`
- **智能家居控制 MCP (e.g., `SmartHomeMCP`)**
  - **功能：** 控制智能灯光、调节温度、开关设备。
  - **DeepWin 功能实现：**
    - **智能面板控制：** DeepWin UI 提供一个智能家居控制面板，用户点击按钮，调用 `set_light_state(room, state)` Tool，控制家中设备。
    - **情景模式：** 用户一键触发“回家模式”，DeepWin 调用多个 `SmartHomeMCP` Tools (`set_light_state`, `set_temperature`) 实现联动。
  - **潜在 MCP URL 示例：** `https://api.some-smarthome-mcp.com/v1`
- **金融数据 MCP (e.g., `StockQuoteMCP`)**
  - **功能：** 查询股票实时报价、历史数据、公司财报。
  - **DeepWin 功能实现：**
    - **投资组合监控：** 用户在 DeepWin 中配置关注的股票，DeepWin 调用 `get_stock_quote(symbol)` Resource，实时显示股价。
    - **个人理财辅助：** 结合用户的记忆（如“我上次买比特币是什么时候？”），DeepWin 查询历史价格数据。
  - **潜在 MCP URL 示例：** `https://api.some-finance-mcp.com/v1`
- **高德地图 MCP (e.g., `AmapMapsMCP`)**
  - **功能：** 提供地图、POI、路径规划、天气等服务。
  - **DeepWin 功能实现：**
    - **城市天气查询：** 通过调用 `maps_weather` 工具，根据城市名称获取天气信息。
    - **地图显示与导航：** 在 UI 中展示地图，进行地点搜索和导航。
  - **潜在 MCP URL 示例：** `https://mcp.so/server/amap-maps/amap`

**总结：** 通过集成这些外部 MCP 服务，DeepWin 能够极大地扩展其功能边界，从一个单纯的记忆管理和设备控制软件，进化为一个能够整合外部信息、操控外部服务的智能中枢。

## 4. DeepWin MCP 客户端模块目录结构

为了保持清晰的模块化和可维护性，DeepWin 内部的 MCP 客户端相关功能建议采用以下目录结构：

```
DeepWin/
├── src/
│   ├── app_logic/
│   │   ├── mcp_client_manager/  # MCP 客户端管理器核心逻辑
│   │   │   ├── __init__.py
│   │   │   ├── mcp_client_manager.py # MCPClientManager 类定义
│   │   │   └── config.py             # MCP 服务注册配置 (URL, API Key, 类型等)
│   │   ├── weather_manager.py        # NEW: 天气业务逻辑管理，将调用 MCPClientManager
│   │   ├── # 其他业务逻辑模块 (e.g., memory_manager, device_logic_manager)
│   ├── services/
│   │   ├── cloud_communication/ # 云端通信服务
│   │   │   ├── __init__.py
│   │   │   ├── api_client.py   # 现有云端API客户端
│   │   │   ├── websocket_client.py # 现有WebSocket客户端
│   │   │   ├── mcp_client_wrappers/ # FastMCPClientWrapper 及其数据适配器
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base_mcp_wrapper.py     # FastMCPClientWrapper 抽象基类 (可选，用于通用接口)
│   │   │   │   ├── generic_mcp_wrapper.py  # 通用 FastMCPClientWrapper 实现 (处理 FastMCP Client 实例)
│   │   │   │   └── data_adapters.py        # 数据适配器类/函数
│   │   ├── hardware_communication/ # 硬件通信服务
│   │   │   ├── # ... (现有串口、CAN总线、协议解析等)
│   │   ├── # 其他服务层模块
│   ├── ui/
│   │   ├── components/
│   │   │   └── mcp_widgets/      # 对应 MCP 服务的 UI 组件，例如 NewsFeedWidget, WeatherQueryWidget
│   │   │       ├── __init__.py
│   │   │       └── weather_query_widget.py # NEW: 天气查询 UI 组件
│   │   └── # 其他 UI 相关文件
│   └── main.py  # 应用程序主入口
├── config/
│   └── app_settings.json # 应用程序主配置文件，包含 MCP 服务 URL 等
└── requirements.txt # 项目依赖
```

**结构说明：**

- **`services/cloud_communication/mcp_client_wrappers/`**: 这是 MCP 客户端相关模块的新位置。由于 MCP 服务通常是基于网络的、提供给 LLM 或其他客户端的抽象接口，将其归类在 `cloud_communication` 下是合理的。这使得 `services` 目录下的职责划分更清晰：`hardware_communication` 负责与物理设备的底层通信，而 `cloud_communication` 负责与远程服务（包括 MCP 服务）的交互。
- **`app_logic/weather_manager.py`**: 新增的天气业务逻辑管理模块，将负责调用 MCP 客户端管理器来获取天气数据。
- **`ui/components/mcp_widgets/weather_query_widget.py`**: 新增的 UI 组件，用于展示天气查询的界面。

## 5. MCP 相关数据流设计

在 DeepWin 中，MCP 相关的典型数据流可以分为两种主要场景：

### 5.1 场景一：DeepWin 直接调用 MCP 服务（用于自身功能实现）

这是 DeepWin 作为 MCP 客户端最直接的应用场景，用于获取数据或执行操作以支持其自身的 UI 功能或内部业务逻辑，通常不涉及 LLM 的直接参与决策。

1. **用户交互/业务逻辑触发：** 用户在 DeepWin UI 上点击某个按钮（例如“查看最新新闻”），或者 DeepWin 内部的定时任务（例如“更新天气信息”）触发。
2. **业务模块发起请求：** 对应的 DeepWin 业务模块（例如，一个 `NewsManager` 或 `WeatherManager`）识别到需要调用外部 MCP。
3. **请求路由至 `MCPClientManager`：** 业务模块将抽象请求（例如 `mcp_client_manager.query_resource("news_mcp", "latest_headlines", topic="AI")` 或 `mcp_client_manager.perform_action("amap_maps_mcp", "maps_weather", args=["北京"])`）发送给 `MCPClientManager`。请求中通常会包含目标 MCP 的标识符和具体的 Resource/Tool 名称及参数。
4. **`MCPClientManager` 分发：** `MCPClientManager` 根据请求中的 MCP 标识符，查找并路由请求给对应的 `FastMCPClientWrapper` 实例。
5. **`FastMCPClientWrapper` 调用 `fastmcp` 客户端：** `FastMCPClientWrapper` 接收到请求，将其转换为 `fastmcp.client.Client` 可以执行的 Resource 查询或 Tool 调用，并通过网络发送到目标 MCP 服务。
6. **MCP 服务响应：** 外部 MCP 服务接收请求，执行相应操作，并返回符合 MCP 协议的响应数据。
7. **`FastMCPClientWrapper` 接收与初步处理：** `FastMCPClientWrapper` 接收到响应，进行初步的错误检查。
8. **`MCPDataAdapters` 数据适配：** 响应数据被传递给 `MCPDataAdapters`，转换为 DeepDiary 内部统一的数据模型。
9. **结果回传至业务模块/UI：** 经过适配的数据返回给 DeepWin 的业务模块，业务模块更新其状态或直接通知 UI 进行显示更新。

_图 2: DeepWin 直接调用 MCP 服务数据流_

### 5.2 场景二：DeepWin 通过 LLM 调用 MCP 服务（LLM 作为核心决策者）

此场景中，用户的意图首先由 LLM 进行理解和决策，LLM 再决定是否调用 MCP 服务。DeepWin 在此扮演 LLM 的前端界面和底层硬件操作的枢纽。

1. **用户自然语言输入：** 用户在 DeepWin 的聊天界面（或通过语音）输入自然语言指令（例如“帮我查找最近的智能家居新闻并控制客厅灯光”）。
2. **请求转发至 LLM Agent：** DeepWin 的语音/文本交互模块将用户的指令发送给 DeepServer 上部署的 LLM Agent (例如 Dify 的 API，FUN018)。
3. **LLM Agent 意图识别与 MCP 调用决策 (在 DeepServer 端)：**
   - DeepServer 上的 LLM Agent 接收到用户指令。
   - LLM 通过其内部推理和工具调用能力，识别用户意图，并决定需要调用哪些 **MCP Tools/Resources** 来完成任务。这些 MCPs 可能包括：
     - DeepServer 自身暴露的 MCPs (如 `MemoryResourceMCP` 的 `query_memories` Resource，或 `DeepArmControlMCP` 的 `move_arm_arm` Tool)。
     - 或者，DeepServer 作为一个更高级的编排者，**它内部可能也配置了 `fastmcp` 客户端去调用外部的 MCP 服务** (例如 `NewsFeedMCP` 或 `SmartHomeMCP`)。
   - LLM Agent 通过其内部的 `fastmcp` 客户端（在 DeepServer 端）调用相应的 MCP 服务。
4. **MCP 服务执行与响应：** 被调用的 MCP 服务执行操作并返回结果。
   - **重要特例：硬件控制 MCPs (例如 `DeepArmControlMCP`)：**
     - 当 LLM Agent 决定控制 DeepArm 机械臂时，DeepServer 上的 `DeepArmControlMCP` 服务会生成机械臂的抽象控制命令。
     - 这些命令需要通过 DeepWin 才能到达物理机械臂。DeepServer 可以通过 WebSocket 或其他 RPC 机制将这些命令发送给连接到它的 DeepWin 客户端。
5. **DeepWin 接收 DeepServer 指令（仅限硬件控制）：** 如果涉及到 DeepWin 直接连接的硬件（如 DeepArm），DeepWin 的 `DeviceLogicManager` 会接收到来自 DeepServer 的控制指令。
6. **DeepWin 执行硬件操作：** `DeviceLogicManager` 将指令转发给 `DeviceProtocolParser` 和 `SerialCommunicator`，最终发送给机械臂。
7. **结果返回至 LLM Agent：** 硬件操作的执行结果（或从其他 MCPs 获取的数据）通过 DeepServer 返回给 LLM Agent。
8. **LLM Agent 生成回复：** LLM Agent 综合所有 MCP 调用的结果，生成最终的自然语言回复。
9. **DeepWin 显示回复：** LLM Agent 将回复发送回 DeepWin UI，展示给用户。

_图 3: DeepWin 通过 LLM 调用 MCP 服务数据流_

## 6. 核心组件设计与解释

### 6.1 `MCPClientManager`

- **位置：** `DeepWin/src/app_logic/mcp_client_manager/mcp_client_manager.py`

- **职责：** DeepWin 中 MCP 客户端功能的总协调者和入口点。

- **核心功能：**

  - **初始化：** 在 DeepWin 启动时，根据 `config/app_settings.json` 中配置的 MCP 服务信息，实例化对应的 `FastMCPClientWrapper` 实例。

  - **服务注册表：** 维护一个字典，键为 MCP 服务的唯一标识符（例如 "deepserver_memory_mcp", "news_feed_mcp"），值为对应的 `FastMCPClientWrapper` 实例。

  - **请求路由：** 接收来自 DeepWin 业务模块（如 `MemoryManager`、`DeviceLogicManager`）的抽象请求，根据目标 MCP 的标识符，将请求转发给正确的 `FastMCPClientWrapper` 实例。

  - **生命周期管理：** 负责 MCP 客户端的连接建立和断开。

  - **接口示例：**

    ```
    # mcp_client_manager.py
    class MCPClientManager(QObject):
        mcp_response_ready = Signal(str, dict) # (mcp_id, data)
        mcp_error = Signal(str, str) # (mcp_id, error_message)

        def __init__(self, config_manager: ConfigManager, log_manager: LogManager, parent=None):
            super().__init__(parent)
            self.config_manager = config_manager
            self.logger = log_manager.get_logger("MCPClientManager")
            self._mcp_wrappers: Dict[str, FastMCPClientWrapper] = {}
            self._load_mcp_configurations()

        def _load_mcp_configurations(self):
            # 从 config_manager 加载所有 MCP 配置
            # 例如：app_settings.json 中有一个 "mcp_services" 列表
            mcp_configs = self.config_manager.get('mcp_services', [])
            for config in mcp_configs:
                mcp_id = config.get("id")
                mcp_url = config.get("url")
                mcp_api_key = config.get("api_key") # 可选
                if mcp_id and mcp_url:
                    # NEW: 调整 import 路径
                    from deepwin.services.cloud_communication.mcp_client_wrappers.generic_mcp_wrapper import GenericFastMCPClientWrapper
                    wrapper = GenericFastMCPClientWrapper(
                        mcp_id, mcp_url, mcp_api_key, self.logger # 传入 logger
                    )
                    # 连接 wrapper 的信号到 MCPClientManager 的信号
                    wrapper.response_ready.connect(self.mcp_response_ready)
                    wrapper.error.connect(self.mcp_error)
                    self._mcp_wrappers[mcp_id] = wrapper
                    self.logger.info(f"MCPClientManager: 已注册 MCP 服务 '{mcp_id}' (URL: {mcp_url})")
                else:
                    self.logger.warning(f"MCPClientManager: 无效的 MCP 配置: {config}")

        @Slot(str, str, list)
        async def perform_action(self, mcp_id: str, tool_name: str, args: list) -> Dict[str, Any]:
            """
            向指定 MCP 服务执行 Tool 调用。
            :param mcp_id: 目标 MCP 服务的标识符。
            :param tool_name: 要调用的 Tool 名称。
            :param args: Tool 的参数。
            """
            wrapper = self._mcp_wrappers.get(mcp_id)
            if not wrapper:
                raise ValueError(f"未找到 MCP 服务 '{mcp_id}' 的封装器。")
            return await wrapper.call_tool(tool_name, *args)

        @Slot(str, str, dict)
        async def query_resource(self, mcp_id: str, resource_name: str, params: dict) -> Dict[str, Any]:
            """
            向指定 MCP 服务查询 Resource。
            :param mcp_id: 目标 MCP 服务的标识符。
            :param resource_name: 要查询的 Resource 名称。
            :param params: Resource 的查询参数。
            """
            wrapper = self._mcp_wrappers.get(mcp_id)
            if not wrapper:
                raise ValueError(f"未找到 MCP 服务 '{mcp_id}' 的封装器。")
            return await wrapper.query_resource(resource_name, **params)

        def cleanup(self):
            for wrapper in self._mcp_wrappers.values():
                # 异步关闭 HTTP 客户端，确保所有 await 结束
                try:
                    asyncio.run(wrapper.close())
                except RuntimeError as e:
                    self.logger.warning(f"清理 MCP wrapper 失败: {e}. 可能在非事件循环中调用异步操作.")
    ```

### 6.2 `FastMCPClientWrapper`

- **位置：** `DeepWin/src/services/cloud_communication/mcp_client_wrappers/generic_mcp_wrapper.py`

- **职责：** 封装 `fastmcp` 库提供的客户端功能，处理与单个 MCP 服务的具体交互。

- **核心功能：**

  - **`fastmcp.client.Client` 实例：** 每个 `FastMCPClientWrapper` 实例内部持有一个 `fastmcp.client.Client` 实例，负责与特定的 MCP 服务 URL 进行底层通信。

  - **请求构建与发送：** 将上层请求（如 `call_tool` 或 `query_resource`）转换为 `fastmcp` 库所需的格式，并发送请求。

  - **响应处理：** 接收 `fastmcp` 客户端的响应，进行初步解析、错误检查，并将原始响应数据传递给数据适配器。

  - **认证：** 管理与特定 MCP 服务交互所需的 API Key 或其他认证凭证。

  - **接口示例：**

    ```
    # services/cloud_communication/mcp_client_wrappers/generic_mcp_wrapper.py
    import asyncio
    from fastmcp.client import Client
    from typing import Dict, Any, Optional
    from PySide6.QtCore import QObject, Signal, Slot # 导入 QObject, Signal, Slot

    class GenericFastMCPClientWrapper(QObject): # 继承 QObject 以便使用信号槽
        response_ready = Signal(str, dict) # (mcp_id, data)
        error = Signal(str, str) # (mcp_id, error_message)

        def __init__(self, mcp_id: str, mcp_url: str, api_key: Optional[str], logger: Any, parent=None):
            super().__init__(parent)
            self.mcp_id = mcp_id
            self.mcp_url = mcp_url
            self.api_key = api_key
            self.logger = logger
            self.client = Client(server_url=mcp_url, api_key=api_key) # fastmcp 客户端实例
            self.logger.info(f"FastMCPClientWrapper for '{mcp_id}' initialized.")

        async def call_tool(self, tool_name: str, *args) -> Dict[str, Any]:
            """调用 MCP 服务的 Tool。"""
            try:
                self.logger.debug(f"Calling tool '{tool_name}' on MCP '{self.mcp_id}' with args: {args}")
                # fastmcp client 的工具调用方法
                # Amap Maps 的 maps_weather 工具期望一个 'city' 参数
                if tool_name == "maps_weather" and len(args) > 0:
                    city = args[0]
                    result = await self.client.tools.call(tool_name, city=city)
                else:
                    # 对于其他通用工具调用
                    result = await self.client.tools.call(tool_name, *args)

                self.response_ready.emit(self.mcp_id, {"tool_name": tool_name, "result": result})
                return result
            except Exception as e:
                error_msg = f"调用 MCP '{self.mcp_id}' 的工具 '{tool_name}' 失败: {e}"
                self.logger.error(error_msg)
                self.error.emit(self.mcp_id, error_msg)
                raise

        async def query_resource(self, resource_name: str, **params) -> Dict[str, Any]:
            """查询 MCP 服务的 Resource。"""
            try:
                self.logger.debug(f"Querying resource '{resource_name}' on MCP '{self.mcp_id}' with params: {params}")
                resource_data = await self.client.resources.query(resource_name, **params)
                self.response_ready.emit(self.mcp_id, {"resource_name": resource_name, "data": resource_data})
                return resource_data
            except Exception as e:
                error_msg = f"查询 MCP '{self.mcp_id}' 的资源 '{resource_name}' 失败: {e}"
                self.logger.error(error_msg)
                self.error.emit(self.mcp_id, error_msg)
                raise

        async def close(self):
            """关闭底层 HTTP 客户端连接 (如果 fastmcp 客户端支持)。"""
            # fastmcp client 通常不需要显式关闭，如果底层是 httpx，可能需要
            if hasattr(self.client, 'http_client') and hasattr(self.client.http_client, 'aclose'):
               await self.client.http_client.aclose()
            self.logger.info(f"FastMCPClientWrapper for '{self.mcp_id}' closed.")
    ```

### 6.3 `MCPDataAdapters`

- **位置：** `DeepWin/src/services/cloud_communication/mcp_client_wrappers/data_adapters.py`

- **职责：** 将从 MCP 服务接收到的原始数据转换为 DeepDiary 内部统一的数据模型。

- **核心功能：**

  - **数据模型转换：** 定义从各种 MCP 响应到 DeepDiary 内部数据结构的映射规则。

  - **数据清洗与验证：** 对接收到的数据进行必要的清洗、格式化和验证。

  - **接口示例：**

    ```
    # services/cloud_communication/mcp_client_wrappers/data_adapters.py
    from typing import Dict, Any, List

    class NewsDataAdapter:
        """将 NewsFeedMCP 响应转换为 DeepDiary 统一的新闻数据模型。"""
        @staticmethod
        def adapt(raw_news_data: Dict[str, Any]) -> List[Dict[str, Any]]:
            adapted_articles = []
            for article in raw_news_data.get("articles", []):
                adapted_articles.append({
                    "title": article.get("title", "无标题"),
                    "summary": article.get("description", "无描述"),
                    "source": article.get("source", {}).get("name", "未知来源"),
                    "url": article.get("url"),
                    "publish_date": article.get("publishedAt"),
                    # ... 更多字段映射
                })
            return adapted_articles

    class WeatherDataAdapter:
        """
        将 Amap Maps MCP 的 maps_weather 工具响应转换为 DeepDiary 统一的天气数据模型。
        响应结构可能因 MCP 服务而异，这里假设一个简化的结构。
        """
        @staticmethod
        def adapt(raw_weather_data: Dict[str, Any]) -> Dict[str, Any]:
            # 假设 raw_weather_data 是 maps_weather 工具返回的直接数据
            # 实际 MCP 响应结构可能需要根据 mcp.so 提供的工具文档来精确适配
            # 示例响应结构可能类似：{"status": "1", "lives": [...]}
            if raw_weather_data.get("status") == "1" and raw_weather_data.get("lives"):
                live_weather = raw_weather_data["lives"][0]
                adapted_weather = {
                    "province": live_weather.get("province"),
                    "city": live_weather.get("city"),
                    "weather": live_weather.get("weather"),
                    "temperature": live_weather.get("temperature"),
                    "winddirection": live_weather.get("winddirection"),
                    "windpower": live_weather.get("windpower"),
                    "humidity": live_weather.get("humidity"),
                    "reporttime": live_weather.get("reporttime")
                }
                return adapted_weather
            return {"error": "无法解析天气数据"}
    ```

## 7. 开发与集成指南

### 7.1 开发步骤

1. **安装 `fastmcp`：**

   ```
   pip install fastmcp httpx # httpx 是 fastmcp 的推荐 HTTP 客户端
   ```

2. **定义 MCP 服务配置：** 在 `config/app_settings.json` 中添加需要连接的外部 MCP 服务的配置信息，例如：

   ```
   {
     "mcp_services": [
       {
         "id": "news_feed_mcp",
         "url": "https://api.some-news-mcp.com/v1",
         "api_key": "YOUR_NEWS_API_KEY",
         "type": "external_news"
       },
       {
         "id": "amap_maps_mcp",
         "url": "https://mcp.so/server/amap-maps/amap",
         "api_key": "YOUR_AMAP_API_KEY_FOR_MCP_IF_NEEDED",
         "type": "external_maps"
       },
       {
         "id": "deepserver_memory_mcp",
         "url": "https://your-deepserver-ip/mcp",
         "api_key": "YOUR_DEEPSERVER_MCP_API_KEY",
         "type": "internal_memory_resource"
       }
     ]
   }
   ```

   _注：`mcp.so` 上的 MCP 服务可能需要其自身的 API Key，请查阅其文档。这里示例 `YOUR_AMAP_API_KEY_FOR_MCP_IF_NEEDED`。_

3. **实现 `FastMCPClientWrapper`：**

   - 对于通用 MCP 交互，可以使用 `GenericFastMCPClientWrapper` (如 6.2 节所示，已包含 `maps_weather` 适配)。
   - 如果某个外部 MCP 服务的通信或响应解析有特殊性，可以继承 `GenericFastMCPClientWrapper` 并实现特定的逻辑。

4. **实现 `MCPDataAdapters`：** 为每种 MCP 服务的响应数据定义适配器，将其转换为 DeepDiary 内部统一的数据模型 (如 6.3 节所示，已包含 `WeatherDataAdapter` )。

5. **在 `MCPClientManager` 中加载和管理：** `MCPClientManager` 会自动根据配置实例化和管理 `FastMCPClientWrapper` 实例。

6. **实现 `WeatherManager` (业务逻辑)：**

   ```
   # src/app_logic/weather_manager.py
   import asyncio
   from PySide6.QtCore import QObject, Signal, Slot
   from typing import Dict, Any

   # NEW: 导入 MCPClientManager 和 WeatherDataAdapter
   from deepwin.app_logic.mcp_client_manager.mcp_client_manager import MCPClientManager
   from deepwin.services.cloud_communication.mcp_client_wrappers.data_adapters import WeatherDataAdapter
   from deepwin.data_management.log_manager import LogManager # 假设有LogManager

   class WeatherManager(QObject):
       weather_info_ready = Signal(dict) # 信号：天气信息已准备好 (adapted_data)
       weather_error = Signal(str)      # 信号：天气查询错误 (error_message)

       def __init__(self, mcp_client_manager: MCPClientManager, log_manager: LogManager, parent=None):
           super().__init__(parent)
           self.mcp_client_manager = mcp_client_manager
           self.logger = log_manager.get_logger("WeatherManager")

           # 连接 MCPClientManager 的通用错误信号，用于捕获来自 MCP 的错误
           self.mcp_client_manager.mcp_error.connect(self._handle_mcp_error)
           # 对于特定响应，也可以连接 mcp_response_ready 并根据 mcp_id 过滤
           # 但这里我们将直接在 perform_weather_query 中处理结果

       @Slot(str)
       def query_city_weather(self, city_name: str):
           """
           根据城市名称查询天气。
           这个方法是一个槽，可以从 UI 线程调用。
           它将启动一个异步任务来执行 MCP 调用。
           """
           self.logger.info(f"WeatherManager: 收到查询城市 '{city_name}' 天气的请求。")
           # 在 PyQt 中，直接在槽函数中调用 asyncio.run() 是不推荐的
           # 更好的方式是使用 QThreadPool 或 QThread 来运行异步代码
           # 简化起见，这里直接使用 asyncio.create_task (假定已有运行中的事件循环)
           # 或者通过一个 WorkerRunnable 来桥接

           # 实际应用中，你可能需要一个 QThreadPool 来运行异步任务
           # from deepwin.app_logic.core_manager.coordinator import WorkerRunnable # 假设WorkerRunnable可用
           # worker = WorkerRunnable(self._async_query_weather, city_name)
           # self.thread_pool.start(worker) # 需要在 __init__ 中注入 thread_pool

           # 假设当前环境支持直接调用异步函数 (例如通过 PySide6-Asyncio)
           asyncio.create_task(self._async_query_weather(city_name))

       async def _async_query_weather(self, city_name: str):
           """异步执行天气查询逻辑。"""
           try:
               # 调用 MCPClientManager 发起 Tool 调用
               # Amap Maps MCP 的 ID 为 "amap_maps_mcp"，工具名为 "maps_weather"
               # 参数为 city 名称
               self.logger.debug(f"WeatherManager: 调用 Amap Maps MCP 的 maps_weather 工具，城市: {city_name}")
               raw_weather_data = await self.mcp_client_manager.perform_action(
                   "amap_maps_mcp", "maps_weather", [city_name]
               )
               self.logger.debug(f"WeatherManager: 收到原始天气数据: {raw_weather_data}")

               # 使用数据适配器转换数据
               adapted_weather = WeatherDataAdapter.adapt(raw_weather_data)
               self.logger.info(f"WeatherManager: 已获取并适配天气数据: {adapted_weather}")
               self.weather_info_ready.emit(adapted_weather)

           except Exception as e:
               error_message = f"查询城市 '{city_name}' 天气失败: {e}"
               self.logger.error(f"WeatherManager: {error_message}")
               self.weather_error.emit(error_message)

       @Slot(str, str)
       def _handle_mcp_error(self, mcp_id: str, error_msg: str):
           """处理来自 MCPClientManager 的通用错误。"""
           self.logger.error(f"WeatherManager: 来自 MCP '{mcp_id}' 的错误: {error_msg}")
           # 如果是天气相关的错误，可以进一步处理或发出特定信号
           if mcp_id == "amap_maps_mcp":
               self.weather_error.emit(f"高德地图天气服务错误: {error_msg}")
   ```

7. **实现 `WeatherQueryWidget` (UI 组件)：**

   ```
   # src/ui/components/mcp_widgets/weather_query_widget.py
   import asyncio
   from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
   from PySide6.QtCore import Qt, Signal, Slot
   from typing import Dict, Any

   # 导入 WeatherManager (业务逻辑)
   from deepwin.app_logic.weather_manager import WeatherManager # 假设路径正确
   from deepwin.data_management.log_manager import LogManager # 假设有LogManager

   # 导入 PySide6-Fluent-Widgets 组件以保持风格一致
   # from qfluentwidgets import LineEdit, PushButton, CardWidget, BodyLabel, SubtitleLabel # 仅作示例，需要实际导入

   class WeatherQueryWidget(QWidget):
       # 信号，用于在 GUI 线程中接收异步结果
       _weather_result_received = Signal(dict)
       _weather_error_received = Signal(str)

       def __init__(self, weather_manager: WeatherManager, log_manager: LogManager, parent=None):
           super().__init__(parent)
           self.weather_manager = weather_manager
           self.logger = log_manager.get_logger("WeatherQueryWidget")

           self._weather_result_received.connect(self._display_weather_info)
           self._weather_error_received.connect(self._show_error_message)

           self.init_ui()
           self._setup_connections()

       def init_ui(self):
           self.setWindowTitle("天气查询")
           self.layout = QVBoxLayout(self)

           # 城市输入
           self.city_input_layout = QHBoxLayout()
           self.city_label = QLabel("城市名称:")
           self.city_input = QLineEdit() # 替换为 Fluent Widgets 的 LineEdit
           self.city_input.setPlaceholderText("请输入城市名称，例如：北京")
           self.query_button = QPushButton("查询天气") # 替换为 Fluent Widgets 的 PushButton

           self.city_input_layout.addWidget(self.city_label)
           self.city_input_layout.addWidget(self.city_input)
           self.city_input_layout.addWidget(self.query_button)
           self.layout.addLayout(self.city_input_layout)

           # 天气信息显示
           self.weather_display_card = QWidget() # 替换为 Fluent Widgets 的 CardWidget
           self.weather_display_layout = QVBoxLayout(self.weather_display_card)
           self.weather_display_card.setObjectName("WeatherDisplayCard") # 用于QSS样式

           self.city_display_label = QLabel("城市: -") # 替换为 Fluent Widgets 的 SubtitleLabel
           self.temperature_label = QLabel("温度: -")
           self.weather_label = QLabel("天气: -")
           self.wind_label = QLabel("风向/风力: -")
           self.humidity_label = QLabel("湿度: -")
           self.report_time_label = QLabel("更新时间: -")

           self.weather_display_layout.addWidget(self.city_display_label)
           self.weather_display_layout.addWidget(self.temperature_label)
           self.weather_display_layout.addWidget(self.weather_label)
           self.weather_display_layout.addWidget(self.wind_label)
           self.weather_display_layout.addWidget(self.humidity_label)
           self.weather_display_layout.addWidget(self.report_time_label)
           self.weather_display_layout.addStretch(1) # 填充空白

           self.layout.addWidget(self.weather_display_card)
           self.layout.addStretch(1) # 填充空白

           # 样式 (仅作示例，实际应在QSS文件中定义)
           # self.setStyleSheet("""
           #     #WeatherDisplayCard {
           #         background-color: #f0f0f0;
           #         border-radius: 8px;
           #         padding: 15px;
           #     }
           # """)

       def _setup_connections(self):
           self.query_button.clicked.connect(self._on_query_button_clicked)
           # 将 WeatherManager 的信号连接到 WeatherQueryWidget 的内部槽函数，
           # 这些槽函数会发射自定义信号，确保在 GUI 线程中更新 UI
           self.weather_manager.weather_info_ready.connect(self._weather_result_received.emit)
           self.weather_manager.weather_error.connect(self._weather_error_received.emit)

       @Slot()
       def _on_query_button_clicked(self):
           city = self.city_input.text().strip()
           if city:
               self.logger.info(f"UI: 用户点击查询天气按钮，城市: {city}")
               self._clear_weather_display()
               self.city_display_label.setText("正在查询...")
               self.weather_manager.query_city_weather(city)
           else:
               QMessageBox.warning(self, "输入错误", "请输入城市名称。")

       @Slot(dict)
       def _display_weather_info(self, adapted_weather: Dict[str, Any]):
           if adapted_weather and not adapted_weather.get("error"):
               self.city_display_label.setText(f"城市: {adapted_weather.get('city', '-')}")
               self.temperature_label.setText(f"温度: {adapted_weather.get('temperature', '-')}°C")
               self.weather_label.setText(f"天气: {adapted_weather.get('weather', '-')}")
               self.wind_label.setText(f"风向/风力: {adapted_weather.get('winddirection', '-')}/{adapted_weather.get('windpower', '-')}级")
               self.humidity_label.setText(f"湿度: {adapted_weather.get('humidity', '-')}%")
               self.report_time_label.setText(f"更新时间: {adapted_weather.get('reporttime', '-')}")
           else:
               self._show_error_message(adapted_weather.get("error", "未知天气查询错误。"))

       @Slot(str)
       def _show_error_message(self, error_message: str):
           self.logger.error(f"UI: 显示错误消息: {error_message}")
           QMessageBox.critical(self, "天气查询错误", f"查询失败: {error_message}")
           self._clear_weather_display()
           self.city_display_label.setText("城市: -") # 重置显示

       def _clear_weather_display(self):
           self.temperature_label.setText("温度: -")
           self.weather_label.setText("天气: -")
           self.wind_label.setText("风向/风力: -")
           self.humidity_label.setText("湿度: -")
           self.report_time_label.setText("更新时间: -")
   ```

8. **更新 `Coordinator`：** 实例化 `WeatherManager` 并将其注入到 `WeatherQueryWidget`。

   ```
   # src/app_logic/core_manager/coordinator.py (仅显示关键更新部分)
   # ... 其他导入
   from deepwin.app_logic.mcp_client_manager.mcp_client_manager import MCPClientManager
   from deepwin.app_logic.weather_manager import WeatherManager # NEW: 导入 WeatherManager
   from deepwin.ui.components.mcp_widgets.weather_query_widget import WeatherQueryWidget # NEW: 导入 WeatherQueryWidget

   class Coordinator(QObject):
       # ... __init__ 方法

       def __init__(self, log_manager: LogManager, parent: Optional[QObject] = None):
           super().__init__(parent)
           self.logger = log_manager.get_logger(__name__)
           # ...

           self.config_manager = ConfigManager(log_manager=log_manager)

           # 实例化 MCPClientManager
           self.mcp_client_manager = MCPClientManager(log_manager=log_manager, config_manager=self.config_manager) # NEW
           # 实例化 WeatherManager，并传入 mcp_client_manager
           self.weather_manager = WeatherManager(mcp_client_manager=self.mcp_client_manager, log_manager=log_manager) # NEW

           self.gui_manager = MockGuiManager(log_manager=log_manager, config_manager=self.config_manager)

           # ... 实例化其他服务层组件和设备逻辑管理器

           self.logger.info("Coordinator: 正在设置信号和槽连接...")
           self._setup_connections()
           self.logger.info("Coordinator: 信号和槽连接设置完成。")

           # 可以在这里（或 main.py）创建并显示 WeatherQueryWidget
           self.weather_widget = WeatherQueryWidget(weather_manager=self.weather_manager, log_manager=log_manager) # NEW
           # self.weather_widget.show() # 如果是独立测试

       def _setup_connections(self):
           # ... 现有连接
           # MCPClientManager 的通用信号可以在这里连接到 Coordinator 的 app_status_message
           self.mcp_client_manager.mcp_error.connect(lambda mcp_id, msg: self.app_status_message.emit(f"MCP错误[{mcp_id}]: {msg}"))
           # WeatherManager 的信号连接到 GUI 管理器 (或直接在 UI 组件中连接)
           # 例如，如果 MockGuiManager 有一个 update_weather_display 方法
           # self.weather_manager.weather_info_ready.connect(self.gui_manager.update_weather_display)
           # self.weather_manager.weather_error.connect(self.gui_manager.show_weather_error)

           # ... 其他模块连接

       def cleanup(self):
           # ... 现有清理
           self.mcp_client_manager.cleanup() # NEW: 清理 MCPClientManager
           # self.weather_widget.close() # 如果在 Coordinator 中管理其生命周期
   ```

### 7.2 AI 编辑器/大模型集成指导

此架构使得 AI 编辑器（如 Cursor）或大模型（通过 Dify Agent）更容易理解和生成与 DeepWin MCP 客户端相关的代码。

- **Prompt Engineering：**
  - 在为 LLM 编写 Prompt 时，可以明确指示 LLM 使用 `MCPClientManager` 中暴露的抽象方法 (`perform_action`, `query_resource`) 来调用特定 MCP 服务的 Tools 或 Resources。
  - 例如：“当用户需要新闻时，调用 `mcp_client_manager` 的 `query_resource('news_feed_mcp', 'get_latest_news', {'topic': '...' })`。”
  - 对于天气查询：“当用户询问天气时，调用 `mcp_client_manager` 的 `perform_action('amap_maps_mcp', 'maps_weather', ['城市名称'])`。”
- **代码生成：**
  - AI 编辑器可以根据用户意图和 MCP 服务的注册信息，自动生成调用 `MCPClientManager` 接口的代码片段。
  - 当需要适配新的外部 MCP 服务时，AI 编辑器可以辅助生成 `FastMCPClientWrapper` 和 `MCPDataAdapters` 的模板代码，降低开发门槛。
- **调试与优化：**
  - 通过清晰的模块划分和日志记录，开发人员和 AI 工具可以更容易地追踪 MCP 请求的数据流和执行状态，快速定位问题。

## 8. 总结

DeepWin MCP 客户端架构通过引入 `fastmcp` 和分层的模块设计，实现了与多样化 MCP 服务的灵活集成。这种设计不仅使 DeepWin 能够利用 DeepServer 自身暴露的记忆和设备控制能力，还能轻松扩展到其他外部的智能服务，从而极大地丰富了 DeepWin 的功能生态。清晰的目录结构、数据流和组件职责划分，将为开发人员和 AI 编辑器提供坚实的指导，加速 DeepWin 智能功能的开发和部署。
