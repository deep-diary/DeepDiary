#!/bin/bash
# 端口检查工具

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  ESP32 服务器端口检查工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检查常用端口
check_port() {
    local port=$1
    local service=$2
    
    if lsof -i :$port >/dev/null 2>&1; then
        local process=$(lsof -i :$port | tail -n +2 | awk '{print $1, $2}' | head -1)
        echo -e "${RED}❌ 端口 $port ($service) 已被占用${NC}"
        echo -e "${YELLOW}   占用进程: $process${NC}"
        return 1
    else
        echo -e "${GREEN}✅ 端口 $port ($service) 可用${NC}"
        return 0
    fi
}

echo -e "${YELLOW}检查常用端口状态:${NC}"
echo ""

# 检查常用端口
check_port 8000 "Web服务器"
check_port 8080 "TCP接收"
check_port 8001 "备用Web"
check_port 8081 "备用TCP"

echo ""
echo -e "${YELLOW}端口占用详情:${NC}"

# 显示详细的端口占用信息
if command -v lsof &> /dev/null; then
    echo -e "${BLUE}所有监听的端口:${NC}"
    lsof -i -P -n | grep LISTEN | grep -E ":(8000|8080|8001|8081)" | while read line; do
        echo -e "${YELLOW}  $line${NC}"
    done
else
    echo -e "${RED}lsof 命令不可用，无法显示详细信息${NC}"
fi

echo ""
echo -e "${YELLOW}解决方案:${NC}"
echo "1. 使用启动脚本自动检测可用端口:"
echo -e "   ${GREEN}./start_server.sh${NC}"
echo ""
echo "2. 手动指定端口:"
echo -e "   ${GREEN}python3 tcp_video_server_web.py --tcp-port 8081 --web-port 8001${NC}"
echo ""
echo "3. 停止占用端口的进程:"
echo -e "   ${GREEN}lsof -ti:8000 | xargs kill -9${NC}"
echo ""
echo "4. 查看所有端口占用:"
echo -e "   ${GREEN}lsof -i -P -n | grep LISTEN${NC}"
