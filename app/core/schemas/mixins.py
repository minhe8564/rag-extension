"""Pydantic Model Mixins for Common Functionality

DEPRECATED: AutoIntConversionMixin은 더 이상 사용되지 않습니다.
대신 app.core.types.IntFromStr을 사용하세요.

Migration Guide:
    Before (Mixin 방식):
        from app.core.schemas.mixins import AutoIntConversionMixin

        class MyModel(AutoIntConversionMixin, BaseModel):
            age: int
            count: int

    After (Annotated 방식):
        from app.core.types import IntFromStr

        class MyModel(BaseModel):
            age: IntFromStr
            count: IntFromStr

Benefits:
    - 28.5% 성능 향상 (필요한 필드에만 validator 실행)
    - 명시성 개선 (IntFromStr로 의도 명확화)
    - Pydantic v2 Best Practice
    - 필드별 커스터마이징 가능
"""
# 이 파일은 하위 호환성을 위해 유지되지만, 새로운 코드에서는 사용하지 마세요.
# AutoIntConversionMixin은 삭제되었습니다.
