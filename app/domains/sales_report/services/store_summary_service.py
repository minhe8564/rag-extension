"""Store Summary Service - 매출 데이터 집계 및 분석"""
from typing import Optional, List, Dict
from decimal import Decimal
from datetime import datetime, date
from collections import defaultdict
import logging
import time
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.domains.sales_report.services.adminschool_client import AdminSchoolClient
from app.domains.sales_report.services.store_llm_client import StoreLLMClient
from app.domains.runpod.repositories.runpod_repository import RunpodRepository
from app.domains.sales_report.exceptions import (
    ExternalAPIError,
    DataValidationError,
    LLMServiceError,
    RunpodNotFoundError
)
from app.domains.sales_report.schemas.response.store_summary_response import (
    StoreSummaryResponse,
    DailySalesReport,
    MonthlySalesReport,
    StoreInfo,
    PaymentBreakdown,
    TopCustomer,
    ReceivableCustomer,
    LLMInsights,
    Metadata,
)
from app.domains.sales_report.schemas.request.store_summary_request import StoreInfoRequest


class StoreSummaryService:
    """매출 리포트 생성 서비스"""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.client = AdminSchoolClient()
        self.db = db

    async def generate_report(
        self,
        store_id: str,
        report_date: Optional[date] = None,
        year_month: Optional[str] = None,
        include_ai_summary: bool = False
    ) -> StoreSummaryResponse:
        """
        매출 리포트 생성

        Args:
            store_id: 안경원 ID
            report_date: 일별 리포트 기준일 (None이면 생략)
            year_month: 월별 리포트 기준 년월 (None이면 생략)
            include_ai_summary: AI 요약 포함 여부 (기본값: False)

        Returns:
            StoreSummaryResponse: 통합 리포트
        """
        # 외부 API 데이터 조회
        raw_data = await self.client.fetch_sales_data(store_id)

        # 매장 정보 추출
        store_info = self._extract_store_info(raw_data["info"])

        # 일별 리포트 생성
        daily_report = None
        if report_date:
            daily_report = self._generate_daily_report(raw_data["data"], report_date)

        # 월별 리포트 생성
        monthly_report = None
        if year_month:
            monthly_report = self._generate_monthly_report(raw_data["data"], year_month)

        # AI 인사이트 및 메타데이터 생성 (요청 시에만)
        llm_insights = None
        metadata = None
        if include_ai_summary and monthly_report and self.db:
            start_time = time.time()
            llm_insights = await self._generate_ai_summary(store_info, monthly_report)
            generation_time_ms = int((time.time() - start_time) * 1000)

            if llm_insights:
                metadata = Metadata(
                    ai_model="qwen3-vl:8b",
                    generation_time_ms=generation_time_ms
                )

        return StoreSummaryResponse(
            store_info=store_info,
            daily_report=daily_report,
            monthly_report=monthly_report,
            llm_insights=llm_insights,
            metadata=metadata
        )

    async def generate_report_from_data(
        self,
        store_info: StoreInfoRequest,
        transactions: List[dict],
        report_date: Optional[date] = None,
        year_month: Optional[str] = None,
        include_ai_summary: bool = False
    ) -> StoreSummaryResponse:
        """
        전달받은 데이터로 매출 리포트 생성 (외부 API 호출 없음)

        Args:
            store_info: 매장 정보 (Pydantic 모델)
            transactions: 거래 데이터 리스트
            report_date: 일별 리포트 기준일 (None이면 생략)
            year_month: 월별 리포트 기준 년월 (None이면 생략)
            include_ai_summary: AI 요약 포함 여부 (기본값: False)

        Returns:
            StoreSummaryResponse: 통합 리포트
        """
        # 매장 정보 변환 (Pydantic → Response 모델)
        store_info_response = self._convert_store_info(store_info)

        # 일별 리포트 생성
        daily_report = None
        if report_date:
            daily_report = self._generate_daily_report(transactions, report_date)

        # 월별 리포트 생성
        monthly_report = None
        if year_month:
            monthly_report = self._generate_monthly_report(transactions, year_month)

        # AI 인사이트 및 메타데이터 생성 (요청 시에만)
        llm_insights = None
        metadata = None
        if include_ai_summary and monthly_report and self.db:
            start_time = time.time()
            llm_insights = await self._generate_ai_summary(store_info_response, monthly_report)
            generation_time_ms = int((time.time() - start_time) * 1000)

            if llm_insights:
                metadata = Metadata(
                    ai_model="qwen3-vl:8b",
                    generation_time_ms=generation_time_ms
                )

        return StoreSummaryResponse(
            store_info=store_info_response,
            daily_report=daily_report,
            monthly_report=monthly_report,
            llm_insights=llm_insights,
            metadata=metadata
        )

    def _extract_store_info(self, info_data: dict) -> StoreInfo:
        """매장 정보 추출 (한글/영문 필드명 모두 지원) - 기존 API용"""
        return StoreInfo(
            store_name=info_data.get("안경원명") or info_data.get("store_name", ""),
            store_phone=info_data.get("매장번호") or info_data.get("store_phone", ""),
            owner_name=info_data.get("대표자명") or info_data.get("owner_name", "")
        )

    def _convert_store_info(self, store_info: StoreInfoRequest) -> StoreInfo:
        """Pydantic 모델을 Response 모델로 변환"""
        return StoreInfo(
            store_name=store_info.store_name,
            store_phone=store_info.store_phone,
            owner_name=store_info.owner_name
        )

    def _generate_daily_report(
        self,
        transactions: List[dict],
        report_date: date
    ) -> DailySalesReport:
        """일별 리포트 생성"""
        # 해당 날짜의 거래만 필터링
        date_str = report_date.strftime("%Y-%m-%d")
        daily_transactions = [
            t for t in transactions
            if t.get("판매일자") == date_str and t.get("판매유형") == "판매"
        ]

        # 데이터가 없으면 최신 데이터 날짜 사용
        if not daily_transactions:
            # 판매 유형의 거래만 필터링
            sales_transactions = [
                t for t in transactions if t.get("판매유형") == "판매"
            ]

            if not sales_transactions:
                # 판매 데이터가 아예 없으면 기본값 반환
                return DailySalesReport(
                    report_date=report_date,
                    total_sales=Decimal("0"),
                    avg_transaction_amount=Decimal("0"),
                    new_customers_count=0,
                    top_customers=[]
                )

            # 최신 날짜 찾기
            latest_date_str = max(t.get("판매일자", "") for t in sales_transactions)

            # 최신 날짜의 데이터로 리포트 생성
            daily_transactions = [
                t for t in sales_transactions
                if t.get("판매일자") == latest_date_str
            ]

            # 실제 데이터가 있는 날짜로 변경
            report_date = datetime.strptime(latest_date_str, "%Y-%m-%d").date()

        # 💰 총 판매금액
        total_sales = sum(Decimal(str(t.get("판매금액", 0))) for t in daily_transactions)

        # 💵 평균 판매금액
        avg_amount = total_sales / len(daily_transactions) if daily_transactions else Decimal("0")

        # 👤 신규 고객 수
        new_customers = [t for t in daily_transactions if t.get("첫방문여부") == "첫방문"]
        new_customers_count = len(new_customers)

        # 🏆 구매 Top 고객 (일: 3명)
        top_customers = self._calculate_top_customers(daily_transactions, limit=3)

        return DailySalesReport(
            report_date=report_date,
            total_sales=total_sales,
            avg_transaction_amount=avg_amount,
            new_customers_count=new_customers_count,
            top_customers=top_customers
        )

    def _generate_monthly_report(
        self,
        transactions: List[dict],
        year_month: str
    ) -> MonthlySalesReport:
        """월별 리포트 생성"""
        # 해당 월의 거래만 필터링
        monthly_transactions = [
            t for t in transactions
            if t.get("판매일자", "").startswith(year_month) and t.get("판매유형") == "판매"
        ]

        if not monthly_transactions:
            # 데이터 없으면 기본값 반환
            return self._create_empty_monthly_report(year_month)

        # 💰 총 판매금액
        total_sales = sum(Decimal(str(t.get("판매금액", 0))) for t in monthly_transactions)

        # 💳 결제 수단 비율
        payment_breakdown = self._calculate_payment_breakdown(monthly_transactions)

        # 🧾 현금영수증 발급 금액
        cash_receipt_amount = sum(Decimal(str(t.get("현금영수", 0))) for t in monthly_transactions)

        # 👥 재방문 고객 비율
        returning_rate = self._calculate_returning_customer_rate(monthly_transactions)

        # 👤 신규 고객 수
        new_customers_count = len([
            t for t in monthly_transactions if t.get("첫방문여부") == "첫방문"
        ])

        # 💵 평균 판매금액
        avg_amount = total_sales / len(monthly_transactions) if monthly_transactions else Decimal("0")

        # 🧾 총 미수금액 / 명단
        total_receivables, receivable_customers = self._calculate_receivables(monthly_transactions)

        # 🏆 구매 Top 고객 (월: 10명)
        top_customers = self._calculate_top_customers(monthly_transactions, limit=10)

        # 📅 매출 피크일
        peak_date, peak_amount = self._find_peak_sales_date(monthly_transactions)

        return MonthlySalesReport(
            year_month=year_month,
            total_sales=total_sales,
            payment_breakdown=payment_breakdown,
            cash_receipt_amount=cash_receipt_amount,
            returning_customer_rate=returning_rate,
            new_customers_count=new_customers_count,
            avg_transaction_amount=avg_amount,
            total_receivables=total_receivables,
            receivable_customers=receivable_customers,
            top_customers=top_customers,
            peak_sales_date=peak_date,
            peak_sales_amount=peak_amount
        )

    def _calculate_payment_breakdown(self, transactions: List[dict]) -> PaymentBreakdown:
        """
        결제 수단 비율 계산 (카드, 현금, 상품권)

        Note: 현금영수증은 결제 수단이 아니므로 비율 계산에서 제외
              현금영수증 발급 금액은 별도 필드(cash_receipt_amount)로 제공
        """
        total_card = sum(Decimal(str(t.get("카드", 0))) for t in transactions)
        total_cash = sum(Decimal(str(t.get("현금", 0))) for t in transactions)
        total_voucher = sum(Decimal(str(t.get("상품권금액", 0))) for t in transactions)

        # 실제 결제 수단만 합산 (카드 + 현금 + 상품권)
        total_payment = total_card + total_cash + total_voucher

        if total_payment == 0:
            return PaymentBreakdown(
                card=Decimal("0"),
                cash=Decimal("0"),
                voucher=Decimal("0")
            )

        return PaymentBreakdown(
            card=round(total_card / total_payment, 4),
            cash=round(total_cash / total_payment, 4),
            voucher=round(total_voucher / total_payment, 4)
        )

    def _calculate_returning_customer_rate(self, transactions: List[dict]) -> Decimal:
        """재방문 고객 비율 계산"""
        if not transactions:
            return Decimal("0")

        returning_count = len([
            t for t in transactions if t.get("첫방문여부") == "재방문"
        ])

        return round(Decimal(returning_count) / Decimal(len(transactions)), 4)

    def _calculate_receivables(
        self,
        transactions: List[dict]
    ) -> tuple[Decimal, List[ReceivableCustomer]]:
        """미수금 계산"""
        # 고객별 미수금 집계
        customer_receivables = defaultdict(Decimal)

        for t in transactions:
            customer_name = t.get("고객명", "")
            receivable = Decimal(str(t.get("미수금액", 0)))

            if receivable > 0:
                customer_receivables[customer_name] += receivable

        # 총 미수금액
        total_receivables = sum(customer_receivables.values())

        # 미수금 고객 명단 (미수금액 내림차순 정렬)
        receivable_list = [
            ReceivableCustomer(
                customer_name=name,
                receivable_amount=amount
            )
            for name, amount in sorted(
                customer_receivables.items(),
                key=lambda x: x[1],
                reverse=True
            )
        ]

        return total_receivables, receivable_list

    def _calculate_top_customers(
        self,
        transactions: List[dict],
        limit: int = 10
    ) -> List[TopCustomer]:
        """구매 Top 고객 계산"""
        # 고객별 구매 집계
        customer_stats = defaultdict(lambda: {"amount": Decimal("0"), "count": 0})

        for t in transactions:
            customer_name = t.get("고객명", "")
            amount = Decimal(str(t.get("판매금액", 0)))

            customer_stats[customer_name]["amount"] += amount
            customer_stats[customer_name]["count"] += 1

        # 구매금액 내림차순 정렬 후 상위 N명
        top_list = sorted(
            customer_stats.items(),
            key=lambda x: x[1]["amount"],
            reverse=True
        )[:limit]

        return [
            TopCustomer(
                rank=idx + 1,
                customer_name=name,
                total_amount=stats["amount"],
                transaction_count=stats["count"]
            )
            for idx, (name, stats) in enumerate(top_list)
        ]

    def _find_peak_sales_date(
        self,
        transactions: List[dict]
    ) -> tuple[date, Decimal]:
        """매출 피크일 찾기"""
        # 날짜별 매출 집계
        daily_sales = defaultdict(Decimal)

        for t in transactions:
            date_str = t.get("판매일자", "")
            if date_str:
                amount = Decimal(str(t.get("판매금액", 0)))
                daily_sales[date_str] += amount

        if not daily_sales:
            # 데이터 없으면 오늘 날짜 반환
            return date.today(), Decimal("0")

        # 최대 매출일 찾기
        peak_date_str, peak_amount = max(daily_sales.items(), key=lambda x: x[1])
        peak_date = datetime.strptime(peak_date_str, "%Y-%m-%d").date()

        return peak_date, peak_amount

    def _create_empty_monthly_report(self, year_month: str) -> MonthlySalesReport:
        """빈 월별 리포트 생성"""
        return MonthlySalesReport(
            year_month=year_month,
            total_sales=Decimal("0"),
            payment_breakdown=PaymentBreakdown(
                card=Decimal("0"),
                cash=Decimal("0"),
                voucher=Decimal("0")
            ),
            cash_receipt_amount=Decimal("0"),
            returning_customer_rate=Decimal("0"),
            new_customers_count=0,
            avg_transaction_amount=Decimal("0"),
            total_receivables=Decimal("0"),
            receivable_customers=[],
            top_customers=[],
            peak_sales_date=date.today(),
            peak_sales_amount=Decimal("0")
        )

    async def _generate_ai_summary(
        self,
        store_info: StoreInfo,
        monthly_report: MonthlySalesReport
    ) -> Optional[LLMInsights]:
        """
        AI 요약 리포트 생성 (구조화된 인사이트)

        Args:
            store_info: 매장 정보
            monthly_report: 월별 리포트

        Returns:
            Optional[LLMInsights]: AI 생성 구조화된 인사이트 (실패 시 None)
        """
        try:
            # Runpod에서 qwen3 LLM 주소 조회
            runpod = await RunpodRepository.find_by_name(self.db, "qwen3")

            if not runpod or not runpod.address:
                logger.warning("AI 요약 생성 실패: LLM 서버를 찾을 수 없습니다.")
                raise RunpodNotFoundError("qwen3 LLM 서버를 찾을 수 없습니다.")

            # LLM 클라이언트 생성
            llm_client = StoreLLMClient(runpod.address)

            # Top 고객 데이터 변환 (Pydantic 모델 → dict)
            top_customers_dict = [
                {
                    "customer_name": customer.customer_name,
                    "total_amount": customer.total_amount,
                    "transaction_count": customer.transaction_count
                }
                for customer in monthly_report.top_customers
            ]

            # 결제 수단 비율 변환 (카드, 현금, 상품권만)
            payment_breakdown_dict = {
                "card": monthly_report.payment_breakdown.card,
                "cash": monthly_report.payment_breakdown.cash,
                "voucher": monthly_report.payment_breakdown.voucher
            }

            # AI 인사이트 생성 (구조화된 형식)
            insights_dict = await llm_client.generate_sales_summary(
                store_name=store_info.store_name,
                total_sales=monthly_report.total_sales,
                payment_breakdown=payment_breakdown_dict,
                cash_receipt_amount=monthly_report.cash_receipt_amount,
                returning_customer_rate=monthly_report.returning_customer_rate,
                new_customers_count=monthly_report.new_customers_count,
                avg_transaction_amount=monthly_report.avg_transaction_amount,
                total_receivables=monthly_report.total_receivables,
                top_customers=top_customers_dict,
                peak_sales_date=str(monthly_report.peak_sales_date),
                peak_sales_amount=monthly_report.peak_sales_amount
            )

            # Dict를 Pydantic 모델로 변환
            return LLMInsights(**insights_dict)

        except RunpodNotFoundError:
            # Runpod 서버를 찾을 수 없는 경우 - None 반환 (AI 요약 선택적 기능)
            return None
        except Exception as e:
            # 기타 에러 발생 시 로그 남기고 LLMServiceError 발생
            logger.error(f"AI 요약 생성 실패: {str(e)}", exc_info=True)
            raise LLMServiceError(f"AI 요약 생성 중 오류 발생: {str(e)}")
