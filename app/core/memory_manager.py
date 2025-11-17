"""
UserMemoryManager - 사용자별 Memory 관리자
"""

import uuid
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
from zoneinfo import ZoneInfo
from loguru import logger
import base64

KST = ZoneInfo("Asia/Seoul")


def _now_kst() -> datetime:
    """현재 KST(Asia/Seoul) 시간 반환."""
    return datetime.now(tz=KST)

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
    PYMONGO_AVAILABLE = True
except ImportError:
    MongoClient = None  # type: ignore[assignment]
    PyMongoError = Exception  # type: ignore[assignment]
    PYMONGO_AVAILABLE = False

try:
    from bson.binary import Binary
    BSON_AVAILABLE = True
except ImportError:
    Binary = None  # type: ignore[assignment]
    BSON_AVAILABLE = False

# ✅ transformers 사용 가능 여부 체크
try:
    from transformers import AutoTokenizer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    AutoTokenizer = None
    TRANSFORMERS_AVAILABLE = False

TRANSFORMERS_AVAILABLE = True
def get_qwen_token_counter() -> Optional[Callable]:
    """
    Qwen 모델용 토큰 카운터 생성
    Ollama qwen3-vl 등 Qwen 계열 모델에 사용
    
    주의: transformers의 경고를 완전히 억제하기 위해 로깅 레벨 조정 및 
    토크나이저 내부 속성을 수정합니다.
    """
    if not TRANSFORMERS_AVAILABLE:
        logger.warning("transformers not available. Cannot create Qwen token counter.")
        return None
    
    try:
        # transformers 로깅 레벨 조정 (경고 억제)
        import logging
        transformers_logger = logging.getLogger("transformers")
        original_level = transformers_logger.level
        transformers_logger.setLevel(logging.ERROR)  # ERROR 이상만 출력
        
        # Qwen 2.5 계열 토크나이저 로드 (Ollama qwen3-vl 대응)
        tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-7B")
        
        # max_length를 매우 큰 값으로 설정하여 토큰 길이 제한 경고 방지
        if hasattr(tokenizer, 'model_max_length'):
            original_max_length = tokenizer.model_max_length
            # 매우 큰 값으로 설정 (실제로는 토큰 수만 세므로 제한이 필요 없음)
            tokenizer.model_max_length = 1_000_000  # 100만 토큰으로 설정
            logger.debug(f"Qwen tokenizer max_length set to {tokenizer.model_max_length} (original: {original_max_length})")
        
        # 토크나이저 내부 속성도 수정 (더 확실한 경고 억제)
        if hasattr(tokenizer, 'tokenizer'):
            # tokenizers 라이브러리의 내부 속성도 수정
            if hasattr(tokenizer.tokenizer, 'model'):
                if hasattr(tokenizer.tokenizer.model, 'max_length'):
                    tokenizer.tokenizer.model.max_length = 1_000_000
        
        # LangChain이 요구하는 token_counter 함수 형태로 반환
        def token_counter(text: str) -> int:
            # 토큰 카운터는 단순히 토큰 수를 세는 것이므로, truncation과 max_length를 명시적으로 설정
            # warnings와 로깅을 완전히 억제하여 경고 메시지 방지
            import warnings
            import os
            
            # 환경 변수로 transformers 경고 비활성화
            os.environ["TOKENIZERS_PARALLELISM"] = "false"
            
            # transformers 로깅 임시 비활성화 (경고 메시지 억제)
            original_log_level = transformers_logger.level
            transformers_logger.setLevel(logging.ERROR)  # ERROR 이상만 출력
            
            try:
                with warnings.catch_warnings():
                    # 모든 경고 무시
                    warnings.simplefilter("ignore")
                    warnings.filterwarnings("ignore", category=UserWarning)
                    warnings.filterwarnings("ignore", message=".*sequence length.*")
                    warnings.filterwarnings("ignore", message=".*max_length.*")
                    warnings.filterwarnings("ignore", message=".*Token indices.*")
                    warnings.filterwarnings("ignore", message=".*longer than.*")
                    
                    # truncation=False, max_length를 매우 큰 값으로 명시적으로 설정
                    # 실제로는 토큰 수만 세므로 truncation이 필요 없음
                    tokens = tokenizer.encode(
                        text, 
                        add_special_tokens=False,
                        truncation=False,
                        max_length=1_000_000,  # 명시적으로 매우 큰 값 설정
                        return_tensors=None  # 리스트로 반환
                    )
                    return len(tokens)
            except Exception as encode_error:
                # 인코딩 실패 시 경고만 로그하고 휴리스틱 사용
                logger.debug(f"Token encoding failed, using heuristic: {encode_error}")
                # 휴리스틱: 대략적인 토큰 수 추정 (한국어 기준 약 4자당 1토큰)
                return max(1, int(len(text) / 4))
            finally:
                # 로깅 레벨 복원
                transformers_logger.setLevel(original_log_level)
        
        logger.debug("Qwen token counter created successfully")
        return token_counter
    except Exception as e:
        logger.warning(f"Failed to create Qwen token counter: {e}")
        return None

# Chat history class moved to a dedicated module to avoid circular imports
try:
    from app.core.custom_chat_history import CustomMongoChatMessageHistory
except Exception:
    CustomMongoChatMessageHistory = None  # type: ignore[assignment]

try:
    # LangChain 1.0.x - langchain-classic에서 import 시도
    from langchain_classic.memory import ConversationSummaryBufferMemory
except ImportError:
    try:
        # LangChain 1.0.x - langchain 패키지에서 시도
        from langchain.memory import ConversationSummaryBufferMemory
    except ImportError:
        try:
            # LangChain 1.0.x alternative paths
            from langchain_core.memory import ConversationSummaryBufferMemory
        except ImportError:
            try:
                # Fallback for older versions
                from langchain.memory import ConversationSummaryBufferMemory
            except ImportError:
                ConversationSummaryBufferMemory = None
                logger.warning(
                    "langchain memory modules not installed. History functionality will be limited. "
                    "Please install: pip install langchain-classic langchain-community"
                )


# (class implementation moved to app.core.custom_chat_history)


class UserMemoryManager:
    """사용자별 Memory 관리자"""

    def __init__(self):
        from app.core.settings import settings
        
        # MongoDB 설정
        self.mongo_enabled = False
        self.mongo_client: Optional[MongoClient] = None  # type: ignore[type-arg]
        self.mongo_db = None
        self.mongo_collection = None
        self.mongo_collection_name = "MESSAGE"

        self.mongo_database = getattr(settings, "mongo_database", None)
        self.mongo_url = getattr(settings, "mongo_url", None)
        self.mongo_connect_timeout_ms = 5000
        self.mongo_server_selection_timeout_ms = 5000

        self._init_mongo_client()

        self._memory_cache = {}  # user_id -> memory 객체
        # Pending references handoff between generator and chat history
        self._pending_references: Dict[str, Optional[List[Dict[str, Any]]]] = {}
        # Request-scoped context provided by router (session_no, user_no, llm_no)
        self._request_contexts: Dict[str, Dict[str, Any]] = {}
        # Pending AI payload (citations, token usage, latency, llm)
        self._pending_ai_payloads: Dict[str, Dict[str, Any]] = {}
        # Token counter (Qwen tokenizer), lazily initialized
        self._token_counter = None
        # Last AI message metadata per user/session
        self._last_ai_message_meta: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _to_uuid_if_possible(value: Any) -> Any:
        """Convert to uuid.UUID when possible, otherwise return original. Accepts uuid.UUID, uuid string, or base64 Binary (RFC-4122)."""
        if value is None:
            return None
        try:
            import uuid as _uuid
            if isinstance(value, _uuid.UUID):
                return value
            # Binary to uuid: assume subtype 3 RFC-4122 bytes; attempt best-effort
            if BSON_AVAILABLE and isinstance(value, Binary):  # type: ignore[arg-type]
                try:
                    u = _uuid.UUID(bytes=bytes(value))
                    return u
                except Exception:
                    return value
            # Try parse uuid string
            try:
                s = str(value).strip()
                u = _uuid.UUID(s)
                return u
            except Exception:
                # Try base64 → bytes → uuid
                try:
                    decoded = base64.b64decode(str(value).strip())
                    u = _uuid.UUID(bytes=decoded)
                    return u
                except Exception:
                    return value
        except Exception:
            return value

    def _ensure_token_counter(self) -> None:
        if self._token_counter is None:
            try:
                self._token_counter = get_qwen_token_counter()
            except Exception:
                self._token_counter = None

    def count_tokens(self, text: str) -> int:
        """Count tokens using Qwen tokenizer when available; fallback to simple heuristic."""
        if not text:
            return 0
        self._ensure_token_counter()
        try:
            if callable(self._token_counter):
                return int(self._token_counter(text))  # type: ignore[misc]
        except Exception:
            pass
        # Fallback heuristic: rough subword estimate
        try:
            return max(1, int(len(text) / 4))
        except Exception:
            return len(text)

    def _init_mongo_client(self) -> None:
        """MongoDB 클라이언트 초기화"""
        if not PYMONGO_AVAILABLE:
            logger.warning("PyMongo not installed. MongoDB persistence disabled.")
            return

        if not self.mongo_url or not self.mongo_database:
            logger.warning("MongoDB configuration missing. Skipping MongoDB initialization.")
            return

        try:
            self.mongo_client = MongoClient(
                self.mongo_url,
                serverSelectionTimeoutMS=self.mongo_server_selection_timeout_ms,
                connectTimeoutMS=self.mongo_connect_timeout_ms,
                uuidRepresentation="javaLegacy",  # use Java legacy (subtype=3, RFC-4122 byte order)
            )
            # 연결 확인
            self.mongo_client.admin.command("ping")

            self.mongo_db = self.mongo_client[self.mongo_database]
            self.mongo_collection = self.mongo_db[self.mongo_collection_name]

            self.mongo_enabled = True
            logger.debug(
                f"MongoDB initialized successfully for collection '{self.mongo_collection_name}'"
            )
        except PyMongoError as error:  # type: ignore[misc]
            logger.error(f"Failed to initialize MongoDB client: {error}")
            self.mongo_client = None
            self.mongo_db = None
            self.mongo_collection = None
            self.mongo_enabled = False

    def get_or_create_memory(
        self,
        user_id: str,
        session_id: str,
        llm=None
    ):
        """사용자별 Memory 객체를 가져오거나 생성 (항상 summary_buffer 전략 사용)"""

        cache_key = f"{user_id}_{session_id}_summary_buffer"

        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        # 새 Memory 객체 생성 (summary_buffer로 고정)
        memory = self._create_memory(llm, user_id, session_id)
        self._memory_cache[cache_key] = memory
        return memory

    def _get_chat_history(self, user_id: str, session_id: str):
        """Custom MongoDB chat_history 반환"""
        if (
            not self.mongo_enabled
            or self.mongo_collection is None
            or self.mongo_client is None
        ):
            logger.warning("MongoDB chat history requested but MongoDB is not initialized.")
            return None

        try:
            return CustomMongoChatMessageHistory(self, user_id, session_id)
        except Exception as error:
            logger.error(f"Failed to create custom MongoDB chat history: {error}")
            return None

    def _set_last_ai_message(self, user_id: str, session_id: str, *, message_no: Any, created_at: Any) -> None:
        key = f"{user_id}:{session_id}"
        # Normalize to string ISO for created_at if possible
        try:
            created_iso = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)
        except Exception:
            created_iso = str(created_at)
        # Normalize message_no to string
        try:
            import uuid as _uuid
            if isinstance(message_no, _uuid.UUID):
                msg_str = str(message_no)
            else:
                msg_str = str(message_no)
        except Exception:
            msg_str = str(message_no)
        self._last_ai_message_meta[key] = {"messageNo": msg_str, "createdAt": created_iso}

    def get_last_ai_message_meta(self, user_id: str, session_id: str) -> Dict[str, Any]:
        return self._last_ai_message_meta.get(f"{user_id}:{session_id}", {})

    def _build_session_filter(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Filter by USER_NO + SESSION_NO (preferred).
        Falls back to legacy SESSION_ID only in legacy cleanup/search paths.
        """
        # Prefer router-provided session_no; else derive deterministic UUID from (user_id, session_id)
        context = self.get_request_context(user_id, session_id)
        provided_session_no = context.get("session_no") if isinstance(context, dict) else None
        if provided_session_no is not None:
            session_no_value = self._to_uuid_if_possible(provided_session_no)
        else:
            session_uuid = self._session_uuid(user_id, session_id)
            session_no_value = self._to_uuid_if_possible(session_uuid) if session_uuid is not None else session_id

        return {
            "USER_NO": self._to_uuid_if_possible(user_id),
            "SESSION_NO": session_no_value,
        }

    def _normalize_references(
        self, references: Optional[List[Dict[str, Any]]]
    ) -> Optional[List[Dict[str, Any]]]:
        if not references:
            return [] if references == [] else None

        normalized: List[Dict[str, Any]] = []
        # If already in target reference schema (has fileNo), pass-through
        try:
            if isinstance(references, list) and references and all(isinstance(r, dict) and ("fileNo" in r) for r in references):
                return references
        except Exception:
            pass
        for reference in references:
            if not isinstance(reference, dict):
                continue

            text_value = reference.get("text", "")
            page_value = reference.get("page", 1)
            chunk_id_value = reference.get("chunk_id", 0)
            score_value = reference.get("score")

            try:
                page_number = int(page_value)
            except (TypeError, ValueError):
                page_number = 1

            try:
                chunk_identifier = int(chunk_id_value)
            except (TypeError, ValueError):
                chunk_identifier = 0

            try:
                score_number = float(score_value) if score_value is not None else None
            except (TypeError, ValueError):
                score_number = None

            normalized.append(
                {
                    "text": str(text_value),
                    "page": page_number,
                    "chunk_id": chunk_identifier,
                    "score": score_number,
                }
            )

        return normalized

    def _session_uuid(self, user_id: str, session_id: str) -> Optional[uuid.UUID]:
        try:
            return uuid.uuid5(uuid.NAMESPACE_URL, f"{user_id}:{session_id}")
        except Exception as error:
            logger.debug(f"Failed to generate session UUID: {error}")
            return None

    def _fetch_custom_messages(self, user_id: str, session_id: str) -> List[Dict[str, Any]]:
        if self.mongo_collection is None:
            return []

        try:
            filter_query = self._build_session_filter(user_id, session_id)
            new_cursor = list(
                self.mongo_collection
                .find(filter_query)
                .sort("CREATED_AT", 1)
            )
            if new_cursor:
                return new_cursor

            # Fallback to legacy schema
            legacy_cursor = self.mongo_collection.find({
                "user_id": user_id,
                "session_id": session_id,
            }).sort("created_at", 1)
            return list(legacy_cursor)
        except PyMongoError as error:  # type: ignore[misc]
            logger.warning(f"Failed to load custom messages from MongoDB: {error}")
            return []

    def set_pending_references(self, user_id: str, session_id: str, references: Optional[List[Dict[str, Any]]]) -> None:
        """Store references temporarily so add_ai_message can attach them when saving via memory.save_context."""
        key = f"{user_id}:{session_id}"
        try:
            self._pending_references[key] = self._normalize_references(references)
        except Exception:
            self._pending_references[key] = None

    def pop_pending_references(self, user_id: str, session_id: str) -> Optional[List[Dict[str, Any]]]:
        key = f"{user_id}:{session_id}"
        return self._pending_references.pop(key, None)

    def set_request_context(self, user_id: str, session_id: str, *, session_no: Optional[Any] = None, user_no: Optional[Any] = None, llm_no: Optional[str] = None) -> None:
        key = f"{user_id}:{session_id}"
        self._request_contexts[key] = {
            "session_no": session_no,
            "user_no": user_no,
            "llm_no": llm_no,
        }

    def get_request_context(self, user_id: str, session_id: str) -> Dict[str, Any]:
        return self._request_contexts.get(f"{user_id}:{session_id}", {})

    def set_pending_ai_payload(
        self,
        user_id: str,
        session_id: str,
        *,
        references: Optional[List[Dict[str, Any]]] = None,
        llm_no: Optional[str] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        response_time_ms: Optional[int] = None,
    ) -> None:
        key = f"{user_id}:{session_id}"
        normalized_refs = self._normalize_references(references)
        # Merge with existing pending payload (do not drop previously set fields)
        existing = self._pending_ai_payloads.get(key, {}) if isinstance(self._pending_ai_payloads.get(key, {}), dict) else {}

        # Coalesce None to 0 for token fields
        def to_int_or_zero(value: Optional[int]) -> int:
            try:
                return 0 if value is None else int(value)
            except Exception:
                return 0

        in_tok = to_int_or_zero(input_tokens) if input_tokens is not None else existing.get("input_tokens", 0)
        out_tok = to_int_or_zero(output_tokens) if output_tokens is not None else existing.get("output_tokens", 0)
        tot_tok = to_int_or_zero(total_tokens) if total_tokens is not None else existing.get("total_tokens", 0)
        if tot_tok == 0:
            tot_tok = (in_tok or 0) + (out_tok or 0)

        merged = dict(existing)
        if normalized_refs is not None:
            merged["references"] = normalized_refs
        if llm_no is not None:
            merged["llm_no"] = llm_no
        merged["input_tokens"] = in_tok
        merged["output_tokens"] = out_tok
        merged["total_tokens"] = tot_tok
        if response_time_ms is not None:
            merged["response_time_ms"] = response_time_ms

        self._pending_ai_payloads[key] = merged

    def pop_pending_ai_payload(self, user_id: str, session_id: str) -> Dict[str, Any]:
        return self._pending_ai_payloads.pop(f"{user_id}:{session_id}", {})

    def _delete_custom_messages(self, user_id: str, session_id: str) -> None:
        if self.mongo_collection is None:
            return

        try:
            filter_query = self._build_session_filter(user_id, session_id)
            self.mongo_collection.delete_many(filter_query)
            # Legacy schema cleanup
            self.mongo_collection.delete_many({
                "user_id": user_id,
                "session_id": session_id,
            })
        except PyMongoError as error:  # type: ignore[misc]
            logger.error(f"Failed to delete messages for user {user_id}: {error}")

    def _create_memory(
        self,
        llm,
        user_id: str,
        session_id: str
    ):
        """Memory 객체 생성 (항상 summary_buffer 전략 사용)"""
        if ConversationSummaryBufferMemory is None:
            logger.error("ConversationSummaryBufferMemory is not available. History will be disabled.")
            return None

        chat_history = self._get_chat_history(user_id, session_id)
        
        # Mongo 연결 실패 시에도 메모리 없이 계속 진행 (인메모리만 사용)
        if chat_history is None:
            logger.warning(f"MongoDB chat history is None for user {user_id}, session {session_id}. Memory will work without persistence (in-memory only).")
        
        if llm is None:
            logger.error(
                f"LLM is None for user {user_id}, cannot create ConversationSummaryBufferMemory"
            )
            return None

        # 기본 max_token_limit 설정
        max_token_limit = 2000

        # token_counter 설정
        # GPT 모델인 경우 tiktoken 사용, 그 외에는 None으로 설정하여 자동 처리
        token_counter = None
        if llm is not None:
            # LLM 모델 이름 확인
            model_name = None
            if hasattr(llm, "model_name"):
                model_name = llm.model_name
            elif hasattr(llm, "model"):
                model_name = llm.model
            elif hasattr(llm, "_model_name"):
                model_name = llm._model_name
            
            # GPT 모델인 경우 tiktoken 사용
            if model_name and "gpt" in str(model_name).lower():
                try:
                    import tiktoken
                    token_counter = tiktoken.get_encoding("cl100k_base")
                    logger.debug(f"Using tiktoken for token counting (model: {model_name})")
                except ImportError:
                    logger.warning("tiktoken not available, ConversationSummaryBufferMemory will use automatic token counting")
            else:
                # Ollama 등 다른 모델의 경우 token_counter를 None으로 설정
                # ConversationSummaryBufferMemory가 자동으로 처리하거나, 
                # transformers를 사용하여 토큰 계산을 시도함
                logger.debug(f"token_counter set to None for model: {model_name}. ConversationSummaryBufferMemory will handle token counting automatically.")

        try:
            # chat_history가 None이어도 ConversationSummaryBufferMemory는 작동할 수 있음 (인메모리만 사용)
            # token_counter가 None이면 ConversationSummaryBufferMemory가 자동으로 토큰 계산을 시도함
            # (LLM의 get_token_ids 메서드 사용 또는 transformers 사용)
            return ConversationSummaryBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                llm=llm,
                max_token_limit=max_token_limit,
                chat_memory=chat_history,  # None이어도 작동 (인메모리만 사용)
                token_counter=token_counter,  # None이면 자동 처리
                output_key="answer"
            )
        except Exception as e:
            logger.error(f"Failed to create ConversationSummaryBufferMemory: {e}")
            # transformers가 없어서 실패하는 경우, max_token_limit을 매우 크게 설정하여 재시도
            if "transformers" in str(e).lower() or "get_token_ids" in str(e).lower():
                logger.warning("Token counting failed. Creating memory with very large max_token_limit to bypass token counting...")
                try:
                    return ConversationSummaryBufferMemory(
                        memory_key="chat_history",
                        return_messages=True,
                        llm=llm,
                        max_token_limit=1000000,  # 매우 큰 값으로 설정하여 토큰 제한 사실상 비활성화
                        chat_memory=chat_history,
                        token_counter=None,  # 토큰 계산 비활성화
                        output_key="answer"
                    )
                except Exception as e2:
                    logger.error(f"Failed to create ConversationSummaryBufferMemory even with large max_token_limit: {e2}")
                    return None
            return None

    def clear_user_memory(self, user_id: str, session_id: str):
        """특정 사용자의 Memory 초기화"""
        # Memory 캐시에서 제거
        keys_to_remove = [
            key for key in self._memory_cache.keys()
            if key.startswith(f"{user_id}_")
        ]
        for key in keys_to_remove:
            del self._memory_cache[key]

        # MongoDB에서도 제거
        if self.mongo_enabled:
            self._delete_custom_messages(user_id, session_id)

    def save_custom_message(
        self,
        user_id: str,
        session_id: str,
        role: str,
        content: str,
        llm_no: Optional[str] = None,
        input_tokens: Optional[int] = None,
        output_tokens: Optional[int] = None,
        total_tokens: Optional[int] = None,
        response_time_ms: Optional[int] = None,
        references: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        session_no: Optional[Any] = None,
        message_no: Optional[Any] = None,
        allow_insert: bool = True,
        allow_update: bool = True,
        **extra: Any,
    ) -> Optional[Any]:
        """커스텀 메시지를 MongoDB에 저장 또는 갱신"""

        if not self.mongo_enabled or self.mongo_collection is None:
            logger.debug("MongoDB persistence disabled. Skipping save_custom_message.")
            return None

        if not user_id or not session_id or not role:
            logger.warning("Missing required identifiers for MongoDB persistence. Skipping save.")
            return None

        normalized_role = role.upper()
        normalized_references = references if references and all(isinstance(item, dict) for item in references) else self._normalize_references(references)
        session_filter = self._build_session_filter(user_id, session_id)
        message_filter = {
            **session_filter,
            "ROLE": normalized_role,
            "CONTENT": content,
        }

        # Update existing message if allowed
        existing = None
        if allow_update:
            try:
                existing = self.mongo_collection.find_one(
                    message_filter,
                    sort=[("CREATED_AT", -1)],
                )
                if existing is None:
                    existing = self.mongo_collection.find_one(
                        {
                            **session_filter,
                            "ROLE": normalized_role,
                        },
                        sort=[("CREATED_AT", -1)],
                    )
            except PyMongoError as error:  # type: ignore[misc]
                logger.warning(f"Failed to lookup existing message for update: {error}")
                existing = None

            if existing is not None:
                update_fields: Dict[str, Any] = {}
                update_fields["CONTENT"] = content
                if llm_no is not None:
                    update_fields["LLM_NO"] = llm_no
                # Always set token fields; coalesce None -> 0
                update_fields["INPUT_TOKENS"] = 0 if input_tokens is None else input_tokens
                update_fields["OUTPUT_TOKENS"] = 0 if output_tokens is None else output_tokens
                update_fields["TOTAL_TOKENS"] = (
                    (0 if total_tokens is None else total_tokens)
                    if not (input_tokens is not None or output_tokens is not None)
                    else ( (input_tokens or 0) + (output_tokens or 0) )
                )
                if response_time_ms is not None:
                    update_fields["RESPONSE_TIME_MS"] = response_time_ms
                # Only AI messages should carry references
                if normalized_role == "AI" and normalized_references is not None:
                    update_fields["REFERENCES"] = normalized_references
                if metadata is not None:
                    update_fields["METADATA"] = metadata
                if extra:
                    update_fields["EXTRA"] = extra

                if update_fields:
                    update_fields["UPDATED_AT"] = _now_kst()
                    logger.debug(
                        "Updating MongoDB message for user_id=%s, session_id=%s with fields=%s",
                        user_id,
                        session_id,
                        list(update_fields.keys()),
                    )
                    try:
                        self.mongo_collection.update_one(
                            {"_id": existing["_id"]},
                            {"$set": update_fields},
                        )
                        logger.debug(
                            f"Updated existing message in MongoDB for user_id={user_id}, session_id={session_id}, role={normalized_role}"
                        )
                    except PyMongoError as error:  # type: ignore[misc]
                        logger.warning(f"Failed to update MongoDB message: {error}")
                else:
                    logger.debug(
                        "Existing MongoDB message found with identical content. Skipping update.")

                return existing.get("_id")

        if not allow_insert:
            return None

        session_uuid = self._session_uuid(user_id, session_id)
        message_uuid = uuid.uuid4()

        # Build in a fixed order for readability in viewers
        document: Dict[str, Any] = {}

        # SESSION_NO first
        if session_no is not None:
            document["SESSION_NO"] = self._to_uuid_if_possible(session_no)
        elif session_uuid is not None:
            document["SESSION_NO"] = self._to_uuid_if_possible(session_uuid)

        # MESSAGE_NO next
        if message_no is not None:
            document["MESSAGE_NO"] = self._to_uuid_if_possible(message_no)
        else:
            document["MESSAGE_NO"] = self._to_uuid_if_possible(message_uuid)

        # Role/content/timestamp
        document["ROLE"] = normalized_role
        document["CONTENT"] = content
        document["CREATED_AT"] = _now_kst()

        # User id (for display near the top)
        document["USER_NO"] = self._to_uuid_if_possible(user_id)

        if normalized_role == "AI":
            if llm_no is not None:
                document["LLM_NO"] = self._to_uuid_if_possible(llm_no)
            input_val = 0 if input_tokens is None else input_tokens
            output_val = 0 if output_tokens is None else output_tokens
            total_val = (0 if total_tokens is None else total_tokens) or (input_val + output_val)
            document["INPUT_TOKENS"] = input_val
            document["OUTPUT_TOKENS"] = output_val
            document["TOTAL_TOKENS"] = total_val
            if response_time_ms is not None:
                document["RESPONSE_TIME_MS"] = response_time_ms
        if metadata is not None:
            document["METADATA"] = metadata
        if extra:
            document["EXTRA"] = extra

        # Place references near the end (AI only)
        if normalized_role == "AI" and normalized_references is not None:
            document["REFERENCES"] = normalized_references

        # _class at the end
        document["_class"] = "com.ssafy.hebees.chat.entity.Message"

        try:
            result = self.mongo_collection.insert_one(document)
            # Remember last AI message meta for response assembly
            try:
                if normalized_role == "AI":
                    self._set_last_ai_message(
                        user_id=str(user_id),
                        session_id=str(session_id),
                        message_no=document.get("MESSAGE_NO"),
                        created_at=document.get("CREATED_AT"),
                    )
            except Exception:
                pass
            logger.debug(
                f"Saved message to MongoDB for user_id={user_id}, session_id={session_id}, role={normalized_role}"
            )
            return result.inserted_id
        except PyMongoError as error:  # type: ignore[misc]
            logger.warning(f"Failed to save message to MongoDB: {error}")
            return None


# 전역 Memory 관리자 인스턴스는 lazy initialization으로 변경
# settings에서 설정을 가져오기 위해 함수로 제공
def get_memory_manager() -> UserMemoryManager:
    """Memory manager 인스턴스 반환 (lazy initialization)"""
    if not hasattr(get_memory_manager, '_instance'):
        get_memory_manager._instance = UserMemoryManager()
    return get_memory_manager._instance

memory_manager = None  # 초기화는 get_memory_manager() 호출 시