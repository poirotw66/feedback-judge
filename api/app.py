#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Application for Disability Certificate AI Test Results Accuracy Evaluation
身心障礙手冊AI測試結果準確度評分系統 - FastAPI版本
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Response, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import io
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

# Import our core evaluators
from .evaluator_service import DisabilityDataEvaluatorService
from .document_evaluator_service import DocumentEvaluatorService
# from .document_evaluator_core import DocumentDataEvaluator
# from .document_excel_generator import DocumentExcelGenerator
from .test_data_evaluator import TestDataEvaluator
from .test_excel_generator import TestExcelGenerator
from .models import EvaluationResponse, ErrorResponse
from .exceptions import (
    EvaluatorException, FileValidationError, FileProcessingError,
    DataValidationError, EvaluationError, ExcelGenerationError,
    file_validation_http_exception, file_processing_http_exception,
    data_validation_http_exception, evaluation_http_exception,
    excel_generation_http_exception
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Disability Certificate AI Accuracy Evaluator",
    description="身心障礙手冊AI測試結果準確度評分系統 API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the evaluator services
evaluator_service = DisabilityDataEvaluatorService()
test_evaluator = TestDataEvaluator()
test_excel_generator = TestExcelGenerator()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Disability Certificate AI Accuracy Evaluator API",
        "description": "身心障礙手冊AI測試結果準確度評分系統",
        "version": "1.0.0",
        "endpoints": {
            "evaluate": "/evaluate - POST endpoint for disability certificate accuracy evaluation",
            "evaluate-document": "/evaluate-document - POST endpoint for external document accuracy evaluation",
            "evaluate-test": "/evaluate-test - POST endpoint for test data evaluation",
            "evaluate-fixed-test": "/evaluate-fixed-test - GET endpoint for fixed test file evaluation",
            "health": "/health - Health check endpoint",
            "docs": "/docs - API documentation"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Disability Certificate AI Accuracy Evaluator"
    }

@app.post("/evaluate")
async def evaluate_accuracy(
    file: UploadFile = File(..., description="Excel file (.xlsx or .xls) containing AI test results"),
    valueSetId: str = Form(None, description="Value Set ID for the evaluation")
):
    """
    Evaluate accuracy of AI test results from uploaded Excel file

    Args:
        file: Excel file containing the AI test results data
        valueSetId: Optional Value Set ID for the evaluation

    Returns:
        Excel file with accuracy evaluation results
    """
    try:
        # Validate file exists and has content
        if not file.filename:
            raise file_validation_http_exception("No file provided", "")

        # Validate file size (10MB limit)
        file_content = await file.read()
        if len(file_content) == 0:
            raise file_validation_http_exception("Empty file provided", file.filename)

        if len(file_content) > 10 * 1024 * 1024:  # 10MB limit
            raise file_validation_http_exception("File too large. Maximum size is 10MB", file.filename)

        # Validate file format
        if not await evaluator_service.validate_file_format(file.filename):
            raise file_validation_http_exception(
                "Invalid file format. Please upload an Excel file (.xlsx or .xls)",
                file.filename
            )

        logger.info(f"Processing file: {file.filename}, size: {len(file_content)} bytes, valueSetId: {valueSetId}")

        # Process the file and get results
        result_file_content, output_filename = await evaluator_service.process_excel_file(
            file_content, file.filename, valueSetId
        )

        logger.info(f"Successfully processed file: {file.filename}")

        # Return the result as a downloadable Excel file
        # Encode filename properly for Chinese characters
        from urllib.parse import quote
        encoded_filename = quote(output_filename.encode('utf-8'))

        return StreamingResponse(
            io.BytesIO(result_file_content),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )

    except HTTPException:
        raise
    except FileValidationError as e:
        logger.warning(f"File validation error for {file.filename}: {str(e)}")
        raise file_validation_http_exception(str(e), file.filename)
    except FileProcessingError as e:
        logger.error(f"File processing error for {file.filename}: {str(e)}")
        raise file_processing_http_exception(str(e), file.filename)
    except DataValidationError as e:
        logger.error(f"Data validation error for {file.filename}: {str(e)}")
        raise data_validation_http_exception(str(e), e.missing_columns)
    except EvaluationError as e:
        logger.error(f"Evaluation error for {file.filename}: {str(e)}")
        raise evaluation_http_exception(str(e))
    except ExcelGenerationError as e:
        logger.error(f"Excel generation error for {file.filename}: {str(e)}")
        raise excel_generation_http_exception(str(e))
    except Exception as e:
        logger.error(f"Unexpected error processing file {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": True,
                "message": "An unexpected error occurred while processing the file",
                "details": {
                    "error_type": "unexpected_error",
                    "filename": file.filename
                }
            }
        )

async def process_test_data_file(file_content: bytes, filename: str) -> Tuple[bytes, str]:
    """
    Process test data file and return evaluation results
    處理測試資料檔案並返回評估結果
    """
    import time
    start_time = time.time()
    
    try:
        # Read Excel file from memory
        file_buffer = io.BytesIO(file_content)
        df = pd.read_excel(file_buffer, engine='openpyxl', header=None)
        
        if df is None or df.empty:
            raise FileProcessingError("無法讀取Excel檔案或檔案為空", filename)
        
        logger.info(f"成功載入測試資料檔案，共 {len(df)} 筆記錄")
        
        # Evaluate test data
        evaluation_results = test_evaluator.evaluate_test_data(df)
        
        processing_time = time.time() - start_time
        
        # Generate result Excel file
        result_content = await test_excel_generator.generate_test_result_excel(
            original_data=df,
            evaluation_results=evaluation_results,
            original_filename=filename,
            processing_time=processing_time
        )
        
        # Generate output filename
        base_name = filename.rsplit('.', 1)[0] if '.' in filename else filename
        output_filename = f"{base_name}_評估結果_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        logger.info(f"測試資料評估完成，處理時間: {processing_time:.2f}秒")
        return result_content, output_filename
        
    except Exception as e:
        logger.error(f"處理測試資料檔案時發生錯誤: {str(e)}")
        raise EvaluationError(f"處理測試資料檔案時發生未預期的錯誤: {str(e)}")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler"""
    logger.warning(f"HTTP Exception: {exc.status_code} - {exc.detail}")

    # If detail is already a dict, use it directly
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )

    # Otherwise, wrap it in our standard format
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": str(exc.detail),
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(EvaluatorException)
async def evaluator_exception_handler(request: Request, exc: EvaluatorException):
    """Custom evaluator exception handler"""
    logger.error(f"Evaluator Exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": str(exc),
            "status_code": 500,
            "timestamp": datetime.now().isoformat(),
            "details": exc.details
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "An unexpected internal server error occurred",
            "status_code": 500,
            "timestamp": datetime.now().isoformat(),
            "details": {
                "error_type": "unexpected_error"
            }
        }
    )


@app.post("/evaluate-document", tags=["外來函文評估"])
async def evaluate_document(
    file: UploadFile = File(..., description="外來函文Excel檔案")
):
    """
    外來函文AI測試結果準確度評估端點
    External Document AI Test Results Accuracy Evaluation Endpoint
    """
    try:
        logger.info(f"收到外來函文評估請求: {file.filename}")
        
        # 驗證檔案類型
        if not file.filename or not file.filename.lower().endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=422,
                detail="只支援 Excel 檔案格式 (.xlsx, .xls)"
            )
        
        # 檢查檔案大小
        if file.size and file.size > 50 * 1024 * 1024:  # 50MB
            raise HTTPException(
                status_code=422,
                detail="檔案大小不能超過 50MB"
            )
        
        # 讀取檔案內容
        file_content = await file.read()
        
        if len(file_content) == 0:
            raise HTTPException(
                status_code=422,
                detail="檔案為空，請上傳有效的Excel檔案"
            )
        
        logger.info(f"開始處理外來函文檔案: {file.filename}, 大小: {len(file_content)} bytes")
        
        # 使用外來函文評估服務
        document_service = DocumentEvaluatorService()
        result_content, output_filename = await document_service.process_document_file(
            file_content, file.filename
        )
        
        logger.info(f"外來函文評估完成: {file.filename}")
        
        # 返回Excel結果檔案
        from urllib.parse import quote
        encoded_filename = quote(output_filename.encode('utf-8'))
        
        return StreamingResponse(
            io.BytesIO(result_content),
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
        
    except HTTPException:
        raise
    except FileValidationError as e:
        logger.warning(f"檔案驗證錯誤: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except FileProcessingError as e:
        logger.error(f"檔案處理錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except DataValidationError as e:
        logger.error(f"資料驗證錯誤: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except EvaluationError as e:
        logger.error(f"評估錯誤: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"外來函文評估過程中發生錯誤: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"外來函文評估失敗: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
