from .base import BaseGenerationStrategy
from typing import Dict, Any, List, Optional, AsyncIterator
from loguru import logger
import os
import time
import httpx
import uuid
import json
import asyncio
import queue
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import text
from app.core.database import SessionLocal
from app.core.settings import settings
from app.service.history_stream_service import get_history_stream_service

# ✅ OpenAI LLM (LangChain 전용 Wrapper)
from langchain_openai import ChatOpenAI

# ✅ LangChain Core (LCEL 기반 구성 요소)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document
from langchain_core.runnables.history import RunnableWithMessageHistory

# ✅ LangChain Chains (Retrieval + Combination)
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain


class Openai(BaseGenerationStrategy):
    """
    ✅ LangChain 1.x 구조 기반 OpenAI 답변 생성 전략
    - RetrievalQA / ConversationalRetrievalChain / load_qa_chain 삭제됨
    - 대신 create_retrieval_chain + create_stuff_documents_chain + RunnableWithMessageHistory 사용
    """

    def __init__(self, parameters: Dict[Any, Any] = None):
        super().__init__(parameters)

        # 파라미터에서 설정값 가져오기
        self.model_name = self.parameters.get("model_name", "gpt-4o")
        self.temperature = self.parameters.get("temperature", 0.1)

        # OPENAI API 키 초기화 (우선순위: 파라미터 → 환경변수 → 설정 파일)
        self.openai_api_key: Optional[str] = (
            str(self.parameters.get("openai_api_key") or "").strip()
            or str(self.parameters.get("apiKey") or "").strip()
            or str(os.getenv("OPENAI_API_KEY") or "").strip()
            or str(getattr(settings, "openai_api_key", "") or "").strip()
        ) or None
        
        # 파라미터에서 llmNo와 userNo 가져오기
        llm_no = self.parameters.get("llmNo") or self.parameters.get("llm_no")
        user_no = self.parameters.get("userNo") or self.parameters.get("user_no")
        self.llm_no = llm_no
        self.user_no = user_no

        # llmNo와 userNo가 있으면 DB에서 API_KEY 조회
        if llm_no and user_no:
            try:
                logger.info(f"[OpenAI] Fetching API_KEY from DB: llmNo={llm_no}, userNo={user_no}")
                api_key = self._fetch_api_key_from_db(llm_no, user_no)
                if api_key:
                    self.openai_api_key = api_key
                    logger.info("[OpenAI] API_KEY fetched from DB successfully")
                else:
                    logger.warning(f"[OpenAI] API_KEY not found in DB for llmNo={llm_no}, userNo={user_no}, using fallback")
            except Exception as e:
                logger.warning(f"[OpenAI] Failed to fetch API_KEY from DB: {str(e)}, using fallback")

        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set in environment, parameters, or database")

        logger.info(f"[OpenAI] Initializing LLM: {self.model_name}")

        try:
            self.llm = ChatOpenAI(
                openai_api_key=self.openai_api_key,
                model_name=self.model_name,
                temperature=self.temperature
            )
            logger.info("[OpenAI] LLM initialized successfully")
        except Exception as e:
            logger.error(f"[OpenAI] Failed to initialize LLM: {str(e)}")
            raise

    def _fetch_api_key_from_db(self, llm_no: str, user_no: str) -> Optional[str]:
        """DB에서 STRATEGY_NO(=llm_no)와 USER_NO로 API_KEY 조회"""
        session = SessionLocal()
        try:
            # STRATEGY_NO에 LLM_NO를, USER_NO에 USER_NO를 넣어서 조회
            stmt = text(
                "SELECT `API_KEY` "
                "FROM `LLM_KEY` "
                "WHERE `STRATEGY_NO` = UUID_TO_BIN(:llm_no) "
                "AND `USER_NO` = UUID_TO_BIN(:user_no) "
                "LIMIT 1"
            )
            result = session.execute(stmt, {"llm_no": llm_no, "user_no": user_no})
            row = result.first()
            if row:
                api_key = row[0] if isinstance(row, tuple) else getattr(row, "API_KEY", None)
                return api_key
            return None
        except Exception as e:
            logger.error(f"[OpenAI] Database query error: {str(e)}")
            raise
        finally:
            session.close()

    def _init_prompt_template(self, include_history: bool = False):
        """✅ LCEL용 ChatPromptTemplate 생성 (context, question 필수)"""
        use_strict_unknown = self.parameters.get("use_strict_unknown", False)
        unknown_clause = (
            "If you don't know the answer, just say that you don't know, don't make up an answer.\n\n"
            if use_strict_unknown else ""
        )
        # Allow override via systemPrompt/userPrompt ({{query}}/{{docs}} → {input}/{context})
        system_prompt = str(self.parameters.get("systemPrompt", "")) or None
        user_prompt = str(self.parameters.get("userPrompt", "")) or None
        def normalize(p: str) -> str:
            return p.replace("{{query}}", "{input}").replace("{{docs}}", "{context}")
        if system_prompt:
            system_prompt = unknown_clause + normalize(system_prompt)
        else:
            system_prompt = unknown_clause + "Use the provided context to answer the user's question accurately."
        if not user_prompt:
            user_prompt = "Context:\n{context}\n\nQuestion: {input}"
        else:
            user_prompt = normalize(user_prompt)

        # Log effective prompts (truncated)
        try:
            logger.info(f"[OpenAI] systemPrompt: {(system_prompt or '')[:200]}")
            logger.info(f"[OpenAI] userPrompt: {(user_prompt or '')[:200]}")
        except Exception:
            pass
        if include_history:
            return ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", user_prompt)
            ])
        else:
            return ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("human", user_prompt)
            ])
    
    def generate(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        memory=None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_headers: Optional[Dict[str, str]] = None
    ) -> Dict[Any, Any]:
        """
        ✅ LangChain 1.x 구조에 맞는 답변 생성
        - memory가 있으면 RunnableWithMessageHistory 사용
        - 없으면 create_stuff_documents_chain + create_retrieval_chain 조합
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        logger.info(
            f"[OpenAI] Generating answer for query: {query[:50]}... with {len(retrieved_chunks)} chunks, memory={memory is not None}"
        )

        try:
            # ✅ retrieved_chunks → Document 변환 (duck-typing 기반 간소화, 예외 제거)
            def get_val(obj, key, default=None):
                val = getattr(obj, key, None)
                if val is not None:
                    return val
                getter = getattr(obj, 'get', None)
                return getter(key, default) if callable(getter) else default

            documents: List[Document] = []
            for index, chunk in enumerate(retrieved_chunks):
                text = get_val(chunk, 'page_content', None) or get_val(chunk, 'text', '') or ''
                meta = get_val(chunk, 'metadata', {}) or {}
                page_value = get_val(chunk, 'page', None)
                chunk_id_value = get_val(chunk, 'chunk_id', None)
                score_value = get_val(chunk, 'score', None)
                file_no = get_val(chunk, 'fileNo', None)
                file_name = get_val(chunk, 'fileName', None)

                page_number = int((page_value if page_value is not None else meta.get('page', 1)) or 1)
                chunk_identifier = int((chunk_id_value if chunk_id_value is not None else meta.get('chunk_id', index)) or index)
                score_number = float((score_value if score_value is not None else meta.get('score', 0.0)) or 0.0)

                doc_meta = {"page": page_number, "chunk_id": chunk_identifier, "score": score_number}
                if file_no:
                    doc_meta["file_no"] = file_no
                if file_name:
                    # also nest like milvus row
                    doc_meta["metadata"] = {"FILE_NAME": file_name}
                documents.append(Document(page_content=text, metadata=doc_meta))

            if not documents:
                logger.warning("[OpenAI] No documents retrieved")
                try:
                    history_stream_service = get_history_stream_service()
                    history_stream_service.append_error_event(
                        error_code="NO_DOCUMENTS",
                        message="No documents retrieved for query",
                        error_type="RESPONSE",
                        user_id=str(self.user_no or user_id) if (self.user_no or user_id) else None,
                        session_id=str(session_id) if session_id else None,
                        llm_no=self.llm_no,
                        query=query,
                    )
                except Exception as stream_error:
                    logger.warning(f"[OpenAI] Failed to append error event to Redis stream: {stream_error}")
                return {
                    "query": query,
                    "answer": "I don't have enough information to answer this question.",
                    "citations": [],
                    "contexts_used": 0,
                    "strategy": "openAI",
                    "parameters": self.parameters,
                }

            prompt = self._init_prompt_template(include_history=bool(memory))
            
            combine_chain = create_stuff_documents_chain(self.llm, prompt)

            # ✅ Static retriever (이미 가져온 문서 사용)
            from app.core.retriever import StaticDocumentRetriever
            retriever = StaticDocumentRetriever(documents=documents)

            retrieval_chain = create_retrieval_chain(retriever, combine_chain)

            def build_citations(source_documents: List[Any]) -> List[Dict[str, Any]]:
                items: List[Dict[str, Any]] = []
                for index, doc in enumerate(source_documents):
                    text_value = get_val(doc, 'page_content', None) or get_val(doc, 'text', '') or ''
                    meta = get_val(doc, 'metadata', {}) or {}
                    page_value = get_val(doc, 'page', meta.get('page', 1))
                    chunk_id_value = get_val(doc, 'chunk_id', meta.get('chunk_id', index))
                    score_value = get_val(doc, 'score', meta.get('score', 0.0))
                    page_number = int(page_value)
                    chunk_identifier = int(chunk_id_value)
                    score_number = float(score_value)
                    items.append({"text": str(text_value), "page": page_number, "chunk_id": chunk_identifier, "score": score_number})
                return items

            def build_references_from_documents(source_documents: List[Any]) -> List[Dict[str, Any]]:
                refs: List[Dict[str, Any]] = []
                def _fetch_presigned(file_no: str) -> str:
                    if not file_no:
                        return ""
                    # Internal backend URL
                    url = f"http://hebees-python-backend:8000/api/v1/files/{file_no}/presigned"
                    logger.info(f"[OpenAI] Fetching presigned URL: {url}")
                    try:
                        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                            # Forward role/uuid headers only (internal communication)
                            headers = {}
                            if request_headers:
                                if request_headers.get("x-user-uuid"):
                                    headers["x-user-uuid"] = request_headers.get("x-user-uuid")
                                if request_headers.get("x-user-role"):
                                    headers["x-user-role"] = request_headers.get("x-user-role")
                            r = client.get(url, headers=headers)
                            r.raise_for_status()
                            presigned_url = ""
                            try:
                                data = r.json()
                                presigned_url = (data.get("result", {}).get("data", {}) or {}).get("url") or data.get("url") or ""
                            except Exception:
                                presigned_url = r.text.strip().strip('"')
                            if not presigned_url:
                                logger.warning(f"[OpenAI] Presigned URL not resolved for {file_no}")
                                return ""
                            logger.info("presigned URL fetched")
                            logger.info(f"presigned URL: {presigned_url}")
                            return presigned_url
                    except Exception as e:
                        logger.warning(f"[OpenAI] presigned fetch failed for {file_no}: {e}")
                        return ""
                for doc in source_documents:
                    text_value = get_val(doc, 'page_content', None) or get_val(doc, 'text', '') or ''
                    meta = get_val(doc, 'metadata', {}) or {}
                    inner = meta.get('metadata', {}) if isinstance(meta.get('metadata', {}), dict) else {}
                    file_no = meta.get('file_no') or meta.get('FILE_NO') or inner.get('FILE_NO') or inner.get('file_no')
                    file_name = inner.get('FILE_NAME') or meta.get('file_name') or ""
                    title = str(file_name) if file_name else ""
                    base_name = title.replace('\\', '/').split('/')[-1] if title else ""
                    name_wo_ext = base_name.rsplit('.', 1)[0] if '.' in base_name else base_name
                    file_ext = base_name.rsplit('.', 1)[-1].lower() if '.' in base_name else ""
                    page_value = get_val(doc, 'page', meta.get('page', 1))
                    try:
                        page_number = int(page_value)
                    except Exception:
                        page_number = 1
                    download_url = _fetch_presigned(str(file_no)) if file_no else ""
                    refs.append({
                        "fileNo": str(file_no) if file_no else "",
                        "name": base_name,            # swap: store full filename with extension
                        "title": name_wo_ext,         # swap: store filename without extension
                        "type": file_ext,
                        "index": page_number,
                        "downloadUrl": download_url,
                        "snippet": str(text_value),
                    })
                return refs

            # ✅ 메모리 지원 여부에 따라 분기
            # 응답 시간 측정 시작
            response_start_time = time.time() * 1000  # milliseconds
            citations: List[Dict[str, Any]] = []
            
            if memory is not None:
                logger.info("[OpenAI] Using create_retrieval_chain with memory")
                # 간결한 history 추출: chat_memory.messages가 있으면 최근 10개, 없으면 빈 리스트
                history_messages = []
                if hasattr(memory, 'chat_memory') and hasattr(memory.chat_memory, 'messages'):
                    msgs = memory.chat_memory.messages
                    history_messages = msgs[-10:] if len(msgs) > 10 else msgs

                # 프롬프트 실행
                result = retrieval_chain.invoke({
                    "input": query,
                    "chat_history": history_messages
                })

                # answer만 단순 추출
                answer = (
                    (result.get("answer") if isinstance(result, dict) else None)
                    or getattr(result, "content", None)
                    or (str(result) if result else "")
                )
                if not answer:
                    logger.error(f"[OpenAI] Could not extract answer from result. Result type: {type(result)}, Result: {result}")
                    raise ValueError(f"Could not extract answer from retrieval chain result. Result type: {type(result)}")
                logger.debug(f"[OpenAI] Extracted answer length: {len(answer)}")
                
                # 응답 시간 계산
                response_time_ms = int((time.time() * 1000) - response_start_time)

                # Build citations and pending AI payload (tokens, latency, model)
                citations = build_citations(documents)
                references = build_references_from_documents(documents)
                from app.core.memory_manager import get_memory_manager

                input_tokens = output_tokens = total_tokens = None
                try:
                    result_usage = result.get('usage')  # type: ignore[assignment]
                except AttributeError:
                    result_usage = None
                if isinstance(result_usage, dict):
                    input_tokens = result_usage.get('prompt_tokens')
                    output_tokens = result_usage.get('completion_tokens')
                    total_tokens = result_usage.get('total_tokens')
                else:
                    try:
                        usage = result.response_metadata.get('token_usage', {})
                        if usage:
                            input_tokens = usage.get('prompt_tokens')
                            output_tokens = usage.get('completion_tokens')
                            total_tokens = usage.get('total_tokens')
                    except Exception:
                        pass

                get_memory_manager().set_pending_ai_payload(
                    user_id,
                    session_id,
                    references=references,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    response_time_ms=response_time_ms,
                )

                # 메모리에 대화 저장
                # ConversationSummaryBufferMemory는 output_key="answer"로 설정되어 있으므로
                # save_context는 내부적으로 output_key를 사용하여 출력을 찾음
                # 따라서 {"answer": answer} 형식 사용
                try:
                    memory.save_context({"input": query}, {"answer": answer})
                    logger.debug(f"[OpenAI] Successfully saved context to memory")
                except Exception as save_error:
                    logger.warning(f"[OpenAI] Failed to save context: {save_error}")
                
                # citations already built above
            else:
                logger.info("[OpenAI] Using create_retrieval_chain (no memory)")
                response_start_time = time.time() * 1000  # milliseconds
                # create_retrieval_chain은 "input" 키를 기대하며, context는 자동으로 제공됨
                try:
                    result = retrieval_chain.invoke({"input": query})
                    answer = result.get("answer", "")
                except Exception as e:
                    logger.error(f"[OpenAI] Error invoking retrieval chain: {e}")
                    raise
                
                citations = build_citations(documents)

                # 메모리를 사용하지 않는 경우에는 MongoDB에 수동 저장하지 않음

            logger.info(f"[OpenAI] Answer generated. Length: {len(answer)}")


            if not citations:
                citations = build_citations(documents)

            return {
                "query": query,
                "answer": answer,
                "citations": citations,
                "contexts_used": len(citations),
                "strategy": "openAI",
                "parameters": self.parameters,
            }

        except Exception as e:
            logger.error(f"[OpenAI] Error during generation: {str(e)}")
            try:
                history_stream_service = get_history_stream_service()
                history_stream_service.append_error_event(
                    error_code="GENERATION_EXCEPTION",
                    message=str(e),
                    error_type="SYSTEM",
                    user_id=str(self.user_no or user_id) if (self.user_no or user_id) else None,
                    session_id=str(session_id) if session_id else None,
                    llm_no=self.llm_no,
                    query=query,
                )
            except Exception as stream_error:
                logger.warning(f"[OpenAI] Failed to append system error event to Redis stream: {stream_error}")
            raise
    
    async def generate_stream(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        memory=None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_headers: Optional[Dict[str, str]] = None
    ) -> AsyncIterator[str]:
        """
        스트리밍 방식으로 답변 생성
        - LLM에서 실시간으로 토큰을 받아서 전달
        - 맨 처음에 init 메시지 전송 (messageNo, role, createdAt)
        - 이후 각 토큰을 update 메시지로 전송
        - 완료 후 MongoDB에 저장
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        logger.info(
            f"[OpenAI] Generating stream answer for query: {query[:50]}... with {len(retrieved_chunks)} chunks, memory={memory is not None}"
        )

        try:
            # retrieved_chunks → Document 변환 (generate와 동일)
            def get_val(obj, key, default=None):
                val = getattr(obj, key, None)
                if val is not None:
                    return val
                getter = getattr(obj, 'get', None)
                return getter(key, default) if callable(getter) else default
            
            documents: List[Document] = []
            for index, chunk in enumerate(retrieved_chunks):
                text = get_val(chunk, 'page_content', None) or get_val(chunk, 'text', '') or ''
                meta = get_val(chunk, 'metadata', {}) or {}
                page_value = get_val(chunk, 'page', None)
                chunk_id_value = get_val(chunk, 'chunk_id', None)
                score_value = get_val(chunk, 'score', None)
                file_no = get_val(chunk, 'fileNo', None)
                file_name = get_val(chunk, 'fileName', None)

                page_number = int((page_value if page_value is not None else meta.get('page', 1)) or 1)
                chunk_identifier = int((chunk_id_value if chunk_id_value is not None else meta.get('chunk_id', index)) or index)
                score_number = float((score_value if score_value is not None else meta.get('score', 0.0)) or 0.0)

                doc_meta = {"page": page_number, "chunk_id": chunk_identifier, "score": score_number}
                if file_no:
                    doc_meta["file_no"] = file_no
                if file_name:
                    doc_meta["metadata"] = {"FILE_NAME": file_name}
                documents.append(Document(page_content=text, metadata=doc_meta))

            # documents가 없을 때 처리
            if not documents:
                logger.warning("[OpenAI] No documents retrieved for stream")
                try:
                    history_stream_service = get_history_stream_service()
                    history_stream_service.append_error_event(
                        error_code="NO_DOCUMENTS",
                        message="No documents retrieved for query",
                        error_type="RESPONSE",
                        user_id=str(self.user_no or user_id) if (self.user_no or user_id) else None,
                        session_id=str(session_id) if session_id else None,
                        llm_no=self.llm_no,
                        query=query,
                    )
                except Exception as stream_error:
                    logger.warning(f"[OpenAI] Failed to append error event to Redis stream: {stream_error}")
                
                # 빈 답변으로 init 메시지 전송
                message_no = uuid.uuid4()
                created_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
                init_message = {
                    "messageNo": str(message_no),
                    "role": "ai",
                    "createdAt": created_at,
                    "references": []  # documents가 없으므로 빈 references
                }
                yield f"event: init\ndata: {json.dumps(init_message, ensure_ascii=False)}\n\n"
                
                # 빈 답변 전송
                update_message = {
                    "content": "I don't have enough information to answer this question."
                }
                yield f"event: update\ndata: {json.dumps(update_message, ensure_ascii=False)}\n\n"
                return

            prompt = self._init_prompt_template(include_history=bool(memory))
            combine_chain = create_stuff_documents_chain(self.llm, prompt)

            from app.core.retriever import StaticDocumentRetriever
            retriever = StaticDocumentRetriever(documents=documents)
            retrieval_chain = create_retrieval_chain(retriever, combine_chain)

            # 메모리 관리자 가져오기
            from app.core.memory_manager import get_memory_manager
            memory_manager = get_memory_manager()
            
            # MESSAGE_NO 미리 생성 및 createdAt 생성
            message_no = uuid.uuid4()
            created_at = datetime.now(ZoneInfo("Asia/Seoul")).isoformat()
            
            # references 빌드 함수 (generate와 동일)
            def build_references_from_documents(source_docs: List[Any]) -> List[Dict[str, Any]]:
                refs: List[Dict[str, Any]] = []
                def _fetch_presigned(file_no: str) -> str:
                    if not file_no:
                        return ""
                    url = f"http://hebees-python-backend:8000/api/v1/files/{file_no}/presigned"
                    try:
                        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
                            headers = {}
                            if request_headers:
                                if request_headers.get("x-user-uuid"):
                                    headers["x-user-uuid"] = request_headers.get("x-user-uuid")
                                if request_headers.get("x-user-role"):
                                    headers["x-user-role"] = request_headers.get("x-user-role")
                            r = client.get(url, headers=headers)
                            r.raise_for_status()
                            presigned_url = ""
                            try:
                                data = r.json()
                                presigned_url = (data.get("result", {}).get("data", {}) or {}).get("url") or data.get("url") or ""
                            except Exception:
                                presigned_url = r.text.strip().strip('"')
                            return presigned_url if presigned_url else ""
                    except Exception as e:
                        logger.warning(f"[OpenAI] presigned fetch failed for {file_no}: {e}")
                        return ""
                
                for doc in source_docs:
                    text_value = get_val(doc, 'page_content', None) or get_val(doc, 'text', '') or ''
                    meta = get_val(doc, 'metadata', {}) or {}
                    inner = meta.get('metadata', {}) if isinstance(meta.get('metadata', {}), dict) else {}
                    file_no = meta.get('file_no') or meta.get('FILE_NO') or inner.get('FILE_NO') or inner.get('file_no')
                    file_name = inner.get('FILE_NAME') or meta.get('file_name') or ""
                    title = str(file_name) if file_name else ""
                    base_name = title.replace('\\', '/').split('/')[-1] if title else ""
                    name_wo_ext = base_name.rsplit('.', 1)[0] if '.' in base_name else base_name
                    file_ext = base_name.rsplit('.', 1)[-1].lower() if '.' in base_name else ""
                    page_value = get_val(doc, 'page', meta.get('page', 1))
                    try:
                        page_number = int(page_value)
                    except Exception:
                        page_number = 1
                    download_url = _fetch_presigned(str(file_no)) if file_no else ""
                    refs.append({
                        "fileNo": str(file_no) if file_no else "",
                        "name": base_name,
                        "title": name_wo_ext,
                        "type": file_ext,
                        "index": page_number,
                        "downloadUrl": download_url,
                        "snippet": str(text_value),
                    })
                return refs

            # references 미리 빌드 (event: init에 포함하기 위해)
            initial_references = build_references_from_documents(documents)
            
            # 맨 처음에 init 메시지 전송
            init_message = {
                "messageNo": str(message_no),
                "role": "ai",
                "createdAt": created_at,
                "references": initial_references
            }
            yield f"event: init\ndata: {json.dumps(init_message, ensure_ascii=False)}\n\n"
            
            # 응답 시간 측정 시작
            response_start_time = time.time() * 1000
            full_answer = ""
            source_documents = documents  # 기본값으로 documents 사용

            # 스트리밍 시작
            if memory is not None:
                logger.info("[OpenAI] Using create_retrieval_chain with memory (stream)")
                history_messages = []
                if hasattr(memory, 'chat_memory') and hasattr(memory.chat_memory, 'messages'):
                    msgs = memory.chat_memory.messages
                    history_messages = msgs[-10:] if len(msgs) > 10 else msgs

                # retrieval_chain.stream() 사용
                stream = retrieval_chain.stream({
                    "input": query,
                    "chat_history": history_messages
                })
            else:
                logger.info("[OpenAI] Using create_retrieval_chain (no memory, stream)")
                stream = retrieval_chain.stream({"input": query})

            # 스트리밍 처리 (동기 이터레이터를 async로 변환)
            # 큐를 사용하여 실시간 스트리밍 구현
            stream_queue = queue.Queue()
            stream_done = False
            stream_error = None
            
            def process_stream():
                """별도 스레드에서 스트림 처리"""
                nonlocal stream_done, stream_error
                try:
                    for chunk in stream:
                        stream_queue.put(("chunk", chunk))
                    stream_queue.put(("done", None))
                except Exception as e:
                    stream_error = e
                    stream_queue.put(("error", str(e)))
            
            # 별도 스레드에서 스트림 시작
            stream_task = asyncio.create_task(asyncio.to_thread(process_stream))
            
            # 스트리밍 처리 (큐에서 실시간으로 읽기)
            while True:
                try:
                    # 큐에서 데이터 가져오기 (타임아웃 설정)
                    try:
                        msg_type, chunk = stream_queue.get(timeout=0.1)
                    except queue.Empty:
                        # 큐가 비어있으면 잠시 대기 후 다시 시도
                        await asyncio.sleep(0.01)
                        continue
                    
                    if msg_type == "done":
                        break
                    elif msg_type == "error":
                        raise Exception(f"Stream error: {chunk}")
                    
                    # chunk 처리
                    if isinstance(chunk, dict):
                        answer_chunk = chunk.get("answer", "")
                        if answer_chunk:
                            full_answer += answer_chunk
                            # update 메시지로 전송 (JSON 이스케이프 처리)
                            update_message = {
                                "content": answer_chunk
                            }
                            yield f"event: update\ndata: {json.dumps(update_message, ensure_ascii=False)}\n\n"
                        
                        # context 문서 수집 (마지막에 references 빌드용)
                        if "context" in chunk:
                            context_docs = chunk.get("context", [])
                            if context_docs:
                                source_documents = context_docs
                    else:
                        # 단순 문자열인 경우
                        chunk_str = str(chunk)
                        full_answer += chunk_str
                        update_message = {
                            "content": chunk_str
                        }
                        yield f"event: update\ndata: {json.dumps(update_message, ensure_ascii=False)}\n\n"
                except Exception as e:
                    logger.error(f"[OpenAI] Error processing stream chunk: {e}", exc_info=True)
                    if stream_error:
                        raise stream_error
                    raise
            
            # 스트림 태스크 완료 대기
            await stream_task
            
            # 스트리밍 완료 후 처리
            response_time_ms = int((time.time() * 1000) - response_start_time)
            
            # references 빌드
            references = build_references_from_documents(source_documents)
            
            # 토큰 사용량 추출 (stream에서는 직접 얻기 어려움)
            input_tokens = output_tokens = total_tokens = None
            
            # MongoDB에 저장
            if user_id and session_id:
                try:
                    # pending payload 설정
                    memory_manager.set_pending_ai_payload(
                        user_id,
                        session_id,
                        references=references,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens,
                        response_time_ms=response_time_ms,
                    )
                    
                    # 메시지 저장
                    memory_manager.save_custom_message(
                        user_id=user_id,
                        session_id=session_id,
                        role="ai",
                        content=full_answer,
                        llm_no=self.parameters.get("llmNo"),
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens,
                        response_time_ms=response_time_ms,
                        references=references,
                        message_no=message_no,
                    )
                    
                    # memory에 저장
                    if memory:
                        try:
                            memory.save_context({"input": query}, {"answer": full_answer})
                            logger.debug(f"[OpenAI] Successfully saved context to memory")
                        except Exception as save_error:
                            logger.warning(f"[OpenAI] Failed to save context: {save_error}")
                    
                    logger.info(f"[OpenAI] Stream answer completed. Length: {len(full_answer)}")
                    
                except Exception as e:
                    logger.error(f"[OpenAI] Failed to save stream result to MongoDB: {e}", exc_info=True)
            else:
                logger.info(f"[OpenAI] Stream answer completed (no user_id/session_id). Length: {len(full_answer)}")

        except Exception as e:
            logger.error(f"[OpenAI] Error during stream generation: {str(e)}", exc_info=True)
            try:
                history_stream_service = get_history_stream_service()
                history_stream_service.append_error_event(
                    error_code="GENERATION_EXCEPTION",
                    message=str(e),
                    error_type="SYSTEM",
                    user_id=str(self.user_no or user_id) if (self.user_no or user_id) else None,
                    session_id=str(session_id) if session_id else None,
                    llm_no=self.llm_no,
                    query=query,
                )
            except Exception as stream_error:
                logger.warning(f"[OpenAI] Failed to append system error event to Redis stream: {stream_error}")
            error_message = {
                "message": str(e)
            }
            yield f"event: error\ndata: {json.dumps(error_message, ensure_ascii=False)}\n\n"
            raise

