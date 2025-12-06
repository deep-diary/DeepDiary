
#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    print_error "未找到 docker 命令，请先安装 Docker"
    exit 1
fi

# 检查 Docker 服务是否运行
if ! docker info &> /dev/null; then
    print_error "Docker 服务未运行"
    print_info "请启动 Docker Desktop (macOS) 或运行: sudo systemctl start docker (Linux)"
    exit 1
fi

# 检查 docker compose 是否可用
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif docker-compose version &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    print_error "未找到 docker compose 命令"
    exit 1
fi

# 检查目录是否存在
if [ ! -d "./immich-app" ]; then
    print_error "未找到 immich-app 目录"
    print_info "请先运行 ./deploy.sh 进行部署"
    exit 1
fi

# 进入目录
cd ./immich-app || { print_error "进入目录失败"; exit 1; }

# 检查必要文件
if [ ! -f "docker-compose.yml" ]; then
    print_error "未找到 docker-compose.yml 文件"
    exit 1
fi

if [ ! -f ".env" ]; then
    print_warning "未找到 .env 文件，将使用默认配置"
fi

# 启动服务
print_info "正在启动 Immich 服务..."
if $DOCKER_COMPOSE up -d; then
    print_success "服务启动成功！"
    print_info "等待服务就绪..."
    sleep 3
    
    # 显示服务状态
    print_info "服务状态："
    $DOCKER_COMPOSE ps
    
    print_success "Immich 已启动！"
    print_info "访问地址: http://localhost:2283"
else
    print_error "服务启动失败"
    print_info "查看日志: $DOCKER_COMPOSE logs"
    exit 1
fi
