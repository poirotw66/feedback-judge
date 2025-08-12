#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Evaluator Logic for Disability Certificate AI Test Results
身心障礙手冊AI測試結果準確度評分系統 - 核心評估邏輯
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
    """身心障礙資料準確度評估器 - 核心邏輯"""
    
    def __init__(self):
        self.similarity_threshold = 0.8
        self.weight_config = {
            FieldType.DISABILITY_LEVEL: 0.3,
            FieldType.DISABILITY_CATEGORY: 0.3,
            FieldType.ICD_DIAGNOSIS: 0.25,
            FieldType.CERTIFICATE_TYPE: 0.15
        }
        self.field_mappings = {
            '障礙等級': ('正面_障礙等級', '反面_障礙等級'),
            '障礙類別': ('正面_障礙類別', '反面_障礙類別'),
            'ICD診斷': ('正面_ICD診斷', '反面_ICD診斷')
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
    
    def evaluate_all_fields(self, df: pd.DataFrame) -> Dict[str, EvaluationResult]:
        """評估所有欄位的準確度"""
        results = {}

        for field_name, (correct_col, predicted_col) in self.field_mappings.items():
            if correct_col in df.columns and predicted_col in df.columns:
                # 檢查欄位是否有實際資料
                correct_data = df[correct_col].dropna()
                predicted_data = df[predicted_col].dropna()

                if len(correct_data) == 0:
                    print(f"警告: 正確答案欄位 {correct_col} 沒有資料")
                    continue
                if len(predicted_data) == 0:
                    print(f"警告: 預測結果欄位 {predicted_col} 沒有資料")
                    continue

                correct_values = df[correct_col].tolist()
                predicted_values = df[predicted_col].tolist()

                result = self.evaluate_field(correct_values, predicted_values, field_name)
                results[field_name] = result
                print(f"成功評估欄位: {field_name} ({correct_col} vs {predicted_col})")
            else:
                missing_cols = []
                if correct_col not in df.columns:
                    missing_cols.append(correct_col)
                if predicted_col not in df.columns:
                    missing_cols.append(predicted_col)
                print(f"警告: 找不到欄位 {missing_cols} for {field_name}")

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
            field_mappings = self.field_mappings

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

                    # 檢查是否有實際資料（不是NaN或空值）
                    if pd.notna(correct_value) and pd.notna(predicted_value):
                        record_data[field_name] = (correct_value, predicted_value)
                    elif pd.notna(correct_value) and pd.isna(predicted_value):
                        # 有正確答案但沒有預測結果，記錄為0分
                        record_data[field_name] = (correct_value, "")
                    # 如果正確答案也是空的，就跳過這個欄位

            if record_data:
                # 評估本筆記錄
                evaluation = self.evaluate_record_fields(record_data, record_id, subject_id)
                record_evaluations.append(evaluation)

        return record_evaluations
    
    def get_improvement_suggestion(self, field_result: RecordFieldResult) -> str:
        """為欄位錯誤提供改進建議"""
        if field_result.similarity > 0.8:
            return "格式標準化 - 相似度高，主要是格式問題"
        elif field_result.similarity > 0.5:
            return "內容檢查 - 部分正確，需要細節調整"
        elif field_result.similarity > 0.2:
            return "重新訓練 - 識別錯誤，需要加強相關資料訓練"
        else:
            return "完全重做 - 識別失敗，需要重新處理或手動檢查"
