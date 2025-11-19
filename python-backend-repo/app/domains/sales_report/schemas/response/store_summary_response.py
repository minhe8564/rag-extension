"""Store Summary Response Schemas"""
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


class DailySalesTrend(BaseModel):
    """일별 매출 추이 (차트용)"""
    sale_date: date = Field(..., description="날짜")
    sales_amount: Decimal = Field(..., description="당일 매출액")

    class Config:
        json_schema_extra = {
            "example": {
                "sale_date": "2024-11-01",
                "sales_amount": "850000"
            }
        }


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
    period: str = Field(..., description="리포트 기간 (예: 2024-11-01 ~ 2024-11-30 또는 2024-11)")

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

    # 💵 평균 판매금액
    avg_transaction_amount: Decimal = Field(..., description="평균 판매금액 (객단가)")

    # 📅 매출 피크일
    peak_sales_date: date = Field(..., description="매출 피크일")
    peak_sales_amount: Decimal = Field(..., description="피크일 판매금액")

    # 📈 일별 매출 추이 (차트용)
    daily_sales_trend: List[DailySalesTrend] = Field(..., description="해당 월의 일별 매출 추이")

    class Config:
        json_schema_extra = {
            "example": {
                "period": "2024-11-01 ~ 2024-11-30",
                "total_sales": "45000000",
                "payment_breakdown": {
                    "card": "0.75",
                    "cash": "0.20",
                    "voucher": "0.05"
                },
                "cash_receipt_amount": "3000000",
                "returning_customer_rate": "0.65",
                "new_customers_count": 43,
                "avg_transaction_amount": "375000",
                "peak_sales_date": "2024-11-15",
                "peak_sales_amount": "2500000",
                "daily_sales_trend": [
                    {
                        "date": "2024-11-01",
                        "sales_amount": "850000"
                    },
                    {
                        "date": "2024-11-02",
                        "sales_amount": "920000"
                    }
                ]
            }
        }


# ============== AI 인사이트 ==============

class LLMInsights(BaseModel):
    """LLM 생성 인사이트 (구조화된 형식)"""
    sales_summary: str = Field(..., description="매출 요약 (2-3문장)")
    sales_strategies: List[str] = Field(..., description="추천 매출 전략 목록")
    marketing_strategies: List[str] = Field(..., description="추천 마케팅 전략 목록")


class Metadata(BaseModel):
    """메타데이터"""
    ai_model: str = Field(..., description="사용된 AI 모델")
    generation_time_ms: int = Field(..., description="생성 소요 시간 (ms)")


# ============== 통합 리포트 ==============

class StoreSummaryData(BaseModel):
    """개별 안경원 매출 요약 리포트 데이터 (BaseResponse의 result.data 안에 들어갈 내용)"""
    store_info: StoreInfo = Field(..., description="매장 정보")
    daily_report: Optional[DailySalesReport] = Field(None, description="일별 리포트")
    monthly_report: Optional[MonthlySalesReport] = Field(None, description="월별 리포트")
    llm_insights: Optional[LLMInsights] = Field(None, description="🤖 AI 인사이트")
    metadata: Optional[Metadata] = Field(None, description="메타데이터")


# 하위 호환성을 위한 alias (deprecated)
StoreSummaryResponse = StoreSummaryData
