from fastapi import APIRouter, HTTPException, Header
from app.schemas.request.extractRequest import ExtractProcessRequest
from app.schemas.response.extractProcessResponse import ExtractProcessResponse, ExtractProcessResult, Page
from app.schemas.response.errorResponse import ErrorResponse
from app.middleware.metrics_middleware import with_extract_metrics
from app.service.extract_service import ExtractService
from typing import Optional, Dict, Any
import importlib
import time
from loguru import logger
from app.service.ingest_progress_client import IngestProgressPusher

router = APIRouter(tags=["extract"])


def get_strategy(strategy_name: str, file_type: str, parameters: Dict[Any, Any] = None) -> Any:
    """
    전략 이름으로 전략 클래스 동적 로드 및 인스턴스 생성
    
    Args:
        strategy_name: 전략 이름 (예: "pyMuPDF", "openpyxl", "txt", "docx")
        file_type: 파일 타입 (txt, xlsx, pdf, docs, docx) - 로깅용
        parameters: 전략 파라미터
    
    Returns:
        전략 클래스 인스턴스
    """
    try:
        # 전략명으로 모듈 import (예: "pyMuPDF" -> app.src.pyMuPDF, "openpyxl" -> app.src.openpyxl)
        strategy_module_name = f"app.src.{strategy_name}"
        logger.debug(f"Attempting to import module: {strategy_module_name}")
        
        strategy_module = importlib.import_module(strategy_module_name)
        logger.debug(f"Module imported successfully: {strategy_module_name}, available attributes: {dir(strategy_module)}")
        
        # 전략 클래스 가져오기 (파일명과 클래스명이 전략명과 동일)
        # 전략명의 첫 글자만 대문자로 변환 (예: "pyMuPDF" -> "PyMuPDF", "openpyxl" -> "Openpyxl", "txt" -> "Txt")
        strategy_class_name = strategy_name[0].upper() + strategy_name[1:] if strategy_name else ""
        logger.debug(f"Looking for class: {strategy_class_name} in module {strategy_module_name}")
        
        if not hasattr(strategy_module, strategy_class_name):
            available_classes = [name for name in dir(strategy_module) if not name.startswith('_') and isinstance(getattr(strategy_module, name, None), type)]
            logger.error(f"Class '{strategy_class_name}' not found in module {strategy_module_name}. Available classes: {available_classes}")
            raise AttributeError(f"Class '{strategy_class_name}' not found")
        
        strategy_class = getattr(strategy_module, strategy_class_name)
        
        # 인스턴스 생성
        strategy_instance = strategy_class(parameters=parameters)
        
        logger.info(f"Loaded strategy: {strategy_class_name} (module: {strategy_module_name}) for file type: {file_type}")
        return strategy_instance
    
    except ModuleNotFoundError as e:
        logger.error(f"Strategy module not found: {strategy_module_name}, error: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Extraction strategy module '{strategy_name}' not found: {str(e)}"
        )
    except AttributeError as e:
        logger.error(f"Strategy class '{strategy_class_name}' not found in module {strategy_module_name}, error: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Extraction strategy class '{strategy_class_name}' not found in module '{strategy_name}': {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error loading strategy '{strategy_name}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error loading extraction strategy '{strategy_name}': {str(e)}"
        )


@router.post("/process")
@with_extract_metrics
async def extract_process(
    request: ExtractProcessRequest, 
    x_user_role: str | None = Header(default=None, alias="x-user-role"), 
    x_user_uuid: str | None = Header(default=None, alias="x-user-uuid"), 
    authorization: str | None = Header(default=None, alias="Authorization")
):
    """
    Extract /process 엔드포인트
    - path로 파일 접근
    - extractionStrategy로 전략 클래스 선택
    - extract() 메서드 호출
    """
    try:
        # Progress pusher (runId가 없으면 fileNo로 대체)
        progress_pusher = IngestProgressPusher(
            user_id=x_user_uuid,
            file_no=request.fileNo,
            run_id=None,
            step_name="EXTRACTION",
        )
        logger.info(f"[PROGRESS] Progress pusher 초기화 - runId={progress_pusher.run_id}, fileNo={request.fileNo}, userId={x_user_uuid}")
        
        service = ExtractService()
        processed = await service.process_request(
            request=request,
            x_user_role=x_user_role,
            x_user_uuid=x_user_uuid,
            progress_pusher=progress_pusher,
        )

        result = processed["result"]
        file_name = processed["file_name"]
        file_ext = processed["file_ext"]
        strategy_name = processed["strategy"]
        parameters = processed["strategy_parameter"]

        # Response 생성 (원본 parameters 사용 - progress_cb 없음)
        pages = [
            Page(
                page=page.get("page", i + 1),
                content=page.get("content", "")
            )
            for i, page in enumerate(result.get("pages", []))
        ]
        
        response = ExtractProcessResponse(
            status=200,
            code="OK",
            message="요청에 성공하였습니다.",
            isSuccess=True,
            result=ExtractProcessResult(
                fileName=file_name,
                fileType=file_ext,
                pages=pages,
                total_pages=result.get("total_pages", len(pages)),
                strategy=strategy_name,
                strategyParameter=parameters  # 원본 parameters 사용 (progress_cb 없음)
            )
        )
        
        logger.info("Extract process completed successfully")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in extract_process: {type(e).__name__}: {str(e)}", exc_info=True)
        error_response = ErrorResponse(
            status=500,
            code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=500, detail=error_response.model_dump())



