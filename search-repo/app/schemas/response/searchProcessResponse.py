from pydantic import BaseModel
from typing import List, Dict, Any


class MetadataDetail(BaseModel):
    """Metadata Detail 스키마"""
    FILE_NAME: str
    PAGE_NO: int
    INDEX_NO: int
    CREATED_AT: str
    UPDATED_AT: str


class Metadata(BaseModel):
    """Metadata 스키마"""
    id: str
    file_no: str
    metadata: MetadataDetail


class CandidateEmbedding(BaseModel):
    """Candidate Embedding 스키마"""
    text: str
    metadata: Metadata
    score: float


class SearchProcessResult(BaseModel):
    """Search Process 결과 스키마"""
    collection: str
    candidateEmbeddings: List[CandidateEmbedding]
    count: int
    strategy: str
    parameters: Dict[Any, Any]


class SearchProcessResponse(BaseModel):
    """Search /process 응답 스키마"""
    status: int
    code: str
    message: str
    isSuccess: bool
    result: SearchProcessResult









