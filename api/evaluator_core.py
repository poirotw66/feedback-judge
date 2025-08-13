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
    cer: float = 0.0  # 字元錯誤率
    wer: float = 0.0  # 單詞錯誤率

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
        """標準化文字處理（OCR專用，保留原始字元）"""
        if pd.isna(text) or text is None:
            return ""

        text = str(text).strip()
        # 移除多餘的空格，但保留原始字元用於精確OCR評估
        text = re.sub(r'\s+', '', text)
        # 不進行括號轉換，保持原始字元以進行精確的OCR評估
        return text

    def normalize_text_for_wer(self, text: str) -> str:
        """標準化文字，用於WER計算（保留空格用於單詞分割）"""
        if pd.isna(text) or text is None:
            return ""

        text = str(text).strip()
        # 標準化空格，但保留用於單詞分割
        text = re.sub(r'\s+', ' ', text)
        return text
    
    def calculate_cer(self, reference: str, hypothesis: str) -> float:
        """
        計算字元錯誤率 (Character Error Rate, CER)
        CER = (S + D + I) / N
        其中 S=替換, D=刪除, I=插入, N=參考文字字元數
        """
        ref_norm = self.normalize_text(reference)
        hyp_norm = self.normalize_text(hypothesis)

        if not ref_norm and not hyp_norm:
            return 0.0
        if not ref_norm:
            return 1.0 if hyp_norm else 0.0
        if not hyp_norm:
            return 1.0

        # 使用標準的編輯距離算法計算CER
        return self._calculate_edit_distance_rate(ref_norm, hyp_norm)
    
    def calculate_wer(self, reference: str, hypothesis: str) -> float:
        """
        計算單詞錯誤率 (Word Error Rate, WER)
        WER = (S + D + I) / N
        其中 S=替換, D=刪除, I=插入, N=參考文字單詞數

        對於中文，將每個字符視為一個"單詞"
        對於英文，按空格分割單詞
        """
        # 使用保留空格的標準化方法
        ref_norm = self.normalize_text_for_wer(reference)
        hyp_norm = self.normalize_text_for_wer(hypothesis)

        if not ref_norm and not hyp_norm:
            return 0.0
        if not ref_norm:
            return 1.0 if hyp_norm else 0.0
        if not hyp_norm:
            return 1.0

        # 智能分詞：如果包含空格則按空格分割，否則按字符分割
        if ' ' in ref_norm or ' ' in hyp_norm:
            # 英文模式：按空格分割單詞
            ref_words = ref_norm.split()
            hyp_words = hyp_norm.split()
        else:
            # 中文模式：每個字符視為一個單詞
            ref_words = list(ref_norm)
            hyp_words = list(hyp_norm)

        # 使用標準的編輯距離算法計算WER
        return self._calculate_edit_distance_rate(ref_words, hyp_words)

    def _calculate_edit_distance_rate(self, reference, hypothesis) -> float:
        """
        使用動態規劃計算標準編輯距離錯誤率

        Args:
            reference: 參考序列（字符串或列表）
            hypothesis: 假設序列（字符串或列表）

        Returns:
            float: 錯誤率 (0.0 到 1.0+)
        """
        if not reference and not hypothesis:
            return 0.0
        if not reference:
            return 1.0
        if not hypothesis:
            return 1.0

        # 轉換為列表以統一處理
        if isinstance(reference, str):
            ref_seq = list(reference)
        else:
            ref_seq = reference

        if isinstance(hypothesis, str):
            hyp_seq = list(hypothesis)
        else:
            hyp_seq = hypothesis

        # 動態規劃計算編輯距離
        m, n = len(ref_seq), len(hyp_seq)

        # 創建DP表
        dp = [[0] * (n + 1) for _ in range(m + 1)]

        # 初始化邊界條件
        for i in range(m + 1):
            dp[i][0] = i  # 刪除操作
        for j in range(n + 1):
            dp[0][j] = j  # 插入操作

        # 填充DP表
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if ref_seq[i-1] == hyp_seq[j-1]:
                    # 字符相同，不需要操作
                    dp[i][j] = dp[i-1][j-1]
                else:
                    # 字符不同，選擇最小代價操作
                    dp[i][j] = 1 + min(
                        dp[i-1][j],    # 刪除
                        dp[i][j-1],    # 插入
                        dp[i-1][j-1]   # 替換
                    )

        # 計算錯誤率
        edit_distance = dp[m][n]

        # 使用較長序列作為分母，避免錯誤率超過100%
        max_length = max(len(ref_seq), len(hyp_seq))
        if max_length == 0:
            return 0.0

        error_rate = edit_distance / max_length
        # 確保錯誤率不超過1.0 (100%)
        return min(error_rate, 1.0)

    def calculate_cer_accuracy(self, reference: str, hypothesis: str) -> float:
        """
        計算基於CER的準確率
        準確率 = 1 - CER
        """
        cer = self.calculate_cer(reference, hypothesis)
        return max(0.0, 1.0 - cer)

    def calculate_wer_accuracy(self, reference: str, hypothesis: str) -> float:
        """
        計算基於WER的準確率
        準確率 = 1 - WER
        """
        wer = self.calculate_wer(reference, hypothesis)
        return max(0.0, 1.0 - wer)

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """
        計算兩個文字的相似度（基於CER的準確度）
        準確度 = 1 - CER
        """
        return self.calculate_cer_accuracy(text1, text2)
    
    def calculate_ocr_metrics(self, reference: str, hypothesis: str) -> Dict[str, float]:
        """
        計算OCR評估的完整指標
        返回: CER, WER, 以及基於CER的準確度
        """
        cer = self.calculate_cer(reference, hypothesis)
        wer = self.calculate_wer(reference, hypothesis)
        accuracy = max(0.0, 1.0 - cer)
        
        return {
            'cer': cer,
            'wer': wer,
            'accuracy': accuracy,
            'similarity': accuracy  # 保持向後兼容性
        }
    
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
            # 檢查欄位是否存在（支援索引和名稱）
            correct_exists = False
            predicted_exists = False

            if isinstance(correct_col, int):
                correct_exists = correct_col < len(df.columns)
            else:
                correct_exists = correct_col in df.columns

            if isinstance(predicted_col, int):
                predicted_exists = predicted_col < len(df.columns)
            else:
                predicted_exists = predicted_col in df.columns

            if correct_exists and predicted_exists:
                # 檢查欄位是否有實際資料
                if isinstance(correct_col, int):
                    correct_data = df.iloc[:, correct_col].dropna()
                else:
                    correct_data = df[correct_col].dropna()

                if isinstance(predicted_col, int):
                    predicted_data = df.iloc[:, predicted_col].dropna()
                else:
                    predicted_data = df[predicted_col].dropna()

                if len(correct_data) == 0:
                    print(f"警告: 正確答案欄位 {correct_col} 沒有資料")
                    continue
                if len(predicted_data) == 0:
                    print(f"警告: 預測結果欄位 {predicted_col} 沒有資料")
                    continue

                # 處理欄位映射（支援索引和名稱）
                if isinstance(correct_col, int):
                    # 如果是索引，直接使用iloc
                    correct_values = df.iloc[:, correct_col].tolist()
                else:
                    # 如果是欄位名稱，處理重複欄位名稱的情況
                    correct_data = df[correct_col]
                    if isinstance(correct_data, pd.DataFrame):
                        correct_values = correct_data.iloc[:, 0].tolist()
                    else:
                        correct_values = correct_data.tolist()

                if isinstance(predicted_col, int):
                    # 如果是索引，直接使用iloc
                    predicted_values = df.iloc[:, predicted_col].tolist()
                else:
                    # 如果是欄位名稱，處理重複欄位名稱的情況
                    predicted_data = df[predicted_col]
                    if isinstance(predicted_data, pd.DataFrame):
                        predicted_values = predicted_data.iloc[:, 1].tolist() if predicted_data.shape[1] > 1 else predicted_data.iloc[:, 0].tolist()
                    else:
                        predicted_values = predicted_data.tolist()

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
            # 計算OCR指標
            ocr_metrics = self.calculate_ocr_metrics(correct_value, predicted_value)
            similarity = ocr_metrics['accuracy']
            cer = ocr_metrics['cer']
            wer = ocr_metrics['wer']
            
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
                is_exact_match=is_exact_match,
                cer=cer,
                wer=wer
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
                # 檢查欄位是否存在（支援索引和名稱）
                correct_exists = False
                predicted_exists = False

                if isinstance(correct_col, int):
                    correct_exists = correct_col < len(df.columns)
                else:
                    correct_exists = correct_col in df.columns

                if isinstance(predicted_col, int):
                    predicted_exists = predicted_col < len(df.columns)
                else:
                    predicted_exists = predicted_col in df.columns

                if correct_exists and predicted_exists:
                    # 取得欄位值（支援索引和名稱）
                    if isinstance(correct_col, int):
                        correct_value = row.iloc[correct_col]
                    else:
                        correct_value = row.get(correct_col)

                    if isinstance(predicted_col, int):
                        predicted_value = row.iloc[predicted_col]
                    else:
                        predicted_value = row.get(predicted_col)

                    # 檢查是否有實際資料（不是NaN或空值）
                    if pd.notna(correct_value) and pd.notna(predicted_value):
                        record_data[field_name] = (str(correct_value), str(predicted_value))
                    elif pd.notna(correct_value) and pd.isna(predicted_value):
                        # 有正確答案但沒有預測結果，記錄為0分
                        record_data[field_name] = (str(correct_value), "")
                    # 如果正確答案也是空的，就跳過這個欄位

            if record_data:
                # 評估本筆記錄
                evaluation = self.evaluate_record_fields(record_data, record_id, subject_id)
                record_evaluations.append(evaluation)
        return record_evaluations
    
    def get_improvement_suggestion(self, field_result: RecordFieldResult) -> str:
        """為欄位錯誤提供改進建議（基於CER）"""
        cer = field_result.cer
        wer = field_result.wer
        
        if cer == 0.0:
            return "完美識別 - 無需改進"
        elif cer <= 0.1:
            return "優秀識別 - 僅有微小錯誤，可能是格式問題"
        elif cer <= 0.2:
            return "良好識別 - 少量字元錯誤，建議檢查OCR預處理"
        elif cer <= 0.4:
            return "普通識別 - 中等程度錯誤，需要改進訓練資料品質"
        elif cer <= 0.6:
            return "較差識別 - 較多字元錯誤，建議增加相似樣本訓練"
        else:
            return "差劣識別 - 嚴重錯誤，需要重新檢查輸入資料或模型"
    
    def get_ocr_performance_level(self, cer: float) -> str:
        """根據CER判斷OCR性能等級"""
        if cer <= 0.05:
            return "優秀"
        elif cer <= 0.1:
            return "良好"
        elif cer <= 0.2:
            return "可接受"
        elif cer <= 0.4:
            return "需改進"
        else:
            return "不合格"
