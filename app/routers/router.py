from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.request.embeddingRequest import EmbeddingProcessRequest
from app.schemas.response.embeddingProcessResponse import EmbeddingProcessResponse, EmbeddingProcessResult
from app.schemas.response.errorResponse import ErrorResponse
from app.service.milvus_service import MilvusService
from app.service.ingest_progress_client import IngestProgressClient
from app.core.settings import settings
from app.models.database import get_db
from app.models.collection import Collection
from app.models.chunk import Chunk
from app.middleware.metrics_middleware import with_embedding_metrics
from typing import Dict, Any, List, Optional
import importlib
from datetime import datetime
from loguru import logger
import uuid
import httpx
import asyncio
import math

router = APIRouter(tags=["embedding"])


def get_strategy(strategy_name: str, parameters: Dict[Any, Any] = None) -> Any:
    """
    전략 이름으로 전략 클래스 동적 로드 및 인스턴스 생성
    
    Args:
        strategy_name: 전략 이름 (예: "e5Large")
        parameters: 전략 파라미터
    
    Returns:
        전략 클래스 인스턴스
    """
    try:
        # 전략명으로 모듈 import (예: "e5Large" -> app.src.e5Large)
        strategy_module_name = f"app.src.{strategy_name}"
        logger.debug(f"Attempting to import module: {strategy_module_name}")
        
        strategy_module = importlib.import_module(strategy_module_name)
        logger.debug(f"Module imported successfully: {strategy_module_name}, available attributes: {dir(strategy_module)}")
        
        # 전략 클래스 가져오기 (파일명과 클래스명이 전략명과 동일)
        # 전략명의 첫 글자만 대문자로 변환 (예: "e5Large" -> "E5Large")
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
            detail=f"Embedding strategy module '{strategy_name}' not found: {str(e)}"
        )
    except AttributeError as e:
        logger.error(f"Strategy class '{strategy_class_name}' not found in module {strategy_module_name}, error: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Embedding strategy class '{strategy_class_name}' not found in module '{strategy_name}': {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error loading strategy '{strategy_name}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error loading embedding strategy '{strategy_name}': {str(e)}"
        )


@router.post("/process")
@with_embedding_metrics
async def embedding_process(
    request: EmbeddingProcessRequest,
    db: AsyncSession = Depends(get_db),
    x_user_role: str | None = Header(default=None, alias="x-user-role"),
    x_user_uuid: str | None = Header(default=None, alias="x-user-uuid")
):
    """
    Embedding /process 엔드포인트
    - embeddingStrategy로 전략 클래스 선택
    - embed() 메서드 호출하여 chunks를 임베딩으로 변환
    - collectionName이 제공되면 Milvus에 저장
    """
    try:
        chunks = request.chunks
        strategy_name = request.embeddingStrategy
        parameters = request.embeddingParameter
        collection_name = request.collectionName
        collection_no = request.collectionNo
        bucket = (getattr(request, "bucket", None) or "").strip().lower() if hasattr(request, "bucket") else None
        file_name = request.fileName or "unknown"
        file_no = request.fileNo
        user_id = x_user_uuid

        # 진행률 전송 클라이언트 초기화
        progress_client = None
        if file_no:
            try:
                progress_client = IngestProgressClient(
                    user_id=user_id,
                    file_no=file_no,
                    run_id=file_no  # fileNo를 runId로 사용
                )
            except Exception as e:
                logger.warning(f"Failed to initialize progress client: {e}")

        logger.info(f"Processing embedding: {len(chunks)} chunks with strategy: {strategy_name}")
        logger.info(f"Embedding parameters: {parameters}")

        # 청크 데이터 검증
        if not chunks:
            error_response = ErrorResponse(
                status=400,
                code="VALIDATION_ERROR",
                message="요청 파라미터가 유효하지 않습니다.",
                isSuccess=False,
                result={"chunks": "chunks cannot be empty"}
            )
            raise HTTPException(status_code=400, detail=error_response.dict())
        
        # 각 청크가 올바른 형식인지 확인
        for idx, chunk in enumerate(chunks):
            if not isinstance(chunk, dict):
                error_response = ErrorResponse(
                    status=400,
                    code="VALIDATION_ERROR",
                    message="요청 파라미터가 유효하지 않습니다.",
                    isSuccess=False,
                    result={f"chunks[{idx}]": "must be a dictionary"}
                )
                raise HTTPException(status_code=400, detail=error_response.dict())
            if "text" not in chunk:
                error_response = ErrorResponse(
                    status=400,
                    code="VALIDATION_ERROR",
                    message="요청 파라미터가 유효하지 않습니다.",
                    isSuccess=False,
                    result={f"chunks[{idx}].text": "field required"}
                )
                raise HTTPException(status_code=400, detail=error_response.dict())

        # EMBEDDING 단계 시작
        progress_task: Optional[asyncio.Task] = None
        total_chunks = len(chunks)
        if progress_client:
            try:
                await progress_client.embedding_start(total=total_chunks)
            except Exception as e:
                logger.debug(f"Failed to send embedding start progress: {e}")

            # UI용 fake 진행률 타이머 (20% 단위)
            # embedding 은 외부 api 호출로 0~100% 진행률을 알 수 없으므로
            # UI 용 fake 진행률로 대체합니다 !! 주의
            async def _embedding_progress_spinner() -> None:
                try:
                    if total_chunks <= 0:
                        return
                    processed = 0
                    # 10% 단위로 processed 증가 (조금 더 큼직하게)
                    step = max(1, math.ceil(total_chunks * 0.20))
                    while True:
                        await asyncio.sleep(1.0)
                        processed = min(total_chunks - 1, processed + step)
                        try:
                            await progress_client.embedding_advance(
                                processed=processed,
                                total=total_chunks,
                            )
                        except Exception as pe:
                            logger.debug(f"Failed to send embedding spinner progress: {pe}")
                        if processed >= total_chunks - 1:
                            break
                except asyncio.CancelledError:
                    # 태스크 취소 시 조용히 종료
                    return
                except Exception as e:
                    logger.debug(f"Embedding spinner task error (ignored): {e}")

            if total_chunks > 0:
                progress_task = asyncio.create_task(_embedding_progress_spinner())

        # 외부 임베딩 API 호출로 embeddings 생성
        documents = [str(chunk.get("text", "")) for chunk in chunks]
        logger.info(f"Documents: {documents}")
        model_name = (parameters or {}).get("model", "intfloat/multilingual-e5-large")
        vectors: List[List[float]] = []
        embedded_chunks: List[Dict[str, Any]] = []

        try:
            payload = {
                "documents": documents,
                "models": [model_name],
            }
            provider_url = settings.embedding_provider_url.rstrip("/") + "/api/v1/embedding/documents"
            logger.info(f"Requesting external embeddings: url={provider_url}, model={model_name}, docs={len(documents)}")
            async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
                resp = await client.post(provider_url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                # 기대 응답: result.data.embeddings[model_name] -> List[List[float]]
                embeddings_map = (((data or {}).get("result") or {}).get("data") or {}).get("embeddings") or {}
                vectors = embeddings_map.get(model_name) or []
                if not isinstance(vectors, list):
                    raise ValueError("Invalid embeddings format from provider")
                if len(vectors) != len(documents):
                    logger.warning(f"Embeddings count mismatch: got {len(vectors)} for {len(documents)} documents")
        except Exception as e:
            logger.error(f"External embedding request failed: {str(e)}", exc_info=True)

            # fake 진행률 타이머 중단
            if progress_task is not None:
                progress_task.cancel()
                try:
                    await progress_task
                except Exception:
                    pass

            # EMBEDDING 실패 알림
            if progress_client:
                try:
                    await progress_client.embedding_fail(processed=0, total=total_chunks)
                except Exception as pe:
                    logger.debug(f"Failed to send embedding fail progress: {pe}")

            # 실패 시 기존 전략으로 폴백 (progress 콜백 주입)
            strategy_params = dict(parameters) if isinstance(parameters, dict) else {}
            if progress_client:
                # 동기 embed()에서 사용할 진행률 콜백
                def _embedding_progress_cb(processed: int, total: Optional[int] = None) -> None:
                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(
                            progress_client.embedding_advance(
                                processed=processed,
                                total=total if total is not None else total_chunks,
                            )
                        )
                    except Exception:
                        # 진행률 전송 실패는 무시
                        pass

                strategy_params["progress_cb"] = _embedding_progress_cb

            strategy = get_strategy(strategy_name, strategy_params)
            result = strategy.embed(chunks)
            if isinstance(result, dict):
                if "embeddings" in result:
                    vectors = result["embeddings"]
                if "chunks" in result:
                    embedded_chunks = result["chunks"]
            elif isinstance(result, list):
                vectors = result

        # EMBEDDING 단계 완료
        if progress_client:
            # fake 진행률 타이머 중단
            if progress_task is not None:
                progress_task.cancel()
                try:
                    await progress_task
                except Exception:
                    pass

            try:
                await progress_client.embedding_complete(
                    processed=len(vectors) if vectors else total_chunks,
                    total=total_chunks,
                )
            except Exception as e:
                logger.debug(f"Failed to send embedding complete progress: {e}")

        # Milvus에 저장 (collection_name이 제공된 경우)
        if collection_name and vectors:
            total_vectors = len(embedded_chunks) if embedded_chunks else len(vectors)

            # VECTOR_STORE 단계 시작
            if progress_client:
                try:
                    await progress_client.vector_store_start(total=total_vectors)
                except Exception as e:
                    logger.debug(f"Failed to send vector_store start progress: {e}")
            
            try:
                milvus_service = MilvusService(
                    host=settings.milvus_host,
                    port=settings.milvus_port,
                )

                # 임베딩 데이터 준비
                now = datetime.utcnow().isoformat()
                milvus_data = []
                processed_vectors = 0

                # embedded_chunks가 있으면 그것을 사용, 없으면 원본 chunks와 vectors를 조합
                if embedded_chunks:
                    # embedded_chunks는 이미 embedding이 포함되어 있음
                    for chunk in embedded_chunks:
                        # metadata 구성 (이미지 참고)
                        metadata = {
                            "FILE_NAME": file_name,
                            "PAGE_NO": chunk.get("page", 1),
                            "INDEX_NO": chunk.get("chunk_id", 1),
                            "CREATED_AT": chunk.get("CREATED_AT", now),
                            "UPDATED_AT": chunk.get("UPDATED_AT", now)
                        }
                        milvus_data.append(
                            {
                                "file_no": file_no,
                                "text": chunk.get("text", ""),
                                "vector": chunk.get("embedding", []),
                                "metadata": metadata,
                            }
                        )

                        processed_vectors += 1
                        if progress_client:
                            try:
                                await progress_client.vector_store_advance(
                                    processed=processed_vectors,
                                    total=total_vectors,
                                )
                            except Exception as pe:
                                logger.debug(f"Failed to send vector_store advance progress: {pe}")
                else:
                    # 원본 chunks와 vectors를 조합
                    for idx, (chunk, vector) in enumerate(zip(chunks, vectors)):
                        # metadata 구성 (이미지 참고)
                        metadata = {
                            "FILE_NAME": file_name,
                            "PAGE_NO": chunk.get("page", chunk.get("PAGE_NO", 1)),
                            "chunk_id": chunk.get("chunk_id", chunk.get("INDEX_NO", chunk.get("index_no", idx))),
                            "CREATED_AT": chunk.get("CREATED_AT", now),
                            "UPDATED_AT": chunk.get("UPDATED_AT", now)
                        }
                        milvus_data.append(
                            {
                                "file_no": file_no,
                                "text": chunk.get("text", ""),
                                "vector": vector,
                                "metadata": metadata,
                            }
                        )

                        processed_vectors += 1
                        if progress_client:
                            try:
                                await progress_client.vector_store_advance(
                                    processed=processed_vectors,
                                    total=total_vectors,
                                )
                            except Exception as pe:
                                logger.debug(f"Failed to send vector_store advance progress: {pe}")
                
                # 벡터 차원 확인 (첫 번째 벡터의 길이 사용)
                if milvus_data and milvus_data[0]["vector"]:
                    vector_dim = len(milvus_data[0]["vector"])
                else:
                    vector_dim = 1024  # 기본값
                
                # Milvus 컬렉션 확인 및 생성 (새로 생성되었는지 확인)
                _, is_newly_created = milvus_service.ensure_collection(collection_name, vector_dim)
                if (x_user_role or "").lower() == "admin":
                    try:
                        milvus_service.ensure_partitions(collection_name, ["public", "hebees"])
                    except Exception as pe:
                        logger.warning(f"Partition ensure failed: {str(pe)}")
                # Milvus에 삽입
                target_partition = None
                if (x_user_role or "").lower() == "admin" and bucket in {"public", "hebees"}:
                    target_partition = bucket
                milvus_service.insert_embeddings(
                    collection_name=collection_name,
                    embeddings=milvus_data,
                    vector_dim=vector_dim,
                    partition_name=target_partition
                )
                
                logger.info(f"Inserted {len(milvus_data)} embeddings into Milvus collection '{collection_name}'")
                
                # VECTOR_STORE 단계 완료
                if progress_client:
                    try:
                        await progress_client.vector_store_complete(processed=len(milvus_data), total=len(milvus_data))
                    except Exception as e:
                        logger.debug(f"Failed to send vector_store complete progress: {e}")
                
            except Exception as e:
                logger.error(f"Failed to insert embeddings into Milvus: {str(e)}", exc_info=True)

                # VECTOR_STORE 단계 실패 알림
                if progress_client:
                    try:
                        await progress_client.vector_store_fail(
                            processed=processed_vectors or None,
                            total=total_vectors,
                        )
                    except Exception as pe:
                        logger.debug(f"Failed to send vector_store fail progress: {pe}")
                # VECTOR_STORE 실패 알림
                if progress_client:
                    try:
                        await progress_client.vector_store_fail(processed=0, total=len(vectors))
                    except Exception as pe:
                        logger.debug(f"Failed to send vector_store fail progress: {pe}")
                # Milvus 저장 실패해도 임베딩 결과는 반환
            
            # Milvus 처리 성공/실패와 상관없이 MySQL CHUNK 저장 시도
            try:
                # DB에서 컬렉션 정보 확인 (없으면 생성)
                from sqlalchemy import select
                stmt = select(Collection).where(Collection.NAME == collection_name)
                result = await db.execute(stmt)
                db_collection = result.scalar_one_or_none()
                # Embedding 쪽에서는 COLLECTION 생성하지 않음 (ingest가 관리)
                if not db_collection and not collection_no:
                    logger.warning("No DB collection row and no collectionNo provided; skipping DB CHUNK/FILE updates.")
                
                if db_collection or collection_no:
                    # 미리 필요한 바이트값을 보관 (롤백 후 속성 만료 이슈 방지)
                    collection_no_bytes = None
                    # 우선순위: 요청에 전달된 collectionNo 사용
                    if collection_no:
                        try:
                            if len(collection_no) == 32:
                                collection_no_bytes = bytes.fromhex(collection_no)
                            else:
                                import uuid as _uuid
                                collection_no_bytes = _uuid.UUID(collection_no).bytes
                            logger.info(f"Using collectionNo from request for CHUNK/FILE insert")
                        except Exception:
                            logger.warning("Invalid collectionNo format in request; falling back to DB collection_no")
                            collection_no_bytes = None
                    if collection_no_bytes is None and db_collection:
                        collection_no_bytes = db_collection.COLLECTION_NO
                        logger.info(f"Using collectionNo from DB for CHUNK/FILE insert")
                    # fileNo 준비: 없거나 잘못된 경우 새 UUID 생성
                    file_no_bytes = None
                    if file_no:
                        try:
                            if len(file_no) == 32:
                                file_no_bytes = bytes.fromhex(file_no)
                            else:
                                file_no_bytes = uuid.UUID(file_no).bytes
                        except (ValueError, AttributeError):
                            logger.warning(f"Invalid fileNo format: {file_no}, will generate a new UUID for FILE_NO")
                            file_no_bytes = None
                    if not file_no_bytes:
                        generated_file_no = uuid.uuid4()
                        file_no_bytes = generated_file_no.bytes
                        logger.info(f"Generated FILE_NO for CHUNK insert: {generated_file_no}")
                    
                    # 청크 정보 수집
                    chunks_to_insert = []
                    if embedded_chunks:
                        for chunk in embedded_chunks:
                            chunks_to_insert.append({
                                "page": chunk.get("page", 1),
                                "chunk_id": chunk.get("chunk_id", 0),
                            })
                    else:
                        for idx, chunk in enumerate(chunks):
                            chunks_to_insert.append({
                                "page": chunk.get("page", chunk.get("PAGE_NO", 1)),
                                "chunk_id": chunk.get("chunk_id", chunk.get("INDEX_NO", idx)),
                            })

                    # 동적 컬럼 존재 여부 확인 후 INSERT (ORM flush 회피, 순수 SQL 사용)
                    from sqlalchemy import text
                    try:
                        # CHUNK.FILE_NAME 존재 여부 확인
                        col_check_sql = text(
                            "SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS "
                            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'CHUNK' AND COLUMN_NAME = 'FILE_NAME'"
                        )
                        check_res = await db.execute(col_check_sql)
                        has_file_name = check_res.first() is not None

                        params = []
                        for chunk_info in chunks_to_insert:
                            base = {
                                "chunk_no": uuid.uuid4().bytes,
                                "collection_no": collection_no_bytes,
                                "file_no": file_no_bytes,
                                "page_no": chunk_info["page"],
                                "index_no": chunk_info["chunk_id"],
                            }
                            if has_file_name:
                                base["file_name"] = file_name
                            params.append(base)
                        
                        if has_file_name:
                            insert_sql = text(
                                "INSERT INTO `CHUNK` "
                                "(`CHUNK_NO`, `COLLECTION_NO`, `FILE_NO`, `FILE_NAME`, `PAGE_NO`, `INDEX_NO`, `CREATED_AT`, `UPDATED_AT`) "
                                "VALUES (:chunk_no, :collection_no, :file_no, :file_name, :page_no, :index_no, now(), now())"
                            )
                        else:
                            insert_sql = text(
                                "INSERT INTO `CHUNK` "
                                "(`CHUNK_NO`, `COLLECTION_NO`, `FILE_NO`, `PAGE_NO`, `INDEX_NO`, `CREATED_AT`, `UPDATED_AT`) "
                                "VALUES (:chunk_no, :collection_no, :file_no, :page_no, :index_no, now(), now())"
                            )

                        await db.execute(insert_sql, params)
                        await db.commit()
                        logger.info(f"Inserted {len(params)} chunks into database{' (without FILE_NAME)' if not has_file_name else ''}")
                    except Exception as e:
                        await db.rollback()
                        logger.exception("CHUNK insert failed: {}", e)
                        raise
                    # Update FILE.COLLECTION_NO after Milvus insertion
                    try:
                        if collection_no_bytes and file_no_bytes:
                            from sqlalchemy import text as _text
                            file_update_sql = _text(
                                "UPDATE `FILE` SET `COLLECTION_NO` = :collection_no, `UPDATED_AT` = NOW() "
                                "WHERE `FILE_NO` = :file_no"
                            )
                            await db.execute(file_update_sql, {"collection_no": collection_no_bytes, "file_no": file_no_bytes})
                            await db.commit()
                            logger.info("Updated FILE.COLLECTION_NO in embedding service")
                    except Exception as e:
                        await db.rollback()
                        logger.warning(f"Failed to update FILE.COLLECTION_NO in embedding service: {str(e)}")
            except Exception as e:
                logger.exception("Failed to ensure collection or insert chunks into database: {}", e)
                await db.rollback()

        # Response 생성 (새 스키마)
        embeddings_list = vectors
        
        # count 계산
        count = len(embedded_chunks) if embedded_chunks else len(embeddings_list) if embeddings_list else len(chunks)
        
        # embedding_dimension 계산
        embedding_dimension = 0
        if embedded_chunks and embedded_chunks[0].get("embedding"):
            embedding_dimension = len(embedded_chunks[0]["embedding"])
        elif embeddings_list and embeddings_list[0]:
            embedding_dimension = len(embeddings_list[0])
        
        response = EmbeddingProcessResponse(
            status=200,
            code="OK",
            message="요청에 성공하였습니다.",
            isSuccess=True,
            result=EmbeddingProcessResult(
                count=count,
                embedding_dimension=embedding_dimension,
                collectionName=collection_name,
                strategy=strategy_name,
                strategyParameter=parameters
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
        logger.exception("Error processing embedding: {}", e)
        error_response = ErrorResponse(
            status=500,
            code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())
