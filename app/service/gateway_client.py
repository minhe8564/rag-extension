import httpx
from typing import Dict, Any, List
from app.core.settings import settings
import json
from loguru import logger


class GatewayClient:
    def __init__(self):
        # settings에서 서비스 URL 로드
        self.gateway_url = settings.gateway_url
        self.extract_service_url = settings.extract_service_url
        self.chunking_service_url = settings.chunking_service_url
        self.embedding_service_url = settings.embedding_service_url
        self.query_embedding_service_url = settings.query_embedding_service_url
        self.search_service_url = settings.search_service_url
        self.cross_encoder_service_url = settings.cross_encoder_service_url
        self.generation_service_url = settings.generation_service_url
        
        # 서비스 간 직접 통신 URL (Gateway를 거치지 않음)
        self.extraction_direct_url = f"{self.extract_service_url}/process"
        self.chunking_direct_url = f"{self.chunking_service_url}/process"
        self.embedding_direct_url = f"{self.embedding_service_url}/process"
        self.query_embedding_direct_url = f"{self.query_embedding_service_url}/process"
        self.search_direct_url = f"{self.search_service_url}/process"
        self.cross_encoder_direct_url = f"{self.cross_encoder_service_url}/process"
        self.generation_direct_url = f"{self.generation_service_url}/process"
    
    async def request_extraction(
        self,
        file_ids: list,
        extraction_strategy: str,
        extraction_params: dict
    ) -> Dict[Any, Any]:
        """Extraction 컨테이너로 요청 - 서비스 간 직접 통신"""
        logger.debug(f"POST {self.extraction_direct_url} | extractionStrategy={extraction_strategy}")
        async with httpx.AsyncClient(timeout=3600.0) as client:
            # Extract 서비스에 직접 접근 (서비스 간 통신이므로 인증 불필요)
            response = await client.post(
                self.extraction_direct_url,
                json={
                    "file": file_ids,
                    "extractionStrategy": extraction_strategy,
                    "extractionParameter": extraction_params
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def request_extraction_by_path(
        self,
        path: str,
        extraction_strategy: str,
        extraction_params: dict
    ) -> Dict[Any, Any]:
        """Extraction 컨테이너로 요청 - 경로 기반 /process 사용 (서비스 간 직접 통신)"""
        logger.debug(f"POST {self.extraction_direct_url} | extractionStrategy={extraction_strategy} path={path}")
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.post(
                self.extraction_direct_url,
                json={
                    "path": path,
                    "extractionStrategy": extraction_strategy,
                    "extractionParameter": extraction_params or {}
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def request_extraction_by_file_no(
        self,
        file_no: str,
        extraction_strategy: str,
        extraction_params: dict,
        extra_headers: Dict[str, Any] = None
    ) -> Dict[Any, Any]:
        """Extraction 컨테이너로 요청 - fileNo 기반 /process 사용 (서비스 간 직접 통신)"""
        logger.debug(f"POST {self.extraction_direct_url} | extractionStrategy={extraction_strategy} fileNo={file_no}")
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.post(
                self.extraction_direct_url,
                headers={k: v for k, v in (extra_headers or {}).items() if v},
                json={
                    "fileNo": file_no,
                    "extractionStrategy": extraction_strategy,
                    "extractionParameter": extraction_params or {}
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def request_extraction_with_file(
        self,
        file_content: bytes,
        filename: str,
        extraction_strategy: str,
        extraction_params: dict,
        content_type: str = None
    ) -> Dict[Any, Any]:
        """파일을 직접 받아서 Extract 서비스로 전송 (multipart/form-data) - 서비스 간 직접 통신"""
        logger.debug(f"POST {self.extraction_direct_url} (multipart) | filename={filename} extractionStrategy={extraction_strategy}")
        async with httpx.AsyncClient(timeout=3600.0) as client:
            # multipart/form-data로 파일과 메타데이터 전송
            files = {
                "file": (filename, file_content, content_type or "application/octet-stream")
            }
            data = {
                "extractionStrategy": extraction_strategy,
                "extractionParameter": json.dumps(extraction_params) if extraction_params else "{}"
            }
            
            # Extract 서비스에 직접 접근 (서비스 간 통신이므로 인증 불필요)
            logger.info(f"POST {self.extraction_direct_url} (multipart) | filename={filename} extractionStrategy={extraction_strategy}")
            response = await client.post(
                self.extraction_direct_url,
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json()
    
    async def request_chunking(
        self,
        data: Dict[Any, Any],
        strategy: str,
        parameters: dict
    ) -> Dict[Any, Any]:
        """Chunking 컨테이너로 요청 - 서비스 간 직접 통신"""
        logger.debug(f"POST {self.chunking_direct_url} | chunkingStrategy={strategy}")
        
        # extraction_result에서 pages 형식으로 변환
        # extract-repo의 응답 형식: {"result": {...}} 또는 직접 결과
        # data가 이미 pages 리스트인 경우도 있음 (ingest_router.py에서 처리한 경우)
        if isinstance(data, list):
            # 이미 pages 형식인 경우
            pages = data
        else:
            # extraction_result에서 result 추출
            extraction_data = data.get("result", data) if isinstance(data, dict) else data
            
            # pages 필드가 있으면 사용 (PDF 등)
            if isinstance(extraction_data, dict) and "pages" in extraction_data:
                pages = extraction_data["pages"]
            elif isinstance(extraction_data, dict) and "content" in extraction_data:
                # content만 있는 경우 (TXT, DOCX, XLSX 등) pages 형식으로 변환
                pages = [{"page": 1, "content": extraction_data["content"]}]
            else:
                # 다른 형식인 경우 기본 처리
                pages = [{"page": 1, "content": str(extraction_data)}]
        
        async with httpx.AsyncClient(timeout=3600.0) as client:
            # Chunking 서비스에 직접 접근 (서비스 간 통신이므로 인증 불필요)
            response = await client.post(
                self.chunking_direct_url,
                json={
                    "pages": pages,
                    "chunkingStrategy": strategy,
                    "chunkingParameter": parameters
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def request_embedding(
        self,
        data: Dict[Any, Any],
        collection_name: str,
        collection_no: str = None,
        file_name: str = None,
        file_no: str = None,
        strategy: str = None,
        parameters: dict = None,
        bucket: str = None,
        extra_headers: Dict[str, Any] = None
    ) -> Dict[Any, Any]:
        """Embedding 컨테이너로 요청 - 서비스 간 직접 통신"""
        logger.debug(f"POST {self.embedding_direct_url} | embeddingStrategy={strategy}")
        # chunking_result에서 chunks 형식으로 변환
        # chunking-repo의 응답 형식: {"chunks": [...], ...}
        async with httpx.AsyncClient(timeout=3600.0) as client:
            # Embedding 서비스에 직접 접근 (서비스 간 통신이므로 인증 불필요)
            request_data = {
                "chunks": data.get("result", {}).get("chunks", []),
                "collectionName": collection_name,
                "collectionNo": collection_no,
                "fileName": file_name,
                "fileNo": file_no,
                "embeddingStrategy": strategy,
                "embeddingParameter": parameters or {},
                "bucket": bucket
            }
            if file_no:
                request_data["fileNo"] = file_no
            
            response = await client.post(
                self.embedding_direct_url,
                json=request_data,
                headers={k: v for k, v in (extra_headers or {}).items() if v}
            )
            response.raise_for_status()
            return response.json()

    async def request_query_embedding(
        self,
        query: str,
        strategy: str,
        parameters: dict
    ) -> Dict[Any, Any]:
        """Query Embedding 컨테이너로 요청 - 서비스 간 직접 통신"""
        logger.debug(f"POST {self.query_embedding_direct_url} | queryEmbeddingStrategy={strategy}")
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.post(
                self.query_embedding_direct_url,
                json={
                    "query": query,
                    "queryEmbeddingStrategy": strategy,
                    "queryEmbeddingParameter": parameters
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def request_search(
        self,
        embedding: List[float],
        collection_name: str,
        strategy: str = "basic",
        parameters: dict = None
    ) -> Dict[Any, Any]:
        """Search 컨테이너로 요청 - 서비스 간 직접 통신"""
        logger.debug(f"POST {self.search_direct_url} | searchStrategy={strategy}")
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.post(
                self.search_direct_url,
                json={
                    "embedding": embedding,
                    "collectionName": collection_name,
                    "searchStrategy": strategy,
                    "searchParameter": parameters or {}
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def request_cross_encoder(
        self,
        query: str,
        candidate_embeddings: List[Dict[Any, Any]],
        strategy: str,
        parameters: dict
    ) -> Dict[Any, Any]:
        """Cross Encoder 컨테이너로 요청 - 서비스 간 직접 통신"""
        logger.debug(f"POST {self.cross_encoder_direct_url} | crossEncoderStrategy={strategy}")
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.post(
                self.cross_encoder_direct_url,
                json={
                    "query": query,
                    "candidateEmbeddings": candidate_embeddings,
                    "crossEncoderStrategy": strategy,
                    "crossEncoderParameter": parameters
                }
            )
            response.raise_for_status()
            return response.json()
    
    async def request_generation(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        strategy: str,
        parameters: dict
    ) -> Dict[Any, Any]:
        """Generation 컨테이너로 요청 - 서비스 간 직접 통신"""
        logger.debug(f"POST {self.generation_direct_url} | generationStrategy={strategy}")
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.post(
                self.generation_direct_url,
                json={
                    "query": query,
                    "retrievedChunks": retrieved_chunks,
                    "generationStrategy": strategy,
                    "generationParameter": parameters
                }
            )
            response.raise_for_status()
            return response.json()

    async def upload_files(self, files: list) -> Dict[Any, Any]:
        """게이트웨이를 통해 파일 컨테이너로 전송하여 MinIO에 업로드하고 파일 ID 반환"""
        # files 항목은 (name, fileobj, content_type) 형태의 튜플 리스트를 기대
        async with httpx.AsyncClient(timeout=3600.0) as client:
            response = await client.post(
                self.file_upload_url,
                files=files
            )
            response.raise_for_status()
            return response.json()

