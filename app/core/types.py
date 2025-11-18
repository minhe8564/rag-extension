"""Custom Type Aliases with Validators

Pydantic v2 타입 별칭 모음 - BeforeValidator를 사용한 명시적 타입 변환
"""
from typing import Any, Annotated
from pydantic import BeforeValidator


def str_to_int(v: Any) -> int:
    """
    문자열을 정수로 변환하는 validator

    Args:
        v: 입력 값 (Any)

    Returns:
        int: 변환된 정수

    Raises:
        ValueError: 정수로 변환할 수 없는 경우

    Examples:
        >>> str_to_int("123")
        123
        >>> str_to_int(123)
        123
        >>> str_to_int(None)
        None
        >>> str_to_int("abc")
        ValueError: 'abc'는 정수로 변환할 수 없습니다
    """
    # None 값은 그대로 반환 (Optional 필드 지원)
    if v is None:
        return v

    # 이미 int면 그대로 반환
    if isinstance(v, int):
        return v

    # 문자열인 경우 변환 시도
    if isinstance(v, str):
        # 빈 문자열 체크
        if v.strip() == "":
            raise ValueError("빈 문자열은 정수로 변환할 수 없습니다")

        try:
            return int(v)
        except ValueError:
            raise ValueError(
                f"'{v}'는 정수로 변환할 수 없습니다. "
                f"올바른 정수 형식의 문자열을 입력해주세요."
            )

    # float인 경우 int로 변환 (Pydantic 기본 동작과 동일)
    if isinstance(v, float):
        return int(v)

    # 기타 타입은 그대로 반환하여 Pydantic이 처리하도록 함
    return v


# 타입 별칭: 문자열 → 정수 자동 변환
IntFromStr = Annotated[int, BeforeValidator(str_to_int)]
"""
문자열을 정수로 자동 변환하는 타입 별칭

Usage:
    from app.core.types import IntFromStr

    class MyModel(BaseModel):
        age: IntFromStr  # "25" → 25 자동 변환
        count: IntFromStr

Examples:
    >>> class User(BaseModel):
    ...     age: IntFromStr
    >>> User(age="25")
    User(age=25)
    >>> User(age=25)
    User(age=25)
    >>> User(age="abc")
    ValidationError: 'abc'는 정수로 변환할 수 없습니다
"""
