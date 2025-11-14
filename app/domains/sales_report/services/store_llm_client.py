"""Store LLM Client - Qwen3 모델을 사용한 AI 요약 생성"""
import httpx
import logging
import json
import re
from typing import Optional, Dict
from decimal import Decimal

logger = logging.getLogger(__name__)


class StoreLLMClient:
    """Qwen3 LLM 클라이언트 - AI 매출 요약 생성"""

    def __init__(self, runpod_address: str):
        """
        Args:
            runpod_address: Runpod 서버 주소 (예: "https://xxx.runpod.net")
        """
        self.base_url = runpod_address.rstrip("/")
        self.timeout = 120.0  # LLM 응답은 시간이 걸릴 수 있음 (구조화된 응답 생성에 더 오래 걸림)

    async def generate_sales_summary(
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
        """
        매출 데이터를 기반으로 AI 요약 리포트 생성

        Args:
            store_name: 안경원명
            total_sales: 총 판매금액
            payment_breakdown: 결제 수단 비율 (카드, 현금, 상품권)
            cash_receipt_amount: 현금영수증 발급 금액
            returning_customer_rate: 재방문 고객 비율
            new_customers_count: 신규 고객 수
            avg_transaction_amount: 평균 판매금액
            total_receivables: 총 미수금액
            top_customers: Top 고객 리스트
            peak_sales_date: 매출 피크일
            peak_sales_amount: 피크일 판매금액

        Returns:
            Dict: AI 생성 구조화된 인사이트
        """
        # 프롬프트 생성
        prompt = self._create_prompt(
            store_name=store_name,
            total_sales=total_sales,
            payment_breakdown=payment_breakdown,
            cash_receipt_amount=cash_receipt_amount,
            returning_customer_rate=returning_customer_rate,
            new_customers_count=new_customers_count,
            avg_transaction_amount=avg_transaction_amount,
            total_receivables=total_receivables,
            top_customers=top_customers,
            peak_sales_date=peak_sales_date,
            peak_sales_amount=peak_sales_amount
        )

        # LLM API 호출
        try:
            response_text = await self._call_llm_api(prompt)
            # 구조화된 응답 파싱 (JSON 우선, 텍스트 파싱 fallback)
            insights = self._parse_insights(response_text)
            return insights
        except Exception as e:
            error_type = type(e).__name__
            error_msg = str(e) if str(e) else "알 수 없는 오류"
            logger.error(f"LLM 요약 생성 실패 [{error_type}]: {error_msg}", exc_info=True)
            # LLM 호출 실패 시 기본 구조 반환
            return {
                "sales_summary": f"AI 요약 생성에 실패했습니다 ({error_type}: {error_msg})",
                "sales_strategies": ["데이터를 분석하여 전략을 수립해주세요."],
                "marketing_strategies": ["고객 데이터를 기반으로 마케팅을 계획해주세요."]
            }

    def _create_prompt(
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
        """AI 요약 생성을 위한 프롬프트 작성"""

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

    def _parse_insights(self, response_text: str) -> Dict:
        """
        LLM 응답을 구조화된 인사이트로 파싱 (Hybrid: JSON 우선, 텍스트 파싱 fallback)

        Args:
            response_text: LLM 원본 응답 텍스트

        Returns:
            Dict: 구조화된 인사이트 (sales_summary, sales_strategies, marketing_strategies)
        """
        # 1단계: JSON 파싱 시도
        try:
            # JSON 코드 블록 추출 (```json ... ``` 또는 ``` ... ```)
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                parsed = json.loads(json_str)

                # 필수 키 검증
                if all(k in parsed for k in ["sales_summary", "sales_strategies", "marketing_strategies"]):
                    logger.info("JSON 파싱 성공")
                    return parsed

            # JSON 코드 블록 없이 직접 JSON 파싱 시도
            parsed = json.loads(response_text)
            if all(k in parsed for k in ["sales_summary", "sales_strategies", "marketing_strategies"]):
                logger.info("직접 JSON 파싱 성공")
                return parsed

        except json.JSONDecodeError:
            logger.info("JSON 파싱 실패, 텍스트 파싱으로 전환")

        # 2단계: 텍스트 파싱 fallback
        return self._parse_text_format(response_text)

    def _parse_text_format(self, text: str) -> Dict:
        """
        텍스트 형식 응답 파싱

        형식:
        매출 요약:
        (내용)

        추천 매출 전략:
        1. (전략1)
        2. (전략2)

        추천 마케팅 전략:
        1. (전략1)
        2. (전략2)
        """
        # 매출 요약 추출
        summary_match = re.search(r'매출\s*요약\s*[:：]\s*(.+?)(?=추천|$)', text, re.DOTALL)
        sales_summary = summary_match.group(1).strip() if summary_match else "매출 데이터 분석이 완료되었습니다."

        # 추천 매출 전략 추출
        sales_strategies_match = re.search(r'추천\s*매출\s*전략\s*[:：]\s*(.+?)(?=추천\s*마케팅|$)', text, re.DOTALL)
        sales_strategies = []
        if sales_strategies_match:
            strategies_text = sales_strategies_match.group(1)
            # 번호가 있는 항목 추출 (1. , 2. , 3. 등)
            strategies = re.findall(r'\d+\.\s*(.+?)(?=\d+\.|$)', strategies_text, re.DOTALL)
            sales_strategies = [s.strip() for s in strategies if s.strip()]

        # 번호 없이 줄바꿈으로 구분된 경우
        if not sales_strategies and sales_strategies_match:
            lines = [line.strip() for line in sales_strategies_match.group(1).strip().split('\n') if line.strip()]
            sales_strategies = [line.lstrip('- ').strip() for line in lines if line]

        # 추천 마케팅 전략 추출
        marketing_strategies_match = re.search(r'추천\s*마케팅\s*전략\s*[:：]\s*(.+?)$', text, re.DOTALL)
        marketing_strategies = []
        if marketing_strategies_match:
            strategies_text = marketing_strategies_match.group(1)
            # 번호가 있는 항목 추출
            strategies = re.findall(r'\d+\.\s*(.+?)(?=\d+\.|$)', strategies_text, re.DOTALL)
            marketing_strategies = [s.strip() for s in strategies if s.strip()]

        # 번호 없이 줄바꿈으로 구분된 경우
        if not marketing_strategies and marketing_strategies_match:
            lines = [line.strip() for line in marketing_strategies_match.group(1).strip().split('\n') if line.strip()]
            marketing_strategies = [line.lstrip('- ').strip() for line in lines if line]

        # 기본값 설정 (전략이 없으면)
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
