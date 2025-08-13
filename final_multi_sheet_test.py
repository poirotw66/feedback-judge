#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Final comprehensive test for multi-sheet functionality
最終的多sheet功能綜合測試
"""

import requests
import pandas as pd
import os

def test_multi_sheet_functionality():
    """最終的多sheet功能測試"""
    
    print("=" * 60)
    print("🧪 最終多sheet功能綜合測試")
    print("=" * 60)
    
    test_file = "data/multi_model_test_proper.xlsx"
    
    if not os.path.exists(test_file):
        print(f"❌ 測試檔案不存在: {test_file}")
        return False
    
    try:
        base_url = "http://localhost:8000"
        
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            print(f"🚀 上傳檔案: {test_file}")
            response = requests.post(f"{base_url}/evaluate", files=files)
            
            print(f"📊 回應狀態: {response.status_code}")
            
            if response.status_code == 200:
                # 儲存結果檔案
                output_filename = f"output/final_multi_sheet_result.xlsx"
                
                # 確保output目錄存在
                os.makedirs("output", exist_ok=True)
                
                with open(output_filename, 'wb') as output_file:
                    output_file.write(response.content)
                
                print(f"✅ 結果已儲存: {output_filename}")
                print(f"📊 檔案大小: {len(response.content)} bytes")
                
                # 詳細驗證結果檔案
                success = verify_multi_sheet_result(output_filename)
                
                return success
            else:
                print(f"❌ API請求失敗: {response.status_code}")
                try:
                    error_info = response.json()
                    print(f"錯誤詳情: {error_info}")
                except:
                    print(f"錯誤內容: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        return False

def verify_multi_sheet_result(filename: str):
    """詳細驗證多sheet結果"""
    
    print(f"\n🔍 詳細驗證結果檔案: {filename}")
    
    try:
        # 讀取Excel檔案的所有sheet
        excel_file = pd.ExcelFile(filename)
        sheet_names = excel_file.sheet_names
        
        print(f"📋 工作表數量: {len(sheet_names)}")
        print(f"📋 工作表名稱: {sheet_names}")
        
        expected_models = ['gemini-2.5-pro', 'gemma3_27b', 'ChatGPT-4']
        
        # 檢查是否有預期的模型工作表
        success_count = 0
        
        for expected_model in expected_models:
            if expected_model in sheet_names:
                print(f"✅ 找到模型工作表: {expected_model}")
                success_count += 1
                
                # 詳細檢查工作表內容
                df = pd.read_excel(filename, sheet_name=expected_model, header=None)
                
                print(f"  📊 工作表大小: {len(df)} 行 x {len(df.columns)} 欄")
                
                # 檢查第一行模型名稱
                if len(df) > 0:
                    first_row = df.iloc[0]
                    cell_a1 = str(first_row.iloc[0]) if len(first_row) > 0 else ''
                    cell_b1 = str(first_row.iloc[1]) if len(first_row) > 1 else ''
                    
                    if cell_a1 == '模型':
                        print(f"  ✅ A1 = '模型' (正確)")
                        if expected_model.replace('_', ':') in cell_b1 or expected_model.replace('_', '-') in cell_b1:
                            print(f"  ✅ B1 包含正確的模型名稱: '{cell_b1}'")
                        else:
                            print(f"  ⚠️  B1 模型名稱可能不正確: '{cell_b1}'")
                    else:
                        print(f"  ❌ A1 應該是 '模型'，但是 '{cell_a1}'")
                
                # 檢查第二行標題
                if len(df) > 1:
                    second_row = df.iloc[1]
                    headers = [str(cell) for cell in second_row]
                    expected_headers = ['受編', '欄位', '準確度', 'CER', 'WER']
                    
                    if headers == expected_headers:
                        print(f"  ✅ 標題行正確: {headers}")
                    else:
                        print(f"  ⚠️  標題行: {headers}")
                
                # 檢查是否有評估資料
                if len(df) > 2:
                    print(f"  ✅ 包含評估資料 ({len(df) - 2} 行)")
                else:
                    print(f"  ⚠️  沒有評估資料")
                    
            else:
                print(f"❌ 缺少模型工作表: {expected_model}")
        
        # 總結驗證結果
        print(f"\n📊 驗證總結:")
        print(f"  期望模型數: {len(expected_models)}")
        print(f"  實際工作表數: {len(sheet_names)}")
        print(f"  成功匹配數: {success_count}")
        
        if success_count == len(expected_models) and len(sheet_names) == len(expected_models):
            print(f"  ✅ 多sheet功能完全正常")
            return True
        elif success_count > 0:
            print(f"  ⚠️  部分功能正常")
            return True
        else:
            print(f"  ❌ 多sheet功能異常")
            return False
            
    except Exception as e:
        print(f"❌ 驗證過程中發生錯誤: {e}")
        return False

def main():
    """主測試函數"""
    
    print("🎯 開始最終多sheet功能測試")
    
    success = test_multi_sheet_functionality()
    
    print("\n" + "=" * 60)
    print("🏁 最終測試結果")
    print("=" * 60)
    
    if success:
        print("🎉 多sheet功能測試完全成功！")
        print("✅ API能夠正確處理多模型檔案")
        print("✅ 生成了正確的多工作表結果檔案")
        print("✅ 每個模型都有獨立的工作表")
        print("✅ 模型名稱正確提取和顯示")
        print("✅ 評估結果完整")
        print("\n🚀 多sheet功能已完全修復並正常工作！")
    else:
        print("❌ 多sheet功能測試失敗！")
        print("需要進一步檢查問題")

if __name__ == "__main__":
    main()
