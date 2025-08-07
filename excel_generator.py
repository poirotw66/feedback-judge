#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Excel Result Generator for Disability Certificate AI Test Results
身心障礙手冊AI測試結果準確度評分系統 - Excel結果生成器
"""

import pandas as pd
import numpy as np
import io
from typing import Dict, List, Any
import logging
from datetime import datetime

from evaluator_core import EvaluationResult, RecordEvaluation
from exceptions import ExcelGenerationError

logger = logging.getLogger(__name__)

class ExcelResultGenerator:
    """Excel結果生成器"""
    
    def __init__(self):
        pass
    
    async def generate_result_excel(self,
                                  original_data: pd.DataFrame,
                                  field_results: Dict[str, EvaluationResult],
                                  record_evaluations: List[RecordEvaluation],
                                  summary: Dict) -> bytes:
        """
        生成包含評估結果的Excel檔案
        
        Args:
            original_data: 原始資料
            field_results: 欄位評估結果
            record_evaluations: 記錄評估結果
            summary: 評估摘要
            
        Returns:
            bytes: Excel檔案內容
        """
        try:
            # 驗證輸入數據
            if not record_evaluations:
                raise ValueError("記錄評估結果為空")
            if not field_results:
                raise ValueError("欄位評估結果為空")

            output = io.BytesIO()
            logger.info("開始生成Excel檔案...")

            # Use openpyxl engine for Chinese characters support
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                try:
                    # 1. Individual Record Analysis Sheet (NEW - Primary detailed breakdown)
                    logger.info("生成個別記錄分析工作表...")
                    self._create_individual_record_analysis_sheet(writer, record_evaluations)

                    # 2. Field-by-Field Summary Sheet (NEW - Field accuracy summary)
                    logger.info("生成欄位準確度摘要工作表...")
                    self._create_field_summary_sheet(writer, field_results, record_evaluations)

                    # 3. 評估摘要頁 (Overall summary)
                    logger.info("生成評估摘要工作表...")
                    self._create_summary_sheet(writer, summary, field_results)

                    # 4. 記錄摘要頁 (Record summary)
                    logger.info("生成記錄摘要工作表...")
                    self._create_record_summary_sheet(writer, record_evaluations)

                    # 5. 詳細欄位比較頁 (Detailed comparison)
                    logger.info("生成詳細欄位比較工作表...")
                    self._create_detailed_comparison_sheet(writer, record_evaluations)

                    # 6. 錯誤分析頁 (Error analysis)
                    logger.info("生成錯誤分析工作表...")
                    self._create_error_analysis_sheet(writer, record_evaluations)

                    # 7. 原始資料頁 (Original data)
                    logger.info("生成原始資料工作表...")
                    self._create_original_data_sheet(writer, original_data)

                except Exception as sheet_error:
                    logger.error(f"生成工作表時發生錯誤: {sheet_error}")
                    # 至少創建一個基本的錯誤報告工作表
                    error_df = pd.DataFrame({
                        '錯誤報告': [f'Excel生成過程中發生錯誤: {str(sheet_error)}'],
                        '時間': [datetime.now().strftime('%Y-%m-%d %H:%M:%S')]
                    })
                    error_df.to_excel(writer, sheet_name='錯誤報告', index=False)

            output.seek(0)
            result = output.read()

            # 驗證生成的檔案不為空
            if len(result) == 0:
                raise ValueError("生成的Excel檔案為空")

            logger.info(f"Excel檔案生成成功，大小: {len(result)} bytes")
            return result

        except Exception as e:
            logger.error(f"生成Excel檔案時發生錯誤: {str(e)}")
            raise ExcelGenerationError(f"生成Excel檔案時發生錯誤: {str(e)}")

    def _create_individual_record_analysis_sheet(self, writer: pd.ExcelWriter, record_evaluations: List[RecordEvaluation]):
        """建立個別記錄分析頁 - 詳細的逐筆記錄分析"""
        analysis_data = []

        for evaluation in record_evaluations:
            # 為每個受編添加標題行
            analysis_data.append({
                '受編': str(evaluation.subject_id) if evaluation.subject_id is not None else '',
                '欄位': '=== 記錄開始 ===',
                '正解': '',
                '模型識別結果': '',
                '準確度': '',
                '狀態': f"整體準確度: {evaluation.overall_accuracy:.1%}",
                '備註': f"完全匹配: {evaluation.matched_fields}/{evaluation.total_fields}"
            })

            # 添加每個欄位的詳細資訊
            for field_name, field_result in evaluation.field_results.items():
                accuracy_percentage = f"{field_result.similarity:.1%}"
                status = "完全匹配" if field_result.is_exact_match else "不匹配" if field_result.similarity < 0.5 else "部分匹配"

                # 安全處理值，確保不會有None或NaN
                correct_value = str(field_result.correct_value) if field_result.correct_value is not None else ''
                predicted_value = str(field_result.predicted_value) if field_result.predicted_value is not None else ''

                # 清理可能導致Excel問題的字符
                correct_value = self._clean_excel_value(correct_value)
                predicted_value = self._clean_excel_value(predicted_value)

                analysis_data.append({
                    '受編': '',  # 空白，避免重複顯示
                    '欄位': str(field_name),
                    '正解': correct_value,
                    '模型識別結果': predicted_value,
                    '準確度': accuracy_percentage,
                    '狀態': status,
                    '備註': self._get_improvement_suggestion(field_result) if not field_result.is_exact_match else '正確'
                })

            # 添加分隔行
            analysis_data.append({
                '受編': '',
                '欄位': '--- 分隔線 ---',
                '正解': '',
                '模型識別結果': '',
                '準確度': '',
                '狀態': '',
                '備註': ''
            })

        analysis_df = pd.DataFrame(analysis_data)
        self._safe_dataframe_to_excel(analysis_df, writer, '個別記錄分析')

    def _create_field_summary_sheet(self, writer: pd.ExcelWriter, field_results: Dict[str, EvaluationResult], record_evaluations: List[RecordEvaluation]):
        """建立欄位摘要頁 - 各欄位的整體準確度統計"""
        summary_data = []

        # 計算各欄位的詳細統計
        for field_name, result in field_results.items():
            # 從record_evaluations中收集該欄位的所有結果
            field_accuracies = []
            exact_matches = 0
            total_records = 0

            for evaluation in record_evaluations:
                if field_name in evaluation.field_results:
                    field_result = evaluation.field_results[field_name]
                    field_accuracies.append(field_result.similarity)
                    if field_result.is_exact_match:
                        exact_matches += 1
                    total_records += 1

            if field_accuracies:
                avg_accuracy = sum(field_accuracies) / len(field_accuracies)
                min_accuracy = min(field_accuracies)
                max_accuracy = max(field_accuracies)
                match_rate = exact_matches / total_records if total_records > 0 else 0

                summary_data.append({
                    '欄位名稱': field_name,
                    '整體準確度': f"{avg_accuracy:.2%}",
                    '完全匹配數': exact_matches,
                    '總記錄數': total_records,
                    '完全匹配率': f"{match_rate:.1%}",
                    '最高準確度': f"{max_accuracy:.1%}",
                    '最低準確度': f"{min_accuracy:.1%}",
                    '表現等級': self._get_performance_level(avg_accuracy),
                    '需改進記錄數': total_records - exact_matches,
                    '改進建議': self._get_field_improvement_suggestion(avg_accuracy, match_rate)
                })

        summary_df = pd.DataFrame(summary_data)
        self._safe_dataframe_to_excel(summary_df, writer, '欄位準確度摘要')

    def _create_summary_sheet(self, writer: pd.ExcelWriter, summary: Dict, field_results: Dict[str, EvaluationResult]):
        """建立評估摘要頁"""
        summary_data = []
        
        # 整體統計
        summary_data.append(['項目', '數值', '說明'])
        summary_data.append(['總記錄數', summary.get('total_records', 0), '處理的總記錄數量'])
        summary_data.append(['整體準確度', f"{summary.get('overall_accuracy', 0):.2%}", '加權平均準確度'])
        summary_data.append(['完全正確記錄', summary.get('perfect_records', 0), '所有欄位都完全匹配的記錄數'])
        summary_data.append(['處理時間', f"{summary.get('processing_time', 0):.2f}秒", '檔案處理耗時'])
        summary_data.append(['處理時間戳', summary.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S'), '處理完成時間'])
        summary_data.append(['', '', ''])  # 空行
        
        # 各欄位準確度
        summary_data.append(['欄位名稱', '準確度', '完全匹配率'])
        for field_name, result in field_results.items():
            match_rate = result.exact_matches / result.total_records if result.total_records > 0 else 0
            summary_data.append([field_name, f"{result.accuracy:.2%}", f"{match_rate:.1%}"])
        
        summary_df = pd.DataFrame(summary_data)
        self._safe_dataframe_to_excel(summary_df, writer, '評估摘要', header=False)
    
    def _create_record_summary_sheet(self, writer: pd.ExcelWriter, record_evaluations: List[RecordEvaluation]):
        """建立記錄摘要頁"""
        summary_data = []
        
        for evaluation in record_evaluations:
            summary_data.append({
                '編號': evaluation.record_id,
                '受編': evaluation.subject_id,
                '整體準確度': f"{evaluation.overall_accuracy:.2%}",
                '完全匹配欄位數': evaluation.matched_fields,
                '總欄位數': evaluation.total_fields,
                '匹配率': f"{evaluation.matched_fields/evaluation.total_fields:.1%}" if evaluation.total_fields > 0 else "0%",
                '狀態描述': f"({evaluation.matched_fields}/{evaluation.total_fields} 完全匹配)",
                '表現等級': self._get_performance_level(evaluation.overall_accuracy)
            })
        
        summary_df = pd.DataFrame(summary_data)
        self._safe_dataframe_to_excel(summary_df, writer, '記錄摘要')
    
    def _create_detailed_comparison_sheet(self, writer: pd.ExcelWriter, record_evaluations: List[RecordEvaluation]):
        """建立詳細欄位比較頁"""
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
                    '差異描述': '完全相同' if field_result.is_exact_match else f"相似度: {field_result.similarity:.1%}",
                    '改進建議': self._get_improvement_suggestion(field_result)
                })
        
        detailed_df = pd.DataFrame(detailed_data)
        self._safe_dataframe_to_excel(detailed_df, writer, '詳細欄位比較')
    
    def _create_field_statistics_sheet(self, writer: pd.ExcelWriter, field_statistics: Dict):
        """建立各欄位統計頁"""
        if not field_statistics:
            return
        
        stats_data = []
        
        for field_name, stats in field_statistics.items():
            stats_data.append({
                '欄位名稱': field_name,
                '平均準確度': f"{stats.get('average_accuracy', 0):.2%}",
                '完全匹配數': stats.get('exact_matches', 0),
                '總記錄數': stats.get('total_records', 0),
                '匹配率': f"{stats.get('match_rate', 0):.1%}",
                '最低準確度': f"{stats.get('min_accuracy', 0):.2%}",
                '最高準確度': f"{stats.get('max_accuracy', 0):.2%}",
                '標準差': f"{stats.get('std_accuracy', 0):.3f}",
                '需改進記錄數': stats.get('total_records', 0) - stats.get('exact_matches', 0),
                '表現等級': self._get_performance_level(stats.get('average_accuracy', 0))
            })
        
        stats_df = pd.DataFrame(stats_data)
        stats_df.to_excel(writer, sheet_name='欄位統計', index=False)
    
    def _create_error_analysis_sheet(self, writer: pd.ExcelWriter, record_evaluations: List[RecordEvaluation]):
        """建立錯誤分析頁"""
        error_data = []
        
        for evaluation in record_evaluations:
            for field_name, field_result in evaluation.field_results.items():
                if not field_result.is_exact_match:
                    error_type = self._classify_error_type(field_result.similarity)
                    
                    error_data.append({
                        '編號': field_result.record_id,
                        '受編': field_result.subject_id,
                        '欄位': field_name,
                        '錯誤類型': error_type,
                        '相似度': f"{field_result.similarity:.1%}",
                        '正確值': field_result.correct_value,
                        '預測值': field_result.predicted_value,
                        '改進建議': self._get_improvement_suggestion(field_result),
                        '優先級': self._get_error_priority(field_result.similarity)
                    })
        
        if error_data:
            error_df = pd.DataFrame(error_data)
            self._safe_dataframe_to_excel(error_df, writer, '錯誤分析')
    
    def _create_original_data_sheet(self, writer: pd.ExcelWriter, original_data: pd.DataFrame):
        """建立原始資料頁"""
        self._safe_dataframe_to_excel(original_data, writer, '原始資料')
    
    def _create_accuracy_distribution_sheet(self, writer: pd.ExcelWriter, accuracy_distribution: Dict):
        """建立準確度分佈頁"""
        if not accuracy_distribution:
            return
        
        distribution_data = []
        
        for category, data in accuracy_distribution.items():
            category_name = {
                'excellent': '優秀 (90-100%)',
                'good': '良好 (70-90%)',
                'fair': '普通 (50-70%)',
                'poor': '需改進 (0-50%)'
            }.get(category, category)
            
            distribution_data.append({
                '準確度等級': category_name,
                '記錄數': data.get('count', 0),
                '百分比': f"{data.get('percentage', 0):.1%}",
                '說明': self._get_category_description(category)
            })
        
        distribution_df = pd.DataFrame(distribution_data)
        distribution_df.to_excel(writer, sheet_name='準確度分佈', index=False)
    
    def _get_performance_level(self, accuracy: float) -> str:
        """取得表現等級"""
        if accuracy >= 0.9:
            return '優秀'
        elif accuracy >= 0.7:
            return '良好'
        elif accuracy >= 0.5:
            return '普通'
        else:
            return '需改進'
    
    def _classify_error_type(self, similarity: float) -> str:
        """分類錯誤類型"""
        if similarity > 0.7:
            return '格式差異'
        elif similarity > 0.3:
            return '內容錯誤'
        else:
            return '完全不符'
    
    def _get_improvement_suggestion(self, field_result) -> str:
        """取得改進建議"""
        if field_result.similarity > 0.8:
            return "格式標準化 - 相似度高，主要是格式問題"
        elif field_result.similarity > 0.5:
            return "內容檢查 - 部分正確，需要細節調整"
        elif field_result.similarity > 0.2:
            return "重新訓練 - 識別錯誤，需要加強相關資料訓練"
        else:
            return "完全重做 - 識別失敗，需要重新處理或手動檢查"
    
    def _get_error_priority(self, similarity: float) -> str:
        """取得錯誤優先級"""
        if similarity < 0.3:
            return '高'
        elif similarity < 0.7:
            return '中'
        else:
            return '低'
    
    def _get_category_description(self, category: str) -> str:
        """取得類別描述"""
        descriptions = {
            'excellent': 'AI識別表現優異，準確度很高',
            'good': 'AI識別表現良好，有少量錯誤',
            'fair': 'AI識別表現普通，需要改進',
            'poor': 'AI識別表現不佳，需要重新訓練'
        }
        return descriptions.get(category, '')

    def _get_field_improvement_suggestion(self, avg_accuracy: float, match_rate: float) -> str:
        """為欄位提供改進建議"""
        if avg_accuracy >= 0.9 and match_rate >= 0.8:
            return "表現優異，維持現有訓練方式"
        elif avg_accuracy >= 0.7:
            return "表現良好，可針對錯誤案例加強訓練"
        elif avg_accuracy >= 0.5:
            return "需要改進，建議增加訓練資料並調整模型參數"
        else:
            return "表現不佳，需要重新檢視訓練資料和模型架構"

    def _clean_excel_value(self, value: str) -> str:
        """清理Excel值，移除可能導致問題的字符"""
        if not value or value == 'nan':
            return ''

        # 轉換為字符串
        value = str(value)

        # 移除或替換可能導致Excel問題的字符
        # 移除控制字符
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\t\n\r')

        # 限制長度，避免Excel單元格過長
        if len(value) > 32767:  # Excel單元格最大字符數
            value = value[:32760] + "..."

        return value

    def _safe_dataframe_to_excel(self, df: pd.DataFrame, writer: pd.ExcelWriter, sheet_name: str, header: bool = True):
        """安全地將DataFrame寫入Excel"""
        try:
            # 清理DataFrame中的所有值
            cleaned_df = df.copy()

            for col in cleaned_df.columns:
                if cleaned_df[col].dtype == 'object':
                    cleaned_df[col] = cleaned_df[col].apply(
                        lambda x: self._clean_excel_value(str(x)) if x is not None else ''
                    )
                else:
                    # 處理數值列中的NaN
                    cleaned_df[col] = cleaned_df[col].fillna('')

            # 確保工作表名稱有效
            safe_sheet_name = self._clean_sheet_name(sheet_name)

            cleaned_df.to_excel(writer, sheet_name=safe_sheet_name, index=False, header=header)

        except Exception as e:
            logger.error(f"寫入工作表 {sheet_name} 時發生錯誤: {e}")
            # 創建一個簡單的錯誤工作表
            error_df = pd.DataFrame({'錯誤': [f'無法生成 {sheet_name} 工作表: {str(e)}']})
            safe_error_name = self._clean_sheet_name(f'錯誤_{sheet_name[:10]}')
            error_df.to_excel(writer, sheet_name=safe_error_name, index=False)

    def _clean_sheet_name(self, name: str) -> str:
        """清理工作表名稱"""
        # Excel工作表名稱限制
        invalid_chars = ['\\', '/', '*', '?', ':', '[', ']']
        for char in invalid_chars:
            name = name.replace(char, '_')

        # 限制長度（Excel限制31字符）
        if len(name) > 31:
            name = name[:28] + "..."

        return name
