#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify the final Excel format with model header
驗證最終的Excel格式（含模型標題）
"""

import pandas as pd
import os

def verify_final_format(filename: str = "output/test_[gemini2.5pro]身心障礙手冊_AI測試結果資料_result.xlsx"):
    """驗證最終的Excel格式"""
    
    if not os.path.exists(filename):
        print(f"❌ 檔案不存在: {filename}")
        return False
    
    print("=" * 60)
    print(f"驗證最終Excel格式: {filename}")
    print("=" * 60)
    
    try:
        # 讀取Excel檔案（不使用header，以便看到原始結構）
        df = pd.read_excel(filename, sheet_name='個別記錄分析', header=None)
        
        print(f"📊 資料大小: {len(df)} 行 x {len(df.columns)} 欄")
        print(f"📝 欄位名稱: {list(df.columns)}")
        print()
        
        # 驗證格式結構
        print("🔍 格式結構驗證:")
        
        # 檢查第一行（模型名稱）
        if len(df) > 0:
            row1 = df.iloc[0]
            model_cell = str(row1.iloc[0]) if len(row1) > 0 else ''
            cell_b1 = str(row1.iloc[1]) if len(row1) > 1 else ''
            cell_c1 = str(row1.iloc[2]) if len(row1) > 2 else ''
            
            print(f"  第1行: A1='{model_cell}' | B1='{cell_b1}' | C1='{cell_c1}'")
            
            if '模型' in model_cell:
                print("  ✅ 第1行包含模型名稱")
            else:
                print("  ❌ 第1行不包含模型名稱")
                
            if cell_b1 in ['nan', ''] and cell_c1 in ['nan', '']:
                print("  ✅ B1和C1為空（正確）")
            else:
                print("  ❌ B1和C1不為空")
        
        # 檢查第二行（標題）
        if len(df) > 1:
            row2 = df.iloc[1]
            headers = [str(cell) for cell in row2]
            print(f"  第2行: {headers}")
            
            expected_headers = ['受編', '欄位', '準確度']
            if headers == expected_headers:
                print("  ✅ 第2行標題正確")
            else:
                print(f"  ❌ 第2行標題不正確，期望: {expected_headers}")
        
        # 檢查資料行格式
        print(f"\n📋 資料行格式範例（前10行）:")
        for i in range(min(10, len(df))):
            row_data = []
            for j in range(3):  # 只顯示前3欄
                cell_value = str(df.iloc[i, j]) if j < len(df.columns) else ''
                if cell_value == 'nan':
                    cell_value = '[空]'
                row_data.append(cell_value)
            
            print(f"  行{i+1:2d}: {row_data[0]:<20} | {row_data[1]:<15} | {row_data[2]}")
        
        # 統計分析
        print(f"\n📊 內容統計:")
        
        # 統計受編數量（第一欄非空且不是標題的行）
        subject_count = 0
        for i in range(2, len(df)):  # 從第3行開始（跳過模型名稱和標題）
            cell_value = str(df.iloc[i, 0])
            if cell_value not in ['nan', '', '受編']:
                subject_count += 1
        
        print(f"  受編數量: {subject_count}")
        
        # 統計欄位類型
        field_counts = {}
        for i in range(2, len(df)):
            if len(df.columns) > 1:
                field_value = str(df.iloc[i, 1])
                if field_value not in ['nan', '', '欄位']:
                    field_counts[field_value] = field_counts.get(field_value, 0) + 1
        
        print(f"  欄位統計:")
        for field, count in field_counts.items():
            print(f"    {field}: {count} 次")
        
        print(f"\n✅ Excel格式驗證完成！")
        return True
        
    except Exception as e:
        print(f"❌ 驗證過程中發生錯誤: {e}")
        return False

def show_expected_format():
    """顯示期望的格式範例"""
    
    print("\n" + "=" * 60)
    print("期望的Excel格式範例")
    print("=" * 60)
    
    expected_format = """
Row 1: 模型 gemini-2.5-pro          [空]        [空]
Row 2: 受編                         欄位        準確度
Row 3: ZA24761194                  [空]        [空]
Row 4: [空]                        障礙類別     100.0%
Row 5: [空]                        ICD診斷      100.0%
Row 6: [空]                        整體準確度    100.00%
Row 7: [空]                        --- 分隔線 --- [空]
Row 8: MT00953431                  [空]        [空]
Row 9: [空]                        障礙類別     100.0%
...
"""
    
    print(expected_format)

if __name__ == "__main__":
    # 驗證gemini2.5pro檔案
    success1 = verify_final_format("output/test_[gemini2.5pro]身心障礙手冊_AI測試結果資料_result.xlsx")
    
    # 驗證gemma3檔案
    success2 = verify_final_format("output/test_[gemma3]身心障礙手冊_AI測試結果資料_result.xlsx")
    
    # 顯示期望格式
    show_expected_format()
    
    if success1 and success2:
        print("\n🎉 所有Excel格式驗證都成功！")
    else:
        print("\n❌ 部分Excel格式驗證失敗！")
