#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外來函文資料評估服務
Document Data Evaluator Service
"""

import pandas as pd
import numpy as np
import io
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import re

from .document_evaluator_core import DocumentDataEvaluator
from .document_excel_generator import DocumentExcelGenerator
from .exceptions import FileValidationError, FileProcessingError, DataValidationError, EvaluationError

logger = logging.getLogger(__name__)

class DocumentEvaluatorService:
    """外來函文評估服務類"""
    
    def __init__(self):
        """初始化外來函文評估服務"""
        self.evaluator = DocumentDataEvaluator()
        self.excel_generator = DocumentExcelGenerator()
    
    async def validate_file_format(self, filename: str) -> bool:
        """驗證檔案格式"""
        if not filename:
            return False
        return filename.lower().endswith(('.xlsx', '.xls'))
    
    def parse_model_columns(self, df: pd.DataFrame) -> Dict[str, Dict[str, int]]:
        """
        解析模型欄位映射
        
        Returns:
            {
                'model_name': {
                    'ai_col': column_index,
                    'human_col': column_index
                }
            }
        """
        model_mappings = {}
        
        # 讀取第一行作為模型標題行
        header_row = df.iloc[0]
        
        logger.info(f"解析模型欄位，標題行內容: {header_row.to_dict()}")
        
        # 跳過第一欄（案件號）
        col_idx = 1
        while col_idx < len(header_row):
            model_name = header_row.iloc[col_idx]
            
            # 檢查是否為有效的模型名稱
            if pd.notna(model_name) and str(model_name).strip():
                model_name = str(model_name).strip()
                
                # 確保下一欄是人工標記（假設AI欄位後面緊跟人工欄位）
                if col_idx + 1 < len(header_row):
                    next_col = header_row.iloc[col_idx + 1]
                    
                    # 檢查是否為人工標記欄位（可能是空值或'人工'等標記）
                    if pd.isna(next_col) or str(next_col).strip() in ['', '人工', 'human', 'manual']:
                        model_mappings[model_name] = {
                            'ai_col': col_idx,
                            'human_col': col_idx + 1
                        }
                        logger.info(f"找到模型: {model_name}, AI欄位: {col_idx}, 人工欄位: {col_idx + 1}")
                        col_idx += 2  # 跳過這兩欄
                    else:
                        col_idx += 1
                else:
                    col_idx += 1
            else:
                col_idx += 1
        
        logger.info(f"總共找到 {len(model_mappings)} 個模型")
        return model_mappings
    
    def extract_field_mappings(self, df: pd.DataFrame) -> Dict[str, Tuple[int, str]]:
        """
        提取欄位映射關係
        
        Returns:
            {
                'field_name': (row_index, field_description)
            }
        """
        field_mappings = {}
        
        # 檢查第2行是否為欄位名稱行（第1行通常是模型名稱）
        if len(df) >= 2:
            second_row = df.iloc[1]
            first_col_value = second_row.iloc[0]
            
            # 如果第2行第1欄是"案件號"，說明第2行是欄位名稱行
            if pd.notna(first_col_value) and str(first_col_value).strip() in ['案件號', '案例編號', 'ID']:
                logger.info("發現第2行為欄位名稱行")
                
                # 使用第2行的欄位名稱，但忽略"人工"等標記欄位
                for col_idx, field_value in enumerate(second_row):
                    if pd.notna(field_value) and str(field_value).strip():
                        field_name = str(field_value).strip()
                        
                        # 只保留實際的欄位名稱，跳過"人工"標記
                        if field_name not in ['人工', 'human', 'manual', 'Human', 'Manual']:
                            field_mappings[field_name] = (col_idx, field_name)
                            logger.info(f"找到欄位: {field_name} 在欄位 {col_idx}")
                
                return field_mappings
        
        # 如果沒有找到標準格式，嘗試原來的方法（從第二行開始查找欄位名稱）
        logger.info("使用原始方法解析欄位映射")
        
        # 從第二行開始查找欄位名稱（第一行是模型名稱）
        for row_idx in range(1, min(len(df), 10)):  # 只檢查前10行
            first_col_value = df.iloc[row_idx, 0]
            
            if pd.notna(first_col_value) and str(first_col_value).strip():
                field_name = str(first_col_value).strip()
                
                # 跳過案件號等非欄位內容
                if not field_name.startswith('99099') and field_name not in ['案件號', 'MODEL']:
                    field_mappings[field_name] = (row_idx, field_name)
                    logger.info(f"找到欄位: {field_name} 在第 {row_idx} 行")
        
        return field_mappings
    
    def extract_model_data(
        self,
        df: pd.DataFrame,
        model_mappings: Dict[str, Dict[str, int]],
        field_mappings: Dict[str, Tuple[int, str]]
    ) -> Dict[str, pd.DataFrame]:
        """
        提取每個模型的資料
        
        Returns:
            {
                'model_name': DataFrame with columns ['field_name', 'ai_value', 'human_value']
            }
        """
        model_data = {}
        
        for model_name, col_info in model_mappings.items():
            ai_col = col_info['ai_col']
            human_col = col_info['human_col']
            
            records = []
            
            # 提取每個欄位的資料
            for field_name, (row_idx, _) in field_mappings.items():
                ai_value = df.iloc[row_idx, ai_col] if ai_col < len(df.columns) else None
                human_value = df.iloc[row_idx, human_col] if human_col < len(df.columns) else None
                
                records.append({
                    'field_name': field_name,
                    'ai_value': ai_value,
                    'human_value': human_value,
                    'row_index': row_idx
                })
            
            model_df = pd.DataFrame(records)
            model_data[model_name] = model_df
            
            logger.info(f"模型 {model_name} 提取了 {len(records)} 個欄位的資料")
        
        return model_data
    
    def evaluate_model_data(self, model_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        評估所有模型的資料
        
        Returns:
            {
                'model_name': {
                    'field_results': {...},
                    'accuracy_stats': {...}
                }
            }
        """
        all_evaluations = {}
        
        for model_name, model_df in model_data.items():
            logger.info(f"開始評估模型: {model_name}")
            
            field_results = {}
            correct_count = 0
            total_count = 0
            
            for _, row in model_df.iterrows():
                field_name = row['field_name']
                ai_value = row['ai_value']
                human_value = row['human_value']
                
                # 只評估有資料的欄位
                if pd.notna(human_value) or pd.notna(ai_value):
                    total_count += 1
                    
                    # 使用評估器進行比對
                    field_result = self.evaluator.evaluate_single_field(
                        correct_value=human_value,
                        predicted_value=ai_value,
                        field_name=field_name
                    )
                    
                    field_results[field_name] = {
                        'correct_value': str(human_value) if pd.notna(human_value) else '',
                        'predicted_value': str(ai_value) if pd.notna(ai_value) else '',
                        'similarity': field_result.similarity,
                        'cer': field_result.cer,
                        'wer': field_result.wer,
                        'is_exact_match': field_result.is_exact_match,
                        'field_type': field_result.field_type.value,
                        'error_description': field_result.error_description
                    }
                    
                    if field_result.is_exact_match:
                        correct_count += 1
            
            # 計算準確度統計
            accuracy_stats = {
                'total_fields': total_count,
                'correct_fields': correct_count,
                'accuracy_rate': correct_count / total_count if total_count > 0 else 0.0,
                'field_results': field_results
            }
            
            all_evaluations[model_name] = accuracy_stats
            
            logger.info(f"模型 {model_name} 評估完成: {correct_count}/{total_count} = {accuracy_stats['accuracy_rate']:.2%}")
        
        return all_evaluations
    
    async def process_document_file(
        self,
        file_content: bytes,
        filename: str,
        value_set_id: str = None
    ) -> Tuple[bytes, str]:
        """
        處理外來函文檔案並返回評估結果
        
        Args:
            file_content: 檔案內容
            filename: 檔案名稱
            
        Returns:
            (result_content, output_filename)
        """
        try:
            logger.info(f"開始處理外來函文檔案: {filename}")
            
            # 讀取Excel檔案
            df = pd.read_excel(io.BytesIO(file_content), header=None)
            
            if df is None or df.empty:
                raise FileProcessingError("無法讀取Excel檔案或檔案為空", filename)
            
            logger.info(f"成功讀取檔案，資料形狀: {df.shape}")
            
            # 解析外來函文的水平格式資料
            evaluation_results = self.parse_horizontal_document_data(df)
            
            if not evaluation_results['field_evaluations']:
                raise DataValidationError("未找到有效的欄位評估資料", [])
            
            # 生成Excel結果檔案
            result_content = await self.excel_generator.generate_document_evaluation_report(
                original_data=df,
                evaluation_results=evaluation_results,
                original_filename=filename,
                value_set_id=value_set_id
            )
            
            # 生成輸出檔案名稱
            base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
            output_filename = f"{base_name}_外來函文評估結果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            logger.info(f"外來函文評估完成，評估了 {len(evaluation_results['field_evaluations'])} 個欄位")
            
            return result_content, output_filename
            
        except Exception as e:
            logger.error(f"處理外來函文檔案時發生錯誤: {str(e)}")
            raise EvaluationError(f"處理外來函文檔案失敗: {str(e)}")
    
    def parse_horizontal_document_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        解析外來函文的水平格式資料
        
        外來函文格式:
        - 第1行: 模型名稱
        - 第2行: 欄位名稱 
        - 第3行開始: 案件資料
        - 每個模型負責不同欄位，每個欄位有AI預測+人工標記
        
        Returns:
            {
                'field_evaluations': {
                    'field_name': {
                        'model_name': str,
                        'ai_column': int,
                        'human_column': int,
                        'total_cases': int,
                        'correct_cases': int,
                        'accuracy_rate': float,
                        'case_results': [...]
                    }
                },
                'summary': {...}
            }
        """
        try:
            if len(df) < 3:
                raise DataValidationError("資料不足，至少需要3行（模型名稱、欄位名稱、資料）", [])
            
            model_row = df.iloc[0]  # 第1行：模型名稱
            field_row = df.iloc[1]  # 第2行：欄位名稱
            data_rows = df.iloc[2:]  # 第3行開始：案件資料
            
            logger.info(f"解析水平格式資料：{len(data_rows)} 個案件")
            
            field_evaluations = {}
            current_model = None
            ai_column = None
            
            # 遍歷所有欄位
            for col_idx in range(len(field_row)):
                model_name = model_row.iloc[col_idx]
                field_name = field_row.iloc[col_idx]
                
                # 更新當前模型
                if pd.notna(model_name) and str(model_name).strip() and str(model_name).strip() != 'MODEL':
                    current_model = str(model_name).strip()
                    ai_column = col_idx
                    logger.info(f"發現模型 '{current_model}' 於欄位 {col_idx}")
                
                # 處理欄位名稱
                if pd.notna(field_name) and str(field_name).strip():
                    field_str = str(field_name).strip()
                    
                    # 如果是"人工"標記，表示這是人工標記欄位
                    if field_str in ['人工', 'human', 'manual', 'Human', 'Manual']:
                        if current_model and ai_column is not None:
                            # 找到對應的AI欄位名稱
                            ai_field_name = None
                            if ai_column < len(field_row):
                                prev_field = field_row.iloc[ai_column]
                                if pd.notna(prev_field) and str(prev_field).strip() not in ['人工', 'human', 'manual']:
                                    ai_field_name = str(prev_field).strip()
                            
                            if ai_field_name and ai_field_name not in ['案件號', '債務人ID']:
                                # 評估這個欄位
                                field_eval = self.evaluate_field_data(
                                    data_rows, ai_column, col_idx, ai_field_name, current_model
                                )
                                field_evaluations[f"{ai_field_name}_{current_model}"] = field_eval
                                logger.info(f"評估欄位 '{ai_field_name}' (模型: {current_model})")
                    
                    # 如果不是人工標記，更新AI欄位位置
                    elif current_model and field_str not in ['案件號', '債務人ID']:
                        ai_column = col_idx
            
            # 計算總體統計
            total_evaluations = len(field_evaluations)
            total_accuracy = 0.0
            if total_evaluations > 0:
                total_accuracy = sum(eval_data['accuracy_rate'] for eval_data in field_evaluations.values()) / total_evaluations
            
            summary = {
                'total_fields': total_evaluations,
                'total_cases': len(data_rows),
                'overall_accuracy': total_accuracy,
                'processing_time': datetime.now().isoformat()
            }
            
            return {
                'field_evaluations': field_evaluations,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"解析外來函文資料時發生錯誤: {str(e)}")
            raise DataValidationError(f"解析外來函文資料失敗: {str(e)}", [])
    
    def evaluate_field_data(
        self,
        data_rows: pd.DataFrame,
        ai_col: int,
        human_col: int,
        field_name: str,
        model_name: str
    ) -> Dict[str, Any]:
        """評估單一欄位的資料"""
        case_results = []
        correct_count = 0
        total_count = 0
        
        for idx, row in data_rows.iterrows():
            ai_value = row.iloc[ai_col] if ai_col < len(row) else None
            human_value = row.iloc[human_col] if human_col < len(row) else None
            case_id = row.iloc[0] if len(row) > 0 else f"案件_{idx}"
            
            # 只評估有資料的案件
            if pd.notna(human_value) or pd.notna(ai_value):
                total_count += 1
                
                # 使用評估器進行比對
                field_result = self.evaluator.evaluate_single_field(
                    correct_value=human_value,
                    predicted_value=ai_value,
                    field_name=field_name
                )
                
                case_result = {
                    'case_id': str(case_id),
                    'ai_value': str(ai_value) if pd.notna(ai_value) else '',
                    'human_value': str(human_value) if pd.notna(human_value) else '',
                    'is_correct': field_result.is_exact_match,
                    'similarity': field_result.similarity,
                    'cer': field_result.cer,
                    'wer': field_result.wer
                }
                case_results.append(case_result)
                
                if field_result.is_exact_match:
                    correct_count += 1
        
        accuracy_rate = correct_count / total_count if total_count > 0 else 0.0
        
        return {
            'model_name': model_name,
            'ai_column': ai_col,
            'human_column': human_col,
            'total_cases': total_count,
            'correct_cases': correct_count,
            'accuracy_rate': accuracy_rate,
            'case_results': case_results
        }
