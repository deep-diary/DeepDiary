# GitHub CLI 使用指南

基于 DeepServer 项目的 GitHub CLI (gh) 完整使用指南。

## 📚 目录

1. [安装和配置](#安装和配置)
2. [认证](#认证)
3. [仓库操作](#仓库操作)
4. [Pull Request 管理](#pull-request-管理)
5. [Issue 管理](#issue-管理)
6. [CI/CD 工作流](#cicd-工作流)
7. [Dependabot 管理](#dependabot-管理)
8. [常用工作流](#常用工作流)
9. [高级功能](#高级功能)

---

## 安装和配置

### 安装 GitHub CLI

#### Linux (Ubuntu/Debian)
```bash
# 方法 1: 使用官方脚本
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# 方法 2: 使用 snap
sudo snap install gh

# 方法 3: 使用包管理器
sudo apt install gh
```

#### macOS
```bash
brew install gh
```

#### Windows
```bash
# 使用 Chocolatey
choco install gh

# 或使用 Scoop
scoop install gh
```

### 验证安装
```bash
gh --version
```

---

## 认证

### 首次登录
```bash
# 交互式登录（推荐）
gh auth login

# 选择认证方式：
# 1. GitHub.com
# 2. HTTPS（推荐）或 SSH
# 3. 浏览器登录或使用 token
```

### 使用 Token 登录
```bash
# 从 GitHub 生成 Personal Access Token
# Settings -> Developer settings -> Personal access tokens -> Tokens (classic)
# 权限：repo, workflow, read:org

gh auth login --with-token < token.txt
```

### 检查认证状态
```bash
gh auth status
```

### 切换账户
```bash
gh auth switch
```

### 登出
```bash
gh auth logout
```

---

## 仓库操作

### 克隆仓库
```bash
# 克隆当前项目
gh repo clone <owner>/deepserver

# 或使用简短形式（如果已认证）
gh repo clone deepserver
```

### 查看仓库信息
```bash
# 查看当前仓库信息
gh repo view

# 查看特定仓库
gh repo view <owner>/deepserver

# 查看仓库的详细信息
gh repo view --web
```

### Fork 仓库
```bash
gh repo fork <owner>/deepserver
```

### 创建仓库
```bash
# 创建新的私有仓库
gh repo create my-new-repo --private

# 创建并克隆
gh repo create my-new-repo --private --clone

# 从当前目录创建
gh repo create --source=. --public --push
```

---

## Pull Request 管理

### 创建 Pull Request

#### 方法 1: 从当前分支创建
```bash
# 确保在功能分支上
git checkout -b feature/new-feature

# 提交更改
git add .
git commit -m "Add new feature"

# 推送分支
git push origin feature/new-feature

# 创建 PR（交互式）
gh pr create

# 创建 PR（命令行）
gh pr create --title "Add new feature" \
  --body "This PR adds a new feature to the project" \
  --base main \
  --head feature/new-feature
```

#### 方法 2: 快速创建（自动检测）
```bash
# 自动检测当前分支并创建 PR
gh pr create --fill
```

### 查看 Pull Request

```bash
# 列出所有 PR
gh pr list

# 查看特定 PR
gh pr view <pr-number>

# 在浏览器中打开 PR
gh pr view --web

# 查看 PR 的差异
gh pr diff <pr-number>

# 查看 PR 的检查状态
gh pr checks <pr-number>
```

### 管理 Pull Request

```bash
# 合并 PR
gh pr merge <pr-number> --squash

# 合并并删除分支
gh pr merge <pr-number> --squash --delete-branch

# 关闭 PR
gh pr close <pr-number>

# 重新打开 PR
gh pr reopen <pr-number>

# 添加评论
gh pr comment <pr-number> --body "Looks good!"

# 请求审查
gh pr review <pr-number> --approve
gh pr review <pr-number> --request-changes --body "Please fix the issues"
```

### 检查 PR 状态

```bash
# 查看当前分支的 PR 状态
gh pr status

# 查看 CI 检查结果
gh pr checks

# 查看 PR 的详细状态
gh pr view --json statusCheckRollup
```

---

## Issue 管理

### 创建 Issue

```bash
# 交互式创建
gh issue create

# 命令行创建
gh issue create \
  --title "Bug: Something is broken" \
  --body "Description of the bug" \
  --label "bug"

# 从模板创建
gh issue create --template bug_report
```

### 查看和管理 Issue

```bash
# 列出所有 issue
gh issue list

# 查看特定 issue
gh issue view <issue-number>

# 在浏览器中打开
gh issue view --web

# 关闭 issue
gh issue close <issue-number>

# 重新打开 issue
gh issue reopen <issue-number>

# 添加评论
gh issue comment <issue-number> --body "This is fixed in PR #123"

# 分配 issue
gh issue assign <issue-number> @username

# 添加标签
gh issue edit <issue-number> --add-label "enhancement"
```

### 搜索 Issue

```bash
# 搜索 open 状态的 bug
gh issue list --label "bug" --state open

# 搜索分配给自己的 issue
gh issue list --assignee @me

# 搜索包含特定关键词的 issue
gh issue list --search "authentication"
```

---

## CI/CD 工作流

### 查看工作流运行状态

```bash
# 列出所有工作流运行
gh run list

# 查看特定运行
gh run view <run-id>

# 在浏览器中查看
gh run view --web

# 查看最新的运行
gh run view

# 查看特定工作流的运行
gh run list --workflow=ci.yml
```

### 重新运行工作流

```bash
# 重新运行失败的 workflow
gh run rerun <run-id>

# 重新运行并查看日志
gh run rerun <run-id> --watch
```

### 查看工作流日志

```bash
# 查看运行日志
gh run view <run-id> --log

# 实时查看日志
gh run watch <run-id>

# 查看特定 job 的日志
gh run view <run-id> --log --job <job-id>
```

### 下载工作流产物

```bash
# 列出所有产物
gh run view <run-id> --json artifacts

# 下载产物
gh run download <run-id>
```

### 基于当前项目的 CI 工作流

根据项目的 `.github/workflows/ci.yml`，你可以：

```bash
# 查看 CI 工作流状态
gh workflow view ci.yml

# 查看 CI 运行历史
gh run list --workflow=ci.yml

# 查看最新的 CI 运行
gh run list --workflow=ci.yml --limit 1

# 查看特定 PR 的 CI 状态
gh pr checks <pr-number>
```

---

## Dependabot 管理

### 查看 Dependabot PR

```bash
# 列出所有 Dependabot PR
gh pr list --author "app/dependabot"

# 查看 Dependabot 配置
gh api repos/:owner/:repo/dependabot/alerts

# 查看依赖更新
gh pr list --label "dependencies"
```

### 管理 Dependabot PR

根据项目的 `.github/dependabot.yml` 配置：

```bash
# 批量合并 Dependabot PR（谨慎使用）
gh pr list --author "app/dependabot" --state open --json number --jq '.[].number' | \
  xargs -I {} gh pr merge {} --squash --delete-branch

# 查看 Dependabot PR 详情
gh pr view <dependabot-pr-number>
```

---

## 常用工作流

### 工作流 1: 创建功能分支并提交 PR

```bash
# 1. 创建并切换到新分支
git checkout -b feature/add-new-api

# 2. 进行开发...
# 编辑文件、提交更改
git add .
git commit -m "Add new API endpoint"

# 3. 推送分支
git push origin feature/add-new-api

# 4. 创建 PR
gh pr create --title "Add new API endpoint" \
  --body "This PR adds a new API endpoint for user management" \
  --base main

# 5. 查看 PR 状态
gh pr status
```

### 工作流 2: 检查 CI 状态并合并

```bash
# 1. 查看 PR 列表
gh pr list

# 2. 查看特定 PR 的 CI 状态
gh pr checks <pr-number>

# 3. 如果 CI 通过，合并 PR
gh pr merge <pr-number> --squash --delete-branch

# 4. 更新本地 main 分支
git checkout main
git pull origin main
```

### 工作流 3: 处理 Issue 并创建修复 PR

```bash
# 1. 查看 open 的 issue
gh issue list --state open

# 2. 查看特定 issue
gh issue view <issue-number>

# 3. 创建修复分支
git checkout -b fix/issue-<issue-number>

# 4. 修复问题并提交
git add .
git commit -m "Fix issue #<issue-number>: <description>"

# 5. 推送并创建 PR
git push origin fix/issue-<issue-number>
gh pr create --title "Fix issue #<issue-number>" \
  --body "Closes #<issue-number>" \
  --base main

# 6. PR 合并后，issue 会自动关闭
```

### 工作流 4: 查看和管理 CI 运行

```bash
# 1. 查看最新的 CI 运行
gh run list --limit 5

# 2. 查看特定运行的详细信息
gh run view <run-id>

# 3. 查看运行日志
gh run view <run-id> --log

# 4. 如果失败，重新运行
gh run rerun <run-id>

# 5. 实时查看运行状态
gh run watch <run-id>
```

### 工作流 5: 代码审查

```bash
# 1. 查看需要审查的 PR
gh pr list --review-requested @me

# 2. 查看 PR 详情
gh pr view <pr-number>

# 3. 查看代码差异
gh pr diff <pr-number>

# 4. 添加审查评论
gh pr review <pr-number> --comment --body "Good work, but please add tests"

# 5. 批准 PR
gh pr review <pr-number> --approve

# 6. 请求更改
gh pr review <pr-number> --request-changes --body "Please fix the issues mentioned"
```

---

## 高级功能

### 使用 GitHub API

```bash
# 查看仓库信息
gh api repos/:owner/:repo

# 查看工作流运行
gh api repos/:owner/:repo/actions/runs

# 查看 PR 列表（JSON 格式）
gh pr list --json number,title,author,state

# 使用 jq 处理 JSON
gh pr list --json number,title | jq '.[] | select(.title | contains("bug"))'
```

### 批量操作

```bash
# 批量关闭过时的 PR
gh pr list --state open --json number --jq '.[].number' | \
  xargs -I {} gh pr close {}

# 批量添加标签
gh issue list --state open --json number --jq '.[].number' | \
  xargs -I {} gh issue edit {} --add-label "needs-review"
```

### 自定义别名

在 `~/.bashrc` 或 `~/.zshrc` 中添加：

```bash
# GitHub CLI 别名
alias ghpr='gh pr list'
alias ghprc='gh pr create'
alias ghprv='gh pr view'
alias ghiss='gh issue list'
alias ghisc='gh issue create'
alias ghrun='gh run list'
alias ghrunv='gh run view'
```

### 脚本自动化

创建脚本 `scripts/gh-workflow.sh`:

```bash
#!/bin/bash
# 自动化工作流脚本

# 创建功能分支并推送
create_feature_branch() {
    local branch_name=$1
    git checkout -b "feature/$branch_name"
    git push -u origin "feature/$branch_name"
    echo "Branch created and pushed: feature/$branch_name"
}

# 创建 PR
create_pr() {
    local title=$1
    local body=$2
    gh pr create --title "$title" --body "$body" --base main
}

# 检查 CI 状态
check_ci() {
    gh pr checks
}

# 使用示例
# create_feature_branch "new-api"
# create_pr "Add new API" "This PR adds a new API endpoint"
# check_ci
```

---

## 基于当前项目的实际示例

### 示例 1: 提交代码更改并创建 PR

```bash
cd /home/liyun.xu/DeepDiary/DeepServer/deepserver

# 1. 创建功能分支
git checkout -b feature/improve-ci

# 2. 修改 CI 配置或代码
# 编辑 .github/workflows/ci.yml 或其他文件

# 3. 提交更改
git add .
git commit -m "Improve CI workflow configuration"

# 4. 推送分支
git push origin feature/improve-ci

# 5. 创建 PR（会自动触发 CI）
gh pr create --title "Improve CI workflow" \
  --body "This PR improves the CI workflow configuration" \
  --base main

# 6. 查看 CI 运行状态
gh run list --workflow=ci.yml --limit 1
```

### 示例 2: 处理 Dependabot PR

```bash
# 1. 查看所有 Dependabot PR
gh pr list --author "app/dependabot" --state open

# 2. 查看特定 Dependabot PR
gh pr view <pr-number>

# 3. 检查 CI 状态
gh pr checks <pr-number>

# 4. 如果 CI 通过，合并 PR
gh pr merge <pr-number> --squash --delete-branch
```

### 示例 3: 查看 CI 失败并调试

```bash
# 1. 查看最新的 CI 运行
gh run list --workflow=ci.yml --limit 1

# 2. 查看失败的运行
gh run view <run-id>

# 3. 查看详细日志
gh run view <run-id> --log

# 4. 查看特定 job 的日志（例如 pytest）
gh run view <run-id> --log --job pytest

# 5. 修复问题后，重新运行
gh run rerun <run-id>
```

---

## 实用技巧

### 1. 快速查看项目状态

```bash
# 创建别名脚本
cat > ~/bin/gh-status << 'EOF'
#!/bin/bash
echo "=== Open PRs ==="
gh pr list --state open
echo ""
echo "=== Open Issues ==="
gh issue list --state open
echo ""
echo "=== Recent CI Runs ==="
gh run list --limit 3
EOF

chmod +x ~/bin/gh-status
```

### 2. 自动检查 PR 状态

```bash
# 添加到 .bashrc 或 .zshrc
check_pr_status() {
    gh pr status
    echo ""
    echo "=== Recent CI Runs ==="
    gh run list --limit 3
}
```

### 3. 快速创建 PR 模板

```bash
# 创建 PR 模板文件
cat > .github/pull_request_template.md << 'EOF'
## 描述
<!-- 描述这个 PR 的目的和变更 -->

## 变更类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 重构
- [ ] 文档更新
- [ ] 其他

## 测试
<!-- 描述如何测试这些变更 -->

## 检查清单
- [ ] 代码已通过 lint 检查
- [ ] 已添加/更新测试
- [ ] 文档已更新
- [ ] CI 通过
EOF
```

---

## 故障排除

### 常见问题

1. **认证失败**
   ```bash
   gh auth refresh
   ```

2. **权限不足**
   ```bash
   # 检查权限
   gh auth status
   # 重新登录并选择正确的权限范围
   gh auth login --scopes repo,workflow
   ```

3. **网络问题**
   ```bash
   # 使用代理
   export HTTPS_PROXY=http://proxy.example.com:8080
   gh pr list
   ```

---

## 参考资源

- [GitHub CLI 官方文档](https://cli.github.com/manual/)
- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [Dependabot 文档](https://docs.github.com/en/code-security/dependabot)

---

## 快速参考

```bash
# 认证
gh auth login
gh auth status

# 仓库
gh repo view
gh repo clone <repo>

# PR
gh pr create
gh pr list
gh pr view <number>
gh pr merge <number>
gh pr checks

# Issue
gh issue create
gh issue list
gh issue view <number>

# CI/CD
gh run list
gh run view <run-id>
gh run rerun <run-id>
gh workflow view <workflow>

# 通用
gh --help
gh <command> --help
```

---

**提示**：使用 `gh <command> --help` 查看任何命令的详细帮助信息。

