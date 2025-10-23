#!/bin/bash
# ESP32 TCP 视频服务器快速启动脚本

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ESP32 TCP 视频服务器启动脚本${NC}"
echo -e "${BLUE}========================================${NC}"
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

# 选择服务器类型
echo -e "${BLUE}请选择服务器类型:${NC}"
echo "  1) 简化版 (快速测试，本地显示)"
echo "  2) 完整版 (视频录制，本地显示)"
echo "  3) Web 版 (浏览器访问，适合云端部署)"
echo ""
read -p "请选择 [1-3]: " choice

case $choice in
    1)
        echo -e "${GREEN}启动简化版服务器...${NC}"
        python3 tcp_video_server_simple.py
        ;;
    2)
        echo -e "${GREEN}启动完整版服务器...${NC}"
        read -p "是否启用视频录制? [y/N]: " record
        if [[ $record == "y" || $record == "Y" ]]; then
            python3 tcp_video_server.py --save-video
        else
            python3 tcp_video_server.py
        fi
        ;;
    3)
        echo -e "${GREEN}启动 Web 版服务器...${NC}"
        
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
            while [ $port -lt $((start_port + 100)) ]; do
                if check_port $port; then
                    echo $port
                    return 0
                fi
                port=$((port + 1))
            done
            echo $start_port  # 如果都找不到，返回原始端口
        }
        
        # TCP端口检测
        read -p "TCP 端口 [8080]: " tcp_port
        tcp_port=${tcp_port:-8080}
        if ! check_port $tcp_port; then
            echo -e "${YELLOW}警告: TCP端口 $tcp_port 已被占用${NC}"
            available_tcp=$(find_available_port $tcp_port)
            if [ $available_tcp -ne $tcp_port ]; then
                echo -e "${GREEN}建议使用端口: $available_tcp${NC}"
                read -p "是否使用建议端口 $available_tcp? [Y/n]: " use_suggested
                if [[ $use_suggested != "n" && $use_suggested != "N" ]]; then
                    tcp_port=$available_tcp
                fi
            fi
        fi
        
        # Web端口检测
        read -p "Web 端口 [8000]: " web_port
        web_port=${web_port:-8000}
        if ! check_port $web_port; then
            echo -e "${YELLOW}警告: Web端口 $web_port 已被占用${NC}"
            available_web=$(find_available_port $web_port)
            if [ $available_web -ne $web_port ]; then
                echo -e "${GREEN}建议使用端口: $available_web${NC}"
                read -p "是否使用建议端口 $available_web? [Y/n]: " use_suggested
                if [[ $use_suggested != "n" && $use_suggested != "N" ]]; then
                    web_port=$available_web
                fi
            fi
        fi
        
        echo ""
        echo -e "${GREEN}服务器启动中...${NC}"
        echo -e "${YELLOW}浏览器访问: http://localhost:${web_port}${NC}"
        echo -e "${BLUE}TCP接收端口: ${tcp_port}${NC}"
        echo -e "${BLUE}Web访问端口: ${web_port}${NC}"
        python3 tcp_video_server_web.py --tcp-port $tcp_port --web-port $web_port
        ;;
    *)
        echo -e "${RED}无效的选择${NC}"
        exit 1
        ;;
esac

