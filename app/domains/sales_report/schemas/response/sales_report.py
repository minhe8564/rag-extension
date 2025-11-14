"""Sales Report Response Schemas"""
from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal
from datetime import date


# ============== 공통 스키마 ==============

class StoreInfo(BaseModel):
    """매장 정보"""
    store_name: str = Field(..., description="안경원명")
    store_phone: str = Field(..., description="매장번호")
    owner_name: str = Field(..., description="대표자명")


class PaymentBreakdown(BaseModel):
    """결제 수단 비율 (카드, 현금, 상품권)"""
    card: Decimal = Field(..., description="카드 결제 비율 (0.0 ~ 1.0)")
    cash: Decimal = Field(..., description="현금 결제 비율 (0.0 ~ 1.0)")
    voucher: Decimal = Field(..., description="상품권 비율 (0.0 ~ 1.0)")


class TopCustomer(BaseModel):
    """구매 Top 고객"""
    rank: int = Field(..., description="순위")
    customer_name: str = Field(..., description="고객명")
    total_amount: Decimal = Field(..., description="총 구매금액")
    transaction_count: int = Field(..., description="구매 건수")


class ReceivableCustomer(BaseModel):
    """미수금 고객"""
    customer_name: str = Field(..., description="고객명")
    receivable_amount: Decimal = Field(..., description="미수금액")


# ============== 일별 리포트 ==============

class DailySalesReport(BaseModel):
    """일별 매출 리포트"""
    report_date: date = Field(..., description="리포트 기준일")

    # 💰 총 판매금액
    total_sales: Decimal = Field(..., description="총 판매금액")

    # 💵 평균 판매금액
    avg_transaction_amount: Decimal = Field(..., description="평균 판매금액 (객단가)")

    # 👤 신규 고객 수
    new_customers_count: int = Field(..., description="신규 고객 수")

    # 🏆 구매 Top 고객 (일: 3명)
    top_customers: List[TopCustomer] = Field(..., description="구매 Top 3 고객")

    class Config:
        json_schema_extra = {
            "example": {
                "report_date": "2024-11-12",
                "total_sales": "1500000",
                "avg_transaction_amount": "125000",
                "new_customers_count": 8,
                "top_customers": [
                    {
                        "rank": 1,
                        "customer_name": "홍길동",
                        "total_amount": "500000",
                        "transaction_count": 2
                    }
                ]
            }
        }


# ============== 월별 리포트 ==============

class MonthlySalesReport(BaseModel):
    """월별 매출 리포트"""
    year_month: str = Field(..., description="리포트 기준 년월 (YYYY-MM)")

    # 💰 총 판매금액
    total_sales: Decimal = Field(..., description="총 판매금액")

    # 💳 결제 수단 비율
    payment_breakdown: PaymentBreakdown = Field(..., description="결제 수단 비율 (카드, 현금, 상품권)")

    # 🧾 현금영수증 발급 금액
    cash_receipt_amount: Decimal = Field(..., description="현금영수증 발급 금액")

    # 👥 재방문 고객 비율
    returning_customer_rate: Decimal = Field(..., description="재방문 고객 비율 (0.0 ~ 1.0)")

    # 👤 신규 고객 수
    new_customers_count: int = Field(..., description="신규 고객 수")

    # 📈 전월/전년 대비 매출 증감률
    month_over_month_growth: Optional[Decimal] = Field(None, description="전월 대비 증감률")
    year_over_year_growth: Optional[Decimal] = Field(None, description="전년 대비 증감률")

    # 💵 평균 판매금액
    avg_transaction_amount: Decimal = Field(..., description="평균 판매금액 (객단가)")

    # 🧾 총 미수금액 / 명단
    total_receivables: Decimal = Field(..., description="총 미수금액")
    receivable_customers: List[ReceivableCustomer] = Field(..., description="미수금 고객 명단")

    # 🏆 구매 Top 고객 (월: 10명)
    top_customers: List[TopCustomer] = Field(..., description="구매 Top 10 고객")

    # 📅 매출 피크일
    peak_sales_date: date = Field(..., description="매출 피크일")
    peak_sales_amount: Decimal = Field(..., description="피크일 판매금액")

    class Config:
        json_schema_extra = {
            "example": {
                "year_month": "2024-11",
                "total_sales": "45000000",
                "payment_breakdown": {
                    "card": "0.75",
                    "cash": "0.20",
                    "voucher": "0.05"
                },
                "cash_receipt_amount": "3000000",
                "returning_customer_rate": "0.65",
                "new_customers_count": 43,
                "month_over_month_growth": "0.05",
                "year_over_year_growth": "0.12",
                "avg_transaction_amount": "375000",
                "total_receivables": "5000000",
                "receivable_customers": [
                    {
                        "customer_name": "김철수",
                        "receivable_amount": "1500000"
                    }
                ],
                "top_customers": [
                    {
                        "rank": 1,
                        "customer_name": "홍길동",
                        "total_amount": "5000000",
                        "transaction_count": 12
                    }
                ],
                "peak_sales_date": "2024-11-15",
                "peak_sales_amount": "2500000"
            }
        }


# ============== 통합 리포트 ==============

class SalesReportResponse(BaseModel):
    """매출 리포트 통합 응답"""
    store_info: StoreInfo = Field(..., description="매장 정보")
    daily_report: Optional[DailySalesReport] = Field(None, description="일별 리포트")
    monthly_report: Optional[MonthlySalesReport] = Field(None, description="월별 리포트")
    ai_summary: Optional[str] = Field(None, description="🤖 AI 요약 리포트")

    class Config:
        json_schema_extra = {
            "example": {
                "store_info": {
                    "store_name": "행복안경원",
                    "store_phone": "02-1234-5678",
                    "owner_name": "홍길동"
                },
                "daily_report": {"report_date": "2024-11-12"},
                "monthly_report": {"year_month": "2024-11"},
                "ai_summary": "이번 달 매출이 전월 대비 5% 증가했습니다..."
            }
        }
