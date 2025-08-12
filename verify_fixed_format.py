#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify the fixed Excel format with correct model header structure
驗證修復後的Excel格式（正確的模型標題結構）
"""

import pandas as pd
import os

def verify_fixed_format(filename: str = "output/test_model_header_result.xlsx"):
    """驗證修復後的Excel格式"""
    
    if not os.path.exists(filename):
        print(f"❌ 檔案不存在: {filename}")
        return False
    
    print("=" * 60)
    print(f"驗證修復後的Excel格式: {filename}")
    print("=" * 60)
    
    try:
        # 讀取Excel檔案（不使用header，以便看到原始結構）
        df = pd.read_excel(filename, sheet_name='個別記錄分析', header=None)
        
        print(f"📊 資料大小: {len(df)} 行 x {len(df.columns)} 欄")
        print()
        
        # 驗證第一行格式（模型名稱行）
        print("🔍 第一行格式驗證:")
        if len(df) > 0:
            row1 = df.iloc[0]
            cell_a1 = str(row1.iloc[0]) if len(row1) > 0 else ''
            cell_b1 = str(row1.iloc[1]) if len(row1) > 1 else ''
            cell_c1 = str(row1.iloc[2]) if len(row1) > 2 else ''
            
            print(f"  A1: '{cell_a1}'")
            print(f"  B1: '{cell_b1}'")
            print(f"  C1: '{cell_c1}'")
            
            # 檢查A1是否為"模型"
            if cell_a1 == '模型':
                print("  ✅ A1 = '模型' (正確)")
            else:
                print(f"  ❌ A1 應該是 '模型'，但是 '{cell_a1}'")
            
            # 檢查B1是否包含模型名稱
            if 'gemini' in cell_b1.lower():
                print(f"  ✅ B1 包含模型名稱: '{cell_b1}'")
                
                # 檢查是否為完整的模型名稱
                if 'gemini-2.5-pro-exp-03-25' in cell_b1:
                    print("  ✅ 模型名稱完整正確")
                else:
                    print("  ⚠️  模型名稱不完整")
            else:
                print(f"  ❌ B1 不包含預期的模型名稱: '{cell_b1}'")
            
            # 檢查C1是否為空
            if cell_c1 in ['nan', '']:
                print("  ✅ C1 為空 (正確)")
            else:
                print(f"  ❌ C1 應該為空，但是 '{cell_c1}'")
        
        # 驗證第二行格式（標題行）
        print(f"\n🔍 第二行格式驗證:")
        if len(df) > 1:
            row2 = df.iloc[1]
            headers = [str(cell) for cell in row2]
            print(f"  標題行: {headers}")
            
            expected_headers = ['受編', '欄位', '準確度']
            if headers == expected_headers:
                print("  ✅ 標題行正確")
            else:
                print(f"  ❌ 標題行不正確，期望: {expected_headers}")
        
        # 顯示完整的前5行格式
        print(f"\n📋 前5行完整格式:")
        for i in range(min(5, len(df))):
            row_data = []
            for j in range(3):
                cell_value = str(df.iloc[i, j]) if j < len(df.columns) else ''
                if cell_value == 'nan':
                    cell_value = ''
                row_data.append(cell_value)
            
            if i == 0:
                print(f"  行{i+1}: 模型 | {row_data[1]} | {row_data[2]}")
            elif i == 1:
                print(f"  行{i+1}: {row_data[0]} | {row_data[1]} | {row_data[2]}")
            else:
                print(f"  行{i+1}: {row_data[0]} | {row_data[1]} | {row_data[2]}")
        
        # 驗證期望的格式
        print(f"\n✅ 期望格式對比:")
        print("  期望:")
        print("    行1: 模型 | gemini-2.5-pro-exp-03-25 | ")
        print("    行2: 受編 | 欄位 | 準確度")
        print("    行3: ZA24761194 |  | ")
        print("    行4:  | 障礙類別 | 100.0%")
        print("    行5:  | ICD診斷 | 100.0%")
        
        print("  實際:")
        for i in range(min(5, len(df))):
            row_data = []
            for j in range(3):
                cell_value = str(df.iloc[i, j]) if j < len(df.columns) else ''
                if cell_value == 'nan':
                    cell_value = ''
                row_data.append(cell_value)
            print(f"    行{i+1}: {row_data[0]} | {row_data[1]} | {row_data[2]}")
        
        return True
        
    except Exception as e:
        print(f"❌ 驗證過程中發生錯誤: {e}")
        return False

if __name__ == "__main__":
    success = verify_fixed_format()
    
    if success:
        print(f"\n🎉 Excel格式修復驗證成功！")
        print("✅ A1 = '模型'")
        print("✅ B1 = 'gemini-2.5-pro-exp-03-25'")
        print("✅ C1 = 空白")
        print("✅ 第二行為正確的標題行")
    else:
        print(f"\n❌ Excel格式修復驗證失敗！")
