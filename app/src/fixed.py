from .base import BaseChunkingStrategy
from typing import List, Dict, Any
from loguru import logger
from app.core.utils import dispose_model
import httpx

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
    
    def _download_text(self, bucket: str, path: str, request_headers: Dict[str, Any] | None) -> str:
        presign_url = "http://hebees-python-backend:8000/api/v1/files/presigned"
        params = {"bucket": bucket, "path": path, "inline": "false"}
        with httpx.Client(timeout=3600.0) as client:
            r = client.get(presign_url, params=params, headers={k: v for k, v in (request_headers or {}).items() if v})
            r.raise_for_status()
            try:
                js = r.json()
                url = js.get("result", {}).get("data", {}).get("url")
            except Exception:
                url = r.text.strip().strip('"')
            if not url:
                raise RuntimeError("Failed to resolve presigned URL for chunking")
            rd = client.get(url)
            rd.raise_for_status()
            return rd.text

    def chunk(self, bucket: str, path: str, request_headers: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
        """
        TXT 등 일반 텍스트를 토큰 기반 청크로 나눕니다. (bucket/path 원격 다운로드)
        """
        raw_text = self._download_text(bucket, path, request_headers) or ""
        if not raw_text.strip():
            return []
        
        chunks = []
        chunk_id = 0
        prev_page_last_tokens = []  # 이전 페이지의 마지막 토큰들 (overlap용)
        # 단일 페이지로 처리
        page_num = 1
        raw = raw_text.strip()
        # 텍스트를 토큰 ID의 리스트로 인코딩
        token_ids = self.tokenizer.encode(raw, add_special_tokens=False, truncation=False)
        # 이전 페이지의 마지막 토큰들과 현재 페이지의 첫 토큰들을 합침 (overlap)
        if prev_page_last_tokens:
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
                if len(token_ids) >= self.overlap:
                    prev_page_last_tokens = token_ids[-self.overlap:]
                    logger.debug(f"[Basic] Page {page_num}: Saved {len(prev_page_last_tokens)} tokens for next page overlap")
                else:
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

