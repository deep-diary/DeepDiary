
#!/bin/bash

# 创建目录并进入
cd ./immich-app || { echo "❌ 进入目录失败"; exit 1; }
sudo docker compose up -d
