#!/bin/bash
# Bash 脚本：同步主仓库和子模块
# 用法: ./scripts/sync-with-submodules.sh

echo "正在同步主仓库和子模块..."

# 1. 拉取主仓库更新
echo ""
echo "[1/3] 拉取主仓库更新..."
git pull

if [ $? -ne 0 ]; then
    echo "主仓库拉取失败，请检查网络连接或权限"
    exit 1
fi

# 2. 初始化并更新所有子模块
echo ""
echo "[2/3] 更新子模块..."
git submodule update --init --recursive

if [ $? -ne 0 ]; then
    echo "子模块更新失败"
    exit 1
fi

# 3. 显示子模块状态
echo ""
echo "[3/3] 子模块状态:"
git submodule status

echo ""
echo "同步完成！"

