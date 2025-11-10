from .base import BaseEmbeddingStrategy
from typing import List, Dict, Any
from loguru import logger
import numpy as np
import time

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None
    logger.warning("sentence-transformers not installed. E5Large embedding will not work.")


class Dense(BaseEmbeddingStrategy):
    """
    E5 multilingual large 모델을 사용하여 텍스트를 임베딩하는 전략
    'passage:' 접두사를 붙여 텍스트를 저장용 문서로 임베딩합니다.
    """
    
    def __init__(self, parameters: Dict[Any, Any] = None):
        super().__init__(parameters)
        
        if SentenceTransformer is None:
            raise ImportError("sentence-transformers is required for E5Large embedding. Install it with: pip install sentence-transformers")
        
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
    
    def _prepare(self, texts: List[str]) -> List[str]:
        """
        E5 모델의 요구사항에 맞게 텍스트 앞에 'passage:' 접두사를 추가합니다.
        
        Args:
            texts: 처리할 텍스트 리스트
        
        Returns:
            접두사가 추가된 텍스트 리스트
        """
        return ["passage: " + text for text in texts]
    
    def embed(self, chunks: List[Dict[str, Any]]) -> Dict[Any, Any]:
        """
        청크 데이터를 임베딩으로 변환
        
        Args:
            chunks: 청크 리스트, 각 청크는 {"page": int, "chunk_id": int, "text": str} 형식
        
        Returns:
            임베딩 결과 딕셔너리
        """
        if not chunks:
            return {
                "chunks": [],
                "embeddings": [],
                "count": 0
            }
        
        # 청크에서 텍스트 추출
        texts = []
        chunk_metadata = []
        
        for chunk in chunks:
            text = chunk.get("text", "")
            if text and text.strip():
                texts.append(text.strip())
                chunk_metadata.append({
                    "page": chunk.get("page", 0),
                    "chunk_id": chunk.get("chunk_id", 0)
                })
        
        if not texts:
            logger.warning("[E5Large] No valid texts found in chunks")
            return {
                "chunks": chunks,
                "embeddings": [],
                "count": 0
            }
        
        logger.info(f"[E5Large] Embedding {len(texts)} chunks")
        t0 = time.time()
        
        # 텍스트에 접두사 추가
        prepared_texts = self._prepare(texts)
        
        # 임베딩 수행
        try:
            embeddings = self.model.encode(
                prepared_texts,
                convert_to_numpy=True,
                show_progress_bar=False
            )
            
            dt = time.time() - t0
            logger.info(f"[E5Large] Done. Shape={embeddings.shape}, elapsed={dt:.2f}s")
            
            # 결과 반환 (numpy array를 리스트로 변환)
            embeddings_list = embeddings.tolist()
            
            # 각 청크에 임베딩 추가
            embedded_chunks = []
            for i, chunk_meta in enumerate(chunk_metadata):
                embedded_chunks.append({
                    **chunk_meta,
                    "text": texts[i],
                    "embedding": embeddings_list[i]
                })
            
            return {
                "chunks": embedded_chunks,
                "embeddings": embeddings_list,
                "count": len(embedded_chunks),
                "embedding_dimension": len(embeddings_list[0]) if embeddings_list else 0
            }
            
        except Exception as e:
            logger.error(f"[E5Large] Error during embedding: {str(e)}")
            raise

