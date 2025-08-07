#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify the simplified Excel output structure
驗證簡化的Excel輸出結構
"""

import pandas as pd
import os

def verify_simplified_excel(filename: str = "gemma3_result.xlsx"):
    """驗證簡化的Excel檔案結構"""
    
    if not os.path.exists(filename):
        print(f"❌ 檔案不存在: {filename}")
        return False
    
    print("=" * 60)
    print(f"驗證簡化Excel檔案結構: {filename}")
    print("=" * 60)
    
    try:
        # 讀取Excel檔案的所有工作表
        excel_file = pd.ExcelFile(filename)
        sheet_names = excel_file.sheet_names
        
        print(f"📊 工作表數量: {len(sheet_names)}")
        print(f"📋 工作表名稱: {sheet_names}")
        
        # 檢查是否只有一個工作表
        if len(sheet_names) != 1:
            print(f"❌ 錯誤：應該只有1個工作表，但發現 {len(sheet_names)} 個")
            return False
        
        # 檢查工作表名稱
        if sheet_names[0] != '個別記錄分析':
            print(f"❌ 錯誤：工作表名稱應該是 '個別記錄分析'，但是 '{sheet_names[0]}'")
            return False
        
        print("✅ 工作表數量和名稱正確")
        
        # 讀取工作表內容
        df = pd.read_excel(filename, sheet_name='個別記錄分析')
        
        print(f"📏 資料大小: {len(df)} 行 x {len(df.columns)} 欄")
        print(f"📝 欄位名稱: {list(df.columns)}")
        
        # 檢查欄位名稱
        expected_columns = ['受編', '欄位', '準確度']
        if list(df.columns) != expected_columns:
            print(f"❌ 錯誤：欄位名稱應該是 {expected_columns}，但是 {list(df.columns)}")
            return False
        
        print("✅ 欄位名稱正確")
        
        # 顯示前幾行資料來驗證格式
        print("\n📋 資料格式驗證:")
        print("前15行資料:")
        
        for i, (idx, row) in enumerate(df.head(15).iterrows()):
            subject = row['受編'] if pd.notna(row['受編']) and row['受編'] != '' else ''
            field = row['欄位'] if pd.notna(row['欄位']) and row['欄位'] != '' else ''
            accuracy = row['準確度'] if pd.notna(row['準確度']) and row['準確度'] != '' else ''
            
            print(f"  行{i+1:2d}: 受編='{subject}' | 欄位='{field}' | 準確度='{accuracy}'")
        
        # 統計分析
        print(f"\n📊 統計分析:")
        
        # 統計受編數量
        subject_rows = df[df['受編'].notna() & (df['受編'] != '')]
        unique_subjects = subject_rows['受編'].nunique()
        print(f"   受編數量: {unique_subjects}")
        
        # 統計分隔線數量
        separator_rows = df[df['欄位'] == '--- 分隔線 ---']
        print(f"   分隔線數量: {len(separator_rows)}")
        
        # 統計整體準確度行數量
        overall_rows = df[df['欄位'] == '整體準確度']
        print(f"   整體準確度行數量: {len(overall_rows)}")
        
        # 檢查格式是否正確
        if unique_subjects == len(overall_rows) == len(separator_rows):
            print("✅ 資料格式正確：每個受編都有對應的整體準確度和分隔線")
        else:
            print("❌ 資料格式錯誤：受編、整體準確度、分隔線數量不一致")
            return False
        
        print(f"\n🎉 簡化Excel檔案驗證成功！")
        return True
        
    except Exception as e:
        print(f"❌ 驗證過程中發生錯誤: {e}")
        return False

def show_sample_format(filename: str = "gemma3_result.xlsx", num_subjects: int = 2):
    """顯示範例格式"""
    
    try:
        df = pd.read_excel(filename, sheet_name='個別記錄分析')
        
        print("=" * 60)
        print("範例格式顯示")
        print("=" * 60)
        
        current_subject = None
        subject_count = 0
        
        for _, row in df.iterrows():
            if subject_count >= num_subjects:
                break
            
            subject = row['受編'] if pd.notna(row['受編']) and row['受編'] != '' else ''
            field = row['欄位'] if pd.notna(row['欄位']) and row['欄位'] != '' else ''
            accuracy = row['準確度'] if pd.notna(row['準確度']) and row['準確度'] != '' else ''
            
            if subject and subject != current_subject:
                current_subject = subject
                subject_count += 1
                print(f"{subject}")
            elif field:
                print(f"              {field:<12} {accuracy}")
        
    except Exception as e:
        print(f"❌ 顯示範例時發生錯誤: {e}")

if __name__ == "__main__":
    # 驗證檔案結構
    success = verify_simplified_excel()
    
    if success:
        print()
        # 顯示範例格式
        show_sample_format()
    
    print("\n📋 簡化Excel檔案驗證完成！")
