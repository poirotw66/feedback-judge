#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
進一步分析外來函文資料格式
"""

import pandas as pd

def analyze_document_structure():
    df = pd.read_excel('/Users/cfh00896102/Github/feedback-judge/data/[TEST]外來函文_AI測試結果資料.xlsx', header=None)
    
    print("=== 資料結構分析 ===")
    print(f"檔案形狀: {df.shape}")
    print()
    
    print("第1行 (模型名稱行):")
    row1 = df.iloc[0]
    for i in range(min(15, len(row1))):
        if pd.notna(row1.iloc[i]):
            print(f"  欄位{i}: {row1.iloc[i]}")
    
    print("\n第2行 (欄位名稱行):")
    row2 = df.iloc[1]
    for i in range(min(15, len(row2))):
        if pd.notna(row2.iloc[i]):
            print(f"  欄位{i}: {row2.iloc[i]}")
    
    print("\n第3行 (第一筆資料):")
    row3 = df.iloc[2]
    for i in range(min(15, len(row3))):
        if pd.notna(row3.iloc[i]):
            print(f"  欄位{i}: {row3.iloc[i]}")
    
    print("\n分析模型對應關係:")
    print("從資料看起來，格式是:")
    print("- 第1行: 模型名稱")
    print("- 第2行: 欄位名稱")
    print("- 第3行開始: 實際資料")
    print("- 每個模型佔2欄：AI結果 + 人工結果")
    
    # 嘗試識別模型和欄位的對應關係
    print("\n模型-欄位對應分析:")
    model_row = df.iloc[0]
    field_row = df.iloc[1]
    
    current_model = None
    for i in range(len(model_row)):
        model_name = model_row.iloc[i]
        field_name = field_row.iloc[i]
        
        if pd.notna(model_name):
            current_model = str(model_name).strip()
            print(f"\n模型 '{current_model}' 開始於欄位 {i}")
        
        if pd.notna(field_name):
            field_str = str(field_name).strip()
            print(f"  欄位{i}: {field_str} (模型: {current_model})")

if __name__ == "__main__":
    analyze_document_structure()
