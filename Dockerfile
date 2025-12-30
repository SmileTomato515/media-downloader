# 使用 Python 3.10 輕量版
FROM python:3.10-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴 (cloudscraper 需要編譯環境)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    && rm -rf /var/lib/apt/lists/*

# 複製需求檔並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製程式碼
COPY api ./api

# 設定環境變數 (讓 Python 輸出不被緩衝)
ENV PYTHONUNBUFFERED=1

# Cloud Run 預設會聽 8080 port
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8080"]