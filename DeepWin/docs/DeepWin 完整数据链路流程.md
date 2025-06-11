## DeepWin 完整数据链路流程

经过对服务层 (`src/services/hardware_communication`) 的集成，DeepWin 的数据链路现在能够更清晰地展示数据从硬件设备到应用逻辑层，以及从应用逻辑层到硬件设备的完整流转。这一流程遵循了严格的分层架构，确保了模块间的解耦和职责分离。

### 1. 数据从设备到应用逻辑层（上行数据流）

这条链路描述了从 DeepArm 机械臂（通过 CAN 转 USB 串口）获取原始数据，到最终在 DeepWin 应用逻辑层更新设备状态的过程。

1. **DeepArm 设备（硬件）**
   - **发送数据**：DeepArm 机械臂采集自身的关节角度、温度、状态等信息，并通过 CAN 总线传输。
   - **CAN 转 USB 模块**：这个硬件模块将 CAN 帧数据封装成特定的串口字符串格式（`AT头 + CANID + Len + Data + \r\n`），并通过 USB 接口（模拟为串口）发送给 DeepWin 运行的电脑。
2. **`SerialCommunicator` (服务层：`src/services/hardware_communication/serial_communicator.py`)**
   - **接收原始串口数据**：`SerialCommunicator` 在 `_read_serial_data` 方法中周期性地从模拟串口 (`COM1`) 读取原始字节行（例如 `b"AT00000108AABBCCDDEEFF0011\r\n"`）。
   - **初步串口协议解析**：它解析这条字符串，去除 `AT` 头和 `\r\n` 尾，并将中间的十六进制字符串（CAN ID, Len, Data）转换为 Python 原生类型（`int` 和 `bytes`）。
   - **发射 CAN 帧组件信号**：将解析出的 CAN 帧组件 (`port_name`, `arbitration_id`, `data_bytes`, `is_extended_id`) 通过 `can_frame_components_received` 信号发射出去。
   - **信号连接**：`SerialCommunicator.can_frame_components_received` **连接**到 `CanBusCommunicator.process_serial_can_frame`。
3. **`CanBusCommunicator` (服务层：`src/services/hardware_communication/can_bus_communicator.py`)**
   - **接收 CAN 帧组件**：`process_serial_can_frame` 槽函数接收到 `SerialCommunicator` 发射的 CAN 帧组件。
   - **创建 `can.Message` 对象**：它将这些组件封装成 `python-can` 库的 `can.Message` 对象。
   - **DBC 文件解析**：在 `_on_can_message_received` 方法中，`CanBusCommunicator` 会查找与 `can.Message` 的 `arbitration_id` 匹配的 DBC 报文定义。如果找到，它会使用 `cantools` 库（根据 `deeparm.dbc` 文件）将原始的 `data_bytes` 解码成具有实际物理意义的信号（例如 `{"Joint1Angle": 170, "Joint2Angle": 187, ...}`）。
   - **发射解析后 CAN 信号信号**：将解析后的 CAN 信号数据 (`channel`, `parsed_signals_dict`) 通过 `can_parsed_data_received` 信号发射出去。
   - **信号连接**：`CanBusCommunicator.can_parsed_data_received` **连接**到 `DeviceProtocolParser.parse_low_level_data`。
4. **`DeviceProtocolParser` (服务层：`src/services/hardware_communication/device_protocol_parser.py`)**
   - **接收低层次解析数据**：`parse_low_level_data` 槽函数接收到 `CanBusCommunicator` 发射的 DBC 解析后的信号字典。
   - **转换为业务语义数据**：它根据预定义的设备协议规则（在 `_device_protocol_rules` 中），将这些底层信号名映射到应用逻辑层理解的业务字段名（例如将 `Joint1Angle` 映射为 `joint1_angle`），并进行必要的单位转换或数据校验。
   - **发射业务语义数据信号**：将转换后的业务语义数据 (`device_id`, `semantic_data_dict`) 通过 `device_semantic_data_ready` 信号发射出去。
   - **信号连接**：`DeviceProtocolParser.device_semantic_data_ready` **连接**到 `DeviceLogicManager.handle_device_semantic_data`。
5. **`DeviceLogicManager` (应用逻辑层：`src/app_logic/device_logic_manager/manager.py`)**
   - **接收业务语义数据**：`handle_device_semantic_data` 槽函数接收到 `DeviceProtocolParser` 发射的、已经具备业务语义的数据字典。
   - **更新设备状态模型**：它将这些数据更新到其内部维护的 `DeepArmState` 或 `DeepToyState` 对象中。
   - **执行业务逻辑**：在此之后，可以执行与设备状态相关的业务逻辑，例如异常检测 (`_check_anomaly`)、示教轨迹记录等。
   - **发射设备状态更新信号**：通过 `device_status_updated` 信号通知 `Coordinator`（进而通知 UI）设备状态已更新。

### 2. 命令从应用逻辑层到设备（下行命令流）

这条链路描述了 DeepWin 应用逻辑层发出抽象控制命令，到最终命令通过串口发送给 DeepArm 机械臂的过程。

1. **`DeviceLogicManager` (应用逻辑层：`src/app_logic/device_logic_manager/manager.py`)**
   - **接收抽象命令**：当应用逻辑层需要控制 DeepArm 机械臂时（例如，UI 请求“移动到指定点”，或者智能体发出指令），它会调用 `DeviceLogicManager.send_command_to_device(device_id, abstract_command)`。
   - **发射抽象命令请求信号**：`send_command_to_device` 方法将抽象命令及其参数解析后，通过 `send_device_abstract_command_requested(device_id, abstract_command_name, args)` 信号发射出去，请求 `Coordinator` 处理。
   - **信号连接**：`DeviceLogicManager.send_device_abstract_command_requested` **连接**到 `Coordinator._on_device_abstract_command_requested`。
2. **`Coordinator` (核心协调器：`src/app_logic/core_manager/coordinator.py`)**
   - **接收抽象命令请求**：`_on_device_abstract_command_requested` 槽函数接收到 `DeviceLogicManager` 发出的抽象命令请求。
   - **请求协议转换**：`Coordinator` 调用 `DeviceProtocolParser.generate_low_level_command(device_id, abstract_command_name, *args)`。
   - **发送底层命令**：一旦获得底层命令的字节串（例如 `b"AT000001080A141E28323C\r\n"`），`Coordinator` 会调用 `SerialCommunicator.send_bytes(device_id, low_level_command_bytes)` 将其发送给串口。
   - **信号连接**：`Coordinator` 间接通过调用 `SerialCommunicator.send_bytes` 来完成命令的下发。
3. **`DeviceProtocolParser` (服务层：`src/services/hardware_communication/device_protocol_parser.py`)**
   - **生成底层命令**：`generate_low_level_command` 方法接收抽象命令名称和参数，并根据设备类型和协议规则，将这些高级指令转换为设备可以直接理解的底层协议命令（例如，CAN 帧的实际数据，并封装到 `AT头 + CANID + Len + Data + \r\n` 格式的字节串）。
4. **`SerialCommunicator` (服务层：`src/services/hardware_communication/serial_communicator.py`)**
   - **发送原始字节数据**：`send_bytes` 方法接收 `DeviceProtocolParser` 生成的最终字节串，并通过实际的串口发送给 CAN 转 USB 模块。
5. **CAN 转 USB 模块 & DeepArm 设备（硬件）**
   - **接收串口数据**：CAN 转 USB 模块接收到串口数据。
   - **转换为 CAN 帧**：该模块将串口数据还原为 CAN 帧。
   - **DeepArm 执行命令**：CAN 帧最终到达 DeepArm 机械臂，机械臂根据命令执行相应动作。

### 总结

这个完整的数据链路设计实现了清晰的职责划分：

- **硬件层**：负责物理通信和最底层的协议封装/解封装（CAN 转 USB）。
- **服务层 (`hardware_communication`)**：
  - `SerialCommunicator`：处理串口物理通信和“AT”帧的初步解析/组装。
  - `CanBusCommunicator`：专注于 CAN 协议（包括 DBC 解析），将 CAN 帧转换为可理解的信号字典，并处理信号编码。
  - `DeviceProtocolParser`：作为硬件通信层与应用逻辑层的桥梁，将底层信号数据转换为业务语义，并将业务抽象命令转换为底层协议命令。
- **应用逻辑层 (`device_logic_manager`)**：
  - `DeviceLogicManager`：专注于设备的业务逻辑、状态管理和高层次的控制（如示教），不关心底层通信细节。
- **核心协调器 (`coordinator`)**：
  - `Coordinator`：作为中央枢纽，实例化并连接各个模块，负责信号的路由和跨层级的协调。

这种架构提供了极高的灵活性和可扩展性，未来可以轻松地添加新的设备类型（只需更新 DBC 文件或 `DeviceProtocolParser` 规则）、新的通信协议，而无需大规模修改核心业务逻辑。
