from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from app.schemas.request.generationRequest import GenerationProcessRequest
from app.schemas.response.generationProcessResponse import GenerationProcessResponse, GenerationProcessResult, Citation
from app.schemas.response.errorResponse import ErrorResponse
from app.core.memory_manager import get_memory_manager
from app.middleware.metrics_middleware import with_generation_metrics
from app.service.history_stream_service import get_history_stream_service
from typing import Dict, Any, AsyncIterator
import importlib
import json
import httpx
from loguru import logger

router = APIRouter(tags=["generation"])

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
            detail=f"Generation strategy module '{strategy_name}' not found: {str(e)}"
        )
    except AttributeError as e:
        logger.error(f"Strategy class '{strategy_class_name}' not found, error: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Generation strategy class '{strategy_class_name}' not found: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error loading strategy '{strategy_name}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error loading generation strategy '{strategy_name}': {str(e)}"
        )


@router.post("/process")
@with_generation_metrics
async def generation_process(
    request: GenerationProcessRequest,
    x_user_role: str | None = Header(default=None, alias="x-user-role"),
    x_user_uuid: str | None = Header(default=None, alias="x-user-uuid")
):
    """Generation /process 엔드포인트"""
    try:
        query = request.query
        retrieved_chunks = request.retrievedChunks
        retrieved_chunks_image = request.retrievedChunksImage or []
        strategy_name = request.generationStrategy
        parameters = request.generationParameter
        
        # History 관련 파라미터 (ingest에서 전달된 값 사용)
        # 우선순위: generationParameter.userNo/sessionNo/llmNo -> 요청 필드(userId/sessionId)
        user_no_param = None
        session_no_param = None
        llm_no_param = None
        try:
            if isinstance(parameters, dict):
                user_no_param = parameters.get("userNo")
                session_no_param = parameters.get("sessionNo")
                llm_no_param = parameters.get("llmNo")
        except Exception:
            pass
        userNo = user_no_param or request.userId
        sessionNo = session_no_param or request.sessionId

        logger.info(
            f"Processing generation: query={query[:50]}..., {len(retrieved_chunks)} text chunks, "
            f"{len(retrieved_chunks_image)} image chunks, strategy={strategy_name}, userNo={userNo}, sessionNo={sessionNo}"
        )

        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="query cannot be empty")

        # Redis Stream에 질의 기록
        try:
            history_stream_service = get_history_stream_service()
            history_stream_service.append_user_query(
                query=query,
                user_id=str(userNo) if userNo else None,
                session_id=str(sessionNo) if sessionNo else None,
                strategy=strategy_name,
            )
        except Exception as stream_error:
            logger.warning(f"Failed to append query to Redis stream: {stream_error}")

        # 전략 로드
        strategy = get_strategy(strategy_name, parameters)

        # Memory 생성 (userNo와 sessionNo가 있으면 항상 사용)
        memory = None
        if userNo and sessionNo:
            try:
                # Memory manager 가져오기
                memory_manager = get_memory_manager()
                # 요청 컨텍스트 설정: SESSION_NO, USER_NO, LLM_NO를 그대로 사용하여 MongoDB에 저장되도록 함
                try:
                    memory_manager.set_request_context(
                        str(userNo),
                        str(sessionNo),
                        session_no=session_no_param,
                        user_no=user_no_param,
                        llm_no=llm_no_param,
                    )
                    # AI 메시지 저장 시 LLM_NO가 포함되도록 pending payload에도 설정
                    memory_manager.set_pending_ai_payload(
                        str(userNo),
                        str(sessionNo),
                        llm_no=llm_no_param
                    )
                except Exception as ctx_err:
                    logger.warning(f"Failed to set request context for memory: {ctx_err}")
                
                # LLM 인스턴스 가져오기 (strategy에서)
                llm = None
                if hasattr(strategy, 'llm'):
                    llm = strategy.llm
                
                # Memory 생성 (항상 summary_buffer 전략 사용)
                memory = memory_manager.get_or_create_memory(
                    user_id=str(userNo),
                    session_id=str(sessionNo),
                    llm=llm
                )
                if memory is None:
                    logger.warning(f"Memory initialization returned None. History will be disabled. userNo={userNo}, sessionNo={sessionNo}")
                else:
                    logger.info(f"Memory initialized successfully: strategy=summary_buffer (fixed), userNo={userNo}, sessionNo={sessionNo}")
            except Exception as e:
                logger.error(f"Failed to initialize memory: {e}", exc_info=True)
                logger.warning("Continuing without history...")
        else:
            logger.info("userNo or sessionNo is missing. Memory will not be used.")

        # generate() 메서드 호출 (memory, user_id, session_id 전달)
        # 요청 헤더 전달 (presigned URL 요청 시 사용)
        forward_headers = {
            "x-user-role": x_user_role,
            "x-user-uuid": x_user_uuid,
        }
        result = strategy.generate(
            query, 
            retrieved_chunks, 
            memory=memory,
            user_id=str(userNo) if userNo else None,
            session_id=str(sessionNo) if sessionNo else None,
            request_headers={k: v for k, v in forward_headers.items() if v},
            retrieved_chunks_image=retrieved_chunks_image if retrieved_chunks_image else None
        )

        # citations 변환 (text chunks)
        citations = [
            Citation(
                text=citation.get("text", ""),
                page=citation.get("page", 1),
                chunk_id=citation.get("chunk_id", 0),
                score=citation.get("score", 0.0)
            )
            for citation in result.get("citations", [])
        ]

        # Image chunks에 대해 reference 생성 (presigned_url 가져오기)
        image_references = []
        if retrieved_chunks_image:
            def _fetch_presigned(file_no: str, inline: bool = False) -> str:
                if not file_no:
                    return ""
                inline_param = "true" if inline else "false"
                url = f"http://hebees-python-backend:8000/api/v1/files/{file_no}/presigned?inline={inline_param}"
                logger.info(f"[Generation] Fetching presigned URL for image (inline={inline_param}): {url}")
                try:
                    with httpx.Client(timeout=3600.0, follow_redirects=True) as client:
                        headers = {}
                        if x_user_uuid:
                            headers["x-user-uuid"] = x_user_uuid
                        if x_user_role:
                            headers["x-user-role"] = x_user_role
                        r = client.get(url, headers=headers)
                        r.raise_for_status()
                        presigned_url = ""
                        try:
                            data = r.json()
                            presigned_url = (data.get("result", {}).get("data", {}) or {}).get("url") or data.get("url") or ""
                        except Exception:
                            presigned_url = r.text.strip().strip('"')
                        if not presigned_url:
                            logger.warning(f"[Generation] Presigned URL not resolved for image file_no: {file_no}")
                            return ""
                        logger.info(f"[Generation] Presigned URL fetched for image (inline={inline_param}): {presigned_url[:100]}...")
                        return presigned_url
                except Exception as e:
                    logger.warning(f"[Generation] Presigned fetch failed for image file_no {file_no}: {e}")
                    return ""
            
            for chunk in retrieved_chunks_image:
                file_no = chunk.get("fileNo") or chunk.get("metadata", {}).get("file_no") or ""
                file_name = chunk.get("fileName") or chunk.get("metadata", {}).get("metadata", {}).get("FILE_NAME") or ""
                page = chunk.get("page", 1)
                # 이미지 chunk의 text 가져오기 (이미지 설명/캡션)
                image_text = chunk.get("text", "") or chunk.get("page_content", "") or ""
                
                # downloadUrl은 inline=false, snippet용은 inline=true
                download_url = _fetch_presigned(str(file_no), inline=False) if file_no else ""
                inline_url = _fetch_presigned(str(file_no), inline=True) if file_no else ""
                
                # snippet 형식: ![대체 이미지 텍스트](이미지 url)
                alt_text = image_text if image_text else "이미지"
                snippet = f"![{alt_text}]({inline_url})" if inline_url else (f"image: {image_text}" if image_text else "image")
                
                image_references.append({
                    "fileNo": str(file_no) if file_no else "",
                    "name": file_name,
                    "title": file_name.rsplit('.', 1)[0] if '.' in file_name else file_name,
                    "type": file_name.rsplit('.', 1)[-1].lower() if '.' in file_name else "",
                    "index": int(page) if page else 1,
                    "downloadUrl": download_url,
                    "snippet": snippet
                })
        
        # 기존 references에 image references 추가
        existing_references = result.get("references", [])
        all_references = existing_references + image_references

        # Response 생성 (messageNo/createdAt 포함)
        last_meta = {}
        try:
            memory_manager = get_memory_manager()
            last_meta = memory_manager.get_last_ai_message_meta(str(userNo), str(sessionNo))
        except Exception:
            last_meta = {}
        
        # references를 result에 포함시키기 위해 수정
        result_with_references = dict(result)
        result_with_references["references"] = all_references
        
        response = GenerationProcessResponse(
            status=200,
            code="OK",
            message="요청에 성공하였습니다.",
            isSuccess=True,
            result=GenerationProcessResult(
                query=result_with_references.get("query", query),
                answer=result_with_references.get("answer", ""),
                citations=citations,
                contexts_used=result_with_references.get("contexts_used", 0),
                strategy=result_with_references.get("strategy", strategy_name),
                parameters=result_with_references.get("parameters", parameters),
                messageNo=last_meta.get("messageNo"),
                createdAt=last_meta.get("createdAt"),
                references=all_references
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
        logger.error(f"Error processing generation: {str(e)}", exc_info=True)
        error_response = ErrorResponse(
            status=500,
            code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())


@router.post("/process/stream")
@with_generation_metrics
async def generation_process_stream(
    request: GenerationProcessRequest,
    x_user_role: str | None = Header(default=None, alias="x-user-role"),
    x_user_uuid: str | None = Header(default=None, alias="x-user-uuid")
):
    """Generation /process/stream 엔드포인트 - SSE 스트리밍"""
    try:
        query = request.query
        retrieved_chunks = request.retrievedChunks
        retrieved_chunks_image = request.retrievedChunksImage or []
        strategy_name = request.generationStrategy
        parameters = request.generationParameter
        
        # History 관련 파라미터 (ingest에서 전달된 값 사용)
        user_no_param = None
        session_no_param = None
        llm_no_param = None
        try:
            if isinstance(parameters, dict):
                user_no_param = parameters.get("userNo")
                session_no_param = parameters.get("sessionNo")
                llm_no_param = parameters.get("llmNo")
        except Exception:
            pass
        userNo = user_no_param or request.userId
        sessionNo = session_no_param or request.sessionId

        logger.info(
            f"Processing generation stream: query={query[:50]}..., {len(retrieved_chunks)} chunks, "
            f"strategy={strategy_name}, userNo={userNo}, sessionNo={sessionNo}"
        )

        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="query cannot be empty")

        # Redis Stream에 질의 기록
        try:
            history_stream_service = get_history_stream_service()
            history_stream_service.append_user_query(
                query=query,
                user_id=str(userNo) if userNo else None,
                session_id=str(sessionNo) if sessionNo else None,
                strategy=strategy_name,
            )
        except Exception as stream_error:
            logger.warning(f"Failed to append query to Redis stream: {stream_error}")

        # 전략 로드
        strategy = get_strategy(strategy_name, parameters)

        # Memory 생성 (userNo와 sessionNo가 있으면 항상 사용)
        memory = None
        if userNo and sessionNo:
            try:
                memory_manager = get_memory_manager()
                try:
                    memory_manager.set_request_context(
                        str(userNo),
                        str(sessionNo),
                        session_no=session_no_param,
                        user_no=user_no_param,
                        llm_no=llm_no_param,
                    )
                    memory_manager.set_pending_ai_payload(
                        str(userNo),
                        str(sessionNo),
                        llm_no=llm_no_param
                    )
                except Exception as ctx_err:
                    logger.warning(f"Failed to set request context for memory: {ctx_err}")
                
                llm = None
                if hasattr(strategy, 'llm'):
                    llm = strategy.llm
                
                memory = memory_manager.get_or_create_memory(
                    user_id=str(userNo),
                    session_id=str(sessionNo),
                    llm=llm
                )
                if memory is None:
                    logger.warning(f"Memory initialization returned None. History will be disabled. userNo={userNo}, sessionNo={sessionNo}")
                else:
                    logger.info(f"Memory initialized successfully: strategy=summary_buffer (fixed), userNo={userNo}, sessionNo={sessionNo}")
            except Exception as e:
                logger.error(f"Failed to initialize memory: {e}", exc_info=True)
                logger.warning("Continuing without history...")
        else:
            logger.info("userNo or sessionNo is missing. Memory will not be used.")

        # 요청 헤더 전달
        forward_headers = {
            "x-user-role": x_user_role,
            "x-user-uuid": x_user_uuid,
        }

        async def stream_generator() -> AsyncIterator[bytes]:
            """스트리밍 응답 생성기"""
            try:
                # strategy.generate_stream 호출
                stream = strategy.generate_stream(
                    query=query,
                    retrieved_chunks=retrieved_chunks,
                    memory=memory,
                    user_id=str(userNo) if userNo else None,
                    session_id=str(sessionNo) if sessionNo else None,
                    request_headers={k: v for k, v in forward_headers.items() if v},
                    retrieved_chunks_image=retrieved_chunks_image if retrieved_chunks_image else None
                )
                
                # 스트리밍 데이터 전송 (generate_stream이 이미 init과 update를 전송함)
                async for chunk in stream:
                    yield chunk.encode('utf-8')
                
            except Exception as e:
                logger.error(f"Error in stream generation: {str(e)}", exc_info=True)
                error_data = {
                    "message": str(e)
                }
                yield f"event: error\ndata: {json.dumps(error_data, ensure_ascii=False)}\n\n".encode('utf-8')

        return StreamingResponse(
            content=stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
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
        logger.error(f"Error processing generation stream: {str(e)}", exc_info=True)
        error_response = ErrorResponse(
            status=500,
            code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())

