# DeepWeb 软件技术架构文档

## 文档信息
- **项目名称**: DeepWeb - 不倒翁桌面记忆管家Web端
- **版本**: v1.0
- **创建日期**: 2025-10-26
- **最后更新**: 2025-10-26
- **文档类型**: 技术架构设计文档

## 1. 架构概述

### 1.1 整体架构设计
DeepWeb采用分层架构设计，包含前端展示层、业务逻辑层、数据访问层和基础设施层，支持多阶段开发策略。

### 1.2 开发阶段规划

#### 阶段一：Demo原型阶段 (4-6周)
**目标**: 快速验证核心功能和技术可行性

**技术栈选择**:
- **前端框架**: Streamlit (Python)
- **后端服务**: FastAPI (Python)
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **消息队列**: Redis + MQTT
- **图像处理**: OpenCV + Pillow
- **AI集成**: OpenAI API / 本地模型

**架构特点**:
- 单体应用架构，快速开发
- 内置Web界面，无需额外前端开发
- 支持实时数据流和交互式组件
- 便于AI模型集成和调试

#### 阶段二：产品化阶段 (8-12周)
**目标**: 构建可扩展的生产级系统

**技术栈选择**:
- **前端框架**: Vue 3 + TypeScript + Element Plus
- **状态管理**: Pinia
- **构建工具**: Vite
- **UI组件**: Element Plus + 自定义组件
- **图表库**: ECharts / Chart.js
- **实时通信**: WebSocket + Socket.io

- **后端框架**: FastAPI + Python 3.11+
- **API网关**: Nginx
- **数据库**: PostgreSQL + Redis
- **消息队列**: RabbitMQ + MQTT Broker
- **文件存储**: MinIO / AWS S3
- **容器化**: Docker + Docker Compose

**架构特点**:
- 微服务架构，模块化设计
- 前后端分离，独立部署
- 支持水平扩展和负载均衡
- 完整的监控和日志系统

## 2. 系统架构设计

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        DeepWeb 系统架构                          │
├─────────────────────────────────────────────────────────────────┤
│  前端层 (Frontend Layer)                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  设备控制   │  │  记忆管理   │  │  资源管理   │              │
│  │   界面      │  │   界面      │  │   界面      │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              AI聊天统一入口界面                            │ │
│  └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  API网关层 (API Gateway Layer)                                  │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Nginx + 负载均衡                              │ │
│  └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  业务服务层 (Business Service Layer)                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  设备交互   │  │  记忆管理   │  │  资源管理   │              │
│  │   服务      │  │   服务      │  │   服务      │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  AI聊天     │  │  图像处理   │  │  用户管理   │              │
│  │   服务      │  │   服务      │  │   服务      │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│  核心逻辑层 (Core Logic Layer) - 复用DeepWin架构               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  记忆管理   │  │  资源需求   │  │  AI协调器   │              │
│  │   逻辑      │  │   管理逻辑   │  │   逻辑      │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  设备逻辑   │  │  数据处理   │  │  智能体     │              │
│  │   管理器     │  │   管理器     │  │   管理器     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│  数据访问层 (Data Access Layer)                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  PostgreSQL │  │    Redis    │  │   MinIO     │              │
│  │   (主数据库) │  │  (缓存/队列) │  │  (文件存储) │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
├─────────────────────────────────────────────────────────────────┤
│  基础设施层 (Infrastructure Layer)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  MQTT Broker│  │   Docker    │  │  监控日志   │              │
│  │  (设备通信)  │  │  (容器化)   │  │   (ELK)     │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 核心逻辑层设计 (复用DeepWin架构)

#### 2.2.1 记忆管理逻辑
```
记忆管理逻辑 (Memory Manager)
├── 记忆存储管理
│   ├── 多模态数据存储
│   ├── 记忆索引构建
│   └── 记忆检索优化
├── 记忆处理服务
│   ├── 图像处理 (Image Processing)
│   ├── 文本处理 (Text Processing)
│   ├── 语音处理 (Audio Processing)
│   └── 视频处理 (Video Processing)
├── 记忆融合服务
│   ├── 多源数据整合
│   ├── 时间线构建
│   └── 关联分析
└── 智能推荐引擎
    ├── 基于内容的推荐
    ├── 协同过滤推荐
    └── 深度学习推荐
```

#### 2.2.2 资源需求管理逻辑
```
资源需求管理逻辑 (Resource Demand Manager)
├── 资源管理
│   ├── 资源分类和标签
│   ├── 资源搜索和过滤
│   └── 资源关系维护
├── 需求管理
│   ├── 需求优先级管理
│   ├── 需求状态跟踪
│   └── 需求匹配算法
├── 智能匹配引擎
│   ├── 向量化匹配
│   ├── 语义相似度计算
│   └── 多维度评分
└── 关系图谱构建
    ├── 用户关系网络
    ├── 资源关系网络
    └── 需求关系网络
```

#### 2.2.3 AI协调器逻辑
```
AI协调器逻辑 (AI Coordinator)
├── 智能体管理
│   ├── 智能体注册和发现
│   ├── 智能体生命周期管理
│   └── 智能体通信协调
├── 任务调度
│   ├── 任务分解和分配
│   ├── 任务优先级管理
│   └── 任务执行监控
├── 意图识别
│   ├── 自然语言理解
│   ├── 多模态意图识别
│   └── 上下文管理
└── 响应生成
    ├── 模板引擎
    ├── 动态内容生成
    └── 多媒体响应
```

#### 2.2.4 设备逻辑管理器
```
设备逻辑管理器 (Device Logic Manager)
├── 设备状态管理
│   ├── 设备连接状态
│   ├── 设备健康监控
│   └── 设备异常检测
├── 设备控制逻辑
│   ├── 控制命令队列
│   ├── 命令执行监控
│   └── 控制响应处理
├── 设备数据管理
│   ├── 传感器数据处理
│   ├── 设备日志管理
│   └── 历史数据存储
└── 设备协议适配
    ├── MQTT协议适配
    ├── TCP协议适配
    └── WebSocket适配
```

### 2.3 核心模块架构

#### 2.3.1 设备交互模块
```
设备交互服务
├── MQTT客户端管理
│   ├── 连接池管理
│   ├── 主题订阅/发布
│   └── 消息路由
├── TCP图像服务
│   ├── 图像流管理
│   ├── 格式转换
│   └── 缓存机制
├── 设备控制服务
│   ├── 命令队列
│   ├── 状态同步
│   └── 错误处理
└── 实时数据服务
    ├── WebSocket管理
    ├── 数据推送
    └── 连接管理
```

#### 2.2.2 记忆管理模块
```
记忆管理服务
├── Immich集成
│   ├── API客户端
│   ├── 数据同步
│   └── 缓存策略
├── Django后端集成
│   ├── 用户数据API
│   ├── 聊天记录API
│   └── 日记管理API
├── 数据融合服务
│   ├── 多源数据整合
│   ├── 去重处理
│   └── 关联分析
└── 搜索服务
    ├── 全文检索
    ├── 语义搜索
    └── 智能推荐
```

#### 2.2.3 AI聊天模块
```
AI聊天服务
├── 对话管理
│   ├── 会话管理
│   ├── 上下文维护
│   └── 历史记录
├── 多模态处理
│   ├── 文本处理
│   ├── 语音处理
│   ├── 图像处理
│   └── 文件处理
├── 意图识别
│   ├── 设备控制意图
│   ├── 记忆查询意图
│   ├── 资源匹配意图
│   └── 通用对话意图
└── 响应生成
    ├── 模板引擎
    ├── 动态内容
    └── 多媒体响应
```

## 3. 代码复用策略

### 3.1 DeepWin代码复用方案

#### 3.1.1 高度可复用模块
**记忆管理模块** (`app_logic/memory_manager/`):
- **复用内容**: 记忆存储、检索、融合逻辑
- **适配方式**: 保持Python实现，通过API接口暴露
- **Web端集成**: 通过FastAPI服务调用

**资源需求管理** (`app_logic/resource_demand_manager/`):
- **复用内容**: 资源分类、匹配算法、关系图谱
- **适配方式**: 直接复用Python实现
- **Web端集成**: 作为微服务部署

**AI协调器** (`app_logic/ai_coordinator/`):
- **复用内容**: 智能体管理、任务调度、意图识别
- **适配方式**: 保持核心逻辑，适配Web环境
- **Web端集成**: 通过WebSocket进行实时通信

#### 3.1.2 需要适配的模块
**设备逻辑管理器** (`app_logic/device_logic_manager/`):
- **适配内容**: 移除串口通信，保留MQTT通信
- **适配方式**: 抽象设备通信接口，实现MQTT适配器
- **Web端集成**: 通过MQTT客户端进行设备通信

**数据处理模块** (`app_logic/memory_processing/`):
- **复用内容**: 图像处理、文本处理算法
- **适配方式**: 保持处理逻辑，适配Web存储
- **Web端集成**: 通过MinIO进行文件存储

#### 3.1.3 不可复用的模块
**UI模块** (`ui/`):
- **原因**: 基于PySide6，与Web端Vue3不兼容
- **解决方案**: 重新设计Web界面，复用业务逻辑

**硬件通信** (`services/hardware_communication/`):
- **原因**: 基于串口和CAN总线，Web端不需要
- **解决方案**: 使用MQTT替代串口通信

### 3.2 代码复用实现方案

#### 3.2.1 共享库架构
```
deepwin-shared/
├── memory_manager/          # 记忆管理核心逻辑
├── resource_manager/       # 资源管理核心逻辑
├── ai_coordinator/         # AI协调器核心逻辑
├── device_manager/         # 设备管理核心逻辑
├── data_processing/        # 数据处理核心逻辑
└── utils/                  # 共享工具函数
```

#### 3.2.2 适配器模式
```python
# 设备通信适配器示例
class DeviceCommunicationAdapter:
    def __init__(self, communication_type: str):
        if communication_type == "serial":
            self.communicator = SerialCommunicator()
        elif communication_type == "mqtt":
            self.communicator = MQTTCommunicator()
        elif communication_type == "tcp":
            self.communicator = TCPCommunicator()
    
    def send_command(self, device_id: str, command: dict):
        return self.communicator.send_command(device_id, command)
    
    def receive_data(self, device_id: str):
        return self.communicator.receive_data(device_id)
```

#### 3.2.3 微服务化部署
```yaml
# docker-compose.yml for shared services
version: '3.8'
services:
  memory-service:
    build: ./deepwin-shared/memory_manager
    ports:
      - "8001:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/memory
  
  resource-service:
    build: ./deepwin-shared/resource_manager
    ports:
      - "8002:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/resource
  
  ai-coordinator-service:
    build: ./deepwin-shared/ai_coordinator
    ports:
      - "8003:8000"
    environment:
      - REDIS_URL=redis://redis:6379
```

## 4. 技术选型详细说明

### 3.1 Demo阶段技术栈

#### 3.1.1 前端技术
**Streamlit**:
- 优势: 快速开发、内置组件丰富、AI集成友好
- 适用场景: 原型验证、数据可视化、交互式应用
- 核心组件: 设备状态面板、图像显示、聊天界面

**技术实现**:
```python
# 核心组件示例
import streamlit as st
import plotly.graph_objects as go
from streamlit_webrtc import webrtc_streamer

# 设备状态监控
def device_status_panel():
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("连接状态", "在线", "正常")
    with col2:
        st.metric("CPU温度", "45°C", "2°C")
    with col3:
        st.metric("内存使用", "65%", "5%")

# 实时图像显示
def image_stream():
    webrtc_streamer(
        key="device_camera",
        video_transformer_factory=VideoTransformer,
        async_transform=True
    )
```

#### 3.1.2 后端技术
**FastAPI**:
- 优势: 高性能、自动API文档、类型提示支持
- 核心功能: RESTful API、WebSocket支持、异步处理

**技术实现**:
```python
from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json

app = FastAPI(title="DeepWeb API", version="1.0.0")

# MQTT消息处理
@app.websocket("/ws/device/{device_id}")
async def websocket_endpoint(websocket: WebSocket, device_id: str):
    await websocket.accept()
    # 处理设备数据推送
    while True:
        data = await get_device_data(device_id)
        await websocket.send_text(json.dumps(data))
        await asyncio.sleep(1)
```

### 3.2 产品化阶段技术栈

#### 3.2.1 前端技术
**Vue 3 + TypeScript**:
- 优势: 组合式API、更好的类型安全、性能优化
- 核心特性: 响应式数据、组件化开发、状态管理

**技术实现**:
```typescript
// 设备状态管理
interface DeviceState {
  id: string;
  status: 'online' | 'offline' | 'error';
  lastUpdate: Date;
  components: ComponentStatus[];
}

// 设备控制组件
<template>
  <div class="device-control">
    <el-card v-for="device in devices" :key="device.id">
      <DeviceStatusPanel :device="device" />
      <DeviceControlPanel :device="device" @command="sendCommand" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useDeviceStore } from '@/stores/device';

const deviceStore = useDeviceStore();
const devices = ref<DeviceState[]>([]);

const sendCommand = async (deviceId: string, command: DeviceCommand) => {
  await deviceStore.sendCommand(deviceId, command);
};
</script>
```

#### 3.2.2 后端技术
**微服务架构**:
- 服务拆分: 设备服务、记忆服务、资源服务、AI服务
- 通信方式: HTTP API、消息队列、事件驱动
- 数据一致性: 分布式事务、最终一致性

**技术实现**:
```python
# 设备服务
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from .models import Device, DeviceCommand
from .mqtt_client import MQTTClient
from .database import get_db

app = FastAPI()

@app.post("/devices/{device_id}/commands")
async def send_device_command(
    device_id: str,
    command: DeviceCommand,
    db: Session = Depends(get_db)
):
    # 验证设备存在
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # 发送MQTT命令
    await mqtt_client.publish_command(device_id, command)
    
    # 记录命令历史
    command_record = DeviceCommandRecord(
        device_id=device_id,
        command=command.dict(),
        timestamp=datetime.utcnow()
    )
    db.add(command_record)
    db.commit()
    
    return {"status": "success", "command_id": command.id}
```

## 4. 数据流架构

### 4.1 设备数据流
```
ESP32设备 → MQTT Broker → 设备交互服务 → WebSocket → 前端界面
                ↓
            Redis缓存 → PostgreSQL → 历史数据查询
```

### 4.2 图像数据流
```
ESP32摄像头 → TCP流 → 图像处理服务 → 格式转换 → 前端显示
                ↓
            MinIO存储 → 图像检索 → 记忆管理
```

### 4.3 AI聊天数据流
```
用户输入 → 前端界面 → AI聊天服务 → 意图识别 → 服务路由
                ↓
        设备控制 ← 记忆查询 ← 资源匹配 ← 响应生成
```

## 5. 部署架构

### 5.1 Demo阶段部署
```yaml
# docker-compose.yml
version: '3.8'
services:
  deepweb:
    build: .
    ports:
      - "8501:8501"
    environment:
      - MQTT_BROKER=mqtt://broker:1883
      - DATABASE_URL=postgresql://user:pass@db:5432/deepweb
    depends_on:
      - postgres
      - redis
      - mqtt

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: deepweb
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  mqtt:
    image: eclipse-mosquitto:2
    ports:
      - "1883:1883"
      - "9001:9001"
```

### 5.2 产品化阶段部署
```yaml
# kubernetes部署配置
apiVersion: apps/v1
kind: Deployment
metadata:
  name: deepweb-frontend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: deepweb-frontend
  template:
    metadata:
      labels:
        app: deepweb-frontend
    spec:
      containers:
      - name: frontend
        image: deepweb/frontend:latest
        ports:
        - containerPort: 80
        env:
        - name: API_BASE_URL
          value: "https://api.deepweb.com"
---
apiVersion: v1
kind: Service
metadata:
  name: deepweb-frontend-service
spec:
  selector:
    app: deepweb-frontend
  ports:
  - port: 80
    targetPort: 80
  type: LoadBalancer
```

## 6. 性能优化策略

### 6.1 前端优化
- **代码分割**: 按路由和功能模块分割
- **懒加载**: 组件和资源按需加载
- **缓存策略**: 静态资源CDN缓存
- **虚拟滚动**: 大数据列表性能优化

### 6.2 后端优化
- **数据库优化**: 索引优化、查询优化
- **缓存策略**: Redis多级缓存
- **异步处理**: 非阻塞IO操作
- **连接池**: 数据库和MQTT连接池

### 6.3 系统优化
- **负载均衡**: Nginx负载均衡
- **水平扩展**: 微服务水平扩展
- **监控告警**: 性能监控和自动告警
- **容灾备份**: 数据备份和故障恢复

## 7. 安全架构

### 7.1 认证授权
- **JWT Token**: 无状态认证
- **RBAC**: 基于角色的访问控制
- **OAuth 2.0**: 第三方登录集成

### 7.2 数据安全
- **传输加密**: HTTPS/TLS加密
- **存储加密**: 敏感数据加密存储
- **访问控制**: API访问权限控制

### 7.3 设备安全
- **设备认证**: MQTT设备身份验证
- **消息加密**: MQTT消息加密传输
- **访问控制**: 设备操作权限控制

## 8. 监控和运维

### 8.1 监控体系
- **应用监控**: APM性能监控
- **基础设施监控**: 服务器资源监控
- **业务监控**: 关键业务指标监控

### 8.2 日志管理
- **集中日志**: ELK日志收集分析
- **日志分级**: 不同级别日志处理
- **日志审计**: 操作日志审计追踪

### 8.3 运维自动化
- **CI/CD**: 自动化构建部署
- **健康检查**: 服务健康状态检查
- **自动扩缩容**: 基于负载自动扩缩容

## 9. 技术债务管理

### 9.1 代码质量
- **代码规范**: 统一的代码规范标准
- **代码审查**: 强制代码审查流程
- **单元测试**: 完善的单元测试覆盖

### 9.2 技术升级
- **依赖管理**: 定期更新依赖版本
- **技术栈升级**: 渐进式技术栈升级
- **性能优化**: 持续性能优化改进

## 10. 架构优化建议

### 10.1 基于DeepWin分析的优化建议

#### 10.1.1 核心逻辑层优化
**建议**: 引入DeepWin的核心逻辑层，实现代码复用
- **记忆管理**: 直接复用DeepWin的记忆管理逻辑
- **资源管理**: 复用资源需求管理和匹配算法
- **AI协调**: 复用智能体管理和任务调度逻辑
- **设备管理**: 适配设备逻辑管理器，支持MQTT通信

#### 10.1.2 服务层架构优化
**建议**: 采用微服务架构，提高系统可扩展性
- **记忆服务**: 独立的记忆管理微服务
- **资源服务**: 独立的资源管理微服务
- **AI服务**: 独立的AI协调微服务
- **设备服务**: 独立的设备管理微服务

#### 10.1.3 数据层优化
**建议**: 统一数据访问层，支持多种数据存储
- **关系数据库**: PostgreSQL存储结构化数据
- **向量数据库**: Qdrant存储向量化数据
- **图数据库**: Neo4j存储关系图谱
- **对象存储**: MinIO存储多媒体文件

### 10.2 技术债务管理

#### 10.2.1 代码复用策略
- **共享库**: 提取DeepWin核心逻辑为共享库
- **适配器模式**: 使用适配器模式处理不同通信协议
- **接口抽象**: 定义统一的业务接口，支持多种实现

#### 10.2.2 架构演进路径
1. **第一阶段**: Demo原型，验证核心功能
2. **第二阶段**: 引入DeepWin核心逻辑，实现代码复用
3. **第三阶段**: 微服务化改造，提高可扩展性
4. **第四阶段**: 智能化升级，集成更多AI功能

### 10.3 开发效率提升

#### 10.3.1 代码复用收益
- **开发时间**: 减少60%的核心逻辑开发时间
- **维护成本**: 统一维护，降低维护成本
- **质量保证**: 复用经过验证的代码，提高质量
- **功能一致性**: 保证桌面端和Web端功能一致性

#### 10.3.2 技术栈统一
- **后端语言**: 统一使用Python，便于团队协作
- **数据库**: 统一数据模型，便于数据同步
- **AI框架**: 统一AI框架，便于模型共享
- **部署方式**: 统一容器化部署，便于运维管理

## 11. 总结

基于对DeepWin架构的深入分析，DeepWeb架构需要进行以下关键优化：

### 11.1 架构调整要点

1. **引入核心逻辑层**: 复用DeepWin的核心业务逻辑
2. **采用微服务架构**: 提高系统的可扩展性和可维护性
3. **统一数据访问层**: 支持多种数据存储方式
4. **实现代码复用**: 通过共享库和适配器模式实现代码复用

### 11.2 技术优势

- **开发效率**: 通过代码复用大幅提升开发效率
- **功能一致性**: 保证桌面端和Web端功能的一致性
- **维护成本**: 统一维护核心逻辑，降低维护成本
- **技术债务**: 通过合理的架构设计减少技术债务

### 11.3 实施建议

1. **分阶段实施**: 按照Demo→核心逻辑集成→微服务化→智能化的顺序实施
2. **渐进式迁移**: 逐步将DeepWin的核心逻辑迁移到Web端
3. **持续优化**: 根据实际使用情况持续优化架构设计
4. **团队协作**: 建立跨平台的开发团队，确保架构的一致性

**关键成功因素**:
1. 充分利用DeepWin的成熟架构和代码
2. 采用微服务架构提高系统可扩展性
3. 实现代码复用，提高开发效率
4. 统一技术栈，便于团队协作
5. 持续优化架构，适应业务发展