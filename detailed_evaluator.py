#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
按編號詳細比較準確度的增強評估器
Enhanced evaluator for detailed accuracy comparison by record ID
"""

import pandas as pd
import numpy as np
from accuracy_evaluator import DisabilityDataEvaluator
from smart_processor import smart_read_excel
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class RecordComparison:
    """單筆記錄的比較結果"""
    record_id: str
    subject_id: str  # 受編
    field_comparisons: Dict[str, Dict]
    overall_accuracy: float
    total_fields: int
    matched_fields: int


class DetailedEvaluator:
    """詳細評估器 - 按編號比較每個欄位"""
    
    def __init__(self):
        self.base_evaluator = DisabilityDataEvaluator()
        
    def compare_single_record(self, record_data: Dict[str, Tuple[str, str]], record_id: str, subject_id: str) -> RecordComparison:
        """比較單筆記錄的所有欄位"""
        field_comparisons = {}
        total_score = 0.0
        matched_count = 0
        total_fields = 0
        
        for field_name, (correct_value, predicted_value) in record_data.items():
            # 計算相似度
            similarity = self.base_evaluator.calculate_similarity(correct_value, predicted_value)
            is_exact_match = similarity >= 0.99
            
            if is_exact_match:
                matched_count += 1
            
            field_comparisons[field_name] = {
                '正確值': str(correct_value) if correct_value is not None else '',
                '預測值': str(predicted_value) if predicted_value is not None else '',
                '相似度': similarity,
                '完全匹配': is_exact_match,
                '狀態': '✅' if is_exact_match else '❌' if similarity < 0.5 else '⚠️'
            }
            
            total_score += similarity
            total_fields += 1
        
        overall_accuracy = total_score / total_fields if total_fields > 0 else 0.0
        
        return RecordComparison(
            record_id=record_id,
            subject_id=subject_id,
            field_comparisons=field_comparisons,
            overall_accuracy=overall_accuracy,
            total_fields=total_fields,
            matched_fields=matched_count
        )
    
    def evaluate_all_records(self, file_path: str) -> List[RecordComparison]:
        """評估所有記錄"""
        print(f"正在進行按編號的詳細準確度分析...")
        
        # 讀取資料
        df, header_row = smart_read_excel(file_path)
        
        if df is None:
            print("無法讀取檔案")
            return []
        
        print(f"成功讀取 {len(df)} 筆記錄")
        
        # 識別欄位
        key_columns = self._identify_columns(df)
        
        if not key_columns:
            print("無法識別必要的欄位")
            return []
        
        print(f"識別到的欄位配對:")
        for field_name, (正面_col, 反面_col) in key_columns.items():
            print(f"  {field_name}: {正面_col} vs {反面_col}")
        
        # 逐筆記錄進行比較
        record_comparisons = []
        
        for index, row in df.iterrows():
            # 取得編號和受編
            record_id = str(row.get('編號', index + 1))
            subject_id = str(row.get('受編', f'記錄{index + 1}'))
            
            # 準備本筆記錄的欄位資料
            record_data = {}
            
            for field_name, (正面_col, 反面_col) in key_columns.items():
                correct_value = row.get(正面_col)
                predicted_value = row.get(反面_col)
                record_data[field_name] = (correct_value, predicted_value)
            
            # 比較本筆記錄
            comparison = self.compare_single_record(record_data, record_id, subject_id)
            record_comparisons.append(comparison)
        
        return record_comparisons
    
    def _identify_columns(self, df: pd.DataFrame) -> Dict[str, Tuple[str, str]]:
        """識別欄位配對"""
        key_columns = {}
        cols = list(df.columns)
        
        # 障礙等級
        for i, col in enumerate(cols):
            if '障礙等級' in str(col) and not str(col).endswith('.1'):
                # 尋找對應的反面欄位
                for j, other_col in enumerate(cols[i+1:], i+1):
                    if '障礙等級' in str(other_col) and j != i:
                        key_columns['障礙等級'] = (col, other_col)
                        break
                break
        
        # 障礙類別
        for i, col in enumerate(cols):
            if '障礙類別' in str(col) and not str(col).endswith('.1') and not str(col).endswith('.2'):
                # 尋找對應的反面欄位
                for j, other_col in enumerate(cols[i+1:], i+1):
                    if '障礙類別' in str(other_col) and j != i and (str(other_col).endswith('.1') or str(other_col).endswith('.2')):
                        key_columns['障礙類別'] = (col, other_col)
                        break
                break
        
        # ICD診斷
        for i, col in enumerate(cols):
            if 'ICD' in str(col) and not str(col).endswith('.1') and not str(col).endswith('.2'):
                # 尋找對應的反面欄位
                for j, other_col in enumerate(cols[i+1:], i+1):
                    if 'ICD' in str(other_col) and j != i and (str(other_col).endswith('.1') or str(other_col).endswith('.2')):
                        key_columns['ICD診斷'] = (col, other_col)
                        break
                break
        
        return key_columns
    
    def generate_detailed_report(self, record_comparisons: List[RecordComparison]) -> str:
        """生成詳細報告"""
        if not record_comparisons:
            return "無比較結果"
        
        report = []
        report.append("=" * 100)
        report.append("按編號詳細準確度分析報告")
        report.append("=" * 100)
        
        # 整體統計
        total_records = len(record_comparisons)
        avg_accuracy = np.mean([comp.overall_accuracy for comp in record_comparisons])
        total_perfect_records = sum(1 for comp in record_comparisons if comp.matched_fields == comp.total_fields)
        
        report.append(f"📊 整體統計:")
        report.append(f"  總記錄數: {total_records}")
        report.append(f"  平均準確度: {avg_accuracy:.2%}")
        report.append(f"  完全正確記錄: {total_perfect_records}/{total_records} ({total_perfect_records/total_records:.1%})")
        report.append("")
        
        # 各欄位統計
        if record_comparisons:
            field_names = list(record_comparisons[0].field_comparisons.keys())
            report.append(f"📈 各欄位統計:")
            
            for field_name in field_names:
                field_accuracies = []
                field_matches = 0
                
                for comp in record_comparisons:
                    if field_name in comp.field_comparisons:
                        field_accuracies.append(comp.field_comparisons[field_name]['相似度'])
                        if comp.field_comparisons[field_name]['完全匹配']:
                            field_matches += 1
                
                avg_field_accuracy = np.mean(field_accuracies) if field_accuracies else 0
                match_rate = field_matches / len(field_accuracies) if field_accuracies else 0
                
                report.append(f"  {field_name}: {avg_field_accuracy:.2%} (完全匹配: {field_matches}/{len(field_accuracies)}, {match_rate:.1%})")
            
            report.append("")
        
        # 詳細記錄分析
        report.append(f"📋 詳細記錄分析:")
        report.append("-" * 100)
        
        for i, comp in enumerate(record_comparisons, 1):
            report.append(f"【記錄 {comp.record_id}】受編: {comp.subject_id}")
            report.append(f"  整體準確度: {comp.overall_accuracy:.2%} ({comp.matched_fields}/{comp.total_fields} 完全匹配)")
            
            for field_name, field_data in comp.field_comparisons.items():
                status = field_data['狀態']
                similarity = field_data['相似度']
                correct = field_data['正確值']
                predicted = field_data['預測值']
                
                report.append(f"    {status} {field_name}: {similarity:.1%}")
                if similarity < 0.99:
                    report.append(f"      正確: '{correct}'")
                    report.append(f"      預測: '{predicted}'")
            
            report.append("")
            
            # 每10筆記錄顯示一次分隔線
            if i % 10 == 0 and i < len(record_comparisons):
                report.append("-" * 50)
        
        return "\n".join(report)
    
    def save_detailed_excel(self, record_comparisons: List[RecordComparison], output_path: str):
        """儲存詳細Excel結果"""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 整體摘要頁
            summary_data = []
            for comp in record_comparisons:
                summary_data.append({
                    '編號': comp.record_id,
                    '受編': comp.subject_id,
                    '整體準確度': f"{comp.overall_accuracy:.2%}",
                    '完全匹配欄位數': comp.matched_fields,
                    '總欄位數': comp.total_fields,
                    '匹配率': f"{comp.matched_fields/comp.total_fields:.1%}" if comp.total_fields > 0 else "0%"
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='整體摘要', index=False)
            
            # 詳細比較頁
            detailed_data = []
            for comp in record_comparisons:
                for field_name, field_data in comp.field_comparisons.items():
                    detailed_data.append({
                        '編號': comp.record_id,
                        '受編': comp.subject_id,
                        '欄位': field_name,
                        '正確值': field_data['正確值'],
                        '預測值': field_data['預測值'],
                        '相似度': f"{field_data['相似度']:.2%}",
                        '完全匹配': '是' if field_data['完全匹配'] else '否',
                        '狀態': field_data['狀態']
                    })
            
            detailed_df = pd.DataFrame(detailed_data)
            detailed_df.to_excel(writer, sheet_name='詳細比較', index=False)
            
            # 各欄位統計頁
            if record_comparisons:
                field_names = list(record_comparisons[0].field_comparisons.keys())
                field_stats_data = []
                
                for field_name in field_names:
                    accuracies = []
                    matches = 0
                    total = 0
                    
                    for comp in record_comparisons:
                        if field_name in comp.field_comparisons:
                            accuracies.append(comp.field_comparisons[field_name]['相似度'])
                            if comp.field_comparisons[field_name]['完全匹配']:
                                matches += 1
                            total += 1
                    
                    avg_accuracy = np.mean(accuracies) if accuracies else 0
                    match_rate = matches / total if total > 0 else 0
                    
                    field_stats_data.append({
                        '欄位名稱': field_name,
                        '平均準確度': f"{avg_accuracy:.2%}",
                        '完全匹配數': matches,
                        '總記錄數': total,
                        '匹配率': f"{match_rate:.1%}"
                    })
                
                field_stats_df = pd.DataFrame(field_stats_data)
                field_stats_df.to_excel(writer, sheet_name='欄位統計', index=False)


def main():
    """主程式"""
    evaluator = DetailedEvaluator()
    target_file = "身心障礙手冊_AI測試結果資料 (1).xlsx"
    
    if not os.path.exists(target_file):
        print(f"找不到檔案: {target_file}")
        return
    
    # 執行詳細評估
    record_comparisons = evaluator.evaluate_all_records(target_file)
    
    if record_comparisons:
        # 生成報告
        report = evaluator.generate_detailed_report(record_comparisons)
        print(report)
        
        # 儲存詳細結果
        output_file = "按編號詳細準確度分析.xlsx"
        evaluator.save_detailed_excel(record_comparisons, output_file)
        print(f"\n詳細分析結果已儲存至: {output_file}")
    else:
        print("無法完成評估")


if __name__ == "__main__":
    main()
