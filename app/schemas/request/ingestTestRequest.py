from typing import Optional
from pydantic import BaseModel


class IngestTestRequest(BaseModel):
    """Ingest /test 요청 스키마 (Form 데이터)"""
    collectionName: str
    extractionPdf: str
    extractionPdfParameter: dict = {}
    extractionXlsx: str
    extractionXlsxParameter: dict = {}
    extractionDocs: str
    extractionDocsParameter: dict = {}
    extractionTxt: str
    extractionTxtParameter: dict = {}
    chunkingStrategy: str
    chunkingParameter: dict = {}
    embeddingStrategy: str
    embeddingParameter: dict = {}






