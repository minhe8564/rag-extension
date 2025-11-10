from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Header
from app.schemas.request.extractRequest import ExtractProcessRequest
from app.schemas.response.extractProcessResponse import ExtractProcessResponse, ExtractProcessResult, Page
from app.schemas.response.extractTestResponse import ExtractTestResponse, ExtractTestResult
from app.schemas.response.errorResponse import ErrorResponse
from typing import Optional, Dict, Any
import json
import importlib
from loguru import logger

router = APIRouter(tags=["extract"])


def get_strategy(strategy_name: str, file_type: str, parameters: Dict[Any, Any] = None) -> Any:
    """
    전략 이름으로 전략 클래스 동적 로드 및 인스턴스 생성
    
    Args:
        strategy_name: 전략 이름 (예: "pyMuPDF", "openpyxl", "txt", "docx")
        file_type: 파일 타입 (txt, xlsx, pdf, docs, docx) - 로깅용
        parameters: 전략 파라미터
    
    Returns:
        전략 클래스 인스턴스
    """
    try:
        # 전략명으로 모듈 import (예: "pyMuPDF" -> app.src.pyMuPDF, "openpyxl" -> app.src.openpyxl)
        strategy_module_name = f"app.src.{strategy_name}"
        logger.debug(f"Attempting to import module: {strategy_module_name}")
        
        strategy_module = importlib.import_module(strategy_module_name)
        logger.debug(f"Module imported successfully: {strategy_module_name}, available attributes: {dir(strategy_module)}")
        
        # 전략 클래스 가져오기 (파일명과 클래스명이 전략명과 동일)
        # 전략명의 첫 글자만 대문자로 변환 (예: "pyMuPDF" -> "PyMuPDF", "openpyxl" -> "Openpyxl", "txt" -> "Txt")
        strategy_class_name = strategy_name[0].upper() + strategy_name[1:] if strategy_name else ""
        logger.debug(f"Looking for class: {strategy_class_name} in module {strategy_module_name}")
        
        if not hasattr(strategy_module, strategy_class_name):
            available_classes = [name for name in dir(strategy_module) if not name.startswith('_') and isinstance(getattr(strategy_module, name, None), type)]
            logger.error(f"Class '{strategy_class_name}' not found in module {strategy_module_name}. Available classes: {available_classes}")
            raise AttributeError(f"Class '{strategy_class_name}' not found")
        
        strategy_class = getattr(strategy_module, strategy_class_name)
        
        # 인스턴스 생성
        strategy_instance = strategy_class(parameters=parameters)
        
        logger.info(f"Loaded strategy: {strategy_class_name} (module: {strategy_module_name}) for file type: {file_type}")
        return strategy_instance
    
    except ModuleNotFoundError as e:
        logger.error(f"Strategy module not found: {strategy_module_name}, error: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Extraction strategy module '{strategy_name}' not found: {str(e)}"
        )
    except AttributeError as e:
        logger.error(f"Strategy class '{strategy_class_name}' not found in module {strategy_module_name}, error: {str(e)}")
        raise HTTPException(
            status_code=404,
            detail=f"Extraction strategy class '{strategy_class_name}' not found in module '{strategy_name}': {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error loading strategy '{strategy_name}': {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error loading extraction strategy '{strategy_name}': {str(e)}"
        )


@router.post("/process")
async def extract_process(request: ExtractProcessRequest, x_user_role: str | None = Header(default=None, alias="x-user-role"), x_user_uuid: str | None = Header(default=None, alias="x-user-uuid"), authorization: str | None = Header(default=None, alias="Authorization")):
    """
    Extract /process 엔드포인트
    - path로 파일 접근
    - extractionStrategy로 전략 클래스 선택
    - extract() 메서드 호출
    """
    try:
        strategy_name = request.extractionStrategy
        parameters = request.extractionParameter

        import os
        import tempfile
        import httpx
        from urllib.parse import urlparse, unquote

        tmp_path = None
        cleanup_tmp = False


        # 1) presigned URL 획득
        file_no = request.fileNo
        presigned_endpoint = f"http://hebees-python-backend:8000/be/api/v1/files/{file_no}/presigned"  # 내부통신용 (주석)
        logger.info(f"Fetching presigned URL: {presigned_endpoint}")
        async with httpx.AsyncClient(timeout=3600.0) as client:
            # 전달받은 헤더를 그대로 /be 호출에 포함
            forward_headers = {}
            if x_user_role: 
                forward_headers["x-user-role"] = x_user_role   # 내부통신 시 사용 (주석)
            if x_user_uuid: 
                forward_headers["x-user-uuid"] = x_user_uuid   # 내부통신 시 사용 (주석)
            presigned_resp = await client.get(presigned_endpoint, headers=forward_headers)
            presigned_resp.raise_for_status()
            presigned_url = None
            try:
                data = presigned_resp.json()
                presigned_url = (
                    data.get("result", {}).get("data", {}).get("url")
                )
            except Exception:
                presigned_url = presigned_resp.text.strip().strip('"')
            if not presigned_url:
                raise HTTPException(status_code=500, detail="Failed to resolve presigned URL")
            logger.info("presigned URL fetched")
            logger.info(f"presigned URL: {presigned_url}")
            
            # 2) 파일 다운로드
            dl_resp = await client.get(presigned_url)
            logger.info(f"file download started")
            dl_resp.raise_for_status()
            logger.info(f"file download completed")
            # 파일명/확장자 결정
            file_name = None
            content_disp = dl_resp.headers.get("content-disposition") or dl_resp.headers.get("Content-Disposition")
            if content_disp and "filename=" in content_disp:
                file_name = content_disp.split("filename=")[-1].strip().strip('";')
            if not file_name:
                parsed = urlparse(presigned_url)
                tail = os.path.basename(unquote(parsed.path))
                file_name = tail or file_no
            file_ext = file_name.split('.')[-1].lower() if '.' in file_name else ""

            # 임시 파일 저장
            suffix = f".{file_ext}" if file_ext else ""
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(dl_resp.content)
                tmp_path = tmp_file.name
            cleanup_tmp = True
            file_path = tmp_path
            logger.info(f"file download completed")
        
        if not file_ext:
            error_response = ErrorResponse(
                status=400,
                code="VALIDATION_ERROR",
                message="요청 파라미터가 유효하지 않습니다.",
                isSuccess=False,
                result={"file": "파일 확장자를 확인할 수 없습니다."}
            )
            raise HTTPException(status_code=400, detail=error_response.dict())

        logger.info(f"Processing file: {file_name} (type: {file_ext}, path: {file_path}, strategy: {strategy_name})")

        # 지원되는 파일 타입 확인
        if file_ext not in ["txt", "xlsx", "xls", "pdf", "docs", "doc", "docx"]:
            error_response = ErrorResponse(
                status=400,
                code="VALIDATION_ERROR",
                message="요청 파라미터가 유효하지 않습니다.",
                isSuccess=False,
                result={"fileType": f"지원하지 않는 파일 타입: {file_ext}. 지원 타입: txt, xlsx, pdf, docs"}
            )
            raise HTTPException(status_code=400, detail=error_response.dict())

        # 전략 로드 (전략 이름 + 파일 타입 조합)
        logger.info(f"Extraction strategy: {strategy_name}, parameters: {parameters}")
        strategy = get_strategy(strategy_name, file_ext, parameters)
        logger.info("strategy: {}", strategy)
        # extract() 메서드 호출
        try:
            result = strategy.extract(file_path)
        finally:
            # 임시 파일 정리
            if cleanup_tmp and tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)

        # Response 생성
        pages = [
            Page(
                page=page.get("page", i + 1),
                content=page.get("content", "")
            )
            for i, page in enumerate(result.get("pages", []))
        ]
        
        response = ExtractProcessResponse(
            status=200,
            code="OK",
            message="요청에 성공하였습니다.",
            isSuccess=True,
            result=ExtractProcessResult(
                fileName=file_name,
                fileType=file_ext,
                pages=pages,
                total_pages=result.get("total_pages", len(pages)),
                strategy=strategy_name,
                strategyParameter=parameters
            )
        )
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}", exc_info=True)
        error_response = ErrorResponse(
            status=500,
            code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())


@router.post("/test")
async def extract_test(
    file: UploadFile = File(..., description="업로드할 파일"),
    extractionStrategy: str = Form(..., description="추출 전략"),
    extractionParameter: Optional[str] = Form(default="{}", description="추출 파라미터 (JSON 문자열)")
):
    """
    Extract /test 엔드포인트
    - UploadFile에서 file_type 자동 감지
    - extractionStrategy와 file_type으로 전략 클래스 선택
    - extract() 메서드 호출 (임시 파일 저장 후 처리)
    """
    from app.schemas.response.extractTestResponse import ExtractTestResponse, ExtractTestResult, Page
    
    try:
        # 파일 확장자로 타입 감지
        filename = file.filename or "unknown"
        file_ext = filename.split('.')[-1].lower() if '.' in filename else ""
        
        if not file_ext:
            error_response = ErrorResponse(
                status=400,
                code="VALIDATION_ERROR",
                message="요청 파라미터가 유효하지 않습니다.",
                isSuccess=False,
                result={"file": "파일 확장자를 확인할 수 없습니다."}
            )
            raise HTTPException(status_code=400, detail=error_response.dict())
        
        logger.info(f"Processing uploaded file: {filename} (detected type: {file_ext}, strategy: {extractionStrategy})")

        # 파라미터 파싱
        parameters = {}
        if extractionParameter:
            try:
                parameters = json.loads(extractionParameter)
            except json.JSONDecodeError as e:
                error_response = ErrorResponse(
                    status=400,
                    code="VALIDATION_ERROR",
                    message="요청 파라미터가 유효하지 않습니다.",
                    isSuccess=False,
                    result={"extractionParameter": f"JSON 파싱 오류: {str(e)}"}
                )
                raise HTTPException(status_code=400, detail=error_response.dict())

        # 파일 내용 읽기
        file_content = await file.read()
        
        # 전략 로드 (전략 이름 + 파일 타입 조합)
        strategy = get_strategy(extractionStrategy, file_ext, parameters)
        
        # 임시 파일로 저장 후 extract() 호출
        import tempfile
        import os
        
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_ext}") as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name
        
        try:
            # extract() 메서드 호출
            result = strategy.extract(tmp_path)
        finally:
            # 임시 파일 삭제
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        # Response 생성
        pages = [
            Page(
                page=page.get("page", i + 1),
                content=page.get("content", "")
            )
            for i, page in enumerate(result.get("pages", []))
        ]
        
        response = ExtractTestResponse(
            status=200,
            code="OK",
            message="요청에 성공하였습니다.",
            isSuccess=True,
            result=ExtractTestResult(
                fileName=filename,
                fileType=file_ext,
                pages=pages,
                total_pages=result.get("total_pages", len(pages)),
                strategy=extractionStrategy,  # 확장자에 따라 선택된 전략
                strategyParameter=parameters
            )
        )
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing uploaded file: {str(e)}", exc_info=True)
        error_response = ErrorResponse(
            status=500,
            code="INTERNAL_ERROR",
            message=f"Internal server error: {str(e)}",
            isSuccess=False,
            result={}
        )
        raise HTTPException(status_code=500, detail=error_response.dict())