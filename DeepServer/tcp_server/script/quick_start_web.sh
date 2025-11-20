#!/bin/bash
# ESP32 Web服务器快速启动脚本 - 自动检测可用端口

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ESP32 Web服务器快速启动${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查端口占用函数
check_port() {
    local port=$1
    if lsof -i :$port >/dev/null 2>&1; then
        return 1  # 端口被占用
    else
        return 0  # 端口空闲
    fi
}

# 自动检测可用端口
find_available_port() {
    local start_port=$1
    local port=$start_port
    while [ $port -lt $((start_port + 50)) ]; do
        if check_port $port; then
            echo $port
            return 0
        fi
        port=$((port + 1))
    done
    echo $start_port  # 如果都找不到，返回原始端口
}

# 自动选择端口
tcp_port=$(find_available_port 8080)
web_port=$(find_available_port 8000)

echo -e "${YELLOW}自动检测可用端口:${NC}"
echo -e "${GREEN}✅ TCP接收端口: $tcp_port${NC}"
echo -e "${GREEN}✅ Web访问端口: $web_port${NC}"
echo ""

# 检查依赖
echo -e "${YELLOW}检查依赖...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 Python3${NC}"
    exit 1
fi

# 检查必要的 Python 包
python3 -c "import cv2" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}警告: opencv-python 未安装${NC}"
    echo -e "${YELLOW}正在安装依赖...${NC}"
    pip3 install -r requirements_tcp_server.txt
fi

echo -e "${GREEN}✓ 依赖检查完成${NC}"
echo ""

# 获取本机 IP
echo -e "${YELLOW}本机 IP 地址:${NC}"
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    ifconfig | grep "inet " | grep -v 127.0.0.1 | awk '{print "  - " $2}'
else
    # Linux
    hostname -I | tr ' ' '\n' | grep -v '^$' | awk '{print "  - " $1}'
fi
echo ""

echo -e "${GREEN}启动 Web 版服务器...${NC}"
echo -e "${YELLOW}浏览器访问: http://localhost:${web_port}${NC}"
echo -e "${BLUE}TCP接收端口: ${tcp_port}${NC}"
echo -e "${BLUE}Web访问端口: ${web_port}${NC}"
echo ""
echo -e "${YELLOW}按 Ctrl+C 停止服务器${NC}"
echo ""

# 启动服务器
python3 tcp_video_server_web.py --tcp-port $tcp_port --web-port $web_port
