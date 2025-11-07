FROM python:3.11-slim AS builder

WORKDIR /app

# 필수 패키지 (marker-pdf에 필요한 시스템 의존성 포함)
RUN apt-get update && apt-get install -y \
    curl ca-certificates python3-venv build-essential gcc \
    git ghostscript libglib2.0-0 libsm6 libxext6 libxrender1 \
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
    uv sync --frozen --no-dev; \
    .venv/bin/python -c "import uvicorn; print(f'✓ uvicorn {uvicorn.__version__} installed')" || (echo "ERROR: uvicorn not found!" && exit 1)

# CUDA 버전 PyTorch 설치 (시스템 uv 사용, venv 지정)
RUN uv pip install --python /app/.venv/bin/python --no-cache-dir --index-url https://download.pytorch.org/whl/cu126 \
    torch==2.7.0+cu126 \
    torchvision==0.22.0+cu126 \
    torchaudio==2.7.0+cu126

FROM python:3.11-slim

WORKDIR /app

# marker-pdf에 필요한 런타임 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    ghostscript libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# 빌더에서 준비한 venv 및 메타데이터 복사
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/pyproject.toml /app/uv.lock ./

# 앱 코드 복사
COPY . .

# 가상환경 우선 사용
ENV PATH="/app/.venv/bin:${PATH}"

# venv가 제대로 복사되었는지 확인
RUN /app/.venv/bin/python -c "import uvicorn; print(f'uvicorn version: {uvicorn.__version__}')" || \
    (echo "ERROR: uvicorn not found in venv!" && exit 1)

# 런타임 환경 변수
ENV HF_HOME=/cache/hf \
    TRANSFORMERS_CACHE=/cache/hf \
    WORK_DIR=/work \
    MARKER_DEVICE=cuda \
    MARKER_DTYPE=float16 \
    TQDM_DISABLE=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 작업 디렉토리 및 캐시 디렉토리 생성
RUN mkdir -p /work /cache/hf

# 비루트 사용자
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app /work /cache

USER app

EXPOSE 8000

CMD ["/app/.venv/bin/python", "run.py"]