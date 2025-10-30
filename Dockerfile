FROM python:3.11-slim AS builder

# 작업 디렉터리 설정
WORKDIR /app

# 필수 패키지 설치: curl, CA 인증서, venv, 빌드 도구
RUN apt-get update && apt-get install -y \
    curl ca-certificates python3-venv build-essential gcc \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 프로젝트 메타데이터와 잠금 파일만 먼저 복사 (레이어 캐시 최적화)
COPY pyproject.toml uv.lock ./

# uv 설치 후 가상환경(.venv)에 동기화 (--frozen: uv.lock 엄격 준수)
RUN set -eux; \
    curl -fsSL https://astral.sh/uv/install.sh | sh -s -- -y; \
    install -m 0755 /root/.local/bin/uv /usr/local/bin/uv || true; \
    install -m 0755 /root/.local/bin/uvx /usr/local/bin/uvx || true; \
    export PATH="/usr/local/bin:/root/.local/bin:$PATH"; \
    uv --version; \
    uv sync --frozen --no-dev


FROM python:3.11-slim

# 작업 디렉터리 설정
WORKDIR /app

# 빌더에서 준비한 가상환경과 메타데이터 복사
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/pyproject.toml /app/uv.lock ./

# 애플리케이션 코드 복사
COPY . .

# 가상환경 우선 사용
ENV PATH="/app/.venv/bin:${PATH}"

# 비루트 사용자 생성 및 권한 설정 + 로그 디렉터리 준비
RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /var/log/hebees \
    && chown -R app:app /app /var/log/hebees
USER app

# 애플리케이션 포트 노출
EXPOSE 8000

# 애플리케이션 실행
CMD ["python", "run.py"]
