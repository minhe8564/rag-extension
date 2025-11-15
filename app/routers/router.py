from fastapi import APIRouter, HTTPException
from app.schemas.request.chunkingRequest import ChunkingProcessRequest
from app.schemas.response.chunkingProcessResponse import ChunkingProcessResponse, ChunkingProcessResult, Chunk
from app.schemas.response.errorResponse import ErrorResponse
from app.middleware.metrics_middleware import with_chunking_metrics
from typing import Dict, Any
import importlib
from loguru import logger

router = APIRouter(tags=["chunking"])


def get_strategy(strategy_name: str, parameters: Dict[Any, Any] = None) -> Any:
    """
    전략 이름으로 전략 클래스 동적 로드 및 인스턴스 생성
    
    Args:
        strategy_name: 전략 이름 (예: "basic")
        parameters: 전략 파라미터
    
    Returns:
        전략 클래스 인스턴스
    """
    try:
        # 전략명으로 모듈 import (예: "basic" -> app.src.basic)
        strategy_module_name = f"app.src.{strategy_name}"
        logger.debug(f"Attempting to import module: {strategy_module_name}")
        
        strategy_module = importlib.import_module(strategy_module_name)
        logger.debug(f"Module imported successfully: {strategy_module_name}, available attributes: {dir(strategy_module)}")
        
        # 전략 클래스 가져오기 (파일명과 클래스명이 전략명과 동일)
        # 전략명의 첫 글자만 대문자로 변환 (예: "basic" -> "Basic")
        strategy_class_name = strategy_name[0].upper() + strategy_name[1:] if strategy_name else ""
        logger.debug(f"Looking for class: {strategy_class_name} in module {strategy_module_name}")
        
        if not hasattr(strategy_module, strategy_class_name):
            available_classes = [name for name in dir(strategy_module) if not name.startswith('_') and isinstance(getattr(strategy_module, name, None), type)]
            logger.error(f"Class '{strategy_class_name}' not found in module {strategy_module_name}. Available classes: {available_classes}")
            raise AttributeError(f"Class '{strategy_class_name}' not found")
        
        strategy_class = getattr(strategy_module, strategy_class_name)
        
        # 인스턴스 생성
        strategy_instance = strategy_class(parameters=parameters)
        
        logger.info(f"Loaded strategy: {strategy_class_name} (module: {strategy_module_name})")
        return strategy_instance
    
    except ModuleNotFoundError as e:
        logger.error(f"Strategy module not found: {strategy_module_name}, error: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Chunking strategy module '{strategy_name}' not found: {str(e)}"
        )
    except AttributeError as e:
        logger.error(f"Strategy class '{strategy_class_name}' not found in module {strategy_module_name}, error: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Chunking strategy class '{strategy_class_name}' not found in module '{strategy_name}': {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error loading strategy '{strategy_name}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error loading chunking strategy '{strategy_name}': {str(e)}"
        )


@router.post("/process")
@with_chunking_metrics
async def chunking_process(request: ChunkingProcessRequest):
    """
    Chunking /process 엔드포인트
    - chunkingStrategy로 전략 클래스 선택
    - chunk() 메서드 호출하여 pages를 청크로 나누기
    """
    try:
        pages = request.pages
        strategy_name = request.chunkingStrategy
        parameters = request.chunkingParameter

        logger.info(f"Processing chunking: {len(pages)} pages with strategy: {strategy_name}")

        # 페이지 데이터 검증
        if not pages:
            raise HTTPException(
                status_code=400,
                detail="pages cannot be empty"
            )
        
        # 각 페이지가 올바른 형식인지 확인
        for idx, page in enumerate(pages):
            if not isinstance(page, dict):
                raise HTTPException(
                    status_code=400,
                    detail=f"Page at index {idx} must be a dictionary"
                )
            if "content" not in page:
                raise HTTPException(
                    status_code=400,
                    detail=f"Page at index {idx} must have 'content' field"
                )

        # 전략 로드
        logger.info(f"Chunking strategy: {strategy_name}, parameters: {parameters}")
        strategy = get_strategy(strategy_name, parameters)

        # chunk() 메서드 호출
        chunks = strategy.chunk(pages)
        
        # Response 생성
        chunk_list = [
            Chunk(
                page=chunk.get("page", 1),
                chunk_id=chunk.get("chunk_id", i),
                text=chunk.get("text", "")
            )
            for i, chunk in enumerate(chunks)
        ]
        
        response = ChunkingProcessResponse(
            status=200,
            code="OK",
            message="요청에 성공하였습니다.",
            isSuccess=True,
            result=ChunkingProcessResult(
                chunks=chunk_list,
                chunk_count=len(chunk_list),
                strategy=strategy_name,
                strategyParameter=parameters
            )
        )
        return response
    except HTTPException as e:
        error_response = ErrorResponse(
            status=e.status_code,
            code="VALIDATION_ERROR" if e.status_code == 400 else "NOT_FOUND" if e.status_code == 404 else "INTERNAL_ERROR",
            message="요청 파라미터가 유효하지 않습니다." if e.status_code == 400 else str(e.detail),
            isSuccess=False,
            result={"pages": str(e.detail)} if e.status_code == 400 else {}
        )
        raise HTTPException(status_code=e.status_code, detail=error_response.dict())
    except Exception as e:
        logger.error(f"Error processing chunking: {str(e)}", exc_info=True)
        error_response = ErrorResponse(
            status=500,
            code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())
