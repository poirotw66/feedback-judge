#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成詳細記錄分析的Excel檔案
Generate detailed record analysis Excel file
"""

from accuracy_evaluator import DisabilityDataEvaluator
from smart_processor import smart_read_excel
import os


def generate_detailed_excel():
    """生成包含詳細記錄分析的Excel檔案"""
    
    target_file = "身心障礙手冊_AI測試結果資料 (1).xlsx"
    
    if not os.path.exists(target_file):
        print(f"找不到檔案: {target_file}")
        return
    
    print("生成詳細記錄分析Excel檔案...")
    print("=" * 60)
    
    # 讀取資料
    df, header_row = smart_read_excel(target_file)
    
    if df is None:
        print("無法讀取檔案")
        return
    
    print(f"成功讀取 {len(df)} 筆記錄")
    
    # 識別欄位映射
    field_mappings = {
        '障礙等級': ('障礙等級', '障礙等級.1'),
        '障礙類別': ('障礙類別', '障礙類別.1'), 
        'ICD診斷': ('ICD診斷', 'ICD診斷.1')
    }
    
    # 建立評估器
    evaluator = DisabilityDataEvaluator()
    
    # 執行按記錄評估
    record_evaluations = evaluator.evaluate_all_records(df, field_mappings)
    
    if record_evaluations:
        # 儲存詳細結果到Excel
        output_file = "詳細記錄分析報告.xlsx"
        evaluator.save_record_results(record_evaluations, output_file)
        print(f"✅ 詳細結果已儲存至: {output_file}")
        
        # 顯示部分結果預覽
        print(f"\n📋 結果預覽:")
        print(f"共生成 {len(record_evaluations)} 筆記錄的詳細分析")
        
        # 顯示前2筆記錄的格式
        for i, evaluation in enumerate(record_evaluations[:2], 1):
            print(f"\n【記錄 {evaluation.record_id}】受編: {evaluation.subject_id}")
            print(f"  整體準確度: {evaluation.overall_accuracy:.2%} ({evaluation.matched_fields}/{evaluation.total_fields} 完全匹配)")
            
            for field_name, field_result in evaluation.field_results.items():
                status = "✅" if field_result.is_exact_match else "❌" if field_result.similarity < 0.5 else "⚠️"
                print(f"    {status} {field_name}: {field_result.similarity:.1%}")
                
                if not field_result.is_exact_match:
                    print(f"      正確: '{field_result.correct_value}'")
                    print(f"      預測: '{field_result.predicted_value}'")
        
        print(f"\n💾 Excel檔案包含以下工作表:")
        print(f"  1. 記錄摘要 - 每筆記錄的整體準確度")
        print(f"  2. 詳細欄位比較 - 每個欄位的詳細比較")
        print(f"  3. 記錄詳情 - 格式化的記錄詳情（如您要求的格式）")
        print(f"  4. 欄位統計 - 各欄位的統計資訊")
        print(f"  5. 錯誤分析 - 需要改進的項目分析")
        
        # 統計資訊
        total_records = len(record_evaluations)
        perfect_records = sum(1 for eval_result in record_evaluations 
                             if eval_result.matched_fields == eval_result.total_fields)
        
        print(f"\n📊 統計摘要:")
        print(f"  總記錄數: {total_records}")
        print(f"  完全正確記錄: {perfect_records}")
        print(f"  完全正確率: {perfect_records/total_records:.1%}")
        
    else:
        print("❌ 無法完成評估")


if __name__ == "__main__":
    generate_detailed_excel()
