# 使用官方 Python 3.12 slim 映像作為基礎
FROM python:3.12-slim

# 設置工作目錄
WORKDIR /app

# 設置環境變數
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 複製 requirements.txt 並安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 複製應用程式代碼
COPY . .

# 創建輸出目錄
RUN mkdir -p output data

# 設置權限
RUN chmod +x start_api.sh

# 暴露端口
EXPOSE 8003

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# 設置啟動命令
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8003", "--workers", "1"]
