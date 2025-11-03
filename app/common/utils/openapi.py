"""Utility helpers for OpenAPI schema customization."""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI):
    """Generate an OpenAPI schema with role header security definition."""
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
        "description": "역할(Role) 헤더. 예: USER, ADMIN",
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema

