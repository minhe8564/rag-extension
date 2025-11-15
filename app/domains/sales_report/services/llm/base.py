"""LLM 제공자 추상 베이스 클래스"""
from abc import ABC, abstractmethod
from typing import Dict
from decimal import Decimal


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
        peak_sales_amount: Decimal
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
        visit_sales_patterns
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

        Returns:
            Dict: {
                "sales_summary": str,
                "sales_strategies": List[str],
                "marketing_strategies": List[str]
            }
        """
        pass
