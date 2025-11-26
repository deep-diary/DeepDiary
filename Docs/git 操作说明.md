git submodule add git@github.com:deep-diary/xiaozhi-esp32.git xiaozhi-esp32
cd xiaozhi-esp32
git remote add upstream git@github.com:78/xiaozhi-esp32.git
git pull upstream main
git push origin main

git checkout -b dev



# 3. 如果有冲突，解决后：
# git add .
# git commit -m "解决合并冲突"

# 4. 推送到你的Fork
git push origin main


git submodule add git@github.com:deep-diary/xiaozhi-esp32-server.git DeepServer/xiaozhi-esp32-server
# 添加上游仓库（原始仓库）作为remote
git remote add upstream https://github.com/xinnan-tech/xiaozhi-esp32-server.git
git pull upstream main
git push origin main
git checkout -b dev