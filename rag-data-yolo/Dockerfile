FROM python:3.11-slim AS builder

WORKDIR /app

# 필수 패키지
RUN apt-get update && apt-get install -y \
    curl ca-certificates python3-venv build-essential gcc \
    git libglib2.0-0 libsm6 libxext6 libxrender1 libgl1 \
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

# OpenCV 런타임 의존성
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libsm6 libxext6 libxrender1 libgl1 \
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

# 모델 가중치 파일 복사
COPY weights/doclayout_yolo_docstructbench_imgsz1024.pt /weights/doclayout_yolo_docstructbench_imgsz1024.pt
RUN test -f /weights/doclayout_yolo_docstructbench_imgsz1024.pt

# 런타임 환경 변수 (CUDA 서버에서 사용)
ENV WORK_DIR=/work \
    YOLO_DEVICE=cuda \
    YOLO_WEIGHTS=/weights/doclayout_yolo_docstructbench_imgsz1024.pt \
    YOLO_CONF=0.4 \
    TQDM_DISABLE=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 작업 디렉토리 및 가중치 디렉토리 생성
RUN mkdir -p /work /weights

# 비루트 사용자
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app /work /weights

USER app

EXPOSE 7002

CMD ["/app/.venv/bin/python", "run.py"]

