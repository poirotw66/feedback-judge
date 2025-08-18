#!/bin/bash

# API 端點測試腳本
# 用於驗證部署後的 API 是否正常工作

# 設置測試的基礎 URL
BASE_URL=${1:-"http://localhost:8003"}

echo "🚀 測試 API 端點: $BASE_URL"
echo "================================"

# 測試函數 (GET 請求)
test_endpoint() {
    local url=$1
    local expected_status=${2:-200}
    local description=$3
    
    echo -n "測試 $description... "
    
    status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    
    if [ "$status_code" -eq "$expected_status" ]; then
        echo "✅ ($status_code)"
        return 0
    else
        echo "❌ (期望: $expected_status, 實際: $status_code)"
        return 1
    fi
}

# 測試函數 (POST 請求)
test_post_endpoint() {
    local url=$1
    local expected_status=${2:-200}
    local description=$3
    
    echo -n "測試 $description... "
    
    status_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$url")
    
    if [ "$status_code" -eq "$expected_status" ]; then
        echo "✅ ($status_code)"
        return 0
    else
        echo "❌ (期望: $expected_status, 實際: $status_code)"
        return 1
    fi
}

# 測試端點
echo "1. 基本端點測試:"
test_endpoint "$BASE_URL/" 200 "主應用根端點"
test_endpoint "$BASE_URL/feedback-service/" 200 "feedback-service 根端點"
test_endpoint "$BASE_URL/feedback-service/health" 200 "健康檢查端點"

echo ""
echo "2. API 文檔端點測試:"
test_endpoint "$BASE_URL/openapi.json" 307 "OpenAPI 重定向"
test_endpoint "$BASE_URL/feedback-service/openapi.json" 200 "OpenAPI 規範"
test_endpoint "$BASE_URL/feedback-service/docs" 200 "Swagger UI"
test_endpoint "$BASE_URL/feedback-service/redoc" 200 "ReDoc 文檔"

echo ""
echo "3. API 功能端點測試:"
test_post_endpoint "$BASE_URL/feedback-service/evaluate" 422 "評估端點 (無文件)"
test_post_endpoint "$BASE_URL/feedback-service/evaluate-document" 422 "文檔評估端點 (無文件)"

echo ""
echo "🎉 所有端點測試完成！"
