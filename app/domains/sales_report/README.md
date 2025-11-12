# Sales Report API - 안경원 매출 리포트

안경원 매출 데이터를 집계하여 일별/월별 리포트를 생성하는 API입니다.

## 📁 디렉토리 구조

```
sales_report/
├── __init__.py
├── routers/
│   ├── __init__.py
│   └── sales_reports.py          # API 엔드포인트
├── schemas/
│   ├── __init__.py
│   ├── request/
│   │   └── __init__.py
│   └── response/
│       ├── __init__.py
│       └── sales_report.py        # 응답 스키마
└── services/
    ├── __init__.py
    ├── adminschool_client.py      # 외부 API 클라이언트
    └── sales_report_service.py    # 데이터 집계 서비스
```

## 🚀 API 엔드포인트

### 1. 일별 매출 리포트 조회

```
GET /api/v1/sales-reports/{store_id}/daily?report_date=YYYY-MM-DD
```

**응답 항목:**
- 💰 총 판매금액
- 💵 평균 판매금액 (객단가)
- 👤 신규 고객 수
- 🏆 구매 Top 3 고객

**예시:**
```bash
curl http://localhost:8000/api/v1/sales-reports/6266/daily?report_date=2024-11-12
```

### 2. 월별 매출 리포트 조회

```
GET /api/v1/sales-reports/{store_id}/monthly?year_month=YYYY-MM
```

**응답 항목:**
- 💰 총 판매금액
- 💳 결제 수단 비율 (카드/현금/현금영수증/상품권)
- 👥 재방문 고객 비율
- 👤 신규 고객 수
- 📈 전월/전년 대비 매출 증감률
- 💵 평균 판매금액
- 🧾 총 미수금액 및 고객 명단
- 🏆 구매 Top 10 고객
- 📅 매출 피크일

**예시:**
```bash
curl http://localhost:8000/api/v1/sales-reports/6266/monthly?year_month=2024-11
```

### 3. 통합 리포트 조회 (일별 + 월별)

```
GET /api/v1/sales-reports/{store_id}/combined?report_date=YYYY-MM-DD&year_month=YYYY-MM
```

**예시:**
```bash
curl http://localhost:8000/api/v1/sales-reports/6266/combined?report_date=2024-11-12&year_month=2024-11
```

## 📊 응답 예시

```json
{
  "store_info": {
    "store_name": "행복안경원",
    "store_phone": "02-1234-5678",
    "owner_name": "홍길동"
  },
  "daily_report": {
    "report_date": "2024-11-12",
    "total_sales": "1500000",
    "avg_transaction_amount": "125000",
    "new_customers_count": 8,
    "top_customers": [
      {
        "customer_name": "홍길동",
        "total_amount": "500000",
        "transaction_count": 2
      }
    ]
  },
  "monthly_report": {
    "year_month": "2024-11",
    "total_sales": "45000000",
    "payment_breakdown": {
      "card": "0.75",
      "cash": "0.20",
      "cash_receipt": "0.03",
      "voucher": "0.02"
    },
    "returning_customer_rate": "0.65",
    "new_customers_count": 43,
    "avg_transaction_amount": "375000",
    "total_receivables": "5000000",
    "receivable_customers": [...],
    "top_customers": [...],
    "peak_sales_date": "2024-11-15",
    "peak_sales_amount": "2500000"
  },
  "ai_summary": null
}
```

## 🔧 구현 세부사항

### AdminSchoolClient
- 외부 API (https://napi.adminschool.net) 호출
- 안경원 판매 데이터 조회
- 타임아웃: 30초

### SalesReportService
- 거래 데이터 필터링 및 집계
- 일별/월별 리포트 생성
- 결제 수단 비율 계산
- 재방문 고객 비율 계산
- Top 고객 순위 계산
- 미수금 집계
- 매출 피크일 분석

### 데이터 처리 로직
1. 외부 API에서 전체 데이터 조회
2. 판매 유형별 필터링 ("판매", "반품", "납부")
3. 날짜/기간별 필터링
4. 고객별 집계 (신규/재방문, 구매금액, 미수금)
5. 결제 수단별 집계
6. 일별 매출 집계 (피크일 계산)

## 📝 데이터 정제 규칙

### 필터링
- **판매 데이터**: `판매유형 == "판매"` 만 집계
- **반품/납부**: 현재 버전에서는 제외 (추후 확장 가능)

### 고객 분류
- **신규 고객**: `첫방문여부 == "첫방문"`
- **재방문 고객**: `첫방문여부 == "재방문"`

### 금액 계산
- **총 판매금액**: `판매금액` 합계
- **결제금액**: `카드 + 현금 + 현금영수 + 상품권금액`
- **미수금**: `미수금액` 양수인 거래만 집계

## 🚧 추후 확장 계획

### Phase 2: DB 저장
- MySQL 테이블 생성
- 리포트 이력 저장
- 이력 조회 API 추가

### Phase 3: AI 요약
- 🤖 AI 요약 리포트 생성
- Gemini API 연동
- 매출 트렌드 분석 텍스트 생성

### Phase 4: 추가 분석
- 전월/전년 대비 증감률 계산 (이력 데이터 필요)
- 요일별 매출 패턴 분석
- 고객 세그먼트 분석
- 재방문 주기 분석

## 📌 주의사항

1. **외부 API 의존성**
   - AdminSchool API가 다운되면 서비스 불가
   - 타임아웃 설정: 30초

2. **데이터 크기**
   - 대량 데이터 시 응답 시간 증가 가능
   - 추후 페이지네이션 고려

3. **날짜 형식**
   - 일별: `YYYY-MM-DD` (예: 2024-11-12)
   - 월별: `YYYY-MM` (예: 2024-11)

4. **미구현 기능**
   - 전월/전년 대비 증감률 (이력 데이터 필요)
   - AI 요약 리포트 (Gemini API 연동 필요)

## 🧪 테스트

```bash
# 서버 실행
python run.py

# API 문서 확인
# http://localhost:8000/docs

# 월별 리포트 테스트
curl http://localhost:8000/api/v1/sales-reports/6266/monthly

# 일별 리포트 테스트
curl http://localhost:8000/api/v1/sales-reports/6266/daily
```

## 📈 통계

- **총 코드 라인**: 703줄
- **API 엔드포인트**: 3개
- **응답 스키마**: 7개
- **서비스 레이어**: 2개
