"""Sales Report API Router"""
from fastapi import APIRouter, HTTPException, Query, Depends
from datetime import date, datetime
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.sales_report.services.sales_report_service import SalesReportService
from app.domains.sales_report.schemas.response.sales_report import SalesReportResponse
from app.core.database import get_db


router = APIRouter(prefix="/sales-reports", tags=["sales-reports"])


@router.get("/{store_id}/daily", response_model=SalesReportResponse)
async def get_daily_sales_report(
    store_id: str,
    report_date: Optional[date] = Query(None, description="리포트 기준일 (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db)
):
    """
    일별 매출 리포트 조회

    Args:
        store_id: 안경원 ID (예: "6266")
        report_date: 리포트 기준일 (미지정 시 오늘)
        db: DB 세션

    Returns:
        일별 매출 리포트
    """
    try:
        # 날짜 미지정 시 오늘로 설정
        if report_date is None:
            report_date = date.today()

        service = SalesReportService(db=db)
        report = await service.generate_report(
            store_id=store_id,
            report_date=report_date,
            year_month=None
        )

        return report

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"일별 리포트 생성 중 오류 발생: {str(e)}"
        )


@router.get("/{store_id}/monthly", response_model=SalesReportResponse)
async def get_monthly_sales_report(
    store_id: str,
    year_month: Optional[str] = Query(None, description="리포트 기준 년월 (YYYY-MM)"),
    skip_ai: bool = Query(True, description="AI 요약 생략 여부 (기본값: True)"),
    db: AsyncSession = Depends(get_db)
):
    """
    월별 매출 리포트 조회

    Args:
        store_id: 안경원 ID (예: "6266")
        year_month: 리포트 기준 년월 (미지정 시 이번 달)
        skip_ai: AI 요약 생략 여부 (True: 즉시 응답, False: AI 요약 포함하여 40-50초 소요)
        db: DB 세션

    Returns:
        월별 매출 리포트
    """
    try:
        # 년월 미지정 시 이번 달로 설정
        if year_month is None:
            year_month = datetime.now().strftime("%Y-%m")

        # 년월 형식 검증
        if not _validate_year_month(year_month):
            raise HTTPException(
                status_code=400,
                detail="year_month는 YYYY-MM 형식이어야 합니다."
            )

        service = SalesReportService(db=db)

        # skip_ai=True면 즉시 응답, False면 AI 요약 포함 (40-50초 소요)
        report = await service.generate_report(
            store_id=store_id,
            report_date=None,
            year_month=year_month,
            include_ai_summary=not skip_ai
        )

        return report

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"월별 리포트 생성 중 오류 발생: {str(e)}"
        )


@router.get("/{store_id}/combined", response_model=SalesReportResponse)
async def get_combined_sales_report(
    store_id: str,
    report_date: Optional[date] = Query(None, description="일별 리포트 기준일 (YYYY-MM-DD)"),
    year_month: Optional[str] = Query(None, description="월별 리포트 기준 년월 (YYYY-MM)"),
    skip_ai: bool = Query(True, description="AI 요약 생략 여부 (기본값: True)"),
    db: AsyncSession = Depends(get_db)
):
    """
    일별 + 월별 통합 매출 리포트 조회

    Args:
        store_id: 안경원 ID (예: "6266")
        report_date: 일별 리포트 기준일 (미지정 시 오늘)
        year_month: 월별 리포트 기준 년월 (미지정 시 이번 달)
        skip_ai: AI 요약 생략 여부 (True: 즉시 응답, False: AI 요약 포함하여 40-50초 소요)
        db: DB 세션

    Returns:
        일별 + 월별 통합 리포트
    """
    try:
        # 날짜 미지정 시 오늘로 설정
        if report_date is None:
            report_date = date.today()

        # 년월 미지정 시 이번 달로 설정
        if year_month is None:
            year_month = datetime.now().strftime("%Y-%m")

        # 년월 형식 검증
        if not _validate_year_month(year_month):
            raise HTTPException(
                status_code=400,
                detail="year_month는 YYYY-MM 형식이어야 합니다."
            )

        service = SalesReportService(db=db)

        # skip_ai=True면 즉시 응답, False면 AI 요약 포함 (40-50초 소요)
        report = await service.generate_report(
            store_id=store_id,
            report_date=report_date,
            year_month=year_month,
            include_ai_summary=not skip_ai
        )

        return report

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"통합 리포트 생성 중 오류 발생: {str(e)}"
        )


@router.post("/{store_id}/monthly/generate-ai-summary")
async def generate_ai_summary(
    store_id: str,
    year_month: Optional[str] = Query(None, description="리포트 기준 년월 (YYYY-MM)"),
    db: AsyncSession = Depends(get_db)
):
    """
    AI 요약 리포트 생성 (사용자가 버튼 클릭 시 호출)

    Args:
        store_id: 안경원 ID (예: "6266")
        year_month: 리포트 기준 년월 (미지정 시 이번 달)
        db: DB 세션

    Returns:
        dict: AI 요약 텍스트 (40-50초 소요)
    """
    try:
        # 년월 미지정 시 이번 달로 설정
        if year_month is None:
            year_month = datetime.now().strftime("%Y-%m")

        # 년월 형식 검증
        if not _validate_year_month(year_month):
            raise HTTPException(
                status_code=400,
                detail="year_month는 YYYY-MM 형식이어야 합니다."
            )

        service = SalesReportService(db=db)

        # AI 요약 포함하여 리포트 생성 (40-50초 소요)
        report = await service.generate_report(
            store_id=store_id,
            report_date=None,
            year_month=year_month,
            include_ai_summary=True
        )

        # AI 요약만 반환
        return {
            "ai_summary": report.ai_summary
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI 요약 생성 중 오류 발생: {str(e)}"
        )


def _validate_year_month(year_month: str) -> bool:
    """년월 형식 검증 (YYYY-MM)"""
    try:
        datetime.strptime(year_month, "%Y-%m")
        return True
    except ValueError:
        return False
