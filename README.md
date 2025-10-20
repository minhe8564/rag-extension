# HEBEES Extract Service

문서 추출을 담당하는 FastAPI 서비스입니다.

## 실행 방법

```bash
# 의존성 설치
pip install -r requirements.txt

# 서버 실행
python run.py
```

## API 엔드포인트

- `GET /` - 서비스 상태 확인
- `GET /health` - 헬스 체크

## 포트

- 기본 포트: 8001
- Swagger UI: http://localhost:8001/docs
