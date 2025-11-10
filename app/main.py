from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from . import __version__, __title__, __description__
from .core.settings import settings
from datetime import datetime
from .routers import ingest_router, query_router
from .routers import docs_router
from .core.database import Base, engine
from .core.openapi import custom_openapi

app = FastAPI(
    title=__title__,
    description=__description__,
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)

app.include_router(ingest_router)
app.include_router(query_router)
app.include_router(docs_router)
Base.metadata.create_all(bind=engine)

# Apply custom OpenAPI schema
app.openapi = lambda: custom_openapi(app)

@app.get("/")
async def root():
    return {
        "message": "Hebees Ingest Service is running"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": __version__,
    }
