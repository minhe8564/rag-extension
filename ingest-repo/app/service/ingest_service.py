from app.service.gateway_client import GatewayClient
from app.service.file_service import FileService
from app.schemas.request.ingestRequest import IngestRequest
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from loguru import logger


class IngestService:
    def __init__(self):
        self.gateway_client = GatewayClient()
        self.file_service = FileService()
    
    async def process_ingest(
        self, 
        request: IngestRequest, 
        db: AsyncSession
    ) -> Dict[Any, Any]:
        """Ingest 요청 처리: 각 파일을 순차로 Extract -> Chunking -> Embedding 처리"""

        logger.info("Starting ingest pipeline for {} file(s)", len(request.file))
        # 파일 ID로 파일 정보 조회
        files = await self.file_service.get_files_by_ids(db, request.file)

        if not files:
            raise ValueError(f"No files found for IDs: {request.file}")

        # 파일 타입별로 분류해두고, 입력된 순서대로 타입을 역참조
        files_by_type = self.file_service.group_files_by_type(files)

        def resolve_file_type(file_id: int) -> str:
            file_id_str = str(file_id)
            if file_id_str in files_by_type.get("pdf", []):
                return "pdf"
            if file_id_str in files_by_type.get("xlsx", []):
                return "xlsx"
            if file_id_str in files_by_type.get("docs", []):
                return "docs"
            if file_id_str in files_by_type.get("txt", []):
                return "txt"
            return "txt"

        pipeline_results = []

        for file_id in request.file:
            logger.info("Processing file {}", file_id)
            ftype = resolve_file_type(file_id)
            if ftype == "pdf":
                extraction_strategy = request.extractionPdf
                extraction_params = request.extractionPdfParameter
            elif ftype == "xlsx":
                extraction_strategy = request.extractionXlsx
                extraction_params = request.extractionXlsxParameter
            elif ftype == "docs":
                extraction_strategy = request.extractionDocs
                extraction_params = request.extractionDocsParameter
            else:
                extraction_strategy = request.extractionTxt
                extraction_params = request.extractionTxtParameter

            # 1) 단일 파일 추출
            logger.debug("Extracting file {} with type {}", file_id, ftype)
            extraction_result = await self.gateway_client.request_extraction(
                file_ids=[file_id],
                extraction_strategy=extraction_strategy,
                extraction_params=extraction_params,
            )

            # 2) 단일 파일 청킹
            logger.debug("Chunking file {}", file_id)
            chunking_result = await self.gateway_client.request_chunking(
                data=extraction_result,
                strategy=request.chunkingStrategy,
                parameters=request.chunkingParameter,
            )

            # 3) 단일 파일 임베딩
            logger.debug("Embedding file {}", file_id)
            # 파일 정보에서 FILE_NO와 파일명 가져오기
            file_id_str = str(file_id)
            file_info = next((f for f in files if (f.file_no.hex() if isinstance(f.file_no, bytes) else str(f.file_no)) == file_id_str), None)
            
            if file_info:
                file_no = file_info.file_no.hex() if isinstance(file_info.file_no, bytes) else str(file_info.file_no)
                file_name = file_info.name if hasattr(file_info, 'name') else f"file_{file_id}"
            else:
                file_no = file_id_str
                file_name = f"file_{file_id}"
            
            embedding_result = await self.gateway_client.request_embedding(
                data=chunking_result,
                collection_name=request.collection.name,
                file_name=file_name,
                file_no=file_no,
                strategy=request.embeddingStrategy,
                parameters=request.embeddingParameter,
            )

            pipeline_results.append(
                {
                    "fileId": file_id,
                    "extraction": extraction_result,
                    "chunking": chunking_result,
                    "embedding": embedding_result,
                }
            )

        return {
            "pipelineResults": pipeline_results,
            "collection": {
                "name": request.collection.name,
                "numberList": request.collection.numberList,
            },
        }

