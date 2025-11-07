#!/bin/bash

# DeepWeb 停止脚本
# 功能：安全地停止运行中的 Web 应用

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${SCRIPT_DIR}/deepweb.pid"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DeepWeb 停止脚本${NC}"
echo -e "${BLUE}========================================${NC}"

# 查找运行中的进程
PIDS=$(pgrep -f "python.*main.py" || true)

if [ -z "$PIDS" ]; then
    echo -e "${YELLOW}没有找到运行中的进程${NC}"
    [ -f "$PID_FILE" ] && rm -f "$PID_FILE"
    exit 0
fi

echo -e "${YELLOW}找到运行中的进程: ${PIDS}${NC}"

# 优雅地停止进程
for pid in $PIDS; do
    if kill -0 "$pid" 2>/dev/null; then
        echo -e "${YELLOW}正在停止进程 ${pid}...${NC}"
        kill -TERM "$pid" 2>/dev/null || true
    fi
done

# 等待进程退出（最多等待 5 秒）
for i in {1..10}; do
    sleep 0.5
    REMAINING=$(pgrep -f "python.*main.py" || true)
    if [ -z "$REMAINING" ]; then
        break
    fi
done

# 如果还有进程在运行，强制杀死
REMAINING=$(pgrep -f "python.*main.py" || true)
if [ -n "$REMAINING" ]; then
    echo -e "${YELLOW}强制停止残留进程...${NC}"
    for pid in $REMAINING; do
        kill -9 "$pid" 2>/dev/null || true
    done
    sleep 1
fi

# 清理 PID 文件
[ -f "$PID_FILE" ] && rm -f "$PID_FILE"

# 验证是否已停止
FINAL_CHECK=$(pgrep -f "python.*main.py" || true)
if [ -z "$FINAL_CHECK" ]; then
    echo -e "${GREEN}✓ 所有进程已停止${NC}"
else
    echo -e "${RED}✗ 警告: 仍有进程在运行: ${FINAL_CHECK}${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"

