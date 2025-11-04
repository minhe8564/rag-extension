from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI):
    """
    Custom OpenAPI schema generator supporting JWT, Role, and UUID header auth.
    
    - BearerAuth: Authorization: Bearer <JWT>
    - RoleHeader: x-user-role: USER / ADMIN ...
    - UserUUID: x-user-uuid: 사용자 UUID
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    components = openapi_schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})

    security_schemes["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT 토큰을 입력하세요. 예: Bearer eyJhbGciOiJIUzUxMiJ9..."
    }

    security_schemes["RoleHeader"] = {
        "type": "apiKey",
        "in": "header",
        "name": "x-user-role",
        "description": "사용자 역할(Role) 헤더를 입력하세요. 예: USER, ADMIN"
    }

    security_schemes["UserUUID"] = {
        "type": "apiKey",
        "in": "header",
        "name": "x-user-uuid",
        "description": "사용자 UUID 헤더를 입력하세요. 예: e1d23c4b-56f7-890a-bcde-1234567890ab"
    }

    openapi_schema["security"] = [
        {"BearerAuth": []},
        {"RoleHeader": []},
        {"UserUUID": []}
    ]

    app.openapi_schema = openapi_schema
    return app.openapi_schema