# Git Submodule 操作指南

## 一、项目当前配置

### 当前子模块配置

根据 `.gitmodules` 文件，项目包含以下子模块：

```ini
[submodule "xiaozhi-esp32"]
    path = xiaozhi-esp32
    url = git@github.com:deep-diary/xiaozhi-esp32.git

[submodule "DeepServer/xiaozhi-esp32-server"]
    path = DeepServer/xiaozhi-esp32-server
    url = git@github.com:deep-diary/xiaozhi-esp32-server.git
```

### 项目结构

```
DeepDiary/
├── .gitmodules                    # 子模块配置文件
├── xiaozhi-esp32/                 # 子模块1
│   └── .git/                      # 子模块的Git配置
└── DeepServer/
    └── xiaozhi-esp32-server/      # 子模块2
        └── .git/                  # 子模块的Git配置
```

## 二、基本概念

### 什么是 Git Submodule？

Git Submodule（子模块）允许你将一个 Git 仓库作为另一个 Git 仓库的子目录。这样可以：

- ✅ 在主项目中包含并使用其他项目的代码
- ✅ 保持这些项目的独立版本控制
- ✅ 可以随时更新到最新版本
- ✅ 可以修改子模块代码而不影响原始仓库

### 核心概念

- **主项目（Super Project）**：包含子模块的项目（DeepDiary）
- **子模块（Submodule）**：被包含的独立 Git 仓库（xiaozhi-esp32、xiaozhi-esp32-server）
- **引用关系**：主项目只保存子模块的特定 commit 引用，不保存实际代码

### 工作原理

1. 主项目**不保存子模块的代码**，只保存：

   - 子模块的 commit SHA（在 `.git/modules/` 中记录）
   - 子模块的路径和 URL（在 `.gitmodules` 中记录）

2. 子模块是**独立的 Git 仓库**，有自己的：
   - `.git` 目录
   - 完整的提交历史
   - 远程仓库配置

## 三、常用操作

### 3.1 克隆包含子模块的项目

#### 方式 1：克隆时自动初始化子模块（推荐）

```bash
git clone --recurse-submodules git@github.com:deep-diary/DeepDiary.git
```

#### 方式 2：先克隆，再初始化子模块

```bash
# 克隆主项目
git clone git@github.com:deep-diary/DeepDiary.git
cd DeepDiary

# 初始化并更新所有子模块
git submodule update --init --recursive
```

### 3.2 查看子模块状态

```bash
# 查看所有子模块的状态
git submodule status

# 输出示例：
#  abc1234 xiaozhi-esp32 (v1.0.0)
#  def5678 DeepServer/xiaozhi-esp32-server (v2.1.0)
```

**状态前缀说明**：

- 无前缀：子模块已初始化且指向正确的 commit
- `-`：子模块未初始化
- `+`：子模块的 commit 与主项目记录的不同
- `U`：子模块有合并冲突

### 3.3 更新子模块

#### 更新到主项目记录的版本

```bash
# 更新所有子模块到主项目记录的版本
git submodule update

# 更新特定子模块
git submodule update xiaozhi-esp32
```

#### 更新到远程最新版本

```bash
# 更新所有子模块到远程最新版本
git submodule update --remote

# 更新特定子模块
git submodule update --remote DeepServer/xiaozhi-esp32-server
```

### 3.4 进入子模块进行操作

子模块是独立的 Git 仓库，可以像普通仓库一样操作：

```bash
# 进入子模块目录
cd xiaozhi-esp32

# 查看状态
git status

# 查看分支
git branch -a

# 创建新分支
git checkout -b dev

# 进行修改
vim some_file.py
git add .
git commit -m "修改子模块代码"

# 返回主项目
cd ..
```

### 3.5 在主项目中提交子模块引用更新

当子模块有新的提交后，需要在主项目中更新引用：

```bash
# 查看主项目状态
git status

# 输出示例：
# Changes not staged for commit:
#   modified:   xiaozhi-esp32 (new commits)

# 提交子模块的引用更新
git add xiaozhi-esp32
git commit -m "更新子模块 xiaozhi-esp32 的引用"

# 推送到远程
git push origin main
```

## 四、针对当前项目的操作示例

### 4.1 初始化项目（首次克隆后）

```bash
# 克隆项目
git clone --recurse-submodules git@github.com:deep-diary/DeepDiary.git
cd DeepDiary

# 如果子模块未初始化，执行：
git submodule update --init --recursive
```

### 4.2 修改 xiaozhi-esp32 子模块

```bash
# 进入子模块
cd xiaozhi-esp32

# 创建或切换到开发分支
git checkout -b dev

# 进行修改
vim some_file.cpp
git add .
git commit -m "修改 xiaozhi-esp32 代码"

# 推送到远程（如果有权限）
git push origin dev

# 返回主项目
cd ..

# 更新主项目中的子模块引用
git add xiaozhi-esp32
git commit -m "更新 xiaozhi-esp32 子模块"
git push origin main
```

### 4.3 修改 xiaozhi-esp32-server 子模块

```bash
# 进入子模块
cd DeepServer/xiaozhi-esp32-server

# 创建或切换到开发分支
git checkout -b dev

# 进行修改
vim main/xiaozhi-server/some_file.py
git add .
git commit -m "修改 xiaozhi-esp32-server 代码"

# 推送到远程（如果有权限）
git push origin dev

# 返回主项目
cd ../..

# 更新主项目中的子模块引用
git add DeepServer/xiaozhi-esp32-server
git commit -m "更新 xiaozhi-esp32-server 子模块"
git push origin main
```

### 4.4 同步上游更新（如果配置了 upstream）

如果子模块配置了上游仓库（upstream），可以同步上游更新：

```bash
# 进入子模块
cd xiaozhi-esp32

# 检查是否配置了 upstream
git remote -v

# 如果没有 upstream，添加它（示例）
# git remote add upstream git@github.com:xinnan-tech/xiaozhi-esp32-server.git
# git remote add upstream git@github.com:78/xiaozhi-esp32.git

# 获取上游更新
git fetch upstream

# 合并上游更新
git merge upstream/main

# 如果有冲突，解决后：
# git add .
# git commit -m "解决合并冲突"

# 推送到你的仓库
git push origin dev

# 返回主项目并更新引用
cd ..
git add xiaozhi-esp32
git commit -m "同步 xiaozhi-esp32 上游更新"
git push origin main
```

### 4.5 批量更新所有子模块

```bash
# 方式1：使用 foreach 命令
git submodule foreach 'git pull origin main'

# 方式2：使用 update --remote
git submodule update --remote

# 然后提交主项目的引用更新
git add .
git commit -m "更新所有子模块"
git push origin main
```

## 五、重要注意事项

### 5.1 子模块修改必须推送到远程

⚠️ **关键**：如果子模块有本地修改，必须推送到子模块的远程仓库，否则团队成员无法获取。

```bash
# ❌ 错误做法：只提交到本地
cd xiaozhi-esp32
git commit -m "本地修改"
# 没有执行 git push
cd ..
git add xiaozhi-esp32
git commit -m "更新子模块"
git push origin main
# 结果：团队成员无法获取你的修改

# ✅ 正确做法：推送到远程
cd xiaozhi-esp32
git commit -m "本地修改"
git push origin dev  # 推送到子模块的远程仓库
cd ..
git add xiaozhi-esp32
git commit -m "更新子模块"
git push origin main
# 结果：团队成员可以获取你的修改
```

### 5.2 检查子模块 commit 是否在远程

```bash
# 进入子模块
cd xiaozhi-esp32

# 获取当前 commit
CURRENT_COMMIT=$(git rev-parse HEAD)
echo "当前 commit: $CURRENT_COMMIT"

# 检查是否在远程仓库中
if git ls-remote origin | grep -q "$CURRENT_COMMIT"; then
    echo "✅ commit 在远程仓库中，团队成员可以获取"
else
    echo "❌ commit 只在本地，团队成员无法获取"
    echo "   需要执行: git push origin <branch>"
fi
```

### 5.3 克隆后子模块目录为空

如果克隆后子模块目录是空的，需要初始化：

```bash
git submodule update --init --recursive
```

### 5.4 拉取主项目更新后更新子模块

```bash
# 拉取主项目更新
git pull

# 如果子模块引用有更新，需要更新子模块
git submodule update
```

## 六、常用命令速查

### 查看信息

```bash
# 查看子模块状态
git submodule status

# 查看子模块配置
cat .gitmodules

# 查看子模块的详细信息
git submodule foreach 'echo $name: $(git rev-parse HEAD)'
```

### 初始化与更新

```bash
# 初始化所有子模块
git submodule init

# 初始化并更新
git submodule update --init --recursive

# 更新到主项目记录的版本
git submodule update

# 更新到远程最新版本
git submodule update --remote
```

### 批量操作

```bash
# 在所有子模块中执行命令
git submodule foreach git status
git submodule foreach git pull origin main
git submodule foreach 'git checkout -b feature-branch'
```

### 同步配置

```bash
# 同步 .gitmodules 到 .git/config
git submodule sync

# 同步并更新
git submodule sync --recursive
git submodule update --init --recursive
```

## 七、最佳实践

### 7.1 分支管理

在子模块中使用独立分支进行修改：

```bash
cd xiaozhi-esp32
# 创建本地分支并跟踪远程分支
git checkout -b dev origin/dev
# 进行修改...
git commit -m "修改"
git push origin dev
```

### 7.2 定期更新

定期同步子模块的上游更新：

```bash
# 创建更新脚本
#!/bin/bash
# update-submodules.sh

cd xiaozhi-esp32
git fetch origin
git merge origin/main
cd ..

cd DeepServer/xiaozhi-esp32-server
git fetch origin
git merge origin/main
cd ../..

git add .
git commit -m "同步所有子模块的上游更新"
git push origin main
```

### 7.3 文档记录

在 README 中说明：

- 项目使用了哪些子模块
- 如何初始化和更新子模块
- 子模块的用途和版本要求

### 7.4 团队协作

确保团队成员了解：

- 克隆项目时使用 `--recurse-submodules`
- 拉取更新后需要执行 `git submodule update`
- 修改子模块后需要推送到子模块的远程仓库

## 八、常见问题解答

### Q1: 为什么克隆后子模块目录是空的？

**A**: 需要初始化子模块：

```bash
git submodule update --init --recursive
```

### Q2: 如何查看子模块的状态？

```bash
git submodule status
```

### Q3: 子模块可以指向不同的分支吗？

**A**: 可以，在 `.gitmodules` 中配置：

```ini
[submodule "xiaozhi-esp32"]
    path = xiaozhi-esp32
    url = git@github.com:deep-diary/xiaozhi-esp32.git
    branch = dev
```

然后使用：

```bash
git submodule update --remote
```

### Q4: 如何批量更新所有子模块？

```bash
git submodule foreach git pull origin main
```

或者：

```bash
git submodule update --remote
```

### Q5: 子模块的修改会推送到原始仓库吗？

**A**: 不会，除非你：

1. 进入子模块目录
2. 有原始仓库的推送权限
3. 主动执行 `git push`

### Q6: 如何查看子模块的修改历史？

```bash
cd xiaozhi-esp32
git log
git diff origin/main..HEAD
```

### Q7: 如何删除子模块？

```bash
# 1. 从 .gitmodules 中删除配置
git submodule deinit -f xiaozhi-esp32

# 2. 从 .git/config 中删除配置
git rm --cached xiaozhi-esp32

# 3. 删除 .git/modules 中的配置
rm -rf .git/modules/xiaozhi-esp32

# 4. 删除工作目录
rm -rf xiaozhi-esp32

# 5. 提交更改
git commit -m "删除子模块 xiaozhi-esp32"
```

## 九、工作流程示例

### 日常开发流程

```bash
# 1. 拉取主项目更新
git pull

# 2. 更新子模块
git submodule update

# 3. 进入子模块进行开发
cd xiaozhi-esp32
git checkout dev
# 进行修改...
git add .
git commit -m "功能开发"
git push origin dev

# 4. 返回主项目，更新引用
cd ..
git add xiaozhi-esp32
git commit -m "更新子模块"
git push origin main
```

### 同步上游更新流程

```bash
# 1. 进入子模块
cd xiaozhi-esp32

# 2. 获取上游更新
git fetch upstream  # 如果配置了 upstream
# 或
git fetch origin


# 1. 进入子模块目录
cd DeepServer/xiaozhi-esp32-server

# 2. 确保在正确的分支（比如 dev）
git checkout main

# 3. 获取 upstream 的最新更新
git fetch upstream

# 4. 查看是否有新提交
git log HEAD..upstream/main --oneline

# 5. 如果有新提交，查看具体变化
git diff --stat HEAD..upstream/main

# 6. 查看详细的代码差异（可选）
git diff HEAD..upstream/main

# 7. 如果决定合并，执行合并
git merge upstream/main

# 3. 合并更新
git merge upstream/main
# 或
git merge origin/main

# 4. 解决冲突（如果有）
# git add .
# git commit -m "解决冲突"

# 5. 推送到你的仓库
git push origin dev

# 6. 更新主项目引用
cd ..
git add xiaozhi-esp32
git commit -m "同步上游更新"
git push origin main
```

## 十、总结

### 核心要点

1. **子模块是独立的 Git 仓库**

   - 有自己的 `.git` 目录
   - 可以独立进行 Git 操作

2. **主项目只保存引用**

   - 不保存子模块的实际代码
   - 只保存 commit SHA

3. **修改必须推送到远程**

   - 子模块的修改需要推送到子模块的远程仓库
   - 否则团队成员无法获取

4. **克隆时需要初始化**
   - 使用 `--recurse-submodules` 或手动初始化

### 当前项目的子模块

- `xiaozhi-esp32`：位于项目根目录
- `DeepServer/xiaozhi-esp32-server`：位于 DeepServer 目录下

### 推荐操作流程

1. 克隆：`git clone --recurse-submodules <url>`
2. 开发：在子模块中创建分支，修改后推送到远程
3. 更新：在主项目中提交子模块引用更新
4. 同步：定期从上游拉取更新并合并

---

**提示**：如果遇到问题，先检查子模块状态 `git submodule status`，确保子模块已正确初始化和更新。
