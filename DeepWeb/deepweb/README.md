# DeepWeb - 不倒翁设备控制平台

基于Streamlit的Web控制界面，用于控制ESP32-S3不倒翁设备。

## 🚀 功能特性

- **设备状态监控**: 实时显示设备状态、传感器数据、电机状态
- **设备控制**: 发送控制命令到设备（电机、机械臂、摄像头、LED）
- **视频监控**: 实时显示设备摄像头画面
- **MQTT通信**: 基于MQTT协议的设备通信
- **多页面布局**: 使用Streamlit多页面设计

## 📋 系统要求

- Python 3.8+
- pip3
- 支持的操作系统: Linux, macOS, Windows

## 🛠️ 安装步骤

### 1. 克隆项目
```bash
git clone <repository-url>
cd DeepWeb/deepweb
```

### 2. 安装依赖
```bash
pip3 install -r requirements.txt
```

### 3. 配置设置
编辑 `config/config.json` 文件，设置MQTT服务器地址等参数：

```json
{
  "mqtt": {
    "host": "your-mqtt-server.com",
    "port": 1883,
    "username": "your-username",
    "password": "your-password"
  }
}
```

## 🚀 启动应用

### 方式1: 使用启动脚本（推荐）
```bash
chmod +x start.sh
./start.sh
```

### 方式2: 手动启动
```bash
# 启动TCP视频服务器（后台）
python3 services/cloud_communication/tcp_server/tcp_video_server_web.py &

# 启动Streamlit应用
streamlit run main.py --server.port 8501
```

## 📱 访问界面

启动成功后，在浏览器中访问：
- **主界面**: http://localhost:8501
- **TCP视频服务器**: http://localhost:8000

## 🎮 使用说明

### 首页
- 查看系统概览和设备列表
- 快速操作按钮

### 设备状态
- 实时监控设备状态
- 查看传感器数据
- 显示电机和机械臂状态

### 设备控制
- **电机控制**: 控制单个或多个电机
- **机械臂控制**: 控制关节和末端执行器
- **摄像头控制**: 调整图像参数
- **LED控制**: 控制LED颜色和效果

### 摄像头监控
- 实时视频流显示
- 图像处理选项
- 截图和录制功能

### 设置
- MQTT连接配置
- TCP服务器设置
- 界面个性化设置

## 🔧 技术架构

### 核心模块
- `app_logic/`: 核心业务逻辑
- `services/`: 服务层（MQTT、TCP等）
- `ui/pages/`: Streamlit页面
- `config/`: 配置管理
- `data_management/`: 数据管理

### 通信协议
- **MQTT**: 设备状态和控制命令
- **TCP**: 视频流传输
- **HTTP**: Web界面访问

## 📊 设备协议

支持ESP32-S3设备的MQTT协议，包括：

### 上行主题（设备→服务器）
- `deepcontroller/{device_id}/status` - 设备状态
- `deepcontroller/{device_id}/sensor` - 传感器数据
- `deepcontroller/{device_id}/motor` - 电机状态
- `deepcontroller/{device_id}/arm` - 机械臂状态
- `deepcontroller/{device_id}/camera` - 摄像头状态

### 下行主题（服务器→设备）
- `deepcontroller/{device_id}/command` - 控制命令

## 🐛 故障排除

### 常见问题

1. **MQTT连接失败**
   - 检查MQTT服务器地址和端口
   - 确认用户名密码正确
   - 检查网络连接

2. **视频流无法显示**
   - 确认ESP32设备已连接TCP服务器
   - 检查TCP端口8080是否被占用
   - 查看设备摄像头是否正常工作

3. **设备控制无响应**
   - 确认设备在线状态
   - 检查MQTT主题订阅
   - 查看命令历史记录

### 日志查看
应用运行时会在控制台输出详细日志，包括：
- MQTT连接状态
- 设备数据接收
- 命令发送结果

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- **开发团队**: DeepDiary Team
- **项目地址**: [GitHub Repository]
- **问题反馈**: [Issues Page]

---

**DeepWeb v1.0.0** - 不倒翁设备控制平台
