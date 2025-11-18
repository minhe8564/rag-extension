"""Chain Summary Response Schemas"""
from pydantic import BaseModel, Field
from typing import List, Optional, Union
from datetime import datetime
from decimal import Decimal


class AnalysisPeriod(BaseModel):
    """분석 기간 정보"""
    current_month: str = Field(..., description="분석 대상 월 (YYYY-MM)")
    last_month: str = Field(..., description="전월 (YYYY-MM)")
    analysis_date: datetime = Field(..., description="분석 생성 일시")


class StorePerformance(BaseModel):
    """매장별 성과"""
    store_name: str = Field(..., description="매장명")
    total_revenue: Decimal = Field(..., description="총 매출액")
    total_transactions: Union[int, float] = Field(..., description="총 거래 건수")
    avg_transaction_value: Decimal = Field(..., description="평균 객단가")
    growth_rate: Optional[Decimal] = Field(None, description="전월 대비 성장률 (%)")


class TopProduct(BaseModel):
    """베스트 상품"""
    product_name: str = Field(..., description="상품명")
    brand_name: str = Field(..., description="브랜드명")
    product_category: str = Field(..., description="상품 구분")
    total_revenue: Decimal = Field(..., description="총 매출액")
    revenue_share: Decimal = Field(..., description="매출 비중 (%)")
    quantity_sold: Union[int, float] = Field(..., description="판매 수량")
    avg_price: Decimal = Field(..., description="평균 판매가")


class TopBrand(BaseModel):
    """베스트 브랜드"""
    brand_name: str = Field(..., description="브랜드명")
    total_revenue: Decimal = Field(..., description="총 매출액")
    revenue_share: Decimal = Field(..., description="매출 비중 (%)")
    quantity_sold: Union[int, float] = Field(..., description="판매 수량")
    brand_rank: Union[int, float] = Field(..., description="매출 순위")


class CategoryRevenue(BaseModel):
    """상품 구분별 매출"""
    category_name: str = Field(..., description="상품 구분")
    total_revenue: Decimal = Field(..., description="총 매출액")
    revenue_share: Decimal = Field(..., description="매출 비중 (%)")
    quantity_sold: Union[int, float] = Field(..., description="판매 수량")
    category_rank: Union[int, float] = Field(..., description="매출 순위")


class RevenueDistribution(BaseModel):
    """매출 집중도"""
    top_3_share: Decimal = Field(..., description="상위 3개 상품 매출 비중 (%)")
    top_5_share: Decimal = Field(..., description="상위 5개 상품 매출 비중 (%)")
    total_products: int = Field(..., description="전체 상품 수")


class ProductInsights(BaseModel):
    """상품 인사이트"""
    top_products: List[TopProduct] = Field(..., description="베스트 상품 목록")
    top_brands: List[TopBrand] = Field(..., description="베스트 브랜드 목록 (상위 5개)")
    category_revenues: List[CategoryRevenue] = Field(..., description="상품 구분별 매출")
    revenue_distribution: RevenueDistribution = Field(..., description="매출 집중도")


class WeeklyPattern(BaseModel):
    """요일별 패턴"""
    day_code: Union[int, float] = Field(..., description="요일 코드 (1=일요일, 7=토요일)")
    day_name: str = Field(..., description="요일명")
    revenue: Decimal = Field(..., description="매출액")
    revenue_rank: Union[int, float] = Field(..., description="매출 순위")


class HourlyPattern(BaseModel):
    """시간대별 패턴"""
    time_slot: str = Field(..., description="시간대 (예: 14-16)")
    revenue: Decimal = Field(..., description="매출액")
    revenue_rank: Union[int, float] = Field(..., description="매출 순위")


class PeakInsights(BaseModel):
    """피크 인사이트"""
    best_day: str = Field(..., description="최고 매출 요일")
    best_time: str = Field(..., description="최고 매출 시간대")
    worst_day: str = Field(..., description="최저 매출 요일")
    worst_time: str = Field(..., description="최저 매출 시간대")


class TimePatterns(BaseModel):
    """시간 패턴 분석"""
    weekly: List[WeeklyPattern] = Field(..., description="요일별 패턴")
    hourly: List[HourlyPattern] = Field(..., description="시간대별 패턴")
    peak_insights: PeakInsights = Field(..., description="피크 인사이트")


class CustomerDemographic(BaseModel):
    """고객 연령대별 분석"""
    age_code: Union[int, float] = Field(..., description="연령 코드 (-1=미분류, 0=10대미만, 1-9=연령대)")
    age_group: str = Field(..., description="연령대")
    purchase_count: Union[int, float] = Field(..., description="구매 횟수")
    avg_purchase_amount: Decimal = Field(..., description="평균 구매 금액")
    total_revenue: Decimal = Field(..., description="총 매출액")
    revenue_share: Decimal = Field(..., description="매출 비중 (%)")


class KeySegments(BaseModel):
    """핵심 고객 세그먼트"""
    dominant_age_group: str = Field(..., description="주력 연령대")
    highest_avg_purchase_age: str = Field(..., description="객단가 최고 연령대")


class CustomerAnalysis(BaseModel):
    """고객 분석"""
    demographics: List[CustomerDemographic] = Field(..., description="연령대별 분석")
    key_segments: KeySegments = Field(..., description="핵심 세그먼트")


class VisitSalesPattern(BaseModel):
    """방문-매출 효율 패턴"""
    day_name: str = Field(..., description="요일명")
    hour: str = Field(..., description="시간대")
    total_visits: Union[int, float] = Field(..., description="총 방문 수")
    total_revenue: Decimal = Field(..., description="총 매출액")
    revenue_per_visit: Decimal = Field(..., description="방문당 평균 매출")
    efficiency_rank: Union[int, float] = Field(..., description="효율성 순위")


class LLMInsights(BaseModel):
    """LLM 생성 인사이트 (구조화된 형식)"""
    sales_summary: str = Field(..., description="매출 요약 (2-3문장)")
    sales_strategies: List[str] = Field(..., description="추천 매출 전략 목록")
    marketing_strategies: List[str] = Field(..., description="추천 마케팅 전략 목록")


class Metadata(BaseModel):
    """메타데이터"""
    ai_model: str = Field(..., description="사용된 AI 모델")
    generation_time_ms: int = Field(..., description="생성 소요 시간 (ms)")


class ChainSummaryData(BaseModel):
    """체인 매니저 매출 분석 데이터 (BaseResponse의 result.data 안에 들어갈 내용)"""

    analysis_period: AnalysisPeriod = Field(..., description="분석 기간")
    store_performance: List[StorePerformance] = Field(..., description="매장별 성과")
    product_insights: ProductInsights = Field(..., description="상품 인사이트")
    time_patterns: TimePatterns = Field(..., description="시간 패턴")
    customer_analysis: CustomerAnalysis = Field(..., description="고객 분석")
    visit_sales_patterns: List[VisitSalesPattern] = Field(..., description="방문-매출 효율 패턴")
    llm_insights: LLMInsights = Field(..., description="AI 인사이트")
    metadata: Metadata = Field(..., description="메타데이터")


# 하위 호환성을 위한 alias (deprecated)
ChainSummaryResponse = ChainSummaryData
