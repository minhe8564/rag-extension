"""Utility helpers for the Python Backend service."""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI):
    """Generate an OpenAPI schema with JWT bearer security definition."""
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
    security_schemes["RoleHeader"] = {
        "type": "apiKey",
        "in": "header",
        "name": "x-user-role",
        "description": "게이트웨이가 추가하는 사용자 역할 헤더. 예: USER, ADMIN",
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

