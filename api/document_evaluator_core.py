#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外來函文資料評估核心模組
Document Data Evaluator Core Module
"""

import pandas as pd
import numpy as np
import re
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Tuple, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FieldType(Enum):
    """欄位類型枚舉"""
    DATE = "日期"
    AMOUNT = "金額" 
    BOOLEAN = "布林值"
    TEXT = "文字"
    JUDGMENT = "判斷"

class ComparisonType(Enum):
    """比對類型枚舉"""
    EXACT_MATCH = "精確匹配"
    NUMERIC_MATCH = "數值匹配"
    DATE_MATCH = "日期匹配"
    TEXT_SIMILARITY = "文字相似度"

@dataclass
class DocumentFieldResult:
    """外來函文單個欄位的評估結果"""
    field_name: str           # 欄位名稱
    field_type: FieldType     # 欄位類型
    correct_value: str        # 正確答案
    predicted_value: str      # AI預測值
    similarity: float         # 相似度 (0-1)
    is_exact_match: bool      # 是否完全匹配
    cer: float = 0.0          # 字元錯誤率
    wer: float = 0.0          # 單詞錯誤率
    error_description: str = ""  # 錯誤描述

@dataclass
class DocumentEvaluation:
    """外來函文單筆記錄的完整評估結果"""
    record_id: str
    case_number: str
    field_results: Dict[str, DocumentFieldResult]
    overall_accuracy: float
    total_fields: int
    matched_fields: int
    field_type_accuracy: Dict[FieldType, float]  # 各類型欄位的準確度

class DocumentDataEvaluator:
    """外來函文資料準確度評估器"""
    
    def __init__(self):
        """初始化外來函文評估器"""
        self.similarity_threshold = 0.8
        
        # 基於實際檔案結構的欄位映射
        self.field_mappings = {
            '發文日期': {
                'ai_column': 'gemma 3 27b qat',
                'human_column': 'Unnamed: 5',
                'type': FieldType.DATE,
                'comparison': ComparisonType.DATE_MATCH
            },
            '得請領_金額': {
                'ai_column': 'Chatgpt 4.1',
                'human_column': 'Unnamed: 8',
                'type': FieldType.AMOUNT,
                'comparison': ComparisonType.NUMERIC_MATCH
            },
            '繼續性_金額': {
                'ai_column': 'Chatgpt 4.1.1',
                'human_column': 'Unnamed: 11',
                'type': FieldType.AMOUNT,
                'comparison': ComparisonType.NUMERIC_MATCH
            },
            '解約金_金額': {
                'ai_column': 'Chatgpt 4.1.2',
                'human_column': 'Unnamed: 14',
                'type': FieldType.AMOUNT,
                'comparison': ComparisonType.NUMERIC_MATCH
            },
            '解約金_範圍': {
                'ai_column': 'Chatgpt 4.1.3',
                'human_column': 'Unnamed: 17',
                'type': FieldType.TEXT,
                'comparison': ComparisonType.EXACT_MATCH  # 改為精確匹配，因為是單筆/全部
            },
            '小額終老非扣押範圍': {
                'ai_column': 'Chatgpt 4.1.4',
                'human_column': 'Unnamed: 20',
                'type': FieldType.BOOLEAN,
                'comparison': ComparisonType.EXACT_MATCH
            },
        }
    
    def normalize_date(self, date_str: str) -> str:
        """標準化日期格式"""
        if pd.isna(date_str) or date_str is None:
            return ""
        
        date_str = str(date_str).strip()
        if not date_str:
            return ""
        
        # 移除常見的日期分隔符，統一為數字
        normalized = re.sub(r'[/-]', '', date_str)
        
        # 如果是8位數字，轉換為標準格式 (例如: 1140424 -> 114/04/24)
        if re.match(r'^\d{7,8}$', normalized):
            if len(normalized) == 7:
                normalized = '0' + normalized
            year = normalized[:3]
            month = normalized[3:5]
            day = normalized[5:7]
            return f"{year}/{month}/{day}"
        
        return date_str
    
    def normalize_amount(self, amount_str: str) -> float:
        """標準化金額格式"""
        if pd.isna(amount_str) or amount_str is None:
            return 0.0
        
        amount_str = str(amount_str).strip()
        if not amount_str:
            return 0.0
        
        # 移除逗號和其他非數字字符
        cleaned = re.sub(r'[,\s]', '', amount_str)
        
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def normalize_boolean(self, bool_str: str) -> str:
        """標準化布林值格式"""
        if pd.isna(bool_str) or bool_str is None:
            return ""
        
        bool_str = str(bool_str).strip().upper()
        
        if bool_str in ['Y', 'YES', 'TRUE', '1', '是']:
            return 'Y'
        elif bool_str in ['N', 'NO', 'FALSE', '0', '否']:
            return 'N'
        
        return bool_str
    
    def calculate_cer(self, correct: str, predicted: str) -> float:
        """計算字元錯誤率 (Character Error Rate)"""
        if not correct and not predicted:
            return 0.0
        if not correct:
            return 1.0
        if not predicted:
            return 1.0
        
        correct = str(correct)
        predicted = str(predicted)
        
        # 計算編輯距離
        edit_distance = self._edit_distance(correct, predicted)
        
        # CER = 編輯距離 / 正確字符數
        return edit_distance / len(correct) if len(correct) > 0 else 1.0
    
    def calculate_wer(self, correct: str, predicted: str) -> float:
        """計算單詞錯誤率 (Word Error Rate)"""
        if not correct and not predicted:
            return 0.0
        if not correct:
            return 1.0
        if not predicted:
            return 1.0
        
        # 對於中文，按字符分割
        correct_chars = list(str(correct))
        predicted_chars = list(str(predicted))
        
        if not correct_chars:
            return 1.0
        
        # 計算編輯距離
        edit_distance = self._edit_distance(correct_chars, predicted_chars)
        
        # WER = 編輯距離 / 正確字符數
        return edit_distance / len(correct_chars)
    
    def _edit_distance(self, seq1, seq2) -> int:
        """計算編輯距離（Levenshtein距離）"""
        len1, len2 = len(seq1), len(seq2)
        
        # 創建距離矩陣
        dp = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # 初始化第一行和第一列
        for i in range(len1 + 1):
            dp[i][0] = i
        for j in range(len2 + 1):
            dp[0][j] = j
        
        # 填充距離矩陣
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                if seq1[i - 1] == seq2[j - 1]:
                    dp[i][j] = dp[i - 1][j - 1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i - 1][j],      # 刪除
                        dp[i][j - 1],      # 插入
                        dp[i - 1][j - 1]     # 替換
                    )
        
        return dp[len1][len2]
    
    def calculate_date_similarity(self, correct: str, predicted: str) -> float:
        """計算日期相似度"""
        norm_correct = self.normalize_date(correct)
        norm_predicted = self.normalize_date(predicted)
        
        if norm_correct == norm_predicted:
            return 1.0
        
        # 分割日期比較各部分
        correct_parts = norm_correct.split('/')
        predicted_parts = norm_predicted.split('/')
        
        if len(correct_parts) == 3 and len(predicted_parts) == 3:
            matches = sum(1 for c, p in zip(correct_parts, predicted_parts) if c == p)
            return matches / 3.0
        
        return 0.0
    
    def calculate_amount_similarity(self, correct: str, predicted: str) -> float:
        """計算金額相似度"""
        norm_correct = self.normalize_amount(correct)
        norm_predicted = self.normalize_amount(predicted)
        
        if norm_correct == norm_predicted:
            return 1.0
        
        return 0.0
    
    def calculate_boolean_similarity(self, correct: str, predicted: str) -> float:
        """計算布林值相似度"""
        norm_correct = self.normalize_boolean(correct)
        norm_predicted = self.normalize_boolean(predicted)
        
        return 1.0 if norm_correct == norm_predicted else 0.0
    
    def calculate_text_similarity(self, correct: str, predicted: str) -> float:
        """計算文字相似度"""
        if str(correct).strip() == str(predicted).strip():
            return 1.0
        
        # 使用字元錯誤率計算相似度
        cer = self.calculate_cer(correct, predicted)
        return max(0.0, 1.0 - cer)
    
    def evaluate_single_field(self, correct_value: Any, predicted_value: Any, field_name: str) -> DocumentFieldResult:
        """
        評估單個欄位的準確度
        
        Args:
            correct_value: 正確值
            predicted_value: 預測值
            field_name: 欄位名稱
            
        Returns:
            DocumentFieldResult: 欄位評估結果
        """
        # 確定欄位類型
        field_type = self.determine_field_type(field_name, correct_value, predicted_value)
        
        # 標準化數值
        norm_correct = self.normalize_value(correct_value, field_type)
        norm_predicted = self.normalize_value(predicted_value, field_type)
        
        # 計算相似度
        similarity = self.calculate_field_similarity(norm_correct, norm_predicted, field_type)
        
        # 計算OCR指標
        cer = self.calculate_cer(str(norm_correct), str(norm_predicted))
        wer = self.calculate_wer(str(norm_correct), str(norm_predicted))
        
        # 判斷是否完全匹配
        is_exact_match = similarity >= 0.99
        
        # 生成錯誤描述
        error_description = self.generate_error_description(
            norm_correct, norm_predicted, field_type, similarity
        )
        
        return DocumentFieldResult(
            field_name=field_name,
            field_type=field_type,
            correct_value=str(norm_correct),
            predicted_value=str(norm_predicted),
            similarity=similarity,
            is_exact_match=is_exact_match,
            cer=cer,
            wer=wer,
            error_description=error_description
        )
    
    def determine_field_type(self, field_name: str, correct_value: Any, predicted_value: Any) -> FieldType:
        """根據欄位名稱和內容確定欄位類型"""
        field_name_lower = field_name.lower()
        
        # 根據欄位名稱判斷
        if '日期' in field_name or 'date' in field_name_lower:
            return FieldType.DATE
        elif '金額' in field_name or 'amount' in field_name_lower or '元' in field_name:
            return FieldType.AMOUNT
        elif '範圍' in field_name and ('單筆' in str(correct_value) or '全部' in str(correct_value)):
            return FieldType.TEXT
        elif field_name == '小額終老非扣押範圍':
            return FieldType.BOOLEAN
        
        # 根據內容判斷
        for value in [correct_value, predicted_value]:
            if pd.notna(value):
                value_str = str(value).strip()
                
                # 布林值判斷
                if value_str in ['Y', 'N', 'y', 'n', 'Yes', 'No', 'True', 'False']:
                    return FieldType.BOOLEAN
                
                # 日期判斷
                if re.match(r'\d{2,3}[/-]\d{1,2}[/-]\d{1,2}', value_str):
                    return FieldType.DATE
                
                # 金額判斷
                if re.match(r'^\d+(\.\d+)?$', value_str.replace(',', '')):
                    return FieldType.AMOUNT
        
        return FieldType.TEXT
    
    def normalize_value(self, value: Any, field_type: FieldType) -> Any:
        """根據欄位類型標準化數值"""
        if pd.isna(value):
            return ""
        
        if field_type == FieldType.DATE:
            return self.normalize_date(str(value))
        elif field_type == FieldType.AMOUNT:
            return self.normalize_amount(str(value))
        elif field_type == FieldType.BOOLEAN:
            return self.normalize_boolean(str(value))
        else:
            return str(value).strip()
    
    def calculate_field_similarity(self, correct_value: Any, predicted_value: Any, field_type: FieldType) -> float:
        """根據欄位類型計算相似度"""
        if field_type == FieldType.DATE:
            return self.calculate_date_similarity(str(correct_value), str(predicted_value))
        elif field_type == FieldType.AMOUNT:
            return self.calculate_amount_similarity(str(correct_value), str(predicted_value))
        elif field_type == FieldType.BOOLEAN:
            return self.calculate_boolean_similarity(str(correct_value), str(predicted_value))
        else:
            return self.calculate_text_similarity(str(correct_value), str(predicted_value))
    
    def generate_error_description(
        self,
        correct_value: Any,
        predicted_value: Any,
        field_type: FieldType,
        similarity: float
    ) -> str:
        """生成錯誤描述"""
        if similarity >= 0.99:
            return ""
        
        if field_type == FieldType.DATE:
            return "日期格式或內容不符"
        elif field_type == FieldType.AMOUNT:
            return "金額數值錯誤"
        elif field_type == FieldType.BOOLEAN:
            return "Y/N判斷錯誤"
        else:
            return "文字內容不符"

    def evaluate_record_fields(
        self,
        record_data: Dict[str, Tuple[Any, Any]],
        record_id: str,
        case_number: str
    ) -> DocumentEvaluation:
        """評估單筆記錄的所有欄位"""
        field_results = {}
        field_type_stats = {}
        total_fields = 0
        matched_fields = 0
        
        for field_name, (correct_value, predicted_value) in record_data.items():
            total_fields += 1
            
            # 評估單個欄位
            field_result = self.evaluate_single_field(correct_value, predicted_value, field_name)
            field_results[field_name] = field_result
            
            # 統計匹配欄位
            if field_result.is_exact_match:
                matched_fields += 1
            
            # 按類型統計
            field_type = field_result.field_type
            if field_type not in field_type_stats:
                field_type_stats[field_type] = {'total': 0, 'correct': 0}
            field_type_stats[field_type]['total'] += 1
            if field_result.is_exact_match:
                field_type_stats[field_type]['correct'] += 1
        
        # 計算各類型準確度
        field_type_accuracy = {}
        for field_type, stats in field_type_stats.items():
            accuracy = stats['correct'] / stats['total'] if stats['total'] > 0 else 0.0
            field_type_accuracy[field_type] = accuracy
        
        # 計算整體準確度
        overall_accuracy = matched_fields / total_fields if total_fields > 0 else 0.0
        
        return DocumentEvaluation(
            record_id=record_id,
            case_number=case_number,
            field_results=field_results,
            overall_accuracy=overall_accuracy,
            total_fields=total_fields,
            matched_fields=matched_fields,
            field_type_accuracy=field_type_accuracy
        )
    
    def evaluate_all_records(self, df: pd.DataFrame) -> List[DocumentEvaluation]:
        """評估所有外來函文記錄"""
        record_evaluations = []
        
        for index, row in df.iterrows():
            # 跳過標題行
            if index == 0:
                continue
            
            # 取得案件號作為記錄ID (第一欄是案件號)
            case_number = str(row.iloc[0]) if pd.notna(row.iloc[0]) else f'記錄{index}'
            record_id = str(index)
            
            # 準備本筆記錄的欄位資料
            record_data = {}
            
            for field_name, config in self.field_mappings.items():
                ai_col = config['ai_column']
                human_col = config['human_column']
                
                if ai_col in df.columns and human_col in df.columns:
                    correct_value = row.get(human_col)
                    predicted_value = row.get(ai_col)
                    
                    # 只評估有資料的欄位
                    if pd.notna(correct_value) or pd.notna(predicted_value):
                        record_data[field_name] = (correct_value, predicted_value)
            
            if record_data:
                # 評估本筆記錄
                evaluation = self.evaluate_record_fields(record_data, record_id, case_number)
                record_evaluations.append(evaluation)
        
        return record_evaluations
