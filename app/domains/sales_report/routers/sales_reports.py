"""Sales Report API Router"""
from fastapi import APIRouter, HTTPException, Query
from datetime import date, datetime
from typing import Optional

from app.domains.sales_report.services.sales_report_service import SalesReportService
from app.domains.sales_report.schemas.response.sales_report import SalesReportResponse


router = APIRouter(prefix="/sales-reports", tags=["sales-reports"])


@router.get("/{store_id}/daily", response_model=SalesReportResponse)
async def get_daily_sales_report(
    store_id: str,
    report_date: Optional[date] = Query(None, description="리포트 기준일 (YYYY-MM-DD)")
):
    """
    일별 매출 리포트 조회

    Args:
        store_id: 안경원 ID (예: "6266")
        report_date: 리포트 기준일 (미지정 시 오늘)

    Returns:
        일별 매출 리포트
    """
    try:
        # 날짜 미지정 시 오늘로 설정
        if report_date is None:
            report_date = date.today()

        service = SalesReportService()
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
    year_month: Optional[str] = Query(None, description="리포트 기준 년월 (YYYY-MM)")
):
    """
    월별 매출 리포트 조회

    Args:
        store_id: 안경원 ID (예: "6266")
        year_month: 리포트 기준 년월 (미지정 시 이번 달)

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

        service = SalesReportService()
        report = await service.generate_report(
            store_id=store_id,
            report_date=None,
            year_month=year_month
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
    year_month: Optional[str] = Query(None, description="월별 리포트 기준 년월 (YYYY-MM)")
):
    """
    일별 + 월별 통합 매출 리포트 조회

    Args:
        store_id: 안경원 ID (예: "6266")
        report_date: 일별 리포트 기준일 (미지정 시 오늘)
        year_month: 월별 리포트 기준 년월 (미지정 시 이번 달)

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

        service = SalesReportService()
        report = await service.generate_report(
            store_id=store_id,
            report_date=report_date,
            year_month=year_month
        )

        return report

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"통합 리포트 생성 중 오류 발생: {str(e)}"
        )


def _validate_year_month(year_month: str) -> bool:
    """년월 형식 검증 (YYYY-MM)"""
    try:
        datetime.strptime(year_month, "%Y-%m")
        return True
    except ValueError:
        return False
