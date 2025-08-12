#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pydantic Models for Disability Certificate AI Accuracy Evaluator API
身心障礙手冊AI測試結果準確度評分系統 - API模型定義
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class FieldType(str, Enum):
    """欄位類型枚舉"""
    DISABILITY_LEVEL = "障礙等級"
    DISABILITY_CATEGORY = "障礙類別"
    ICD_DIAGNOSIS = "ICD診斷"
    CERTIFICATE_TYPE = "證明/手冊"

class EvaluationFieldResult(BaseModel):
    """單一欄位評估結果"""
    field_name: str = Field(..., description="欄位名稱")
    accuracy: float = Field(..., ge=0.0, le=1.0, description="準確度 (0-1)")
    exact_matches: int = Field(..., ge=0, description="完全匹配數量")
    total_records: int = Field(..., gt=0, description="總記錄數")
    match_rate: float = Field(..., ge=0.0, le=1.0, description="匹配率")
    similarity_scores: List[float] = Field(default=[], description="相似度分數列表")

class RecordFieldResult(BaseModel):
    """單筆記錄的欄位評估結果"""
    record_id: str = Field(..., description="記錄編號")
    subject_id: str = Field(..., description="受編")
    field_name: str = Field(..., description="欄位名稱")
    correct_value: str = Field(..., description="正確值")
    predicted_value: str = Field(..., description="預測值")
    similarity: float = Field(..., ge=0.0, le=1.0, description="相似度")
    is_exact_match: bool = Field(..., description="是否完全匹配")

class RecordEvaluation(BaseModel):
    """單筆記錄的完整評估結果"""
    record_id: str = Field(..., description="記錄編號")
    subject_id: str = Field(..., description="受編")
    field_results: Dict[str, RecordFieldResult] = Field(..., description="欄位結果字典")
    overall_accuracy: float = Field(..., ge=0.0, le=1.0, description="整體準確度")
    total_fields: int = Field(..., gt=0, description="總欄位數")
    matched_fields: int = Field(..., ge=0, description="匹配欄位數")

class EvaluationSummary(BaseModel):
    """評估摘要"""
    total_records: int = Field(..., ge=0, description="總記錄數")
    overall_accuracy: float = Field(..., ge=0.0, le=1.0, description="整體準確度")
    field_accuracies: Dict[str, float] = Field(..., description="各欄位準確度")
    perfect_records: int = Field(..., ge=0, description="完全正確記錄數")
    processing_time: float = Field(..., ge=0.0, description="處理時間(秒)")
    timestamp: datetime = Field(default_factory=datetime.now, description="處理時間戳")

class EvaluationResponse(BaseModel):
    """API評估回應"""
    success: bool = Field(True, description="處理是否成功")
    message: str = Field("Evaluation completed successfully", description="回應訊息")
    summary: EvaluationSummary = Field(..., description="評估摘要")
    field_results: Dict[str, EvaluationFieldResult] = Field(..., description="欄位評估結果")
    record_evaluations: List[RecordEvaluation] = Field(default=[], description="記錄評估結果")
    output_filename: str = Field(..., description="輸出檔案名稱")

class ErrorResponse(BaseModel):
    """錯誤回應"""
    error: bool = Field(True, description="是否為錯誤")
    message: str = Field(..., description="錯誤訊息")
    status_code: int = Field(..., description="HTTP狀態碼")
    timestamp: datetime = Field(default_factory=datetime.now, description="錯誤時間戳")
    details: Optional[Dict[str, Any]] = Field(None, description="錯誤詳細資訊")

class FileValidationError(BaseModel):
    """檔案驗證錯誤"""
    filename: str = Field(..., description="檔案名稱")
    error_type: str = Field(..., description="錯誤類型")
    message: str = Field(..., description="錯誤訊息")
    supported_formats: List[str] = Field(default=[".xlsx", ".xls"], description="支援的檔案格式")

class ProcessingStatus(BaseModel):
    """處理狀態"""
    status: str = Field(..., description="處理狀態")
    progress: float = Field(..., ge=0.0, le=1.0, description="處理進度 (0-1)")
    current_step: str = Field(..., description="當前步驟")
    estimated_time_remaining: Optional[float] = Field(None, description="預估剩餘時間(秒)")

class HealthCheckResponse(BaseModel):
    """健康檢查回應"""
    status: str = Field("healthy", description="服務狀態")
    timestamp: datetime = Field(default_factory=datetime.now, description="檢查時間戳")
    service: str = Field("Disability Certificate AI Accuracy Evaluator", description="服務名稱")
    version: str = Field("1.0.0", description="版本號")

class APIInfo(BaseModel):
    """API資訊"""
    message: str = Field(..., description="歡迎訊息")
    description: str = Field(..., description="API描述")
    version: str = Field(..., description="版本號")
    endpoints: Dict[str, str] = Field(..., description="端點說明")
    supported_file_formats: List[str] = Field(default=[".xlsx", ".xls"], description="支援的檔案格式")
    max_file_size: str = Field("10MB", description="最大檔案大小")

# Configuration models
class EvaluatorConfig(BaseModel):
    """評估器配置"""
    similarity_threshold: float = Field(0.8, ge=0.0, le=1.0, description="相似度閾值")
    weight_config: Dict[FieldType, float] = Field(
        default={
            FieldType.DISABILITY_LEVEL: 0.3,
            FieldType.DISABILITY_CATEGORY: 0.3,
            FieldType.ICD_DIAGNOSIS: 0.25,
            FieldType.CERTIFICATE_TYPE: 0.15
        },
        description="欄位權重配置"
    )
    field_mappings: Dict[str, tuple] = Field(
        default={
            '障礙等級': ('正面_障礙等級', '反面_障礙等級'),
            '障礙類別': ('正面_障礙類別', '反面_障礙類別'),
            'ICD診斷': ('正面_ICD診斷', '反面_ICD診斷')
        },
        description="欄位對應關係"
    )
