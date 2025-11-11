from .base import BaseQueryEmbeddingStrategy
from typing import Dict, Any
from loguru import logger
import time

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
    logger.warning("sentence-transformers not installed. E5Large query embedding will not work.")


class E5Large(BaseQueryEmbeddingStrategy):
    """
    E5 multilingual large 모델을 사용하여 쿼리를 임베딩으로 변환
    'query:' 접두사를 붙여 텍스트를 검색 쿼리로 임베딩합니다.
    """
    
    def __init__(self, parameters: Dict[Any, Any] = None):
        super().__init__(parameters)
        
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers is required for E5Large query embedding. Install it with: pip install sentence-transformers")
        
        # 파라미터에서 설정값 가져오기 (기본값: intfloat/multilingual-e5-large)
        model_name = self.parameters.get("model_name", "intfloat/multilingual-e5-large")
        device = self.parameters.get("device", None)
        
        logger.info(f"[E5Large] Loading model: {model_name}")
        
        try:
            self.model = SentenceTransformer(model_name, device=device)
            logger.info(f"[E5Large] Model loaded successfully")
        except Exception as e:
            logger.error(f"[E5Large] Failed to load model: {str(e)}")
            raise
        
        # 모델의 최대 시퀀스 길이를 설정
        try:
            self.model.max_seq_length = 512
        except Exception:
            pass
    
    def _prepare_query(self, query: str) -> str:
        """
        E5 모델의 요구사항에 맞게 쿼리 앞에 'query:' 접두사를 추가합니다.
        
        Args:
            query: 원본 쿼리
        
        Returns:
            접두사가 추가된 쿼리
        """
        return "query: " + query
    
    def embed(self, query: str) -> Dict[Any, Any]:
        """
        쿼리를 임베딩으로 변환
        
        Args:
            query: 검색 쿼리 문자열
        
        Returns:
            임베딩 결과 딕셔너리
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        prepared_query = self._prepare_query(query.strip())
        
        logger.info(f"[E5Large] Embedding query: {query[:50]}...")
        t0 = time.time()
        
        try:
            # 쿼리 임베딩 생성 (sentence-transformers 사용)
            embedding = self.model.encode(
                prepared_query,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            # numpy array를 리스트로 변환
            embedding_list = embedding.tolist()
            
            dt = time.time() - t0
            logger.info(f"[E5Large] Query embedding completed. Dimension: {len(embedding_list)}, elapsed={dt:.2f}s")
            
            return {
                "query": query,
                "embedding": embedding_list,
                "dimension": len(embedding_list),
                "strategy": "e5Large",
                "parameters": self.parameters
            }
            
        except Exception as e:
            logger.error(f"[E5Large] Error during query embedding: {str(e)}")
            raise

