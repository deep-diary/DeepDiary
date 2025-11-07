#!/bin/bash

# DeepWeb 启动脚本
# 功能：安全地停止旧进程并启动新的 Web 应用

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/output.log"
PID_FILE="${SCRIPT_DIR}/deepweb.pid"
MAIN_SCRIPT="${SCRIPT_DIR}/deepweb/main.py"
PORT=7860

# 切换到脚本所在目录
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DeepWeb 启动脚本${NC}"
echo -e "${BLUE}========================================${NC}"

# 1. 检查并激活虚拟环境
echo -e "${YELLOW}[1/7] 检查并激活虚拟环境...${NC}"
VENV_PATH="$HOME/diary_env"
if [ -d "$VENV_PATH" ] && [ -f "$VENV_PATH/bin/activate" ]; then
    echo -e "${YELLOW}  找到虚拟环境: ${VENV_PATH}${NC}"
    source "$VENV_PATH/bin/activate"
    echo -e "${GREEN}✓ 虚拟环境已激活${NC}"
    # 使用虚拟环境中的 Python
    PYTHON_CMD="$VENV_PATH/bin/python"
else
    echo -e "${YELLOW}⚠ 未找到虚拟环境，使用系统 Python${NC}"
    PYTHON_CMD="python3"
fi

# 2. 检查 Python 环境
echo -e "${YELLOW}[2/7] 检查 Python 环境...${NC}"
if ! command -v "$PYTHON_CMD" &> /dev/null; then
    echo -e "${RED}✗ 错误: 未找到 Python${NC}"
    exit 1
fi
PYTHON_VERSION=$("$PYTHON_CMD" --version 2>&1)
echo -e "${GREEN}✓ Python 版本: ${PYTHON_VERSION}${NC}"

# 3. 检查主脚本文件
echo -e "${YELLOW}[3/7] 检查主脚本文件...${NC}"
if [ ! -f "$MAIN_SCRIPT" ]; then
    echo -e "${RED}✗ 错误: 找不到主脚本文件 ${MAIN_SCRIPT}${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 主脚本文件存在${NC}"

# 4. 检查端口是否被占用
echo -e "${YELLOW}[4/7] 检查端口 ${PORT} 是否被占用...${NC}"
PORT_IN_USE=false
if command -v lsof &> /dev/null; then
    if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
        PORT_IN_USE=true
    fi
elif command -v ss &> /dev/null; then
    if ss -tlnp 2>/dev/null | grep -q ":${PORT} "; then
        PORT_IN_USE=true
    fi
elif command -v netstat &> /dev/null; then
    if netstat -tlnp 2>/dev/null | grep -q ":${PORT} "; then
        PORT_IN_USE=true
    fi
fi

if [ "$PORT_IN_USE" = true ]; then
    echo -e "${YELLOW}⚠ 端口 ${PORT} 已被占用，将在停止旧进程后释放${NC}"
else
    echo -e "${GREEN}✓ 端口 ${PORT} 可用${NC}"
fi

# 5. 停止旧进程
echo -e "${YELLOW}[5/7] 停止旧进程...${NC}"
OLD_PIDS=$(pgrep -f "python.*main.py" || true)
if [ -n "$OLD_PIDS" ]; then
    echo -e "${YELLOW}  找到运行中的进程: ${OLD_PIDS}${NC}"
    # 优雅地停止进程
    for pid in $OLD_PIDS; do
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}  正在停止进程 ${pid}...${NC}"
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
        echo -e "${YELLOW}  强制停止残留进程...${NC}"
        pkill -9 -f "python.*main.py" 2>/dev/null || true
        sleep 1
    fi
    
    echo -e "${GREEN}✓ 旧进程已停止${NC}"
else
    echo -e "${GREEN}✓ 没有运行中的进程${NC}"
fi

# 清理 PID 文件
[ -f "$PID_FILE" ] && rm -f "$PID_FILE"

# 6. 启动新进程
echo -e "${YELLOW}[6/7] 启动新进程...${NC}"
# 使用虚拟环境中的 Python（如果已激活）或系统 Python
nohup "$PYTHON_CMD" -u "$MAIN_SCRIPT" > "$LOG_FILE" 2>&1 &
NEW_PID=$!

# 保存 PID
echo $NEW_PID > "$PID_FILE"
echo -e "${GREEN}✓ 新进程已启动 (PID: ${NEW_PID})${NC}"

# 7. 等待并验证启动
echo -e "${YELLOW}[7/7] 验证启动状态...${NC}"
sleep 2

# 检查进程是否还在运行
if ! kill -0 "$NEW_PID" 2>/dev/null; then
    echo -e "${RED}✗ 错误: 进程启动失败，请检查日志: ${LOG_FILE}${NC}"
    echo -e "${RED}最后 20 行日志:${NC}"
    tail -20 "$LOG_FILE" 2>/dev/null || echo "无法读取日志文件"
    exit 1
fi

# 检查端口是否开始监听（最多等待 10 秒）
PORT_READY=false
for i in {1..20}; do
    sleep 0.5
    if command -v lsof &> /dev/null; then
        if lsof -Pi :${PORT} -sTCP:LISTEN -t >/dev/null 2>&1; then
            PORT_READY=true
            break
        fi
    elif command -v ss &> /dev/null; then
        if ss -tlnp 2>/dev/null | grep -q ":${PORT} "; then
            PORT_READY=true
            break
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tlnp 2>/dev/null | grep -q ":${PORT} "; then
            PORT_READY=true
            break
        fi
    fi
done

if [ "$PORT_READY" = true ]; then
    echo -e "${GREEN}✓ 端口 ${PORT} 已开始监听${NC}"
else
    echo -e "${YELLOW}⚠ 警告: 端口 ${PORT} 尚未开始监听，但进程正在运行${NC}"
    echo -e "${YELLOW}  请稍等片刻或检查日志: ${LOG_FILE}${NC}"
fi

# 显示启动信息
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}启动完成！${NC}"
echo -e "${GREEN}进程 ID: ${NEW_PID}${NC}"
echo -e "${GREEN}访问地址: https://www.deep-diary.com${NC}"
echo -e "${GREEN}本地地址: http://localhost:${PORT}${NC}"
echo -e "${GREEN}日志文件: ${LOG_FILE}${NC}"
echo -e "${GREEN}PID 文件: ${PID_FILE}${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}查看日志: tail -f ${LOG_FILE}${NC}"
echo -e "${BLUE}停止服务: kill ${NEW_PID} 或 pkill -f 'python.*main.py'${NC}"
