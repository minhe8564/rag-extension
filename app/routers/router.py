from fastapi import APIRouter, HTTPException
from app.schemas.request.crossEncoderRequest import CrossEncoderProcessRequest
from app.schemas.response.crossEncoderProcessResponse import CrossEncoderProcessResponse, CrossEncoderProcessResult, RetrievedChunk
from app.schemas.response.errorResponse import ErrorResponse
from typing import Dict, Any
import importlib
from loguru import logger

router = APIRouter(tags=["cross-encoder"])


def get_strategy(strategy_name: str, parameters: Dict[Any, Any] = None) -> Any:
    """전략 이름으로 전략 클래스 동적 로드 및 인스턴스 생성"""
    try:
        strategy_module_name = f"app.src.{strategy_name}"
        logger.debug(f"Attempting to import module: {strategy_module_name}")
        
        strategy_module = importlib.import_module(strategy_module_name)
        logger.debug(f"Module imported successfully: {strategy_module_name}")
        
        strategy_class_name = strategy_name[0].upper() + strategy_name[1:] if strategy_name else ""
        logger.debug(f"Looking for class: {strategy_class_name}")
        
        if not hasattr(strategy_module, strategy_class_name):
            available_classes = [name for name in dir(strategy_module) if not name.startswith('_') and isinstance(getattr(strategy_module, name, None), type)]
            logger.error(f"Class '{strategy_class_name}' not found. Available classes: {available_classes}")
            raise AttributeError(f"Class '{strategy_class_name}' not found")
        
        strategy_class = getattr(strategy_module, strategy_class_name)
        strategy_instance = strategy_class(parameters=parameters)
        
        logger.info(f"Loaded strategy: {strategy_class_name}")
        return strategy_instance
    
    except ModuleNotFoundError as e:
        logger.error(f"Strategy module not found: {strategy_module_name}, error: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Cross-encoder strategy module '{strategy_name}' not found: {str(e)}"
        )
    except AttributeError as e:
        logger.error(f"Strategy class '{strategy_class_name}' not found, error: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Cross-encoder strategy class '{strategy_class_name}' not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error loading strategy '{strategy_name}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error loading cross-encoder strategy '{strategy_name}': {str(e)}"
        )


@router.post("/process")
async def cross_encoder_process(request: CrossEncoderProcessRequest):
    """Cross Encoder /process 엔드포인트"""
    try:
        query = request.query
        candidate_embeddings = request.candidateEmbeddings
        strategy_name = request.crossEncoderStrategy
        parameters = request.crossEncoderParameter

        logger.info(f"Processing cross-encoder: {len(candidate_embeddings)} candidates, strategy={strategy_name}")

        if not query:
            raise HTTPException(status_code=400, detail="query cannot be empty")

        # 전략 로드
        strategy = get_strategy(strategy_name, parameters)

        # rerank() 메서드 호출 (기존 코드와 호환을 위해 Dict 형태로 변환)
        query_embedding_dict = {"query": query}
        result = strategy.rerank(query_embedding_dict, candidate_embeddings)

        # retrievedChunks 변환
        retrieved_chunks = [
            RetrievedChunk(
                page=chunk.get("page", 1),
                chunk_id=chunk.get("chunk_id", 0),
                text=chunk.get("text", ""),
                score=chunk.get("score", 0.0),
                fileNo=chunk.get("fileNo", ""),
                fileName=chunk.get("fileName", "")
            )
            for chunk in result.get("retrievedChunks", [])
        ]

        # Response 생성
        response = CrossEncoderProcessResponse(
            status=200,
            code="OK",
            message="요청에 성공하였습니다.",
            isSuccess=True,
            result=CrossEncoderProcessResult(
                query=result.get("query", query),
                retrievedChunks=retrieved_chunks,
                count=result.get("count", len(retrieved_chunks)),
                strategy=result.get("strategy", strategy_name),
                parameters=result.get("parameters", parameters)
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
        logger.error(f"Error processing cross-encoder: {str(e)}", exc_info=True)
        error_response = ErrorResponse(
            status=500,
            code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())

