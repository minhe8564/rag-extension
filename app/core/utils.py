from typing import Any
from loguru import logger
import gc

try:
    import torch  # type: ignore
except Exception:
    torch = None  # torch가 없을 수도 있음


def dispose_model(model: Any | None) -> None:
    """
    로컬(특히 EC2 CPU 환경)에서 모델/토크나이저 사용 후 안전하게 해제.
    - 가능한 경우 CPU로 이동하여 디바이스 리소스 해제
    - 참조 제거 후 가비지 컬렉션
    - GPU 환경에서는 캐시/IPC 정리 (CPU-only 환경이면 자동으로 skip)
    """
    if model is None:
        return

    logger.debug("[CHUNKING] 모델/리소스를 해제합니다.")
    try:
        if hasattr(model, "to"):
            model.to("cpu")
    except Exception:
        pass

    try:
        del model
    except Exception:
        pass

    logger.debug("[CHUNKING] 가비지 컬렉터를 호출합니다.")
    try:
        gc.collect()
    except Exception:
        pass

    if torch is not None:
        try:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                if hasattr(torch.cuda, "ipc_collect"):
                    torch.cuda.ipc_collect()  # type: ignore[attr-defined]
        except Exception:
            pass


