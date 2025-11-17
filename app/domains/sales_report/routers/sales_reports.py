"""Sales Report API Router"""
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from datetime import date
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from app.core.database import get_db
from app.core.schemas import BaseResponse, Result
from app.domains.sales_report.services.store_summary_service import StoreSummaryService
from app.domains.sales_report.services.chain_summary_service import ChainSummaryService
from app.domains.sales_report.schemas.response.store_summary_response import StoreSummaryData
from app.domains.sales_report.schemas.request.store_summary_request import StoreSummaryRequest
from app.domains.sales_report.schemas.request.chain_summary_request import ChainSummaryRequest
from app.domains.sales_report.schemas.response.chain_summary_response import ChainSummaryData
from app.domains.sales_report.exceptions import (
    DataValidationError,
    LLMServiceError,
    RunpodNotFoundError
)
from app.domains.sales_report.services.llm.validators import CustomPromptValidator
from app.domains.sales_report.services.llm.validators import CustomPromptValidator


router = APIRouter(prefix="/sales-reports", tags=["sales-reports"])

# 템플릿 디렉토리 설정
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))


@router.post("/store-summary", response_model=BaseResponse[Result[StoreSummaryData]])
async def generate_store_summary(
    request: StoreSummaryRequest,
    start_date: Optional[date] = Query(None, description="조회 시작일 (YYYY-MM-DD, 선택사항)"),
    end_date: Optional[date] = Query(None, description="조회 종료일 (YYYY-MM-DD, 선택사항)"),
    start_date: Optional[date] = Query(None, description="조회 시작일 (YYYY-MM-DD, 선택사항)"),
    end_date: Optional[date] = Query(None, description="조회 종료일 (YYYY-MM-DD, 선택사항)"),
    skip_ai: bool = Query(True, description="AI 요약 생략 여부 (기본값: True)"),
    db: AsyncSession = Depends(get_db)
):
    """
    개별 안경원 매출 요약 리포트 생성

    프론트엔드나 다른 서비스에서 이미 가져온 데이터를 그대로 전달받아
    리포트를 생성합니다. 외부 API 의존성이 없어 빠른 응답이 가능합니다.

    Args:
        request: 매장 정보와 거래 데이터를 포함한 요청 바디
        start_date: 조회 시작일 (선택사항)
        end_date: 조회 종료일 (선택사항)
        start_date: 조회 시작일 (선택사항)
        end_date: 조회 종료일 (선택사항)
        skip_ai: AI 요약 생략 여부 (True: 즉시 응답, False: AI 요약 포함하여 40-50초 소요)
        db: DB 세션

    Returns:
        매출 리포트 (기간별 집계 데이터, daily_report는 최대 매출일 기준)
        매출 리포트 (기간별 집계 데이터, daily_report는 최대 매출일 기준)

    Example Request:
        POST /api/v1/sales-reports/store-summary?start_date=2025-10-01&end_date=2025-10-31&skip_ai=true
        POST /api/v1/sales-reports/store-summary?start_date=2025-10-01&end_date=2025-10-31&skip_ai=true

        Body:
        {
            "custom_prompt": "JSON 형식으로 한국어로만 작성해주세요...",
            "json": {
                "info": {
                    "안경원명": "행복안경원",
                    "매장번호": "02-1234-5678",
                    "대표자명": "홍길동"
                },
                "data": [
                    {
                        "판매일자": "2025-10-15",
                        "고객명": "김철수",
                        "카드": 150000,
                        "현금": 0,
                        "현금영수": 0,
                        "상품권금액": 0,
                        "미수금액": 0
                    }
                ]
            }
            "custom_prompt": "JSON 형식으로 한국어로만 작성해주세요...",
            "json": {
                "info": {
                    "안경원명": "행복안경원",
                    "매장번호": "02-1234-5678",
                    "대표자명": "홍길동"
                },
                "data": [
                    {
                        "판매일자": "2025-10-15",
                        "고객명": "김철수",
                        "카드": 150000,
                        "현금": 0,
                        "현금영수": 0,
                        "상품권금액": 0,
                        "미수금액": 0
                    }
                ]
            }
        }
    """
    try:
        # 커스텀 프롬프트 검증
        validated_prompt = None

        if request.custom_prompt:
            level, sanitized, message = CustomPromptValidator.validate_and_sanitize(
                request.custom_prompt
            )

            if level == "danger":
                # 위험 패턴 감지 → 즉시 거부
                raise HTTPException(
                    status_code=400,
                    detail=f"커스텀 프롬프트 검증 실패: {message}"
                )
            else:  # level == "ok"
                # 정상 → 사용
                validated_prompt = sanitized

        # 커스텀 프롬프트 검증
        validated_prompt = None

        if request.custom_prompt:
            level, sanitized, message = CustomPromptValidator.validate_and_sanitize(
                request.custom_prompt
            )

            if level == "danger":
                # 위험 패턴 감지 → 즉시 거부
                raise HTTPException(
                    status_code=400,
                    detail=f"커스텀 프롬프트 검증 실패: {message}"
                )
            else:  # level == "ok"
                # 정상 → 사용
                validated_prompt = sanitized

        service = StoreSummaryService(db=db)

        # 전달받은 데이터로 리포트 생성 (외부 API 호출 없음)
        report = await service.generate_report_from_data(
            store_info=request.json_content.info,
            transactions=request.json_content.data,
            start_date=start_date,  # Query 파라미터로 받은 시작일
            end_date=end_date,  # Query 파라미터로 받은 종료일
            year_month=request.json_content.year_month,
            include_ai_summary=not skip_ai,
            custom_prompt=validated_prompt  # 검증된 프롬프트 전달
            custom_prompt=validated_prompt  # 검증된 프롬프트 전달
        )

        # BaseResponse로 감싸서 반환
        return BaseResponse[Result[StoreSummaryData]](
            status=200,
            code="OK",
            message="개인 안경원 매출 요약 리포트 생성에 성공하였습니다.",
            isSuccess=True,
            result=Result[StoreSummaryData](data=report)
        )

    except HTTPException:
        raise
    except DataValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"데이터 검증 실패: {str(e)}"
        )
    except LLMServiceError as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI 요약 생성 실패: {str(e)}"
        )
    except RunpodNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"LLM 서버를 찾을 수 없습니다: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"리포트 생성 중 오류 발생: {str(e)}"
        )


@router.post("/store-summary-html", response_class=HTMLResponse)
async def generate_store_summary_html(
    fastapi_request: Request,
    request: StoreSummaryRequest,
    start_date: Optional[date] = Query(None, description="조회 시작일 (YYYY-MM-DD, 선택사항)"),
    end_date: Optional[date] = Query(None, description="조회 종료일 (YYYY-MM-DD, 선택사항)"),
    skip_ai: bool = Query(False, description="AI 요약 생략 여부 (기본값: False)"),
    db: AsyncSession = Depends(get_db)
):
    """
    개별 안경원 매출 요약 리포트 생성 (HTML 형식)

    기존 /store-summary API와 동일한 로직이지만,
    JSON 대신 완성된 HTML 페이지를 반환합니다.

    Args:
        fastapi_request: FastAPI Request 객체 (템플릿 렌더링용)
        request: 매장 정보와 거래 데이터를 포함한 요청 바디
        start_date: 조회 시작일 (선택사항)
        end_date: 조회 종료일 (선택사항)
        skip_ai: AI 요약 생략 여부 (기본값: False)
        db: DB 세션

    Returns:
        완성된 HTML 페이지 (Content-Type: text/html)

    Example Request:
        POST /api/v1/sales-reports/store-summary-html?start_date=2025-10-01&end_date=2025-10-10&skip_ai=false

        Body: (기존 store-summary와 동일)
        {
            "custom_prompt": "...",
            "json": { ... }
        }
    """
    try:
        # 커스텀 프롬프트 검증
        validated_prompt = None

        if request.custom_prompt:
            level, sanitized, message = CustomPromptValidator.validate_and_sanitize(
                request.custom_prompt
            )

            if level == "danger":
                raise HTTPException(
                    status_code=400,
                    detail=f"커스텀 프롬프트 검증 실패: {message}"
                )
            else:
                validated_prompt = sanitized

        service = StoreSummaryService(db=db)

        # 리포트 생성 (기존 로직과 동일)
        report = await service.generate_report_from_data(
            store_info=request.json_content.info,
            transactions=request.json_content.data,
            start_date=start_date,
            end_date=end_date,
            year_month=request.json_content.year_month,
            include_ai_summary=not skip_ai,
            custom_prompt=validated_prompt
        )

        # HTML 템플릿에 데이터 주입하여 반환
        return templates.TemplateResponse(
            "store_summary.html",
            {
                "request": fastapi_request,
                "report": report.model_dump(mode='json')  # Pydantic 모델을 JSON 직렬화 가능한 dict로 변환
            }
        )

    except HTTPException:
        raise
    except DataValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"데이터 검증 실패: {str(e)}"
        )
    except LLMServiceError as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI 요약 생성 실패: {str(e)}"
        )
    except RunpodNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"LLM 서버를 찾을 수 없습니다: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"리포트 생성 중 오류 발생: {str(e)}"
        )


@router.post("/chain-summary", response_model=BaseResponse[Result[ChainSummaryData]])
async def generate_chain_summary(
    request: ChainSummaryRequest,
    skip_ai: bool = Query(True, description="AI 인사이트 생략 여부 (기본값: True)"),
    db: AsyncSession = Depends(get_db)
):
    """
    체인 매니저용 매출 종합 분석 리포트 생성

    여러 매장의 매출 데이터를 분석하여 종합 인사이트를 제공합니다.
    LLM을 통해 구조화된 전략 추천을 생성합니다.

    Args:
        request: 체인 매출 분석 요청 (매출 내역, 시간 패턴, 고객 정보, 방문자 데이터)
        skip_ai: AI 인사이트 생략 여부 (True: 즉시 응답, False: AI 인사이트 포함)
        db: DB 세션

    Returns:
        ChainSummaryResponse: 체인 매출 분석 결과 (8개 카테고리)

    Example Request:
        POST /api/v1/sales-reports/chain-summary?skip_ai=true

        Body:
        {
            "custom_prompt": "JSON 형식으로 한국어로만 작성해주세요...",
            "json": {
                "info": {
                    "안경원명": "히비스 안경원",
                    "매장번호": "02-1234-1234",
                    "대표자명": "김안경"
                },
                "sales": {
                    "name": "작년부터 지난달까지",
                    "data": [...]
                },
                "week": {
                    "name": "지난달 일~토",
                    "data": [...]
                },
                "customer": {
                    "name": "3개월 고객 연령대,신규/재방문",
                    "data": [...]
                },
                "product": {
                    "name": "지난달 브랜드,상품구분별 상품정보",
                    "data": [...]
                }
            }
            "custom_prompt": "JSON 형식으로 한국어로만 작성해주세요...",
            "json": {
                "info": {
                    "안경원명": "히비스 안경원",
                    "매장번호": "02-1234-1234",
                    "대표자명": "김안경"
                },
                "sales": {
                    "name": "작년부터 지난달까지",
                    "data": [...]
                },
                "week": {
                    "name": "지난달 일~토",
                    "data": [...]
                },
                "customer": {
                    "name": "3개월 고객 연령대,신규/재방문",
                    "data": [...]
                },
                "product": {
                    "name": "지난달 브랜드,상품구분별 상품정보",
                    "data": [...]
                }
            }
        }
    """
    try:
        service = ChainSummaryService(db=db)

        # 체인 매출 분석 생성
        analysis = await service.generate_chain_analysis(
            info=request.json_content.info.model_dump(),
            sales_data=request.json_content.sales.data,
            week_data=request.json_content.week.data,
            customer_data=request.json_content.customer.data,
            product_data=request.json_content.product.data,
            include_ai_insights=not skip_ai,
            custom_prompt=request.custom_prompt  # Request Body에서 받은 커스텀 프롬프트 전달
        )

        # BaseResponse로 감싸서 반환
        return BaseResponse[Result[ChainSummaryData]](
            status=200,
            code="OK",
            message="체인 관리자 매출 요약 리포트 생성에 성공하였습니다.",
            isSuccess=True,
            result=Result[ChainSummaryData](data=analysis)
        )

    except HTTPException:
        raise
    except DataValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"데이터 검증 실패: {str(e)}"
        )
    except LLMServiceError as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI 인사이트 생성 실패: {str(e)}"
        )
    except RunpodNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"LLM 서버를 찾을 수 없습니다: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"체인 매출 분석 생성 중 오류 발생: {str(e)}"
        )
