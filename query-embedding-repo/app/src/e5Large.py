from .base import BaseQueryEmbeddingStrategy
from typing import Dict, Any
from loguru import logger
import time
from app.services.runpod_service import RunpodService
from app.services.embedding_client import EmbeddingClient


class E5Large(BaseQueryEmbeddingStrategy):
    """
    E5 multilingual large 모델을 사용하여 쿼리를 임베딩으로 변환
    - DB에서 직접 "EMBEDDING" 이름의 Runpod 주소 조회
    - rag-embedding-model-runpod API를 호출하여 쿼리 임베딩 수행
    """
    
    def __init__(self, parameters: Dict[Any, Any] = None):
        super().__init__(parameters)
        
        # 파라미터에서 설정값 가져오기
        self.runpod_name = self.parameters.get("runpod_name", "EMBEDDING")
        self.model_name = self.parameters.get("model_name", "intfloat/multilingual-e5-large")
        
        logger.info(f"[E5Large] Initialized with runpod_name={self.runpod_name}, model={self.model_name}")
    
    async def embed(self, query: str) -> Dict[Any, Any]:
        """
        쿼리를 임베딩으로 변환 (비동기 메서드)
        Runpod API를 통해 임베딩 수행
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        query = query.strip()
        logger.info(f"[E5Large] Embedding query: {query[:50]}...")
        t0 = time.time()
        
        try:
            # Runpod 주소 조회
            runpod_address = await RunpodService.get_address_by_name(self.runpod_name)
            
            # Runpod API 호출하여 임베딩 수행
            embedding = await EmbeddingClient.get_query_embedding(
                runpod_address=runpod_address,
                query=query,
                model_name=self.model_name
            )
            
            dt = time.time() - t0
            logger.info(f"[E5Large] Query embedding completed. Dimension: {len(embedding)}, elapsed={dt:.2f}s")
            
            return {
                "query": query,
                "embedding": embedding,
                "dimension": len(embedding),
                "strategy": "e5Large",
                "parameters": self.parameters
            }
            
        except Exception as e:
            logger.error(f"[E5Large] Error during query embedding: {str(e)}")
            raise

