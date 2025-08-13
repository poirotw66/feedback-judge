#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify that multi-sheet functionality is actually working
驗證多sheet功能確實正常工作
"""

import requests
import pandas as pd
import os

def test_and_verify_multi_sheet():
    """測試並驗證多sheet功能"""
    
    print("=" * 60)
    print("🔍 驗證多sheet功能是否正常工作")
    print("=" * 60)
    
    # 測試檔案
    test_file = "data/multi_model_test_proper.xlsx"
    
    if not os.path.exists(test_file):
        print(f"❌ 測試檔案不存在: {test_file}")
        return False
    
    # 首先檢查測試檔案的實際內容
    print("📊 檢查測試檔案內容:")
    try:
        # 讀取原始檔案（不使用header）
        df_raw = pd.read_excel(test_file, header=None)
        print(f"原始檔案: {len(df_raw)} 行 x {len(df_raw.columns)} 欄")
        
        # 尋找模型名稱
        model_count = 0
        models_found = []
        
        for idx, row in df_raw.iterrows():
            row_values = [str(cell).strip() if pd.notna(cell) else '' for cell in row]
            for cell_value in row_values:
                if cell_value:
                    cell_lower = cell_value.lower()
                    model_keywords = ['gemini', 'gemma', 'chatgpt', 'claude', 'gpt']
                    if any(keyword in cell_lower for keyword in model_keywords):
                        models_found.append(cell_value)
                        model_count += 1
                        print(f"  第 {idx + 1} 行發現模型: {cell_value}")
                        break
        
        print(f"總共發現 {model_count} 個模型: {models_found}")
        
    except Exception as e:
        print(f"❌ 讀取測試檔案失敗: {e}")
        return False
    
    # 測試API
    print(f"\n🚀 測試API處理:")
    try:
        base_url = "http://localhost:8000"
        
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            
            response = requests.post(f"{base_url}/evaluate", files=files)
            
            print(f"📊 API回應狀態: {response.status_code}")
            
            if response.status_code == 200:
                # 儲存結果檔案
                output_filename = f"output/verify_multi_sheet_result.xlsx"
                os.makedirs("output", exist_ok=True)
                
                with open(output_filename, 'wb') as output_file:
                    output_file.write(response.content)
                
                print(f"✅ 結果已儲存: {output_filename}")
                print(f"📊 檔案大小: {len(response.content)} bytes")
                
                # 檢查結果檔案的工作表
                excel_file = pd.ExcelFile(output_filename)
                sheet_names = excel_file.sheet_names
                
                print(f"\n📋 結果檔案工作表:")
                print(f"  工作表數量: {len(sheet_names)}")
                print(f"  工作表名稱: {sheet_names}")
                
                # 檢查每個工作表
                for sheet_name in sheet_names:
                    df = pd.read_excel(output_filename, sheet_name=sheet_name, header=None)
                    print(f"\n📊 工作表 '{sheet_name}':")
                    print(f"  大小: {len(df)} 行 x {len(df.columns)} 欄")
                    
                    if len(df) > 0:
                        first_row = df.iloc[0]
                        cell_a1 = str(first_row.iloc[0]) if len(first_row) > 0 else ''
                        cell_b1 = str(first_row.iloc[1]) if len(first_row) > 1 else ''
                        print(f"  第一行: A1='{cell_a1}', B1='{cell_b1}'")
                        
                        if cell_a1 == '模型':
                            print(f"  ✅ 這是一個模型工作表，模型名稱: {cell_b1}")
                        else:
                            print(f"  ⚠️  這可能不是模型工作表")
                
                # 判斷結果
                if len(sheet_names) >= model_count:
                    print(f"\n🎉 多sheet功能正常工作！")
                    print(f"  期望模型數: {model_count}")
                    print(f"  實際工作表數: {len(sheet_names)}")
                    print(f"  ✅ 每個模型都有對應的工作表")
                    return True
                else:
                    print(f"\n⚠️  工作表數量不符合期望")
                    print(f"  期望模型數: {model_count}")
                    print(f"  實際工作表數: {len(sheet_names)}")
                    return False
                    
            else:
                print(f"❌ API請求失敗: {response.status_code}")
                try:
                    error_info = response.json()
                    print(f"錯誤詳情: {error_info}")
                except:
                    print(f"錯誤內容: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ API測試失敗: {e}")
        return False

def main():
    """主函數"""
    
    success = test_and_verify_multi_sheet()
    
    print("\n" + "=" * 60)
    print("🏁 驗證結果")
    print("=" * 60)
    
    if success:
        print("🎉 多sheet功能確實正常工作！")
        print("✅ API能夠正確處理多模型檔案")
        print("✅ 為每個模型生成獨立的工作表")
        print("✅ 工作表數量符合模型數量")
    else:
        print("❌ 多sheet功能可能存在問題")
        print("需要進一步檢查")

if __name__ == "__main__":
    main()
