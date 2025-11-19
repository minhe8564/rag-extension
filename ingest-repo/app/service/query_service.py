from app.service.gateway_client import GatewayClient
from app.schemas.request.queryProcessV2Request import QueryProcessV2Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from loguru import logger
from sqlalchemy import text
from app.core.settings import settings
import httpx


class QueryService:
    def __init__(self):
        self.gateway_client = GatewayClient()
    
    async def process_query(
        self,
        request: QueryProcessV2Request,
        db: AsyncSession,
        x_user_role: str | None = None,
        x_user_uuid: str | None = None,
        authorization: str | None = None
    ) -> Dict[Any, Any]:
        """
        Query 요청 처리
        - userNo로 OFFER_NO, ROLE 조회
        - ROLE에 따라 컬렉션명 생성 (USER: h{offerNo}_{version}, ADMIN: publicRetina_{version})
        - QUERY_GROUP에서 IS_DEFAULT=TRUE 파라미터 로드 (retrieval, reranking, prompting)
        - STRATEGY 테이블에서 LLM_NO로 generation_parameter 로드
        - query-embedding -> search (필요시 public 파티션 추가 검색) -> cross-encoder -> generation(ollama)
        - generation 호출 시 sessionNo/userNo/llmNo 전달 (Mongo 저장 메타)
        """
        logger.info("Starting query pipeline for query: {}", request.query)

        # 0) 사용자 정보 조회 (헤더에서 role/uuid, DB에서는 OFFER_NO만 조회)
        user_no = (x_user_uuid or "").strip()
        if not user_no:
            raise ValueError("Missing userNo (x-user-uuid header required)")
        user_stmt = text(
            "SELECT `OFFER_NO` AS offer_no "
            "FROM `USER` WHERE `USER_NO` = UUID_TO_BIN(:user_no) LIMIT 1"
        )
        res = await db.execute(user_stmt, {"user_no": user_no})
        user_row = res.first()
        if not user_row:
            raise ValueError("User not found")
        offer_no = getattr(user_row, "offer_no", None) or user_row[0]
        role = (x_user_role or "USER").upper().strip()
        is_admin = role == "ADMIN"
        logger.info("Resolved user: offerNo={}, role={}", offer_no, role)

        # 1) 컬렉션 버전 조회 및 이름 생성
        if is_admin:
            ver_stmt = text(
                "SELECT COALESCE(MAX(VERSION), 1) AS ver FROM `COLLECTION` WHERE `NAME` LIKE 'publicRetina%'"
            )
            ver_res = await db.execute(ver_stmt)
            ver_row = ver_res.first()
            version_no = int(getattr(ver_row, "ver", 1) if ver_row else 1)
            collection_name = f"publicRetina_{version_no}"
            public_collection_name = collection_name
        else:
            ver_stmt = text(
                "SELECT COALESCE(MAX(VERSION), 1) AS ver FROM `COLLECTION` WHERE `OFFER_NO` = :offer_no"
            )
            ver_res = await db.execute(ver_stmt, {"offer_no": offer_no})
            ver_row = ver_res.first()
            version_no = int(getattr(ver_row, "ver", 1) if ver_row else 1)
            collection_name = f"h{offer_no}_{version_no}"
            # publicRetina 버전도 별도로 조회 (USER 추가 검색용)
            pub_ver_stmt = text(
                "SELECT COALESCE(MAX(VERSION), 1) AS ver FROM `COLLECTION` WHERE `NAME` LIKE 'publicRetina%'"
            )
            pub_ver_res = await db.execute(pub_ver_stmt)
            pub_ver_row = pub_ver_res.first()
            public_version = int(getattr(pub_ver_row, "ver", 1) if pub_ver_row else 1)
            public_collection_name = f"publicRetina_{public_version}"

        logger.info("Resolved collection(s): primary={}, public={}", collection_name, public_collection_name)

        # 2) QUERY_GROUP에서 기본 파라미터 로드 (generation 제외)
        qg_stmt = text(
            "SELECT "
            "`RETRIEVAL_PARAMETER` AS retrieval, "
            "`RERANKING_PARAMETER` AS reranking, "
            "`USER_PROMPTING_PARAMETER` AS user_prompting, "
            "`SYSTEM_PROMPTING_PARAMETER` AS system_prompting "
            "FROM `QUERY_GROUP` WHERE `IS_DEFAULT` = TRUE ORDER BY `CREATED_AT` DESC LIMIT 1"
        )
        qg_res = await db.execute(qg_stmt)
        qg_row = qg_res.first()
        import json as _json
        def _parse_json(raw):
            try:
                if raw is None:
                    return {}
                return _json.loads(raw) if isinstance(raw, str) else dict(raw)
            except Exception:
                return {}
        retrieval_param = _parse_json(getattr(qg_row, "retrieval", None) if qg_row else None)
        reranking_param = _parse_json(getattr(qg_row, "reranking", None) if qg_row else None)
        user_prompting_param = _parse_json(getattr(qg_row, "user_prompting", None) if qg_row else None)
        system_prompting_param = _parse_json(getattr(qg_row, "system_prompting", None) if qg_row else None)
        
        # 2-1) STRATEGY 테이블에서 LLM_NO로 generation_parameter 가져오기
        generation_param = {}
        if request.llmNo:
            try:
                strategy_stmt = text(
                    "SELECT `PARAMETER` AS parameter "
                    "FROM `STRATEGY` WHERE `STRATEGY_NO` = UUID_TO_BIN(:llm_no) LIMIT 1"
                )
                strategy_res = await db.execute(strategy_stmt, {"llm_no": request.llmNo})
                strategy_row = strategy_res.first()
                if strategy_row:
                    generation_param = _parse_json(getattr(strategy_row, "parameter", None))
                    logger.info("Loaded generation parameter from STRATEGY table for llmNo: {}", request.llmNo)
                else:
                    logger.warning("STRATEGY not found for llmNo: {}, using defaults", request.llmNo)
            except Exception as e:
                logger.error(f"Failed to load generation parameter from STRATEGY: {e}", exc_info=True)
                logger.warning("Using default generation parameters")

        retrieval_strategy = (retrieval_param.get("type") or "basic").strip()
        reranking_strategy = (reranking_param.get("type") or "crossEncoder").strip()
        # Generation 전략은 generation_parameter.provider 값을 사용 (없으면 ollama)
        try:
            provider_value = generation_param.get("provider") if isinstance(generation_param, dict) else None
        except Exception:
            provider_value = None
        generation_strategy = (str(provider_value).strip() if provider_value else "") or "ollama"

        # Apply defaults
        try:
            if (retrieval_param.get("type") or "").lower() == "semantic":
                retrieval_param.setdefault("semantic", {}).setdefault("topK", 30)
                retrieval_param.setdefault("semantic", {}).setdefault("threshold", 0.4)
            if reranking_param is None:
                reranking_param = {}
            reranking_param.setdefault("topK", 5)
            reranking_param.setdefault("model", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
            if generation_param is None:
                generation_param = {}
            generation_param.setdefault("model", "qwen3-v1:8b")
            generation_param.setdefault("timeout", 30)
            generation_param.setdefault("provider", "ollama")
            generation_param.setdefault("max_tokens", 512)
            generation_param.setdefault("max_retries", 2)
            generation_param.setdefault("temperature", 0.2)
        except Exception:
            pass

        logger.info("QueryGroup params - retrieval: {}, reranking: {}, generation: {}", retrieval_param, reranking_param, generation_param)

        # 3) Query Embedding - query-embedding-repo 경유 (내부 서비스 호출)
        try:
            qe_strategy = "e5Large"
            qe_param = {"model": "intfloat/multilingual-e5-large"}
            qe_res = await self.gateway_client.request_query_embedding(
                query=request.query,
                strategy=qe_strategy,
                parameters=qe_param
            )
            embedding = qe_res.get("result", {}).get("embedding", [])
            if not isinstance(embedding, list) or not embedding:
                raise ValueError("Invalid query embedding from query-embedding service")
        except Exception as e:
            logger.error(f"Query embedding via query-embedding-repo failed: {str(e)}", exc_info=True)
            raise

        # 3-1) Query Embedding Image - query-embedding-repo/image 경유 (이미지 모델 사용)
        embedding_image = None
        try:
            qe_image_strategy = "mclip"  # 같은 전략, 다른 엔드포인트
            qe_image_param = {"model": "sentence-transformers/clip-ViT-B-32-multilingual-v1"}  # 이미지 모델로 변경 필요할 수 있음
            qe_image_res = await self.gateway_client.request_query_embedding_image(
                query=request.query,
                strategy=qe_image_strategy,
                parameters=qe_image_param
            )
            embedding_image = qe_image_res.get("result", {}).get("embedding", [])
            if not isinstance(embedding_image, list) or not embedding_image:
                logger.warning("Invalid query embedding image, skipping image search")
                embedding_image = None
        except Exception as e:
            logger.warning(f"Query embedding image via query-embedding-repo failed: {str(e)}, continuing without image search")
            embedding_image = None

        # 4) Search - 기본 컬렉션
        logger.info("Retrieval param: {}", retrieval_param)
        search_primary = await self.gateway_client.request_search(
            embedding=embedding,
            collection_name=collection_name,
            strategy=retrieval_strategy,
            parameters=retrieval_param or {}
        )
        candidates = search_primary.get("result", {}).get("candidateEmbeddings", [])
        
        # USER의 경우 publicRetina의 public 파티션 추가 검색
        if not is_admin:
            public_params = dict(retrieval_param or {})
            public_params.setdefault("partition", "public")
            try:
                search_public = await self.gateway_client.request_search(
                    embedding=embedding,
                    collection_name=public_collection_name,
                    strategy=retrieval_strategy,
                    parameters=public_params
                )
                candidates += search_public.get("result", {}).get("candidateEmbeddings", [])
            except Exception as se:
                logger.warning("Public partition search failed or skipped: {}", se)
        
        # 4-1) Search Image - 이미지 컬렉션 (컬렉션 이름에 _image_ 추가)
        candidates_image = []
        if embedding_image:
            try:
                # 컬렉션 이름 형식: h{offerNo}_image_{versionNo} 또는 publicRetina_image_{versionNo}
                if is_admin:
                    image_collection_name = f"publicRetina_image_{version_no}"
                else:
                    image_collection_name = f"h{offer_no}_image_{version_no}"
                search_image_primary = await self.gateway_client.request_search_image(
                    embedding=embedding_image,
                    collection_name=image_collection_name,
                    strategy=retrieval_strategy,
                    parameters=retrieval_param or {}
                )
                candidates_image = search_image_primary.get("result", {}).get("candidateEmbeddings", [])
                
                # USER의 경우 publicRetina 이미지 컬렉션도 추가 검색
                if not is_admin:
                    public_image_collection_name = f"publicRetina_image_{public_version}"
                    public_image_params = dict(retrieval_param or {})
                    public_image_params.setdefault("partition", "public")
                    try:
                        search_image_public = await self.gateway_client.request_search_image(
                            embedding=embedding_image,
                            collection_name=public_image_collection_name,
                            strategy=retrieval_strategy,
                            parameters=public_image_params
                        )
                        candidates_image += search_image_public.get("result", {}).get("candidateEmbeddings", [])
                    except Exception as se:
                        logger.warning("Public image partition search failed or skipped: {}", se)
            except Exception as e:
                logger.warning(f"Image search failed: {str(e)}, continuing without image results")
                candidates_image = []
        
        # 5) Cross-Encoder
        cross_res = await self.gateway_client.request_cross_encoder(
            query=request.query,
            candidate_embeddings=candidates,
            strategy=reranking_strategy,
            parameters=reranking_param or {}
        )
        retrieved_chunks = cross_res.get("result", {}).get("retrievedChunks", [])
        
        # 5-1) Cross-Encoder Image - 같은 방식으로 candidates_image 전달
        retrieved_chunks_image = []
        if candidates_image:
            try:
                cross_image_res = await self.gateway_client.request_cross_encoder_image(
                    query=request.query,
                    candidate_embeddings=candidates_image,
                    strategy=reranking_strategy,
                    parameters=reranking_param or {}
                )
                retrieved_chunks_image = cross_image_res.get("result", {}).get("retrievedChunks", [])
            except Exception as e:
                logger.warning(f"Image cross-encoder failed: {str(e)}, continuing without image reranking")
                retrieved_chunks_image = []

        # 6) Generation (provider 전략) - Mongo 저장 메타 포함
        # text와 image 결과를 따로 전달 (generation에서 구분 가능하도록)
        gen_params = dict(generation_param or {})
        # Inject prompting templates
        try:
            up = (user_prompting_param or {}).get("content")
            sp = (system_prompting_param or {}).get("content")
            if isinstance(up, str) and up:
                gen_params["userPrompt"] = up
            if isinstance(sp, str) and sp:
                gen_params["systemPrompt"] = sp
        except Exception:
            pass
        gen_params.update({
            "sessionNo": request.sessionNo,
            "userNo": user_no,
            "llmNo": request.llmNo
        })
        gen_res = await self.gateway_client.request_generation(
            query=request.query,
            retrieved_chunks=retrieved_chunks,  # text 검색 결과
            retrieved_chunks_image=retrieved_chunks_image if retrieved_chunks_image else None,  # image 검색 결과 (별도 전달)
            strategy=generation_strategy,
            parameters=gen_params,
            extra_headers={
                "x-user-role": x_user_role,
                "x-user-uuid": x_user_uuid,
            }
        )
        gen_result = gen_res.get("result", {})

        # 최종 응답용 데이터 (ingest에서 스키마에 맞춰 변환)
        return {
            "content": gen_result.get("answer", ""),
            "messageNo": gen_result.get("messageNo"),
            "createdAt": gen_result.get("createdAt"),
        }
    
    async def process_query_stream(
        self,
        request: QueryProcessV2Request,
        db: AsyncSession,
        x_user_role: str | None = None,
        x_user_uuid: str | None = None,
        authorization: str | None = None
    ):
        """
        Query 요청 처리 (스트리밍 버전)
        - process_query와 동일하지만 generation을 스트리밍으로 호출
        - QUERY_GROUP에서 기본 파라미터 로드 (retrieval, reranking, prompting)
        - STRATEGY 테이블에서 LLM_NO로 generation_parameter 로드
        """
        logger.info("Starting query pipeline (stream) for query: {}", request.query)

        # 0) 사용자 정보 조회 (헤더에서만 가져옴)
        user_no = (x_user_uuid or "").strip()
        if not user_no:
            raise ValueError("Missing userNo (x-user-uuid header required)")
        user_stmt = text(
            "SELECT `OFFER_NO` AS offer_no "
            "FROM `USER` WHERE `USER_NO` = UUID_TO_BIN(:user_no) LIMIT 1"
        )
        res = await db.execute(user_stmt, {"user_no": user_no})
        user_row = res.first()
        if not user_row:
            raise ValueError("User not found")
        offer_no = getattr(user_row, "offer_no", None) or user_row[0]
        role = (x_user_role or "USER").upper().strip()
        is_admin = role == "ADMIN"
        logger.info("Resolved user: offerNo={}, role={}", offer_no, role)

        # 1) 컬렉션 버전 조회 및 이름 생성
        if is_admin:
            ver_stmt = text(
                "SELECT COALESCE(MAX(VERSION), 1) AS ver FROM `COLLECTION` WHERE `NAME` LIKE 'publicRetina%'"
            )
            ver_res = await db.execute(ver_stmt)
            ver_row = ver_res.first()
            version_no = int(getattr(ver_row, "ver", 1) if ver_row else 1)
            collection_name = f"publicRetina_{version_no}"
            public_collection_name = collection_name
        else:
            ver_stmt = text(
                "SELECT COALESCE(MAX(VERSION), 1) AS ver FROM `COLLECTION` WHERE `OFFER_NO` = :offer_no"
            )
            ver_res = await db.execute(ver_stmt, {"offer_no": offer_no})
            ver_row = ver_res.first()
            version_no = int(getattr(ver_row, "ver", 1) if ver_row else 1)
            collection_name = f"h{offer_no}_{version_no}"
            pub_ver_stmt = text(
                "SELECT COALESCE(MAX(VERSION), 1) AS ver FROM `COLLECTION` WHERE `NAME` LIKE 'publicRetina%'"
            )
            pub_ver_res = await db.execute(pub_ver_stmt)
            pub_ver_row = pub_ver_res.first()
            public_version = int(getattr(pub_ver_row, "ver", 1) if pub_ver_row else 1)
            public_collection_name = f"publicRetina_{public_version}"

        logger.info("Resolved collection(s): primary={}, public={}", collection_name, public_collection_name)

        # 2) QUERY_GROUP에서 기본 파라미터 로드 (generation 제외)
        qg_stmt = text(
            "SELECT "
            "`RETRIEVAL_PARAMETER` AS retrieval, "
            "`RERANKING_PARAMETER` AS reranking, "
            "`USER_PROMPTING_PARAMETER` AS user_prompting, "
            "`SYSTEM_PROMPTING_PARAMETER` AS system_prompting "
            "FROM `QUERY_GROUP` WHERE `IS_DEFAULT` = TRUE ORDER BY `CREATED_AT` DESC LIMIT 1"
        )
        qg_res = await db.execute(qg_stmt)
        qg_row = qg_res.first()
        import json as _json
        def _parse_json(raw):
            try:
                if raw is None:
                    return {}
                return _json.loads(raw) if isinstance(raw, str) else dict(raw)
            except Exception:
                return {}
        retrieval_param = _parse_json(getattr(qg_row, "retrieval", None) if qg_row else None)
        reranking_param = _parse_json(getattr(qg_row, "reranking", None) if qg_row else None)
        user_prompting_param = _parse_json(getattr(qg_row, "user_prompting", None) if qg_row else None)
        system_prompting_param = _parse_json(getattr(qg_row, "system_prompting", None) if qg_row else None)
        
        # 2-1) STRATEGY 테이블에서 LLM_NO로 generation_parameter 가져오기
        generation_param = {}
        if request.llmNo:
            try:
                strategy_stmt = text(
                    "SELECT `PARAMETER` AS parameter "
                    "FROM `STRATEGY` WHERE `STRATEGY_NO` = UUID_TO_BIN(:llm_no) LIMIT 1"
                )
                strategy_res = await db.execute(strategy_stmt, {"llm_no": request.llmNo})
                strategy_row = strategy_res.first()
                if strategy_row:
                    generation_param = _parse_json(getattr(strategy_row, "parameter", None))
                    logger.info("Loaded generation parameter from STRATEGY table for llmNo: {}", request.llmNo)
                else:
                    logger.warning("STRATEGY not found for llmNo: {}, using defaults", request.llmNo)
            except Exception as e:
                logger.error(f"Failed to load generation parameter from STRATEGY: {e}", exc_info=True)
                logger.warning("Using default generation parameters")

        retrieval_strategy = (retrieval_param.get("type") or "basic").strip()
        reranking_strategy = (reranking_param.get("type") or "crossEncoder").strip()
        try:
            provider_value = generation_param.get("provider") if isinstance(generation_param, dict) else None
        except Exception:
            provider_value = None
        generation_strategy = (str(provider_value).strip() if provider_value else "") or "ollama"

        # Apply defaults
        try:
            if (retrieval_param.get("type") or "").lower() == "semantic":
                retrieval_param.setdefault("semantic", {}).setdefault("topK", 30)
                retrieval_param.setdefault("semantic", {}).setdefault("threshold", 0.4)
            if reranking_param is None:
                reranking_param = {}
            reranking_param.setdefault("topK", 5)
            reranking_param.setdefault("model", "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
            if generation_param is None:
                generation_param = {}
            generation_param.setdefault("model", "qwen3-v1:8b")
            generation_param.setdefault("timeout", 30)
            generation_param.setdefault("provider", "ollama")
            generation_param.setdefault("max_tokens", 512)
            generation_param.setdefault("max_retries", 2)
            generation_param.setdefault("temperature", 0.2)
        except Exception:
            pass

        logger.info("QueryGroup params - retrieval: {}, reranking: {}, generation: {}", retrieval_param, reranking_param, generation_param)

        # 3) Query Embedding
        try:
            qe_strategy = "e5Large"
            qe_param = {"model": "intfloat/multilingual-e5-large"}
            qe_res = await self.gateway_client.request_query_embedding(
                query=request.query,
                strategy=qe_strategy,
                parameters=qe_param
            )
            embedding = qe_res.get("result", {}).get("embedding", [])
            if not isinstance(embedding, list) or not embedding:
                raise ValueError("Invalid query embedding from query-embedding service")
        except Exception as e:
            logger.error(f"Query embedding via query-embedding-repo failed: {str(e)}", exc_info=True)
            raise

        # 3-1) Query Embedding Image - query-embedding-repo/image 경유 (이미지 모델 사용)
        embedding_image = None
        try:
            qe_image_strategy = "mclip"  # 같은 전략, 다른 엔드포인트
            qe_image_param = {"model": "sentence-transformers/clip-ViT-B-32-multilingual-v1"}  # 이미지 모델로 변경 필요할 수 있음
            qe_image_res = await self.gateway_client.request_query_embedding_image(
                query=request.query,
                strategy=qe_image_strategy,
                parameters=qe_image_param
            )
            embedding_image = qe_image_res.get("result", {}).get("embedding", [])
            if not isinstance(embedding_image, list) or not embedding_image:
                logger.warning("Invalid query embedding image, skipping image search")
                embedding_image = None
        except Exception as e:
            logger.warning(f"Query embedding image via query-embedding-repo failed: {str(e)}, continuing without image search")
            embedding_image = None

        # 4) Search
        logger.info("Retrieval param: {}", retrieval_param)
        search_primary = await self.gateway_client.request_search(
            embedding=embedding,
            collection_name=collection_name,
            strategy=retrieval_strategy,
            parameters=retrieval_param or {}
        )
        candidates = search_primary.get("result", {}).get("candidateEmbeddings", [])
        
        if not is_admin:
            public_params = dict(retrieval_param or {})
            public_params.setdefault("partition", "public")
            try:
                search_public = await self.gateway_client.request_search(
                    embedding=embedding,
                    collection_name=public_collection_name,
                    strategy=retrieval_strategy,
                    parameters=public_params
                )
                candidates += search_public.get("result", {}).get("candidateEmbeddings", [])
            except Exception as se:
                logger.warning("Public partition search failed or skipped: {}", se)
        
        # 4-1) Search Image - 이미지 컬렉션 (컬렉션 이름에 _image_ 추가)
        candidates_image = []
        if embedding_image:
            try:
                # 컬렉션 이름 형식: h{offerNo}_image_{versionNo} 또는 publicRetina_image_{versionNo}
                if is_admin:
                    image_collection_name = f"publicRetina_image_{version_no}"
                else:
                    image_collection_name = f"h{offer_no}_image_{version_no}"
                search_image_primary = await self.gateway_client.request_search_image(
                    embedding=embedding_image,
                    collection_name=image_collection_name,
                    strategy=retrieval_strategy,
                    parameters=retrieval_param or {}
                )
                candidates_image = search_image_primary.get("result", {}).get("candidateEmbeddings", [])
                
                # USER의 경우 publicRetina 이미지 컬렉션도 추가 검색
                if not is_admin:
                    public_image_collection_name = f"publicRetina_image_{public_version}"
                    public_image_params = dict(retrieval_param or {})
                    public_image_params.setdefault("partition", "public")
                    try:
                        search_image_public = await self.gateway_client.request_search_image(
                            embedding=embedding_image,
                            collection_name=public_image_collection_name,
                            strategy=retrieval_strategy,
                            parameters=public_image_params
                        )
                        candidates_image += search_image_public.get("result", {}).get("candidateEmbeddings", [])
                    except Exception as se:
                        logger.warning("Public image partition search failed or skipped: {}", se)
            except Exception as e:
                logger.warning(f"Image search failed: {str(e)}, continuing without image results")
                candidates_image = []
        
        # 5) Cross-Encoder
        cross_res = await self.gateway_client.request_cross_encoder(
            query=request.query,
            candidate_embeddings=candidates,
            strategy=reranking_strategy,
            parameters=reranking_param or {}
        )
        retrieved_chunks = cross_res.get("result", {}).get("retrievedChunks", [])
        
        # 5-1) Cross-Encoder Image - 같은 방식으로 candidates_image 전달
        retrieved_chunks_image = []
        if candidates_image:
            try:
                cross_image_res = await self.gateway_client.request_cross_encoder_image(
                    query=request.query,
                    candidate_embeddings=candidates_image,
                    strategy=reranking_strategy,
                    parameters=reranking_param or {}
                )
                retrieved_chunks_image = cross_image_res.get("result", {}).get("retrievedChunks", [])
            except Exception as e:
                logger.warning(f"Image cross-encoder failed: {str(e)}, continuing without image reranking")
                retrieved_chunks_image = []

        # 6) Generation (스트리밍)
        # text와 image 결과를 따로 전달 (generation에서 구분 가능하도록)
        gen_params = dict(generation_param or {})
        try:
            up = (user_prompting_param or {}).get("content")
            sp = (system_prompting_param or {}).get("content")
            if isinstance(up, str) and up:
                gen_params["userPrompt"] = up
            if isinstance(sp, str) and sp:
                gen_params["systemPrompt"] = sp
        except Exception:
            pass
        gen_params.update({
            "sessionNo": request.sessionNo,
            "userNo": user_no,
            "llmNo": request.llmNo
        })
        
        # 스트리밍 응답 반환
        async for chunk in self.gateway_client.request_generation_stream(
            query=request.query,
            retrieved_chunks=retrieved_chunks,  # text 검색 결과
            retrieved_chunks_image=retrieved_chunks_image if retrieved_chunks_image else None,  # image 검색 결과 (별도 전달)
            strategy=generation_strategy,
            parameters=gen_params,
            extra_headers={
                "x-user-role": x_user_role,
                "x-user-uuid": x_user_uuid,
            }
        ):
            yield chunk

