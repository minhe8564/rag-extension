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
    ├── llm_client.py              # LLM (qwen3-vl) 클라이언트
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
GET /api/v1/sales-reports/{store_id}/monthly?year_month=YYYY-MM&skip_ai=true
```

**파라미터:**
- `year_month`: 리포트 기준 년월 (생략 시 이번 달)
- `skip_ai`: AI 요약 생략 여부 (기본값: `true`)
  - `true`: 즉시 응답 (ai_summary=null)
  - `false`: AI 요약 포함 (40-50초 소요)

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
- 🤖 AI 요약 리포트 (skip_ai=false인 경우)

**예시:**
```bash
# 즉시 응답 (기본값)
curl http://localhost:8000/api/v1/sales-reports/6266/monthly?year_month=2024-11

# AI 요약 포함 (40-50초 소요)
curl http://localhost:8000/api/v1/sales-reports/6266/monthly?year_month=2024-11&skip_ai=false
```

### 3. 통합 리포트 조회 (일별 + 월별)

```
GET /api/v1/sales-reports/{store_id}/combined?report_date=YYYY-MM-DD&year_month=YYYY-MM&skip_ai=true
```

**파라미터:**
- `report_date`: 일별 리포트 기준일 (생략 시 오늘)
- `year_month`: 월별 리포트 기준 년월 (생략 시 이번 달)
- `skip_ai`: AI 요약 생략 여부 (기본값: `true`)

**예시:**
```bash
# 즉시 응답
curl http://localhost:8000/api/v1/sales-reports/6266/combined?report_date=2024-11-12&year_month=2024-11

# AI 요약 포함
curl http://localhost:8000/api/v1/sales-reports/6266/combined?report_date=2024-11-12&year_month=2024-11&skip_ai=false
```

### 4. AI 요약 생성 (사용자 버튼 클릭)

```
POST /api/v1/sales-reports/{store_id}/monthly/generate-ai-summary?year_month=YYYY-MM
```

**설명:**
- 사용자가 "AI 요약 생성" 버튼 클릭 시 호출
- 매출 데이터를 기반으로 AI 요약 텍스트 생성
- 40-50초 소요

**응답:**
```json
{
  "ai_summary": "이번 달 매출은 전월 대비 1.8% 증가했으나..."
}
```

**예시:**
```bash
curl -X POST http://localhost:8000/api/v1/sales-reports/6266/monthly/generate-ai-summary?year_month=2024-11
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
- AI 요약 리포트 생성 (선택적)

### LLMClient
- Runpod에서 qwen3-vl LLM 서버 주소 조회
- AI 요약 생성 요청 (POST /generate)
- 매출 데이터 기반 한국어 요약 텍스트 생성
- 40-50초 소요

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

## ✅ 구현 완료 기능

### AI 요약 리포트 (MVP)
- 🤖 qwen3-vl LLM 기반 AI 요약 생성
- Runpod 서버 연동
- 매출 데이터 기반 한국어 요약 텍스트
- 선택적 생성 (skip_ai 파라미터)
- 40-50초 소요

**특징:**
- DB 캐싱 없이 매 호출마다 생성 (MVP 단계)
- 사용자가 필요할 때만 생성 가능
- 즉시 응답이 필요한 경우 skip_ai=true 사용

## 🚧 추후 확장 계획

### Phase 2: DB 저장 및 캐싱
- MySQL 테이블 생성
- 리포트 이력 저장
- 이력 조회 API 추가
- AI 요약 캐싱으로 성능 개선

### Phase 3: 추가 분석
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

4. **AI 요약 생성 시간**
   - AI 요약 생성 시 40-50초 소요
   - 즉시 응답이 필요한 경우 `skip_ai=true` 사용
   - 캐싱 없이 매번 생성 (MVP 단계)

5. **미구현 기능**
   - 전월/전년 대비 증감률 (이력 데이터 필요)
   - AI 요약 캐싱 (DB 저장 필요)

## 🧪 테스트

```bash
# 서버 실행
python run.py

# API 문서 확인
# http://localhost:8000/docs

# 월별 리포트 테스트 (AI 요약 제외, 즉시 응답)
curl http://localhost:8000/api/v1/sales-reports/6266/monthly

# 월별 리포트 테스트 (AI 요약 포함, 40-50초 소요)
curl http://localhost:8000/api/v1/sales-reports/6266/monthly?skip_ai=false

# AI 요약만 별도 생성
curl -X POST http://localhost:8000/api/v1/sales-reports/6266/monthly/generate-ai-summary

# 일별 리포트 테스트
curl http://localhost:8000/api/v1/sales-reports/6266/daily
```

## 📈 통계

- **총 코드 라인**: ~800줄 (AI 요약 기능 포함)
- **API 엔드포인트**: 4개 (일별, 월별, 통합, AI 요약 생성)
- **응답 스키마**: 7개
- **서비스 레이어**: 3개 (AdminSchoolClient, LLMClient, SalesReportService)
