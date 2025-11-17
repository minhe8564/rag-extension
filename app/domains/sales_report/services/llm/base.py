"""LLM 제공자 추상 베이스 클래스"""
from abc import ABC, abstractmethod
from typing import Dict, Optional
from decimal import Decimal
import logging

from .utils import PromptBuilder, LLMResponseNormalizer

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """LLM 제공자 추상 인터페이스

    템플릿 메서드 패턴 적용:
    - 베이스 클래스: 전체 흐름 정의 (프롬프트 생성 → API 호출 → 정규화)
    - 서브 클래스: 구체적 구현 제공 (프롬프트 템플릿, API 호출)
    """

    def __init__(self, **kwargs):
        """
        Args:
            **kwargs: 제공자별 설정
                - Qwen: base_url (Runpod 주소)
                - GPT: api_key, model
        """
        pass

    # ==========================================
    # 템플릿 메서드 (공통 흐름 정의)
    # ==========================================

    async def generate_store_summary(
        self,
        store_name: str,
        total_sales: Decimal,
        payment_breakdown: dict,
        cash_receipt_amount: Decimal,
        returning_customer_rate: Decimal,
        new_customers_count: int,
        avg_transaction_amount: Decimal,
        peak_sales_date: str,
        peak_sales_amount: Decimal,
        period: Optional[str] = None,
        custom_prompt: Optional[str] = None
    ) -> Dict:
        """
        매장 매출 요약 생성 (템플릿 메서드)

        흐름:
        1. 프롬프트 생성 (커스텀 vs 기본)
        2. LLM API 호출
        3. 응답 파싱 및 정규화

        Args:
            store_name: 안경원명
            total_sales: 총 판매금액
            payment_breakdown: 결제 수단 비율
            cash_receipt_amount: 현금영수증 발급 금액
            returning_customer_rate: 재방문 고객 비율
            new_customers_count: 신규 고객 수
            avg_transaction_amount: 평균 판매금액
            peak_sales_date: 매출 피크일
            peak_sales_amount: 피크일 판매금액
            period: 리포트 기간 (예: "2024-11-01 ~ 2024-11-30")
            custom_prompt: 커스텀 프롬프트 (선택사항, 이미 검증됨)

        Returns:
            Dict: {
                "sales_summary": str,
                "sales_strategies": List[str],
                "marketing_strategies": List[str]
            }
        """
        # 1. 프롬프트 생성 (분기 로직을 베이스에서 처리)
        if custom_prompt:
            # 커스텀 프롬프트 사용
            data_context = PromptBuilder.build_store_context(
                store_name=store_name,
                total_sales=total_sales,
                payment_breakdown=payment_breakdown,
                cash_receipt_amount=cash_receipt_amount,
                returning_customer_rate=returning_customer_rate,
                new_customers_count=new_customers_count,
                avg_transaction_amount=avg_transaction_amount,
                peak_sales_date=peak_sales_date,
                peak_sales_amount=peak_sales_amount,
                period=period
            )
            prompt = PromptBuilder.merge_custom_prompt(
                custom_prompt=custom_prompt,
                data_context=data_context,
                period=period
            )
        else:
            # 기본 프롬프트 사용 (각 프로바이더의 구현 호출)
            prompt = self._create_default_store_prompt(
                store_name=store_name,
                total_sales=total_sales,
                payment_breakdown=payment_breakdown,
                cash_receipt_amount=cash_receipt_amount,
                returning_customer_rate=returning_customer_rate,
                new_customers_count=new_customers_count,
                avg_transaction_amount=avg_transaction_amount,
                peak_sales_date=peak_sales_date,
                peak_sales_amount=peak_sales_amount,
                period=period
            )

        # 2. LLM API 호출 (각 프로바이더의 구현 호출)
        try:
            response_text = await self._call_llm_api(prompt)
        except Exception as e:
            logger.error(f"LLM API 호출 실패: {e}", exc_info=True)
            # 실패 시 기본 응답 반환
            return LLMResponseNormalizer.DEFAULT_RESPONSE

        # 3. 응답 파싱 및 정규화
        parsed = self._parse_response(response_text)
        return LLMResponseNormalizer.normalize_insights(parsed)

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
        체인 매출 인사이트 생성 (템플릿 메서드)

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
        # 1. 프롬프트 생성
        if custom_prompt:
            # 커스텀 프롬프트 사용
            data_context = PromptBuilder.build_chain_context(
                analysis_period=analysis_period,
                store_performance=store_performance,
                product_insights=product_insights,
                time_patterns=time_patterns,
                customer_analysis=customer_analysis,
                visit_sales_patterns=visit_sales_patterns
            )
            prompt = PromptBuilder.merge_custom_chain_prompt(
                custom_prompt=custom_prompt,
                data_context=data_context
            )
        else:
            # 기본 프롬프트 사용
            prompt = self._create_default_chain_prompt(
                analysis_period=analysis_period,
                store_performance=store_performance,
                product_insights=product_insights,
                time_patterns=time_patterns,
                customer_analysis=customer_analysis,
                visit_sales_patterns=visit_sales_patterns
            )

        # 2. LLM API 호출
        try:
            response_text = await self._call_llm_api(prompt)
        except Exception as e:
            logger.error(f"LLM API 호출 실패: {e}", exc_info=True)
            return LLMResponseNormalizer.DEFAULT_RESPONSE

        # 3. 응답 파싱 및 정규화
        parsed = self._parse_response(response_text)
        return LLMResponseNormalizer.normalize_insights(parsed)

    # ==========================================
    # 추상 메서드 (각 프로바이더가 구현)
    # ==========================================

    @abstractmethod
    def _create_default_store_prompt(
        self,
        store_name: str,
        total_sales: Decimal,
        payment_breakdown: dict,
        cash_receipt_amount: Decimal,
        returning_customer_rate: Decimal,
        new_customers_count: int,
        avg_transaction_amount: Decimal,
        peak_sales_date: str,
        peak_sales_amount: Decimal,
        period: Optional[str] = None
    ) -> str:
        """
        기본 매장 프롬프트 생성 (프로바이더별 구현)

        각 프로바이더는 자신의 스타일에 맞는 프롬프트 템플릿 제공
        """
        pass

    @abstractmethod
    def _create_default_chain_prompt(
        self,
        analysis_period,
        store_performance,
        product_insights,
        time_patterns,
        customer_analysis,
        visit_sales_patterns
    ) -> str:
        """
        기본 체인 프롬프트 생성 (프로바이더별 구현)
        """
        pass

    @abstractmethod
    async def _call_llm_api(self, prompt: str) -> str:
        """
        LLM API 호출 (프로바이더별 구현)

        Args:
            prompt: 생성된 프롬프트

        Returns:
            str: LLM 응답 텍스트
        """
        pass

    # ==========================================
    # 공통 헬퍼 메서드
    # ==========================================

    def _parse_response(self, response: str) -> Dict:
        """
        응답 파싱 (공통 로직)

        JSON 추출 시도 → 실패 시 기본 구조 반환
        """
        # JSON 추출 시도
        parsed = LLMResponseNormalizer.extract_json_from_text(response)

        if parsed:
            return parsed

        # JSON 추출 실패 시 텍스트 파싱 시도 (기본 구조)
        logger.warning("JSON 추출 실패, 기본 구조 반환")
        return {
            "sales_summary": response[:200] if response else "",
            "sales_strategies": [],
            "marketing_strategies": []
        }
