#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
針對身心障礙手冊Excel資料的專用處理器
Specialized processor for disability certificate Excel data
"""

import pandas as pd
import numpy as np
from accuracy_evaluator import DisabilityDataEvaluator
import os


def analyze_excel_structure(file_path: str):
    """分析Excel檔案結構"""
    try:
        # 讀取Excel檔案
        df = pd.read_excel(file_path)
        
        print(f"檔案: {file_path}")
        print(f"資料形狀: {df.shape}")
        print(f"欄位數量: {len(df.columns)}")
        print("\n所有欄位:")
        for i, col in enumerate(df.columns):
            print(f"  {i + 1:2d}. {col}")
        
        print(f"\n前3筆資料預覽:")
        print(df.head(3).to_string(index=False))
        
        return df
        
    except Exception as e:
        print(f"分析檔案時發生錯誤: {e}")
        return None


def process_disability_excel(file_path: str):
    """處理身心障礙手冊Excel檔案並進行準確度評估"""
    
    print("=" * 70)
    print(f"正在處理檔案: {os.path.basename(file_path)}")
    print("=" * 70)
    
    # 分析檔案結構
    df = analyze_excel_structure(file_path)
    
    if df is None:
        return
    
    # 根據實際資料結構進行欄位映射
    # 這裡需要根據您的實際Excel檔案調整
    
    # 常見的欄位名稱模式
    possible_mappings = {
        # 障礙等級
        '正面_障礙等級': ['障礙等級', '等級', '正面障礙等級', '原始障礙等級'],
        '反面_障礙等級': ['AI障礙等級', '預測障礙等級', '反面障礙等級', 'gemma障礙等級'],
        
        # 障礙類別  
        '正面_障礙類別': ['障礙類別', '類別', '正面障礙類別', '原始障礙類別'],
        '反面_障礙類別': ['AI障礙類別', '預測障礙類別', '反面障礙類別', 'gemma障礙類別'],
        
        # ICD診斷
        '正面_ICD診斷': ['ICD診斷', 'ICD', '正面ICD', '原始ICD'],
        '反面_ICD診斷': ['AI_ICD', '預測ICD', '反面ICD', 'gemma_ICD'],
        
        # 證明/手冊類型
        '正面_證明手冊': ['證明手冊', '手冊類型', '正面證明', '原始證明'],
        '反面_證明手冊': ['AI證明', '預測證明', '反面證明', 'gemma證明']
    }
    
    # 自動檢測欄位映射
    column_mapping = {}
    available_columns = df.columns.tolist()
    
    print(f"\n自動檢測欄位映射:")
    for target_col, possible_names in possible_mappings.items():
        found = False
        for possible_name in possible_names:
            for actual_col in available_columns:
                if possible_name.lower() in actual_col.lower() or actual_col.lower() in possible_name.lower():
                    column_mapping[actual_col] = target_col
                    print(f"  {actual_col} -> {target_col}")
                    found = True
                    break
            if found:
                break
        
        if not found:
            print(f"  警告: 未找到 {target_col} 對應的欄位")
    
    # 應用欄位映射
    if column_mapping:
        df_mapped = df.rename(columns=column_mapping)
        print(f"\n已映射 {len(column_mapping)} 個欄位")
    else:
        df_mapped = df.copy()
        print(f"\n未找到可映射的欄位，使用原始欄位名稱")
    
    # 檢查是否有成對的欄位進行評估
    evaluation_pairs = [
        ('正面_障礙等級', '反面_障礙等級'),
        ('正面_障礙類別', '反面_障礙類別'),
        ('正面_ICD診斷', '反面_ICD診斷'),
        ('正面_證明手冊', '反面_證明手冊')
    ]
    
    valid_pairs = []
    for correct_col, predicted_col in evaluation_pairs:
        if correct_col in df_mapped.columns and predicted_col in df_mapped.columns:
            valid_pairs.append((correct_col, predicted_col))
            print(f"✓ 找到評估對: {correct_col} vs {predicted_col}")
        else:
            print(f"✗ 缺少評估對: {correct_col} vs {predicted_col}")
    
    if not valid_pairs:
        print(f"\n無法找到有效的評估欄位對，請檢查Excel檔案格式")
        print(f"可用欄位: {list(df_mapped.columns)}")
        return
    
    # 執行準確度評估
    print(f"\n開始執行準確度評估 ({len(valid_pairs)} 個欄位對)...")
    
    evaluator = DisabilityDataEvaluator()
    results = {}
    
    for correct_col, predicted_col in valid_pairs:
        field_name = correct_col.replace('正面_', '')
        correct_values = df_mapped[correct_col].tolist()
        predicted_values = df_mapped[predicted_col].tolist()
        
        try:
            result = evaluator.evaluate_field(correct_values, predicted_values, field_name)
            results[field_name] = result
            print(f"✓ 完成評估: {field_name}")
        except Exception as e:
            print(f"✗ 評估失敗: {field_name} - {e}")
    
    if results:
        # 計算整體準確度
        overall_accuracy = evaluator.calculate_overall_accuracy(results)
        
        # 生成報告
        report = evaluator.generate_report(results, overall_accuracy)
        print(f"\n{report}")
        
        # 儲存詳細結果
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_file = f"evaluation_results_{base_name}.xlsx"
        evaluator.save_detailed_results(results, output_file)
        print(f"詳細結果已儲存至: {output_file}")
        
        return results, overall_accuracy
    
    else:
        print(f"未能完成任何欄位的評估")
        return None


def batch_process_excel_files():
    """批次處理所有Excel檔案"""
    excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') and not f.startswith('~')]
    
    if not excel_files:
        print("未找到Excel檔案")
        return
    
    print(f"找到 {len(excel_files)} 個Excel檔案:")
    for i, file in enumerate(excel_files):
        print(f"  {i + 1}. {file}")
    
    all_results = {}
    
    for file in excel_files:
        try:
            result = process_disability_excel(file)
            if result:
                all_results[file] = result
        except Exception as e:
            print(f"處理檔案 {file} 時發生錯誤: {e}")
    
    # 生成總結報告
    if all_results:
        print(f"\n" + "=" * 70)
        print(f"批次處理總結報告")
        print(f"=" * 70)
        
        for file, (results, overall_accuracy) in all_results.items():
            print(f"\n檔案: {file}")
            print(f"整體準確度: {overall_accuracy:.2%}")
            for field_name, result in results.items():
                print(f"  {field_name}: {result.accuracy:.2%}")


if __name__ == "__main__":
    batch_process_excel_files()
