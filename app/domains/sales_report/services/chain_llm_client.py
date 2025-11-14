"""Chain LLM Client - 체인 매니저용 구조화된 AI 인사이트 생성"""
import httpx
import logging
import re
import json
from typing import List
from decimal import Decimal

from app.domains.sales_report.schemas.response.chain_summary_response import (
    LLMInsights,
    AnalysisPeriod,
    StorePerformance,
    ProductInsights,
    TimePatterns,
    CustomerAnalysis
)

logger = logging.getLogger(__name__)


class ChainLLMClient:
    """체인 매니저용 LLM 클라이언트 - 구조화된 AI 인사이트 생성"""

    def __init__(self, runpod_address: str):
        """
        Args:
            runpod_address: Runpod 서버 주소 (예: "https://xxx.runpod.net")
        """
        self.base_url = runpod_address.rstrip("/")
        self.timeout = 120.0  # LLM 응답은 시간이 걸릴 수 있음 (구조화된 응답 생성에 더 오래 걸림)

    async def generate_chain_insights(
        self,
        analysis_period: AnalysisPeriod,
        store_performance: List[StorePerformance],
        product_insights: ProductInsights,
        time_patterns: TimePatterns,
        customer_analysis: CustomerAnalysis,
        visit_sales_patterns: List
    ) -> LLMInsights:
        """
        체인 매출 분석 데이터를 기반으로 구조화된 AI 인사이트 생성

        Args:
            analysis_period: 분석 기간
            store_performance: 매장별 성과
            product_insights: 상품 인사이트
            time_patterns: 시간 패턴
            customer_analysis: 고객 분석
            visit_sales_patterns: 방문-매출 효율 패턴

        Returns:
            LLMInsights: 구조화된 인사이트 (sales_summary, sales_strategies, marketing_strategies)
        """
        # 프롬프트 생성
        prompt = self._create_prompt(
            analysis_period=analysis_period,
            store_performance=store_performance,
            product_insights=product_insights,
            time_patterns=time_patterns,
            customer_analysis=customer_analysis,
            visit_sales_patterns=visit_sales_patterns
        )

        # LLM API 호출
        try:
            raw_response = await self._call_llm_api(prompt)

            # 하이브리드 파싱: JSON 우선 → 텍스트 파싱 폴백
            insights = self._parse_hybrid_response(raw_response)
            return insights

        except Exception as e:
            logger.error(f"LLM 인사이트 생성 실패: {str(e)}", exc_info=True)
            # 에러 시 기본 메시지 반환
            return LLMInsights(
                sales_summary=f"AI 인사이트 생성에 실패했습니다: {str(e)}",
                sales_strategies=[],
                marketing_strategies=[]
            )

    def _create_prompt(
        self,
        analysis_period: AnalysisPeriod,
        store_performance: List[StorePerformance],
        product_insights: ProductInsights,
        time_patterns: TimePatterns,
        customer_analysis: CustomerAnalysis,
        visit_sales_patterns: List
    ) -> str:
        """AI 인사이트 생성을 위한 프롬프트 작성"""

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

    def _parse_hybrid_response(self, raw_response: str) -> LLMInsights:
        """
        하이브리드 LLM 응답 파싱: JSON 우선 → 텍스트 파싱 폴백

        Args:
            raw_response: LLM의 원본 응답 텍스트

        Returns:
            LLMInsights: 파싱된 구조화된 인사이트
        """
        # 1단계: JSON 파싱 시도
        try:
            insights = self._parse_json_response(raw_response)
            if insights:
                logger.info("JSON 파싱 성공")
                return insights
        except Exception as e:
            logger.warning(f"JSON 파싱 실패, 텍스트 파싱으로 폴백: {e}")

        # 2단계: 기존 텍스트 파싱 (폴백)
        logger.info("텍스트 파싱 시도")
        return self._parse_structured_response(raw_response)

    def _parse_json_response(self, raw_response: str) -> LLMInsights:
        """
        JSON 형식의 LLM 응답 파싱

        Args:
            raw_response: LLM의 원본 응답 텍스트

        Returns:
            LLMInsights: 파싱된 구조화된 인사이트

        Raises:
            ValueError: JSON 파싱 실패 시
        """
        # JSON 블록 추출 (앞뒤 텍스트 제거)
        # ```json ... ``` 또는 { ... } 형식 지원
        json_patterns = [
            r'```json\s*(\{.*?\})\s*```',  # ```json { ... } ```
            r'```\s*(\{.*?\})\s*```',      # ``` { ... } ```
            r'(\{[^{}]*"sales_summary"[^{}]*\})',  # { "sales_summary": ... }
        ]

        json_match = None
        for pattern in json_patterns:
            json_match = re.search(pattern, raw_response, re.DOTALL)
            if json_match:
                break

        if not json_match:
            raise ValueError("JSON 블록을 찾을 수 없음")

        json_str = json_match.group(1)

        # JSON 파싱
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON 파싱 에러: {e}")

        # 필수 필드 검증
        required_fields = ["sales_summary", "sales_strategies", "marketing_strategies"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"필수 필드 누락: {field}")

        # LLMInsights 객체 생성
        return LLMInsights(
            sales_summary=str(data["sales_summary"]),
            sales_strategies=self._ensure_list(data["sales_strategies"]),
            marketing_strategies=self._ensure_list(data["marketing_strategies"])
        )

    def _ensure_list(self, value) -> List[str]:
        """
        값을 리스트로 변환 (LLM이 문자열로 반환하는 경우 처리)

        Args:
            value: 원본 값 (list 또는 str)

        Returns:
            List[str]: 문자열 리스트
        """
        if isinstance(value, list):
            return [str(item) for item in value]
        elif isinstance(value, str):
            # "1. 전략1\n2. 전략2" 형식 파싱
            lines = value.strip().split('\n')
            strategies = []
            for line in lines:
                line = line.strip()
                # 숫자. 또는 - 제거
                line = re.sub(r'^\d+\.\s*', '', line)
                line = re.sub(r'^-\s*', '', line)
                if line:
                    strategies.append(line)
            return strategies
        else:
            return []

    def _parse_structured_response(self, raw_response: str) -> LLMInsights:
        """
        LLM 응답을 구조화된 형식으로 파싱

        Args:
            raw_response: LLM의 원본 응답 텍스트

        Returns:
            LLMInsights: 파싱된 구조화된 인사이트
        """
        try:
            # 섹션별로 분리
            sales_summary = self._extract_section(raw_response, "매출 요약:", ["추천 매출 전략:", "추천 마케팅 전략:"])
            sales_strategies_text = self._extract_section(raw_response, "추천 매출 전략:", ["추천 마케팅 전략:"])
            marketing_strategies_text = self._extract_section(raw_response, "추천 마케팅 전략:", [])

            # 전략 리스트 파싱 (- 로 시작하는 항목들)
            sales_strategies = self._parse_bullet_list(sales_strategies_text)
            marketing_strategies = self._parse_bullet_list(marketing_strategies_text)

            return LLMInsights(
                sales_summary=sales_summary.strip(),
                sales_strategies=sales_strategies,
                marketing_strategies=marketing_strategies
            )

        except Exception as e:
            logger.error(f"LLM 응답 파싱 실패: {str(e)}", exc_info=True)
            # 파싱 실패 시 원본 텍스트 그대로 반환
            return LLMInsights(
                sales_summary=raw_response,
                sales_strategies=[],
                marketing_strategies=[]
            )

    def _extract_section(self, text: str, start_marker: str, end_markers: List[str]) -> str:
        """
        텍스트에서 특정 섹션 추출

        Args:
            text: 전체 텍스트
            start_marker: 시작 마커 (예: "매출 요약:")
            end_markers: 종료 마커 리스트 (예: ["추천 매출 전략:"])

        Returns:
            추출된 섹션 내용
        """
        # 시작 위치 찾기
        start_idx = text.find(start_marker)
        if start_idx == -1:
            return ""

        # 시작 마커 다음부터 시작
        start_idx += len(start_marker)

        # 종료 위치 찾기
        end_idx = len(text)
        for end_marker in end_markers:
            marker_idx = text.find(end_marker, start_idx)
            if marker_idx != -1:
                end_idx = min(end_idx, marker_idx)

        # 섹션 추출
        section = text[start_idx:end_idx].strip()
        return section

    def _parse_bullet_list(self, text: str) -> List[str]:
        """
        불릿 리스트를 파싱하여 리스트로 변환

        Args:
            text: "- 항목1\n- 항목2\n- 항목3" 형식의 텍스트

        Returns:
            ["항목1", "항목2", "항목3"]
        """
        # "-"로 시작하는 줄들 추출
        lines = text.split("\n")
        items = []

        for line in lines:
            stripped = line.strip()
            # "-"로 시작하는 경우
            if stripped.startswith("-"):
                item = stripped[1:].strip()  # "-" 제거
                if item:
                    items.append(item)
            # "•"로 시작하는 경우도 처리
            elif stripped.startswith("•"):
                item = stripped[1:].strip()  # "•" 제거
                if item:
                    items.append(item)

        return items

    async def _call_llm_api(self, prompt: str) -> str:
        """
        LLM API 호출 (Ollama Chat API)

        Args:
            prompt: 입력 프롬프트

        Returns:
            str: LLM 생성 텍스트
        """
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": "qwen3-vl:8b",
            "messages": [
                {
                    "role": "system",
                    "content": "당신은 체인 안경원 매출 분석 전문가입니다. 데이터를 바탕으로 실용적인 인사이트와 전략을 제공합니다."
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
                logger.debug(f"LLM API Response: {result}")

                # Ollama chat API 응답 파싱
                if "message" in result:
                    message = result["message"]
                    content = message.get("content", "")

                    logger.debug(f"LLM Content Length: {len(content)}")
                    logger.debug(f"LLM Content Preview: {content[:200] if content else 'EMPTY'}")

                    if content and content.strip():
                        return content.strip()

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
            "prompt": f"당신은 체인 안경원 매출 분석 전문가입니다.\n\n{prompt}",
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
            logger.debug(f"LLM Generate API Response: {result}")

            # Ollama generate API 응답 파싱
            if "response" in result:
                content = result["response"]
                logger.debug(f"LLM Generate Content Length: {len(content)}")

                if content and content.strip():
                    return content.strip()

            # 둘 다 실패하면 기본 메시지
            logger.warning("LLM 응답을 파싱할 수 없어 기본 메시지를 반환합니다.")
            return "매출 데이터 분석이 완료되었습니다. LLM 응답을 생성할 수 없어 기본 요약을 제공합니다."
