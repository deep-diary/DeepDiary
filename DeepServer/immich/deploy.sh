
#!/bin/bash

# 检测可用的下载工具（兼容 macOS 和 Linux）
if command -v wget &> /dev/null; then
    USE_WGET=true
elif command -v curl &> /dev/null; then
    USE_WGET=false
else
    echo "❌ 未找到 wget 或 curl，请先安装其中一个工具"
    echo "   macOS: curl 已内置，无需安装"
    echo "   Linux: sudo apt-get install wget 或 sudo yum install wget"
    exit 1
fi

# 下载文件的函数
download_file() {
    local url=$1
    local output=$2
    local filename=$(basename "$output")
    
    echo "正在下载 $filename..."
    
    if [ "$USE_WGET" = true ]; then
        # 使用 wget（Linux 常用）
        wget -q --show-progress -O "$output" "$url"
    else
        # 使用 curl（macOS 和 Linux 都支持）
        curl -L# -o "$output" "$url"
    fi
    
    if [ $? -ne 0 ]; then
        echo "❌ 下载 $filename 失败"
        return 1
    fi
    return 0
}

# 创建目录并进入
mkdir -p ./immich-app
cd ./immich-app || { echo "❌ 进入目录失败"; exit 1; }

# 下载docker-compose.yml
download_file "https://github.com/immich-app/immich/releases/latest/download/docker-compose.yml" "docker-compose.yml" || exit 1

# 下载example.env并重命名为.env
download_file "https://github.com/immich-app/immich/releases/latest/download/example.env" "example.env" || exit 1
mv example.env .env || { echo "❌ 重命名.env文件失败"; exit 1; }

# 验证文件
if [ -f "docker-compose.yml" ] && [ -f ".env" ]; then
    echo -e "\n✅ 部署文件准备完成！"
    echo "当前目录: $(pwd)"
    ls -l
else
    echo "❌ 文件验证失败，请检查下载过程"
    exit 1
fi
