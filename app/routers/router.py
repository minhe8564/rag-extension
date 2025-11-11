from fastapi import APIRouter, HTTPException
from app.schemas.request.searchRequest import SearchProcessRequest
from app.schemas.response.searchProcessResponse import SearchProcessResponse, SearchProcessResult, CandidateEmbedding, Metadata, MetadataDetail
from app.schemas.response.errorResponse import ErrorResponse
from typing import Dict, Any
import importlib
from loguru import logger

router = APIRouter(tags=["search"])


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
            detail=f"Search strategy module '{strategy_name}' not found: {str(e)}"
        )
    except AttributeError as e:
        logger.error(f"Strategy class '{strategy_class_name}' not found, error: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Search strategy class '{strategy_class_name}' not found: {str(e)}"
        )
    except Exception as e:
        logger.exception("Error loading strategy '{}': {}", strategy_name, e)
        raise HTTPException(
            status_code=500,
            detail=f"Error loading search strategy '{strategy_name}': {str(e)}"
        )


@router.post("/process")
async def search_process(request: SearchProcessRequest):
    """
    Search /process 엔드포인트
    - searchStrategy로 전략 클래스 선택
    - search() 메서드 호출하여 벡터 검색 수행
    """
    try:
        embedding = request.embedding
        collection_name = request.collectionName
        strategy_name = request.searchStrategy
        parameters = request.searchParameter

        logger.info(f"Processing search: collection={collection_name}, strategy={strategy_name}")

        if not embedding:
            raise HTTPException(
                status_code=400,
                detail="embedding cannot be empty"
            )

        # 전략 로드
        strategy = get_strategy(strategy_name, parameters)

        # search() 메서드 호출 (기존 코드와 호환을 위해 Dict 형태로 변환)
        query_embedding_dict = {"embedding": embedding}
        result = strategy.search(query_embedding_dict, collection_name, parameters)
        
        # candidateEmbeddings 변환
        candidate_embeddings = []
        for candidate in result.get("candidateEmbeddings", []):
            metadata_dict = candidate.get("metadata", {})
            metadata_detail = metadata_dict.get("metadata", {})
            
            # metadata_detail이 문자열인 경우 JSON 파싱
            if isinstance(metadata_detail, str):
                import json
                metadata_detail = json.loads(metadata_detail)
            
            candidate_embeddings.append(CandidateEmbedding(
                text=candidate.get("text", ""),
                metadata=Metadata(
                    id=str(metadata_dict.get("id", "")),  # id를 string으로 변환
                    file_no=str(metadata_dict.get("file_no", "")),
                    metadata=MetadataDetail(
                        FILE_NAME=metadata_detail.get("FILE_NAME", ""),
                        PAGE_NO=metadata_detail.get("PAGE_NO", 1),
                        INDEX_NO=metadata_detail.get("INDEX_NO", 0),
                        CREATED_AT=metadata_detail.get("CREATED_AT", ""),
                        UPDATED_AT=metadata_detail.get("UPDATED_AT", "")
                    )
                ),
                score=candidate.get("score", 0.0)
            ))

        # Response 생성
        response = SearchProcessResponse(
            status=200,
            code="OK",
            message="요청에 성공하였습니다.",
            isSuccess=True,
            result=SearchProcessResult(
                collection=result.get("collection", collection_name),
                candidateEmbeddings=candidate_embeddings,
                count=result.get("count", len(candidate_embeddings)),
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
        logger.exception("Error processing search: {}", e)
        error_response = ErrorResponse(
            status=500,
            code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())

