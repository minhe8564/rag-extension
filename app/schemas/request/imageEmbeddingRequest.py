from pydantic import BaseModel
from typing import Optional


class ImageEmbeddingProcessRequest(BaseModel):
    """Image Embedding /process/image 요청 스키마"""
    fileNo: str  # 문서의 FILE_NO
    userNo: str  # USER_NO
    collectionName: str  # h{offerNo}_image_{versionNo} 또는 publicRetina_image_{versionNo}
    collectionNo: Optional[str] = None
    bucket: Optional[str] = None  # "public" 또는 "hebees" (publicRetina_image의 경우)
    partition: Optional[str] = None  # "public" 또는 "hebees" (publicRetina_image의 경우)

