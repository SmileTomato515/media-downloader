# 部署指南 - Social Downloader

新的應用 icon 已生成並集成。以下是完整的部署步驟。

## ✅ 已完成的準備工作

- ✅ 生成新的現代藍色 icon（替代舊的 IG 風格）
- ✅ 安裝所有 Python 依賴（`requirements.txt`）
- ✅ 安裝所有 Node.js 依賴（Expo 應用）
- ✅ 驗證 API 後端代碼完整性
- ✅ Icon 已自動配置到 `app/app.json`

## 部署選項

### 選項 1：Google Cloud Run 部署（推薦）

> Dockerfile 已配置用於 Cloud Run

#### 前置條件
```bash
# 安裝 Google Cloud SDK
# Windows 下載：https://cloud.google.com/sdk/docs/install

# 初始化 gcloud
gcloud init
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

#### 部署步驟
```bash
# 1. 從項目根目錄構建並推送 Docker 鏡像
gcloud run deploy social-downloader \
  --source . \
  --platform managed \
  --region asia-east1 \
  --allow-unauthenticated

# 服務會部署到 Cloud Run，獲得一個公開 URL
```

---

### 選項 2：本地 Docker 構建和測試

#### 前置條件
```bash
# Windows 下載：https://www.docker.com/products/docker-desktop
# 安裝後重啟 PowerShell
```

#### 構建並運行
```bash
# 1. 構建 Docker 鏡像
cd d:\Project\media_downloader
docker build -t social-downloader:latest .

# 2. 本地運行測試
docker run -p 8080:8080 social-downloader:latest

# 3. 訪問 API
# 瀏覽器打開：http://localhost:8080/docs
```

---

### 選項 3：本地開發運行

#### 運行 API 後端
```bash
cd d:\Project\media_downloader
python -m uvicorn api.main:app --reload --port 8000
# API 將在 http://localhost:8000 運行
# 文檔：http://localhost:8000/docs
```

#### 運行 Expo 前端
```bash
cd d:\Project\media_downloader\app

# 網頁版（開發）
npm run web

# 或使用 Expo CLI
npx expo start
# 按 'w' 開啟網頁版本
# 按 'a' 開啟 Android
# 按 'i' 開啟 iOS（需要 macOS）
```

---

## 🎨 新 Icon 信息

已生成的 icon 文件位於 `app/assets/`：

| 文件 | 尺寸 | 用途 |
|------|------|------|
| `icon.png` | 1024×1024 | 主應用 icon |
| `splash.png` | 1242×2436 | 應用啟動畫面 |
| `adaptive-icon.png` | 1080×1080 | Android 自適應 icon |
| `favicon.png` | 64×64 | 網頁 favicon |

**設計特色**：
- 藍色現代風格 (#2563EB)
- 三個白色圓圈代表三個社群平台
- 白色下載箭頭，象徵下載功能

如需修改 icon，編輯 `generate_icons.py` 後重新運行：
```bash
python generate_icons.py
```

---

## 環境變數設置

如果 API 需要環境變數（如代理設置），創建 `.env` 文件：

```env
# .env 範例
API_PORT=8080
API_HOST=0.0.0.0
```

## 故障排查

### API 無法啟動
```bash
# 檢查依賴
pip install -r requirements.txt --upgrade

# 檢查 Python 版本（需要 3.10+）
python --version
```

### Expo 構建失敗
```bash
# 清除緩存並重新安裝
cd app
rm -r node_modules package-lock.json
npm install
```

### Docker 構建失敗
```bash
# 確保在項目根目錄
cd d:\Project\media_downloader

# 檢查 Dockerfile 語法
docker build --no-cache -t social-downloader:latest .
```

---

## 下一步

1. **本地測試**：按照「選項 3」在本地運行並驗證新 icon
2. **選擇部署平台**：根據需要選擇 Cloud Run、Docker 或本地部署
3. **配置域名**（可選）：為 Cloud Run 服務設置自定義域名
4. **監控和日誌**：設置應用監控和錯誤日誌追蹤

---

**部署準備狀態**：✅ 完成
**最後更新**：2026-08-11
