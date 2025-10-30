FROM python:3.11-slim AS builder

WORKDIR /app

# 필수 패키지
RUN apt-get update && apt-get install -y \
    curl ca-certificates python3-venv build-essential gcc \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 메타데이터만 먼저 복사 (캐시 최적화)
COPY pyproject.toml uv.lock ./

# uv 설치 + 동기화
RUN set -eux; \
    curl -fsSL https://astral.sh/uv/install.sh | sh; \
    install -m 0755 /root/.local/bin/uv /usr/local/bin/uv; \
    install -m 0755 /root/.local/bin/uvx /usr/local/bin/uvx || true; \
    uv --version; \
    uv sync --frozen --no-dev

FROM python:3.11-slim

WORKDIR /app

# 빌더에서 준비한 venv 및 메타데이터 복사
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/pyproject.toml /app/uv.lock ./

# 앱 코드 복사
COPY . .

# 가상환경 우선 사용
ENV PATH="/app/.venv/bin:${PATH}"

# 비루트 사용자 & 로그 디렉터리
RUN useradd --create-home --shell /bin/bash app \
    && mkdir -p /var/log/hebees \
    && chown -R app:app /app /var/log/hebees

USER app

CMD ["python", "run.py"]


