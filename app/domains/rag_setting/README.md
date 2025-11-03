# RAG Setting Module

RAG (Retrieval-Augmented Generation) 전략 관리를 위한 모듈입니다.

## 📂 디렉토리 구조

```
rag_setting/
├── models/
│   ├── __init__.py
│   └── strategy.py         # Strategy, StrategyType 모델
├── schemas/
│   ├── __init__.py
│   └── strategy.py         # Pydantic 스키마
├── routers/
│   ├── __init__.py
│   └── strategy.py         # API 엔드포인트
├── service/                # 비즈니스 로직 (추후 추가)
└── README.md              # 이 파일
```

---

## 🗄️ 데이터베이스 스키마

### **STRATEGY_TYPE** (전략 유형)

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| STRATEGY_TYPE_NO | binary(16) | PK, UUID |
| NAME | varchar(255) | 전략 유형 이름 (unique) |
| CREATED_AT | datetime | 생성 시간 |
| UPDATED_AT | datetime | 수정 시간 |

**전략 유형 목록:**
- `extraction` - 텍스트 추출
- `chunking` - 텍스트 분할
- `embedding` - 임베딩 생성
- `transformation` - 쿼리 변환
- `retrieval` - 검색
- `reranking` - 재순위화
- `prompting` - 프롬프트 생성
- `generation` - 답변 생성

---

### **STRATEGY** (전략)

| 컬럼명 | 타입 | 설명 |
|--------|------|------|
| STRATEGY_NO | binary(16) | PK, UUID |
| STRATEGY_TYPE_NO | binary(16) | FK → STRATEGY_TYPE |
| NAME | varchar(50) | 전략명 |
| DESCRIPTION | varchar(255) | 설명 |
| PARAMETER | json | 파라미터 (nullable) |
| CREATED_AT | datetime | 생성 시간 |
| UPDATED_AT | datetime | 수정 시간 |

---

## 🚀 사용 방법

### **1. main.py에 라우터 등록**

```python
# app/main.py
from app.rag_setting.routers import strategy_router

app.include_router(strategy_router)
```

---

### **2. API 엔드포인트**

#### **전략 목록 조회**

```http
GET /rag/strategies
Authorization: Bearer {access_token}
```

**Query Parameters:**
- `type` (optional): 전략 유형 필터 (예: `chunking`)
- `pageNum` (default: 1): 페이지 번호
- `pageSize` (default: 20, max: 100): 페이지당 항목 수
- `sort` (default: `name`): 정렬 기준

**응답 예시:**
```json
{
  "status": 200,
  "code": "OK",
  "message": "성공",
  "isSuccess": true,
  "result": {
    "data": [
      {
        "strategyNo": "1a7c2b6e-4d3f-45b1-98c0-6e2c4f9a7b32",
        "name": "슬라이딩 윈도우 청킹",
        "description": "고정 길이 윈도우로 안정적 검색 리콜 확보",
        "type": "chunking",
        "parameter": {
          "window_size": 350,
          "overlap": 50
        }
      }
    ],
    "pagination": {
      "pageNum": 1,
      "pageSize": 20,
      "totalItems": 13,
      "totalPages": 1,
      "hasNext": false
    }
  }
}
```

---

### **3. 모델 사용 예시**

```python
from app.rag_setting.models import Strategy, StrategyType, generate_uuid_binary
from app.db import get_session
from sqlalchemy import select

async def get_chunking_strategies():
    async with get_session() as db:
        # chunking 타입 조회
        result = await db.execute(
            select(StrategyType).where(StrategyType.name == "chunking")
        )
        strategy_type = result.scalar_one_or_none()

        if strategy_type:
            # 해당 타입의 전략 조회
            result = await db.execute(
                select(Strategy).where(
                    Strategy.strategy_type_no == strategy_type.strategy_type_no
                )
            )
            strategies = result.scalars().all()
            return strategies
```

---

### **4. UUID 변환 헬퍼**

```python
from app.rag_setting.models import uuid_to_binary, binary_to_uuid

# UUID 문자열 → binary(16)
uuid_str = "1a7c2b6e-4d3f-45b1-98c0-6e2c4f9a7b32"
uuid_bytes = uuid_to_binary(uuid_str)  # b'\x1a|+n...'

# binary(16) → UUID 문자열
uuid_str = binary_to_uuid(strategy.strategy_no)  # "1a7c2b6e-..."
```

---

## 🔐 인증

현재는 간단한 Bearer 토큰 검증만 구현되어 있습니다.

```python
Authorization: Bearer test-token-12345
```

**추후 구현 필요:**
- JWT 토큰 검증
- 권한 관리 (RBAC)
- 토큰 갱신

---

## 🧪 테스트

### **테스트 데이터 생성**

MySQL에서 STRATEGY_TYPE 데이터를 먼저 생성해야 합니다:

```sql
USE hebees;

INSERT INTO STRATEGY_TYPE (STRATEGY_TYPE_NO, NAME, CREATED_AT, UPDATED_AT)
VALUES
  (UUID_TO_BIN(UUID()), 'extraction', NOW(), NOW()),
  (UUID_TO_BIN(UUID()), 'chunking', NOW(), NOW()),
  (UUID_TO_BIN(UUID()), 'embedding', NOW(), NOW()),
  (UUID_TO_BIN(UUID()), 'transformation', NOW(), NOW()),
  (UUID_TO_BIN(UUID()), 'retrieval', NOW(), NOW()),
  (UUID_TO_BIN(UUID()), 'reranking', NOW(), NOW()),
  (UUID_TO_BIN(UUID()), 'prompting', NOW(), NOW()),
  (UUID_TO_BIN(UUID()), 'generation', NOW(), NOW());
```

---

### **Swagger UI 테스트**

```
http://localhost:8000/docs
```

1. "Authorize" 버튼 클릭
2. `Bearer test-token-12345` 입력
3. `GET /rag/strategies` 엔드포인트 테스트

---

## 📝 추가 개발 사항

### **추후 구현 예정:**

- [ ] Strategy CRUD (생성, 수정, 삭제)
- [ ] StrategyType CRUD
- [ ] 전략 상세 조회
- [ ] 전략 검색 (이름, 설명)
- [ ] 전략 활성화/비활성화
- [ ] 전략 버전 관리
- [ ] 전략 사용 통계
- [ ] JWT 인증 구현
- [ ] 권한 관리 (RBAC)

---

## 🔧 유지보수

### **데이터베이스 마이그레이션**

Alembic 사용 시:

```bash
# 마이그레이션 생성
alembic revision --autogenerate -m "Add Strategy tables"

# 마이그레이션 적용
alembic upgrade head
```

---

### **문제 해결**

#### **Q: 테이블을 찾을 수 없음**
```
Table 'hebees.STRATEGY' doesn't exist
```

**A:** MySQL에서 테이블을 먼저 생성해야 합니다.

```sql
CREATE TABLE STRATEGY_TYPE (
    STRATEGY_TYPE_NO BINARY(16) PRIMARY KEY,
    NAME VARCHAR(255) NOT NULL UNIQUE,
    CREATED_AT DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UPDATED_AT DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE STRATEGY (
    STRATEGY_NO BINARY(16) PRIMARY KEY,
    STRATEGY_TYPE_NO BINARY(16) NOT NULL,
    NAME VARCHAR(50) NOT NULL,
    DESCRIPTION VARCHAR(255) NOT NULL,
    PARAMETER JSON,
    CREATED_AT DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UPDATED_AT DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (STRATEGY_TYPE_NO) REFERENCES STRATEGY_TYPE(STRATEGY_TYPE_NO) ON DELETE CASCADE
);
```

---

#### **Q: UUID 변환 오류**
```
ValueError: badly formed hexadecimal UUID string
```

**A:** binary(16) 데이터를 문자열로 직접 변환하지 말고, `binary_to_uuid()` 헬퍼 함수를 사용하세요.

---

## 📞 문의

문제가 발생하면 팀 백엔드 담당자에게 문의하세요.
