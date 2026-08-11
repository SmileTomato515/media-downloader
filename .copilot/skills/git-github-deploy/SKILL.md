# Git / GitHub 部署流程

本 SKILL 記錄 media-downloader 專案的 Git 版本控制和 GitHub 推送流程。

## 前置條件

1. **安裝 Git**
   - 下載並安裝：https://git-scm.com/downloads
   - 驗證安裝：`git --version`

2. **安裝 GitHub CLI**
   - 下載並安裝：https://cli.github.com/
   - 驗證安裝：`gh --version`

3. **GitHub 帳號**
   - 帳號：SmileTomato515
   - 倉庫：https://github.com/SmileTomato515/media-downloader.git

## 首次設定

### 1. Git 配置

```bash
# 設定使用者資訊
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 設定預設分支名稱
git config --global init.defaultBranch main

# 查看配置
git config --list
```

### 2. GitHub CLI 認證

```bash
# 登入 GitHub
gh auth login

# 選擇：
# - GitHub.com
# - HTTPS
# - Login with a web browser

# 驗證登入狀態
gh auth status
```

輸出範例：
```
github.com
  ✓ Logged in to github.com account SmileTomato515 (keyring)
  - Active account: true
  - Git operations protocol: https
  - Token scopes: 'gist', 'read:org', 'repo'
```

### 3. 初始化 Git 倉庫（如果尚未初始化）

```bash
# 切換到專案目錄
cd d:\Project\media_downloader

# 初始化 Git 倉庫
git init

# 添加遠端倉庫
git remote add origin https://github.com/SmileTomato515/media-downloader.git

# 驗證遠端倉庫
git remote -v
```

## .gitignore 配置

確保 `.gitignore` 文件包含以下內容：

```gitignore
# Python
.venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Environment variables
.env
.env.local
.env.*.local

# Logs
*.log
logs/

# Temporary files
*.tmp
*.temp
.cache/
```

## 日常工作流程

### 1. 查看狀態

```bash
# 查看當前狀態
git status

# 簡短格式
git status --short

# 查看變更差異
git diff

# 查看已暫存的變更
git diff --staged
```

### 2. 暫存變更

```bash
# 暫存特定檔案
git add api/scraper.py
git add README.md

# 暫存所有變更
git add .

# 暫存所有變更（包含刪除）
git add -A

# 互動式暫存
git add -p
```

### 3. 提交變更

```bash
# 提交已暫存的變更
git commit -m "feat: add Threads /share/ link support"

# 提交並添加詳細說明
git commit -m "fix: resolve invalid share link detection" -m "- Check canonical URL for homepage redirect
- Return empty result for deleted posts
- Add validation for /share/ links"

# 修改最後一次提交
git commit --amend -m "fix: corrected commit message"
```

#### 提交訊息規範

使用 Conventional Commits 格式：

- `feat`: 新功能
- `fix`: 修復 Bug
- `docs`: 文檔更新
- `style`: 程式碼格式調整（不影響功能）
- `refactor`: 重構程式碼
- `perf`: 性能優化
- `test`: 測試相關
- `chore`: 構建過程或輔助工具變動

範例：
```
feat(scraper): add Instagram carousel support
fix(api): resolve video URL parsing error
docs(readme): update deployment instructions
chore(deps): update dependencies to latest versions
```

### 4. 推送到 GitHub

```bash
# 推送到遠端 main 分支
git push origin main

# 強制推送（謹慎使用）
git push -f origin main

# 推送並設定上游分支
git push -u origin main

# 推送所有分支
git push --all origin

# 推送標籤
git push --tags
```

### 5. 拉取更新

```bash
# 拉取並合併
git pull origin main

# 僅拉取不合併
git fetch origin

# 拉取後變基（rebase）
git pull --rebase origin main
```

## 完整部署流程

### 方案 A：標準流程

```bash
# 1. 查看狀態
git status

# 2. 暫存變更
git add -A

# 3. 提交
git commit -m "feat: implement new feature"

# 4. 推送
git push origin main
```

### 方案 B：快速提交（單行）

```bash
git add -A && git commit -m "update" && git push origin main
```

### 方案 C：使用 GitHub CLI 創建倉庫

```bash
# 創建新倉庫（如果尚未創建）
gh repo create media-downloader --public --source=. --remote=origin

# 推送程式碼
git push -u origin main
```

## 分支管理

### 創建和切換分支

```bash
# 創建新分支
git branch feature/new-parser

# 切換分支
git checkout feature/new-parser

# 創建並切換（一步完成）
git checkout -b feature/new-parser

# 查看所有分支
git branch -a
```

### 合併分支

```bash
# 切換到 main 分支
git checkout main

# 合併功能分支
git merge feature/new-parser

# 刪除已合併的分支
git branch -d feature/new-parser
```

### 分支策略

建議的分支結構：
- `main`: 穩定的生產版本
- `develop`: 開發主分支
- `feature/*`: 功能開發分支
- `bugfix/*`: Bug 修復分支
- `hotfix/*`: 緊急修復分支

## 查看歷史

```bash
# 查看提交歷史
git log

# 簡潔格式
git log --oneline

# 圖形化顯示
git log --graph --oneline --all

# 查看最近 5 次提交
git log -5

# 查看特定檔案的歷史
git log --follow api/scraper.py

# 查看提交統計
git log --stat

# 搜索提交訊息
git log --grep="fix"
```

## 撤銷變更

### 撤銷未暫存的變更

```bash
# 撤銷特定檔案
git checkout -- api/scraper.py

# 撤銷所有未暫存的變更
git checkout -- .

# 或使用新語法
git restore api/scraper.py
git restore .
```

### 撤銷已暫存的變更

```bash
# 取消暫存特定檔案
git reset HEAD api/scraper.py

# 取消暫存所有檔案
git reset HEAD

# 或使用新語法
git restore --staged api/scraper.py
```

### 撤銷提交

```bash
# 撤銷最後一次提交（保留變更）
git reset --soft HEAD~1

# 撤銷最後一次提交（不保留變更）
git reset --hard HEAD~1

# 創建反向提交（推薦用於已推送的提交）
git revert HEAD
```

## 標籤管理

```bash
# 創建輕量標籤
git tag v1.0.0

# 創建附註標籤
git tag -a v1.0.0 -m "Release version 1.0.0"

# 查看所有標籤
git tag

# 推送標籤到遠端
git push origin v1.0.0

# 推送所有標籤
git push --tags

# 刪除本地標籤
git tag -d v1.0.0

# 刪除遠端標籤
git push origin --delete v1.0.0
```

## 清理倉庫

### 移除不需要的檔案

```bash
# 停止追蹤已加入的檔案（保留本地檔案）
git rm --cached .venv/

# 停止追蹤整個目錄
git rm -r --cached app/node_modules/

# 提交變更
git commit -m "chore: remove tracked node_modules and venv"
```

### 清理歷史中的大檔案

```bash
# 使用 BFG Repo-Cleaner（推薦）
# 1. 下載 BFG: https://rtyley.github.io/bfg-repo-cleaner/
# 2. 移除大於 100MB 的檔案
java -jar bfg.jar --strip-blobs-bigger-than 100M media-downloader.git

# 或使用 git filter-branch（較慢）
git filter-branch --tree-filter 'rm -rf app/node_modules' HEAD
```

## GitHub 操作（使用 CLI）

### 查看倉庫資訊

```bash
# 查看倉庫狀態
gh repo view

# 查看 Issues
gh issue list

# 查看 Pull Requests
gh pr list
```

### 創建 Issue

```bash
gh issue create --title "Bug: API returns wrong media" --body "Description of the issue..."
```

### 創建 Pull Request

```bash
# 從當前分支創建 PR
gh pr create --title "Add new feature" --body "Description of changes"

# 互動式創建 PR
gh pr create
```

### 查看工作流程狀態（GitHub Actions）

```bash
# 查看工作流程運行狀態
gh run list

# 查看特定運行的詳情
gh run view <run-id>
```

## 協作流程

### Fork 和 Pull Request 流程

1. **Fork 倉庫**（在 GitHub 網頁上操作）

2. **克隆 Fork 的倉庫**
   ```bash
   git clone https://github.com/YourUsername/media-downloader.git
   cd media-downloader
   ```

3. **添加上游倉庫**
   ```bash
   git remote add upstream https://github.com/SmileTomato515/media-downloader.git
   ```

4. **創建功能分支**
   ```bash
   git checkout -b feature/your-feature
   ```

5. **開發並提交**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   ```

6. **推送到你的 Fork**
   ```bash
   git push origin feature/your-feature
   ```

7. **創建 Pull Request**
   ```bash
   gh pr create --repo SmileTomato515/media-downloader
   ```

### 同步 Fork

```bash
# 拉取上游變更
git fetch upstream

# 合併到本地 main
git checkout main
git merge upstream/main

# 推送到你的 Fork
git push origin main
```

## 疑難排解

### 問題：推送被拒絕

```bash
# 原因：遠端有新的提交
# 解決：先拉取再推送
git pull --rebase origin main
git push origin main
```

### 問題：合併衝突

```bash
# 1. 拉取時發生衝突
git pull origin main
# Auto-merging api/scraper.py
# CONFLICT (content): Merge conflict in api/scraper.py

# 2. 手動解決衝突（編輯檔案）

# 3. 標記為已解決
git add api/scraper.py

# 4. 完成合併
git commit
```

### 問題：誤提交敏感資訊

```bash
# 1. 立即移除檔案
git rm --cached .env

# 2. 提交移除
git commit -m "chore: remove sensitive file"

# 3. 推送
git push origin main

# 4. 如果已推送，需要清理歷史
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# 5. 強制推送
git push origin --force --all
```

### 問題：本地與遠端完全不同步

```bash
# 備份當前工作
git stash

# 重置到遠端狀態
git fetch origin
git reset --hard origin/main

# 恢復工作（如果需要）
git stash pop
```

## 最佳實踐

1. **頻繁提交**：小步提交，易於追蹤和回滾
2. **清晰的提交訊息**：遵循 Conventional Commits 規範
3. **使用 .gitignore**：避免提交不必要的檔案
4. **定期推送**：避免本地累積過多未推送的提交
5. **保持分支整潔**：及時刪除已合併的分支
6. **Code Review**：使用 Pull Request 進行程式碼審查
7. **保護主分支**：在 GitHub 設定分支保護規則
8. **使用標籤**：標記重要版本

## 參考資料

- [Git 官方文檔](https://git-scm.com/doc)
- [GitHub CLI 文檔](https://cli.github.com/manual/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Pro Git 書籍](https://git-scm.com/book/zh-tw/v2)
