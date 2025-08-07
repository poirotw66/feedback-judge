#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
身心障礙手冊AI測試結果準確度評分系統
Accuracy Evaluation System for Disability Certificate AI Test Results
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any
import re
import difflib
from dataclasses import dataclass
from enum import Enum

class FieldType(Enum):
    """欄位類型枚舉"""
    DISABILITY_LEVEL = "障礙等級"
    DISABILITY_CATEGORY = "障礙類別"
    ICD_DIAGNOSIS = "ICD診斷"
    CERTIFICATE_TYPE = "證明/手冊"

@dataclass
class EvaluationResult:
    """評估結果資料類別"""
    field_name: str
    accuracy: float
    exact_matches: int
    total_records: int
    similarity_scores: List[float]
    mismatched_pairs: List[Tuple[str, str]]

@dataclass
class RecordFieldResult:
    """單筆記錄的欄位評估結果"""
    record_id: str
    subject_id: str
    field_name: str
    correct_value: str
    predicted_value: str
    similarity: float
    is_exact_match: bool

@dataclass
class RecordEvaluation:
    """單筆記錄的完整評估結果"""
    record_id: str
    subject_id: str
    field_results: Dict[str, RecordFieldResult]
    overall_accuracy: float
    total_fields: int
    matched_fields: int

class DisabilityDataEvaluator:
    """身心障礙資料準確度評估器"""
    
    def __init__(self):
        self.similarity_threshold = 0.8
        self.weight_config = {
            FieldType.DISABILITY_LEVEL: 0.3,
            FieldType.DISABILITY_CATEGORY: 0.3,
            FieldType.ICD_DIAGNOSIS: 0.25,
            FieldType.CERTIFICATE_TYPE: 0.15
        }
    
    def normalize_text(self, text: str) -> str:
        """標準化文字處理"""
        if pd.isna(text) or text is None:
            return ""
        
        text = str(text).strip()
        # 移除多餘的空格和特殊字符
        text = re.sub(r'\s+', '', text)
        # 統一括號格式
        text = text.replace('【', '[').replace('】', ']')
        text = text.replace('（', '(').replace('）', ')')
        return text.lower()
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """計算兩個文字的相似度"""
        norm_text1 = self.normalize_text(text1)
        norm_text2 = self.normalize_text(text2)
        
        if not norm_text1 and not norm_text2:
            return 1.0
        if not norm_text1 or not norm_text2:
            return 0.0
        
        # 使用SequenceMatcher計算相似度
        similarity = difflib.SequenceMatcher(None, norm_text1, norm_text2).ratio()
        return similarity
    
    def evaluate_field(self, correct_values: List[str], 
                      predicted_values: List[str], 
                      field_name: str) -> EvaluationResult:
        """評估單一欄位的準確度"""
        if len(correct_values) != len(predicted_values):
            raise ValueError(f"正確值和預測值的數量不一致: {len(correct_values)} vs {len(predicted_values)}")
        
        exact_matches = 0
        similarity_scores = []
        mismatched_pairs = []
        
        for correct, predicted in zip(correct_values, predicted_values):
            similarity = self.calculate_similarity(correct, predicted)
            similarity_scores.append(similarity)
            
            if similarity >= 0.99:  # 近似完全匹配
                exact_matches += 1
            elif similarity < self.similarity_threshold:
                mismatched_pairs.append((str(correct), str(predicted)))
        
        accuracy = np.mean(similarity_scores)
        
        return EvaluationResult(
            field_name=field_name,
            accuracy=accuracy,
            exact_matches=exact_matches,
            total_records=len(correct_values),
            similarity_scores=similarity_scores,
            mismatched_pairs=mismatched_pairs
        )
    
    def load_data_from_excel(self, file_path: str) -> pd.DataFrame:
        """從Excel檔案載入資料"""
        try:
            df = pd.read_excel(file_path)
            return df
        except Exception as e:
            print(f"載入Excel檔案時發生錯誤: {e}")
            return None
    
    def create_sample_data(self) -> pd.DataFrame:
        """建立範例資料（基於您提供的資料格式）"""
        data = {
            '編號': [1, 2],
            '受編': ['ZA24761194', 'MT00953431'],
            '正面_障礙等級': ['輕度', '中度'],
            '正面_障礙類別': ['其他類', '第1類【12.2】'],
            '正面_ICD診斷': ['【換16.1】', '【換12.2】'],
            '正面_備註': ['', ''],
            '反面_障礙等級': ['輕度', '中度'],
            '反面_證明手冊': ['身心障礙證明', '身心障礙證明'],
            '反面_障礙類別': ['障礙類別：其他類', '第1類【12.2】'],
            '反面_ICD診斷': ['【換16.1】', '【第12.2】']
        }
        return pd.DataFrame(data)
    
    def evaluate_all_fields(self, df: pd.DataFrame) -> Dict[str, EvaluationResult]:
        """評估所有欄位的準確度"""
        results = {}
        
        # 定義欄位對應關係（正面 vs 反面）
        field_mappings = {
            '障礙等級': ('正面_障礙等級', '反面_障礙等級'),
            '障礙類別': ('正面_障礙類別', '反面_障礙類別'),
            'ICD診斷': ('正面_ICD診斷', '反面_ICD診斷')
        }
        
        for field_name, (correct_col, predicted_col) in field_mappings.items():
            if correct_col in df.columns and predicted_col in df.columns:
                correct_values = df[correct_col].tolist()
                predicted_values = df[predicted_col].tolist()
                
                result = self.evaluate_field(correct_values, predicted_values, field_name)
                results[field_name] = result
            else:
                print(f"警告: 找不到欄位 {correct_col} 或 {predicted_col}")
        
        return results
    
    def calculate_overall_accuracy(self, results: Dict[str, EvaluationResult]) -> float:
        """計算整體加權準確度"""
        total_weighted_accuracy = 0.0
        total_weight = 0.0
        
        for field_name, result in results.items():
            # 根據欄位類型取得權重
            weight = 0.25  # 預設權重
            for field_type in FieldType:
                if field_type.value in field_name:
                    weight = self.weight_config.get(field_type, 0.25)
                    break
            
            total_weighted_accuracy += result.accuracy * weight
            total_weight += weight
        
        return total_weighted_accuracy / total_weight if total_weight > 0 else 0.0
    
    def evaluate_record_fields(self, record_data: Dict[str, Tuple[str, str]], 
                              record_id: str, subject_id: str = None) -> RecordEvaluation:
        """評估單筆記錄中每個欄位的準確度"""
        field_results = {}
        total_score = 0.0
        matched_count = 0
        
        for field_name, (correct_value, predicted_value) in record_data.items():
            # 計算相似度
            similarity = self.calculate_similarity(correct_value, predicted_value)
            is_exact_match = similarity >= 0.99
            
            if is_exact_match:
                matched_count += 1
            
            # 建立欄位結果
            field_result = RecordFieldResult(
                record_id=record_id,
                subject_id=subject_id or record_id,
                field_name=field_name,
                correct_value=str(correct_value) if correct_value is not None else '',
                predicted_value=str(predicted_value) if predicted_value is not None else '',
                similarity=similarity,
                is_exact_match=is_exact_match
            )
            
            field_results[field_name] = field_result
            total_score += similarity
        
        # 計算整體準確度
        overall_accuracy = total_score / len(record_data) if record_data else 0.0
        
        return RecordEvaluation(
            record_id=record_id,
            subject_id=subject_id or record_id,
            field_results=field_results,
            overall_accuracy=overall_accuracy,
            total_fields=len(record_data),
            matched_fields=matched_count
        )
    
    def evaluate_all_records(self, df: pd.DataFrame, 
                           field_mappings: Dict[str, Tuple[str, str]] = None) -> List[RecordEvaluation]:
        """評估所有記錄中每個欄位的準確度"""
        if field_mappings is None:
            # 預設欄位對應關係
            field_mappings = {
                '障礙等級': ('正面_障礙等級', '反面_障礙等級'),
                '障礙類別': ('正面_障礙類別', '反面_障礙類別'),
                'ICD診斷': ('正面_ICD診斷', '反面_ICD診斷')
            }
        
        record_evaluations = []
        
        for index, row in df.iterrows():
            # 取得編號和受編
            record_id = str(row.get('編號', index + 1))
            subject_id = str(row.get('受編', f'記錄{index + 1}'))
            
            # 準備本筆記錄的欄位資料
            record_data = {}
            
            for field_name, (correct_col, predicted_col) in field_mappings.items():
                if correct_col in df.columns and predicted_col in df.columns:
                    correct_value = row.get(correct_col)
                    predicted_value = row.get(predicted_col)
                    record_data[field_name] = (correct_value, predicted_value)
            
            if record_data:
                # 評估本筆記錄
                evaluation = self.evaluate_record_fields(record_data, record_id, subject_id)
                record_evaluations.append(evaluation)
        
        return record_evaluations
    
    def generate_record_report(self, record_evaluations: List[RecordEvaluation]) -> str:
        """生成按記錄的詳細評估報告"""
        if not record_evaluations:
            return "無評估結果"
        
        report = []
        report.append("=" * 80)
        report.append("身心障礙手冊AI測試結果 - 按編號欄位準確度評估報告")
        report.append("=" * 80)
        
        # 整體統計
        total_records = len(record_evaluations)
        avg_accuracy = np.mean([eval_result.overall_accuracy for eval_result in record_evaluations])
        perfect_records = sum(1 for eval_result in record_evaluations if eval_result.matched_fields == eval_result.total_fields)
        
        report.append(f"📊 整體統計:")
        report.append(f"  總記錄數: {total_records}")
        report.append(f"  平均準確度: {avg_accuracy:.2%}")
        report.append(f"  完全正確記錄: {perfect_records}/{total_records} ({perfect_records/total_records:.1%})")
        report.append("")
        
        # 各欄位統計
        if record_evaluations:
            field_names = list(record_evaluations[0].field_results.keys())
            report.append(f"📈 各欄位統計:")
            
            for field_name in field_names:
                field_accuracies = []
                field_matches = 0
                
                for evaluation in record_evaluations:
                    if field_name in evaluation.field_results:
                        field_result = evaluation.field_results[field_name]
                        field_accuracies.append(field_result.similarity)
                        if field_result.is_exact_match:
                            field_matches += 1
                
                avg_field_accuracy = np.mean(field_accuracies) if field_accuracies else 0
                match_rate = field_matches / len(field_accuracies) if field_accuracies else 0
                
                report.append(f"  {field_name}: {avg_field_accuracy:.2%} (完全匹配: {field_matches}/{len(field_accuracies)}, {match_rate:.1%})")
            
            report.append("")
        
        # 詳細記錄分析
        report.append(f"📋 詳細記錄分析:")
        report.append("-" * 80)
        
        for i, evaluation in enumerate(record_evaluations, 1):
            report.append(f"【記錄 {evaluation.record_id}】受編: {evaluation.subject_id}")
            report.append(f"  整體準確度: {evaluation.overall_accuracy:.2%} ({evaluation.matched_fields}/{evaluation.total_fields} 完全匹配)")
            
            for field_name, field_result in evaluation.field_results.items():
                status = "✅" if field_result.is_exact_match else "❌" if field_result.similarity < 0.5 else "⚠️"
                report.append(f"    {status} {field_name}: {field_result.similarity:.1%}")
                
                if not field_result.is_exact_match:
                    report.append(f"      正確: '{field_result.correct_value}'")
                    report.append(f"      預測: '{field_result.predicted_value}'")
            
            report.append("")
        
        return "\n".join(report)
    
    def save_record_results(self, record_evaluations: List[RecordEvaluation], 
                           output_path: str = "record_accuracy_details.xlsx"):
        """儲存按記錄的詳細結果到Excel檔案"""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 記錄摘要頁
            summary_data = []
            for evaluation in record_evaluations:
                summary_data.append({
                    '編號': evaluation.record_id,
                    '受編': evaluation.subject_id,
                    '整體準確度': f"{evaluation.overall_accuracy:.2%}",
                    '完全匹配欄位數': evaluation.matched_fields,
                    '總欄位數': evaluation.total_fields,
                    '匹配率': f"{evaluation.matched_fields/evaluation.total_fields:.1%}" if evaluation.total_fields > 0 else "0%",
                    '狀態描述': f"({evaluation.matched_fields}/{evaluation.total_fields} 完全匹配)"
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='記錄摘要', index=False)
            
            # 詳細欄位比較頁 - 增強版
            detailed_data = []
            for evaluation in record_evaluations:
                for field_name, field_result in evaluation.field_results.items():
                    status_icon = '✅' if field_result.is_exact_match else '❌' if field_result.similarity < 0.5 else '⚠️'
                    status_text = '完全匹配' if field_result.is_exact_match else '不匹配' if field_result.similarity < 0.5 else '部分匹配'
                    
                    detailed_data.append({
                        '編號': field_result.record_id,
                        '受編': field_result.subject_id,
                        '欄位': field_name,
                        '狀態圖示': status_icon,
                        '狀態': status_text,
                        '相似度': f"{field_result.similarity:.1%}",
                        '相似度數值': field_result.similarity,
                        '正確值': field_result.correct_value,
                        '預測值': field_result.predicted_value,
                        '完全匹配': '是' if field_result.is_exact_match else '否',
                        '差異描述': '完全相同' if field_result.is_exact_match else f"相似度: {field_result.similarity:.1%}"
                    })
            
            detailed_df = pd.DataFrame(detailed_data)
            detailed_df.to_excel(writer, sheet_name='詳細欄位比較', index=False)
            
            # 記錄詳情頁 - 新增，格式化顯示每筆記錄的完整資訊
            record_details_data = []
            for evaluation in record_evaluations:
                # 為每筆記錄添加標題行
                record_details_data.append({
                    '記錄編號': f"【記錄 {evaluation.record_id}】",
                    '受編': evaluation.subject_id,
                    '整體準確度': f"{evaluation.overall_accuracy:.2%}",
                    '匹配情況': f"({evaluation.matched_fields}/{evaluation.total_fields} 完全匹配)",
                    '欄位名稱': '',
                    '狀態': '',
                    '相似度': '',
                    '正確值': '',
                    '預測值': '',
                    '備註': '=== 記錄標題 ==='
                })
                
                # 添加每個欄位的詳細資訊
                for field_name, field_result in evaluation.field_results.items():
                    status_icon = '✅' if field_result.is_exact_match else '❌' if field_result.similarity < 0.5 else '⚠️'
                    
                    record_details_data.append({
                        '記錄編號': '',
                        '受編': '',
                        '整體準確度': '',
                        '匹配情況': '',
                        '欄位名稱': field_name,
                        '狀態': f"{status_icon} {field_result.similarity:.1%}",
                        '相似度': f"{field_result.similarity:.1%}",
                        '正確值': field_result.correct_value,
                        '預測值': field_result.predicted_value,
                        '備註': '完全匹配' if field_result.is_exact_match else '需要改進' if field_result.similarity < 0.5 else '部分匹配'
                    })
                
                # 添加空行分隔
                record_details_data.append({
                    '記錄編號': '',
                    '受編': '',
                    '整體準確度': '',
                    '匹配情況': '',
                    '欄位名稱': '',
                    '狀態': '',
                    '相似度': '',
                    '正確值': '',
                    '預測值': '',
                    '備註': '--- 分隔線 ---'
                })
            
            record_details_df = pd.DataFrame(record_details_data)
            record_details_df.to_excel(writer, sheet_name='記錄詳情', index=False)
            
            # 各欄位統計頁
            if record_evaluations:
                field_names = list(record_evaluations[0].field_results.keys())
                field_stats_data = []
                
                for field_name in field_names:
                    accuracies = []
                    matches = 0
                    total = 0
                    
                    for evaluation in record_evaluations:
                        if field_name in evaluation.field_results:
                            field_result = evaluation.field_results[field_name]
                            accuracies.append(field_result.similarity)
                            if field_result.is_exact_match:
                                matches += 1
                            total += 1
                    
                    avg_accuracy = np.mean(accuracies) if accuracies else 0
                    match_rate = matches / total if total > 0 else 0
                    
                    field_stats_data.append({
                        '欄位名稱': field_name,
                        '平均準確度': f"{avg_accuracy:.2%}",
                        '完全匹配數': matches,
                        '總記錄數': total,
                        '匹配率': f"{match_rate:.1%}",
                        '需改進記錄數': total - matches,
                        '表現等級': '優秀' if avg_accuracy >= 0.9 else '良好' if avg_accuracy >= 0.7 else '需改進'
                    })
                
                field_stats_df = pd.DataFrame(field_stats_data)
                field_stats_df.to_excel(writer, sheet_name='欄位統計', index=False)
            
            # 錯誤分析頁 - 新增，專門分析需要改進的項目
            error_analysis_data = []
            for evaluation in record_evaluations:
                for field_name, field_result in evaluation.field_results.items():
                    if not field_result.is_exact_match:
                        error_type = '格式差異' if field_result.similarity > 0.7 else '內容錯誤' if field_result.similarity > 0.3 else '完全不符'
                        
                        error_analysis_data.append({
                            '編號': field_result.record_id,
                            '受編': field_result.subject_id,
                            '欄位': field_name,
                            '錯誤類型': error_type,
                            '相似度': f"{field_result.similarity:.1%}",
                            '正確值': field_result.correct_value,
                            '預測值': field_result.predicted_value,
                            '改進建議': self._get_improvement_suggestion(field_result)
                        })
            
            if error_analysis_data:
                error_analysis_df = pd.DataFrame(error_analysis_data)
                error_analysis_df.to_excel(writer, sheet_name='錯誤分析', index=False)
    
    def _get_improvement_suggestion(self, field_result: RecordFieldResult) -> str:
        """為欄位錯誤提供改進建議"""
        if field_result.similarity > 0.8:
            return "格式標準化 - 相似度高，主要是格式問題"
        elif field_result.similarity > 0.5:
            return "內容檢查 - 部分正確，需要細節調整"
        elif field_result.similarity > 0.2:
            return "重新訓練 - 識別錯誤，需要加強相關資料訓練"
        else:
            return "完全重做 - 識別失敗，需要重新處理或手動檢查"
    
    def generate_report(self, results: Dict[str, EvaluationResult], 
                       overall_accuracy: float) -> str:
        """生成評估報告"""
        report = []
        report.append("=" * 60)
        report.append("身心障礙手冊AI測試結果準確度評估報告")
        report.append("=" * 60)
        report.append(f"整體準確度: {overall_accuracy:.2%}")
        report.append("")
        
        for field_name, result in results.items():
            report.append(f"【{field_name}】")
            report.append(f"  準確度: {result.accuracy:.2%}")
            report.append(f"  完全匹配: {result.exact_matches}/{result.total_records} "
                         f"({result.exact_matches/result.total_records:.1%})")
            
            if result.mismatched_pairs:
                report.append(f"  不匹配項目數: {len(result.mismatched_pairs)}")
                report.append("  主要不匹配項目:")
                for i, (correct, predicted) in enumerate(result.mismatched_pairs[:3]):
                    report.append(f"    {i+1}. 正確: '{correct}' -> 預測: '{predicted}'")
                if len(result.mismatched_pairs) > 3:
                    report.append(f"    ... 還有 {len(result.mismatched_pairs)-3} 項")
            report.append("")
        
        return "\n".join(report)
    
    def save_detailed_results(self, results: Dict[str, EvaluationResult], 
                             output_path: str = "accuracy_details.xlsx"):
        """儲存詳細結果到Excel檔案"""
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 摘要頁
            summary_data = []
            for field_name, result in results.items():
                summary_data.append({
                    '欄位名稱': field_name,
                    '準確度': f"{result.accuracy:.2%}",
                    '完全匹配數': result.exact_matches,
                    '總記錄數': result.total_records,
                    '匹配率': f"{result.exact_matches/result.total_records:.1%}",
                    '不匹配項目數': len(result.mismatched_pairs)
                })
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='摘要', index=False)
            
            # 詳細錯誤頁
            for field_name, result in results.items():
                if result.mismatched_pairs:
                    error_data = []
                    for correct, predicted in result.mismatched_pairs:
                        similarity = self.calculate_similarity(correct, predicted)
                        error_data.append({
                            '正確值': correct,
                            '預測值': predicted,
                            '相似度': f"{similarity:.2%}"
                        })
                    
                    error_df = pd.DataFrame(error_data)
                    sheet_name = f"{field_name}_錯誤詳情"[:31]  # Excel工作表名稱限制
                    error_df.to_excel(writer, sheet_name=sheet_name, index=False)

def main():
    """主程式"""
    evaluator = DisabilityDataEvaluator()
    
    # 使用範例資料進行示範
    print("使用範例資料進行準確度評估...")
    df = evaluator.create_sample_data()
    
    # 如果有實際的Excel檔案，可以取消註解以下行
    # df = evaluator.load_data_from_excel("身心障礙手冊_AI測試結果資料.xlsx")
    
    if df is not None:
        print(f"載入資料成功，共 {len(df)} 筆記錄")
        
        # 傳統整體評估
        print("\n=== 傳統整體評估 ===")
        results = evaluator.evaluate_all_fields(df)
        overall_accuracy = evaluator.calculate_overall_accuracy(results)
        report = evaluator.generate_report(results, overall_accuracy)
        print(report)
        
        # 新的按記錄評估
        print("\n=== 按編號個別欄位評估 ===")
        record_evaluations = evaluator.evaluate_all_records(df)
        record_report = evaluator.generate_record_report(record_evaluations)
        print(record_report)
        
        # 儲存結果
        evaluator.save_detailed_results(results, "整體準確度評估.xlsx")
        evaluator.save_record_results(record_evaluations, "按編號欄位準確度評估.xlsx")
        print("\n詳細結果已儲存至:")
        print("- 整體準確度評估.xlsx")
        print("- 按編號欄位準確度評估.xlsx")
        
    else:
        print("無法載入資料，請檢查檔案路徑")

if __name__ == "__main__":
    main()
