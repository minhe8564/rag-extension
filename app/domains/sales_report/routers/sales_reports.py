"""Sales Report API Router"""
from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import date
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.sales_report.services.sales_report_service import SalesReportService
from app.domains.sales_report.schemas.response.sales_report import SalesReportResponse
from app.domains.sales_report.schemas.request.sales_report import GenerateReportRequest
from app.domains.sales_report.exceptions import (
    DataValidationError,
    LLMServiceError,
    RunpodNotFoundError
)
from app.core.database import get_db


router = APIRouter(prefix="/sales-reports", tags=["sales-reports"])


@router.post("/generate-report", response_model=SalesReportResponse)
async def generate_report_from_json_data(
    request: GenerateReportRequest,
    report_date: Optional[date] = Query(None, description="일별 리포트 기준일 (YYYY-MM-DD, 선택사항)"),
    skip_ai: bool = Query(True, description="AI 요약 생략 여부 (기본값: True)"),
    db: AsyncSession = Depends(get_db)
):
    """
    JSON 데이터로 매출 리포트 생성 (외부 API 호출 없음)

    프론트엔드나 다른 서비스에서 이미 가져온 데이터를 그대로 전달받아
    리포트를 생성합니다. 외부 API 의존성이 없어 빠른 응답이 가능합니다.

    Args:
        request: 매장 정보와 거래 데이터를 포함한 요청 바디
        report_date: 일별 리포트 기준일 (선택사항, 지정 시 일별 리포트 포함)
        skip_ai: AI 요약 생략 여부 (True: 즉시 응답, False: AI 요약 포함하여 40-50초 소요)
        db: DB 세션

    Returns:
        매출 리포트 (report_date 지정 시 일별+월별, 미지정 시 월별만)

    Example Request:
        POST /api/v1/sales-reports/generate-report?report_date=2025-10-15&skip_ai=true

        Body:
        {
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
    """
    try:
        service = SalesReportService(db=db)

        # 전달받은 데이터로 리포트 생성 (외부 API 호출 없음)
        report = await service.generate_report_from_data(
            store_info=request.info,
            transactions=request.data,
            report_date=report_date,  # Query 파라미터로 받은 값 사용
            year_month=request.year_month,
            include_ai_summary=not skip_ai
        )

        return report

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
