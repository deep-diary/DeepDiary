#!/bin/bash
# DeepServer 启动脚本
# 用于启动 Django 开发服务器，监听所有网络接口

cd "$(dirname "$0")"

# 设置环境变量（如果需要）
export USE_DOCKER="${USE_DOCKER:-no}"

# 获取服务器 IP（如果可用）
SERVER_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "")

# 设置额外的允许的主机
if [ -n "$SERVER_IP" ]; then
    export DJANGO_ADDITIONAL_HOSTS="$SERVER_IP"
fi

echo "=========================================="
echo "启动 DeepServer Django 开发服务器"
echo "=========================================="
echo "监听地址: 0.0.0.0:8000"
echo "本地访问: http://127.0.0.1:8000"
if [ -n "$SERVER_IP" ]; then
    echo "外部访问: http://${SERVER_IP}:8000"
fi
echo "=========================================="
echo ""

# 启动 Django 开发服务器，监听所有网络接口
uv run python manage.py runserver 0.0.0.0:8000

