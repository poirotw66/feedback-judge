#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create test data in user's format for testing smart column detection
建立使用者格式的測試資料
"""

import pandas as pd

def create_user_format_test_data():
    """建立使用者格式的測試資料"""
    
    # 根據使用者提供的資料格式 - 使用不同的欄位名稱避免重複
    data = [
        [1, 'ZA24761194', '輕度', '其他類', '【換16.1】', '', '輕度', '身心障礙證明', '障礙類別：其他類', '【換16.1】'],
        [2, 'MT00953431', '中度', '第1類【12.2】', '【換12.2】', '', '中度', '身心障礙證明', '第1類【12.2】', '【第12.2】'],
        [3, 'AB12345678', '重度', '第2類【13.1】', '【換13.1】', '', '重度', '身心障礙證明', '第2類【13.1】', '【換13.1】'],
        [4, 'CD98765432', '輕度', '其他類', '【換16.2】', '', '輕度', '身心障礙證明', '其他類', '【換16.2】'],
        [5, 'EF11223344', '中度', '第1類【12.3】', '【換12.3】', '', '中度', '身心障礙證明', '第1類【12.3】', '【換12.3】']
    ]

    # 定義欄位名稱（按照使用者的格式）
    columns = ['編號', '受編', '障礙等級', '障礙類別', 'ICD診斷', '備註', '障礙等級', '證明/手冊', '障礙類別', 'ICD診斷']
    
    df = pd.DataFrame(data, columns=columns)
    
    # 儲存為Excel檔案
    filename = 'user_format_test_data.xlsx'
    df.to_excel(filename, index=False)
    print(f"使用者格式測試檔案已建立: {filename}")
    print(f"欄位: {list(df.columns)}")
    print("\n資料預覽:")
    print(df.head())
    
    return filename

if __name__ == "__main__":
    create_user_format_test_data()
