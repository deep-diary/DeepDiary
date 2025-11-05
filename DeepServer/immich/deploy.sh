
#!/bin/bash

# 创建目录并进入
mkdir -p ./immich-app
cd ./immich-app || { echo "❌ 进入目录失败"; exit 1; }

# 下载docker-compose.yml
echo "正在下载docker-compose.yml..."
wget -q --show-progress -O docker-compose.yml https://github.com/immich-app/immich/releases/latest/download/docker-compose.yml || { echo "❌ 下载docker-compose.yml失败"; exit 1; }

# 下载example.env并重命名为.env
echo "正在下载.env配置文件..."
wget -q --show-progress -O example.env https://github.com/immich-app/immich/releases/latest/download/example.env || { echo "❌ 下载example.env失败"; exit 1; }
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
