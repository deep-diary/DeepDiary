#!/bin/bash

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    log_error "Docker 未运行，请先启动 Docker"
    exit 1
fi

# 检查并清理占用端口的进程
check_and_kill_port() {
    local port=$1
    local protocol=${2:-tcp}
    
    # 检查是否有Docker容器占用该端口（通过检查端口映射）
    local container_info=$(docker ps -a --format "{{.ID}}|{{.Names}}|{{.Ports}}" | grep -E ":${port}->|:${port}/" | head -1)
    if [ -n "$container_info" ]; then
        local container_id=$(echo "$container_info" | cut -d'|' -f1)
        local container_name=$(echo "$container_info" | cut -d'|' -f2)
        log_warn "发现容器 ${container_name} (${container_id}) 占用端口 ${port}"
        log_info "停止并删除占用端口的容器..."
        docker stop "$container_id" > /dev/null 2>&1 || true
        docker rm "$container_id" > /dev/null 2>&1 || true
        sleep 1
        return 0
    fi
    
    # 检查是否有非Docker进程占用该端口
    if command -v ss > /dev/null 2>&1; then
        local pid=$(ss -tlnp 2>/dev/null | grep -E ":${port}[[:space:]]" | awk '{print $6}' | sed -n 's/.*pid=\([0-9]*\).*/\1/p' | head -1)
        if [ -n "$pid" ] && [ "$pid" != "-" ] && [ "$pid" -gt 0 ] 2>/dev/null; then
            log_warn "发现进程 ${pid} 占用端口 ${port}"
            log_info "终止占用端口的进程..."
            kill -9 "$pid" > /dev/null 2>&1 || true
            sleep 1
            return 0
        fi
    fi
    
    return 1
}

log_info "开始启动 MediaMTX 容器..."

# 定义需要检查的端口列表
PORTS=("8554" "1935" "8888" "8889")

log_info "检查端口占用情况..."
for port in "${PORTS[@]}"; do
    if check_and_kill_port "$port"; then
        log_info "端口 ${port} 已清理"
    fi
done

# 检查容器是否存在并停止
if docker ps -a --format '{{.Names}}' | grep -q "^mediamtx$"; then
    if docker ps --format '{{.Names}}' | grep -q "^mediamtx$"; then
        log_info "停止运行中的 MediaMTX 容器..."
        docker stop mediamtx
    fi
    log_info "删除已存在的 MediaMTX 容器..."
    docker rm mediamtx
else
    log_info "未找到已存在的 MediaMTX 容器，跳过清理步骤"
fi

# 启动 MediaMTX 容器
# 端口说明:
#   8554  - RTSP 端口
#   1935  - RTMP 端口
#   8888  - HTTP 端口
#   8889  - HTTP 端口
#   8890  - UDP 端口
#   8189  - UDP 端口
log_info "启动新的 MediaMTX 容器..."
docker run -d --name mediamtx \
  -e MTX_RTSPTRANSPORTS=tcp \
  -e MTX_WEBRTCADDITIONALHOSTS=104.198.20.50 \
  -p 8554:8554 \
  -p 1935:1935 \
  -p 8888:8888 \
  -p 8889:8889 \
  -p 8890:8890/udp \
  -p 8189:8189/udp \
  --restart unless-stopped \
  bluenviron/mediamtx

#   docker run -it --name mediamtx \
#   -e MTX_RTSPTRANSPORTS=tcp \
#   -e MTX_WEBRTCADDITIONALHOSTS=104.198.20.50 \
#   -p 8554:8554 \
#   -p 1935:1935 \
#   -p 8888:8888 \
#   -p 8889:8889 \
#   -p 8890:8890/udp \
#   -p 8189:8189/udp \
#   --restart unless-stopped \
#   bluenviron/mediamtx

# 等待容器启动
log_info "等待容器启动..."
sleep 3

# 检查容器状态
if docker ps --format '{{.Names}}' | grep -q "^mediamtx$"; then
    log_info "MediaMTX 容器启动成功！"
    log_info "HTTP 访问地址: http://localhost:8888"
    log_info "RTSP 端口: 8554"
    log_info "RTMP 端口: 1935"
    docker ps --filter "name=mediamtx" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    log_error "MediaMTX 容器启动失败，请检查日志: docker logs mediamtx"
    exit 1
fi
