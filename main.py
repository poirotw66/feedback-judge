#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
身心障礙手冊資料處理和評估主程式
Main program for processing and evaluating disability certificate data
"""

import pandas as pd
import numpy as np
from accuracy_evaluator import DisabilityDataEvaluator
import os

def load_excel_data(file_path: str) -> pd.DataFrame:
    """載入Excel資料並進行預處理"""
    try:
        # 嘗試讀取Excel檔案
        df = pd.read_excel(file_path)
        print(f"成功載入檔案: {file_path}")
        print(f"資料形狀: {df.shape}")
        print(f"欄位名稱: {list(df.columns)}")
        return df
    except Exception as e:
        print(f"載入檔案時發生錯誤: {e}")
        return None

def preprocess_gemma_data(df: pd.DataFrame) -> pd.DataFrame:
    """預處理gemma模型的輸出資料"""
    # 假設資料格式包含正面和反面的欄位
    # 根據您提供的樣本調整欄位名稱
    
    processed_df = df.copy()
    
    # 如果需要重新命名欄位，在這裡處理
    column_mapping = {
        # 根據實際Excel檔案的欄位名稱進行映射
        # 例如: '障礙等級_正面': '正面_障礙等級'
    }
    
    if column_mapping:
        processed_df = processed_df.rename(columns=column_mapping)
    
    return processed_df

def evaluate_disability_data(file_path: str):
    """評估身心障礙資料的準確度"""
    evaluator = DisabilityDataEvaluator()
    
    # 載入資料
    df = load_excel_data(file_path)
    
    if df is None:
        print("無法載入資料，程式結束")
        return
    
    # 預處理資料
    df = preprocess_gemma_data(df)
    
    # 顯示資料預覽
    print("\n資料預覽:")
    print(df.head())
    
    # 檢查必要的欄位是否存在
    required_fields = ['正面_障礙等級', '反面_障礙等級', '正面_障礙類別', '反面_障礙類別',
                       '正面_ICD診斷', '反面_ICD診斷']
    
    missing_fields = [field for field in required_fields if field not in df.columns]
    
    if missing_fields:
        print(f"\n警告: 缺少以下必要欄位: {missing_fields}")
        print("可用的欄位:")
        for i, col in enumerate(df.columns):
            print(f"  {i + 1}. {col}")
        
        # 提供欄位映射選項
        print("\n請檢查您的Excel檔案欄位名稱，或修改 preprocess_gemma_data 函數中的欄位映射")
        return
    
    # 執行評估
    print("\n開始執行準確度評估...")
    results = evaluator.evaluate_all_fields(df)
    
    # 計算整體準確度
    overall_accuracy = evaluator.calculate_overall_accuracy(results)
    
    # 生成並顯示報告
    report = evaluator.generate_report(results, overall_accuracy)
    print(report)
    
    # 儲存詳細結果
    output_file = f"accuracy_results_{os.path.splitext(os.path.basename(file_path))[0]}.xlsx"
    evaluator.save_detailed_results(results, output_file)
    print(f"\n詳細結果已儲存至: {output_file}")
    
    return results, overall_accuracy

def demo_with_sample_data():
    """使用範例資料進行示範"""
    print("=" * 60)
    print("使用範例資料進行示範")
    print("=" * 60)
    
    evaluator = DisabilityDataEvaluator()
    
    # 建立更詳細的範例資料
    sample_data = {
        '編號': [1, 2, 3, 4, 5],
        '受編': ['ZA24761194', 'MT00953431', 'AA12345678', 'BB87654321', 'CC11223344'],
        '正面_障礙等級': ['輕度', '中度', '重度', '輕度', '中度'],
        '正面_障礙類別': ['其他類', '第1類【12.2】', '第2類【11.1】', '其他類', '第1類【13.1】'],
        '正面_ICD診斷': ['【換16.1】', '【換12.2】', '【換11.1】', '【換16.2】', '【換13.1】'],
        '正面_備註': ['', '', '需定期複檢', '', ''],
        '反面_障礙等級': ['輕度', '中度', '重度', '輕度', '中度'],
        '反面_證明手冊': ['身心障礙證明', '身心障礙證明', '身心障礙手冊', '身心障礙證明', '身心障礙證明'],
        '反面_障礙類別': ['障礙類別：其他類', '第1類【12.2】', '第2類【11.1】', '障礙類別：其他類', '第1類【13.1】'],
        '反面_ICD診斷': ['【換16.1】', '【第12.2】', '【換11.1】', '【換16.2】', '【換13.1】']
    }
    
    df = pd.DataFrame(sample_data)
    
    print(f"範例資料包含 {len(df)} 筆記錄")
    print("\n資料預覽:")
    print(df.to_string(index=False))
    
    # 執行評估
    results = evaluator.evaluate_all_fields(df)
    overall_accuracy = evaluator.calculate_overall_accuracy(results)
    
    # 生成報告
    report = evaluator.generate_report(results, overall_accuracy)
    print("\n" + report)
    
    # 儲存結果
    evaluator.save_detailed_results(results, "sample_accuracy_results.xlsx")
    print("範例結果已儲存至: sample_accuracy_results.xlsx")

def main():
    """主程式入口"""
    print("身心障礙手冊AI測試結果準確度評分系統")
    print("=" * 50)
    
    # 首先執行範例示範
    demo_with_sample_data()
    
    print("\n" + "=" * 50)
    
    # 檢查工作目錄中的Excel檔案
    excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx')]
    
    if excel_files:
        print("\n發現以下Excel檔案:")
        for i, file in enumerate(excel_files):
            print(f"  {i + 1}. {file}")

        print("\n要評估實際資料，請確保Excel檔案包含以下欄位:")
        print("  - 正面_障礙等級, 反面_障礙等級")
        print("  - 正面_障礙類別, 反面_障礙類別")
        print("  - 正面_ICD診斷, 反面_ICD診斷")
        
        # 可以取消註解以下代碼來評估實際檔案
        # for file in excel_files:
        #     if '身心障礙手冊' in file:
        #         print(f"\n正在評估檔案: {file}")
        #         evaluate_disability_data(file)
    else:
        print("\n未發現Excel檔案，僅顯示範例結果")

if __name__ == "__main__":
    main()
