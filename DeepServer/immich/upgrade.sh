#!/bin/bash

# Immich 自动升级脚本
# 功能：自动升级 Immich 到最新版本，并清理旧镜像

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 检查是否在正确的目录
IMMICH_DIR="./immich-app"
if [ ! -d "$IMMICH_DIR" ]; then
    print_error "未找到 immich-app 目录，请先运行 deploy.sh 进行部署"
    exit 1
fi

cd "$IMMICH_DIR" || { print_error "进入目录失败"; exit 1; }

# 检查必要文件
if [ ! -f "docker-compose.yml" ]; then
    print_error "未找到 docker-compose.yml 文件"
    exit 1
fi

if [ ! -f ".env" ]; then
    print_warning "未找到 .env 文件，将使用默认配置"
fi

print_info "开始升级 Immich..."

# 检查 docker 和 docker compose 是否可用
if ! command -v docker &> /dev/null; then
    print_error "未找到 docker 命令，请先安装 Docker"
    exit 1
fi

if ! docker compose version &> /dev/null && ! docker-compose version &> /dev/null; then
    print_error "未找到 docker compose 命令，请先安装 Docker Compose"
    exit 1
fi

# 确定使用 docker compose 还是 docker-compose
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

# 显示当前版本（如果 .env 中有 IMMICH_VERSION）
if [ -f ".env" ]; then
    CURRENT_VERSION=$(grep "^IMMICH_VERSION=" .env 2>/dev/null | cut -d'=' -f2 || echo "未设置")
    if [ -n "$CURRENT_VERSION" ] && [ "$CURRENT_VERSION" != "未设置" ]; then
        print_info "当前配置的版本: $CURRENT_VERSION"
    fi
fi

# 备份提示
print_warning "建议在升级前备份数据库！"
read -p "是否已备份数据库？(y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "请确保已备份数据库后再继续"
    read -p "继续升级？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "升级已取消"
        exit 0
    fi
fi

# 拉取最新镜像
print_info "正在拉取最新镜像..."
if $DOCKER_COMPOSE pull; then
    print_success "镜像拉取完成"
else
    print_error "镜像拉取失败"
    exit 1
fi

# 重启服务
print_info "正在重启服务..."
if $DOCKER_COMPOSE up -d; then
    print_success "服务重启完成"
else
    print_error "服务重启失败"
    exit 1
fi

# 等待服务启动
print_info "等待服务启动..."
sleep 5

# 检查服务状态
print_info "检查服务状态..."
if $DOCKER_COMPOSE ps | grep -q "Up"; then
    print_success "服务运行正常"
else
    print_warning "部分服务可能未正常启动，请检查日志: $DOCKER_COMPOSE logs"
fi

# 询问是否清理旧镜像
print_info "升级完成！"
read -p "是否清理未使用的 Docker 镜像以释放空间？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "正在清理未使用的镜像..."
    docker image prune -f
    print_success "镜像清理完成"
fi

print_success "Immich 升级完成！"
print_info "如果遇到问题，请查看日志: $DOCKER_COMPOSE logs"
print_info "或访问 https://docs.immich.app/install/upgrading 查看升级文档"

