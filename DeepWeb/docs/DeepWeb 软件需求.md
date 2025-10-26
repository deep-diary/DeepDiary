# DeepWeb 软件需求文档

## 文档信息
- **项目名称**: DeepWeb - 不倒翁桌面记忆管家Web端
- **版本**: v1.0
- **创建日期**: 2025-10-26
- **最后更新**: 2025-10-26
- **文档类型**: 软件需求规格说明书

## 1. 项目概述

### 1.1 项目背景
基于ESP32-S3开发的可控制倒向不倒翁产品，通过Web界面实现设备交互、记忆管理、资源管理和AI聊天等核心功能。项目旨在打造一个具有情感交互和个人记忆管理能力的可交互桌面智能硬件。

### 1.2 核心目标
- 提供直观的Web界面控制不倒翁设备
- 实现基于MQTT协议的实时设备状态监控
- 集成图像传输和AI聊天功能
- 构建完整的记忆管理和资源交互系统

## 2. 系统架构

### 2.1 整体架构
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

### 2.2 开发阶段技术栈

#### 2.2.1 Demo阶段技术栈
- **前端**: Streamlit (Python)
- **后端**: FastAPI (Python)
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **消息队列**: Redis + MQTT
- **图像处理**: OpenCV + Pillow
- **AI集成**: OpenAI API / 本地模型

#### 2.2.2 产品化阶段技术栈
- **前端**: Vue 3 + TypeScript + Element Plus
- **后端**: FastAPI + Python 3.11+
- **API网关**: Nginx
- **数据库**: PostgreSQL + Redis
- **消息队列**: RabbitMQ + MQTT Broker
- **文件存储**: MinIO / AWS S3
- **容器化**: Docker + Docker Compose

### 2.3 通信协议
- **设备通信**: MQTT 3.1.1 + WebSocket
- **图像传输**: TCP + JPEG
- **API通信**: RESTful API + GraphQL
- **实时通信**: WebSocket + Server-Sent Events

## 3. 设备交互模块详细需求

### 3.1 MQTT协议集成

#### 3.1.1 连接管理
**功能描述**: 建立和维护与ESP32设备的MQTT连接

**技术要求**:
- 支持MQTT 3.1.1协议
- 支持TLS加密连接
- 实现自动重连机制
- 支持多设备同时连接

**实现细节**:
```javascript
// MQTT连接配置
const mqttConfig = {
  broker: 'mqtt://broker.example.com:1883',
  options: {
    clientId: 'deepweb-client-' + Date.now(),
    username: 'deepweb_user',
    password: 'secure_password',
    keepalive: 60,
    clean: true,
    reconnectPeriod: 5000,
    connectTimeout: 30 * 1000
  }
};
```

#### 3.1.2 设备状态监控

**功能描述**: 实时监控设备状态信息

**订阅主题**:
- `deepcontroller/{device_id}/status` - 设备状态 (30秒间隔)
- `deepcontroller/{device_id}/sensor` - 传感器数据 (10秒间隔)
- `deepcontroller/{device_id}/motor` - 电机状态 (5秒间隔)
- `deepcontroller/{device_id}/arm` - 机械臂状态 (5秒间隔)
- `deepcontroller/{device_id}/camera` - 摄像头状态 (30秒间隔)
- `deepcontroller/{device_id}/system` - 系统信息 (60秒间隔)
- `deepcontroller/{device_id}/alarm` - 告警信息 (实时)

**数据展示要求**:
- 实时状态面板显示设备连接状态
- 传感器数据可视化图表
- 电机和机械臂状态监控
- 系统资源使用情况监控
- 告警信息实时提醒

**界面组件**:
```typescript
interface DeviceStatusPanel {
  deviceId: string;
  connectionStatus: 'connected' | 'disconnected' | 'error';
  lastUpdateTime: Date;
  components: {
    camera: ComponentStatus;
    canBus: ComponentStatus;
    ledStrip: ComponentStatus;
    gimbal: ComponentStatus;
    sensor: ComponentStatus;
  };
  systemInfo: {
    freeHeap: number;
    uptime: number;
    temperature: number;
  };
}
```

#### 3.1.3 设备控制命令

**功能描述**: 向设备发送控制指令

**发布主题**: `deepcontroller/{device_id}/command`

**支持的控制类型**:
1. **电机控制**
   - 启动/停止电机
   - 设置电机位置
   - 设置电机速度
   - 设置电机扭矩

2. **机械臂控制**
   - 关节角度控制
   - 末端执行器位置控制
   - 运动轨迹规划

3. **摄像头控制**
   - 开始/停止视频流
   - 调整分辨率和质量
   - 拍照功能

4. **LED控制**
   - 颜色设置
   - 亮度调节
   - 动画效果

**命令格式**:
```json
{
  "command_id": "cmd_001",
  "timestamp": 1706284800,
  "command_type": "motor_control",
  "target": "motor",
  "action": "set_position",
  "parameters": {
    "motor_id": 1,
    "position": 90.0,
    "speed": 50.0,
    "duration": 5000
  },
  "priority": "normal",
  "timeout": 10000
}
```

#### 3.1.4 配置管理

**功能描述**: 管理设备配置参数

**发布主题**: `deepcontroller/{device_id}/config`

**配置类型**:
- 传感器配置 (采样率、量程、带宽)
- 电机配置 (最大速度、最大扭矩、加速度)
- 摄像头配置 (分辨率、质量、帧率)
- 系统配置 (WiFi、MQTT连接参数)

### 3.2 TCP图像传输模块

#### 3.2.1 图像流管理

**功能描述**: 通过TCP协议获取设备图像数据

**技术要求**:
- 支持JPEG格式图像传输
- 实现图像流缓冲和显示
- 支持分辨率动态调整
- 实现图像质量设置

**实现方案**:
```typescript
interface ImageStreamManager {
  connect(deviceIp: string, port: number): Promise<void>;
  startStream(): void;
  stopStream(): void;
  setResolution(width: number, height: number): void;
  setQuality(quality: number): void;
  onImageReceived(callback: (imageData: ArrayBuffer) => void): void;
}
```

#### 3.2.2 图像显示组件

**功能描述**: 在Web界面中显示实时图像

**技术要求**:
- 支持Canvas或Video元素显示
- 实现图像缩放和旋转
- 支持全屏显示
- 实现图像录制功能

**界面要求**:
- 实时图像显示区域
- 图像控制面板 (开始/停止/拍照/录制)
- 图像参数调节 (分辨率、质量、帧率)
- 图像历史记录查看

### 3.3 设备管理界面

#### 3.3.1 设备列表管理

**功能描述**: 管理多个设备的连接和状态

**功能要求**:
- 设备列表显示
- 设备连接状态监控
- 设备添加/删除功能
- 设备分组管理

**界面组件**:
```typescript
interface DeviceList {
  devices: DeviceInfo[];
  addDevice(deviceInfo: DeviceInfo): void;
  removeDevice(deviceId: string): void;
  updateDeviceStatus(deviceId: string, status: DeviceStatus): void;
  getDeviceById(deviceId: string): DeviceInfo | null;
}

interface DeviceInfo {
  id: string;
  name: string;
  type: 'ATK-DNESP32S3';
  ipAddress: string;
  mqttTopic: string;
  status: 'online' | 'offline' | 'error';
  lastSeen: Date;
  capabilities: string[];
}
```

#### 3.3.2 控制面板

**功能描述**: 提供直观的设备控制界面

**控制组件**:
1. **电机控制面板**
   - 6个电机的独立控制
   - 位置、速度、扭矩调节
   - 预设动作按钮
   - 实时状态显示

2. **机械臂控制面板**
   - 关节角度调节滑块
   - 末端执行器位置控制
   - 运动轨迹可视化
   - 安全限制设置

3. **摄像头控制面板**
   - 实时图像显示
   - 图像参数调节
   - 拍照和录制功能
   - 图像历史管理

4. **系统监控面板**
   - 系统资源使用情况
   - 网络连接状态
   - 错误日志显示
   - 性能指标监控

### 3.4 实时数据可视化

#### 3.4.1 传感器数据图表

**功能描述**: 实时显示传感器数据

**图表类型**:
- 加速度三轴数据折线图
- 姿态角度实时显示
- 温度变化趋势图
- 自定义数据图表

**技术要求**:
- 使用Chart.js或D3.js实现
- 支持数据缩放和时间范围选择
- 实现数据导出功能
- 支持多设备数据对比

#### 3.4.2 设备状态指示器

**功能描述**: 直观显示设备各组件状态

**指示器类型**:
- 连接状态指示灯
- 组件可用性指示
- 错误状态警告
- 性能指标仪表盘

## 4. 记忆交互模块详细需求

### 4.1 Immich API集成

#### 4.1.1 照片管理功能
**功能描述**: 与Immich服务器集成，实现照片的获取、管理和展示

**技术要求**:
- 支持Immich REST API v1.0+
- 实现OAuth 2.0认证
- 支持照片元数据提取
- 提供照片搜索和过滤功能

**实现细节**:
```typescript
interface ImmichPhoto {
  id: string;
  filename: string;
  fileSize: number;
  createdAt: string;
  updatedAt: string;
  exifInfo: {
    make: string;
    model: string;
    dateTime: string;
    gpsLatitude?: number;
    gpsLongitude?: number;
  };
  people: Person[];
  tags: string[];
  thumbnailUrl: string;
  previewUrl: string;
}

interface Person {
  id: string;
  name: string;
  birthDate?: string;
  thumbnailPath: string;
}
```

#### 4.1.2 人脸识别集成
**功能描述**: 基于设备获取的人脸信息，从Immich获取相关人物照片

**技术要求**:
- 集成Immich人脸识别API
- 支持人脸特征匹配
- 实现人脸数据缓存
- 提供人脸搜索结果展示

**实现方案**:
```python
class FaceRecognitionService:
    def __init__(self, immich_client):
        self.immich_client = immich_client
        self.face_cache = {}
    
    async def find_photos_by_face(self, face_data: bytes) -> List[ImmichPhoto]:
        # 提取人脸特征
        face_features = await self.extract_face_features(face_data)
        
        # 在Immich中搜索匹配的人脸
        search_results = await self.immich_client.search_faces(face_features)
        
        # 获取相关照片
        photos = []
        for person_id in search_results:
            person_photos = await self.immich_client.get_person_photos(person_id)
            photos.extend(person_photos)
        
        return photos
```

### 4.2 Django后端集成

#### 4.2.1 用户数据API
**功能描述**: 与Django后端集成，获取用户相关数据

**API接口**:
- `GET /api/users/{user_id}/profile` - 获取用户基本信息
- `GET /api/users/{user_id}/preferences` - 获取用户偏好设置
- `PUT /api/users/{user_id}/preferences` - 更新用户偏好设置

**数据模型**:
```typescript
interface UserProfile {
  id: string;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  avatar?: string;
  createdAt: string;
  lastLoginAt: string;
}

interface UserPreferences {
  theme: 'light' | 'dark';
  language: string;
  timezone: string;
  notifications: {
    email: boolean;
    push: boolean;
    device: boolean;
  };
  privacy: {
    shareLocation: boolean;
    sharePhotos: boolean;
    shareResources: boolean;
  };
}
```

#### 4.2.2 聊天记录API
**功能描述**: 获取和管理用户的AI聊天记录

**API接口**:
- `GET /api/chat/sessions` - 获取聊天会话列表
- `GET /api/chat/sessions/{session_id}/messages` - 获取会话消息
- `POST /api/chat/sessions` - 创建新会话
- `POST /api/chat/sessions/{session_id}/messages` - 发送消息

**数据模型**:
```typescript
interface ChatSession {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  messageCount: number;
  lastMessage?: ChatMessage;
}

interface ChatMessage {
  id: string;
  sessionId: string;
  role: 'user' | 'assistant';
  content: string;
  contentType: 'text' | 'image' | 'file';
  timestamp: string;
  metadata?: Record<string, any>;
}
```

#### 4.2.3 日记管理API
**功能描述**: 管理用户的个人日记

**API接口**:
- `GET /api/diaries` - 获取日记列表
- `GET /api/diaries/{diary_id}` - 获取日记详情
- `POST /api/diaries` - 创建新日记
- `PUT /api/diaries/{diary_id}` - 更新日记
- `DELETE /api/diaries/{diary_id}` - 删除日记

**数据模型**:
```typescript
interface Diary {
  id: string;
  title: string;
  content: string;
  mood?: 'happy' | 'sad' | 'neutral' | 'excited' | 'tired';
  tags: string[];
  createdAt: string;
  updatedAt: string;
  isPrivate: boolean;
  attachments?: Attachment[];
}

interface Attachment {
  id: string;
  type: 'image' | 'audio' | 'video' | 'file';
  filename: string;
  url: string;
  size: number;
}
```

### 4.3 记忆融合服务

#### 4.3.1 多源数据整合
**功能描述**: 整合来自不同源的数据，形成统一的记忆库

**技术要求**:
- 实现数据标准化和去重
- 支持时间线排序
- 提供数据关联分析
- 实现智能推荐算法

**实现方案**:
```python
class MemoryFusionService:
    def __init__(self):
        self.immich_client = ImmichClient()
        self.django_client = DjangoClient()
        self.vector_store = VectorStore()
    
    async def fuse_memories(self, user_id: str, time_range: TimeRange) -> List[Memory]:
        # 获取多源数据
        photos = await self.immich_client.get_photos(user_id, time_range)
        diaries = await self.django_client.get_diaries(user_id, time_range)
        chats = await self.django_client.get_chats(user_id, time_range)
        
        # 数据融合和去重
        memories = await self.merge_data(photos, diaries, chats)
        
        # 时间线排序
        memories.sort(key=lambda x: x.timestamp)
        
        # 关联分析
        memories = await self.analyze_relationships(memories)
        
        return memories
```

## 5. 资源交互模块详细需求

### 5.1 资源管理功能

#### 5.1.1 资源录入和管理
**功能描述**: 管理用户及朋友的三大资源和三大需求

**技术要求**:
- 支持资源分类和标签管理
- 实现资源搜索和过滤
- 提供资源关系维护
- 支持批量导入和导出

**数据模型**:
```typescript
interface Resource {
  id: string;
  userId: string;
  type: 'skill' | 'item' | 'time' | 'knowledge' | 'connection';
  category: string;
  title: string;
  description: string;
  tags: string[];
  availability: 'available' | 'busy' | 'unavailable';
  location?: {
    city: string;
    country: string;
    coordinates?: [number, number];
  };
  contactInfo: {
    phone?: string;
    email?: string;
    wechat?: string;
  };
  createdAt: string;
  updatedAt: string;
}

interface Need {
  id: string;
  userId: string;
  type: 'skill' | 'item' | 'time' | 'knowledge' | 'connection';
  category: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  deadline?: string;
  budget?: number;
  location?: {
    city: string;
    country: string;
    coordinates?: [number, number];
  };
  status: 'open' | 'in_progress' | 'completed' | 'cancelled';
  createdAt: string;
  updatedAt: string;
}
```

#### 5.1.2 关系图谱构建
**功能描述**: 构建用户、资源和需求之间的关系图谱

**技术要求**:
- 使用图数据库存储关系数据
- 实现关系查询和遍历
- 支持关系可视化展示
- 提供关系分析功能

**实现方案**:
```python
class RelationshipGraph:
    def __init__(self, graph_db):
        self.db = graph_db
    
    async def add_relationship(self, from_node: str, to_node: str, 
                             relationship_type: str, properties: dict = None):
        query = """
        MATCH (a {id: $from_node})
        MATCH (b {id: $to_node})
        CREATE (a)-[r:{relationship_type} $properties]->(b)
        RETURN r
        """
        return await self.db.execute(query, {
            'from_node': from_node,
            'to_node': to_node,
            'relationship_type': relationship_type,
            'properties': properties or {}
        })
    
    async def find_matches(self, need_id: str) -> List[Match]:
        query = """
        MATCH (n:Need {id: $need_id})
        MATCH (r:Resource)
        WHERE r.type = n.type AND r.availability = 'available'
        WITH n, r, 
             gds.similarity.cosine(r.embedding, n.embedding) as similarity
        WHERE similarity > 0.7
        RETURN r, similarity
        ORDER BY similarity DESC
        """
        results = await self.db.execute(query, {'need_id': need_id})
        return [Match(resource=r, similarity=s) for r, s in results]
```

### 5.2 智能匹配功能

#### 5.2.1 向量化匹配
**功能描述**: 基于向量相似度实现资源和需求的智能匹配

**技术要求**:
- 使用预训练模型进行文本向量化
- 实现余弦相似度计算
- 支持多维度匹配评分
- 提供匹配结果排序

**实现方案**:
```python
class VectorMatchingService:
    def __init__(self, embedding_model):
        self.model = embedding_model
        self.vector_store = VectorStore()
    
    async def create_embedding(self, text: str) -> np.ndarray:
        return await self.model.encode(text)
    
    async def find_matches(self, need: Need, top_k: int = 10) -> List[Match]:
        # 获取需求向量
        need_vector = await self.create_embedding(need.description)
        
        # 搜索相似资源
        similar_resources = await self.vector_store.search(
            vector=need_vector,
            filter={'type': need.type, 'availability': 'available'},
            top_k=top_k
        )
        
        # 计算匹配分数
        matches = []
        for resource, similarity in similar_resources:
            score = self.calculate_match_score(need, resource, similarity)
            matches.append(Match(resource=resource, score=score, similarity=similarity))
        
        # 按分数排序
        matches.sort(key=lambda x: x.score, reverse=True)
        return matches
```

#### 5.2.2 匹配结果展示
**功能描述**: 在Web界面中展示匹配结果

**界面要求**:
- 清晰的匹配结果列表
- 匹配分数和相似度显示
- 资源详情和联系方式
- 一键联系和收藏功能

**组件设计**:
```vue
<template>
  <div class="match-results">
    <div class="match-header">
      <h3>匹配结果 ({{ matches.length }})</h3>
      <div class="filters">
        <el-select v-model="selectedType" placeholder="资源类型">
          <el-option label="全部" value="all" />
          <el-option label="技能" value="skill" />
          <el-option label="物品" value="item" />
          <el-option label="时间" value="time" />
        </el-select>
      </div>
    </div>
    
    <div class="match-list">
      <el-card 
        v-for="match in filteredMatches" 
        :key="match.resource.id"
        class="match-card"
      >
        <div class="match-score">
          <el-progress 
            :percentage="match.score * 100" 
            :color="getScoreColor(match.score)"
          />
          <span class="score-text">{{ (match.score * 100).toFixed(1) }}%</span>
        </div>
        
        <div class="resource-info">
          <h4>{{ match.resource.title }}</h4>
          <p>{{ match.resource.description }}</p>
          <div class="resource-meta">
            <el-tag :type="getTypeColor(match.resource.type)">
              {{ getTypeLabel(match.resource.type) }}
            </el-tag>
            <el-tag v-if="match.resource.location">
              {{ match.resource.location.city }}
            </el-tag>
          </div>
        </div>
        
        <div class="match-actions">
          <el-button type="primary" @click="contactResource(match.resource)">
            联系
          </el-button>
          <el-button @click="saveMatch(match)">
            收藏
          </el-button>
        </div>
      </el-card>
    </div>
  </div>
</template>
```

## 6. AI聊天统一入口模块详细需求

### 6.1 多模态交互功能

#### 6.1.1 语音交互
**功能描述**: 支持语音输入和语音合成输出

**技术要求**:
- 集成Web Speech API
- 支持语音识别和合成
- 实现语音命令处理
- 提供语音反馈功能

**实现方案**:
```typescript
class VoiceInteractionService {
  private recognition: SpeechRecognition;
  private synthesis: SpeechSynthesis;
  
  constructor() {
    this.recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    this.synthesis = window.speechSynthesis;
    this.setupRecognition();
  }
  
  private setupRecognition() {
    this.recognition.continuous = false;
    this.recognition.interimResults = false;
    this.recognition.lang = 'zh-CN';
    
    this.recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      this.handleVoiceInput(transcript);
    };
  }
  
  startListening() {
    this.recognition.start();
  }
  
  speak(text: string) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'zh-CN';
    this.synthesis.speak(utterance);
  }
  
  private async handleVoiceInput(transcript: string) {
    // 处理语音输入
    const response = await this.processVoiceCommand(transcript);
    this.speak(response);
  }
}
```

#### 6.1.2 图像识别
**功能描述**: 支持图片上传和内容识别

**技术要求**:
- 集成图像识别API
- 支持多种图像格式
- 实现图像内容分析
- 提供图像描述生成

**实现方案**:
```python
class ImageRecognitionService:
    def __init__(self, vision_api):
        self.api = vision_api
    
    async def analyze_image(self, image_data: bytes) -> ImageAnalysis:
        # 图像内容识别
        objects = await self.api.detect_objects(image_data)
        faces = await self.api.detect_faces(image_data)
        text = await self.api.extract_text(image_data)
        
        # 生成图像描述
        description = await self.api.generate_description(image_data)
        
        return ImageAnalysis(
            objects=objects,
            faces=faces,
            text=text,
            description=description
        )
    
    async def process_image_command(self, image_data: bytes, command: str) -> str:
        analysis = await self.analyze_image(image_data)
        
        # 根据命令处理图像
        if "找照片" in command:
            return await self.find_similar_photos(analysis)
        elif "识别物体" in command:
            return self.describe_objects(analysis.objects)
        elif "识别人脸" in command:
            return await self.identify_faces(analysis.faces)
        
        return "我无法理解这个图像命令"
```

### 6.2 意图识别与路由

#### 6.2.1 自然语言理解
**功能描述**: 识别用户意图并路由到相应的功能模块

**技术要求**:
- 使用预训练NLP模型
- 实现意图分类和实体提取
- 支持上下文理解
- 提供意图置信度评分

**实现方案**:
```python
class IntentRecognitionService:
    def __init__(self, nlp_model):
        self.model = nlp_model
        self.intent_patterns = {
            'device_control': [
                '控制设备', '打开电机', '调整摄像头', '设置LED'
            ],
            'memory_query': [
                '查找照片', '回忆过去', '查看日记', '搜索记忆'
            ],
            'resource_match': [
                '找资源', '匹配需求', '寻找帮助', '推荐朋友'
            ],
            'general_chat': [
                '你好', '聊天', '对话', '交流'
            ]
        }
    
    async def recognize_intent(self, text: str, context: dict = None) -> Intent:
        # 文本预处理
        processed_text = self.preprocess_text(text)
        
        # 意图分类
        intent_scores = await self.model.classify_intent(processed_text)
        
        # 实体提取
        entities = await self.model.extract_entities(processed_text)
        
        # 上下文分析
        if context:
            intent_scores = self.apply_context(intent_scores, context)
        
        # 选择最佳意图
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        
        return Intent(
            type=best_intent[0],
            confidence=best_intent[1],
            entities=entities,
            text=text
        )
```

#### 6.2.2 服务路由
**功能描述**: 根据识别的意图路由到相应的服务

**实现方案**:
```python
class ServiceRouter:
    def __init__(self):
        self.services = {
            'device_control': DeviceControlService(),
            'memory_query': MemoryQueryService(),
            'resource_match': ResourceMatchService(),
            'general_chat': GeneralChatService()
        }
    
    async def route_request(self, intent: Intent) -> str:
        service = self.services.get(intent.type)
        if not service:
            return "抱歉，我无法理解您的请求"
        
        try:
            response = await service.process(intent)
            return response
        except Exception as e:
            return f"处理请求时发生错误: {str(e)}"
```

## 7. 非功能性需求

### 7.1 性能要求
- 页面加载时间 < 3秒
- 设备状态更新延迟 < 1秒
- 图像传输延迟 < 500ms
- 支持100个并发设备连接
- AI响应时间 < 2秒

### 7.2 可靠性要求
- 系统可用性 > 99.5%
- 自动重连机制
- 数据备份和恢复
- 错误处理和日志记录
- 服务降级和容错

### 7.3 安全性要求
- MQTT连接加密
- 用户身份认证
- 设备访问控制
- 数据传输安全
- 隐私数据保护

### 7.4 兼容性要求
- 支持主流浏览器 (Chrome, Firefox, Safari, Edge)
- 响应式设计，支持移动端访问
- 支持不同分辨率的设备
- 支持多种数据格式

## 5. 开发计划

### 5.1 第一阶段 (4周)
- MQTT连接和基础通信
- 设备状态监控界面
- 基础控制命令发送

### 5.2 第二阶段 (3周)
- TCP图像传输功能
- 图像显示和控制界面
- 设备管理功能

### 5.3 第三阶段 (3周)
- 数据可视化图表
- 高级控制功能
- 错误处理和优化

### 5.4 第四阶段 (2周)
- 性能优化
- 安全加固
- 测试和部署

## 6. 验收标准

### 6.1 功能验收
- [ ] 能够成功连接ESP32设备
- [ ] 实时显示设备状态信息
- [ ] 成功发送控制命令并收到响应
- [ ] 正常显示设备图像流
- [ ] 所有控制功能正常工作

### 6.2 性能验收
- [ ] 页面加载时间符合要求
- [ ] 设备响应时间符合要求
- [ ] 图像传输质量符合要求
- [ ] 系统稳定性符合要求

### 6.3 用户体验验收
- [ ] 界面直观易用
- [ ] 操作响应及时
- [ ] 错误提示清晰
- [ ] 帮助文档完整

---

**文档状态**: 草稿
**下一步**: 技术架构设计和详细设计文档
