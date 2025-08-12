#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Service Layer for Disability Certificate AI Test Results Accuracy Evaluation
身心障礙手冊AI測試結果準確度評分系統 - 服務層
"""

import pandas as pd
import numpy as np
import io
from typing import Dict, List, Tuple, Optional
import logging
from datetime import datetime
import time

from evaluator_core import DisabilityDataEvaluator, EvaluationResult, RecordEvaluation
from excel_generator import ExcelResultGenerator
from exceptions import (
    FileValidationError, FileProcessingError, DataValidationError,
    EvaluationError, ExcelGenerationError
)

logger = logging.getLogger(__name__)

class DisabilityDataEvaluatorService:
    """身心障礙資料準確度評估服務"""
    
    def __init__(self):
        self.evaluator = DisabilityDataEvaluator()
        self.excel_generator = ExcelResultGenerator()
    
    async def process_excel_file(self, file_content: bytes, filename: str) -> Tuple[bytes, str]:
        """
        處理上傳的Excel檔案並返回評估結果
        
        Args:
            file_content: Excel檔案內容
            filename: 原始檔案名稱
            
        Returns:
            Tuple[bytes, str]: (結果Excel檔案內容, 輸出檔案名稱)
        """
        start_time = time.time()
        
        try:
            # 從記憶體讀取Excel檔案
            df = self._read_excel_from_memory(file_content)
            
            if df is None or df.empty:
                raise FileProcessingError("無法讀取Excel檔案或檔案為空", filename)
            
            logger.info(f"成功載入Excel檔案，共 {len(df)} 筆記錄")
            
            # 驗證必要欄位
            self._validate_required_columns(df)
            
            # 執行評估
            field_results = self.evaluator.evaluate_all_fields(df)
            record_evaluations = self.evaluator.evaluate_all_records(df)
            overall_accuracy = self.evaluator.calculate_overall_accuracy(field_results)
            
            processing_time = time.time() - start_time
            
            # 生成結果摘要
            summary = self._create_evaluation_summary(
                df, field_results, record_evaluations, overall_accuracy, processing_time
            )
            
            # 生成輸出Excel檔案
            output_filename = self._generate_output_filename(filename)
            result_content = await self.excel_generator.generate_result_excel(
                original_data=df,
                field_results=field_results,
                record_evaluations=record_evaluations,
                summary=summary,
                original_filename=filename,
                original_file_content=file_content
            )
            
            logger.info(f"評估完成，處理時間: {processing_time:.2f}秒")
            
            return result_content, output_filename
            
        except (FileProcessingError, DataValidationError, EvaluationError, ExcelGenerationError):
            raise
        except Exception as e:
            logger.error(f"處理Excel檔案時發生錯誤: {str(e)}")
            raise EvaluationError(f"處理Excel檔案時發生未預期的錯誤: {str(e)}")
    
    def _read_excel_from_memory(self, file_content: bytes) -> Optional[pd.DataFrame]:
        """從記憶體讀取Excel檔案，智能偵測標題行"""
        try:
            # 嘗試不同的標題行位置，擴展到前5行
            for header_row in range(5):
                try:
                    file_buffer = io.BytesIO(file_content)
                    df = pd.read_excel(file_buffer, engine='openpyxl', header=header_row)

                    # 檢查是否有有意義的欄位名稱
                    meaningful_columns = 0
                    has_key_fields = False

                    for col in df.columns:
                        if isinstance(col, str) and not col.startswith('Unnamed'):
                            if any(keyword in str(col) for keyword in ['編號', '受編', '障礙', '類別', 'ICD', '備註', '證明', '手冊', '解答', 'LLM', '辨識']):
                                meaningful_columns += 1

                            # 特別檢查是否有關鍵欄位組合
                            if '編號' in str(col) and '受編' in str(df.columns):
                                has_key_fields = True

                    logger.info(f"嘗試第 {header_row} 行作為標題: 有意義欄位數 = {meaningful_columns}, 關鍵欄位 = {has_key_fields}")

                    # 如果有編號和受編欄位，且有足夠的有意義欄位，選擇這個
                    if has_key_fields and meaningful_columns >= 4:
                        logger.info(f"選擇第 {header_row} 行作為標題行（找到關鍵欄位組合）")
                        return df
                    elif meaningful_columns >= 6:  # 或者有很多有意義的欄位
                        logger.info(f"選擇第 {header_row} 行作為標題行（有意義欄位充足）")
                        return df

                except Exception as e:
                    logger.warning(f"第 {header_row} 行讀取失敗: {e}")
                    continue

            # 如果智能偵測失敗，嘗試使用xlrd引擎
            try:
                file_buffer = io.BytesIO(file_content)
                df = pd.read_excel(file_buffer, engine='xlrd')
                return df
            except Exception as e2:
                logger.error(f"使用xlrd引擎讀取失敗: {str(e2)}")
                raise FileProcessingError(f"無法讀取Excel檔案: {str(e2)}")

        except FileProcessingError:
            raise
        except Exception as e:
            logger.error(f"讀取Excel檔案失敗: {str(e)}")
            raise FileProcessingError(f"無法讀取Excel檔案: {str(e)}")
    
    def _validate_required_columns(self, df: pd.DataFrame) -> None:
        """驗證必要欄位是否存在，並嘗試智能映射"""
        # 首先嘗試智能映射欄位
        detected_mappings = self._detect_column_mappings(df)

        if detected_mappings:
            # 更新評估器的欄位映射
            self.evaluator.field_mappings = detected_mappings
            logger.info(f"智能映射成功: {detected_mappings}")
            return

        # 如果智能映射失敗，檢查原始欄位映射
        required_columns = []
        for field_name, (correct_col, predicted_col) in self.evaluator.field_mappings.items():
            required_columns.extend([correct_col, predicted_col])

        missing_columns = [col for col in required_columns if col not in df.columns]

        if missing_columns:
            available_columns = list(df.columns)
            raise DataValidationError(
                f"缺少必要欄位: {missing_columns}. 可用欄位: {available_columns}. "
                f"請確保Excel檔案包含正確答案和AI預測的欄位。",
                missing_columns=missing_columns
            )

        logger.info("欄位驗證通過")

    def _detect_column_mappings(self, df: pd.DataFrame) -> Optional[Dict[str, Tuple[str, str]]]:
        """智能偵測欄位映射關係"""
        columns = list(df.columns)
        logger.info(f"偵測到的欄位: {columns}")

        # 初始化映射字典
        mappings = {}

        # 尋找障礙等級欄位
        disability_level_cols = []
        for i, col in enumerate(columns):
            col_str = str(col).strip()
            if '障礙等級' in col_str or col_str == '障礙等級':
                disability_level_cols.append((i, col))

        # 尋找障礙類別欄位
        disability_category_cols = []
        for i, col in enumerate(columns):
            col_str = str(col).strip()
            if '障礙類別' in col_str or col_str == '障礙類別':
                disability_category_cols.append((i, col))

        # 尋找ICD診斷欄位
        icd_diagnosis_cols = []
        for i, col in enumerate(columns):
            col_str = str(col).strip()
            if 'ICD診斷' in col_str or col_str == 'ICD診斷' or 'ICD' in col_str or '診斷' in col_str:
                icd_diagnosis_cols.append((i, col))

        logger.info(f"障礙等級欄位: {disability_level_cols}")
        logger.info(f"障礙類別欄位: {disability_category_cols}")
        logger.info(f"ICD診斷欄位: {icd_diagnosis_cols}")

        # 根據位置判斷正面(正確答案)和反面(AI預測)
        # 假設正確答案在前面，AI預測在後面

        if len(disability_level_cols) >= 2:
            # 取前兩個障礙等級欄位，第一個是正確答案，第二個是AI預測
            correct_col = disability_level_cols[0][1]
            predicted_col = disability_level_cols[1][1]
            mappings['障礙等級'] = (correct_col, predicted_col)

        if len(disability_category_cols) >= 2:
            # 取前兩個障礙類別欄位
            correct_col = disability_category_cols[0][1]
            predicted_col = disability_category_cols[1][1]
            mappings['障礙類別'] = (correct_col, predicted_col)

        if len(icd_diagnosis_cols) >= 2:
            # 取前兩個ICD診斷欄位
            correct_col = icd_diagnosis_cols[0][1]
            predicted_col = icd_diagnosis_cols[1][1]
            mappings['ICD診斷'] = (correct_col, predicted_col)

        # 如果找到至少2個映射，認為偵測成功
        if len(mappings) >= 2:
            logger.info(f"智能映射成功: {mappings}")
            return mappings

        # 如果智能偵測失敗，嘗試基於位置的映射（針對您的資料格式）
        return self._detect_by_position(df)

    def _detect_by_position(self, df: pd.DataFrame) -> Optional[Dict[str, Tuple[str, str]]]:
        """基於位置偵測欄位映射（針對特定資料格式）"""
        columns = list(df.columns)

        # 檢查是否是"解答" vs "LLM辨識"格式
        if '解答' in columns and 'LLM辨識' in columns:
            logger.info("偵測到解答 vs LLM辨識格式")
            return self._detect_answer_llm_format(df)

        # 根據您提供的資料格式：
        # 編號(0), 受編(1), 障礙等級(2), 障礙類別(3), ICD診斷(4), 備註(5),
        # 障礙等級(6), 證明/手冊(7), 障礙類別(8), ICD診斷(9)

        if len(columns) >= 10:
            try:
                mappings = {
                    '障礙等級': (columns[2], columns[6]),    # 第3欄 vs 第7欄
                    '障礙類別': (columns[3], columns[8]),    # 第4欄 vs 第9欄
                    'ICD診斷': (columns[4], columns[9])     # 第5欄 vs 第10欄
                }

                logger.info(f"基於位置的映射: {mappings}")

                # 驗證這些欄位是否包含相關關鍵字
                valid_mappings = {}
                for field_name, (correct_col, predicted_col) in mappings.items():
                    if self._validate_column_content(df, correct_col, predicted_col, field_name):
                        valid_mappings[field_name] = (correct_col, predicted_col)

                if len(valid_mappings) >= 2:
                    return valid_mappings

            except IndexError:
                logger.warning("基於位置的映射失敗：欄位數量不足")

        return None

    def _detect_answer_llm_format(self, df: pd.DataFrame) -> Optional[Dict[str, Tuple[str, str]]]:
        """偵測解答 vs LLM辨識格式的欄位映射"""
        columns = list(df.columns)
        logger.info(f"解答 vs LLM辨識格式，欄位: {columns}")

        # 檢查是否有重複的欄位名稱（如：障礙等級、障礙類別、ICD診斷）
        # 這種情況下，pandas會自動加上.1後綴

        mappings = {}

        # 尋找重複欄位的模式
        for field_name in ['障礙等級', '障礙類別', 'ICD診斷']:
            correct_col = None
            predicted_col = None

            # 尋找原始欄位和帶.1後綴的欄位
            for col in columns:
                if str(col) == field_name:
                    correct_col = col
                elif str(col) == f"{field_name}.1":
                    predicted_col = col

            if correct_col and predicted_col:
                mappings[field_name] = (correct_col, predicted_col)
                logger.info(f"找到重複欄位映射: {field_name} -> ({correct_col}, {predicted_col})")
            elif correct_col and not predicted_col:
                logger.warning(f"找到正確欄位 {field_name} 但沒有找到對應的預測欄位 {field_name}.1")
            elif not correct_col and predicted_col:
                logger.warning(f"找到預測欄位 {field_name}.1 但沒有找到對應的正確欄位 {field_name}")

        # 如果找到足夠的映射，返回結果
        if len(mappings) >= 1:  # 降低要求，至少要有1個有效映射
            logger.info(f"成功偵測重複欄位映射: {mappings}")
            return mappings

        # 備用方案：基於位置的映射
        logger.info("嘗試基於位置的映射")

        # 根據調試結果，正確的映射應該是：
        # 編號(0), 受編(1), 障礙等級(2), 障礙類別(3), ICD診斷(4), 備註(5),
        # 障礙等級.1(6), 證明/手冊(7), 障礙類別.1(8), ICD診斷.1(9)

        if len(columns) >= 10:
            try:
                # 檢查是否有編號和受編欄位
                if '編號' in columns and '受編' in columns:
                    # 找到編號和受編的位置
                    id_idx = columns.index('編號')
                    subject_idx = columns.index('受編')

                    # 基於這些位置推斷其他欄位
                    if id_idx == 0 and subject_idx == 1:
                        mappings = {
                            '障礙等級': (columns[2], columns[6]),
                            '障礙類別': (columns[3], columns[8]),
                            'ICD診斷': (columns[4], columns[9])
                        }
                        logger.info(f"基於編號受編位置的映射: {mappings}")

                        # 驗證這些欄位是否存在
                        valid_mappings = {}
                        for field_name, (correct_col, predicted_col) in mappings.items():
                            if correct_col in columns and predicted_col in columns:
                                valid_mappings[field_name] = (correct_col, predicted_col)

                        if len(valid_mappings) >= 2:
                            return valid_mappings

            except Exception as e:
                logger.error(f"基於位置的映射失敗: {e}")

        logger.warning("無法偵測到有效的欄位映射")
        return None

    def _validate_column_content(self, df: pd.DataFrame, correct_col: str, predicted_col: str, field_name: str) -> bool:
        """驗證欄位內容是否符合預期"""
        try:
            # 檢查欄位是否有資料
            correct_data = df[correct_col].dropna()
            predicted_data = df[predicted_col].dropna()

            if len(correct_data) == 0 or len(predicted_data) == 0:
                return False

            # 根據欄位類型檢查內容
            if field_name == '障礙等級':
                # 檢查是否包含等級相關詞彙
                level_keywords = ['輕度', '中度', '重度', '極重度']
                correct_has_level = any(keyword in str(val) for val in correct_data for keyword in level_keywords)
                predicted_has_level = any(keyword in str(val) for val in predicted_data for keyword in level_keywords)
                return correct_has_level or predicted_has_level

            elif field_name == '障礙類別':
                # 檢查是否包含類別相關詞彙
                category_keywords = ['類', '其他', '第1類', '第2類', '第3類', '第4類', '第5類', '第6類', '第7類', '第8類']
                correct_has_category = any(keyword in str(val) for val in correct_data for keyword in category_keywords)
                predicted_has_category = any(keyword in str(val) for val in predicted_data for keyword in category_keywords)
                return correct_has_category or predicted_has_category

            elif field_name == 'ICD診斷':
                # 檢查是否包含ICD相關格式
                icd_patterns = ['【', '】', '[', ']', '換', '第']
                correct_has_icd = any(pattern in str(val) for val in correct_data for pattern in icd_patterns)
                predicted_has_icd = any(pattern in str(val) for val in predicted_data for pattern in icd_patterns)
                return correct_has_icd or predicted_has_icd

            return True

        except Exception as e:
            logger.warning(f"驗證欄位內容時發生錯誤: {e}")
            return False

    def _create_evaluation_summary(self,
                                 df: pd.DataFrame,
                                 field_results: Dict[str, EvaluationResult],
                                 record_evaluations: List[RecordEvaluation],
                                 overall_accuracy: float,
                                 processing_time: float) -> Dict:
        """建立評估摘要"""
        total_records = len(df)
        perfect_records = sum(1 for eval_result in record_evaluations 
                            if eval_result.matched_fields == eval_result.total_fields)
        
        field_accuracies = {
            field_name: result.accuracy 
            for field_name, result in field_results.items()
        }
        
        summary = {
            'total_records': total_records,
            'overall_accuracy': overall_accuracy,
            'field_accuracies': field_accuracies,
            'perfect_records': perfect_records,
            'processing_time': processing_time,
            'timestamp': datetime.now(),
            'field_statistics': self._calculate_field_statistics(record_evaluations),
            'accuracy_distribution': self._calculate_accuracy_distribution(record_evaluations)
        }
        
        return summary
    
    def _calculate_field_statistics(self, record_evaluations: List[RecordEvaluation]) -> Dict:
        """計算各欄位統計資訊"""
        if not record_evaluations:
            return {}
        
        field_names = list(record_evaluations[0].field_results.keys())
        field_stats = {}
        
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
            
            if accuracies:
                field_stats[field_name] = {
                    'average_accuracy': np.mean(accuracies),
                    'exact_matches': matches,
                    'total_records': total,
                    'match_rate': matches / total,
                    'min_accuracy': min(accuracies),
                    'max_accuracy': max(accuracies),
                    'std_accuracy': np.std(accuracies)
                }
        
        return field_stats
    
    def _calculate_accuracy_distribution(self, record_evaluations: List[RecordEvaluation]) -> Dict:
        """計算準確度分佈"""
        if not record_evaluations:
            return {}
        
        accuracies = [eval_result.overall_accuracy for eval_result in record_evaluations]
        
        # 定義準確度區間
        ranges = {
            'excellent': (0.9, 1.0),    # 優秀: 90-100%
            'good': (0.7, 0.9),         # 良好: 70-90%
            'fair': (0.5, 0.7),         # 普通: 50-70%
            'poor': (0.0, 0.5)          # 需改進: 0-50%
        }
        
        distribution = {}
        total_records = len(accuracies)
        
        for category, (min_acc, max_acc) in ranges.items():
            count = sum(1 for acc in accuracies if min_acc <= acc < max_acc)
            # 處理最高區間的邊界情況
            if category == 'excellent':
                count = sum(1 for acc in accuracies if min_acc <= acc <= max_acc)
            
            distribution[category] = {
                'count': count,
                'percentage': count / total_records if total_records > 0 else 0
            }
        
        return distribution
    
    def _generate_output_filename(self, original_filename: str) -> str:
        """生成輸出檔案名稱"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = original_filename.rsplit('.', 1)[0] if '.' in original_filename else original_filename

        # Ensure the filename is safe for different systems
        # Remove or replace problematic characters
        safe_base_name = base_name.replace('[', '').replace(']', '').replace('/', '_').replace('\\', '_')

        return f"{safe_base_name}_accuracy_evaluation_{timestamp}.xlsx"
    
    async def validate_file_format(self, filename: str) -> bool:
        """驗證檔案格式"""
        allowed_extensions = ['.xlsx', '.xls']
        return any(filename.lower().endswith(ext) for ext in allowed_extensions)
    
    async def get_sample_data(self) -> pd.DataFrame:
        """取得範例資料"""
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
