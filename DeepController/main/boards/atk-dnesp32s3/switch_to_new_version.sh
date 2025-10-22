#!/bin/bash

# 板级代码切换脚本
# 用于在旧版本（单一文件）和新版本（扩展分离）之间切换

set -e  # 遇到错误立即退出

BOARD_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$BOARD_DIR"

echo "========================================="
echo "  板级代码版本切换工具"
echo "========================================="
echo ""

# 检查文件是否存在
if [ ! -f "atk_dnesp32s3.cc" ]; then
    echo "❌ 错误：找不到 atk_dnesp32s3.cc"
    exit 1
fi

if [ ! -f "atk_dnesp32s3_minimal.cc" ]; then
    echo "❌ 错误：找不到 atk_dnesp32s3_minimal.cc"
    exit 1
fi

if [ ! -f "board_extensions.cc" ] || [ ! -f "board_extensions.h" ]; then
    echo "❌ 错误：找不到扩展文件"
    exit 1
fi

# 检查当前版本
CURRENT_LINES=$(wc -l < atk_dnesp32s3.cc | tr -d ' ')

if [ "$CURRENT_LINES" -gt 500 ]; then
    CURRENT_VERSION="旧版本（单一文件）"
    NEW_VERSION="新版本（扩展分离）"
    ACTION="切换到新版本"
else
    CURRENT_VERSION="新版本（扩展分离）"
    NEW_VERSION="旧版本（单一文件）"
    ACTION="回退到旧版本"
fi

echo "当前版本：$CURRENT_VERSION"
echo "目标版本：$NEW_VERSION"
echo ""

# 确认操作
read -p "确定要$ACTION吗？(y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 操作已取消"
    exit 0
fi

echo ""
echo "开始切换..."

# 备份当前文件
BACKUP_FILE="atk_dnesp32s3_backup_$(date +%Y%m%d_%H%M%S).cc"
cp atk_dnesp32s3.cc "$BACKUP_FILE"
echo "✅ 已备份当前文件到：$BACKUP_FILE"

# 执行切换
if [ "$CURRENT_LINES" -gt 500 ]; then
    # 切换到新版本
    mv atk_dnesp32s3.cc atk_dnesp32s3_old.cc
    mv atk_dnesp32s3_minimal.cc atk_dnesp32s3.cc
    echo "✅ 已切换到新版本（扩展分离）"
    echo ""
    echo "📝 新版本特点："
    echo "  - 主文件简洁（~150行）"
    echo "  - 扩展功能独立管理"
    echo "  - 易于升级开源项目"
    echo ""
    echo "📚 相关文档："
    echo "  - UPGRADE_GUIDE.md - 升级指南"
    echo "  - CODE_COMPARISON.md - 代码对比"
else
    # 回退到旧版本
    mv atk_dnesp32s3.cc atk_dnesp32s3_minimal.cc
    mv atk_dnesp32s3_old.cc atk_dnesp32s3.cc
    echo "✅ 已回退到旧版本（单一文件）"
    echo ""
    echo "⚠️  注意：旧版本不便于升级开源项目"
    echo "建议：重新切换到新版本"
fi

echo ""
echo "========================================="
echo "  切换完成"
echo "========================================="
echo ""
echo "下一步："
echo "  1. cd 到项目根目录"
echo "  2. 运行：idf.py build"
echo "  3. 测试所有功能"
echo ""
echo "回退方案："
echo "  如果有问题，可以恢复备份文件："
echo "  cp $BACKUP_FILE atk_dnesp32s3.cc"
echo ""

