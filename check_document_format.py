#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
檢查外來函文測試檔案格式
"""

import pandas as pd
import sys

def check_document_file():
    try:
        # 讀取檔案
        df = pd.read_excel('/Users/cfh00896102/Github/feedback-judge/data/[TEST]外來函文_AI測試結果資料.xlsx', header=None)
        print('檔案形狀:', df.shape)
        print()
        
        print('前5行資料:')
        for i in range(min(5, len(df))):
            row_data = []
            for j in range(min(10, len(df.columns))):
                cell = df.iloc[i, j]
                if pd.notna(cell):
                    cell_str = str(cell)
                    if len(cell_str) > 20:
                        cell_str = cell_str[:20] + '...'
                    row_data.append(cell_str)
                else:
                    row_data.append('NaN')
            print(f'第{i+1}行: {row_data}')
        
        print()
        print('第一行 (模型名稱行):')
        first_row = df.iloc[0]
        for i, val in enumerate(first_row[:10]):
            print(f'  欄位{i}: {val}')
        
        print()
        print('第一欄 (欄位名稱欄):')
        for i in range(min(15, len(df))):
            val = df.iloc[i, 0]
            if pd.notna(val):
                print(f'  第{i+1}行: {val}')
                
    except Exception as e:
        print(f'錯誤: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_document_file()
