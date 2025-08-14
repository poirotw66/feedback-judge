#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
外來函文Excel報告生成器
Document Excel Generator
"""

import pandas as pd
import numpy as np
import io
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows

logger = logging.getLogger(__name__)

class DocumentExcelGenerator:
    """外來函文Excel報告生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.title_font = Font(name='Arial', size=14, bold=True)
        self.header_font = Font(name='Arial', size=12, bold=True, color="FFFFFF")
        self.content_font = Font(name='Arial', size=10)
        
        self.header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        self.correct_fill = PatternFill(start_color="70AD47", end_color="70AD47", fill_type="solid")
        self.incorrect_fill = PatternFill(start_color="FF6B6B", end_color="FF6B6B", fill_type="solid")
        
        self.center_alignment = Alignment(horizontal='center', vertical='center')
        self.thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
    
    async def generate_document_evaluation_report(
        self,
        original_data: pd.DataFrame,
        evaluation_results: Dict[str, Any],
        original_filename: str,
        value_set_id: str = None
    ) -> bytes:
        """
        生成外來函文評估報告（按模型分組格式）
        
        Args:
            original_data: 原始資料
            evaluation_results: 評估結果
            original_filename: 原始檔案名稱
            value_set_id: valueSetId 值
            
        Returns:
            bytes: Excel檔案內容
        """
        try:
            logger.info("開始生成外來函文評估報告（按模型分組）")
            
            # 創建工作簿
            wb = Workbook()
            
            # 移除預設工作表
            wb.remove(wb.active)
            
            # 重新組織資料按模型分組
            model_grouped_data = self._reorganize_data_by_model(evaluation_results)
            
            # 為每個模型創建工作表
            for model_name, model_data in model_grouped_data.items():
                self._create_model_evaluation_sheet(wb, model_name, model_data, original_data, value_set_id)
            
            # 保存到記憶體
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            
            logger.info("外來函文評估報告生成完成")
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"生成外來函文評估報告時發生錯誤: {str(e)}")
            raise
    
    def _reorganize_data_by_model(self, evaluation_results: Dict[str, Any]) -> Dict[str, Dict]:
        """
        重新組織資料按模型分組
        
        Returns:
            {
                'model_name': {
                    'fields': ['field1', 'field2', ...],
                    'cases': {
                        'case_id': {
                            'field1': {'accuracy': 1.0, 'cer': 0.0, 'wer': 0.0, 'ai_value': '...', 'human_value': '...'},
                            'field2': {...}
                        }
                    }
                }
            }
        """
        model_data = {}
        field_evaluations = evaluation_results.get('field_evaluations', {})
        
        # 分析每個欄位屬於哪個模型
        for field_key, field_result in field_evaluations.items():
            model_name = field_result.get('model_name', 'Unknown')
            field_name = field_key.replace(f'_{model_name}', '') if f'_{model_name}' in field_key else field_key
            
            if model_name not in model_data:
                model_data[model_name] = {
                    'fields': [],
                    'cases': {}
                }
            
            if field_name not in model_data[model_name]['fields']:
                model_data[model_name]['fields'].append(field_name)
            
            # 處理案件資料
            case_results = field_result.get('case_results', [])
            for case_result in case_results:
                case_id = case_result.get('case_id', '')
                if case_id not in model_data[model_name]['cases']:
                    model_data[model_name]['cases'][case_id] = {}
                
                # 計算準確率（轉換為百分比）
                accuracy = 100.0 if case_result.get('is_correct', False) else 0.0
                cer_accuracy = max(0, 100.0 - (case_result.get('cer', 0) * 100))
                wer_accuracy = max(0, 100.0 - (case_result.get('wer', 0) * 100))
                
                model_data[model_name]['cases'][case_id][field_name] = {
                    'accuracy': accuracy,
                    'cer_accuracy': cer_accuracy,
                    'wer_accuracy': wer_accuracy,
                    'ai_value': case_result.get('ai_value', ''),
                    'human_value': case_result.get('human_value', '')
                }
        
        return model_data
    
    def _create_model_evaluation_sheet(
        self,
        wb: Workbook,
        model_name: str,
        model_data: Dict,
        original_data: pd.DataFrame,
        value_set_id: str = None
    ):
        """創建模型評估工作表（按您的格式）"""
        # 清理工作表名稱
        sheet_name = f"{model_name}"[:31]
        sheet_name = ''.join(c for c in sheet_name if c.isalnum() or c in ' _-')
        
        ws = wb.create_sheet(sheet_name)
        
        # 設置標題行
        ws['A1'] = '模型'
        ws['B1'] = model_name
        ws['C1'] = 'valueSetId'
        ws['D1'] = value_set_id or 'string'
        
        # 設置表頭
        ws['A2'] = '受編'
        ws['B2'] = '欄位'
        ws['C2'] = '準確度'
        ws['D2'] = 'CER準確率'
        ws['E2'] = 'WER準確率'
        
        # 設置第一行格式 - 標題行
        for cell in [ws['A1'], ws['B1'], ws['C1'], ws['D1']]:
            cell.font = Font(name='Arial', size=12, bold=True)
            cell.alignment = self.center_alignment
            cell.border = self.thin_border
        
        # 設置第二行格式 - 表頭
        for cell in [ws['A2'], ws['B2'], ws['C2'], ws['D2'], ws['E2']]:
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_alignment
            cell.border = self.thin_border
        
        current_row = 3
        cases = model_data.get('cases', {})
        fields = model_data.get('fields', [])
        
        for case_id, case_data in cases.items():
            # 案件ID行
            ws.cell(row=current_row, column=1, value=case_id)
            ws.cell(row=current_row, column=1).font = Font(bold=True)
            current_row += 1
            
            # 欄位評估行
            field_accuracies = []
            for field_name in fields:
                if field_name in case_data:
                    field_info = case_data[field_name]
                    
                    # 欄位名稱
                    ws.cell(row=current_row, column=2, value=field_name)
                    
                    # 準確度
                    accuracy = field_info['accuracy']
                    ws.cell(row=current_row, column=3, value=f"{accuracy:.1f}%")
                    
                    # CER準確率
                    cer_accuracy = field_info['cer_accuracy']
                    ws.cell(row=current_row, column=4, value=f"{cer_accuracy:.1f}%")
                    
                    # WER準確率
                    wer_accuracy = field_info['wer_accuracy']
                    ws.cell(row=current_row, column=5, value=f"{wer_accuracy:.1f}%")
                    
                    # 設置格式
                    for col in range(2, 6):
                        cell = ws.cell(row=current_row, column=col)
                        cell.border = self.thin_border
                        if col > 2:  # 數值欄位置中
                            cell.alignment = self.center_alignment
                    
                    # 根據準確度設置顏色
                    accuracy_cell = ws.cell(row=current_row, column=3)
                    if accuracy >= 90:
                        accuracy_cell.fill = self.correct_fill
                    elif accuracy >= 70:
                        accuracy_cell.fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
                    elif accuracy < 50:
                        accuracy_cell.fill = self.incorrect_fill
                    
                    field_accuracies.append(accuracy)
                    current_row += 1
            
            # 整體準確度
            if field_accuracies:
                overall_accuracy = sum(field_accuracies) / len(field_accuracies)
                ws.cell(row=current_row, column=2, value="整體準確度")
                ws.cell(row=current_row, column=3, value=f"{overall_accuracy:.2f}%")
                
                # 設置格式
                ws.cell(row=current_row, column=2).font = Font(bold=True)
                overall_cell = ws.cell(row=current_row, column=3)
                overall_cell.font = Font(bold=True)
                overall_cell.alignment = self.center_alignment
                
                # 根據整體準確度設置顏色
                if overall_accuracy >= 90:
                    overall_cell.fill = self.correct_fill
                elif overall_accuracy >= 70:
                    overall_cell.fill = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
                elif overall_accuracy < 50:
                    overall_cell.fill = self.incorrect_fill
                
                current_row += 1
            
            # 分隔線
            ws.cell(row=current_row, column=2, value="--- 分隔線 ---")
            ws.cell(row=current_row, column=2).font = Font(italic=True, color="808080")
            current_row += 1
            
            # 增加空行
            current_row += 1
        
        # 調整欄寬
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 12
        ws.column_dimensions['D'].width = 12
        ws.column_dimensions['E'].width = 12
    
    # 保留舊的方法以備不時之需
    async def generate_multi_model_evaluation_report(
        self,
        original_data: pd.DataFrame,
        model_mappings: Dict[str, Dict[str, int]],
        field_mappings: Dict[str, Tuple[int, str]],
        evaluation_results: Dict[str, Any],
        original_filename: str,
        value_set_id: str = None
    ) -> bytes:
        """
        生成多模型外來函文評估報告（舊格式）
        
        Args:
            original_data: 原始資料
            model_mappings: 模型欄位映射
            field_mappings: 欄位映射
            evaluation_results: 評估結果
            original_filename: 原始檔案名稱
            value_set_id: valueSetId 值
            
        Returns:
            bytes: Excel檔案內容
        """
        # 使用新的格式方法
        return await self.generate_document_evaluation_report(
            original_data, evaluation_results, original_filename, value_set_id
        )
