#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verify the Gemini2.5pro result file
驗證Gemini2.5pro結果檔案
"""

import pandas as pd
import os

def verify_gemini_result(filename: str = "gemini2.5pro_result.xlsx"):
    """驗證Gemini2.5pro結果檔案"""
    
    if not os.path.exists(filename):
        print(f"❌ 檔案不存在: {filename}")
        return False
    
    print("=" * 60)
    print(f"驗證Gemini2.5pro結果檔案: {filename}")
    print("=" * 60)
    
    try:
        # 讀取Excel檔案
        df = pd.read_excel(filename, sheet_name='個別記錄分析')
        
        print(f"📊 資料大小: {len(df)} 行 x {len(df.columns)} 欄")
        print(f"📝 欄位名稱: {list(df.columns)}")
        print()
        
        # 分析資料內容
        print("📋 前20行資料:")
        for i, (idx, row) in enumerate(df.head(20).iterrows()):
            subject = row['受編'] if pd.notna(row['受編']) and row['受編'] != '' else ''
            field = row['欄位'] if pd.notna(row['欄位']) and row['欄位'] != '' else ''
            accuracy = row['準確度'] if pd.notna(row['準確度']) and row['準確度'] != '' else ''
            
            if subject:
                print(f"  行{i+1:2d}: 受編='{subject}'")
            elif field:
                print(f"  行{i+1:2d}:              欄位='{field}' | 準確度='{accuracy}'")
        
        # 統計分析
        print(f"\n📊 統計分析:")
        
        # 統計受編數量
        subject_rows = df[df['受編'].notna() & (df['受編'] != '')]
        unique_subjects = subject_rows['受編'].nunique()
        print(f"   受編數量: {unique_subjects}")
        
        # 統計各欄位出現次數
        field_counts = df[df['欄位'].notna() & (df['欄位'] != '')]['欄位'].value_counts()
        print(f"   欄位統計:")
        for field, count in field_counts.items():
            if field not in ['整體準確度', '--- 分隔線 ---']:
                print(f"     {field}: {count} 次")
        
        # 檢查是否有障礙等級的準確度
        level_rows = df[df['欄位'] == '障礙等級']
        if len(level_rows) > 0:
            print(f"\n⚠️  發現 {len(level_rows)} 個障礙等級準確度記錄")
            print("   這可能是問題，因為Gemini2.5pro檔案沒有障礙等級的預測結果")
            
            # 顯示障礙等級的準確度值
            for _, row in level_rows.head(3).iterrows():
                print(f"     受編: {row.get('受編', 'N/A')}, 準確度: {row.get('準確度', 'N/A')}")
        else:
            print(f"\n✅ 沒有發現障礙等級準確度記錄（正確）")
        
        return True
        
    except Exception as e:
        print(f"❌ 驗證過程中發生錯誤: {e}")
        return False

if __name__ == "__main__":
    verify_gemini_result()
