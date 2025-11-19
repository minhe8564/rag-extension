from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from app.core.settings import settings

# 데이터베이스 URL 설정 (settings 사용)
ASYNC_DATABASE_URL = settings.database_url
DATABASE_URL = ASYNC_DATABASE_URL.replace("mysql+aiomysql://", "mysql+pymysql://")

# 공용 Base (모든 모델이 이 Base를 사용해야 합니다)
Base = declarative_base()

# 동기 엔진 (모델 정의용)
engine = create_engine(
    DATABASE_URL,
    echo=True,  # SQL 쿼리 로깅 (프로덕션에서는 False)
    pool_pre_ping=True,
    pool_recycle=3600
)

# 비동기 엔진
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=3600
)

# 세션 팩토리
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    """비동기 데이터베이스 세션 의존성"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()



