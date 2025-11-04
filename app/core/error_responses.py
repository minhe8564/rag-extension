"""
공통 에러 응답 스키마 정의

FastAPI 라우터에서 사용하는 표준 에러 응답 형식을 정의합니다.
"""
from typing import Dict, Any, List


def validation_error_response() -> Dict[str, Any]:
    """
    400 - 유효성 검증 실패 응답

    Returns:
        Dict: OpenAPI 응답 스키마
    """
    return {
        "description": "잘못된 요청 (유효성 검증 실패)",
        "content": {
            "application/json": {
                "example": {
                    "status": 400,
                    "code": "VALIDATION_FAILED",
                    "message": "요청 파라미터 유효성 검증에 실패했습니다.",
                    "isSuccess": False,
                    "result": {
                        "errors": [
                            {
                                "field": "pageNum",
                                "message": "페이지 번호는 1 이상이어야 합니다."
                            }
                        ]
                    }
                }
            }
        }
    }


def unauthorized_error_response() -> Dict[str, Any]:
    """
    401 - 인증 실패 응답

    Returns:
        Dict: OpenAPI 응답 스키마
    """
    return {
        "description": "인증 실패 (Access Token 없음 또는 유효하지 않음)",
        "content": {
            "application/json": {
                "example": {
                    "status": 401,
                    "code": "INVALID_ACCESS_TOKEN",
                    "message": "엑세스 토큰이 유효하지 않거나 만료되었습니다.",
                    "isSuccess": False,
                    "result": {}
                }
            }
        }
    }


def forbidden_error_response(required_roles: List[str] = None) -> Dict[str, Any]:
    """
    403 - 권한 없음 응답

    Args:
        required_roles: 필요한 권한 목록 (기본값: ["ADMIN"])

    Returns:
        Dict: OpenAPI 응답 스키마
    """
    if required_roles is None:
        required_roles = ["ADMIN"]

    return {
        "description": "권한 없음 (관리자 권한 필요)",
        "content": {
            "application/json": {
                "example": {
                    "status": 403,
                    "code": "FORBIDDEN",
                    "message": "요청을 수행할 권한이 없습니다.",
                    "isSuccess": False,
                    "result": {
                        "requiredRole": required_roles
                    }
                }
            }
        }
    }


def not_found_error_response(resource: str = "리소스") -> Dict[str, Any]:
    """
    404 - 리소스를 찾을 수 없음 응답

    Args:
        resource: 찾을 수 없는 리소스 이름

    Returns:
        Dict: OpenAPI 응답 스키마
    """
    return {
        "description": f"{resource}를 찾을 수 없음",
        "content": {
            "application/json": {
                "example": {
                    "status": 404,
                    "code": "NOT_FOUND",
                    "message": f"요청한 {resource}를 찾을 수 없습니다.",
                    "isSuccess": False,
                    "result": {}
                }
            }
        }
    }


def conflict_error_response(resource: str = "리소스") -> Dict[str, Any]:
    """
    409 - 리소스 충돌 응답

    Args:
        resource: 충돌이 발생한 리소스 이름

    Returns:
        Dict: OpenAPI 응답 스키마
    """
    return {
        "description": f"{resource} 충돌",
        "content": {
            "application/json": {
                "example": {
                    "status": 409,
                    "code": "CONFLICT",
                    "message": f"{resource}가 이미 존재하거나 충돌이 발생했습니다.",
                    "isSuccess": False,
                    "result": {}
                }
            }
        }
    }


def internal_server_error_response() -> Dict[str, Any]:
    """
    500 - 서버 내부 오류 응답

    Returns:
        Dict: OpenAPI 응답 스키마
    """
    return {
        "description": "서버 내부 오류",
        "content": {
            "application/json": {
                "example": {
                    "status": 500,
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "서버 내부 오류가 발생했습니다.",
                    "isSuccess": False,
                    "result": {}
                }
            }
        }
    }


# 자주 사용하는 응답 조합
def common_error_responses(
    include_validation: bool = True,
    include_unauthorized: bool = True,
    include_forbidden: bool = True,
    required_roles: List[str] = None,
) -> Dict[int, Dict[str, Any]]:
    """
    자주 사용하는 에러 응답들을 조합하여 반환

    Args:
        include_validation: 400 응답 포함 여부
        include_unauthorized: 401 응답 포함 여부
        include_forbidden: 403 응답 포함 여부
        required_roles: 403 응답에 사용할 필요 권한 목록

    Returns:
        Dict: 상태 코드를 키로 하는 응답 스키마 딕셔너리
    """
    responses = {
        200: {"description": "성공"}
    }

    if include_validation:
        responses[400] = validation_error_response()

    if include_unauthorized:
        responses[401] = unauthorized_error_response()

    if include_forbidden:
        responses[403] = forbidden_error_response(required_roles)

    return responses


def admin_only_responses() -> Dict[int, Dict[str, Any]]:
    """
    관리자 전용 엔드포인트에서 사용하는 표준 에러 응답

    Returns:
        Dict: 상태 코드를 키로 하는 응답 스키마 딕셔너리
    """
    return common_error_responses(
        include_validation=True,
        include_unauthorized=True,
        include_forbidden=True,
        required_roles=["ADMIN"]
    )


def public_endpoint_responses() -> Dict[int, Dict[str, Any]]:
    """
    공개 엔드포인트에서 사용하는 표준 에러 응답

    Returns:
        Dict: 상태 코드를 키로 하는 응답 스키마 딕셔너리
    """
    return common_error_responses(
        include_validation=True,
        include_unauthorized=False,
        include_forbidden=False,
    )
