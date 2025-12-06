#!/bin/bash
# 声纹识别数据库初始化脚本
# 用于创建声纹识别所需的数据库和表

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
CONTAINER_NAME="xiaozhi-esp32-server-db"
MYSQL_USER="root"
MYSQL_PASSWORD="123456"
MYSQL_DATABASE="voiceprint_db"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL_FILE="${SCRIPT_DIR}/create_voiceprint_db.sql"

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    print_info "Docker 已安装"
}

# 检查 MySQL 容器是否运行
check_container() {
    print_info "检查 MySQL 容器状态..."
    
    if ! docker ps --format "{{.Names}}" | grep -q "^${CONTAINER_NAME}$"; then
        print_error "MySQL 容器 '${CONTAINER_NAME}' 未运行"
        print_warn "请先启动 MySQL 容器："
        echo "  docker start ${CONTAINER_NAME}"
        echo "  或者使用 docker-compose 启动服务"
        exit 1
    fi
    
    print_info "MySQL 容器 '${CONTAINER_NAME}' 正在运行"
}

# 检查容器健康状态
check_container_health() {
    print_info "检查容器健康状态..."
    
    local health_status=$(docker inspect --format='{{.State.Health.Status}}' ${CONTAINER_NAME} 2>/dev/null || echo "none")
    
    if [ "$health_status" = "healthy" ]; then
        print_info "容器健康状态：healthy"
        return 0
    elif [ "$health_status" = "starting" ]; then
        print_warn "容器正在启动中，等待健康检查..."
        # 等待最多 60 秒
        local max_wait=60
        local waited=0
        while [ $waited -lt $max_wait ]; do
            sleep 2
            waited=$((waited + 2))
            health_status=$(docker inspect --format='{{.State.Health.Status}}' ${CONTAINER_NAME} 2>/dev/null || echo "none")
            if [ "$health_status" = "healthy" ]; then
                print_info "容器已就绪"
                return 0
            fi
            echo -n "."
        done
        echo
        print_warn "容器健康检查超时，但继续尝试连接..."
    else
        print_warn "容器健康状态：${health_status}，继续尝试连接..."
    fi
}

# 检查 MySQL 服务是否可访问
check_mysql_connection() {
    print_info "检查 MySQL 服务连接..."
    
    # 尝试连接 MySQL
    if docker exec ${CONTAINER_NAME} mysqladmin ping -h localhost -u ${MYSQL_USER} -p${MYSQL_PASSWORD} --silent 2>/dev/null; then
        print_info "MySQL 服务连接成功"
        return 0
    else
        print_error "无法连接到 MySQL 服务"
        print_warn "请检查："
        echo "  1. MySQL 容器是否正常运行"
        echo "  2. MySQL 用户名和密码是否正确"
        echo "  3. MySQL 服务是否已完全启动"
        exit 1
    fi
}

# 检查 SQL 文件是否存在
check_sql_file() {
    if [ ! -f "${SQL_FILE}" ]; then
        print_error "SQL 文件不存在: ${SQL_FILE}"
        exit 1
    fi
    print_info "SQL 文件已找到: ${SQL_FILE}"
}

# 执行 SQL 脚本
execute_sql() {
    print_info "开始执行 SQL 脚本..."
    
    if docker exec -i ${CONTAINER_NAME} mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} < "${SQL_FILE}" 2>&1; then
        print_info "SQL 脚本执行成功"
        return 0
    else
        print_error "SQL 脚本执行失败"
        exit 1
    fi
}

# 验证数据库和表是否创建成功
verify_database() {
    print_info "验证数据库和表..."
    
    # 检查数据库是否存在
    if docker exec ${CONTAINER_NAME} mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} -e "SHOW DATABASES LIKE '${MYSQL_DATABASE}';" 2>/dev/null | grep -q "${MYSQL_DATABASE}"; then
        print_info "✅ 数据库 '${MYSQL_DATABASE}' 已创建"
    else
        print_error "数据库 '${MYSQL_DATABASE}' 创建失败或不存在"
        exit 1
    fi
    
    # 检查表是否存在
    if docker exec ${CONTAINER_NAME} mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE} -e "SHOW TABLES LIKE 'voiceprints';" 2>/dev/null | grep -q "voiceprints"; then
        print_info "✅ 表 'voiceprints' 已创建"
    else
        print_error "表 'voiceprints' 创建失败或不存在"
        exit 1
    fi
    
    # 显示表结构
    print_info "表结构："
    docker exec ${CONTAINER_NAME} mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE} -e "DESCRIBE voiceprints;" 2>/dev/null || true
}

# 主函数
main() {
    echo "=========================================="
    echo "  声纹识别数据库初始化脚本"
    echo "=========================================="
    echo
    
    # 执行检查步骤
    check_docker
    check_container
    check_container_health
    check_mysql_connection
    check_sql_file
    
    echo
    print_info "所有检查通过，开始创建数据库..."
    echo
    
    # 执行 SQL 脚本
    execute_sql
    
    echo
    # 验证结果
    verify_database
    
    echo
    echo "=========================================="
    print_info "✅ 数据库初始化完成！"
    echo "=========================================="
    echo
    print_info "数据库名称: ${MYSQL_DATABASE}"
    print_info "表名: voiceprints"
    echo
    print_info "可以使用以下命令连接数据库："
    echo "  docker exec -it ${CONTAINER_NAME} mysql -u ${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE}"
}

# 运行主函数
main



