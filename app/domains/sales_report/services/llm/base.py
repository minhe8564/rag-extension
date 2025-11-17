"""LLM 제공자 추상 베이스 클래스"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
from decimal import Decimal
import re
import json


class BaseLLMProvider(ABC):
    """LLM 제공자 추상 인터페이스

    모든 LLM 제공자(Qwen, GPT 등)는 이 인터페이스를 구현해야 함
    """

    def __init__(self, **kwargs):
        """
        Args:
            **kwargs: 제공자별 설정
                - Qwen: base_url (Runpod 주소)
                - GPT: api_key, model
        """
        pass

    @abstractmethod
    async def generate_store_summary(
        self,
        store_name: str,
        total_sales: Decimal,
        payment_breakdown: dict,
        cash_receipt_amount: Decimal,
        returning_customer_rate: Decimal,
        new_customers_count: int,
        avg_transaction_amount: Decimal,
        total_receivables: Decimal,
        top_customers: list,
        peak_sales_date: str,
        peak_sales_amount: Decimal,
        custom_prompt: Optional[str] = None
    ) -> Dict:
        """
        매장 매출 요약 생성

        Args:
            store_name: 안경원명
            total_sales: 총 판매금액
            payment_breakdown: 결제 수단 비율
            cash_receipt_amount: 현금영수증 발급 금액
            returning_customer_rate: 재방문 고객 비율
            new_customers_count: 신규 고객 수
            avg_transaction_amount: 평균 판매금액
            total_receivables: 총 미수금액
            top_customers: Top 고객 리스트
            peak_sales_date: 매출 피크일
            peak_sales_amount: 피크일 판매금액
            custom_prompt: 커스텀 프롬프트 (선택사항)

        Returns:
            Dict: {
                "sales_summary": str,
                "sales_strategies": List[str],
                "marketing_strategies": List[str]
            }
        """
        pass

    @abstractmethod
    async def generate_chain_insights(
        self,
        analysis_period,
        store_performance,
        product_insights,
        time_patterns,
        customer_analysis,
        visit_sales_patterns,
        custom_prompt: Optional[str] = None
    ) -> Dict:
        """
        체인 매출 인사이트 생성

        Args:
            analysis_period: 분석 기간
            store_performance: 매장별 성과
            product_insights: 상품 인사이트
            time_patterns: 시간 패턴
            customer_analysis: 고객 분석
            visit_sales_patterns: 방문-매출 효율 패턴
            custom_prompt: 커스텀 프롬프트 (선택사항)

        Returns:
            Dict: {
                "sales_summary": str,
                "sales_strategies": List[str],
                "marketing_strategies": List[str]
            }
        """
        pass

    # ==========================================
    # 공통 유틸리티 메서드 (중복 제거)
    # ==========================================

    def _normalize_insights(self, parsed: Dict) -> Dict:
        """
        LLM 응답 형식 정규화

        LLM이 {"전략": "내용"} 형식으로 응답하는 경우를 "내용" 문자열로 변환
        """
        # sales_summary 정규화
        sales_summary = parsed.get("sales_summary", "")
        if isinstance(sales_summary, dict):
            # dict인 경우 모든 값을 문자열로 결합
            sales_summary = " ".join(str(v) for v in sales_summary.values())

        # sales_strategies 정규화
        sales_strategies = parsed.get("sales_strategies", [])
        normalized_sales = []
        for item in sales_strategies:
            if isinstance(item, dict):
                # {"전략": "내용"} → "내용"
                strategy_text = item.get("전략") or item.get("strategy") or " ".join(str(v) for v in item.values())
                normalized_sales.append(str(strategy_text))
            else:
                normalized_sales.append(str(item))

        # marketing_strategies 정규화
        marketing_strategies = parsed.get("marketing_strategies", [])
        normalized_marketing = []
        for item in marketing_strategies:
            if isinstance(item, dict):
                # {"전략": "내용"} → "내용"
                strategy_text = item.get("전략") or item.get("strategy") or " ".join(str(v) for v in item.values())
                normalized_marketing.append(str(strategy_text))
            else:
                normalized_marketing.append(str(item))

        return {
            "sales_summary": str(sales_summary),
            "sales_strategies": normalized_sales if normalized_sales else ["데이터를 분석하여 매출 전략을 수립해주세요."],
            "marketing_strategies": normalized_marketing if normalized_marketing else ["고객 데이터를 기반으로 마케팅을 계획해주세요."]
        }

    def _create_custom_store_prompt(
        self,
        custom_prompt: str,
        store_name: str,
        total_sales: Decimal,
        payment_breakdown: dict,
        cash_receipt_amount: Decimal,
        returning_customer_rate: Decimal,
        new_customers_count: int,
        avg_transaction_amount: Decimal,
        total_receivables: Decimal,
        top_customers: list,
        peak_sales_date: str,
        peak_sales_amount: Decimal
    ) -> str:
        """커스텀 프롬프트에 데이터 바인딩 (안전한 방식)"""

        # Top 고객 텍스트 생성
        top_customers_text = ""
        for customer in top_customers[:3]:
            top_customers_text += f"- {customer['customer_name']}: {int(customer['total_amount']):,}원 (구매 {customer['transaction_count']}회)\n"

        # 결제 수단 텍스트 생성
        payment_text = f"카드 {float(payment_breakdown['card'])*100:.0f}%, "
        payment_text += f"현금 {float(payment_breakdown['cash'])*100:.0f}%, "
        payment_text += f"상품권 {float(payment_breakdown['voucher'])*100:.0f}%"

        # 매출 데이터 컨텍스트 생성
        sales_context = f"""
# 매장 정보
- 안경원명: {store_name}

# 이번 달 매출 데이터
- 총 판매금액: {int(total_sales):,}원
- 평균 객단가: {int(avg_transaction_amount):,}원
- 신규 고객 수: {new_customers_count}명
- 재방문 고객 비율: {float(returning_customer_rate)*100:.1f}%
- 결제 수단 비율: {payment_text}
- 현금영수증 발급 금액: {int(cash_receipt_amount):,}원
- 총 미수금액: {int(total_receivables):,}원
- 매출 피크일: {peak_sales_date} ({int(peak_sales_amount):,}원)

# 구매 Top 고객 (상위 3명)
{top_customers_text}
"""

        # 커스텀 프롬프트 + 데이터 컨텍스트 결합
        full_prompt = f"""당신은 안경원 매출 분석 전문가입니다. 아래 데이터를 바탕으로 분석해주세요.

{sales_context}

# 사용자 요청사항
{custom_prompt}
"""

        return full_prompt

    def _create_custom_chain_prompt(
        self,
        custom_prompt: str,
        analysis_period,
        store_performance,
        product_insights,
        time_patterns,
        customer_analysis,
        visit_sales_patterns
    ) -> str:
        """체인 커스텀 프롬프트에 데이터 바인딩 (안전한 방식)"""

        # 매장별 성과 텍스트
        store_text = ""
        for perf in store_performance[:3]:
            store_text += f"- {perf.store_name}: {int(perf.total_revenue):,}원 (객단가 {int(perf.avg_transaction_value):,}원)\n"

        # 베스트 상품 텍스트
        product_text = ""
        for product in product_insights.top_products[:5]:
            product_text += f"- {product.product_name} ({product.brand_name}): {int(product.total_revenue):,}원 (매출비중 {product.revenue_share}%)\n"

        # 베스트 브랜드 텍스트
        brand_text = ""
        for brand in product_insights.top_brands[:5]:
            brand_text += f"- {brand.brand_name}: {int(brand.total_revenue):,}원 (매출비중 {brand.revenue_share}%)\n"

        # 상품 구분별 매출 텍스트
        category_text = ""
        for category in product_insights.category_revenues[:5]:
            category_text += f"- {category.category_name}: {int(category.total_revenue):,}원 (매출비중 {category.revenue_share}%, 판매수량 {category.quantity_sold}개)\n"

        # 시간 패턴 텍스트
        time_text = f"최고 매출: {time_patterns.peak_insights.best_day} {time_patterns.peak_insights.best_time}\n"
        time_text += f"최저 매출: {time_patterns.peak_insights.worst_day} {time_patterns.peak_insights.worst_time}"

        # 고객 분석 텍스트
        customer_text = f"주력 연령대: {customer_analysis.key_segments.dominant_age_group}\n"
        customer_text += f"객단가 최고: {customer_analysis.key_segments.highest_avg_purchase_age}"

        # 방문-매출 효율 텍스트
        efficiency_text = ""
        for pattern in visit_sales_patterns[:5]:
            efficiency_text += f"- {pattern.day_name} {pattern.hour}시: 방문당 {int(pattern.revenue_per_visit):,}원 (방문 {pattern.total_visits}명, 매출 {int(pattern.total_revenue):,}원)\n"

        # 체인 매출 데이터 컨텍스트 생성
        chain_context = f"""
# 분석 기간
- 분석 대상 월: {analysis_period.current_month}
- 전월: {analysis_period.last_month}

# 매장별 성과 (상위 3개)
{store_text}

# 베스트 상품 (상위 5개)
{product_text}

# 베스트 브랜드 (상위 5개)
{brand_text}

# 상품 구분별 매출 (상위 5개)
{category_text}

# 시간 패턴
{time_text}

# 고객 분석
{customer_text}

# 방문-매출 효율 (상위 5개)
{efficiency_text}
"""

        # 커스텀 프롬프트 + 데이터 컨텍스트 결합
        full_prompt = f"""당신은 체인 안경원 매출 분석 전문가입니다. 아래 데이터를 바탕으로 분석해주세요.

{chain_context}

# 사용자 요청사항
{custom_prompt}
"""

        return full_prompt
