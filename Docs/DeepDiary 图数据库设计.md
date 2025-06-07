# DeepDiary 图数据库设计

## 修订记录

| 版本信息 | 更新日志         | 日期     | 备注 |
| -------- | ---------------- | -------- | ---- |
| V1.0     | 图数据库设计草稿 | 2025.6.5 |      |
|          |                  |          |      |

## 1. 引言

### 1.1 编写目的

本文档旨在详细描述 DeepDiary 项目的图数据库设计方案，包括图数据库的选择、实体（节点）定义、关系（边）定义、模式设计及查询示例。本设计将充分利用图数据库在处理复杂关系和多跳查询方面的优势，为 DeepDiary 的社交网络分析、资源匹配、记忆追溯和多模态数据关联提供强大的数据支持，从而帮助开发人员快速理解并实现相关功能。

### 1.2 目标读者

本文档的目标读者包括：

- 系统架构师
- 软件开发工程师（特别是后端和数据工程师）
- 测试工程师
- 数据分析师

### 1.3 术语和缩写

- **图数据库 (Graph Database)**：一种使用图结构（节点、边和属性）进行数据存储和查询的数据库。
- **节点 (Node)**：图中的基本单元，代表实体。
- **关系 (Relationship)**：图中的基本单元，代表节点之间的联系。
- **属性 (Property)**：附加在节点或关系上的键值对，用于描述其特征。
- **Cypher**：Neo4j 的声明式图查询语言。
- **Neo4j**：一种流行的原生图数据库。
- **DeepDiary**：个人记忆与资源管理平台。
- **DeepServer**：DeepDiary 项目的云端服务器。
- **RAG**：检索增强生成（Retrieval Augmented Generation）。

## 2. 为什么需要图数据库

DeepDiary 项目的核心功能之一是管理用户及其记忆、资源和需求之间的复杂关联，并支持高效的社交网络分析和智能匹配。传统的关系型数据库在处理这些高度关联的数据时，通常需要复杂的 JOIN 操作，导致查询效率低下和数据模型僵化。图数据库则能以更自然、直观的方式表示这些关系，并提供以下优势：

- **社交网络分析：** 能够高效地查找用户的朋友的朋友，或者发现具有共同兴趣或共享资源的用户群体。例如，快速找出“谁认识拥有Python上位机开发技能的人”。
- **资源匹配：** 通过用户与资源、需求、技能、地点等实体之间的多维关系，实现更精准的资源和需求匹配。例如，找到“在深圳、从事IT行业、需要大模型开发人才”的用户。
- **记忆追溯：** 将记忆与人物、地点、事件、情绪、相关的照片/视频等实体关联起来，实现上下文感知的记忆检索。例如，查询“小明去年在北京拍的所有关于猫的照片”。
- **知识图谱构建：** 为 DeepDiary 平台构建一个活态的知识图谱，实现更智能的数据关联和推理能力，支持 AI 助手的深度理解和问答。
- **性能优势：** 在处理多跳关系查询时，图数据库的性能通常远超关系型数据库，因为它们无需进行复杂的 JOIN 操作，而是直接通过图遍历完成。

## 3. 图数据库选择

根据 DeepDiary 项目的需求和技术栈，我们选择 **Neo4j** 作为图数据库。

### 3.1 Neo4j 优势

- **高性能：** Neo4j 采用原生的图存储和处理引擎，能够实现快速的图遍历和复杂查询，尤其适用于大规模关联数据的处理。
- **灵活的数据模型：** 基于属性图模型，可以灵活地定义节点、关系及其属性，支持敏捷开发和需求变化。
- **丰富的查询语言：** 提供了强大的 Cypher 查询语言，语法直观，易于学习和使用，能够表达复杂的图模式匹配和路径查找。
- **成熟的生态系统：** 拥有活跃的社区、丰富的驱动程序（包括 Python 驱动）、可视化工具（Neo4j Browser, Bloom）和集成方案，便于开发和运维。
- **事务支持：** 提供 ACID 事务特性，确保数据的一致性和可靠性。
- **可扩展性：** 支持集群部署，满足未来数据增长和高可用性需求。

## 4. 图数据库设计

### 4.1 实体（节点）设计

我们将 DeepDiary 项目中的关键实体映射为图数据库中的节点。每个节点都有一个或多个标签 (Label) 和一组属性 (Properties)。

#### 4.1.1 用户 (User)

- **标签**: `User`
- **属性**:
  - `user_id`: 唯一用户ID (与关系型数据库关联) - `BIGINT`
  - `username`: 用户名 - `STRING`
  - `email`: 邮箱 - `STRING`
  - `phone`: 电话 - `STRING`
  - `city`: 所在城市 - `STRING`
  - `industry`: 所在行业 - `STRING`
  - `position`: 岗位 - `STRING`
  - `created_at`: 创建时间 - `DATETIME`
  - `updated_at`: 更新时间 - `DATETIME`
  - `avatar_url`: 用户头像URL - `STRING`

#### 4.1.2 记忆 (Memory)

- **标签**: `Memory`
- **属性**:
  - `memory_id`: 唯一记忆ID (与关系型数据库关联) - `BIGINT`
  - `title`: 记忆标题 - `STRING`
  - `summary`: 记忆内容摘要 - `STRING`
  - `type`: 记忆类型 (e.g., `Photo`, `Video`, `Diary`, `ChatRecord`, `GPS_Track`) - `STRING`
  - `created_at`: 记忆创建/发生时间 - `DATETIME`
  - `location_text`: 记忆发生地点文字描述 - `STRING`
  - `vector_id_ref`: 向量数据库中对应记忆内容的向量ID (用于语义搜索) - `STRING`

#### 4.1.3 资源 (Resource)

- **标签**: `Resource`
- **属性**:
  - `resource_id`: 唯一资源ID (与关系型数据库关联) - `BIGINT`
  - `name`: 资源名称/技能名称 - `STRING`
  - `description`: 资源详细描述 - `STRING`
  - `type`: 资源类型 (e.g., `Skill`, `Item`, `Time`, `Service`) - `STRING`
  - `price`: 是否需要付费匹配的费用 (可选) - `FLOAT`
  - `created_at`: 创建时间 - `DATETIME`
  - `updated_at`: 更新时间 - `DATETIME`
  - `vector_id_ref`: 向量数据库中对应资源描述的向量ID - `STRING`

#### 4.1.4 需求 (Demand)

- **标签**: `Demand`
- **属性**:
  - `demand_id`: 唯一需求ID (与关系型数据库关联) - `BIGINT`
  - `name`: 需求名称 - `STRING`
  - `description`: 需求详细描述 - `STRING`
  - `type`: 需求类型 (e.g., `Learning`, `Help`, `Collaboration`, `ProblemSolving`) - `STRING`
  - `budget`: 愿意支付的预算 (可选) - `FLOAT`
  - `created_at`: 创建时间 - `DATETIME`
  - `updated_at`: 更新时间 - `DATETIME`
  - `urgency`: 紧急程度 (e.g., `Low`, `Medium`, `High`) - `STRING`
  - `vector_id_ref`: 向量数据库中对应需求描述的向量ID - `STRING`

#### 4.1.5 地点 (Location)

- **标签**: `Location`
- **属性**:
  - `location_id`: 唯一地点ID (可为地名哈希或外部ID) - `STRING`
  - `name`: 地点名称 - `STRING`
  - `latitude`: 纬度 - `FLOAT`
  - `longitude`: 经度 - `FLOAT`
  - `address_detail`: 详细地址 - `STRING`
  - `type`: 地点类型 (e.g., `City`, `Building`, `ScenicSpot`) - `STRING`

#### 4.1.6 组织机构 (Organization)

- **标签**: `Organization`
- **属性**:
  - `org_id`: 唯一组织机构ID (与关系型数据库关联) - `BIGINT`
  - `name`: 组织机构名称 - `STRING`
  - `type`: 组织类型 (e.g., `Company`, `School`, `Team`, `Community`) - `STRING`
  - `industry`: 所属行业 - `STRING`
  - `location`: 组织机构所在地 - `STRING`
  - `description`: 描述 - `STRING`

#### 4.1.7 人脸 (Face)

- **标签**: `Face`
- **属性**:
  - `face_id`: 唯一人脸ID (与关系型数据库关联) - `BIGINT`
  - `name`: 识别出的人脸名称 (e.g., "张三", "未知人物") - `STRING`
  - `recognition_model_version`: 识别人脸所使用的模型版本 - `STRING`
  - `vector_id_ref`: 向量数据库中对应人脸特征的向量ID - `STRING`
  - `is_identified`: 是否已被人脸识别并命名 - `BOOLEAN`

#### 4.1.8 照片 (Photo)

- **标签**: `Photo` (同时也可作为 `Memory` 类型的一种)
- **属性**:
  - `photo_id`: 唯一照片ID (与关系型数据库关联) - `BIGINT`
  - `file_path`: 存储路径 (本地或云端) - `STRING`
  - `thumbnail_path`: 缩略图路径 - `STRING`
  - `upload_time`: 上传时间 - `DATETIME`
  - `description`: 照片描述 - `STRING`
  - `resolution`: 分辨率 (e.g., "1920x1080") - `STRING`
  - `exif_data_summary`: EXIF 数据摘要 (e.g., 相机型号, 快门速度) - `STRING`
  - `is_private`: 是否为私有照片 - `BOOLEAN`
  - `vector_id_ref`: 向量数据库中对应照片语义特征的向量ID - `STRING`

#### 4.1.9 视频 (Video)

- **标签**: `Video` (同时也可作为 `Memory` 类型的一种)
- **属性**:
  - `video_id`: 唯一视频ID (与关系型数据库关联) - `BIGINT`
  - `file_path`: 存储路径 (本地或云端) - `STRING`
  - `thumbnail_path`: 缩略图路径 - `STRING`
  - `upload_time`: 上传时间 - `DATETIME`
  - `description`: 视频描述 - `STRING`
  - `duration`: 视频时长 (秒) - `INTEGER`
  - `resolution`: 分辨率 - `STRING`
  - `is_private`: 是否为私有视频 - `BOOLEAN`
  - `vector_id_ref`: 向量数据库中对应视频语义特征的向量ID - `STRING`

#### 4.1.10 设备 (Device)

- **标签**: `Device`
- **属性**:
  - `device_id`: 唯一设备ID (与关系型数据库关联) - `BIGINT`
  - `name`: 设备名称 - `STRING`
  - `type`: 设备类型 (e.g., `DeepGlass`, `DeepArm`, `DeepToy`) - `STRING`
  - `serial_number`: 序列号 - `STRING`
  - `status`: 当前状态 (e.g., `Online`, `Offline`, `Error`) - `STRING`
  - `firmware_version`: 固件版本 - `STRING`
  - `last_active_time`: 最后活跃时间 - `DATETIME`

#### 4.1.11 日记 (Diary)

- **标签**: `Diary` (同时也可作为 `Memory` 类型的一种)
- **属性**:
  - `diary_id`: 唯一日记ID (与关系型数据库关联) - `BIGINT`
  - `title`: 日记标题 - `STRING`
  - `content`: 日记内容 - `STRING`
  - `created_at`: 记录时间 - `DATETIME`
  - `mood`: 心情标签 (e.g., `Happy`, `Sad`, `Neutral`) - `STRING`
  - `weather`: 当日天气 - `STRING`
  - `is_private`: 是否为私有日记 - `BOOLEAN`
  - `vector_id_ref`: 向量数据库中对应日记内容的向量ID - `STRING`

#### 4.1.12 轨迹 (Trajectory)

- **标签**: `Trajectory` (同时也可作为 `Memory` 类型的一种)
- **属性**:
  - `trajectory_id`: 唯一轨迹ID (与关系型数据库关联) - `BIGINT`
  - `name`: 轨迹名称 - `STRING`
  - `start_time`: 轨迹开始时间 - `DATETIME`
  - `end_time`: 轨迹结束时间 - `DATETIME`
  - `total_distance_km`: 总里程 (公里) - `FLOAT`
  - `vector_id_ref`: 向量数据库中对应轨迹摘要的向量ID - `STRING`

#### 4.1.13 工作经历 (WorkExperience)

- **标签**: `WorkExperience`
- **属性**:
  - `experience_id`: 唯一工作经历ID (与关系型数据库关联) - `BIGINT`
  - `title`: 职位名称 - `STRING`
  - `start_date`: 开始日期 - `DATE`
  - `end_date`: 结束日期 (可选) - `DATE`
  - `description`: 工作职责描述 - `STRING`
  - `industry`: 所属行业 - `STRING`
  - `role_type`: 角色类型 (e.g., `FullTime`, `PartTime`, `Intern`) - `STRING`

#### 4.1.14 公司 (Company)

- **标签**: `Company`
- **属性**:
  - `company_id`: 唯一公司ID (与关系型数据库关联) - `BIGINT`
  - `name`: 公司名称 - `STRING`
  - `industry`: 所属行业 - `STRING`
  - `location`: 公司所在地 - `STRING`
  - `description`: 公司简介 - `STRING`
  - `website`: 公司官网 (可选) - `STRING`

#### 4.1.15 产品 (Product)

- **标签**: `Product`
- **属性**:
  - `product_id`: 唯一产品ID (与关系型数据库关联) - `BIGINT`
  - `name`: 产品名称 - `STRING`
  - `description`: 产品描述 - `STRING`
  - `category`: 产品类别 (e.g., `Electronics`, `Software`, `Hardware`) - `STRING`
  - `release_date`: 发布日期 (可选) - `DATE`

### 4.2 关系（边）设计

关系连接图中的节点，表示实体之间的互动或关联。每个关系都有一个类型 (Type) 和一组属性 (Properties)。

#### 4.2.1 用户关系

- `(User)-[:FRIEND_OF {since: DATETIME}]->(User)`: 用户之间的好友关系，`since` 表示成为好友的时间。
- `(User)-[:KNOWS {level: STRING}]->(User)`: 用户之间的认识关系，`level` 可表示熟悉程度。
- `(User)-[:WORKS_AT {start_date: DATE, end_date: DATE, role: STRING}]->(Company)`: 用户在公司的工作关系。
- `(User)-[:BELONGS_TO {joined_at: DATETIME}]->(Organization)`: 用户属于某个组织（例如社区、学校、团队等）。
- `(User)-[:HAS_EXPERIENCE]->(WorkExperience)`: 用户拥有某段工作经历。
- `(User)-[:OWNS_RESOURCE]->(Resource)`: 用户拥有的资源。
- `(User)-[:HAS_DEMAND]->(Demand)`: 用户提出的需求。
- `(User)-[:MATCHED_WITH_RESOURCE {match_score: FLOAT, matched_at: DATETIME, cost: FLOAT}]->(Resource)`: 用户与资源匹配成功，包含匹配度、时间、可能产生的费用。
- `(User)-[:MATCHED_WITH_DEMAND {match_score: FLOAT, matched_at: DATETIME, revenue: FLOAT}]->(Demand)`: 用户与需求匹配成功，包含匹配度、时间、可能获得的收益。
- `(User)-[:CREATED]->(Memory)`: 用户创建了某条记忆（日记、照片、视频等）。
- `(User)-[:USES]->(Device)`: 用户使用某个设备。

#### 4.2.2 记忆关系

- `(Memory)-[:OCCURRED_AT {time_precision: STRING}]->(Location)`: 记忆发生于某个地点，`time_precision` 可表示时间精度（年、月、日、具体时间）。
- `(Memory)-[:MENTIONS]->(User)`: 记忆中提到了某个人（可以是用户或非用户）。
- `(Memory)-[:MENTIONS]->(Face)`: 记忆中识别出某张人脸。
- `(Memory)-[:MENTIONS]->(Organization)`: 记忆中提到了某个组织。
- `(Memory)-[:HAS_TAG {confidence: FLOAT}]->(Tag)`: 记忆被标注了某个标签。
- `(Memory)-[:CAPTURES]->(Photo)`: 记忆类型为视频时，视频中包含哪些照片片段。
- `(Memory)-[:CONTAINS_FACE {start_offset: INTEGER, end_offset: INTEGER}]->(Face)`: 视频记忆在特定时间段内包含某张人脸。
- `(Memory)-[:CONTAINS_OBJECT {object_name: STRING, confidence: FLOAT}]->(Object)`: 记忆中包含某个物体（如果 `Object` 也定义为节点）。
- `(Trajectory)-[:PASSES_THROUGH {sequence_order: INTEGER, timestamp: DATETIME}]->(Location)`: 轨迹经过的地点，包含顺序和时间。
- `(Trajectory)-[:RECORDS]->(Memory)`: 轨迹记录了某条记忆（如 GPS 轨迹上的特定照片）。

#### 4.2.3 组织与产品关系

- `(Company)-[:PRODUCES]->(Product)`: 公司生产某个产品。
- `(Organization)-[:HAS_MEMBERS]->(User)`: 组织拥有成员。

#### 4.2.4 人脸与照片/视频关系

- `(Photo)-[:CONTAINS_FACE_INSTANCE {bounding_box: STRING, confidence: FLOAT}]->(Face)`: 照片中包含某张人脸的实例。
- `(Video)-[:CONTAINS_FACE_INSTANCE {start_time: INTEGER, end_time: INTEGER, bounding_box: STRING, confidence: FLOAT}]->(Face)`: 视频中在特定时间段内包含某张人脸的实例。
- `(Photo)-[:TAKEN_AT {timestamp: DATETIME}]->(Location)`: 照片拍摄于某个地点。
- `(Video)-[:RECORDED_AT {timestamp: DATETIME}]->(Location)`: 视频拍摄于某个地点。
- `(Photo)-[:RELATED_TO]->(Memory)`: 照片作为某种记忆类型与通用记忆节点关联。
- `(Video)-[:RELATED_TO]->(Memory)`: 视频作为某种记忆类型与通用记忆节点关联。

#### 4.2.5 日记关系

- `(Diary)-[:ABOUT_USER]->(User)`: 日记是关于某个用户。
- `(Diary)-[:ABOUT_FACE]->(Face)`: 日记提到了某张人脸。
- `(Diary)-[:ABOUT_LOCATION]->(Location)`: 日记中提到了某个地点。
- `(Diary)-[:ASSOCIATED_WITH]->(Photo)`: 日记与某张照片关联。
- `(Diary)-[:ASSOCIATED_WITH]->(Video)`: 日记与某个视频关联。
- `(Diary)-[:RELATED_TO]->(Memory)`: 日记作为某种记忆类型与通用记忆节点关联。

#### 4.2.6 设备关系

- `(Device)-[:LOCATED_AT]->(Location)`: 设备位于某个地点。
- `(Device)-[:GENERATES_DATA]->(Memory)`: 设备生成记忆数据（如 DeepGlass 拍摄照片，DeepArm 记录操作日志）。

### 4.3 图数据库模式 (Cypher 定义)

以下是使用 Cypher 语言定义的 Neo4j 图数据库模式，包括节点标签和属性的创建，以及关系类型的创建。

```
// -------------------- 节点标签定义 --------------------
CREATE CONSTRAINT ON (u:User) ASSERT u.user_id IS UNIQUE;
CREATE CONSTRAINT ON (m:Memory) ASSERT m.memory_id IS UNIQUE;
CREATE CONSTRAINT ON (r:Resource) ASSERT r.resource_id IS UNIQUE;
CREATE CONSTRAINT ON (d:Demand) ASSERT d.demand_id IS UNIQUE;
CREATE CONSTRAINT ON (l:Location) ASSERT l.location_id IS UNIQUE;
CREATE CONSTRAINT ON (o:Organization) ASSERT o.org_id IS UNIQUE;
CREATE CONSTRAINT ON (f:Face) ASSERT f.face_id IS UNIQUE;
CREATE CONSTRAINT ON (p:Photo) ASSERT p.photo_id IS UNIQUE;
CREATE CONSTRAINT ON (v:Video) ASSERT v.video_id IS UNIQUE;
CREATE CONSTRAINT ON (dev:Device) ASSERT dev.device_id IS UNIQUE;
CREATE CONSTRAINT ON (di:Diary) ASSERT di.diary_id IS UNIQUE;
CREATE CONSTRAINT ON (t:Trajectory) ASSERT t.trajectory_id IS UNIQUE;
CREATE CONSTRAINT ON (we:WorkExperience) ASSERT we.experience_id IS UNIQUE;
CREATE CONSTRAINT ON (co:Company) ASSERT co.company_id IS UNIQUE;
CREATE CONSTRAINT ON (pr:Product) ASSERT pr.product_id IS UNIQUE;

// -------------------- 关系类型定义 (无需 CREATE RELATIONSHIP, 关系在创建时自动定义) --------------------
// 关系类型已在 4.2 节中描述，无需额外Cypher定义。

// -------------------- 节点属性索引 (可选，用于提高查询性能) --------------------
CREATE INDEX ON :User(username);
CREATE INDEX ON :Memory(type);
CREATE INDEX ON :Resource(type);
CREATE INDEX ON :Demand(type);
CREATE INDEX ON :Location(name);
CREATE INDEX ON :Organization(name);
CREATE INDEX ON :Face(name);
CREATE INDEX ON :Photo(upload_time);
CREATE INDEX ON :Video(upload_time);
CREATE INDEX ON :Diary(created_at);
CREATE INDEX ON :Trajectory(start_time);
CREATE INDEX ON :WorkExperience(title);
CREATE INDEX ON :Company(name);
CREATE INDEX ON :Product(name);
```

### 4.4 节点关系流程图 (PlantUML)

以下 PlantUML 代码描述了 DeepDiary 图数据库中主要实体及其核心关系。由于图的复杂性，这里只展示关键节点和关系，以便于理解整体结构。

```
@startuml class diagram
left to right direction
skinparam handwritten true
skinparam style plain
skinparam defaultFontName "Cascadia Code"
skinparam defaultFontSize 14

' 定义节点 (使用 class 关键字以支持内部属性显示)
class User as "用户" {
  user_id
  username
  city
  industry
  position
  created_at
  updated_at
  avatar_url
}
class Memory as "记忆" {
  memory_id
  title
  summary
  type
  created_at
  location_text
  vector_id_ref
}
class Resource as "资源" {
  resource_id
  name
  description
  type
  price
  created_at
  updated_at
  vector_id_ref
}
class Demand as "需求" {
  demand_id
  name
  description
  type
  budget
  created_at
  updated_at
  urgency
  vector_id_ref
}
class Location as "地点" {
  location_id
  name
  latitude
  longitude
  address_detail
  type
}
class Organization as "组织机构" {
  org_id
  name
  type
  industry
  location
  description
}
class Face as "人脸" {
  face_id
  name
  recognition_model_version
  vector_id_ref
  is_identified
}
class Photo as "照片" {
  photo_id
  file_path
  thumbnail_path
  upload_time
  description
  resolution
  exif_data_summary
  is_private
  vector_id_ref
}
class Video as "视频" {
  video_id
  file_path
  thumbnail_path
  upload_time
  description
  duration
  resolution
  is_private
  vector_id_ref
}
class Device as "设备" {
  device_id
  name
  type
  serial_number
  status
  firmware_version
  last_active_time
}
class Diary as "日记" {
  diary_id
  title
  content
  created_at
  mood
  weather
  is_private
  vector_id_ref
}
class Trajectory as "轨迹" {
  trajectory_id
  name
  start_time
  end_time
  total_distance_km
  vector_id_ref
}
class WorkExperience as "工作经历" {
  experience_id
  title
  start_date
  end_date
  description
  industry
  role_type
}
class Company as "公司" {
  company_id
  name
  industry
  location
  description
  website
}
class Product as "产品" {
  product_id
  name
  description
  category
  release_date
}
class Tag as "标签" {
  tag_id
  tag_name
  description
}


' 定义关系
User "1" -- "N" Memory : "创建于"
User "1" -- "N" Resource : "拥有"
User "1" -- "N" Demand : "提出"
User "1" -- "N" Device : "使用"
User "1" -- "N" WorkExperience : "拥有"
User "1" -- "N" Photo : "拍摄者"
User "1" -- "N" Video : "录制者"
User "1" -- "N" Diary : "撰写"
User "1" -- "N" Trajectory : "生成"

User "N" -- "N" User : "FRIEND_OF"
User "N" -- "N" User : "KNOWS"

User "1" -- "N" Organization : "属于"
User "1" -- "N" Company : "工作于"

Memory "N" -- "1" Location : "发生于"
Memory "N" -- "N" User : "提及用户"
Memory "N" -- "N" Face : "提及人脸"
Memory "N" -- "N" Organization : "提及组织"
Memory "N" -- "N" Tag : "带有标签"

Resource "N" -- "N" Demand : "匹配"

Photo "N" -- "N" Face : "包含人脸"
Photo "N" -- "1" Location : "拍摄于"
Photo "1" -- "1" Memory : "关联记忆"

Video "N" -- "N" Face : "包含人脸实例"
Video "N" -- "1" Location : "录制于"
Video "1" -- "1" Memory : "关联记忆"

Diary "1" -- "1" Memory : "关联记忆"
Diary "N" -- "N" User : "关于用户"
Diary "N" -- "N" Face : "关于人脸"
Diary "N" -- "N" Location : "关于地点"
Diary "N" -- "N" Photo : "关联照片"
Diary "N" -- "N" Video : "关联视频"

Trajectory "N" -- "N" Location : "经过"
Trajectory "N" -- "N" Memory : "记录"

Company "1" -- "N" Product : "生产"

Device "N" -- "1" Location : "位于"
Device "N" -- "N" Memory : "生成数据"

WorkExperience "1" -- "1" Company : "公司"

@enduml
```

![graph](https://deep-diary.oss-cn-hangzhou.aliyuncs.com/blog/graph.png)

## 5. 图数据库具体实现方案

### 5.1 Neo4j 集成

DeepServer 后端（基于 Django/Python）将通过官方提供的 **Neo4j Python Driver** 来与 Neo4j 数据库进行交互。

- **连接管理：** 使用连接池管理与 Neo4j 的连接，确保高效和稳定的数据库操作。
- **数据模型映射：** 虽然 Neo4j 是无模式的，但在应用层会定义数据模型，确保数据的一致性。可以将关系型数据库中的实体 ID 作为图数据库节点的属性，以便进行跨数据库关联查询。
- **Cypher 查询构建：** 使用 Cypher 语言进行图数据的创建、读取、更新和删除 (CRUD) 操作。对于复杂查询，可以通过参数化查询或事务函数来提高性能和安全性。

```
from neo4j import GraphDatabase

class Neo4jClient:
    def __init__(self, uri, user, password):
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self._driver.close()

    def create_user(self, user_id, username, email):
        with self._driver.session() as session:
            query = (
                "CREATE (u:User {user_id: $user_id, username: $username, email: $email, created_at: datetime()})"
                "RETURN u"
            )
            result = session.write_transaction(lambda tx: tx.run(query, user_id=user_id, username=username, email=email))
            return result.single()[0]

    def create_friend_relationship(self, user_id1, user_id2):
        with self._driver.session() as session:
            query = (
                "MATCH (u1:User {user_id: $user_id1})"
                "MATCH (u2:User {user_id: $user_id2})"
                "MERGE (u1)-[f:FRIEND_OF]->(u2)"
                "ON CREATE SET f.since = datetime()"
                "RETURN f"
            )
            result = session.write_transaction(lambda tx: tx.run(query, user_id1=user_id1, user_id2=user_id2))
            return result.single()[0]

    def get_friends_of_user(self, user_id):
        with self._driver.session() as session:
            query = (
                "MATCH (u:User {user_id: $user_id})-[:FRIEND_OF]->(f:User)"
                "RETURN f.username, f.email"
            )
            result = session.read_transaction(lambda tx: tx.run(query, user_id=user_id))
            return [record for record in result]

    # ... 其他CRUD操作和查询方法
```

### 5.2 与关系型数据库和向量数据库的协同

图数据库在 DeepDiary 中扮演着**“关联枢纽”**的角色，它将关系型数据库和向量数据库中的数据通过关系串联起来，形成一个完整的知识网络。

- **关联关系型数据：** 图数据库中的节点属性（如 `user_id`, `memory_id`, `resource_id` 等）将作为外键，与关系型数据库中的相应表进行关联。这意味着图数据库负责存储实体间的复杂关系，而实体的详细属性则存储在关系型数据库中。当需要获取某个实体的完整信息时，可以先在图数据库中进行关系查询，然后根据 ID 到关系型数据库中检索详细数据。
- **关联向量数据：** 节点属性中的 `vector_id_ref` 字段将存储向量数据库中相应向量的 ID。当需要进行语义搜索或相似性匹配时，可以先从图数据库中获取相关实体的 `vector_id_ref`，然后到向量数据库中执行向量查询。例如，先通过图查询找到某个用户的所有记忆，再根据这些记忆的 `vector_id_ref` 在向量数据库中进行语义搜索。
- **数据同步：** DeepServer 后端服务负责协调三类数据库之间的数据同步。当关系型数据库中的实体数据发生变化时，需要同步更新图数据库中对应节点的属性。当新的多模态数据被向量化并存入向量数据库时，也需要在图数据库中创建相应的节点并建立关系。

### 5.3 查询优化与性能考量

- **索引使用：** 对常用查询的节点属性创建索引（如 `User.user_id`, `Memory.type` 等），以提高查询效率。
- **查询优化：**
  - 避免全图遍历，尽可能限制查询范围。
  - 使用 `MATCH` 语句时，尽量提供起始节点的标签和属性，缩小匹配范围。
  - 优先使用特定类型的关系，而不是泛化的 `MATCH (a)-[]->(b)`。
  - 利用 `WHERE` 子句进行过滤。
  - 对于写操作，优先使用 `MERGE` 而不是 `CREATE`，避免重复创建节点和关系。
- **硬件资源：** Neo4j 对内存和 CPU 有较高要求。根据数据量和查询复杂度，需要合理配置服务器资源。
- **集群部署：** 对于大规模数据和高并发场景，可以部署 Neo4j 集群（因果集群），以提高可用性和扩展性。

## 6. 总结

本文档详细阐述了 DeepDiary 项目的图数据库设计，明确了其在实现社交网络分析、资源匹配和记忆追溯等核心功能中的重要作用。通过选择 Neo4j 作为图数据库，并结合关系型数据库和向量数据库的协同工作，DeepDiary 系统将能够构建一个强大、灵活、高效的知识网络，为用户提供智能化的服务和卓越的体验。本设计为开发团队提供了清晰的指导，助力项目顺利实施。
