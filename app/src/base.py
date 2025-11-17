from abc import ABC, abstractmethod
from typing import Dict, Any, List, AsyncIterator, Optional
from loguru import logger


class BaseGenerationStrategy(ABC):
    """생성 전략 Base 클래스"""
    
    def __init__(self, parameters: Dict[Any, Any] = None):
        self.parameters = parameters or {}
        logger.info(f"Initialized {self.__class__.__name__} with parameters: {self.parameters}")
    
    @abstractmethod
    def generate(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        memory=None
    ) -> Dict[Any, Any]:
        """
        쿼리와 검색된 청크를 사용하여 최종 답변 생성
        
        Args:
            query: 검색 쿼리 문자열
            retrieved_chunks: 검색된 청크 리스트
            memory: LangChain memory 객체 (선택적, history 기능용)
        
        Returns:
            생성된 답변 딕셔너리
        """
        pass
    
    async def generate_stream(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        memory=None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_headers: Optional[Dict[str, str]] = None
    ) -> AsyncIterator[str]:
        """
        스트리밍 방식으로 답변 생성 (기본 구현: generate를 호출하고 결과를 스트리밍)
        
        Args:
            query: 검색 쿼리 문자열
            retrieved_chunks: 검색된 청크 리스트
            memory: LangChain memory 객체 (선택적)
            user_id: 사용자 ID
            session_id: 세션 ID
            request_headers: 요청 헤더
        
        Yields:
            SSE 형식의 문자열 청크
        """
        # 기본 구현: generate를 호출하고 결과를 스트리밍
        result = self.generate(
            query=query,
            retrieved_chunks=retrieved_chunks,
            memory=memory,
            user_id=user_id,
            session_id=session_id,
            request_headers=request_headers
        )
        answer = result.get("answer", "")
        # 답변을 작은 청크로 나누어 스트리밍
        chunk_size = 10
        for i in range(0, len(answer), chunk_size):
            chunk = answer[i:i + chunk_size]
            yield f"data: {chunk}\n\n"

