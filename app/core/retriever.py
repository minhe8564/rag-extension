"""
Custom retriever for already retrieved chunks
"""
from typing import List
from loguru import logger

# BaseRetriever import
try:
    from langchain_core.retrievers import BaseRetriever
except ImportError:
    try:
        from langchain.schema.retriever import BaseRetriever
    except ImportError:
        BaseRetriever = None
        logger.warning("BaseRetriever not available")

# Document import (여러 경로 시도)
try:
    from langchain_core.documents import Document
except ImportError:
    try:
        from langchain.schema.document import Document
    except ImportError:
        try:
            from langchain.schema import Document
        except ImportError:
            Document = None
            logger.error("Document not available from all import paths")

# Pydantic Field import (LangChain 1.x)
try:
    from pydantic import Field
except ImportError:
    Field = None


class StaticDocumentRetriever(BaseRetriever):
    """
    이미 검색된 문서들을 반환하는 정적 Retriever
    retrieved_chunks를 Document로 변환하여 반환
    """
    
    def __init__(self, documents: List[Document]):
        if BaseRetriever is None:
            raise ImportError("BaseRetriever is not available. Please install langchain-core.")
        if Document is None:
            raise ImportError("Document is not available. Please install langchain-core.")
        
        # Pydantic 모델 초기화 (빈 kwargs로 먼저 초기화)
        super().__init__()
        
        # Pydantic 모델에서는 object.__setattr__를 사용해야 함
        object.__setattr__(self, '_documents', documents)
    
    def _get_relevant_documents(self, query: str) -> List[Document]:
        """이미 검색된 문서들을 그대로 반환"""
        return object.__getattribute__(self, '_documents')
    
    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        """비동기 버전"""
        return object.__getattribute__(self, '_documents')

