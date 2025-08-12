#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Custom Exceptions for Disability Certificate AI Accuracy Evaluator
身心障礙手冊AI測試結果準確度評分系統 - 自定義例外處理
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException

class EvaluatorException(Exception):
    """評估器基礎例外類別"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

class FileValidationError(EvaluatorException):
    """檔案驗證錯誤"""
    def __init__(self, message: str, filename: str = "", details: Optional[Dict[str, Any]] = None):
        self.filename = filename
        super().__init__(message, details)

class FileProcessingError(EvaluatorException):
    """檔案處理錯誤"""
    def __init__(self, message: str, filename: str = "", details: Optional[Dict[str, Any]] = None):
        self.filename = filename
        super().__init__(message, details)

class DataValidationError(EvaluatorException):
    """資料驗證錯誤"""
    def __init__(self, message: str, missing_columns: list = None, details: Optional[Dict[str, Any]] = None):
        self.missing_columns = missing_columns or []
        super().__init__(message, details)

class EvaluationError(EvaluatorException):
    """評估處理錯誤"""
    pass

class ExcelGenerationError(EvaluatorException):
    """Excel生成錯誤"""
    pass

# HTTP Exception wrappers
def create_http_exception(status_code: int, message: str, details: Optional[Dict[str, Any]] = None) -> HTTPException:
    """建立HTTP例外"""
    return HTTPException(
        status_code=status_code,
        detail={
            "error": True,
            "message": message,
            "details": details or {}
        }
    )

def file_validation_http_exception(message: str, filename: str = "") -> HTTPException:
    """檔案驗證HTTP例外"""
    return create_http_exception(
        status_code=400,
        message=message,
        details={
            "error_type": "file_validation_error",
            "filename": filename,
            "supported_formats": [".xlsx", ".xls"]
        }
    )

def file_processing_http_exception(message: str, filename: str = "") -> HTTPException:
    """檔案處理HTTP例外"""
    return create_http_exception(
        status_code=422,
        message=message,
        details={
            "error_type": "file_processing_error",
            "filename": filename
        }
    )

def data_validation_http_exception(message: str, missing_columns: list = None) -> HTTPException:
    """資料驗證HTTP例外"""
    return create_http_exception(
        status_code=422,
        message=message,
        details={
            "error_type": "data_validation_error",
            "missing_columns": missing_columns or []
        }
    )

def evaluation_http_exception(message: str) -> HTTPException:
    """評估處理HTTP例外"""
    return create_http_exception(
        status_code=500,
        message=message,
        details={
            "error_type": "evaluation_error"
        }
    )

def excel_generation_http_exception(message: str) -> HTTPException:
    """Excel生成HTTP例外"""
    return create_http_exception(
        status_code=500,
        message=message,
        details={
            "error_type": "excel_generation_error"
        }
    )
