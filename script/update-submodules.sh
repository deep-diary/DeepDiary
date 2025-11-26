#!/bin/bash
# 更新子模块脚本
# 用于定期从上游拉取最新代码并合并到本地修改分支

echo "开始更新子模块..."

# 更新项目A
echo "更新项目A (xiaozhi-esp32-server)..."
cd libs/xiaozhi-esp32-server

# 确保在本地修改分支
git checkout local-customizations

# 获取上游更新
git fetch origin

# 查看当前分支和上游的差异
echo "检查上游更新..."
git log HEAD..origin/main --oneline

# 询问是否合并（可以改为自动合并）
read -p "是否合并上游更新到本地分支? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "合并上游更新..."
    git merge origin/main --no-edit
    
    # 如果有冲突，提示解决
    if [ $? -ne 0 ]; then
        echo "⚠️  检测到合并冲突，请手动解决："
        echo "   1. 进入 libs/xiaozhi-esp32-server 目录"
        echo "   2. 解决冲突文件"
        echo "   3. git add . && git commit"
        exit 1
    fi
    
    echo "✅ 项目A更新完成"
else
    echo "跳过项目A的更新"
fi

cd ../..

# 更新项目B
echo "更新项目B..."
cd libs/xiaozhi-other

# 确保在本地修改分支
git checkout local-customizations

# 获取上游更新
git fetch origin

# 查看当前分支和上游的差异
echo "检查上游更新..."
git log HEAD..origin/main --oneline

# 询问是否合并
read -p "是否合并上游更新到本地分支? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "合并上游更新..."
    git merge origin/main --no-edit
    
    # 如果有冲突，提示解决
    if [ $? -ne 0 ]; then
        echo "⚠️  检测到合并冲突，请手动解决："
        echo "   1. 进入 libs/xiaozhi-other 目录"
        echo "   2. 解决冲突文件"
        echo "   3. git add . && git commit"
        exit 1
    fi
    
    echo "✅ 项目B更新完成"
else
    echo "跳过项目B的更新"
fi

cd ../..

# 更新demo项目中的子模块引用
echo "更新demo项目中的子模块引用..."
git add libs/
git commit -m "更新子模块到最新版本" || echo "没有需要提交的更改"

echo "✅ 所有子模块更新完成！"

