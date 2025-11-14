"""LLM Client - Qwen3 모델을 사용한 AI 요약 생성"""
import httpx
import logging
from typing import Optional
from decimal import Decimal

logger = logging.getLogger(__name__)


class LLMClient:
    """Qwen3 LLM 클라이언트 - AI 매출 요약 생성"""

    def __init__(self, runpod_address: str):
        """
        Args:
            runpod_address: Runpod 서버 주소 (예: "https://xxx.runpod.net")
        """
        self.base_url = runpod_address.rstrip("/")
        self.timeout = 60.0  # LLM 응답은 시간이 걸릴 수 있음

    async def generate_sales_summary(
        self,
        store_name: str,
        total_sales: Decimal,
        payment_breakdown: dict,
        cash_receipt_amount: Decimal,
        returning_customer_rate: Decimal,
        new_customers_count: int,
        month_over_month_growth: Optional[Decimal],
        year_over_year_growth: Optional[Decimal],
        avg_transaction_amount: Decimal,
        total_receivables: Decimal,
        top_customers: list,
        peak_sales_date: str,
        peak_sales_amount: Decimal
    ) -> str:
        """
        매출 데이터를 기반으로 AI 요약 리포트 생성

        Args:
            store_name: 안경원명
            total_sales: 총 판매금액
            payment_breakdown: 결제 수단 비율 (카드, 현금, 상품권)
            cash_receipt_amount: 현금영수증 발급 금액
            returning_customer_rate: 재방문 고객 비율
            new_customers_count: 신규 고객 수
            month_over_month_growth: 전월 대비 증감률
            year_over_year_growth: 전년 대비 증감률
            avg_transaction_amount: 평균 판매금액
            total_receivables: 총 미수금액
            top_customers: Top 고객 리스트
            peak_sales_date: 매출 피크일
            peak_sales_amount: 피크일 판매금액

        Returns:
            str: AI 생성 요약 리포트
        """
        # 프롬프트 생성
        prompt = self._create_prompt(
            store_name=store_name,
            total_sales=total_sales,
            payment_breakdown=payment_breakdown,
            cash_receipt_amount=cash_receipt_amount,
            returning_customer_rate=returning_customer_rate,
            new_customers_count=new_customers_count,
            month_over_month_growth=month_over_month_growth,
            year_over_year_growth=year_over_year_growth,
            avg_transaction_amount=avg_transaction_amount,
            total_receivables=total_receivables,
            top_customers=top_customers,
            peak_sales_date=peak_sales_date,
            peak_sales_amount=peak_sales_amount
        )

        # LLM API 호출
        try:
            summary = await self._call_llm_api(prompt)
            return summary
        except Exception as e:
            # LLM 호출 실패 시 기본 메시지 반환
            return f"AI 요약 생성에 실패했습니다: {str(e)}"

    def _create_prompt(
        self,
        store_name: str,
        total_sales: Decimal,
        payment_breakdown: dict,
        cash_receipt_amount: Decimal,
        returning_customer_rate: Decimal,
        new_customers_count: int,
        month_over_month_growth: Optional[Decimal],
        year_over_year_growth: Optional[Decimal],
        avg_transaction_amount: Decimal,
        total_receivables: Decimal,
        top_customers: list,
        peak_sales_date: str,
        peak_sales_amount: Decimal
    ) -> str:
        """AI 요약 생성을 위한 프롬프트 작성"""

        # 증감률 텍스트 생성
        growth_text = ""
        if month_over_month_growth is not None:
            mom_percent = float(month_over_month_growth) * 100
            mom_direction = "증가" if mom_percent > 0 else "감소"
            growth_text += f"- 전월 대비: {abs(mom_percent):.1f}% {mom_direction}\n"

        if year_over_year_growth is not None:
            yoy_percent = float(year_over_year_growth) * 100
            yoy_direction = "증가" if yoy_percent > 0 else "감소"
            growth_text += f"- 전년 대비: {abs(yoy_percent):.1f}% {yoy_direction}\n"

        # Top 고객 텍스트 생성 (상위 3명만)
        top_customers_text = ""
        for customer in top_customers[:3]:
            top_customers_text += f"- {customer['customer_name']}: {int(customer['total_amount']):,}원 (구매 {customer['transaction_count']}회)\n"

        # 결제 수단 텍스트 생성 (카드, 현금, 상품권만)
        payment_text = f"카드 {float(payment_breakdown['card'])*100:.0f}%, "
        payment_text += f"현금 {float(payment_breakdown['cash'])*100:.0f}%, "
        payment_text += f"상품권 {float(payment_breakdown['voucher'])*100:.0f}%"

        prompt = f"""당신은 안경원 매출 분석 전문가입니다. 아래 데이터를 바탕으로 매출 요약과 전략을 제안해주세요.

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

# 매출 증감률
{growth_text}

# 구매 Top 고객 (상위 3명)
{top_customers_text}

# 요청사항
아래 형식으로 **바로** 한국어로만 작성해주세요. 영어 사고 과정은 절대 쓰지 마세요.

매출 요약: 이번 달 매출의 주요 특징과 인사이트를 2-3문장으로 요약
추천 매출 전략: 매출을 증대시키기 위한 구체적인 전략 1-2가지
추천 마케팅 전략: 고객 유치 및 재방문 유도를 위한 마케팅 방안 1-2가지

**필수 규칙**:
1. 반드시 "매출 요약:", "추천 매출 전략:", "추천 마케팅 전략:" 레이블 사용
2. 영어 설명이나 사고 과정 절대 포함하지 마세요 (예: "Let me...", "Wait...", "Check..." 등 금지)
3. 글자수나 메타 정보 포함하지 마세요
4. 친절하고 실용적인 톤으로 500자 이내로 간결하게 작성
5. 바로 답변만 작성하세요
"""
        return prompt

    async def _call_llm_api(self, prompt: str) -> str:
        """
        LLM API 호출 (Ollama Chat API - 더 안정적)

        Args:
            prompt: 입력 프롬프트

        Returns:
            str: LLM 생성 텍스트
        """
        # Ollama의 /api/chat 엔드포인트 시도 (더 안정적)
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": "qwen3-vl:8b",
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 안경원 매출 분석 전문가입니다. 데이터를 바탕으로 실용적인 인사이트를 제공합니다."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 10000  # 토큰 제한: 영어 사고 + 한글 답변
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                result = response.json()

                # 응답 로깅
                logger.debug(f"LLM API Response: {result}")

                # Ollama chat API 응답 파싱
                if "message" in result:
                    message = result["message"]
                    content = message.get("content", "")

                    # 응답 내용 로깅
                    logger.debug(f"LLM Content Length: {len(content)}")
                    logger.debug(f"LLM Content Preview: {content[:200] if content else 'EMPTY'}")

                    # content에 답변이 있으면 바로 반환
                    if content and content.strip():
                        return content.strip()

                # content가 비어있으면 에러
                raise ValueError("LLM 응답이 비어있습니다.")

        except Exception as e:
            logger.warning(f"LLM Chat API Failed: {e}, trying generate API...")

            # 폴백: /api/generate 시도
            return await self._call_llm_api_generate(prompt)

    async def _call_llm_api_generate(self, prompt: str) -> str:
        """
        LLM API 호출 폴백 (Ollama Generate API)

        Args:
            prompt: 입력 프롬프트

        Returns:
            str: LLM 생성 텍스트
        """
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": "qwen3-vl:8b",
            "prompt": f"당신은 안경원 매출 분석 전문가입니다.\n\n{prompt}",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 10000  # 토큰 제한: 영어 사고 + 한글 답변
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()

            # 응답 로깅
            logger.debug(f"LLM Generate API Response: {result}")

            # Ollama generate API 응답 파싱
            if "response" in result:
                content = result["response"]

                # 응답 내용 로깅
                logger.debug(f"LLM Generate Content Length: {len(content)}")
                logger.debug(f"LLM Generate Content Preview: {content[:200] if content else 'EMPTY'}")

                if content and content.strip():
                    return content.strip()

            # 둘 다 실패하면 기본 메시지
            logger.warning("LLM 응답을 파싱할 수 없어 기본 메시지를 반환합니다.")
            return "매출 데이터 분석이 완료되었습니다. LLM 응답을 생성할 수 없어 기본 요약을 제공합니다."
