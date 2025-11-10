from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.request.queryRequest import QueryProcessRequest
from app.schemas.response.queryProcessResponse import QueryProcessResponse, QueryProcessResult, Citation
from app.schemas.response.errorResponse import ErrorResponse
from app.service.query_service import QueryService
from loguru import logger

router = APIRouter(prefix="/query", tags=["query"])

query_service = QueryService()


@router.post("/process")
async def query(
    request: QueryProcessRequest,
    db: AsyncSession = Depends(get_db)
):
    """Query 요청 처리: query-embedding -> search -> cross-encoder -> generation 순서로 처리"""
    try:
        logger.info("Received query request: {}", request.query)
        result = await query_service.process_query(request, db)
        
        # citations 변환
        citations = [
            Citation(
                text=citation.get("text", ""),
                page=citation.get("page", 1),
                chunk_id=citation.get("chunk_id", 0),
                score=citation.get("score", 0.0)
            )
            for citation in result.get("citations", [])
        ]
        
        # Response 생성
        response = QueryProcessResponse(
            status=200,
            code="OK",
            message="요청에 성공하였습니다.",
            isSuccess=True,
            result=QueryProcessResult(
                query=result.get("query", request.query),
                answer=result.get("answer", ""),
                citations=citations
            )
        )
        return response
    except ValueError as e:
        logger.error(f"Value error in query processing: {str(e)}")
        error_response = ErrorResponse(
            status=404,
            code="NOT_FOUND",
            message=str(e),
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=404, detail=error_response.dict())
    except Exception as e:
        logger.error(f"Error in query processing: {str(e)}", exc_info=True)
        error_response = ErrorResponse(
            status=500,
            code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())
