#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Script for Disability Certificate AI Accuracy Evaluator API
身心障礙手冊AI測試結果準確度評分系統 - API測試腳本
"""

import requests
import pandas as pd
import io
import os
import time
from datetime import datetime

def create_test_excel_file(filename: str = "test_data.xlsx"):
    """建立測試用的Excel檔案"""
    data = {
        '編號': [1, 2, 3, 4, 5],
        '受編': ['ZA24761194', 'MT00953431', 'AB12345678', 'CD98765432', 'EF11223344'],
        '正面_障礙等級': ['輕度', '中度', '重度', '輕度', '中度'],
        '正面_障礙類別': ['其他類', '第1類【12.2】', '第2類【13.1】', '其他類', '第1類【12.3】'],
        '正面_ICD診斷': ['【換16.1】', '【換12.2】', '【換13.1】', '【換16.2】', '【換12.3】'],
        '正面_備註': ['', '', '', '', ''],
        '反面_障礙等級': ['輕度', '中度', '重度', '輕度', '中度'],
        '反面_證明手冊': ['身心障礙證明', '身心障礙證明', '身心障礙證明', '身心障礙證明', '身心障礙證明'],
        '反面_障礙類別': ['障礙類別：其他類', '第1類【12.2】', '第2類【13.1】', '其他類', '第1類【12.3】'],
        '反面_ICD診斷': ['【換16.1】', '【第12.2】', '【換13.1】', '【換16.2】', '【換12.3】']
    }
    
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    print(f"測試檔案已建立: {filename}")
    return filename

def test_api_health(base_url: str = "http://localhost:8000"):
    """測試API健康檢查"""
    print("\n=== 測試API健康檢查 ===")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            print(f"回應: {response.json()}")
            return True
        else:
            print(f"錯誤: {response.text}")
            return False
    except Exception as e:
        print(f"連線錯誤: {str(e)}")
        return False

def test_api_root(base_url: str = "http://localhost:8000"):
    """測試API根端點"""
    print("\n=== 測試API根端點 ===")
    try:
        response = requests.get(f"{base_url}/")
        print(f"狀態碼: {response.status_code}")
        if response.status_code == 200:
            print(f"回應: {response.json()}")
            return True
        else:
            print(f"錯誤: {response.text}")
            return False
    except Exception as e:
        print(f"連線錯誤: {str(e)}")
        return False

def test_file_upload_evaluation(base_url: str = "http://localhost:8000", test_file: str = "test_data.xlsx"):
    """測試檔案上傳和評估"""
    print("\n=== 測試檔案上傳和評估 ===")
    
    if not os.path.exists(test_file):
        print(f"測試檔案不存在: {test_file}")
        return False
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            print(f"上傳檔案: {test_file}")
            start_time = time.time()
            
            response = requests.post(f"{base_url}/evaluate", files=files)
            
            processing_time = time.time() - start_time
            print(f"處理時間: {processing_time:.2f}秒")
            print(f"狀態碼: {response.status_code}")
            
            if response.status_code == 200:
                # 儲存結果檔案
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"test_result_{timestamp}.xlsx"
                
                with open(output_filename, 'wb') as output_file:
                    output_file.write(response.content)
                
                print(f"評估成功！結果已儲存至: {output_filename}")
                print(f"檔案大小: {len(response.content)} bytes")
                
                # 檢查回應標頭
                content_disposition = response.headers.get('Content-Disposition')
                if content_disposition:
                    print(f"Content-Disposition: {content_disposition}")
                
                return True
            else:
                print(f"評估失敗: {response.status_code}")
                try:
                    error_info = response.json()
                    print(f"錯誤詳情: {error_info}")
                except:
                    print(f"錯誤內容: {response.text}")
                return False
                
    except Exception as e:
        print(f"測試過程中發生錯誤: {str(e)}")
        return False

def test_invalid_file_format(base_url: str = "http://localhost:8000"):
    """測試無效檔案格式"""
    print("\n=== 測試無效檔案格式 ===")
    
    # 建立一個文字檔案
    test_content = "這不是Excel檔案"
    
    try:
        files = {'file': ('test.txt', io.StringIO(test_content), 'text/plain')}
        response = requests.post(f"{base_url}/evaluate", files=files)
        
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 400:
            print("正確拒絕了無效檔案格式")
            try:
                error_info = response.json()
                print(f"錯誤訊息: {error_info}")
            except:
                print(f"錯誤內容: {response.text}")
            return True
        else:
            print("應該要拒絕無效檔案格式")
            return False
            
    except Exception as e:
        print(f"測試過程中發生錯誤: {str(e)}")
        return False

def test_empty_file(base_url: str = "http://localhost:8000"):
    """測試空檔案"""
    print("\n=== 測試空檔案 ===")
    
    try:
        files = {'file': ('empty.xlsx', io.BytesIO(b''), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
        response = requests.post(f"{base_url}/evaluate", files=files)
        
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 400:
            print("正確拒絕了空檔案")
            try:
                error_info = response.json()
                print(f"錯誤訊息: {error_info}")
            except:
                print(f"錯誤內容: {response.text}")
            return True
        else:
            print("應該要拒絕空檔案")
            return False
            
    except Exception as e:
        print(f"測試過程中發生錯誤: {str(e)}")
        return False

def run_all_tests(base_url: str = "http://localhost:8000"):
    """執行所有測試"""
    print("=" * 60)
    print("身心障礙手冊AI測試結果準確度評分系統 - API測試")
    print("=" * 60)
    
    # 建立測試檔案
    test_file = create_test_excel_file()
    
    # 執行測試
    tests = [
        ("API根端點", lambda: test_api_root(base_url)),
        ("API健康檢查", lambda: test_api_health(base_url)),
        ("檔案上傳和評估", lambda: test_file_upload_evaluation(base_url, test_file)),
        ("無效檔案格式", lambda: test_invalid_file_format(base_url)),
        ("空檔案", lambda: test_empty_file(base_url))
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"測試 {test_name} 發生例外: {str(e)}")
            results.append((test_name, False))
    
    # 顯示測試結果摘要
    print("\n" + "=" * 60)
    print("測試結果摘要")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    # 清理測試檔案
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"已清理測試檔案: {test_file}")
    
    return passed == total

if __name__ == "__main__":
    import sys
    
    base_url = "http://localhost:8000"
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    print(f"測試API端點: {base_url}")
    
    success = run_all_tests(base_url)
    
    if success:
        print("\n🎉 所有測試都通過了！")
        sys.exit(0)
    else:
        print("\n❌ 有測試失敗，請檢查API服務")
        sys.exit(1)
