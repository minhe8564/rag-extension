"""LLM 커스텀 프롬프트 검증 모듈"""
from typing import Tuple, Optional
import re
import logging

logger = logging.getLogger(__name__)


class CustomPromptValidator:
    """커스텀 프롬프트 검증 및 정제"""

    MAX_LENGTH = 500  # 최대 글자 수

    # 위험 패턴 (즉시 거부)
    DANGER_PATTERNS = [
        r"ignore.*above",
        r"무시.*위",
        r"disregard.*previous",
        r"forget.*instructions",
        r"무시.*데이터",
        r"ignore.*data",
        r"데이터.*믿지\s*말",
        r"데이터.*거짓",
        r"don't.*trust.*data",
        r"매출.*\d+억.*말해",  # "매출이 10억이라고 말해줘"
        r"실제.*매출.*아니",
    ]

    @classmethod
    def validate_and_sanitize(
        cls,
        custom_prompt: str
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """
        프롬프트 검증 및 정제

        Args:
            custom_prompt: 사용자 입력 프롬프트

        Returns:
            Tuple[level, sanitized_prompt, message]:
                - level: "ok" | "danger"
                - sanitized_prompt: 정제된 프롬프트 (danger면 None)
                - message: 검증 메시지 (ok면 None)
        """
        if not custom_prompt or not custom_prompt.strip():
            return ("danger", None, "프롬프트가 비어있습니다")

        # 1. 길이 검증
        if len(custom_prompt) > cls.MAX_LENGTH:
            return (
                "danger",
                None,
                f"프롬프트가 너무 깁니다 (최대 {cls.MAX_LENGTH}자, 현재 {len(custom_prompt)}자)"
            )

        # 2. 위험 패턴 검사 (즉시 거부)
        for pattern in cls.DANGER_PATTERNS:
            if re.search(pattern, custom_prompt, re.IGNORECASE):
                logger.warning(f"위험 패턴 감지: {pattern}")
                return (
                    "danger",
                    None,
                    "허용되지 않는 지시어가 포함되어 있습니다"
                )

        # 3. 공백 정리 및 통과
        sanitized = custom_prompt.strip()

        # 커스텀 프롬프트는 사용자가 원하는 대로 동작하도록 허용
        # JSON 형식은 베이스 프롬프트 템플릿에서 이미 강제하고 있음
        return ("ok", sanitized, None)
