# DeepWin Web 演示平台

基于 Streamlit 的 DeepWin 功能演示平台，提供直观的 Web 界面来展示和测试 DeepWin 的各项功能。

## 🚀 功能特点

- **配置管理演示**: 展示多格式配置管理、环境变量管理、配置验证等功能
- **记忆处理演示**: 展示文本、图片、视频、GPS 等多种记忆类型的创建、检索、分析
- **设备控制演示**: 展示机械臂控制、设备连接、状态监控、轨迹规划等功能
- **AI 功能演示**: 展示智能对话、记忆分析、任务规划、智能搜索等 AI 功能
- **交互式测试**: 提供直观的测试界面，支持实时配置修改和测试执行

## 🛠️ 技术架构

- **前端框架**: Streamlit
- **数据可视化**: Plotly, Altair
- **数据处理**: Pandas, NumPy
- **配置管理**: 复用 DeepWin 核心配置管理器
- **测试框架**: 集成 DeepWin 测试基类系统

## 📦 安装依赖

### 1. 安装核心依赖

```bash
pip install -r requirements.txt
```

### 2. 安装可选依赖（推荐）

```bash
# 数据可视化增强
pip install altair matplotlib seaborn

# 开发工具
pip install black pylint pytest
```

## 🚀 快速开始

### 1. 启动 Web 演示

```bash
# 方法1: 使用启动脚本（推荐）
cd DeepWin/scripts
python start_web_demo.py

# 方法2: 直接启动
cd DeepWin/web_demo
streamlit run main.py
```

### 2. 访问演示界面

启动成功后，在浏览器中访问：

```
http://localhost:8501
```

### 3. 功能导航

- **🏠 首页**: 项目介绍和系统状态
- **⚙️ 配置管理**: 配置查看、测试、环境变量管理
- **🧠 记忆处理**: 记忆创建、检索、分析、同步
- **🤖 设备控制**: 设备连接、控制、状态监控、轨迹规划
- **🤖 AI 功能**: 智能对话、记忆分析、任务规划、智能搜索

## 🧪 测试功能

### 配置管理测试

- **基本配置加载**: 测试配置文件的加载和基本配置项
- **配置验证**: 验证配置结构和配置值的有效性
- **多格式支持**: 测试 JSON、YAML、TOML 等格式的配置保存
- **环境变量加载**: 测试环境变量的加载和优先级

### 记忆处理测试

- **记忆创建**: 创建不同类型的记忆（文本、图片、GPS 等）
- **记忆检索**: 通过关键词、标签、时间等方式检索记忆
- **记忆分析**: 分析记忆的统计信息、时间分布、标签分布
- **记忆同步**: 测试云端同步功能和状态

### 设备控制测试

- **设备连接**: 连接不同类型的设备（机械臂、摄像头、GPS 等）
- **设备控制**: 手动控制、轨迹执行、示教模式等
- **状态监控**: 实时监控设备状态和性能指标
- **轨迹规划**: 生成直线、圆弧等不同类型的轨迹

## 🔧 配置说明

### 环境变量配置

创建 `.env` 文件来配置环境变量：

```bash
# API配置
LLM_API_KEY=your_api_key_here
DEEPWIN_API_KEY=your_deepwin_key

# 设备配置
DEEPARM_SERIAL_PORT=COM11
DEEPARM_BAUD_RATE=115200

# 应用配置
DEEPWIN_ENV=development
DEEPWIN_LOG_LEVEL=INFO
```

### 配置文件

Web 演示平台会复用 DeepWin 的核心配置管理器，支持：

- JSON 配置文件
- YAML 配置文件
- TOML 配置文件
- 环境变量文件

## 📁 目录结构

```
web_demo/
├── main.py                    # 主入口文件
├── requirements.txt           # 依赖包列表
├── README.md                  # 说明文档
├── pages/                     # 页面模块
│   ├── __init__.py           # 页面包初始化
│   ├── config_demo.py        # 配置管理演示
│   ├── memory_demo.py        # 记忆处理演示
│   ├── device_demo.py        # 设备控制演示
│   └── ai_demo.py            # AI功能演示
├── components/                # 可复用组件
│   ├── __init__.py           # 组件包初始化
│   ├── config_viewer.py      # 配置查看器
│   └── test_runner.py        # 测试运行器
├── utils/                     # 工具函数
│   ├── __init__.py           # 工具包初始化
│   └── streamlit_utils.py    # Streamlit工具
├── static/                    # 静态资源
│   ├── css/                  # 样式文件
│   ├── js/                   # JavaScript文件
│   └── images/               # 图片资源
└── data/                      # 演示数据
    ├── sample_configs/        # 示例配置
    ├── test_results/          # 测试结果
    └── demo_outputs/          # 演示输出
```

## 🎨 自定义开发

### 添加新页面

1. 在 `pages/` 目录下创建新的页面文件
2. 实现 `show()` 函数
3. 在 `main.py` 中添加页面路由
4. 在 `pages/__init__.py` 中导入新页面

### 添加新组件

1. 在 `components/` 目录下创建新的组件文件
2. 实现组件类和相关方法
3. 在 `components/__init__.py` 中导入新组件

### 自定义样式

1. 修改 `utils/streamlit_utils.py` 中的 CSS 样式
2. 在 `static/css/` 目录下添加自定义样式文件
3. 使用 Streamlit 的 `st.markdown()` 和 HTML/CSS

## 🐛 故障排除

### 常见问题

1. **导入错误**: 确保 DeepWin 核心模块在 Python 路径中
2. **依赖缺失**: 运行 `pip install -r requirements.txt` 安装依赖
3. **端口占用**: 修改启动脚本中的端口号（默认 8501）
4. **路径问题**: 确保在正确的目录下运行启动脚本

### 调试技巧

1. **启用详细日志**: 在启动时添加 `--logger.level=debug`
2. **检查依赖**: 使用 `pip list` 查看已安装的包
3. **路径检查**: 使用 `print(Path.cwd())` 检查当前工作目录

## 📚 相关文档

- [DeepWin 主项目文档](../README.md)
- [Streamlit 官方文档](https://docs.streamlit.io/)
- [Plotly 图表库文档](https://plotly.com/python/)
- [Pandas 数据处理文档](https://pandas.pydata.org/docs/)

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用与 DeepWin 主项目相同的许可证。

## 🆕 更新日志

### v0.1.0 (当前版本)

- ✅ 创建基础 Web 演示框架
- ✅ 实现配置管理演示页面
- ✅ 实现记忆处理演示页面
- ✅ 实现设备控制演示页面
- ✅ 实现 AI 功能演示页面
- ✅ 创建可复用组件系统
- ✅ 提供启动脚本和依赖管理
