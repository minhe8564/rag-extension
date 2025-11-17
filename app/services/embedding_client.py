"""
Embedding API 클라이언트 모듈
Runpod Embedding API를 호출하는 기능 제공
"""
import httpx
from typing import List
from loguru import logger


class EmbeddingClient:
    """Runpod Embedding API 클라이언트"""
    
    @staticmethod
    async def get_query_embedding(
        runpod_address: str,
        query: str,
        model_name: str,
        timeout: float = 60.0
    ) -> List[float]:
        """
        Runpod의 embedding API를 호출하여 쿼리 임베딩 수행
        
        Args:
            runpod_address: Runpod 주소 (예: "https://xxx-8000.proxy.runpod.net")
            query: 임베딩할 쿼리
            model_name: 모델 이름 (예: "intfloat/multilingual-e5-large")
            timeout: 요청 타임아웃 (초)
            
        Returns:
            임베딩 벡터 (List[float])
            
        Raises:
            ValueError: 임베딩을 찾을 수 없거나 형식이 잘못된 경우
            httpx.HTTPStatusError: HTTP 요청 실패
        """
        try:
            url = f"{runpod_address}/api/v1/embedding/query"
            payload = {
                "query": query,
                "models": [model_name]
            }
            
            logger.info(f"[EmbeddingClient] Requesting embedding from: {url}, model: {model_name}")
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "accept": "application/json",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                # BaseResponse 형식: result.data.embeddings[model_name]
                embeddings = data.get("result", {}).get("data", {}).get("embeddings", {})
                embedding = embeddings.get(model_name)
                
                if not embedding:
                    raise ValueError(f"Embedding not found for model: {model_name}")
                
                if not isinstance(embedding, list):
                    raise ValueError(f"Invalid embedding format: expected list, got {type(embedding)}")
                
                logger.info(f"[EmbeddingClient] Embedding retrieved, dimension: {len(embedding)}")
                return embedding
                
        except httpx.HTTPStatusError as e:
            logger.error(f"[EmbeddingClient] Failed to get embedding: HTTP {e.response.status_code}, {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"[EmbeddingClient] Error getting embedding: {str(e)}")
            raise

