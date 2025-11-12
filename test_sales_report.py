"""Sales Report API 테스트 스크립트"""
import asyncio
from datetime import date
from app.domains.sales_report.services.sales_report_service import SalesReportService


async def test_monthly_report():
    """월별 리포트 테스트"""
    print("=" * 60)
    print("월별 매출 리포트 테스트 (store_id: 6266, 2024-11)")
    print("=" * 60)

    service = SalesReportService()

    try:
        # 외부 API 데이터 조회 및 리포트 생성
        report = await service.generate_report(
            store_id="6266",
            report_date=None,
            year_month="2024-11"
        )

        # 매장 정보
        print("\n[매장 정보]")
        print(f"안경원명: {report.store_info.store_name}")
        print(f"매장번호: {report.store_info.store_phone}")
        print(f"대표자명: {report.store_info.owner_name}")

        # 월별 리포트
        if report.monthly_report:
            mr = report.monthly_report
            print("\n[월별 리포트]")
            print(f"💰 총 판매금액: {mr.total_sales:,}원")
            print(f"💵 평균 판매금액: {mr.avg_transaction_amount:,}원")
            print(f"👤 신규 고객 수: {mr.new_customers_count}명")
            print(f"👥 재방문 고객 비율: {mr.returning_customer_rate * 100:.1f}%")

            print("\n[💳 결제 수단 비율]")
            print(f"  - 카드: {mr.payment_breakdown.card * 100:.1f}%")
            print(f"  - 현금: {mr.payment_breakdown.cash * 100:.1f}%")
            print(f"  - 현금영수증: {mr.payment_breakdown.cash_receipt * 100:.1f}%")
            print(f"  - 상품권: {mr.payment_breakdown.voucher * 100:.1f}%")

            print(f"\n[🧾 미수금]")
            print(f"총 미수금액: {mr.total_receivables:,}원")
            print(f"미수금 고객: {len(mr.receivable_customers)}명")
            if mr.receivable_customers:
                print("\n미수금 Top 5:")
                for i, customer in enumerate(mr.receivable_customers[:5], 1):
                    print(f"  {i}. {customer.customer_name}: {customer.receivable_amount:,}원")

            print(f"\n[🏆 구매 Top 10 고객]")
            for i, customer in enumerate(mr.top_customers, 1):
                print(f"  {i}. {customer.customer_name}: {customer.total_amount:,}원 ({customer.transaction_count}건)")

            print(f"\n[📅 매출 피크일]")
            print(f"날짜: {mr.peak_sales_date}")
            print(f"금액: {mr.peak_sales_amount:,}원")

        print("\n✅ 테스트 성공!")
        return report

    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_daily_report():
    """일별 리포트 테스트"""
    print("\n" + "=" * 60)
    print("일별 매출 리포트 테스트 (store_id: 6266, 오늘)")
    print("=" * 60)

    service = SalesReportService()

    try:
        report = await service.generate_report(
            store_id="6266",
            report_date=date.today(),
            year_month=None
        )

        if report.daily_report:
            dr = report.daily_report
            print("\n[일별 리포트]")
            print(f"기준일: {dr.report_date}")
            print(f"💰 총 판매금액: {dr.total_sales:,}원")
            print(f"💵 평균 판매금액: {dr.avg_transaction_amount:,}원")
            print(f"👤 신규 고객 수: {dr.new_customers_count}명")

            print(f"\n[🏆 구매 Top 3 고객]")
            for i, customer in enumerate(dr.top_customers, 1):
                print(f"  {i}. {customer.customer_name}: {customer.total_amount:,}원 ({customer.transaction_count}건)")

        print("\n✅ 일별 테스트 성공!")
        return report

    except Exception as e:
        print(f"\n❌ 일별 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """메인 테스트 실행"""
    print("\n🚀 Sales Report API 테스트 시작\n")

    # 월별 리포트 테스트
    await test_monthly_report()

    # 일별 리포트 테스트
    await test_daily_report()

    print("\n" + "=" * 60)
    print("모든 테스트 완료!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
