# Google Cloud Run 部署流程

本 SKILL 記錄 media-downloader 專案部署到 Google Cloud Run 的完整步驟。

## 前置條件

1. **安裝 Google Cloud CLI**
   - 下載並安裝：https://cloud.google.com/sdk/docs/install
   - 驗證安裝：`gcloud --version`

2. **GCP 專案配置**
   - 專案 ID：`omni-calc-20260615`
   - 帳號：`a0970900945@gmail.com`
   - 區域：`us-central1`

3. **必要的 GCP API**
   - Cloud Run API
   - Cloud Build API
   - Container Registry API

## 首次設定

### 1. 認證與登入

```bash
# 登入 GCP 帳號
gcloud auth login

# 設定專案 ID
gcloud config set project omni-calc-20260615

# 設定預設區域
gcloud config set run/region us-central1

# 驗證配置
gcloud config list
```

### 2. 啟用必要的 API

```bash
# 啟用 Cloud Run API
gcloud services enable run.googleapis.com

# 啟用 Cloud Build API
gcloud services enable cloudbuild.googleapis.com

# 啟用 Artifact Registry API (用於儲存容器映像)
gcloud services enable artifactregistry.googleapis.com
```

## 部署流程

### 完整部署指令

```bash
# 切換到專案目錄
cd d:\Project\media_downloader

# 執行部署
gcloud run deploy media-downloader \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --timeout 300
```

### 指令參數說明

- `media-downloader`: Cloud Run 服務名稱
- `--source .`: 使用當前目錄的 Dockerfile 構建
- `--platform managed`: 使用完全託管的 Cloud Run
- `--region us-central1`: 部署到美國中部區域
- `--allow-unauthenticated`: 允許未經認證的公開訪問
- `--memory 512Mi`: 配置 512MB 記憶體
- `--timeout 300`: 設定請求超時為 300 秒

### 部署過程

1. **驗證配置** - Cloud Run 檢查 Dockerfile 和專案設定
2. **上傳原始碼** - 將專案檔案上傳到 Cloud Build
3. **構建容器** - 使用 Dockerfile 構建容器映像
4. **創建版本** - 生成新的服務版本 (revision)
5. **路由流量** - 將 100% 流量導向新版本
6. **設定 IAM** - 配置權限策略

### 部署完成

部署成功後會顯示：
```
Service [media-downloader] revision [media-downloader-00XXX-xxx] has been deployed and is serving 100 percent of traffic.
Service URL: https://media-downloader-962329744591.us-central1.run.app
```

## 驗證部署

### 1. 測試 API 端點

```powershell
# 使用 PowerShell 測試
$body = @{url = "https://www.threads.com/@tank88601/post/Db3BDDbgT-K"} | ConvertTo-Json
Invoke-RestMethod -Uri "https://media-downloader-962329744591.us-central1.run.app/api/analyze" -Method Post -Body $body -ContentType "application/json"
```

### 2. 查看服務狀態

```bash
# 列出所有 Cloud Run 服務
gcloud run services list

# 查看特定服務詳情
gcloud run services describe media-downloader --region us-central1

# 查看服務日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=media-downloader" --limit 50 --format json
```

## 更新部署

當程式碼有變更時，只需重新執行部署指令：

```bash
gcloud run deploy media-downloader --source . --platform managed --region us-central1 --allow-unauthenticated --memory 512Mi --timeout 300
```

Cloud Run 會：
1. 自動構建新的容器映像
2. 創建新的 revision (版本號遞增)
3. 將流量從舊版本切換到新版本
4. 保留舊版本以便回滾

## 管理版本 (Revisions)

### 查看所有版本

```bash
gcloud run revisions list --service media-downloader --region us-central1
```

### 回滾到舊版本

```bash
# 將流量導向特定版本
gcloud run services update-traffic media-downloader \
  --to-revisions=media-downloader-00005-hkr=100 \
  --region us-central1
```

### 刪除舊版本

```bash
# 刪除特定版本
gcloud run revisions delete media-downloader-00001-abc --region us-central1
```

## 配置調整

### 調整記憶體配置

```bash
gcloud run services update media-downloader \
  --memory 1Gi \
  --region us-central1
```

### 調整 CPU 配置

```bash
gcloud run services update media-downloader \
  --cpu 2 \
  --region us-central1
```

### 調整超時時間

```bash
gcloud run services update media-downloader \
  --timeout 600 \
  --region us-central1
```

### 設定環境變數

```bash
gcloud run services update media-downloader \
  --set-env-vars="DEBUG=true,LOG_LEVEL=info" \
  --region us-central1
```

## 監控與除錯

### 即時日誌

```bash
# 串流即時日誌
gcloud logging tail "resource.type=cloud_run_revision AND resource.labels.service_name=media-downloader"
```

### 查看指標

```bash
# 在 GCP Console 查看
https://console.cloud.google.com/run/detail/us-central1/media-downloader/metrics
```

### 除錯建議

1. **構建失敗**：檢查 Dockerfile 和依賴安裝
2. **部署超時**：增加 timeout 設定
3. **記憶體不足**：增加 memory 配置
4. **API 錯誤**：查看日誌排查問題

## 成本管理

### 查看帳單

```bash
# 在 GCP Console 查看
https://console.cloud.google.com/billing
```

### 成本優化建議

1. **最小實例數**：設為 0 (按需啟動)
2. **記憶體配置**：根據實際需求調整 (目前 512Mi)
3. **超時設定**：避免設定過長 (目前 300秒)
4. **流量限制**：考慮設定每日請求上限

## 刪除服務

如需完全移除服務：

```bash
gcloud run services delete media-downloader --region us-central1
```

## Dockerfile 要求

Cloud Run 需要的 Dockerfile 關鍵配置：

```dockerfile
# 1. 使用支援的基礎映像
FROM python:3.10-slim

# 2. 設定工作目錄
WORKDIR /app

# 3. 安裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. 複製程式碼
COPY api ./api

# 5. 監聽 8080 port (Cloud Run 預設)
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

## 疑難排解

### 問題：部署時提示權限不足

```bash
# 賦予 Cloud Build 服務帳號必要的權限
gcloud projects add-iam-policy-binding omni-calc-20260615 \
  --member="serviceAccount:962329744591-compute@developer.gserviceaccount.com" \
  --role="roles/run.admin"
```

### 問題：容器構建失敗

1. 檢查 Dockerfile 語法
2. 確認 requirements.txt 中的套件都能安裝
3. 查看構建日誌：
   ```bash
   gcloud builds list --limit 5
   gcloud builds log <BUILD_ID>
   ```

### 問題：服務無法訪問

1. 確認服務是否允許未經認證的訪問：
   ```bash
   gcloud run services get-iam-policy media-downloader --region us-central1
   ```

2. 設定公開訪問：
   ```bash
   gcloud run services add-iam-policy-binding media-downloader \
     --region=us-central1 \
     --member="allUsers" \
     --role="roles/run.invoker"
   ```

## 參考資料

- [Cloud Run 官方文檔](https://cloud.google.com/run/docs)
- [gcloud CLI 參考](https://cloud.google.com/sdk/gcloud/reference/run)
- [Dockerfile 最佳實踐](https://docs.docker.com/develop/dev-best-practices/)
