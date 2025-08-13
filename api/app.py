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
from typing import Dict, List, Optional
import logging
from datetime import datetime

# Import our core evaluator
from .evaluator_service import DisabilityDataEvaluatorService
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

# Initialize the evaluator service
evaluator_service = DisabilityDataEvaluatorService()

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Disability Certificate AI Accuracy Evaluator API",
        "description": "身心障礙手冊AI測試結果準確度評分系統",
        "version": "1.0.0",
        "endpoints": {
            "evaluate": "/evaluate - POST endpoint for accuracy evaluation",
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
