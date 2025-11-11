from .base import BaseGenerationStrategy
from typing import Dict, Any, List, Optional
from loguru import logger
import os
import time
import httpx

# ✅ LangChain - Ollama 통합
from langchain_ollama import ChatOllama

# ✅ LangChain Core (LCEL 기반)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.documents import Document

# ✅ LangChain Chains (Retrieval + Document Combination)
from langchain_classic.chains.retrieval import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

class Ollama(BaseGenerationStrategy):
    """
    ✅ LangChain 1.x 구조 기반 Ollama 답변 생성 전략
    - RetrievalQA / ConversationalRetrievalChain / load_qa_chain 삭제됨
    - 대신 create_retrieval_chain + create_stuff_documents_chain + RunnableWithMessageHistory 사용
    """

    def __init__(self, parameters: Dict[Any, Any] = None):
        super().__init__(parameters)

        # ✅ 설정값 로드
        self.model_name = self.parameters.get("model_name", "qwen3-vl:8b")
        self.base_url = self.parameters.get("base_url", "https://yo4z0wke606i0e-11434.proxy.runpod.net/")
        self.temperature = self.parameters.get("temperature", 0.1)

        logger.info(f"[Ollama] Initializing LLM: {self.model_name} at {self.base_url}")

        try:
            self.llm = ChatOllama(
                model=self.model_name,
                base_url=self.base_url,
                temperature=self.temperature
            )
            logger.info("[Ollama] LLM initialized successfully")
        except Exception as e:
            sleep_msg = str(e)
            logger.error(f"[Ollama] Failed to initialize LLM: {sleep_msg}")
            raise

    def _init_prompt_template(self, include_history: bool = False):
        " LCEL용 ChatPromptTemplate 생성 (context, question 필수)"
        use_strict_unknown = self.parameters.get("use_strict_unknown", False)
        unknown_clause = (
            "If you don't know the answer, just say that you don't know, don't make up an answer.\n\n"
            if use_strict_unknown else ""
        )
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

        try:
            logger.info(f"[Ollama] systemPrompt: {system_prompt[:200]}")
            logger.info(f"[Ollama] userPrompt: {user_prompt[:200]}")
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
            f"[Ollama] Generating answer for query: {query[:50]}... with {len(retrieved_chunks)} chunks, memory={memory is not None}"
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
                    doc_meta["metadata"] = {"FILE_NAME": file_name}
                documents.append(Document(page_content=text, metadata=doc_meta))

            # Allow zero-doc scenario (LLM will answer with empty context)

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
                    logger.info(f"[Ollama] Fetching presigned URL: {url}")
                    try:
                        with httpx.Client(timeout=3600.0, follow_redirects=True) as client:
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
                                logger.warning(f"[Ollama] Presigned URL not resolved for {file_no}")
                                return ""
                            logger.info("presigned URL fetched")
                            logger.info(f"presigned URL: {presigned_url}")
                            return presigned_url
                    except Exception as e:
                        logger.warning(f"[Ollama] presigned fetch failed for {file_no}: {e}")
                        return ""
                for doc in source_documents:
                    text_value = get_val(doc, 'page_content', None) or get_val(doc, 'text', '') or ''
                    meta = get_val(doc, 'metadata', {}) or {}
                    inner = meta.get('metadata', {}) if isinstance(meta.get('metadata', {}), dict) else {}
                    file_no = meta.get('file_no') or meta.get('FILE_NO') or inner.get('FILE_NO') or inner.get('file_no')
                    file_name = inner.get('FILE_NAME') or meta.get('file_name') or ''
                    base_name = str(file_name).replace('\\', '/').split('/')[-1] if file_name else ''
                    name_wo_ext = base_name.rsplit('.', 1)[0] if '.' in base_name else base_name
                    file_ext = base_name.rsplit('.', 1)[-1].lower() if '.' in base_name else ''
                    page_value = get_val(doc, 'page', meta.get('page', 1))
                    try:
                        page_number = int(page_value)
                    except Exception:
                        page_number = 1
                    download_url = _fetch_presigned(str(file_no)) if file_no else ''
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
                logger.info("[Ollama] Using create_retrieval_chain with memory")
                # 간결한 history 추출
                history_messages = []
                if hasattr(memory, 'chat_memory') and hasattr(memory.chat_memory, 'messages'):
                    msgs = memory.chat_memory.messages
                    history_messages = msgs[-10:] if len(msgs) > 10 else msgs

                result = retrieval_chain.invoke({
                    "input": query,
                    "chat_history": history_messages
                })

                answer = (
                    (result.get("answer") if isinstance(result, dict) else None)
                    or getattr(result, "content", None)
                    or (str(result) if result else "")
                )

                # 응답 시간 계산
                response_time_ms = int((time.time() * 1000) - response_start_time)

                # Build citations and pending AI payload (tokens, latency, model)
                citations = build_citations(documents)
                references = build_references_from_documents(documents)
                from app.core.memory_manager import get_memory_manager

                input_tokens = output_tokens = total_tokens = None
                try:
                    usage = result.response_metadata.get('usage', {})
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
                    logger.debug(f"[Ollama] Successfully saved context to memory")
                except Exception as save_error:
                    logger.warning(f"[Ollama] Failed to save context: {save_error}")

            else:
                logger.info("[Ollama] Using create_retrieval_chain (no memory)")
                response_start_time = time.time() * 1000  # milliseconds
                # create_retrieval_chain은 "input" 키를 기대하며, context는 자동으로 제공됨
                result = retrieval_chain.invoke({"input": query})
                answer = result.get("answer", "")
                citations = build_citations(documents)
                # 문서 존재 여부와 관계없이 빈 context로도 진행

            logger.info(f"[Ollama] Answer generated. Length: {len(answer)}")

            return {
                "query": query,
                "answer": answer,
                "citations": citations,
                "contexts_used": len(citations),
                "strategy": "ollama",
                "parameters": self.parameters,
            }

        except Exception as e:
            logger.error(f"[Ollama] Error during generation: {str(e)}")
            raise
