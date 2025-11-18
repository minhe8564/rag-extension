from .base import BaseQueryEmbeddingStrategy
from typing import Dict, Any
from loguru import logger
import time
from app.services.runpod_service import RunpodService
from app.services.embedding_client import EmbeddingClient


class Mclip(BaseQueryEmbeddingStrategy):
    """
    Mclip 모델을 사용하여 이미지를 임베딩으로 변환
    - DB에서 직접 "EMBEDDING" 이름의 Runpod 주소 조회
    - rag-embedding-model-runpod API를 호출하여 이미지 임베딩 수행
    """
    
    def __init__(self, parameters: Dict[Any, Any] = None):
        super().__init__(parameters)
        
        # 파라미터에서 설정값 가져오기
        self.runpod_name = self.parameters.get("runpod_name", "EMBEDDING")
        self.model_name = self.parameters.get("model_name", "sentence-transformers/clip-ViT-B-32")
        
        logger.info(f"[Mclip] Initialized with runpod_name={self.runpod_name}, model={self.model_name}")
    
    async def embed(self, query: str) -> Dict[Any, Any]:
        """
        이미지를 임베딩으로 변환 (비동기 메서드)
        Runpod API를 통해 이미지 임베딩 수행
        
        Args:
            query: 이미지 URL 또는 이미지 데이터 (문자열)
        """
        if not query or not query.strip():
            raise ValueError("Query (image) cannot be empty")
        
        query = query.strip()
        logger.info(f"[Mclip] Embedding image: {query[:50]}...")
        t0 = time.time()
        
        try:
            # Runpod 주소 조회
            runpod_address = await RunpodService.get_address_by_name(self.runpod_name)
            
            # Runpod API 호출하여 이미지 임베딩 수행
            embedding = await EmbeddingClient.get_image_embedding(
                runpod_address=runpod_address,
                query=query,
                model_name=self.model_name
            )
            
            dt = time.time() - t0
            logger.info(f"[Mclip] Image embedding completed. Dimension: {len(embedding)}, elapsed={dt:.2f}s")
            
            return {
                "query": query,
                "embedding": embedding,
                "dimension": len(embedding),
                "strategy": "mclip",
                "parameters": self.parameters
            }
            
        except Exception as e:
            logger.error(f"[Mclip] Error during image embedding: {str(e)}")
            raise

