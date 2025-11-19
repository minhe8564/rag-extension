# rag-extractor-deploy

RAG Extractor API - FastAPI 기반 프로젝트

## 프로젝트 구조

```
rag-extractor-deploy/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 애플리케이션 진입점
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Settings 클래스 (.env 기반 설정)
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/
│   │       ├── __init__.py
│   │       └── health.py    # Health check 엔드포인트
│   ├── models/              # 데이터 모델
│   └── services/            # 비즈니스 로직
├── .env                     # 환경 변수 (로컬)
├── .env.example             # 환경 변수 템플릿
├── pyproject.toml           # uv 프로젝트 설정
└── requirements.txt         # pip 호환성 (참고용)
```

## 시작하기

### 사전 요구사항

- Python 3.9 이상
- [uv](https://github.com/astral-sh/uv) 패키지 관리자

### 설치

1. uv 설치 (이미 설치되어 있다면 생략)
   ```bash
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # 또는 pip로 설치
   pip install uv
   ```

2. 프로젝트 클론 및 디렉토리 이동
   ```bash
   cd rag-extractor-deploy
   ```

3. 의존성 설치
   ```bash
   uv sync
   ```

4. 환경 변수 설정
   ```bash
   # .env.example을 복사하여 .env 파일 생성
   cp .env.example .env
   
   # .env 파일을 편집하여 필요한 환경 변수 설정
   ```

### 실행

```bash
# uv를 사용하여 실행
uv run python -m app.main

# 또는 uvicorn 직접 실행
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 다음 URL에서 접근할 수 있습니다:
- API: http://localhost:8000
- API 문서 (Swagger): http://localhost:8000/docs
- API 문서 (ReDoc): http://localhost:8000/redoc

### 환경 변수

`.env` 파일에서 다음 환경 변수를 설정할 수 있습니다:

- `APP_NAME`: 애플리케이션 이름
- `APP_VERSION`: 애플리케이션 버전
- `DEBUG`: 디버그 모드 (True/False)
- `HOST`: 서버 호스트
- `PORT`: 서버 포트
- `API_V1_PREFIX`: API v1 경로 prefix
- `CORS_ORIGINS`: CORS 허용 오리진 (쉼표로 구분)
- `DATABASE_URL`: 데이터베이스 연결 URL (선택사항)
- `SECRET_KEY`: 보안 키 (선택사항)
- `LOG_LEVEL`: 로그 레벨

## 개발

### 의존성 추가

```bash
# 패키지 추가
uv add <package-name>

# 개발 의존성 추가
uv add --dev <package-name>
```

### 의존성 업데이트

```bash
uv sync
```

## API 엔드포인트

- `GET /`: 루트 엔드포인트
- `GET /api/v1/health`: Health check

## 라이선스

[라이선스 정보를 여기에 추가하세요]
