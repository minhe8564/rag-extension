from typing import List, Optional
from pydantic import BaseModel
from .collectionRequest import CollectionRequest

class IngestRequest(BaseModel):
    file: List[int]
    collection: CollectionRequest
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

