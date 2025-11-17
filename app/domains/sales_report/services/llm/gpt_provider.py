"""OpenAI GPT LLM 제공자"""
import logging
from decimal import Decimal
from typing import Dict, Optional
import json
import re
import openai

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class GPTLLMProvider(BaseLLMProvider):
    """OpenAI GPT LLM 제공자

    OpenAI API를 사용하여 매출 리포트 AI 요약 생성
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        Args:
            api_key: OpenAI API 키
            model: GPT 모델 이름 (gpt-4o-mini, gpt-4, gpt-3.5-turbo 등)
        """
        super().__init__()

        if not api_key or api_key.strip() == "":
            logger.error("OpenAI API 키가 비어있습니다. 환경 변수 OPENAI_API_KEY를 확인하세요.")
            raise ValueError("OpenAI API 키가 필요합니다. .env 파일의 OPENAI_API_KEY를 확인하세요.")

        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        logger.info(f"GPT LLM Provider 초기화 완료 (모델: {model})")

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
        """매장 요약 생성"""

        # 커스텀 프롬프트 또는 기본 프롬프트 사용
        if custom_prompt:
            prompt = self._create_custom_store_prompt(
                custom_prompt, store_name, total_sales, payment_breakdown,
                cash_receipt_amount, returning_customer_rate,
                new_customers_count, avg_transaction_amount,
                total_receivables, top_customers,
                peak_sales_date, peak_sales_amount
            )
        else:
            prompt = self._create_store_prompt(
                store_name, total_sales, payment_breakdown,
                cash_receipt_amount, returning_customer_rate,
                new_customers_count, avg_transaction_amount,
                total_receivables, top_customers,
                peak_sales_date, peak_sales_amount
            )

        try:
            response_text = await self._call_gpt_api(prompt)
            insights = self._parse_insights(response_text)
            return insights
        except Exception as e:
            logger.error(f"GPT 매장 요약 생성 실패: {e}", exc_info=True)
            return {
                "sales_summary": f"AI 요약 생성에 실패했습니다: {str(e)}",
                "sales_strategies": ["데이터를 분석하여 전략을 수립해주세요."],
                "marketing_strategies": ["고객 데이터를 기반으로 마케팅을 계획해주세요."]
            }

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
        """체인 인사이트 생성"""

        # 커스텀 프롬프트 또는 기본 프롬프트 사용
        if custom_prompt:
            prompt = self._create_custom_chain_prompt(
                custom_prompt, analysis_period, store_performance,
                product_insights, time_patterns,
                customer_analysis, visit_sales_patterns
            )
        else:
            prompt = self._create_chain_prompt(
                analysis_period, store_performance,
                product_insights, time_patterns,
                customer_analysis, visit_sales_patterns
            )

        try:
            raw_response = await self._call_gpt_api(prompt)
            insights = self._parse_hybrid_response(raw_response)
            return {
                "sales_summary": insights.get("sales_summary", ""),
                "sales_strategies": insights.get("sales_strategies", []),
                "marketing_strategies": insights.get("marketing_strategies", [])
            }
        except Exception as e:
            logger.error(f"GPT 체인 인사이트 생성 실패: {e}")
            return {
                "sales_summary": f"AI 인사이트 생성 실패: {str(e)}",
                "sales_strategies": [],
                "marketing_strategies": []
            }

    async def _call_gpt_api(self, prompt: str) -> str:
        """OpenAI GPT API 호출"""
        try:
            # API 파라미터 구성
            params = {
                "model": self.model,
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
                "max_completion_tokens": 2000  # 최신 모델용 파라미터
            }

            # temperature 파라미터 조건부 추가 (일부 모델은 미지원)
            # gpt-4o-mini, gpt-4o, gpt-4-turbo 등 표준 모델은 temperature 지원
            if not self.model.startswith("gpt-5"):  # gpt-5 계열은 temperature 미지원 가능성
                params["temperature"] = 0.7

            response = await self.client.chat.completions.create(**params)

            content = response.choices[0].message.content
            logger.debug(f"GPT API Response Length: {len(content)}")
            return content.strip()

        except openai.APIError as e:
            logger.error(f"GPT API 오류: {e}")
            raise
        except Exception as e:
            logger.error(f"GPT 호출 실패: {e}")
            raise

    def _create_store_prompt(
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
    ) -> str:
        """매장 프롬프트 생성 (Qwen과 동일)"""

        # Top 고객 텍스트 생성
        top_customers_text = ""
        for customer in top_customers[:3]:
            top_customers_text += f"- {customer['customer_name']}: {int(customer['total_amount']):,}원 (구매 {customer['transaction_count']}회)\n"

        # 결제 수단 텍스트
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

# 구매 Top 고객 (상위 3명)
{top_customers_text}

# 요청사항
JSON 형식으로 한국어로만 작성해주세요:

```json
{{
  "sales_summary": "이번 달 매출의 주요 특징과 인사이트를 2-3문장으로 요약",
  "sales_strategies": [
    "구체적인 매출 증대 전략 1",
    "구체적인 매출 증대 전략 2",
    "구체적인 매출 증대 전략 3"
  ],
  "marketing_strategies": [
    "고객 유치 및 재방문 유도 마케팅 방안 1",
    "고객 유치 및 재방문 유도 마케팅 방안 2",
    "고객 유치 및 재방문 유도 마케팅 방안 3"
  ]
}}
```

필수: 한국어로만 작성, 전략은 각 3개씩, 실용적인 톤"""

        return prompt

    def _create_chain_prompt(
        self,
        analysis_period,
        store_performance,
        product_insights,
        time_patterns,
        customer_analysis,
        visit_sales_patterns
    ) -> str:
        """체인 프롬프트 생성 (Qwen과 유사)"""

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
            brand_text += f"- {brand.brand_name}: {int(brand.total_revenue):,}원 (매출비중 {brand.revenue_share}%, 판매수량 {brand.quantity_sold}개)\n"

        # 상품 구분별 매출 텍스트
        category_text = ""
        for category in product_insights.category_revenues[:5]:
            category_text += f"- {category.category_name}: {int(category.total_revenue):,}원 (매출비중 {category.revenue_share}%, 판매수량 {category.quantity_sold}개)\n"

        # 시간 패턴 텍스트
        time_text = f"최고 매출: {time_patterns.peak_insights.best_day} {time_patterns.peak_insights.best_time}\n"
        time_text += f"최저 매출: {time_patterns.peak_insights.worst_day} {time_patterns.peak_insights.worst_time}"

        # 고객 연령대 텍스트
        customer_text = f"주력 연령대: {customer_analysis.key_segments.dominant_age_group}\n"
        customer_text += f"객단가 최고: {customer_analysis.key_segments.highest_avg_purchase_age}"

        # 방문-매출 효율 텍스트
        efficiency_text = ""
        for pattern in visit_sales_patterns[:5]:
            efficiency_text += f"- {pattern.day_name} {pattern.hour}시: 방문당 {int(pattern.revenue_per_visit):,}원 (방문 {pattern.total_visits}명, 매출 {int(pattern.total_revenue):,}원)\n"

        prompt = f"""당신은 체인 안경원 매출 분석 전문가입니다. 아래 데이터를 바탕으로 매출 요약과 전략을 제안해주세요.

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

# 요청사항
JSON 형식으로 한국어로만 작성해주세요:

```json
{{
  "sales_summary": "이번 달 매출의 주요 특징과 인사이트를 2-3문장으로 요약",
  "sales_strategies": [
    "구체적인 매출 증대 전략 1",
    "구체적인 매출 증대 전략 2",
    "구체적인 매출 증대 전략 3"
  ],
  "marketing_strategies": [
    "고객 유치 및 재방문 유도 마케팅 방안 1",
    "고객 유치 및 재방문 유도 마케팅 방안 2",
    "고객 유치 및 재방문 유도 마케팅 방안 3"
  ]
}}
```

필수: 한국어로만, 친절하고 실용적인 톤, 500자 이내

**숫자 표기**: 금액은 쉼표 형식 그대로 (예: "48,856,200원")"""

        return prompt

    def _parse_insights(self, response_text: str) -> Dict:
        """인사이트 파싱 (JSON 우선, 텍스트 폴백)"""

        # JSON 파싱 시도
        try:
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed = json.loads(json_str)

                if all(k in parsed for k in ["sales_summary", "sales_strategies", "marketing_strategies"]):
                    logger.info("GPT JSON 파싱 성공")
                    # 형식 검증 및 정규화
                    return self._normalize_insights(parsed)

            # 코드 블록 없이 직접 파싱
            parsed = json.loads(response_text)
            if all(k in parsed for k in ["sales_summary", "sales_strategies", "marketing_strategies"]):
                logger.info("GPT 직접 JSON 파싱 성공")
                # 형식 검증 및 정규화
                return self._normalize_insights(parsed)

        except json.JSONDecodeError:
            logger.info("GPT JSON 파싱 실패, 텍스트 파싱 시도")

        # 텍스트 파싱 폴백 (Qwen과 동일한 로직)
        return self._parse_text_format(response_text)

    # _normalize_insights() → BaseLLMProvider로 이동됨 (중복 제거)

    def _parse_text_format(self, text: str) -> Dict:
        """텍스트 형식 응답 파싱 (Qwen과 동일)"""

        # 매출 요약 추출
        summary_match = re.search(r'매출\s*요약\s*[:：]\s*(.+?)(?=추천|$)', text, re.DOTALL)
        sales_summary = summary_match.group(1).strip() if summary_match else "매출 데이터 분석이 완료되었습니다."

        # 추천 매출 전략 추출
        sales_strategies_match = re.search(r'추천\s*매출\s*전략\s*[:：]\s*(.+?)(?=추천\s*마케팅|$)', text, re.DOTALL)
        sales_strategies = []
        if sales_strategies_match:
            strategies_text = sales_strategies_match.group(1)
            strategies = re.findall(r'\d+\.\s*(.+?)(?=\d+\.|$)', strategies_text, re.DOTALL)
            sales_strategies = [s.strip() for s in strategies if s.strip()]

        if not sales_strategies and sales_strategies_match:
            lines = [line.strip() for line in sales_strategies_match.group(1).strip().split('\n') if line.strip()]
            sales_strategies = [line.lstrip('- ').strip() for line in lines if line]

        # 추천 마케팅 전략 추출
        marketing_strategies_match = re.search(r'추천\s*마케팅\s*전략\s*[:：]\s*(.+?)$', text, re.DOTALL)
        marketing_strategies = []
        if marketing_strategies_match:
            strategies_text = marketing_strategies_match.group(1)
            strategies = re.findall(r'\d+\.\s*(.+?)(?=\d+\.|$)', strategies_text, re.DOTALL)
            marketing_strategies = [s.strip() for s in strategies if s.strip()]

        if not marketing_strategies and marketing_strategies_match:
            lines = [line.strip() for line in marketing_strategies_match.group(1).strip().split('\n') if line.strip()]
            marketing_strategies = [line.lstrip('- ').strip() for line in lines if line]

        # 기본값 설정
        if not sales_strategies:
            sales_strategies = ["데이터를 분석하여 매출 전략을 수립해주세요."]
        if not marketing_strategies:
            marketing_strategies = ["고객 데이터를 기반으로 마케팅을 계획해주세요."]

        return {
            "sales_summary": sales_summary,
            "sales_strategies": sales_strategies,
            "marketing_strategies": marketing_strategies
        }

    def _parse_hybrid_response(self, raw_response: str) -> Dict:
        """하이브리드 응답 파싱 (JSON 우선 → 텍스트 폴백)"""

        # JSON 파싱 시도
        try:
            insights = self._parse_json_response(raw_response)
            if insights:
                logger.info("GPT 체인 JSON 파싱 성공")
                return insights
        except Exception as e:
            logger.warning(f"GPT 체인 JSON 파싱 실패, 텍스트 파싱 폴백: {e}")

        # 텍스트 파싱
        logger.info("GPT 체인 텍스트 파싱 시도")
        return self._parse_text_format(raw_response)

    def _parse_json_response(self, raw_response: str) -> Dict:
        """JSON 형식 응답 파싱"""

        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',
            r'```\s*(\{.*?\})\s*```',
            r'(\{[^{}]*"sales_summary"[^{}]*\})',
        ]

        json_match = None
        for pattern in json_patterns:
            json_match = re.search(pattern, raw_response, re.DOTALL)
            if json_match:
                break

        if not json_match:
            raise ValueError("JSON 블록을 찾을 수 없음")

        json_str = json_match.group(1)

        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 에러: {e}")

        required_fields = ["sales_summary", "sales_strategies", "marketing_strategies"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"필수 필드 누락: {field}")

        return {
            "sales_summary": str(data["sales_summary"]),
            "sales_strategies": data["sales_strategies"] if isinstance(data["sales_strategies"], list) else [],
            "marketing_strategies": data["marketing_strategies"] if isinstance(data["marketing_strategies"], list) else []
        }

    # _create_custom_store_prompt() → BaseLLMProvider로 이동됨 (중복 제거)

    # _create_custom_chain_prompt() → BaseLLMProvider로 이동됨 (중복 제거)
