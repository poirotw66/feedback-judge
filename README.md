# Disability Certificate AI Accuracy Evaluator API

身心障礙手冊AI測試結果準確度評分系統 - FastAPI版本

## 概述

這是一個基於FastAPI的Web API，用於評估身心障礙手冊AI測試結果的準確度。系統接受Excel檔案上傳，分析AI預測結果與正確答案的相似度，並生成詳細的評估報告。

## 功能特色

- **檔案上傳**: 支援.xlsx和.xls格式的Excel檔案
- **準確度評估**: 計算各欄位和整體的準確度分數
- **詳細分析**: 提供逐筆記錄的欄位比較
- **錯誤分析**: 識別和分類不同類型的錯誤
- **Excel輸出**: 生成包含評估結果的Excel報告
- **RESTful API**: 標準的HTTP API介面

## 安裝與設定

### 1. 安裝依賴套件

```bash
pip install -r requirements.txt
```

### 2. 啟動API服務

```bash
# 開發模式
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# 生產模式
uvicorn app:app --host 0.0.0.0 --port 8000
```

### 3. 訪問API文檔

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API端點

### 1. 根端點
- **URL**: `GET /`
- **描述**: 取得API基本資訊
- **回應**: API歡迎訊息和端點列表

### 2. 健康檢查
- **URL**: `GET /health`
- **描述**: 檢查API服務狀態
- **回應**: 服務健康狀態

### 3. 準確度評估
- **URL**: `POST /evaluate`
- **描述**: 上傳Excel檔案進行準確度評估
- **請求**: 
  - Content-Type: `multipart/form-data`
  - 參數: `file` (Excel檔案)
- **回應**: Excel檔案 (包含評估結果)

## 使用方式

### 1. 使用curl

```bash
curl -X POST "http://localhost:8000/evaluate" \
     -H "accept: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_data.xlsx" \
     --output result.xlsx
```

### 2. 使用Python requests

```python
import requests

url = "http://localhost:8000/evaluate"
files = {"file": open("your_data.xlsx", "rb")}

response = requests.post(url, files=files)

if response.status_code == 200:
    with open("result.xlsx", "wb") as f:
        f.write(response.content)
    print("評估完成，結果已儲存至 result.xlsx")
else:
    print(f"錯誤: {response.status_code} - {response.text}")
```

### 3. 使用JavaScript (前端)

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/evaluate', {
    method: 'POST',
    body: formData
})
.then(response => {
    if (response.ok) {
        return response.blob();
    }
    throw new Error('評估失敗');
})
.then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'evaluation_result.xlsx';
    a.click();
});
```

## 輸入檔案格式

Excel檔案應包含以下欄位：

### 必要欄位
- `編號`: 記錄編號
- `受編`: 受測者編號
- `正面_障礙等級`: 正確的障礙等級
- `正面_障礙類別`: 正確的障礙類別
- `正面_ICD診斷`: 正確的ICD診斷
- `反面_障礙等級`: AI預測的障礙等級
- `反面_障礙類別`: AI預測的障礙類別
- `反面_ICD診斷`: AI預測的ICD診斷

### 範例資料格式

| 編號 | 受編 | 正面_障礙等級 | 正面_障礙類別 | 正面_ICD診斷 | 反面_障礙等級 | 反面_障礙類別 | 反面_ICD診斷 |
|------|------|---------------|---------------|---------------|---------------|---------------|---------------|
| 1 | ZA24761194 | 輕度 | 其他類 | 【換16.1】 | 輕度 | 障礙類別：其他類 | 【換16.1】 |
| 2 | MT00953431 | 中度 | 第1類【12.2】 | 【換12.2】 | 中度 | 第1類【12.2】 | 【第12.2】 |

## 輸出檔案內容

生成的Excel檔案包含以下工作表：

1. **評估摘要**: 整體統計和各欄位準確度
2. **記錄摘要**: 每筆記錄的準確度摘要
3. **詳細欄位比較**: 逐欄位的詳細比較結果
4. **欄位統計**: 各欄位的統計分析
5. **錯誤分析**: 錯誤類型分析和改進建議
6. **原始資料**: 上傳的原始資料
7. **準確度分佈**: 準確度等級分佈統計

## 錯誤處理

API提供詳細的錯誤訊息：

### 檔案驗證錯誤 (400)
- 檔案格式不支援
- 檔案為空
- 檔案過大 (>10MB)

### 資料驗證錯誤 (422)
- 缺少必要欄位
- 資料格式錯誤

### 處理錯誤 (500)
- 檔案讀取失敗
- 評估處理錯誤
- Excel生成錯誤

### 錯誤回應格式

```json
{
    "error": true,
    "message": "錯誤描述",
    "status_code": 400,
    "timestamp": "2024-01-01T12:00:00",
    "details": {
        "error_type": "file_validation_error",
        "filename": "example.xlsx"
    }
}
```

## 效能考量

- 檔案大小限制: 10MB
- 建議記錄數: <10,000筆
- 處理時間: 通常在30秒內完成

## 安全性

- 檔案類型驗證
- 檔案大小限制
- 輸入資料驗證
- 錯誤訊息不洩露敏感資訊

## 開發與部署

### 開發環境
```bash
# 安裝開發依賴
pip install -r requirements.txt

# 啟動開發服務器
uvicorn app:app --reload
```

### 生產部署
```bash
# 使用Gunicorn
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker

# 使用Docker
docker build -t accuracy-evaluator .
docker run -p 8000:8000 accuracy-evaluator
```

## 技術架構

- **框架**: FastAPI
- **資料處理**: Pandas, NumPy
- **Excel處理**: openpyxl, xlrd
- **API文檔**: Swagger UI, ReDoc
- **錯誤處理**: 自定義例外類別
- **日誌**: Python logging

## 支援與維護

如有問題或建議，請聯繫開發團隊或提交Issue。
