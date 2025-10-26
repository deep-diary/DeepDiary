#!/bin/bash
# DeepWeb 最终启动脚本

echo "=========================================="
echo "DeepWeb - 不倒翁设备控制平台"
echo "=========================================="

# 检查Python环境
python_version=$(python3 --version 2>&1)
echo "Python版本: $python_version"

# 安装核心依赖
echo "安装依赖包..."
pip3 install streamlit plotly pandas paho-mqtt opencv-python numpy Pillow pyyaml dataclasses-json

echo "=========================================="
echo "启动DeepWeb应用..."
echo "请在浏览器中访问: http://localhost:8501"
echo "TCP视频接收端口: 8080"
echo "按 Ctrl+C 停止服务"
echo "=========================================="

# 启动Streamlit应用
streamlit run main.py --server.port 8501 --server.address 0.0.0.0
