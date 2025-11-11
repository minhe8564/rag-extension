from .base import BaseSearchStrategy
from typing import Dict, Any, List
from loguru import logger
import os

try:
    # langchain-milvus 패키지에서 import 시도
    try:
        from langchain_milvus import MilvusVectorStore
        USE_MILVUS_VECTOR_STORE = True
    except ImportError:
        # 대안: Milvus 클래스 사용 (embedding_function 필요)
        from langchain_milvus import Milvus
        MilvusVectorStore = Milvus
        USE_MILVUS_VECTOR_STORE = False
    
    from pymilvus import connections
    MILVUS_AVAILABLE = True
except ImportError as e:
    MilvusVectorStore = None
    connections = None
    MILVUS_AVAILABLE = False
    USE_MILVUS_VECTOR_STORE = False
    logger.error(f"Failed to import langchain_milvus or pymilvus: {e}")
    logger.error(f"Import error details: {type(e).__name__}: {str(e)}")
    import traceback
    logger.debug(traceback.format_exc())


class Semantic(BaseSearchStrategy):
    """
    기본 Milvus 벡터 검색 전략
    LangChain의 Milvus를 사용하여 벡터 검색을 수행합니다.
    """
    
    def __init__(self, parameters: Dict[Any, Any] = None):
        super().__init__(parameters)
        
        if not MILVUS_AVAILABLE:
            raise ImportError("langchain_milvus and pymilvus are required for Basic search. Install them with: uv add langchain-milvus pymilvus")
        
        # 환경변수에서 Milvus 설정 가져오기
        self.milvus_host = os.getenv("MILVUS_HOST", "localhost")
        self.milvus_port = os.getenv("MILVUS_PORT", "19530")
        self.default_collection = os.getenv("MILVUS_COLLECTION", "default_collection")
        
        # 파라미터에서 오버라이드 가능
        self.milvus_host = self.parameters.get("milvus_host", self.milvus_host)
        self.milvus_port = str(self.parameters.get("milvus_port", self.milvus_port))
        # 포트를 정수로 변환 (connection_args에는 문자열, connections.connect에는 정수)
        try:
            self.milvus_port_int = int(self.milvus_port)
        except (ValueError, TypeError):
            self.milvus_port_int = 19530
        self.default_collection = self.parameters.get("collection", self.default_collection)
        
        logger.info(f"[Basic] Milvus connection: {self.milvus_host}:{self.milvus_port}")
        logger.info(f"[Basic] Default collection: {self.default_collection}")
        # Optional partition to search (e.g., "public")
        try:
            self.partition = str(self.parameters.get("partition")).strip() if self.parameters.get("partition") else None
        except Exception:
            self.partition = None
        # Semantic-specific params: topK and threshold
        self.top_k_override = None
        self.threshold = None
        try:
            semantic_params = self.parameters.get("semantic") or {}
            if isinstance(semantic_params, dict):
                tk = semantic_params.get("topK")
                th = semantic_params.get("threshold")
                if tk is not None:
                    try:
                        self.top_k_override = int(tk)
                    except Exception:
                        self.top_k_override = None
                if th is not None:
                    try:
                        self.threshold = float(th)
                    except Exception:
                        self.threshold = None
        except Exception:
            pass
    
    def _connect_milvus(self):
        """Milvus에 연결"""
        try:
            connections.connect(
                alias="default",
                host=self.milvus_host,
                port=self.milvus_port_int
            )
            logger.debug(f"[Basic] Connected to Milvus: {self.milvus_host}:{self.milvus_port_int}")
        except Exception as e:
            logger.error(f"[Basic] Failed to connect to Milvus: {str(e)}")
            raise
    
    def search(self, query_embedding: Dict[Any, Any], collection: str = None, parameters: Dict[Any, Any] = None) -> Dict[Any, Any]:
        """
        쿼리 임베딩을 사용하여 Milvus에서 검색
        
        Args:
            query_embedding: 쿼리 임베딩 딕셔너리 (embedding 필드 포함)
            collection: 컬렉션 이름 (없으면 기본값 사용)
            top_k: 반환할 상위 k개 결과
        
        Returns:
            검색 결과 딕셔너리
        """
        if not query_embedding or "embedding" not in query_embedding:
            raise ValueError("query_embedding must contain 'embedding' field")
        
        embedding = query_embedding["embedding"]
        collection_name = collection or self.default_collection
        
        # Determine effective top_k/threshold
        # Priority: call-time parameters.semantic > init-time overrides > defaults
        effective_top_k = 5
        effective_threshold = None
        try:
            call_semantic = (parameters or {}).get("semantic") if isinstance(parameters, dict) else None
            if isinstance(call_semantic, dict):
                if call_semantic.get("topK") is not None:
                    try:
                        effective_top_k = int(call_semantic.get("topK"))
                    except Exception:
                        pass
                if call_semantic.get("threshold") is not None:
                    try:
                        effective_threshold = float(call_semantic.get("threshold"))
                    except Exception:
                        effective_threshold = None
        except Exception:
            pass
        if getattr(self, "top_k_override", None) and effective_top_k == 5:
            effective_top_k = self.top_k_override
        if getattr(self, "threshold", None) is not None and effective_threshold is None:
            effective_threshold = self.threshold
        logger.info(f"[Basic] Searching in collection: {collection_name}, top_k: {effective_top_k}")
        if getattr(self, "partition", None):
            logger.info(f"[Basic] Applying partition: {self.partition}")
        if effective_threshold is not None:
            logger.info(f"[Basic] Applying threshold: {effective_threshold}")
        
        try:
            # Milvus 연결
            self._connect_milvus()
            
            logger.info(f"[Basic] USE_MILVUS_VECTOR_STORE: {USE_MILVUS_VECTOR_STORE}")
            logger.info(f"[Basic] Creating vectorstore with host={self.milvus_host}, port={self.milvus_port_int}")
            
            # connection_args 준비 (포트는 문자열로 전달)
            connection_args = {
                "host": self.milvus_host,
                "port": str(self.milvus_port_int),
                "alias": "default"  # 이미 연결된 connection 사용
            }
            
            # MilvusVectorStore 생성 (검색용)
            if USE_MILVUS_VECTOR_STORE:
                # MilvusVectorStore는 embedding_function 없이 사용 가능
                # connection_args에 alias를 명시하여 이미 연결된 connection 사용
                vs_kwargs = {
                    "collection_name": collection_name,
                    "connection_args": connection_args
                }
                # Apply partition if supported
                if getattr(self, "partition", None):
                    vs_kwargs["partition_name"] = self.partition
                try:
                    vectorstore = MilvusVectorStore(**vs_kwargs)
                except TypeError:
                    # 일부 버전은 partition_name을 생성자에서 지원하지 않음 → 제거 후 재시도
                    if "partition_name" in vs_kwargs:
                        _ = vs_kwargs.pop("partition_name", None)
                        logger.info("[Basic] MilvusVectorStore ctor doesn't support partition_name, retrying without it")
                        vectorstore = MilvusVectorStore(**vs_kwargs)
                    else:
                        raise
            else:
                # Milvus 클래스는 embedding_function이 필수이므로 더미 함수 제공
                # 실제로는 사용하지 않지만 생성자에 필요
                embedding_dim = len(embedding)
                class DummyEmbedding:
                    def embed_documents(self, texts):
                        return [[0.0] * embedding_dim for _ in texts]
                    def embed_query(self, text):
                        return [0.0] * embedding_dim
                
                vs_kwargs = {
                    "embedding_function": DummyEmbedding(),
                    "collection_name": collection_name,
                    "connection_args": connection_args
                }
                # 주의: Milvus 클래스 생성자는 partition_name을 지원하지 않는 경우가 많음 → 전달하지 않음
                try:
                    vectorstore = MilvusVectorStore(**vs_kwargs)
                except TypeError as e:
                    logger.info(f"[Basic] Milvus ctor doesn't accept extra kwargs: {e}. Retrying with minimal args.")
                    vectorstore = MilvusVectorStore(
                        embedding_function=vs_kwargs["embedding_function"],
                        collection_name=collection_name,
                        connection_args=connection_args
                    )
            
            # similarity_search_with_score_by_vector 사용하여 벡터 직접 검색
            try:
                if getattr(self, "partition", None):
                    # Try passing partition_names if supported by current backend
                    results = vectorstore.similarity_search_with_score_by_vector(
                        embedding=embedding,
                    k=effective_top_k,
                    partition_names=[self.partition]
                    )
                else:
                    results = vectorstore.similarity_search_with_score_by_vector(
                        embedding=embedding,
                        k=effective_top_k
                    )
            except TypeError:
                # Fallback for backends which don't accept partition_names on search call
                results = vectorstore.similarity_search_with_score_by_vector(
                    embedding=embedding,
                    k=effective_top_k
                )
            
            # 결과 처리
            candidate_embeddings = []
            threshold_val = effective_threshold
            for (doc, score) in results:
                score_float = float(score)
                # Apply threshold filter if provided: keep only scores > threshold
                if threshold_val is not None and not (score_float > threshold_val):
                    continue
                candidate_embeddings.append({
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": score_float,
                })
            
            
            logger.info(f"[Basic] Found {len(candidate_embeddings)} candidates")
            
            return {
                "collection": collection_name,
                "topK": effective_top_k,
                "candidateEmbeddings": candidate_embeddings,
                "count": len(candidate_embeddings),
                "strategy": "basic",
                "parameters": self.parameters
            }
            
        except Exception as e:
            logger.error(f"[Basic] Error during search: {str(e)}")
            raise

