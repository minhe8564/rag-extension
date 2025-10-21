FROM python:3.11-slim AS builder

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 캐싱을 위해 requirements.txt 먼저 복사
COPY requirements.txt .

# Python 의존성 설치
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 런타임 의존성 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 빌드 스테이지에서 Python 의존성 복사
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 애플리케이션 코드 복사
COPY . .

# 비루트 사용자 생성
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# 애플리케이션이 실행되는 포트 노출
EXPOSE 8000

# 애플리케이션 실행
CMD ["python", "run.py"]
