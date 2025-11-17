from __future__ import annotations

from typing import Optional, Dict, Any, Tuple
from fastapi import HTTPException
from loguru import logger
import importlib
import os
import tempfile
from urllib.parse import urlparse, unquote
import httpx
import uuid
import hashlib
from sqlalchemy import text

from app.schemas.request.extractRequest import ExtractProcessRequest
from app.service.minio_client import ensure_bucket, put_object_bytes
from app.models.database import AsyncSessionLocal


INGEST_BUCKET = "ingest"


class ExtractService:
    @staticmethod
    def get_strategy(strategy_name: str, file_type: str, parameters: Dict[Any, Any] = None) -> Any:
        """
        전략 이름으로 전략 클래스 동적 로드 및 인스턴스 생성
        """
        try:
            strategy_module_name = f"app.src.{strategy_name}"
            logger.debug(f"Attempting to import module: {strategy_module_name}")
            strategy_module = importlib.import_module(strategy_module_name)

            strategy_class_name = strategy_name[0].upper() + strategy_name[1:] if strategy_name else ""
            logger.debug(f"Looking for class: {strategy_class_name} in module {strategy_module_name}")
            if not hasattr(strategy_module, strategy_class_name):
                available_classes = [
                    name for name in dir(strategy_module)
                    if not name.startswith('_') and isinstance(getattr(strategy_module, name, None), type)
                ]
                logger.error(f"Class '{strategy_class_name}' not found in module {strategy_module_name}. Available: {available_classes}")
                raise AttributeError(f"Class '{strategy_class_name}' not found")

            strategy_class = getattr(strategy_module, strategy_class_name)
            strategy_instance = strategy_class(parameters=parameters)
            logger.info(f"Loaded strategy: {strategy_class_name} (module: {strategy_module_name}) for file type: {file_type}")
            return strategy_instance

        except ModuleNotFoundError as e:
            logger.error(f"Strategy module not found: {strategy_module_name}, error: {str(e)}")
            raise HTTPException(status_code=404, detail=f"Extraction strategy module '{strategy_name}' not found: {str(e)}")
        except AttributeError as e:
            logger.error(f"Strategy class '{strategy_class_name}' not found in module {strategy_module_name}, error: {str(e)}")
            raise HTTPException(status_code=404, detail=f"Extraction strategy class '{strategy_class_name}' not found in module '{strategy_name}': {str(e)}")
        except Exception as e:
            logger.error(f"Error loading strategy '{strategy_name}': {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error loading extraction strategy '{strategy_name}': {str(e)}")

    @staticmethod
    async def download_file_via_presigned(file_no: str, presigned_endpoint: str, forward_headers: Dict[str, str]) -> Tuple[str, str, str]:
        """
        presigned URL을 통해 파일을 다운로드하고 임시경로에 저장
        Returns: (tmp_path, file_name, file_ext)
        """
        tmp_path = None
        try:
            async with httpx.AsyncClient(timeout=3600.0) as client:
                presigned_resp = await client.get(presigned_endpoint, headers=forward_headers)
                presigned_resp.raise_for_status()
                try:
                    data = presigned_resp.json()
                    presigned_url = data.get("result", {}).get("data", {}).get("url")
                except Exception:
                    presigned_url = presigned_resp.text.strip().strip('"')
                if not presigned_url:
                    raise HTTPException(status_code=500, detail="Failed to resolve presigned URL")

                dl_resp = await client.get(presigned_url)
                dl_resp.raise_for_status()

                file_name = None
                content_disp = dl_resp.headers.get("content-disposition") or dl_resp.headers.get("Content-Disposition")
                if content_disp and "filename=" in content_disp:
                    file_name = content_disp.split("filename=")[-1].strip().strip('";')
                if not file_name:
                    parsed = urlparse(presigned_url)
                    tail = os.path.basename(unquote(parsed.path))
                    file_name = tail or file_no
                file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ""

                suffix = f".{file_ext}" if file_ext else ""
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                    tmp_file.write(dl_resp.content)
                    tmp_path = tmp_file.name
                return tmp_path, file_name, file_ext
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Failed to get presigned/download URL: {str(e)}")
        except Exception as e:
            logger.error(f"Error while downloading file via presigned: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Error while downloading file: {str(e)}")

    async def process_request(
        self,
        request: ExtractProcessRequest,
        x_user_role: Optional[str],
        x_user_uuid: Optional[str],
        x_offer_no: Optional[str],
        progress_pusher,
    ) -> Dict[str, Any]:
        """
        Extract 처리 핵심 로직: presigned 다운로드 -> 전략 로드 -> extract 호출 -> 결과 dict 반환
        """
        strategy_name = request.extractionStrategy
        parameters = request.extractionParameter

        # 1) presigned URL 획득 및 다운로드
        file_no = request.fileNo
        if not file_no:
            raise HTTPException(status_code=400, detail="fileNo is required")

        forward_headers: Dict[str, str] = {}
        if x_user_role:
            forward_headers["x-user-role"] = x_user_role
        if x_user_uuid:
            forward_headers["x-user-uuid"] = x_user_uuid
        
        presigned_endpoint = f"http://hebees-python-backend:8000/api/v1/files/{file_no}/presigned"
        tmp_path, file_name, file_ext = await self.download_file_via_presigned(file_no, presigned_endpoint, forward_headers)
        if not file_ext:
            raise HTTPException(status_code=400, detail="파일 확장자를 확인할 수 없습니다.")

        logger.info(f"Processing file: {file_name} (type: {file_ext}, path: {tmp_path}, strategy: {strategy_name})")

        # 2) 지원 타입 확인
        if file_ext not in ["txt", "xlsx", "xls", "pdf", "docx", "pptx", "ppt", "html", "htm"]:
            raise HTTPException(status_code=400, detail=f"지원하지 않는 파일 타입: {file_ext}. 지원 타입: txt, xlsx, pdf, docs")

        # 3) 전략 파라미터 구성 (progress_cb 주입)
        strategy_params = dict(parameters) if isinstance(parameters, dict) else {}

        def _progress_cb(processed: int, total: Optional[int] = None) -> None:
            try:
                progress_pusher.advance(int(processed), int(total) if total is not None else None)
            except Exception:
                pass

        strategy_params["progress_cb"] = _progress_cb
        # 각 전략이 MinIO 업로드를 직접 수행할 수 있도록 메타 전달
        strategy_params["user_id"] = (x_user_uuid or "").strip() or "unknown-user"
        strategy_params["file_name"] = file_name

        # 4) 전략 로드
        strategy = self.get_strategy(strategy_name, file_ext, strategy_params)
        
        # 5) extract 호출
        try:
            progress_pusher.start()
            result = strategy.extract(tmp_path)
            progress_pusher.complete()
        except Exception as e:
            try:
                progress_pusher.fail()
            except Exception:
                pass
            raise
        finally:
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception:
                pass

        # 6) 업로드는 각 전략에서 수행 → 결과에서 bucket/path 추출
        bucket = None
        path = None
        if isinstance(result, dict):
            bucket = result.get("bucket")
            path = result.get("path")
        
        # 7) 이미지 메타를 FILE DB에 기록 (가능한 경우)
        # - FILE_CATEGORY_NO: 고정 UUID (이미지 카테고리)
        # - OFFER_NO: extractionParameter.offerNo 또는 기본값
        # - USER_NO: x_user_uuid
        # - SOURCE_NO: request.fileNo
        # - STATUS: 'COMPLETED'
        try:
            images = (result or {}).get("images") if isinstance(result, dict) else None
            captions = (result or {}).get("captions") if isinstance(result, dict) else {}
            if images:
                # 우선순위: 헤더(x-offer-no) > 요청 파라미터(extractionParameter.offerNo) > 기본값
                offer_no = ""
                try:
                    offer_no = (x_offer_no or "").strip()
                except Exception:
                    offer_no = ""
                if not offer_no:
                    try:
                        offer_no = str((request.extractionParameter or {}).get("offerNo", "")).strip()
                    except Exception:
                        offer_no = ""
                if not offer_no:
                    # 기본값 (admin 등)
                    offer_no = "0000000000"
                user_no_bytes = None
                try:
                    if x_user_uuid:
                        user_no_bytes = uuid.UUID(x_user_uuid).bytes
                except Exception:
                    user_no_bytes = None
                source_no_bytes = None
                try:
                    if request.fileNo:
                        source_no_bytes = uuid.UUID(request.fileNo).bytes
                except Exception:
                    source_no_bytes = None
                category_uuid = uuid.UUID("797c1dee-b888-11f0-a5ea-0e6c5c03bab1").bytes

                # COLLECTION_NO는 이미지 파일에 대해 항상 NULL로 저장 (요청에 따라 고정)
                collection_no_bytes = None

                # INSERT
                async with AsyncSessionLocal() as session:
                    params = []
                    for img in images:
                        try:
                            file_no_bytes = uuid.uuid4().bytes
                            name = img.get("name") or ""
                            obj = img.get("object_name") or ""
                            bkt = img.get("bucket") or INGEST_BUCKET
                            size = int(img.get("size") or 0)
                            hsh = img.get("hash") or ""
                            typ = img.get("type") or "png"
                            uid = img.get("uid")
                            desc = ""
                            if uid and isinstance(captions, dict):
                                desc = captions.get(uid, "") or ""
                            if not desc:
                                desc = f"Extracted image ({typ})"

                            p = {
                                "file_no": file_no_bytes,
                                "offer_no": offer_no[:10],
                                "user_no": user_no_bytes,
                                "name": name[:255],
                                "size": size,
                                "type": typ[:20],
                                "hash": hsh[:255],
                                "description": desc,
                                "bucket": bkt[:255],
                                "path": obj[:255],
                                "file_category_no": category_uuid,
                                "source_no": source_no_bytes,
                                "status": "COMPLETED",
                            }
                            # COLLECTION_NO는 항상 NULL로 저장 → 파라미터에 추가하지 않음
                            params.append(p)
                        except Exception:
                            continue

                    if params:
                        # COLLECTION_NO는 INSERT 대상에서 제외 (항상 NULL 저장)
                        sql = text(
                            "INSERT INTO `FILE` "
                            "(`FILE_NO`,`OFFER_NO`,`USER_NO`,`NAME`,`SIZE`,`TYPE`,`HASH`,`DESCRIPTION`,`BUCKET`,`PATH`,`FILE_CATEGORY_NO`,`SOURCE_NO`,`STATUS`,`CREATED_AT`,`UPDATED_AT`) "
                            "VALUES (:file_no,:offer_no,:user_no,:name,:size,:type,:hash,:description,:bucket,:path,:file_category_no,:source_no,:status,NOW(),NOW())"
                        )
                        await session.execute(sql, params)
                        await session.commit()
        except Exception as e:
            # DB 에러는 전체 플로우를 막지 않음 (로그만 남김)
            logger.warning(f"[DB] Failed to insert image FILE rows: {e}")

        return {
            "file_name": file_name,
            "file_ext": file_ext,
            "strategy": strategy_name,
            "strategy_parameter": parameters,
            "bucket": bucket,
            "path": path,
        }


