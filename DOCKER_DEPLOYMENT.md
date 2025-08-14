# 外來函文AI測試結果準確度評分系統 - Docker 部署指南

## 🐋 Docker 部署說明

本系統提供了完整的 Docker 容器化部署方案，支持開發和生產環境。

### 📋 系統要求

- Docker 20.10 或更高版本
- Docker Compose 2.0 或更高版本
- 至少 2GB RAM
- 至少 1GB 磁盤空間

### 🚀 快速部署

#### 1. 開發環境部署

```bash
# 克隆代碼
git clone <repository-url>
cd feedback-judge

# 一鍵部署
./deploy.sh
```

#### 2. 手動部署

```bash
# 構建映像
docker-compose build

# 啟動服務
docker-compose up -d

# 查看日誌
docker-compose logs -f
```

### 🏭 生產環境部署

```bash
# 使用生產配置
docker-compose -f docker-compose.prod.yml up -d

# 或者使用 Nginx 反向代理
docker-compose -f docker-compose.prod.yml up -d
```

### 📍 服務端點

- **API 服務**: http://localhost:8003
- **API 文檔**: http://localhost:8003/docs
- **ReDoc 文檔**: http://localhost:8003/redoc
- **健康檢查**: http://localhost:8003/health

### 📁 目錄結構

```
feedback-judge/
├── api/                    # API 源代碼
├── data/                   # 測試數據目錄
├── output/                 # 輸出結果目錄
├── Dockerfile             # Docker 映像定義
├── docker-compose.yml     # 開發環境配置
├── docker-compose.prod.yml # 生產環境配置
├── nginx.conf             # Nginx 配置
├── deploy.sh              # 部署腳本
└── requirements.txt       # Python 依賴
```

### 🛠️ 常用命令

```bash
# 查看服務狀態
docker-compose ps

# 查看服務日誌
docker-compose logs -f

# 重啟服務
docker-compose restart

# 停止服務
docker-compose down

# 完全清理（包括映像）
docker-compose down --rmi all --volumes

# 進入容器調試
docker-compose exec feedback-judge-api bash

# 查看容器資源使用
docker stats
```

### 📊 API 使用示例

#### 身心障礙手冊評估

```bash
curl -X POST "http://localhost:8003/evaluate" \
  -F "file=@test_data.xlsx" \
  -F "valueSetId=TEST_123" \
  --output result.xlsx
```

#### 外來函文評估

```bash
curl -X POST "http://localhost:8003/evaluate-document" \
  -F "file=@document_data.xlsx" \
  -F "valueSetId=DOC_TEST_123" \
  --output document_result.xlsx
```

### 🔧 配置說明

#### 環境變數

- `PYTHONPATH`: Python 模塊路徑
- `UVICORN_HOST`: 服務監聽地址
- `UVICORN_PORT`: 服務端口
- `UVICORN_WORKERS`: Worker 進程數（生產環境）

#### 資源限制

生產環境默認配置：
- 內存限制: 2GB
- CPU 限制: 1.0 核心
- 內存保留: 1GB
- CPU 保留: 0.5 核心

### 🔍 監控和日誌

#### 健康檢查

系統包含內建的健康檢查機制：
- 檢查間隔: 30秒
- 超時時間: 10秒
- 重試次數: 3次
- 啟動等待: 40秒

#### 日誌查看

```bash
# 查看所有服務日誌
docker-compose logs

# 查看特定服務日誌
docker-compose logs feedback-judge-api

# 實時跟蹤日誌
docker-compose logs -f --tail=100

# 查看 Nginx 日誌（如果使用）
docker-compose logs nginx
```

### 🛡️ 安全性考量

#### 生產環境建議

1. **使用 HTTPS**: 配置 SSL 證書
2. **設置防火牆**: 限制端口訪問
3. **資源限制**: 設置適當的資源限制
4. **定期更新**: 保持映像和依賴更新
5. **日誌管理**: 設置日誌輪換和歸檔

#### SSL 配置

將 SSL 證書放置在 `ssl/` 目錄：
```
ssl/
├── cert.pem
└── key.pem
```

然後取消註釋 `nginx.conf` 中的 HTTPS 配置。

### 🐛 故障排除

#### 常見問題

1. **端口衝突**
   ```bash
   # 查看端口使用
   netstat -tlnp | grep 8003
   
   # 修改 docker-compose.yml 中的端口映射
   ports:
     - "8004:8003"  # 使用不同的外部端口
   ```

2. **內存不足**
   ```bash
   # 檢查系統資源
   docker system df
   docker system prune  # 清理未使用的資源
   ```

3. **映像構建失敗**
   ```bash
   # 清理構建緩存
   docker builder prune
   
   # 重新構建
   docker-compose build --no-cache
   ```

4. **服務無法訪問**
   ```bash
   # 檢查容器狀態
   docker-compose ps
   
   # 檢查容器日誌
   docker-compose logs feedback-judge-api
   
   # 檢查網絡連接
   docker network ls
   docker network inspect feedback-judge_feedback-judge-network
   ```

### 📈 性能優化

#### 生產環境建議

1. **Worker 數量**: 根據 CPU 核心數調整
2. **內存分配**: 根據並發需求調整
3. **緩存策略**: 使用 Redis 緩存（如需要）
4. **負載均衡**: 多實例部署

#### 監控指標

建議監控以下指標：
- CPU 使用率
- 內存使用率
- 響應時間
- 錯誤率
- 磁盤使用率

### 📞 支援

如果遇到問題，請：
1. 檢查日誌: `docker-compose logs`
2. 確認配置: 檢查環境變數和端口
3. 資源檢查: 確保足夠的 CPU 和內存
4. 網絡檢查: 確認防火牆和端口設置
