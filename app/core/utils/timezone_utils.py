"""
타임존 유틸리티 모듈
KST(한국 표준시) 기반의 datetime 처리
"""

from datetime import datetime
from zoneinfo import ZoneInfo

# 타임존 상수
KST = ZoneInfo("Asia/Seoul")


def now_kst() -> datetime:
    """
    현재 KST 시간을 반환합니다.

    Returns:
        datetime: timezone-aware한 현재 KST 시간

    Example:
        >>> from app.core.utils.timezone_utils import now_kst
        >>> current_time = now_kst()
        >>> print(current_time)
        2025-01-11 15:30:45.123456+09:00
    """
    return datetime.now(KST)
