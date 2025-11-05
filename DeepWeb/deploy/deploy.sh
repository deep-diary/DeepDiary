#!/bin/bash

# Nginx 部署脚本
# 将项目的 nginx 配置部署到系统 nginx 目录

set -e  # 遇到错误立即退出

# 配置文件名
CONFIG_FILE="deep-diary.conf"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_CONFIG="${SCRIPT_DIR}/${CONFIG_FILE}"

# Nginx 配置目录
NGINX_AVAILABLE_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
TARGET_CONFIG="${NGINX_AVAILABLE_DIR}/${CONFIG_FILE}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查是否以 root 权限运行
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}错误: 请使用 sudo 运行此脚本${NC}"
    exit 1
fi

# 检查源配置文件是否存在
if [ ! -f "$SOURCE_CONFIG" ]; then
    echo -e "${RED}错误: 找不到配置文件 ${SOURCE_CONFIG}${NC}"
    exit 1
fi

# 检查 nginx 是否安装
if ! command -v nginx &> /dev/null; then
    echo -e "${RED}错误: 未找到 nginx，请先安装 nginx${NC}"
    exit 1
fi

echo -e "${GREEN}开始部署 Nginx 配置...${NC}"

# 检查并处理 default 配置冲突
DEFAULT_CONFIG="${NGINX_ENABLED_DIR}/default"
if [ -L "$DEFAULT_CONFIG" ]; then
    echo -e "${YELLOW}[检查] 检测到 default 配置已启用，检查是否有冲突...${NC}"
    if grep -q "server_name.*deep-diary.com" "${NGINX_AVAILABLE_DIR}/default" 2>/dev/null; then
        echo -e "${YELLOW}  发现冲突的 server_name，将禁用 default 配置${NC}"
        rm "$DEFAULT_CONFIG"
        echo -e "${GREEN}✓ default 配置已禁用${NC}"
    fi
fi

# 1. 拷贝配置文件到 sites-available
echo -e "${YELLOW}[1/4] 拷贝配置文件到 ${NGINX_AVAILABLE_DIR}${NC}"
cp "$SOURCE_CONFIG" "$TARGET_CONFIG"
echo -e "${GREEN}✓ 配置文件已拷贝${NC}"

# 2. 创建软链接到 sites-enabled
echo -e "${YELLOW}[2/4] 创建软链接到 ${NGINX_ENABLED_DIR}${NC}"
# 如果已存在软链接，先删除
if [ -L "${NGINX_ENABLED_DIR}/${CONFIG_FILE}" ]; then
    rm "${NGINX_ENABLED_DIR}/${CONFIG_FILE}"
    echo -e "${YELLOW}  移除旧的软链接${NC}"
fi
ln -s "$TARGET_CONFIG" "${NGINX_ENABLED_DIR}/${CONFIG_FILE}"
echo -e "${GREEN}✓ 软链接已创建${NC}"

# 3. 测试 Nginx 配置
echo -e "${YELLOW}[3/4] 测试 Nginx 配置...${NC}"
TEST_OUTPUT=$(nginx -t 2>&1)
TEST_STATUS=$?

if [ $TEST_STATUS -eq 0 ]; then
    echo -e "${GREEN}✓ 配置测试通过${NC}"
    # 检查是否有警告
    if echo "$TEST_OUTPUT" | grep -q "conflicting server name"; then
        echo -e "${YELLOW}⚠ 警告: 检测到 server_name 冲突${NC}"
        echo -e "${YELLOW}  请检查 /etc/nginx/sites-enabled/ 目录下的其他配置文件${NC}"
    fi
else
    echo -e "${RED}✗ 配置测试失败，请检查配置文件${NC}"
    echo "$TEST_OUTPUT"
    exit 1
fi

# 4. 重新加载 Nginx
echo -e "${YELLOW}[4/4] 重新加载 Nginx...${NC}"
if systemctl reload nginx 2>/dev/null || nginx -s reload 2>/dev/null; then
    echo -e "${GREEN}✓ Nginx 已重新加载${NC}"
else
    echo -e "${RED}✗ Nginx 重新加载失败${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}部署完成！${NC}"
echo -e "${GREEN}配置文件: ${TARGET_CONFIG}${NC}"
echo -e "${GREEN}软链接: ${NGINX_ENABLED_DIR}/${CONFIG_FILE}${NC}"
echo -e "${GREEN}========================================${NC}"
