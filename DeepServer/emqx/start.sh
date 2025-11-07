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

log_info "开始启动 EMQX 容器..."

# 检查容器是否存在并停止
if docker ps -a --format '{{.Names}}' | grep -q "^emqx$"; then
    if docker ps --format '{{.Names}}' | grep -q "^emqx$"; then
        log_info "停止运行中的 EMQX 容器..."
        docker stop emqx
    fi
    log_info "删除已存在的 EMQX 容器..."
    docker rm emqx
else
    log_info "未找到已存在的 EMQX 容器，跳过清理步骤"
fi

# 启动 EMQX 容器
# 端口说明:
#   1883  - MQTT TCP 端口
#   8083  - MQTT WebSocket 端口
#   8084  - MQTT WebSocket SSL 端口
#   8883  - MQTT SSL 端口
#   18083 - Dashboard Web 管理界面端口
log_info "启动新的 EMQX 容器..."
docker run -d --name emqx \
  -p 1883:1883 \
  -p 8083:8083 \
  -p 8084:8084 \
  -p 8883:8883 \
  -p 18083:18083 \
  --restart unless-stopped \
  emqx/emqx-enterprise:latest

# 等待容器启动
log_info "等待容器启动..."
sleep 3

# 检查容器状态
if docker ps --format '{{.Names}}' | grep -q "^emqx$"; then
    log_info "EMQX 容器启动成功！"
    log_info "Dashboard 访问地址: http://localhost:18083"
    log_info "默认用户名: admin"
    log_info "默认密码: public"
    docker ps --filter "name=emqx" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    log_error "EMQX 容器启动失败，请检查日志: docker logs emqx"
    exit 1
fi
