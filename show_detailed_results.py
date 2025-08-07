#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Display detailed results from the generated Excel file
顯示生成Excel檔案的詳細結果
"""

import pandas as pd
import os

def show_field_summary(filename: str = "gemma3_result.xlsx"):
    """顯示欄位準確度摘要"""
    
    try:
        df = pd.read_excel(filename, sheet_name='欄位準確度摘要')
        
        print("=" * 60)
        print("欄位準確度摘要 (Field-by-Field Summary)")
        print("=" * 60)
        
        for _, row in df.iterrows():
            field_name = row['欄位名稱']
            accuracy = row['整體準確度']
            exact_matches = row['完全匹配數']
            total_records = row['總記錄數']
            match_rate = row['完全匹配率']
            performance = row['表現等級']
            suggestion = row['改進建議']
            
            print(f"📊 {field_name}:")
            print(f"   整體準確度: {accuracy}")
            print(f"   完全匹配: {exact_matches}/{total_records} ({match_rate})")
            print(f"   表現等級: {performance}")
            print(f"   改進建議: {suggestion}")
            print()
            
    except Exception as e:
        print(f"❌ 讀取欄位摘要失敗: {e}")

def show_individual_records(filename: str = "gemma3_result.xlsx", num_records: int = 3):
    """顯示個別記錄分析"""
    
    try:
        df = pd.read_excel(filename, sheet_name='個別記錄分析')
        
        print("=" * 60)
        print("個別記錄分析 (Individual Record Analysis)")
        print("=" * 60)
        
        current_subject = None
        record_count = 0
        
        for _, row in df.iterrows():
            if record_count >= num_records:
                break
            
            # 檢查是否是新的受編記錄
            if pd.notna(row['受編']) and row['受編'] != '' and row['欄位'] == '=== 記錄開始 ===':
                current_subject = row['受編']
                record_count += 1
                print(f"\n受編: {current_subject}")
                print(f"  {row['狀態']} ({row['備註']})")
                continue
            
            # 顯示欄位詳細資訊
            if pd.notna(row['欄位']) and row['欄位'] not in ['=== 記錄開始 ===', '--- 分隔線 ---']:
                field_name = row['欄位']
                correct = row['正解']
                predicted = row['模型識別結果']
                accuracy = row['準確度']
                status = row['狀態']
                
                print(f"  {field_name}: 正解=\"{correct}\", 模型識別=\"{predicted}\", 準確度={accuracy}")
                print(f"    狀態: {status}")
        
    except Exception as e:
        print(f"❌ 讀取個別記錄失敗: {e}")

def show_overall_summary(filename: str = "gemma3_result.xlsx"):
    """顯示整體摘要"""
    
    try:
        df = pd.read_excel(filename, sheet_name='評估摘要')
        
        print("=" * 60)
        print("整體評估摘要 (Overall Summary)")
        print("=" * 60)
        
        for _, row in df.iterrows():
            if pd.notna(row['項目']) and row['項目'] != '':
                item = row['項目']
                value = row['數值']
                description = row['說明']
                print(f"{item}: {value} ({description})")
        
        print()
        
    except Exception as e:
        print(f"❌ 讀取整體摘要失敗: {e}")

def analyze_performance_issues(filename: str = "gemma3_result.xlsx"):
    """分析表現問題"""
    
    try:
        # 讀取錯誤分析
        df_errors = pd.read_excel(filename, sheet_name='錯誤分析')
        
        print("=" * 60)
        print("表現問題分析 (Performance Issues Analysis)")
        print("=" * 60)
        
        # 統計錯誤類型
        error_types = df_errors['錯誤類型'].value_counts()
        print("📊 錯誤類型分佈:")
        for error_type, count in error_types.items():
            print(f"   {error_type}: {count} 次")
        
        print()
        
        # 顯示高優先級錯誤
        high_priority_errors = df_errors[df_errors['優先級'] == '高']
        if len(high_priority_errors) > 0:
            print("🚨 高優先級錯誤 (需要立即改進):")
            for _, row in high_priority_errors.head(5).iterrows():
                subject = row['受編']
                field = row['欄位']
                correct = row['正確值']
                predicted = row['預測值']
                suggestion = row['改進建議']
                
                print(f"   受編 {subject} - {field}:")
                print(f"     正確: \"{correct}\" → 預測: \"{predicted}\"")
                print(f"     建議: {suggestion}")
                print()
        
    except Exception as e:
        print(f"❌ 分析表現問題失敗: {e}")

def main():
    """主程式"""
    filename = "gemma3_result.xlsx"
    
    if not os.path.exists(filename):
        print(f"❌ 檔案不存在: {filename}")
        print("請先執行: python test_gemma3_file.py")
        return
    
    print("🔍 分析Gemma3模型的準確度評估結果")
    print(f"📁 檔案: {filename}")
    
    # 顯示整體摘要
    show_overall_summary(filename)
    
    # 顯示欄位準確度摘要
    show_field_summary(filename)
    
    # 顯示個別記錄分析範例
    show_individual_records(filename, num_records=3)
    
    # 分析表現問題
    analyze_performance_issues(filename)
    
    print("=" * 60)
    print("✅ 詳細結果分析完成！")
    print("💡 建議:")
    print("   1. 檢查高優先級錯誤，優先改進這些問題")
    print("   2. 針對準確度較低的欄位加強訓練")
    print("   3. 分析錯誤模式，調整模型參數")
    print("=" * 60)

if __name__ == "__main__":
    main()
