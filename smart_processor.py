#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
專用於身心障礙手冊Excel資料的智能處理器
Smart processor for disability certificate Excel data with complex structure
"""

import pandas as pd
import numpy as np
from accuracy_evaluator import DisabilityDataEvaluator
import os


def smart_read_excel(file_path: str, max_header_rows=5):
    """智能讀取Excel檔案，自動偵測標題行"""
    print(f"正在智能分析Excel檔案: {file_path}")
    
    # 先讀取前幾行來分析結構
    for header_row in range(max_header_rows):
        try:
            df = pd.read_excel(file_path, header=header_row)
            
            # 檢查這一行是否包含有意義的欄位名稱
            meaningful_columns = 0
            for col in df.columns:
                if isinstance(col, str) and not col.startswith('Unnamed'):
                    if any(keyword in col for keyword in ['編號', '受編', '障礙', '類別', 'ICD', '備註', '證明', '手冊']):
                        meaningful_columns += 1
            
            print(f"  第 {header_row} 行作為標題: 有意義欄位數 = {meaningful_columns}")
            
            if meaningful_columns >= 3:  # 至少要有3個有意義的欄位
                print(f"  選擇第 {header_row} 行作為標題行")
                return df, header_row
                
        except Exception as e:
            print(f"  第 {header_row} 行讀取失敗: {e}")
            continue
    
    # 如果都沒找到好的標題行，使用預設的第0行
    df = pd.read_excel(file_path, header=0)
    return df, 0


def extract_disability_data(file_path: str):
    """提取身心障礙資料並進行準確度評估"""
    
    print("=" * 80)
    print(f"智能處理檔案: {os.path.basename(file_path)}")
    print("=" * 80)
    
    # 智能讀取Excel檔案
    df, header_row = smart_read_excel(file_path)
    
    if df is None:
        print("無法讀取檔案")
        return
    
    print(f"成功讀取檔案，資料形狀: {df.shape}")
    print(f"使用第 {header_row} 行作為標題")
    
    # 顯示欄位結構
    print(f"\n欄位結構分析:")
    for i, col in enumerate(df.columns):
        sample_data = df[col].dropna().head(3).tolist()
        print(f"  {i+1:2d}. {col:<20} 範例: {sample_data}")
    
    # 嘗試識別正面和反面的資料區域
    # 根據您的資料描述，應該有"正面"和"反面"的區分
    
    # 尋找包含關鍵字的欄位
    key_columns = {}
    
    for i, col in enumerate(df.columns):
        col_str = str(col).lower()
        
        # 障礙等級
        if '障礙等級' in col_str or '等級' in col_str:
            if i < len(df.columns) // 2:
                key_columns['正面_障礙等級'] = col
            else:
                key_columns['反面_障礙等級'] = col
        
        # 障礙類別
        elif '障礙類別' in col_str or ('類別' in col_str and '障礙' not in col_str):
            if i < len(df.columns) // 2:
                key_columns['正面_障礙類別'] = col
            else:
                key_columns['反面_障礙類別'] = col
        
        # ICD診斷
        elif 'icd' in col_str or '診斷' in col_str:
            if i < len(df.columns) // 2:
                key_columns['正面_ICD診斷'] = col
            else:
                key_columns['反面_ICD診斷'] = col
        
        # 證明/手冊
        elif '證明' in col_str or '手冊' in col_str:
            if i < len(df.columns) // 2:
                key_columns['正面_證明手冊'] = col
            else:
                key_columns['反面_證明手冊'] = col
    
    print(f"\n識別的關鍵欄位:")
    for key, col in key_columns.items():
        print(f"  {key}: {col}")
    
    # 如果自動識別失敗，嘗試基於位置的識別
    if len(key_columns) < 4:
        print(f"\n自動識別不足，嘗試基於位置的識別...")
        
        # 假設資料結構是: 編號, 受編, 正面資料..., 反面資料...
        cols = list(df.columns)
        mid_point = len(cols) // 2
        
        # 尋找可能的資料欄位
        for i, col in enumerate(cols):
            col_str = str(col)
            if '障礙' in col_str and '等級' in col_str:
                if i < mid_point:
                    key_columns['正面_障礙等級'] = col
                else:
                    key_columns['反面_障礙等級'] = col
            elif '障礙' in col_str and '類別' in col_str:
                if i < mid_point:
                    key_columns['正面_障礙類別'] = col
                else:
                    key_columns['反面_障礙類別'] = col
            elif 'ICD' in col_str or '診斷' in col_str:
                if i < mid_point:
                    key_columns['正面_ICD診斷'] = col
                else:
                    key_columns['反面_ICD診斷'] = col
    
    # 手動指定欄位（基於您提供的資料結構）
    if len(key_columns) < 4:
        print(f"\n嘗試手動指定欄位映射...")
        
        cols = list(df.columns)
        if len(cols) >= 10:
            # 根據您的資料樣態進行映射
            potential_mapping = {
                '正面_障礙等級': cols[2] if len(cols) > 2 else None,
                '正面_障礙類別': cols[3] if len(cols) > 3 else None,
                '正面_ICD診斷': cols[4] if len(cols) > 4 else None,
                '反面_障礙等級': cols[6] if len(cols) > 6 else None,
                '反面_障礙類別': cols[8] if len(cols) > 8 else None,
                '反面_ICD診斷': cols[9] if len(cols) > 9 else None,
            }
            
            for key, col in potential_mapping.items():
                if col and col not in key_columns.values():
                    key_columns[key] = col
    
    print(f"\n最終映射的欄位:")
    for key, col in key_columns.items():
        print(f"  {key}: {col}")
    
    # 檢查是否有足夠的配對欄位
    evaluation_pairs = []
    
    if '正面_障礙等級' in key_columns and '反面_障礙等級' in key_columns:
        evaluation_pairs.append(('正面_障礙等級', '反面_障礙等級'))
    
    if '正面_障礙類別' in key_columns and '反面_障礙類別' in key_columns:
        evaluation_pairs.append(('正面_障礙類別', '反面_障礙類別'))
    
    if '正面_ICD診斷' in key_columns and '反面_ICD診斷' in key_columns:
        evaluation_pairs.append(('正面_ICD診斷', '反面_ICD診斷'))
    
    if not evaluation_pairs:
        print(f"\n❌ 無法找到配對的評估欄位")
        print(f"請手動檢查資料結構並調整程式")
        return
    
    print(f"\n✅ 找到 {len(evaluation_pairs)} 個評估配對:")
    for i, (正面, 反面) in enumerate(evaluation_pairs):
        print(f"  {i+1}. {正面} vs {反面}")
    
    # 執行準確度評估
    print(f"\n開始執行準確度評估...")
    
    evaluator = DisabilityDataEvaluator()
    results = {}
    
    for 正面_key, 反面_key in evaluation_pairs:
        正面_col = key_columns[正面_key]
        反面_col = key_columns[反面_key]
        
        # 取得資料（跳過標題行）
        正面_data = df[正面_col].dropna().tolist()
        反面_data = df[反面_col].dropna().tolist()
        
        # 確保資料長度一致
        min_len = min(len(正面_data), len(反面_data))
        正面_data = 正面_data[:min_len]
        反面_data = 反面_data[:min_len]
        
        print(f"  評估 {正面_key.replace('正面_', '')}: {len(正面_data)} 筆資料")
        
        # 顯示前幾筆資料範例
        for i in range(min(3, len(正面_data))):
            print(f"    {i+1}. 正面: '{正面_data[i]}' vs 反面: '{反面_data[i]}'")
        
        try:
            field_name = 正面_key.replace('正面_', '')
            result = evaluator.evaluate_field(正面_data, 反面_data, field_name)
            results[field_name] = result
            print(f"    ✅ 完成評估，準確度: {result.accuracy:.2%}")
        except Exception as e:
            print(f"    ❌ 評估失敗: {e}")
    
    if results:
        # 計算整體準確度
        overall_accuracy = evaluator.calculate_overall_accuracy(results)
        
        # 生成報告
        print(f"\n" + "="*60)
        print(f"評估結果摘要")
        print(f"="*60)
        print(f"整體準確度: {overall_accuracy:.2%}")
        print(f"")
        
        for field_name, result in results.items():
            print(f"【{field_name}】")
            print(f"  準確度: {result.accuracy:.2%}")
            print(f"  完全匹配: {result.exact_matches}/{result.total_records}")
            print(f"  匹配率: {result.exact_matches/result.total_records:.1%}")
            
            if result.mismatched_pairs:
                print(f"  不匹配項目: {len(result.mismatched_pairs)}")
                for i, (correct, predicted) in enumerate(result.mismatched_pairs[:2]):
                    sim = evaluator.calculate_similarity(correct, predicted)
                    print(f"    {i+1}. '{correct}' -> '{predicted}' (相似度: {sim:.1%})")
            print()
        
        # 儲存詳細結果
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_file = f"智能評估結果_{base_name}.xlsx"
        evaluator.save_detailed_results(results, output_file)
        print(f"詳細結果已儲存至: {output_file}")
        
        return results, overall_accuracy
    
    else:
        print(f"❌ 未能完成任何欄位的評估")
        return None


def main():
    """主程式"""
    target_file = "身心障礙手冊_AI測試結果資料 (1).xlsx"
    
    if os.path.exists(target_file):
        extract_disability_data(target_file)
    else:
        print(f"找不到檔案: {target_file}")
        
        # 列出所有Excel檔案
        excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx') and not f.startswith('~')]
        if excel_files:
            print(f"可用的Excel檔案:")
            for i, file in enumerate(excel_files):
                print(f"  {i+1}. {file}")


if __name__ == "__main__":
    main()
