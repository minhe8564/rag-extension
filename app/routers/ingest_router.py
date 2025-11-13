from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.request.ingestRequest import IngestRequest
from app.schemas.request.collectionRequest import CollectionRequest
from app.schemas.request.ingestProcessRequest import IngestProcessRequest
from app.schemas.response.ingestProcessResponse import IngestProcessResponse, IngestProcessResult
from app.schemas.response.errorResponse import ErrorResponse
from app.service.ingest_service import IngestService
from app.service.gateway_client import GatewayClient
from app.core.database import get_db
from typing import Optional, List
import json
import httpx
from loguru import logger
from sqlalchemy import text
import uuid
from datetime import datetime, timezone

router = APIRouter(prefix="/ingest", tags=["ingest"])

ingest_service = IngestService()
gateway_client = GatewayClient()


async def parse_ingest_request_from_form(
    collection_name: Optional[str] = Form(None, description="Collection name"),
    collection_number_list: Optional[str] = Form(None, description="Collection number list (JSON array as string)"),
    extractionPdf: str = Form(..., description="PDF extraction type"),
    extractionPdfParameter: Optional[str] = Form(default="{}", description="PDF extraction parameters (JSON object as string)"),
    extractionXlsx: str = Form(..., description="XLSX extraction type"),
    extractionXlsxParameter: Optional[str] = Form(default="{}", description="XLSX extraction parameters (JSON object as string)"),
    extractionDocs: str = Form(..., description="DOCS extraction type"),
    extractionDocsParameter: Optional[str] = Form(default="{}", description="DOCS extraction parameters (JSON object as string)"),
    extractionTxt: str = Form(..., description="TXT extraction type"),
    extractionTxtParameter: Optional[str] = Form(default="{}", description="TXT extraction parameters (JSON object as string)"),
    chunkingStrategy: str = Form(..., description="Chunking strategy"),
    chunkingParameter: Optional[str] = Form(default="{}", description="Chunking parameters (JSON object as string)"),
    embeddingStrategy: str = Form(..., description="Embedding strategy"),
    embeddingParameter: Optional[str] = Form(default="{}", description="Embedding parameters (JSON object as string)")
) -> IngestRequest:
    """Form 데이터를 받아서 IngestRequest로 변환 (/extract 엔드포인트용 - file은 UploadFile로 별도 전달)"""
    try:
        # JSON 문자열 파싱
        collection_number_list_parsed = json.loads(collection_number_list) if collection_number_list else None
        
        # CollectionRequest 생성
        collection = CollectionRequest(
            name=collection_name,
            numberList=collection_number_list_parsed
        )
        
        # IngestRequest 생성 (/extract 엔드포인트에서는 file은 빈 리스트로 설정)
        return IngestRequest(
            file=[],  # /extract 엔드포인트에서는 실제 파일을 UploadFile로 받으므로 빈 리스트
            collection=collection,
            extractionPdf=extractionPdf,
            extractionPdfParameter=json.loads(extractionPdfParameter) if extractionPdfParameter else {},
            extractionXlsx=extractionXlsx,
            extractionXlsxParameter=json.loads(extractionXlsxParameter) if extractionXlsxParameter else {},
            extractionDocs=extractionDocs,
            extractionDocsParameter=json.loads(extractionDocsParameter) if extractionDocsParameter else {},
            extractionTxt=extractionTxt,
            extractionTxtParameter=json.loads(extractionTxtParameter) if extractionTxtParameter else {},
            chunkingStrategy=chunkingStrategy,
            chunkingParameter=json.loads(chunkingParameter) if chunkingParameter else {},
            embeddingStrategy=embeddingStrategy,
            embeddingParameter=json.loads(embeddingParameter) if embeddingParameter else {}
        )
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format in form data: {str(e)}")

@router.post("/process")
async def ingest_process(
    request: IngestProcessRequest,
    db: AsyncSession = Depends(get_db),
    user_role_header: Optional[str] = Header(default=None, alias="x-user-role"),
    user_uuid_header: Optional[str] = Header(default=None, alias="x-user-uuid"),
    authorization_header: Optional[str] = Header(default=None, alias="Authorization")
):
    """Ingest 요청 처리 (경로 기반 파이프라인 + 컬렉션 버전/생성 로직)"""
    try:
        # 유효성
        if not request.files:
            error_response = ErrorResponse(
                status=400,
                code="VALIDATION_ERROR",
                message="요청 파라미터가 유효하지 않습니다.",
                isSuccess=False,
                result={"files": "파일 목록이 비어있습니다."}
            )
            raise HTTPException(status_code=400, detail=error_response.dict())

        # 역할 결정: 헤더 > 바디
        user_role = (user_role_header or "").strip()
        user_uuid = (user_uuid_header or "").strip()
        is_admin = user_role.lower() == "admin"
        logger.info("Ingest role resolved: {}", "Admin" if is_admin else "User")

        # 버킷/파티션
        bucket = (request.bucket or "").strip().lower()

        # 버전 조회 쿼리 및 컬렉션명 생성
        if is_admin:
            base_name = "publicRetina"
            version_stmt = text(
                "SELECT COALESCE(MAX(VERSION), 0) AS ver FROM `COLLECTION` "
                "WHERE `NAME` LIKE 'publicRetina%'"
            )
            # ADMIN의 DB 컬렉션명은 bucket에 따라 구분
            if bucket == "public":
                db_collection_name = "public"
                offer_no_for_collection = "0000000000"
            else:
                db_collection_name = "hebees"
                offer_no_for_collection = request.offerNo
        else:
            base_name = "publicRetina"
            version_stmt = text(
                "SELECT COALESCE(MAX(VERSION), 0) AS ver FROM `COLLECTION` "
                "WHERE `OFFER_NO` = :offer_no"
            )
            db_collection_name = f"h{request.offerNo}"
        
        result = await db.execute(version_stmt, {"offer_no": request.offerNo} if not is_admin else {})
        row = result.first()
        current_version = int(row.ver) if row and hasattr(row, "ver") else 0
        version_no = max(current_version, 1)
        # 컬렉션 이름 (Milvus용): USER/ADMIN 분기
        if is_admin:
            collection_name = f"publicRetina_{version_no}"
        else:
            collection_name = f"h{request.offerNo}_{version_no}"
        logger.info("Resolved collection_name: {} (version={})", collection_name, version_no)
        
        # 전략/파라미터: DB 기본값 로딩
        try:
            # 1) INGEST_GROUP: IS_DEFAULT = TRUE 인 레코드에서 CHUNKING_PARAMETER, INGEST_GROUP_NO
            ingest_stmt = text(
                "SELECT `INGEST_GROUP_NO` AS ig_no, `CHUNKING_PARAMETER` AS chunk_param "
                "FROM `INGEST_GROUP` WHERE `IS_DEFAULT` = TRUE ORDER BY `CREATED_AT` DESC LIMIT 1"
            )
            ingest_res = await db.execute(ingest_stmt)
            ingest_row = ingest_res.first()
            if not ingest_row:
                raise HTTPException(status_code=500, detail="No default ingest group configured")

            ingest_group_no = getattr(ingest_row, "ig_no", None)
            chunking_param_raw = getattr(ingest_row, "chunk_param", {}) or {}
            try:
                chunking_param = json.loads(chunking_param_raw) if isinstance(chunking_param_raw, str) else dict(chunking_param_raw)
            except Exception:
                chunking_param = {}

            # 2) EXTRACTION_GROUP: 해당 INGEST_GROUP_NO의 EXTRACTION_PARAMETER
            extraction_stmt = text(
                "SELECT `EXTRACTION_PARAMETER` AS extraction_param "
                "FROM `EXTRACTION_GROUP` WHERE `INGEST_GROUP_NO` = :ig_no "
                "ORDER BY `CREATED_AT` DESC LIMIT 1"
            )
            extraction_res = await db.execute(extraction_stmt, {"ig_no": ingest_group_no})
            extraction_row = extraction_res.first()
            extraction_param_raw = getattr(extraction_row, "extraction_param", {}) if extraction_row else {}
            try:
                extraction_param = json.loads(extraction_param_raw) if isinstance(extraction_param_raw, str) else dict(extraction_param_raw or {})
            except Exception:
                extraction_param = {}

            # 3) EMBEDDING_GROUP: 해당 INGEST_GROUP_NO의 EMBEDDING_PARAMETER
            embedding_stmt = text(
                "SELECT `EMBEDDING_PARAMETER` AS embedding_param "
                "FROM `EMBEDDING_GROUP` WHERE `INGEST_GROUP_NO` = :ig_no "
                "ORDER BY `CREATED_AT` DESC LIMIT 1"
            )
            embedding_res = await db.execute(embedding_stmt, {"ig_no": ingest_group_no})
            embedding_row = embedding_res.first()
            logger.info("embedding_row: {}", embedding_row)
            embedding_param_raw = getattr(embedding_row, "embedding_param", {}) if embedding_row else {}
            try:
                embedding_param = json.loads(embedding_param_raw) if isinstance(embedding_param_raw, str) else dict(embedding_param_raw or {})
            except Exception:
                embedding_param = {}

            # 전략명은 각 parameter의 type 필드에서 획득
            extraction_strategy_db = (extraction_param or {}).get("type")
            chunking_strategy_db = (chunking_param or {}).get("type")
            embedding_strategy_db = (embedding_param or {}).get("type")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Failed to load default strategies from DB: {}", e)
            raise HTTPException(status_code=500, detail="Failed to load default strategies from DB")
        logger.info("extraction_strategy_db: {}", extraction_strategy_db)
        logger.info("chunking_strategy_db: {}", chunking_strategy_db)
        logger.info("embedding_strategy_db: {}", embedding_strategy_db)
        # 컬렉션 DB 보장 (없으면 생성)
        if is_admin:
            exists_stmt = text("SELECT `COLLECTION_NO` FROM `COLLECTION` WHERE `NAME` = :name")
            exists_params = {"name": db_collection_name}
        else:
            # USER는 자신의 OFFER_NO 기준으로 조회
            exists_stmt = text("SELECT `COLLECTION_NO` FROM `COLLECTION` WHERE `OFFER_NO` = :offer_no")
            exists_params = {"offer_no": request.offerNo}
        exists_res = await db.execute(exists_stmt, exists_params)
        exists_row = exists_res.first()
        collection_no_bytes: bytes = None
        if not exists_row:
            collection_no = uuid.uuid4().bytes
            insert_stmt = text(
                "INSERT INTO `COLLECTION` "
                "(`COLLECTION_NO`, `OFFER_NO`, `NAME`, `VERSION`, `INGEST_GROUP_NO`, `CREATED_AT`, `UPDATED_AT`) "
                "VALUES (:collection_no, :offer_no, :name, :version, :ingest_group_no, NOW(), NOW())"
            )
            await db.execute(insert_stmt, {
                "collection_no": collection_no,
                "offer_no": offer_no_for_collection if is_admin else request.offerNo,
                "name": db_collection_name,
                # 신규 생성 시 버전은 1로 고정
                "version": 1,
                # 기본 INGEST_GROUP의 NO 사용
                "ingest_group_no": ingest_group_no
            })
            await db.commit()
            logger.info("Created collection row in DB: {} (NAME={})", collection_name, db_collection_name)
            collection_no_bytes = collection_no
        else:
            try:
                collection_no_bytes = getattr(exists_row, "COLLECTION_NO", None) or exists_row[0]
            except Exception:
                collection_no_bytes = None
            logger.info("Resolved collection_no from DB: {}", collection_no_bytes.hex() if collection_no_bytes else "None")

        # FILE.COLLECTION_NO 업데이트 (요청된 파일들)
        try:
            if collection_no_bytes:
                update_params = []
                for f in request.files:
                    file_no_str = (f.fileNo or "").strip()
                    if not file_no_str:
                        continue
                    try:
                        if len(file_no_str) == 32:
                            file_no_bytes = bytes.fromhex(file_no_str)
                        else:
                            file_no_bytes = uuid.UUID(file_no_str).bytes
                    except Exception:
                        logger.warning("Skip FILE.COLLECTION_NO update due to invalid fileNo: {}", file_no_str)
                        continue
                    update_params.append({
                        "collection_no": collection_no_bytes,
                        "file_no": file_no_bytes
                    })
                if update_params:
                    update_sql = text(
                        "UPDATE `FILE` SET `COLLECTION_NO` = :collection_no, `UPDATED_AT` = NOW() "
                        "WHERE `FILE_NO` = :file_no"
                    )
                    await db.execute(update_sql, update_params)
                    await db.commit()
                    logger.info("Updated FILE.COLLECTION_NO for {} files", len(update_params))
        except Exception as e:
            logger.warning("Failed to update FILE.COLLECTION_NO: {}", e)
            await db.rollback()

        # 기본 전략 결정 및 파라미터 정규화: DB 값 사용 (없을 경우 기본값)
        # Extract
        extraction_strategy = (extraction_strategy_db or "").strip() or "txt"
        extraction_params = dict(extraction_param or {})
        logger.info("Extraction params (raw): {}", extraction_param)

        # Chunking (token -> max_tokens 매핑, 기본값 채움)
        chunk_strategy = (chunking_strategy_db or "").strip() or "fixed"
        chunk_params = dict(chunking_param or {})
        if "max_tokens" not in chunk_params and "token" in chunk_params:
            chunk_params["max_tokens"] = chunk_params.get("token")
        if "overlap" not in chunk_params:
            chunk_params["overlap"] = 80
        if "model_name" not in chunk_params and "model" in chunk_params:
            chunk_params["model_name"] = chunk_params.get("model")
        if "model_name" not in chunk_params:
            chunk_params["model_name"] = "klue/bert-base"
        if not chunk_params.get("max_tokens"):
            chunk_params["max_tokens"] = 400
        logger.info("Chunking params (raw): {}", chunking_param)
        logger.info("Chunking params (normalized): {}", chunk_params)

        # Embedding (model -> model_name 매핑, 기본값 채움)
        default_embed_strategy = (embedding_strategy_db or "").strip() or "dense"
        embed_params = dict(embedding_param or {})
        if "model_name" not in embed_params and "model" in embed_params:
            embed_params["model_name"] = embed_params.get("model")
        if "model_name" not in embed_params:
            embed_params["model_name"] = "intfloat/multilingual-e5-large"
        logger.info("Embedding params (raw): {}", embedding_param)
        logger.info("Embedding params (normalized): {}", embed_params)

        # 파일별 파이프라인 진행
        processed_first = None
        completed_files: List[str] = []
        failed_files: List[str] = []
        for idx, f in enumerate(request.files):
            file_type = (f.fileType or "").lower()
            file_name = f.fileName
            file_no = f.fileNo  # string 기대

            try:
                # 1) Extract (fileNo 기반)
                extraction_result = await gateway_client.request_extraction_by_file_no(
                    file_no=file_no,
                    extraction_strategy=extraction_strategy,
                    extraction_params=extraction_params,
                    extra_headers={
                        "x-user-role": user_role,
                        "x-user-uuid": user_uuid
                    }
                )
                
                # 2) Chunk
                chunking_result = await gateway_client.request_chunking(
                    data=extraction_result,
                    strategy=chunk_strategy,
                    parameters=chunk_params
                )

                # 3) Embedding
                await gateway_client.request_embedding(
                    data=chunking_result,
                    collection_name=collection_name,
                    collection_no=collection_no_bytes.hex() if collection_no_bytes else None,
                    file_name=file_name,
                    file_no=file_no,
                    strategy=default_embed_strategy,
                    parameters=embed_params,
                    bucket=bucket,
                    extra_headers={"x-user-role": user_role}
                )

                # 파일별 STATUS = COMPLETED
                try:
                    file_no_bytes = None
                    if file_no:
                        try:
                            if len(file_no) == 32:
                                file_no_bytes = bytes.fromhex(file_no)
                            else:
                                file_no_bytes = uuid.UUID(file_no).bytes
                        except Exception:
                            file_no_bytes = None
                    if file_no_bytes:
                        status_sql = text(
                            "UPDATE `FILE` SET `STATUS` = :status, `UPDATED_AT` = NOW() "
                            "WHERE `FILE_NO` = :file_no"
                        )
                        await db.execute(status_sql, [{"status": "COMPLETED", "file_no": file_no_bytes}])
                        await db.commit()
                        logger.info("Updated FILE.STATUS=COMPLETED for {}", file_name)
                except Exception as se:
                    logger.warning("Failed to update FILE.STATUS=COMPLETED for {}: {}", file_name, se)
                    await db.rollback()

                completed_files.append(file_name or "")
                if processed_first is None:
                    processed_first = (file_name, collection_name)
            except Exception as per_file_err:
                logger.exception("Per-file processing failed for {}: {}", file_name, per_file_err)
                # 파일별 STATUS = FAILED
                try:
                    file_no_bytes = None
                    if file_no:
                        try:
                            if len(file_no) == 32:
                                file_no_bytes = bytes.fromhex(file_no)
                            else:
                                file_no_bytes = uuid.UUID(file_no).bytes
                        except Exception:
                            file_no_bytes = None
                    if file_no_bytes:
                        status_sql = text(
                            "UPDATE `FILE` SET `STATUS` = :status, `UPDATED_AT` = NOW() "
                            "WHERE `FILE_NO` = :file_no"
                        )
                        await db.execute(status_sql, [{"status": "FAILED", "file_no": file_no_bytes}])
                        await db.commit()
                        logger.info("Updated FILE.STATUS=FAILED for {}", file_name)
                except Exception as se:
                    logger.warning("Failed to update FILE.STATUS=FAILED for {}: {}", file_name, se)
                    await db.rollback()
                failed_files.append(file_name or "")

        # Response
        first_file_name, coll_name = processed_first if processed_first else ("", collection_name)

        response = IngestProcessResponse(
            status=200,
            code="OK",
            message="요청에 성공하였습니다." if not failed_files else "일부 파일 처리에 실패했습니다.",
            isSuccess=True,
            result=IngestProcessResult(
                completed=completed_files,
                failed=failed_files,
                collectionName=coll_name
            )
        )
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error processing ingest: {}", e)
        error_response = ErrorResponse(
            status=500,
            code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())

@router.post("/test")
async def ingest_test(
    file: UploadFile = File(..., description="업로드할 파일 (PDF, XLSX, DOCS, TXT 등)"),
    collectionName: str = Form(..., description="Collection name"),
    extractionPdf: str = Form(..., description="PDF extraction strategy"),
    extractionPdfParameter: Optional[str] = Form(default="{}", description="PDF extraction parameters"),
    extractionXlsx: str = Form(..., description="XLSX extraction strategy"),
    extractionXlsxParameter: Optional[str] = Form(default="{}", description="XLSX extraction parameters"),
    extractionDocs: str = Form(..., description="DOCS extraction strategy"),
    extractionDocsParameter: Optional[str] = Form(default="{}", description="DOCS extraction parameters"),
    extractionTxt: str = Form(..., description="TXT extraction strategy"),
    extractionTxtParameter: Optional[str] = Form(default="{}", description="TXT extraction parameters"),
    chunkingStrategy: str = Form(..., description="Chunking strategy"),
    chunkingParameter: Optional[str] = Form(default="{}", description="Chunking parameters"),
    embeddingStrategy: str = Form(..., description="Embedding strategy"),
    embeddingParameter: Optional[str] = Form(default="{}", description="Embedding parameters"),
    db: AsyncSession = Depends(get_db)
):
    """
    파일을 multipart/form-data로 받아서 Extract -> Chunking -> Embedding 처리
    """
    from app.schemas.response.ingestTestResponse import IngestTestResponse, IngestTestResult
    from app.schemas.response.errorResponse import ErrorResponse
    
    try:
        # 파일 내용 읽기
        file_content = await file.read()
        
        # 파일 확장자 확인
        filename = file.filename or "uploaded_file"
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ""
        
        if not file_ext:
            error_response = ErrorResponse(
                status=400,
                code="VALIDATION_ERROR",
                message="요청 파라미터가 유효하지 않습니다.",
                isSuccess=False,
                result={"file": "파일 확장자를 확인할 수 없습니다."}
            )
            raise HTTPException(status_code=400, detail=error_response.dict())
        
        # 파라미터 파싱
        try:
            pdf_params = json.loads(extractionPdfParameter) if extractionPdfParameter else {}
            xlsx_params = json.loads(extractionXlsxParameter) if extractionXlsxParameter else {}
            docs_params = json.loads(extractionDocsParameter) if extractionDocsParameter else {}
            txt_params = json.loads(extractionTxtParameter) if extractionTxtParameter else {}
            chunking_params = json.loads(chunkingParameter) if chunkingParameter else {}
            embedding_params = json.loads(embeddingParameter) if embeddingParameter else {}
        except json.JSONDecodeError as e:
            error_response = ErrorResponse(
                status=400,
                code="VALIDATION_ERROR",
                message="요청 파라미터가 유효하지 않습니다.",
                isSuccess=False,
                result={"parameters": f"JSON 파싱 오류: {str(e)}"}
            )
            raise HTTPException(status_code=400, detail=error_response.dict())
        
        # 파일 타입에 맞는 extraction 설정 선택
        if file_ext == "pdf":
            extraction_strategy = extractionPdf
            extraction_params = pdf_params
        elif file_ext in ["xlsx", "xls"]:
            extraction_strategy = extractionXlsx
            extraction_params = xlsx_params
        elif file_ext in ["doc", "docx"]:
            extraction_strategy = extractionDocs
            extraction_params = docs_params
        elif file_ext == "txt":
            extraction_strategy = extractionTxt
            extraction_params = txt_params
        else:
            extraction_strategy = extractionTxt
            extraction_params = txt_params
        
        # 1) Extract 서비스로 전송
        extraction_result = await gateway_client.request_extraction_with_file(
            file_content=file_content,
            filename=filename,
            extraction_strategy=extraction_strategy,
            extraction_params=extraction_params,
            content_type=file.content_type
        )
        
        # 2) Chunking
        chunking_result = await gateway_client.request_chunking(
            data=extraction_result,
            strategy=chunkingStrategy,
            parameters=chunking_params,
        )
        
        # 3) Embedding
        logger.info(f"collectionName: {collectionName}")
        embedding_result = await gateway_client.request_embedding(
            data=chunking_result,
            collection_name=collectionName,
            file_name=filename,
            file_no=None,
            strategy=embeddingStrategy,
            parameters=embedding_params,
        )
        
        # Response 생성
        response = IngestTestResponse(
            status=200,
            code="OK",
            message="요청에 성공하였습니다.",
            isSuccess=True,
            result=IngestTestResult(
                fileName=filename,
                collectionName=collectionName
            )
        )
        return response
        
    except HTTPException:
        raise
    except httpx.HTTPStatusError as e:
        error_response = ErrorResponse(
            status=e.response.status_code,
            code="INTERNAL_ERROR",
            message=f"서비스 오류: {e.response.text}",
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=e.response.status_code, detail=error_response.dict())
    except Exception as e:
        logger.error(f"Error processing ingest test: {str(e)}", exc_info=True)
        error_response = ErrorResponse(
            status=500,
            code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())
