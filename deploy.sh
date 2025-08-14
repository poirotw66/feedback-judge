#!/bin/bash
# Docker 部署腳本
# Docker Deployment Script for Feedback Judge API

set -e

echo "🐋 外來函文AI測試結果準確度評分系統 - Docker 部署"
echo "================================================================"

# 檢查 Docker 是否安裝
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安裝，請先安裝 Docker"
    exit 1
fi

# 檢查 Docker Compose 是否安裝
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安裝，請先安裝 Docker Compose"
    exit 1
fi

echo "✅ Docker 和 Docker Compose 已安裝"

# 創建必要的目錄
mkdir -p output data
echo "✅ 創建輸出和數據目錄"

# 構建 Docker 映像
echo "🔨 構建 Docker 映像..."
docker-compose build

# 啟動服務
echo "🚀 啟動服務..."
docker-compose up -d

# 等待服務啟動
echo "⏳ 等待服務啟動..."
sleep 10

# 檢查服務狀態
echo "🔍 檢查服務狀態..."
docker-compose ps

# 測試 API 健康狀態
echo "🏥 檢查 API 健康狀態..."
if curl -f http://localhost:8003/health > /dev/null 2>&1; then
    echo "✅ API 服務健康檢查通過"
else
    echo "⚠️  API 服務可能還在啟動中，請稍後再試"
fi

echo ""
echo "🎉 部署完成！"
echo "📍 API 服務地址: http://localhost:8003"
echo "📖 API 文檔地址: http://localhost:8003/docs"
echo "📚 ReDoc 文檔地址: http://localhost:8003/redoc"
echo ""
echo "🛠️  常用命令:"
echo "   查看日誌: docker-compose logs -f"
echo "   停止服務: docker-compose down"
echo "   重啟服務: docker-compose restart"
echo "   查看狀態: docker-compose ps"
echo ""
echo "📁 文件掛載:"
echo "   輸出目錄: ./output"
echo "   數據目錄: ./data"
