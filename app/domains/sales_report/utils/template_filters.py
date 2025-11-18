"""Jinja2 템플릿용 커스텀 필터"""
from typing import Any


def humanize_currency(value: Any) -> str:
    """
    통화 포맷팅: 숫자를 한국 원화 형식으로 변환

    Args:
        value: 숫자 값 (int, float, str)

    Returns:
        포맷팅된 문자열 (예: "1,500,000원")

    Examples:
        >>> humanize_currency(1500000)
        '1,500,000원'
        >>> humanize_currency(1500000.5)
        '1,500,000원'
    """
    try:
        return f"{int(float(value)):,}원"
    except (ValueError, TypeError):
        return str(value)


def humanize_percentage(value: Any) -> str:
    """
    퍼센트 포맷팅: 비율(0.0~1.0)을 퍼센트로 변환

    Args:
        value: 비율 값 (0.0 ~ 1.0)

    Returns:
        포맷팅된 문자열 (예: "65.0%")

    Examples:
        >>> humanize_percentage(0.65)
        '65.0%'
        >>> humanize_percentage(0.875)
        '87.5%'
    """
    try:
        return f"{float(value) * 100:.1f}%"
    except (ValueError, TypeError):
        return str(value)


def format_date_korean(value: Any) -> str:
    """
    날짜를 한국어 형식으로 변환

    Args:
        value: ISO 형식 날짜 문자열 (YYYY-MM-DD)

    Returns:
        한국어 포맷 문자열 (예: "10월 15일")

    Examples:
        >>> format_date_korean("2024-10-15")
        '10월 15일'
        >>> format_date_korean("2024-01-05")
        '1월 5일'
    """
    try:
        if isinstance(value, str) and len(value) >= 10:
            parts = value.split('-')
            month = int(parts[1])
            day = int(parts[2])
            return f"{month}월 {day}일"
        return str(value)
    except (ValueError, IndexError, AttributeError):
        return str(value)


def humanize_count(value: Any, unit: str = "명") -> str:
    """
    숫자에 단위를 붙여 포맷팅

    Args:
        value: 숫자 값
        unit: 단위 (기본값: "명")

    Returns:
        포맷팅된 문자열 (예: "150명")

    Examples:
        >>> humanize_count(150)
        '150명'
        >>> humanize_count(5, "회")
        '5회'
    """
    try:
        return f"{int(float(value))}{unit}"
    except (ValueError, TypeError):
        return str(value)
