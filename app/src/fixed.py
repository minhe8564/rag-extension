from .base import BaseChunkingStrategy
from typing import List, Dict, Any
from loguru import logger
from app.core.utils import dispose_model

try:
    from transformers import AutoTokenizer
except ImportError:
    AutoTokenizer = None
    logger.warning("transformers not installed. Basic chunking will not work.")


class Fixed(BaseChunkingStrategy):
    """
    기본 토큰 기반 청킹 전략
    Hugging Face의 transformers 라이브러리를 사용하여 텍스트를 토큰화하고,
    슬라이딩 윈도우 방식으로 겹치는 부분을 처리합니다.
    페이지 간 끊김을 없애기 위해 이전 페이지의 마지막 청크의 끝부분과
    다음 페이지의 첫 번째 토큰이 overlap되도록 처리합니다.
    """
    
    def __init__(self, parameters: Dict[Any, Any] = None):
        super().__init__(parameters)
        
        if AutoTokenizer is None:
            raise ImportError("transformers is required for Basic chunking. Install it with: pip install transformers")
        
        # 파라미터에서 설정값 가져오기 (기본값: token 400, overlap 80, model "klue/bert-base")
        model_name = self.parameters.get("model_name", "klue/bert-base")
        max_tokens = self.parameters.get("max_tokens", 400)
        overlap = self.parameters.get("overlap", 80)
        
        if overlap >= max_tokens:
            raise ValueError("overlap must be smaller than max_tokens")
        
        logger.info(f"[Basic] Loading tokenizer model: {model_name}, max_tokens: {max_tokens}, overlap: {overlap}")
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
        try:
            # 토크나이저의 최대 길이를 매우 큰 값으로 설정하여 자동 잘림을 방지
            self.tokenizer.model_max_length = 10**9
        except Exception:
            pass
        
        self.max_tokens = max_tokens
        self.overlap = overlap
    
    def chunk(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        페이지의 텍스트를 토큰 기반 청크로 나눕니다.
        페이지 간 끊김을 없애기 위해 이전 페이지의 마지막 청크의 끝부분과
        다음 페이지의 첫 번째 토큰이 overlap되도록 처리합니다.
        
        Args:
            pages: 페이지 리스트, 각 페이지는 {"page": int, "content": str} 형식
        
        Returns:
            청크 리스트, 각 청크는 {"page": int, "chunk_id": int, "text": str} 형식
        """
        if not pages:
            return []
        
        chunks = []
        chunk_id = 0
        prev_page_last_tokens = []  # 이전 페이지의 마지막 토큰들 (overlap용)
        
        for page_idx, page in enumerate(pages):
            page_num = page.get("page", page_idx + 1)
            content = page.get("content", "")
            
            if not content or not content.strip():
                continue
            
            raw = content.strip()
            
            # 텍스트를 토큰 ID의 리스트로 인코딩
            token_ids = self.tokenizer.encode(raw, add_special_tokens=False, truncation=False)
            
            # 이전 페이지의 마지막 토큰들과 현재 페이지의 첫 토큰들을 합침 (overlap)
            if prev_page_last_tokens:
                # 이전 페이지의 마지막 overlap 개수의 토큰과 현재 페이지의 토큰을 합침
                combined_token_ids = prev_page_last_tokens + token_ids
                logger.debug(f"[Basic] Page {page_num}: Combined {len(prev_page_last_tokens)} tokens from previous page with {len(token_ids)} tokens from current page")
            else:
                combined_token_ids = token_ids
            
            # 이전 페이지의 overlap 토큰이 있으면, 이미 이전 페이지의 마지막 청크에 포함되었으므로
            # 현재 페이지에서는 건너뛰고 시작 (0부터가 아니라 prev_page_last_tokens 길이부터)
            if prev_page_last_tokens:
                start = len(prev_page_last_tokens)
                logger.debug(f"[Basic] Page {page_num}: Starting from offset {start} (skipping {len(prev_page_last_tokens)} overlap tokens from previous page)")
            else:
                start = 0
            
            while start < len(combined_token_ids):
                # 현재 청크의 끝 인덱스를 계산
                end = min(start + self.max_tokens, len(combined_token_ids))
                piece_ids = combined_token_ids[start:end]
                
                # 토큰 ID들을 다시 텍스트로 디코딩
                piece_text = self.tokenizer.decode(
                    piece_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True
                )
                
                chunks.append({
                    "page": page_num,
                    "chunk_id": chunk_id,
                    "text": piece_text,
                })
                chunk_id += 1
                
                if end == len(combined_token_ids):
                    # 현재 페이지의 마지막 청크인 경우, 다음 페이지와 overlap할 토큰 저장
                    # 현재 페이지의 마지막 overlap 개수의 토큰을 저장
                    # (원본 token_ids 기준으로 저장해야 함 - combined에서 이전 페이지 부분 제외)
                    if len(token_ids) >= self.overlap:
                        # 원본 페이지의 마지막 overlap 개수만큼 저장
                        prev_page_last_tokens = token_ids[-self.overlap:]
                        logger.debug(f"[Basic] Page {page_num}: Saved {len(prev_page_last_tokens)} tokens for next page overlap")
                    else:
                        # overlap 크기보다 작은 경우 전체를 저장
                        prev_page_last_tokens = token_ids
                    break
                
                # 다음 시작 위치는 현재 끝 위치에서 overlap만큼 뺀 값
                start = end - self.overlap
            
            logger.info(f"[Basic] Page {page_num}: Created {len([c for c in chunks if c['page'] == page_num])} chunks")
        
        logger.info(f"[Basic] Total chunks created: {len(chunks)}")
        # 리소스 해제 (CPU 환경 고려)
        try:
            dispose_model(self.tokenizer)
        finally:
            self.tokenizer = None
        return chunks

