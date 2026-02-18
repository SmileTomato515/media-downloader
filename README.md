# Media Downloader

一個以 **FastAPI** 為核心的社群媒體下載工具，支援分析與下載：
- Instagram
- Facebook
- Threads

後端會解析貼文媒體資源，前端提供簡單操作介面，並透過 proxy 下載以降低 CORS / Referer 限制問題。

## 功能特色

- 支援 Instagram / Facebook / Threads 連結分析
- 回傳貼文內圖片與影片清單（依平台結構解析）
- `proxy_download` 代理下載，避免前端直接抓取被擋
- 內建 PWA 靜態檔路由（`manifest.json` / `sw.js`）
- 可用 Docker 部署（預設 Cloud Run 相容設定）

## 技術棧

- Python 3.10
- FastAPI + Uvicorn
- BeautifulSoup4 + lxml
- cloudscraper
- Jinja2 Templates

## 專案結構

```text
.
├─ api/
│  ├─ main.py          # FastAPI 入口與 API 路由
│  ├─ scraper.py       # 各平台解析邏輯
│  ├─ static/          # PWA 靜態檔
│  └─ templates/       # HTML 模板
├─ app/                # Expo React Native App
├─ scraper/            # Node 測試腳本（獨立）
├─ requirements.txt
└─ Dockerfile
```

## 本機啟動（Python）

1. 建立虛擬環境（建議）
2. 安裝套件
3. 啟動 FastAPI

```bash
pip install -r requirements.txt
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
```

啟動後開啟：
- `http://127.0.0.1:8000/`

## Docker 啟動

```bash
docker build -t media-downloader .
docker run --rm -p 8080:8080 media-downloader
```

啟動後開啟：
- `http://127.0.0.1:8080/`

## API 端點

### `POST /api/analyze`

分析貼文連結並回傳媒體資訊。

**Request Body**

```json
{
  "url": "https://www.instagram.com/p/xxxx/"
}
```

**Response（示意）**

```json
{
  "type": "instagram",
  "url": "https://...",
  "media": [
    {
      "type": "video",
      "url": "https://..."
    }
  ]
}
```

### `GET /api/proxy_download`

代理下載媒體檔案。

**Query Params**
- `url`：媒體 URL（必填）
- `name`：下載檔名（選填）
- `inline`：是否以 inline 模式回傳（預設 `false`）

範例：

```text
/api/proxy_download?url=<MEDIA_URL>&name=myfile&inline=false
```

## 前端（Expo App）

`app/` 目錄為 Expo 專案，可獨立安裝與啟動：

```bash
cd app
npm install
npm start
```

## 注意事項

- 各平台可能調整頁面結構或防爬策略，解析結果會受影響。
- 僅下載你有合法權限使用的內容，請遵守平台條款與當地法規。

## License

目前未附授權聲明，預設為保留所有權利（All rights reserved）。
