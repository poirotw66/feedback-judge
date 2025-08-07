#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test the API with user's data format
測試使用者資料格式的API
"""

import requests
import os

def test_user_format_api():
    """測試使用者格式的API"""
    
    base_url = "http://localhost:8000"
    test_file = "user_format_test_data.xlsx"
    
    if not os.path.exists(test_file):
        print(f"測試檔案不存在: {test_file}")
        print("請先執行 python create_test_data_user_format.py")
        return False
    
    print("=" * 60)
    print("測試使用者資料格式的API")
    print("=" * 60)
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            print(f"上傳檔案: {test_file}")
            response = requests.post(f"{base_url}/evaluate", files=files)
            
            print(f"狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                # 儲存結果檔案
                output_filename = "user_format_result.xlsx"
                
                with open(output_filename, 'wb') as output_file:
                    output_file.write(response.content)
                
                print(f"✅ 評估成功！結果已儲存至: {output_filename}")
                print(f"檔案大小: {len(response.content)} bytes")
                
                # 檢查回應標頭
                content_disposition = response.headers.get('Content-Disposition')
                if content_disposition:
                    print(f"Content-Disposition: {content_disposition}")
                
                return True
            else:
                print(f"❌ 評估失敗: {response.status_code}")
                try:
                    error_info = response.json()
                    print(f"錯誤詳情: {error_info}")
                except:
                    print(f"錯誤內容: {response.text}")
                return False
                
    except Exception as e:
        print(f"測試過程中發生錯誤: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_user_format_api()
    if success:
        print("\n🎉 使用者格式測試成功！")
    else:
        print("\n❌ 使用者格式測試失敗！")
