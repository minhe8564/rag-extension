from fastapi import APIRouter, HTTPException
from app.schemas.request.queryEmbeddingRequest import QueryEmbeddingProcessRequest
from app.schemas.response.queryEmbeddingProcessResponse import QueryEmbeddingProcessResponse, QueryEmbeddingProcessResult
from app.schemas.response.errorResponse import ErrorResponse
from app.middleware.metrics_middleware import with_query_embedding_metrics
from typing import Dict, Any
import importlib
import asyncio
from loguru import logger

router = APIRouter(tags=["query-embedding"])


def get_strategy(strategy_name: str, parameters: Dict[Any, Any] = None) -> Any:
    """
    전략 이름으로 전략 클래스 동적 로드 및 인스턴스 생성
    
    Args:
        strategy_name: 전략 이름 (예: "e5Large")
        parameters: 전략 파라미터
    
    Returns:
        전략 클래스 인스턴스
    """
    strategy_module_name = f"app.src.{strategy_name}"
    if strategy_name == "e5Large":
        strategy_class_name = "E5Large"
    else:
        strategy_class_name = strategy_name[0].upper() + strategy_name[1:] if strategy_name else ""
    
    try:
        logger.debug(f"Attempting to import module: {strategy_module_name}")
        
        strategy_module = importlib.import_module(strategy_module_name)
        logger.debug(f"Module imported successfully: {strategy_module_name}, available attributes: {dir(strategy_module)}")
        
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
            detail=f"Query embedding strategy module '{strategy_name}' not found: {str(e)}"
        )
    except AttributeError as e:
        logger.error(f"Strategy class '{strategy_class_name}' not found in module {strategy_module_name}, error: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Query embedding strategy class '{strategy_class_name}' not found in module '{strategy_name}': {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error loading strategy '{strategy_name}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error loading query embedding strategy '{strategy_name}': {str(e)}"
        )


@router.post("/process")
@with_query_embedding_metrics
async def query_embedding_process(request: QueryEmbeddingProcessRequest):
    """
    Query Embedding /process 엔드포인트
    - queryEmbeddingStrategy로 전략 클래스 선택
    - embed() 메서드 호출하여 query를 임베딩으로 변환
    """
    try:
        query = request.query
        strategy_name = request.queryEmbeddingStrategy
        parameters = request.queryEmbeddingParameter

        logger.info(f"Processing query embedding: {query[:50]}... with strategy: {strategy_name}")

        if not query or not query.strip():
            raise HTTPException(
                status_code=400,
                detail="query cannot be empty"
            )

        # 전략 로드
        strategy = get_strategy(strategy_name, parameters)

        if asyncio.iscoroutinefunction(strategy.embed):
            result = await strategy.embed(query)
        else:
            result = strategy.embed(query)

        # Response 생성
        response = QueryEmbeddingProcessResponse(
            status=200,
            code="OK",
            message="요청에 성공하였습니다.",
            isSuccess=True,
            result=QueryEmbeddingProcessResult(
                query=result["query"],
                embedding=result["embedding"],
                dimension=result["dimension"],
                strategy=result["strategy"],
                parameters=result["parameters"]
            )
        )
        return response
    except HTTPException as e:
        error_response = ErrorResponse(
            status=e.status_code,
            code="VALIDATION_ERROR" if e.status_code == 400 else "NOT_FOUND" if e.status_code == 404 else "INTERNAL_ERROR",
            message=str(e.detail),
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=e.status_code, detail=error_response.dict())
    except Exception as e:
        logger.error(f"Error processing query embedding: {str(e)}", exc_info=True)
        error_response = ErrorResponse(
            status=500,
            code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())

