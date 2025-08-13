#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create a proper multi-model test Excel file
創建正確的多模型測試Excel檔案
"""

import pandas as pd
import os

def create_multi_model_test_file():
    """創建多模型測試檔案"""
    
    print("🔧 創建多模型測試檔案...")
    
    # 創建多模型測試資料
    test_data = []
    
    # 空行
    test_data.append(['', '', '', '', '', '', '', '', '', ''])
    
    # 模型1: Gemini
    test_data.append(['模型', 'gemini-2.5-pro', '', '', '', '', '', '', '', ''])
    test_data.append(['編號', '受編', '障礙等級', '障礙類別', 'ICD診斷', '備註', '障礙等級', '障礙類別', 'ICD診斷', '備註'])
    test_data.append(['1', 'A001', '輕度', '第1類', 'F70', '', '輕度', '第1類', 'F70', ''])
    test_data.append(['2', 'A002', '中度', '第2類', 'F71', '', '中度', '第2類', 'F71', ''])
    test_data.append(['3', 'A003', '重度', '第3類', 'F72', '', '重度', '第3類', 'F72', ''])
    
    # 空行
    test_data.append(['', '', '', '', '', '', '', '', '', ''])
    
    # 模型2: Gemma
    test_data.append(['模型', 'gemma3:27b', '', '', '', '', '', '', '', ''])
    test_data.append(['編號', '受編', '障礙等級', '障礙類別', 'ICD診斷', '備註', '障礙等級', '障礙類別', 'ICD診斷', '備註'])
    test_data.append(['1', 'A001', '輕度', '第1類', 'F70', '', '輕度', '第1類', 'F70', ''])
    test_data.append(['2', 'A002', '中度', '第2類', 'F71', '', '重度', '第3類', 'F72', ''])  # 故意錯誤
    test_data.append(['3', 'A003', '重度', '第3類', 'F72', '', '中度', '第2類', 'F71', ''])  # 故意錯誤
    
    # 空行
    test_data.append(['', '', '', '', '', '', '', '', '', ''])
    
    # 模型3: ChatGPT
    test_data.append(['模型', 'ChatGPT-4', '', '', '', '', '', '', '', ''])
    test_data.append(['編號', '受編', '障礙等級', '障礙類別', 'ICD診斷', '備註', '障礙等級', '障礙類別', 'ICD診斷', '備註'])
    test_data.append(['1', 'A001', '輕度', '第1類', 'F70', '', '輕度', '第1類', 'F70', ''])
    test_data.append(['2', 'A002', '中度', '第2類', 'F71', '', '中度', '第2類', 'F71', ''])
    test_data.append(['3', 'A003', '重度', '第3類', 'F72', '', '極重度', '第4類', 'F73', ''])  # 故意錯誤
    
    # 創建DataFrame
    columns = ['col1', 'col2', 'col3', 'col4', 'col5', 'col6', 'col7', 'col8', 'col9', 'col10']
    df = pd.DataFrame(test_data, columns=columns)
    
    # 儲存為Excel檔案
    output_file = "data/multi_model_test_proper.xlsx"
    
    # 確保data目錄存在
    os.makedirs("data", exist_ok=True)
    
    df.to_excel(output_file, index=False, header=False)
    
    print(f"✅ 多模型測試檔案已創建: {output_file}")
    print(f"📊 檔案大小: {len(df)} 行 x {len(df.columns)} 欄")
    
    # 顯示檔案內容預覽
    print(f"\n📋 檔案內容預覽:")
    for i, row in df.head(10).iterrows():
        print(f"  行{i+1}: {list(row)}")
    
    print(f"\n🎯 包含的模型:")
    print(f"  1. gemini-2.5-pro (3筆資料)")
    print(f"  2. gemma3:27b (3筆資料，包含錯誤)")
    print(f"  3. ChatGPT-4 (3筆資料，包含錯誤)")
    
    return output_file

if __name__ == "__main__":
    create_multi_model_test_file()
