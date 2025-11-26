#!/bin/bash
# 子模块初始化脚本
# 用于在demo项目中设置子模块的本地修改分支

echo "初始化子模块..."

# 初始化并更新子模块
git submodule update --init --recursive

# 进入项目A子模块
cd libs/xiaozhi-esp32-server
if ! git rev-parse --verify local-customizations >/dev/null 2>&1; then
    echo "创建项目A的本地自定义分支..."
    git checkout -b local-customizations
else
    echo "切换到项目A的本地自定义分支..."
    git checkout local-customizations
fi
cd ../..

# 进入项目B子模块
cd libs/xiaozhi-other
if ! git rev-parse --verify local-customizations >/dev/null 2>&1; then
    echo "创建项目B的本地自定义分支..."
    git checkout -b local-customizations
else
    echo "切换到项目B的本地自定义分支..."
    git checkout local-customizations
fi
cd ../..

echo "子模块初始化完成！"
echo "现在你可以在子模块中进行修改，这些修改只会保存在本地分支中。"

