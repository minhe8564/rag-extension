"""Pydantic Model Mixins for Common Functionality"""
from typing import Any, get_origin, get_args
from pydantic import field_validator


class AutoIntConversionMixin:
    """
    문자열을 정수로 자동 변환하는 Mixin 클래스

    int 타입으로 정의된 필드에 문자열이 들어오면 자동으로 정수로 변환합니다.
    Pydantic의 기본 타입 강제 변환(type coercion)을 활성화합니다.

    Usage:
        class MyModel(AutoIntConversionMixin, BaseModel):
            age: int
            score: int
            name: str

        # "25"와 같은 문자열이 자동으로 25(int)로 변환됨
        model = MyModel(age="25", score="100", name="홍길동")

    Note:
        - None 값은 그대로 유지됩니다 (Optional 필드용)
        - 변환 불가능한 문자열은 명확한 에러 메시지와 함께 실패합니다
        - int 타입이 아닌 필드는 영향을 받지 않습니다
    """

    @field_validator('*', mode='before')
    @classmethod
    def auto_convert_string_to_int(cls, v: Any, info) -> Any:
        """
        모든 int 필드에 대해 문자열을 자동으로 정수로 변환

        Args:
            v: 입력 값
            info: 필드 정보

        Returns:
            변환된 값 또는 원본 값

        Raises:
            ValueError: 정수로 변환할 수 없는 문자열인 경우
        """
        # None 값은 그대로 반환 (Optional 필드 지원)
        if v is None:
            return v

        # 필드 정보 가져오기
        field_name = info.field_name
        if not hasattr(cls, 'model_fields') or field_name not in cls.model_fields:
            return v

        field_info = cls.model_fields[field_name]
        field_type = field_info.annotation

        # Optional[int] 처리: get_origin이 Union이고 int가 args에 있는 경우
        origin = get_origin(field_type)
        if origin is not None:
            type_args = get_args(field_type)
            # Union 타입 (Optional 포함)에서 int 찾기
            if int in type_args:
                field_type = int
            else:
                return v

        # int 타입 필드만 변환
        if field_type == int or field_type is int:
            if isinstance(v, str):
                # 빈 문자열 처리
                if v.strip() == "":
                    raise ValueError(f"필드 '{field_name}': 빈 문자열은 정수로 변환할 수 없습니다")

                try:
                    return int(v)
                except ValueError:
                    raise ValueError(
                        f"필드 '{field_name}': '{v}'는 정수로 변환할 수 없습니다. "
                        f"올바른 정수 형식의 문자열을 입력해주세요."
                    )

        return v
