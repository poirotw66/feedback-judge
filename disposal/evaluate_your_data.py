#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to help users evaluate their own Excel files
幫助使用者評估自己Excel檔案的腳本
"""

import requests
import os
import sys
from datetime import datetime

def evaluate_excel_file(file_path: str, api_url: str = "http://localhost:8000"):
    """評估Excel檔案"""
    
    print("=" * 60)
    print("身心障礙手冊AI測試結果準確度評分系統")
    print("=" * 60)
    
    # 檢查檔案是否存在
    if not os.path.exists(file_path):
        print(f"❌ 檔案不存在: {file_path}")
        return False
    
    # 檢查檔案格式
    if not file_path.lower().endswith(('.xlsx', '.xls')):
        print(f"❌ 不支援的檔案格式: {file_path}")
        print("請使用 .xlsx 或 .xls 格式的Excel檔案")
        return False
    
    # 檢查檔案大小
    file_size = os.path.getsize(file_path)
    if file_size > 10 * 1024 * 1024:  # 10MB
        print(f"❌ 檔案過大: {file_size / 1024 / 1024:.2f}MB")
        print("檔案大小不能超過 10MB")
        return False
    
    print(f"📁 檔案: {file_path}")
    print(f"📊 大小: {file_size / 1024:.2f}KB")
    
    # 檢查API服務是否運行
    try:
        health_response = requests.get(f"{api_url}/health", timeout=5)
        if health_response.status_code != 200:
            print(f"❌ API服務無法連接: {api_url}")
            print("請確保API服務正在運行：python start_api.py")
            return False
    except requests.exceptions.RequestException:
        print(f"❌ API服務無法連接: {api_url}")
        print("請確保API服務正在運行：python start_api.py")
        return False
    
    print(f"✅ API服務正常: {api_url}")
    
    # 上傳檔案進行評估
    try:
        print("\n🔄 正在上傳和評估檔案...")
        
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            start_time = datetime.now()
            response = requests.post(f"{api_url}/evaluate", files=files, timeout=120)
            end_time = datetime.now()
            
            processing_time = (end_time - start_time).total_seconds()
            
            print(f"⏱️  處理時間: {processing_time:.2f}秒")
            print(f"📡 狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                # 生成輸出檔案名稱
                base_name = os.path.splitext(os.path.basename(file_path))[0]
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{base_name}_accuracy_evaluation_{timestamp}.xlsx"
                
                # 儲存結果檔案
                with open(output_filename, 'wb') as output_file:
                    output_file.write(response.content)
                
                print(f"\n🎉 評估成功！")
                print(f"📄 結果檔案: {output_filename}")
                print(f"📊 檔案大小: {len(response.content) / 1024:.2f}KB")
                
                # 檢查回應標頭
                content_disposition = response.headers.get('Content-Disposition')
                if content_disposition:
                    print(f"📎 下載檔名: {content_disposition}")
                
                print(f"\n📋 結果檔案包含以下工作表:")
                print(f"   1. 評估摘要 - 整體統計和各欄位準確度")
                print(f"   2. 記錄摘要 - 每筆記錄的準確度摘要")
                print(f"   3. 詳細欄位比較 - 逐欄位的詳細比較結果")
                print(f"   4. 欄位統計 - 各欄位的統計分析")
                print(f"   5. 錯誤分析 - 錯誤類型分析和改進建議")
                print(f"   6. 原始資料 - 上傳的原始資料")
                print(f"   7. 準確度分佈 - 準確度等級分佈統計")
                
                return True
                
            else:
                print(f"\n❌ 評估失敗: {response.status_code}")
                try:
                    error_info = response.json()
                    print(f"錯誤類型: {error_info.get('details', {}).get('error_type', '未知')}")
                    print(f"錯誤訊息: {error_info.get('message', '無詳細訊息')}")
                    
                    # 提供具體的解決建議
                    error_type = error_info.get('details', {}).get('error_type', '')
                    if error_type == 'file_validation_error':
                        print(f"\n💡 解決建議:")
                        print(f"   - 確保檔案格式為 .xlsx 或 .xls")
                        print(f"   - 檢查檔案是否損壞")
                        print(f"   - 確認檔案大小不超過 10MB")
                    elif error_type == 'data_validation_error':
                        print(f"\n💡 解決建議:")
                        print(f"   - 檢查Excel檔案是否包含必要的欄位")
                        print(f"   - 確保有障礙等級、障礙類別、ICD診斷等欄位")
                        print(f"   - 檢查是否有重複的欄位名稱")
                        missing_cols = error_info.get('details', {}).get('missing_columns', [])
                        if missing_cols:
                            print(f"   - 缺少的欄位: {missing_cols}")
                    
                except:
                    print(f"錯誤內容: {response.text}")
                
                return False
                
    except requests.exceptions.Timeout:
        print(f"❌ 請求超時，檔案可能太大或處理時間過長")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 網路錯誤: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ 未預期的錯誤: {str(e)}")
        return False

def main():
    """主程式"""
    if len(sys.argv) < 2:
        print("使用方式: python evaluate_your_data.py <Excel檔案路徑> [API網址]")
        print("")
        print("範例:")
        print("  python evaluate_your_data.py my_data.xlsx")
        print("  python evaluate_your_data.py my_data.xlsx http://localhost:8000")
        print("")
        print("注意:")
        print("  - 請確保API服務正在運行：python start_api.py")
        print("  - 支援的檔案格式：.xlsx, .xls")
        print("  - 檔案大小限制：10MB")
        return
    
    file_path = sys.argv[1]
    api_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:8000"
    
    success = evaluate_excel_file(file_path, api_url)
    
    if success:
        print(f"\n✨ 評估完成！請檢查生成的結果檔案。")
    else:
        print(f"\n💔 評估失敗，請檢查上述錯誤訊息並重試。")
        print(f"\n🔧 故障排除:")
        print(f"   1. 確保API服務正在運行：python start_api.py")
        print(f"   2. 檢查Excel檔案格式和內容")
        print(f"   3. 參考 USER_GUIDE.md 了解詳細要求")

if __name__ == "__main__":
    main()
