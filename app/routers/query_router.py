from fastapi import APIRouter, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.request.queryProcessV2Request import QueryProcessV2Request
from app.schemas.response.queryProcessResponse import QueryProcessResponse, QueryProcessResult
from app.schemas.response.errorResponse import ErrorResponse
from app.service.query_service import QueryService
from typing import AsyncIterator
from loguru import logger


router = APIRouter(prefix="/query", tags=["query"])

query_service = QueryService()


@router.post("/process")
async def query(
    request: QueryProcessV2Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(default=None, alias="x-user-role"),
    x_user_uuid: str | None = Header(default=None, alias="x-user-uuid"),
    authorization: str | None = Header(default=None, alias="Authorization")
):
    """Query 요청 처리: 사용자/관리자 분기, 기본 파라미터/전략 DB 조회, generation에 메타 전달"""
    try:
        logger.info("Received query request: {}", request.query)
        logger.info("x-user-role: {}", x_user_role)
        logger.info("x-user-uuid: {}", x_user_uuid)
        result = await query_service.process_query(
            request=request,
            db=db,
            x_user_role=x_user_role,
            x_user_uuid=x_user_uuid,
            authorization=authorization
        )
        # Response 생성 (final shape)
        response = QueryProcessResponse(
            status=200,
            code="OK",
            message="요청에 성공하였습니다.",
            isSuccess=True,
            result=QueryProcessResult(
                messageNo=str(result.get("messageNo", "")),
                role="ai",
                content=str(result.get("content", "")),
                createdAt=str(result.get("createdAt", ""))
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


@router.post("/process/stream")
async def query_stream(
    request: QueryProcessV2Request,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(default=None, alias="x-user-role"),
    x_user_uuid: str | None = Header(default=None, alias="x-user-uuid"),
    authorization: str | None = Header(default=None, alias="Authorization")
):
    """Query 요청 처리 (스트리밍 버전): /process와 동작은 동일하지만 응답을 스트리밍으로 전달"""
    try:
        logger.info("Received query stream request: {}", request.query)
        logger.info("x-user-role: {}", x_user_role)
        logger.info("x-user-uuid: {}", x_user_uuid)
        
        async def stream_generator() -> AsyncIterator[bytes]:
            """스트리밍 응답 생성기"""
            try:
                async for chunk in query_service.process_query_stream(
                    request=request,
                    db=db,
                    x_user_role=x_user_role,
                    x_user_uuid=x_user_uuid,
                    authorization=authorization
                ):
                    yield chunk
            except ValueError as e:
                logger.error(f"Value error in query stream processing: {str(e)}")
                error_data = f'event: error\ndata: {{"message":"{str(e)}"}}\n\n'
                yield error_data.encode('utf-8')
            except Exception as e:
                logger.error(f"Error in query stream processing: {str(e)}", exc_info=True)
                error_data = f'event: error\ndata: {{"message":"Internal server error: {str(e)}"}}\n\n'
                yield error_data.encode('utf-8')
        
        return StreamingResponse(
            content=stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Error setting up query stream: {str(e)}", exc_info=True)
        error_response = ErrorResponse(
            status=500,
            code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())
