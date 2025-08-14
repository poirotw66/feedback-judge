#!/bin/bash

# GCP Artifact Registry 部署腳本 (Production 模式)
# 用於將 Feedback Judge API Docker image 上傳到 GCP Artifact Registry 並部署為 Production

set -e  # 遇到錯誤時停止執行

# 配置變數 (請根據你的 GCP 設定修改)
PROJECT_ID="itr-aimasteryhub-lab"
REGION="asia-east1"  # 或其他你偏好的區域
REPOSITORY_NAME="feedback-rating-api"
IMAGE_NAME="feedback-judge-api"
IMAGE_TAG="latest"
SERVICE_NAME="feedback-judge-api"

# 完整的 image 名稱
FULL_IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY_NAME}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "🚀 開始部署 Feedback Judge API 到 GCP (Production 模式)"
echo "專案 ID: ${PROJECT_ID}"
echo "區域: ${REGION}"
echo "Repository: ${REPOSITORY_NAME}"
echo "Image: ${FULL_IMAGE_NAME}"
echo "🎯 模式: PRODUCTION"
echo ""

# 檢查是否已登入 gcloud
echo "📋 檢查 gcloud 認證狀態..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ 請先登入 gcloud: gcloud auth login"
    exit 1
fi

# 設定專案
echo "🔧 設定 GCP 專案..."
gcloud config set project ${PROJECT_ID}

# 檢查並創建 Artifact Registry repository (如果不存在)
echo "📦 檢查 Artifact Registry repository..."
if ! gcloud artifacts repositories describe ${REPOSITORY_NAME} --location=${REGION} >/dev/null 2>&1; then
    echo "🆕 創建新的 Artifact Registry repository..."
    gcloud artifacts repositories create ${REPOSITORY_NAME} \
        --repository-format=docker \
        --location=${REGION} \
        --description="Feedback Judge API Docker images"
else
    echo "✅ Repository ${REPOSITORY_NAME} 已存在"
fi

# 配置 Docker 認證
echo "🔐 配置 Docker 認證..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev

# 建構 Docker image (Production 模式)
echo "🏗️ 建構 Docker image (Production 模式)..."
docker build \
    --build-arg ENV=production \
    --build-arg DEBUG=false \
    -t ${IMAGE_NAME}:${IMAGE_TAG} .

# 標記 image 為 Artifact Registry 格式
echo "🏷️ 標記 image..."
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${FULL_IMAGE_NAME}

# 推送 image 到 Artifact Registry
echo "📤 推送 image 到 Artifact Registry..."
docker push ${FULL_IMAGE_NAME}
# 顯示成功訊息
echo ""
echo "🎉 部署完成！"
echo "Image: ${FULL_IMAGE_NAME}"
echo "🎯 模式: PRODUCTION"
