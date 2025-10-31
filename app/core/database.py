"""
Database connection and session management
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .settings import settings

# 비동기 엔진
engine = create_async_engine(
    settings.database_url,
    echo=True,
    pool_pre_ping=True,
)

# 세션
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

Base = declarative_base()

async def get_db():
    """Database session dependency"""
    async with AsyncSessionLocal() as session:
        yield session

