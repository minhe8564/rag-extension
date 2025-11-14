"""Chain Sales Analysis Service"""
import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from typing import List, Dict, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict

from app.domains.sales_report.schemas.response.chain_summary_response import (
    ChainSummaryResponse,
    AnalysisPeriod,
    StorePerformance,
    ProductInsights,
    TopProduct,
    TopBrand,
    CategoryRevenue,
    RevenueDistribution,
    TimePatterns,
    WeeklyPattern,
    HourlyPattern,
    PeakInsights,
    CustomerAnalysis,
    CustomerDemographic,
    KeySegments,
    VisitSalesPattern,
    LLMInsights,
    Metadata
)
from app.domains.sales_report.services.chain_llm_client import ChainLLMClient
from app.domains.runpod.repositories.runpod_repository import RunpodRepository
from app.domains.sales_report.exceptions import LLMServiceError, RunpodNotFoundError

logger = logging.getLogger(__name__)


# 연령대 코드 매핑
AGE_CODE_MAPPING = {
    -1: "미분류",
    0: "10대 미만",
    1: "10대",
    2: "20대",
    3: "30대",
    4: "40대",
    5: "50대",
    6: "60대",
    7: "70대",
    8: "80대",
    9: "90대 이상"
}

# 요일 코드 매핑 (W: 1=일요일, 7=토요일)
DAY_CODE_MAPPING = {
    1: "일요일",
    2: "월요일",
    3: "화요일",
    4: "수요일",
    5: "목요일",
    6: "금요일",
    7: "토요일"
}


class ChainSummaryService:
    """체인 매니저 매출 분석 서비스"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_chain_analysis(
        self,
        info: Dict[str, str],
        sales_data: List[Dict[str, Any]],
        week_data: List[Dict[str, Any]],
        customer_data: List[Dict[str, Any]],
        product_data: List[Dict[str, Any]],
        include_ai_insights: bool = True
    ) -> ChainSummaryResponse:
        """
        체인 매출 종합 분석 생성

        Args:
            info: 매장 정보 (안경원명, 매장번호, 대표자명)
            sales_data: 월별 매출 데이터
            week_data: 요일/시간대별 방문 및 매출 데이터
            customer_data: 연령대별 고객 데이터
            product_data: 상품별 판매 데이터
            include_ai_insights: AI 인사이트 포함 여부

        Returns:
            ChainSummaryResponse
        """
        start_time = datetime.now()

        # 1. 분석 기간 계산
        analysis_period = self._calculate_analysis_period(sales_data)

        # 2. 매장별 성과 분석
        store_performance = self._analyze_store_performance(info, sales_data)

        # 3. 상품 인사이트
        product_insights = self._analyze_product_insights(product_data)

        # 4. 시간 패턴 분석
        time_patterns = self._analyze_time_patterns(week_data)

        # 5. 고객 분석
        customer_analysis = self._analyze_customer_demographics(customer_data)

        # 6. 방문-매출 효율 패턴
        visit_sales_patterns = self._analyze_visit_sales_patterns(week_data)

        # 7. LLM 인사이트 (구조화된 형식)
        llm_insights = None
        if include_ai_insights:
            llm_insights = await self._generate_llm_insights(
                analysis_period=analysis_period,
                store_performance=store_performance,
                product_insights=product_insights,
                time_patterns=time_patterns,
                customer_analysis=customer_analysis,
                visit_sales_patterns=visit_sales_patterns
            )
        else:
            # AI 생략 시 기본 메시지
            llm_insights = LLMInsights(
                sales_summary="AI 인사이트가 생략되었습니다.",
                sales_strategies=[],
                marketing_strategies=[]
            )

        # 8. 메타데이터
        end_time = datetime.now()
        generation_time_ms = int((end_time - start_time).total_seconds() * 1000)

        metadata = Metadata(
            ai_model="qwen3-vl:8b" if include_ai_insights else "N/A",
            generation_time_ms=generation_time_ms
        )

        return ChainSummaryResponse(
            analysis_period=analysis_period,
            store_performance=store_performance,
            product_insights=product_insights,
            time_patterns=time_patterns,
            customer_analysis=customer_analysis,
            visit_sales_patterns=visit_sales_patterns,
            llm_insights=llm_insights,
            metadata=metadata
        )

    def _calculate_analysis_period(self, sales_data: List) -> AnalysisPeriod:
        """분석 기간 계산"""
        if not sales_data:
            raise ValueError("매출 데이터가 비어있습니다.")

        # 가장 최근 월 찾기 (Pydantic 모델 직접 접근)
        months = [item.년월 for item in sales_data if item.년월]
        if not months:
            raise ValueError("년월 정보가 없습니다.")

        current_month = max(months)  # 가장 최근 월

        # 지난달 계산
        current = datetime.strptime(current_month, "%Y-%m")
        last_month_date = current - relativedelta(months=1)
        last_month = last_month_date.strftime("%Y-%m")

        return AnalysisPeriod(
            current_month=current_month,
            last_month=last_month,
            analysis_date=datetime.now()
        )

    def _calculate_growth_rate(
        self,
        sales_data: List,
        current_month: str
    ) -> Decimal:
        """전월 대비 성장률 계산"""
        try:
            # 현재 월 데이터 (Pydantic 모델 직접 접근)
            current_data = next((item for item in sales_data if item.년월 == current_month), None)
            if not current_data:
                return Decimal("0")

            current_revenue = Decimal(str(current_data.결제금액))

            # 전월 계산 (YYYY-MM 형식)
            year, month = map(int, current_month.split("-"))
            if month == 1:
                prev_month = f"{year - 1}-12"
            else:
                prev_month = f"{year}-{month - 1:02d}"

            # 전월 데이터
            prev_data = next((item for item in sales_data if item.년월 == prev_month), None)
            if not prev_data:
                return Decimal("0")

            prev_revenue = Decimal(str(prev_data.결제금액))

            # 성장률 계산: ((현재 - 전월) / 전월) * 100
            if prev_revenue > 0:
                growth_rate = ((current_revenue - prev_revenue) / prev_revenue) * 100
                return growth_rate.quantize(Decimal("0.1"))
            else:
                return Decimal("0")

        except Exception as e:
            logger.warning(f"성장률 계산 실패: {e}")
            return Decimal("0")

    def _analyze_store_performance(
        self,
        info: Dict[str, str],
        sales_data: List
    ) -> List[StorePerformance]:
        """매장별 성과 분석"""
        if not sales_data:
            logger.warning("sales_data가 비어있습니다.")
            return []

        store_name = info.get("안경원명", "Unknown")

        # 최근 월 데이터 찾기 (Pydantic 모델 직접 접근)
        months = [item.년월 for item in sales_data if item.년월]

        if not months:
            logger.warning("년월 데이터가 없습니다.")
            return []

        latest_month = max(months)
        latest_data = next((item for item in sales_data if item.년월 == latest_month), None)

        if not latest_data:
            logger.warning(f"최근 월({latest_month}) 데이터를 찾을 수 없습니다.")
            return []

        # Pydantic 모델에서 필드 직접 접근
        total_revenue = Decimal(str(latest_data.결제금액))
        total_transactions = int(latest_data.판매_수)

        # 객단가 계산 (결제금액 / 판매_수)
        if total_transactions > 0:
            avg_value = total_revenue / Decimal(total_transactions)
        else:
            avg_value = Decimal("0")

        # 전월비 계산 (전월 데이터와 비교)
        growth_rate = self._calculate_growth_rate(sales_data, latest_month)

        return [StorePerformance(
            store_name=store_name,
            total_revenue=total_revenue,
            total_transactions=total_transactions,
            avg_transaction_value=avg_value,
            growth_rate=growth_rate
        )]

    def _analyze_product_insights(self, product_data: List) -> ProductInsights:
        """상품 인사이트 분석"""
        products = []
        total_revenue = Decimal("0")

        for item in product_data:
            revenue = Decimal(str(item.판매금액합))
            total_revenue += revenue

            # None 값 및 빈 값 처리 (Pydantic 모델 직접 접근)
            product_name = item.상품명 or "알 수 없음"
            brand_name = item.브랜드명 or "알 수 없음"
            product_category = item.상품구분 or "알 수 없음"
            quantity = int(item.판매_수)

            # 빈 문자열도 "알 수 없음"으로 처리
            if not product_name.strip():
                product_name = "알 수 없음"
            if not brand_name.strip():
                brand_name = "알 수 없음"
            if not product_category.strip():
                product_category = "알 수 없음"

            products.append(TopProduct(
                product_name=product_name,
                brand_name=brand_name,
                product_category=product_category,
                total_revenue=revenue,
                revenue_share=Decimal("0"),  # 나중에 계산
                quantity_sold=quantity,
                avg_price=revenue / quantity if quantity > 0 else Decimal("0")
            ))

        # 매출 비중 계산
        for product in products:
            if total_revenue > 0:
                product.revenue_share = (product.total_revenue / total_revenue * 100).quantize(Decimal("0.1"))

        # 매출 기준 정렬
        products.sort(key=lambda x: x.total_revenue, reverse=True)

        # 상위 상품 매출 비중
        top_3_share = sum(p.revenue_share for p in products[:3]) if len(products) >= 3 else Decimal("0")
        top_5_share = sum(p.revenue_share for p in products[:5]) if len(products) >= 5 else Decimal("0")

        revenue_distribution = RevenueDistribution(
            top_3_share=top_3_share,
            top_5_share=top_5_share,
            total_products=len(products)
        )

        # 브랜드별 매출 집계
        brand_agg = defaultdict(lambda: {"revenue": Decimal("0"), "quantity": 0})

        for item in product_data:
            brand = item.브랜드명 or "알 수 없음"
            if not brand.strip():
                brand = "알 수 없음"

            revenue = Decimal(str(item.판매금액합))
            quantity = int(item.판매_수)

            brand_agg[brand]["revenue"] += revenue
            brand_agg[brand]["quantity"] += quantity

        # TopBrand 객체 생성
        top_brands = []
        for brand, data in brand_agg.items():
            revenue = data["revenue"]
            quantity = data["quantity"]
            revenue_share = (revenue / total_revenue * 100).quantize(Decimal("0.1")) if total_revenue > 0 else Decimal("0")

            top_brands.append(TopBrand(
                brand_name=brand,
                total_revenue=revenue,
                revenue_share=revenue_share,
                quantity_sold=quantity,
                brand_rank=0  # 나중에 할당
            ))

        # 매출 기준 정렬 및 순위 할당 (상위 5개만)
        top_brands.sort(key=lambda x: x.total_revenue, reverse=True)
        for rank, brand in enumerate(top_brands[:5], start=1):
            brand.brand_rank = rank

        # 상품 구분별 매출 집계
        category_agg = defaultdict(lambda: {"revenue": Decimal("0"), "quantity": 0})

        for item in product_data:
            category = item.상품구분 or "알 수 없음"
            if not category.strip():
                category = "알 수 없음"

            revenue = Decimal(str(item.판매금액합))
            quantity = int(item.판매_수)

            category_agg[category]["revenue"] += revenue
            category_agg[category]["quantity"] += quantity

        # CategoryRevenue 객체 생성
        category_revenues = []
        for category, data in category_agg.items():
            revenue = data["revenue"]
            quantity = data["quantity"]
            revenue_share = (revenue / total_revenue * 100).quantize(Decimal("0.1")) if total_revenue > 0 else Decimal("0")

            category_revenues.append(CategoryRevenue(
                category_name=category,
                total_revenue=revenue,
                revenue_share=revenue_share,
                quantity_sold=quantity,
                category_rank=0  # 나중에 할당
            ))

        # 매출 기준 정렬 및 순위 할당
        category_revenues.sort(key=lambda x: x.total_revenue, reverse=True)
        for rank, category in enumerate(category_revenues, start=1):
            category.category_rank = rank

        return ProductInsights(
            top_products=products[:10],
            top_brands=top_brands[:5],  # 상위 5개 브랜드만 반환
            category_revenues=category_revenues,
            revenue_distribution=revenue_distribution
        )

    def _analyze_time_patterns(self, week_data: List) -> TimePatterns:
        """시간 패턴 분석"""
        # 요일별 집계
        weekly_agg = defaultdict(lambda: Decimal("0"))
        hourly_agg = defaultdict(lambda: Decimal("0"))

        for item in week_data:
            day_code = int(item.W)
            hour = item.HOUR or ""  # None 처리
            revenue = Decimal(str(item.판매금액))

            weekly_agg[day_code] += revenue
            if hour:  # 빈 문자열이 아닐 때만 집계
                hourly_agg[hour] += revenue

        # 요일별 패턴
        weekly_patterns = []
        for day_code, revenue in weekly_agg.items():
            weekly_patterns.append(WeeklyPattern(
                day_code=day_code,
                day_name=DAY_CODE_MAPPING.get(day_code, "알 수 없음"),
                revenue=revenue,
                revenue_rank=0
            ))

        weekly_patterns.sort(key=lambda x: x.revenue, reverse=True)
        for rank, pattern in enumerate(weekly_patterns, start=1):
            pattern.revenue_rank = rank

        # 시간대별 패턴
        hourly_patterns = []
        for hour, revenue in hourly_agg.items():
            hourly_patterns.append(HourlyPattern(
                time_slot=hour,
                revenue=revenue,
                revenue_rank=0
            ))

        hourly_patterns.sort(key=lambda x: x.revenue, reverse=True)
        for rank, pattern in enumerate(hourly_patterns, start=1):
            pattern.revenue_rank = rank

        # 피크 인사이트
        best_day = weekly_patterns[0].day_name if weekly_patterns else "알 수 없음"
        worst_day = weekly_patterns[-1].day_name if weekly_patterns else "알 수 없음"
        best_time = hourly_patterns[0].time_slot if hourly_patterns else "알 수 없음"
        worst_time = hourly_patterns[-1].time_slot if hourly_patterns else "알 수 없음"

        peak_insights = PeakInsights(
            best_day=best_day,
            best_time=f"{best_time}시",
            worst_day=worst_day,
            worst_time=f"{worst_time}시"
        )

        return TimePatterns(
            weekly=weekly_patterns,
            hourly=hourly_patterns,
            peak_insights=peak_insights
        )

    def _analyze_customer_demographics(self, customer_data: List) -> CustomerAnalysis:
        """고객 연령대별 분석"""
        demographics = []
        total_revenue = Decimal("0")

        # 연령대별 집계
        age_agg = defaultdict(lambda: {"건수": 0, "판매금액": Decimal("0")})

        for item in customer_data:
            age_code = int(item.AGE)
            count = int(item.건수)
            revenue = Decimal(str(item.판매금액))

            age_agg[age_code]["건수"] += count
            age_agg[age_code]["판매금액"] += revenue
            total_revenue += revenue

        # CustomerDemographic 객체 생성
        for age_code, data in age_agg.items():
            count = data["건수"]
            revenue = data["판매금액"]
            avg_amount = revenue / count if count > 0 else Decimal("0")

            demographics.append(CustomerDemographic(
                age_code=age_code,
                age_group=AGE_CODE_MAPPING.get(age_code, "알 수 없음"),
                purchase_count=count,
                avg_purchase_amount=avg_amount,
                total_revenue=revenue,
                revenue_share=Decimal("0")
            ))

        # 매출 비중 계산
        for demo in demographics:
            if total_revenue > 0:
                demo.revenue_share = (demo.total_revenue / total_revenue * 100).quantize(Decimal("0.1"))

        # 핵심 세그먼트
        dominant = max(demographics, key=lambda x: x.total_revenue) if demographics else None
        highest_avg = max(demographics, key=lambda x: x.avg_purchase_amount) if demographics else None

        key_segments = KeySegments(
            dominant_age_group=dominant.age_group if dominant else "알 수 없음",
            highest_avg_purchase_age=highest_avg.age_group if highest_avg else "알 수 없음"
        )

        return CustomerAnalysis(
            demographics=demographics,
            key_segments=key_segments
        )

    def _analyze_visit_sales_patterns(self, week_data: List) -> List[VisitSalesPattern]:
        """방문-매출 효율 패턴 분석"""
        patterns = []

        for item in week_data:
            day_code = int(item.W)
            day_name = DAY_CODE_MAPPING.get(day_code, "알 수 없음")
            hour = item.HOUR or ""  # None 처리
            visits = int(item.방문수)
            revenue = Decimal(str(item.판매금액))

            revenue_per_visit = revenue / visits if visits > 0 else Decimal("0")

            patterns.append(VisitSalesPattern(
                day_name=day_name,
                hour=hour,
                total_visits=visits,
                total_revenue=revenue,
                revenue_per_visit=revenue_per_visit,
                efficiency_rank=0
            ))

        # 효율성 기준 정렬
        patterns.sort(key=lambda x: x.revenue_per_visit, reverse=True)
        for rank, pattern in enumerate(patterns, start=1):
            pattern.efficiency_rank = rank

        return patterns[:20]  # 상위 20개만 반환

    async def _generate_llm_insights(
        self,
        analysis_period: AnalysisPeriod,
        store_performance: List[StorePerformance],
        product_insights: ProductInsights,
        time_patterns: TimePatterns,
        customer_analysis: CustomerAnalysis,
        visit_sales_patterns: List[VisitSalesPattern]
    ) -> LLMInsights:
        """LLM을 사용한 구조화된 인사이트 생성"""
        try:
            # Runpod에서 qwen3 LLM 주소 조회
            runpod = await RunpodRepository.find_by_name(self.db, "qwen3")

            if not runpod or not runpod.address:
                logger.warning("AI 인사이트 생성 실패: LLM 서버를 찾을 수 없습니다.")
                raise RunpodNotFoundError("qwen3 LLM 서버를 찾을 수 없습니다.")

            # LLM 클라이언트 생성
            llm_client = ChainLLMClient(runpod.address)

            # LLM 인사이트 생성 (구조화된 응답)
            insights = await llm_client.generate_chain_insights(
                analysis_period=analysis_period,
                store_performance=store_performance,
                product_insights=product_insights,
                time_patterns=time_patterns,
                customer_analysis=customer_analysis,
                visit_sales_patterns=visit_sales_patterns
            )

            return insights

        except RunpodNotFoundError:
            return LLMInsights(
                sales_summary="LLM 서버를 찾을 수 없어 AI 인사이트를 생성할 수 없습니다.",
                sales_strategies=[],
                marketing_strategies=[]
            )
        except Exception as e:
            logger.error(f"AI 인사이트 생성 실패: {str(e)}", exc_info=True)
            raise LLMServiceError(f"AI 인사이트 생성 중 오류 발생: {str(e)}")
