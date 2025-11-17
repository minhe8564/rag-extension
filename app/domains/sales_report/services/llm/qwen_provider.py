"""Qwen LLM 제공자 (기존 StoreLLMClient, ChainLLMClient 코드 이관)"""
import httpx
import logging
import json
import re
from decimal import Decimal
from typing import Dict, List, Optional

from .base import BaseLLMProvider

logger = logging.getLogger(__name__)


class QwenLLMProvider(BaseLLMProvider):
    """Qwen3 (Ollama) LLM 제공자

    기존 StoreLLMClient, ChainLLMClient 코드를 그대로 이관하여
    Qwen 기반 AI 요약 생성 기능 제공
    """

    def __init__(self, base_url: str):
        """
        Args:
            base_url: Runpod/Ollama 서버 주소 (예: "https://xxx.runpod.net")
        """
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.timeout = 120.0  # LLM 응답은 시간이 걸릴 수 있음
        self.model = "qwen3-vl:8b"

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
        """매장 요약 생성 (기존 StoreLLMClient.generate_sales_summary 로직)"""

        # 프롬프트 생성 (커스텀 프롬프트 우선, 없으면 기본 프롬프트)
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

        # LLM API 호출
        try:
            response_text = await self._call_ollama_api(prompt)
            insights = self._parse_insights(response_text)
            return insights
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e) if str(e) else "알 수 없는 오류"
            logger.error(f"Qwen 매장 요약 생성 실패 [{error_type}]: {error_msg}", exc_info=True)
            return {
                "sales_summary": f"AI 요약 생성에 실패했습니다 ({error_type}: {error_msg})",
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
        """체인 인사이트 생성 (기존 ChainLLMClient 로직)"""

        # 프롬프트 생성 (커스텀 프롬프트 우선, 없으면 기본 프롬프트)
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
            raw_response = await self._call_ollama_api(prompt)
            insights = self._parse_hybrid_response(raw_response)

            return {
                "sales_summary": insights.get("sales_summary", ""),
                "sales_strategies": insights.get("sales_strategies", []),
                "marketing_strategies": insights.get("marketing_strategies", [])
            }
        except Exception as e:
            logger.error(f"Qwen 체인 인사이트 생성 실패: {e}", exc_info=True)
            return {
                "sales_summary": f"AI 인사이트 생성에 실패했습니다: {str(e)}",
                "sales_strategies": [],
                "marketing_strategies": []
            }

    # === Ollama API 호출 메서드 ===

    async def _call_ollama_api(self, prompt: str) -> str:
        """Ollama Chat API 호출 (기존 _call_llm_api 로직)"""
        url = f"{self.base_url}/api/chat"

        payload = {
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
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 10000
            }
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                result = response.json()
                logger.debug(f"Qwen API Response: {result}")

                if "message" in result:
                    message = result["message"]
                    content = message.get("content", "")

                    logger.debug(f"Qwen Content Length: {len(content)}")
                    logger.debug(f"Qwen Content Preview: {content[:200] if content else 'EMPTY'}")

                    if content and content.strip():
                        return content.strip()

                raise ValueError("Qwen 응답이 비어있습니다.")

        except Exception as e:
            logger.warning(f"Qwen Chat API 실패, generate API 시도: {e}")
            return await self._call_ollama_api_generate(prompt)

    async def _call_ollama_api_generate(self, prompt: str) -> str:
        """Ollama Generate API 폴백"""
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": f"당신은 안경원 매출 분석 전문가입니다.\n\n{prompt}",
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 10000
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()
            logger.debug(f"Qwen Generate API Response: {result}")

            if "response" in result:
                content = result["response"]
                logger.debug(f"Qwen Generate Content Length: {len(content)}")

                if content and content.strip():
                    return content.strip()

            logger.warning("Qwen 응답 파싱 실패, 기본 메시지 반환")
            return "매출 데이터 분석이 완료되었습니다. LLM 응답을 생성할 수 없어 기본 요약을 제공합니다."

    # === 프롬프트 생성 메서드 ===

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
        """매장 프롬프트 생성 (기존 StoreLLMClient._create_prompt)"""

        # Top 고객 텍스트 생성 (상위 3명만)
        top_customers_text = ""
        for customer in top_customers[:3]:
            top_customers_text += f"- {customer['customer_name']}: {int(customer['total_amount']):,}원 (구매 {customer['transaction_count']}회)\n"

        # 결제 수단 텍스트 생성
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
아래 두 가지 형식 중 하나로 **바로** 한국어로만 작성해주세요. 영어 사고 과정은 절대 쓰지 마세요.

**형식 1 (JSON - 권장)**:
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

**형식 2 (텍스트)**:
매출 요약:
(이번 달 매출의 주요 특징과 인사이트를 2-3문장으로 요약)

추천 매출 전략:
1. (구체적인 매출 증대 전략 1)
2. (구체적인 매출 증대 전략 2)
3. (구체적인 매출 증대 전략 3)

추천 마케팅 전략:
1. (고객 유치 및 재방문 유도 마케팅 방안 1)
2. (고객 유치 및 재방문 유도 마케팅 방안 2)
3. (고객 유치 및 재방문 유도 마케팅 방안 3)

**필수 규칙**:
1. 영어 설명이나 사고 과정 절대 포함하지 마세요
2. JSON 형식을 우선 사용하되, 텍스트 형식도 가능
3. 전략은 각각 3개씩 작성
4. 친절하고 실용적인 톤으로 작성
"""
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
        """체인 프롬프트 생성 (기존 ChainLLMClient._create_prompt)"""

        # 매장별 성과 텍스트
        store_text = ""
        for perf in store_performance[:3]:  # 상위 3개 매장만
            store_text += f"- {perf.store_name}: {int(perf.total_revenue):,}원 (객단가 {int(perf.avg_transaction_value):,}원)\n"

        # 베스트 상품 텍스트
        product_text = ""
        for product in product_insights.top_products[:5]:  # 상위 5개만
            product_text += f"- {product.product_name} ({product.brand_name}): {int(product.total_revenue):,}원 (매출비중 {product.revenue_share}%)\n"

        # 베스트 브랜드 텍스트
        brand_text = ""
        for brand in product_insights.top_brands[:5]:  # 상위 5개만
            brand_text += f"- {brand.brand_name}: {int(brand.total_revenue):,}원 (매출비중 {brand.revenue_share}%, 판매수량 {brand.quantity_sold}개)\n"

        # 상품 구분별 매출 텍스트
        category_text = ""
        for category in product_insights.category_revenues[:5]:  # 상위 5개만
            category_text += f"- {category.category_name}: {int(category.total_revenue):,}원 (매출비중 {category.revenue_share}%, 판매수량 {category.quantity_sold}개)\n"

        # 시간 패턴 텍스트
        time_text = f"최고 매출: {time_patterns.peak_insights.best_day} {time_patterns.peak_insights.best_time}\n"
        time_text += f"최저 매출: {time_patterns.peak_insights.worst_day} {time_patterns.peak_insights.worst_time}"

        # 고객 연령대 텍스트
        customer_text = f"주력 연령대: {customer_analysis.key_segments.dominant_age_group}\n"
        customer_text += f"객단가 최고: {customer_analysis.key_segments.highest_avg_purchase_age}"

        # 방문-매출 효율 텍스트
        efficiency_text = ""
        for pattern in visit_sales_patterns[:5]:  # 상위 5개만
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
아래 두 가지 형식 중 하나로 **바로** 한국어로만 작성해주세요. 영어 사고 과정은 절대 쓰지 마세요.

**형식 1 (JSON - 권장)**:
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

**형식 2 (텍스트)**:
매출 요약:
(이번 달 매출의 주요 특징과 인사이트를 2-3문장으로 요약)

추천 매출 전략:
- (구체적인 매출 증대 전략 1)
- (구체적인 매출 증대 전략 2)
- (구체적인 매출 증대 전략 3)

추천 마케팅 전략:
- (고객 유치 및 재방문 유도 마케팅 방안 1)
- (고객 유치 및 재방문 유도 마케팅 방안 2)
- (고객 유치 및 재방문 유도 마케팅 방안 3)

**필수 규칙**:
1. 영어 설명이나 사고 과정 절대 포함하지 마세요
2. 바로 답변만 작성하세요
3. 친절하고 실용적인 톤으로 500자 이내로 간결하게 작성

**숫자 표기 규칙 (매우 중요!)**:
- 금액은 반드시 쉼표 형식 그대로 사용하세요 (예: "48,856,200원", "130,283원")
- 절대로 "만원" 단위로 변환하지 마세요
- 예시: "48,856,200원" ✅ | "4885만원" ❌ | "48,856만원" ❌
"""
        return prompt

    # === 응답 파싱 메서드 ===

    def _parse_insights(self, response_text: str) -> Dict:
        """인사이트 파싱 (JSON 우선, 텍스트 파싱 fallback)"""

        # 1단계: JSON 파싱 시도
        try:
            # JSON 코드 블록 추출
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed = json.loads(json_str)

                if all(k in parsed for k in ["sales_summary", "sales_strategies", "marketing_strategies"]):
                    logger.info("JSON 파싱 성공")
                    # 형식 검증 및 정규화
                    return self._normalize_insights(parsed)

            # JSON 코드 블록 없이 직접 파싱
            parsed = json.loads(response_text)
            if all(k in parsed for k in ["sales_summary", "sales_strategies", "marketing_strategies"]):
                logger.info("직접 JSON 파싱 성공")
                # 형식 검증 및 정규화
                return self._normalize_insights(parsed)

        except json.JSONDecodeError:
            logger.info("JSON 파싱 실패, 텍스트 파싱으로 전환")

        # 2단계: 텍스트 파싱 fallback
        return self._parse_text_format(response_text)

    # _normalize_insights() → BaseLLMProvider로 이동됨 (중복 제거)

    def _parse_text_format(self, text: str) -> Dict:
        """텍스트 형식 응답 파싱"""

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

        logger.info(f"텍스트 파싱 완료: summary={len(sales_summary)}, sales={len(sales_strategies)}, marketing={len(marketing_strategies)}")

        return {
            "sales_summary": sales_summary,
            "sales_strategies": sales_strategies,
            "marketing_strategies": marketing_strategies
        }

    def _parse_hybrid_response(self, raw_response: str) -> Dict:
        """하이브리드 응답 파싱 (JSON 우선 → 텍스트 파싱 폴백)"""

        # JSON 파싱 시도
        try:
            insights = self._parse_json_response(raw_response)
            if insights:
                logger.info("체인 JSON 파싱 성공")
                return insights
        except Exception as e:
            logger.warning(f"체인 JSON 파싱 실패, 텍스트 파싱 폴백: {e}")

        # 텍스트 파싱
        logger.info("체인 텍스트 파싱 시도")
        return self._parse_structured_response(raw_response)

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
            "sales_strategies": self._ensure_list(data["sales_strategies"]),
            "marketing_strategies": self._ensure_list(data["marketing_strategies"])
        }

    def _ensure_list(self, value) -> List[str]:
        """값을 리스트로 변환"""

        if isinstance(value, list):
            return [str(item) for item in value]
        elif isinstance(value, str):
            lines = value.strip().split('\n')
            strategies = []
            for line in lines:
                line = line.strip()
                line = re.sub(r'^\d+\.\s*', '', line)
                line = re.sub(r'^-\s*', '', line)
                if line:
                    strategies.append(line)
            return strategies
        else:
            return []

    def _parse_structured_response(self, raw_response: str) -> Dict:
        """구조화된 텍스트 응답 파싱"""

        try:
            sales_summary = self._extract_section(raw_response, "매출 요약:", ["추천 매출 전략:", "추천 마케팅 전략:"])
            sales_strategies_text = self._extract_section(raw_response, "추천 매출 전략:", ["추천 마케팅 전략:"])
            marketing_strategies_text = self._extract_section(raw_response, "추천 마케팅 전략:", [])

            sales_strategies = self._parse_bullet_list(sales_strategies_text)
            marketing_strategies = self._parse_bullet_list(marketing_strategies_text)

            return {
                "sales_summary": sales_summary.strip(),
                "sales_strategies": sales_strategies,
                "marketing_strategies": marketing_strategies
            }

        except Exception as e:
            logger.error(f"구조화된 응답 파싱 실패: {str(e)}", exc_info=True)
            return {
                "sales_summary": raw_response,
                "sales_strategies": [],
                "marketing_strategies": []
            }

    def _extract_section(self, text: str, start_marker: str, end_markers: List[str]) -> str:
        """텍스트에서 특정 섹션 추출"""

        start_idx = text.find(start_marker)
        if start_idx == -1:
            return ""

        start_idx += len(start_marker)

        end_idx = len(text)
        for end_marker in end_markers:
            marker_idx = text.find(end_marker, start_idx)
            if marker_idx != -1:
                end_idx = min(end_idx, marker_idx)

        section = text[start_idx:end_idx].strip()
        return section

    def _parse_bullet_list(self, text: str) -> List[str]:
        """불릿 리스트를 파싱하여 리스트로 변환"""

        lines = text.split("\n")
        items = []

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("-"):
                item = stripped[1:].strip()
                if item:
                    items.append(item)
            elif stripped.startswith("•"):
                item = stripped[1:].strip()
                if item:
                    items.append(item)

        return items

    # === 커스텀 프롬프트 메서드 ===
    # _create_custom_store_prompt() → BaseLLMProvider로 이동됨 (중복 제거)

    # _create_custom_chain_prompt() → BaseLLMProvider로 이동됨 (중복 제거)
