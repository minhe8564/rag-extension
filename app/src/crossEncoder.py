from .base import BaseCrossEncoderStrategy
from typing import Dict, Any, List
from loguru import logger
import json
try:
    from sentence_transformers import CrossEncoder as STCrossEncoder
except ImportError:
    STCrossEncoder = None
    logger.warning("sentence-transformers not installed. MiniLM cross-encoder will not work.")


class CrossEncoder(BaseCrossEncoderStrategy):
    """
    MiniLM 기반 Cross Encoder 전략
    query와 candidate들을 cross-encoder로 재정렬합니다.
    """
    
    def __init__(self, parameters: Dict[Any, Any] = None):
        super().__init__(parameters)
        
        if STCrossEncoder is None:
            raise ImportError("sentence-transformers is required for MiniLM cross-encoder. Install it with: pip install sentence-transformers")
        
        # 파라미터에서 설정값 가져오기 (기본값: cross-encoder/mmarco-mMiniLMv2-L12-H384-v1)
        model_name = (
            self.parameters.get("model_name")
            or self.parameters.get("model")
            or "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
        )
        
        logger.info(f"[MiniLM] Loading cross-encoder model: {model_name}")
        
        try:
            self.cross_encoder = STCrossEncoder(model_name)
            logger.info(f"[MiniLM] Cross-encoder model loaded successfully")
        except Exception as e:
            logger.error(f"[MiniLM] Failed to load model: {str(e)}")
            raise
    
    def rerank(self, query_embedding: Dict[Any, Any], candidate_embeddings: List[Dict[str, Any]]) -> Dict[Any, Any]:
        """
        쿼리와 후보들을 cross-encoder로 재정렬
        
        Args:
            query_embedding: 쿼리 임베딩 딕셔너리 (query 필드 포함)
            candidate_embeddings: 후보 임베딩 리스트 (각각 text, metadata 포함)
        
        Returns:
            재정렬된 결과 딕셔너리
        """
        if not query_embedding or "query" not in query_embedding:
            raise ValueError("query_embedding must contain 'query' field")
        
        query = query_embedding["query"]
        
        if not candidate_embeddings:
            logger.warning("[MiniLM] No candidate embeddings provided")
            return {
                "query": query,
                "retrievedChunks": [],
                "count": 0,
                "strategy": "minilm",
                "parameters": self.parameters
            }
        
        logger.info(f"[MiniLM] Reranking {len(candidate_embeddings)} candidates for query: {query[:50]}...")
        
        try:
        # query와 각 candidate 텍스트를 페어로 만들어 cross-encoder에 입력
            pairs = [(query, candidate.get("text", "")) for candidate in candidate_embeddings]
            
            # Cross-encoder로 점수 예측
            scores = self.cross_encoder.predict(pairs)
            
            # 점수와 함께 후보들 결합 및 정렬
            ranked_candidates = []
            for candidate, score in zip(candidate_embeddings, scores):
                ranked_candidates.append({
                    **candidate,
                    "crossEncoderScore": float(score)
                })
            
            # 점수 내림차순 정렬
            ranked_candidates.sort(key=lambda x: x["crossEncoderScore"], reverse=True)

            # 상위 topK만 유지 (파라미터에 지정되면 사용, 없으면 기본 5)
            top_k = 5
            try:
                if isinstance(self.parameters, dict) and self.parameters.get("topK") is not None:
                    top_k = int(self.parameters.get("topK"))
            except Exception:
                top_k = 5
            if top_k > 0:
                ranked_candidates = ranked_candidates[:top_k]
            
            # retrievedChunks 형식으로 변환 (fileNo/fileName 등 메타 포함)
            retrieved_chunks = []
            for i, candidate in enumerate(ranked_candidates):
                meta_outer = candidate.get("metadata", {}) or {}
                meta_inner = {}
                if isinstance(meta_outer.get("metadata"), dict):
                    meta_inner = meta_outer.get("metadata") or {}
                # Attempt to read file_no and file name
                file_no = meta_outer.get("file_no") or meta_outer.get("FILE_NO") or meta_inner.get("FILE_NO")
                file_name = meta_inner.get("FILE_NAME") or meta_outer.get("file_name")
                page_no = meta_inner.get("PAGE_NO", 1)
                index_no = meta_inner.get("INDEX_NO", i)
                retrieved_chunks.append({
                    "page": page_no if page_no is not None else 1,
                    "chunk_id": index_no if index_no is not None else i,
                    "text": candidate.get("text", ""),
                    "score": candidate.get("crossEncoderScore", 0.0),
                    "fileNo": file_no or "",
                    "fileName": file_name or "",
                })
            
            logger.info(f"[MiniLM] Reranking completed. Top score: {ranked_candidates[0]['crossEncoderScore'] if ranked_candidates else 'N/A'}")
            return {
                "query": query,
                "retrievedChunks": retrieved_chunks,
                "count": len(retrieved_chunks),
                "strategy": "minilm",
                "parameters": self.parameters
            }
            
        except Exception as e:
            logger.error(f"[MiniLM] Error during reranking: {str(e)}")
            raise

