"""
Database Connection
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://agent_t:dev_password@localhost:5432/agent_t_db")

# 디버깅용 로그
print(f"[DB] Connecting to: {DATABASE_URL.replace('dev_password', '***')}")

# Async 엔진 (PostgreSQL용)
if DATABASE_URL.startswith("postgresql://"):
    # asyncpg 사용
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
    AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)
else:
    async_engine = None
    AsyncSessionLocal = None

# Sync 엔진 (테이블 생성용)
sync_engine = create_engine(DATABASE_URL, echo=False)

def create_tables():
    """테이블 생성"""
    from .models import Base
    Base.metadata.create_all(bind=sync_engine)
    print("[DB] Tables created/verified")

async def get_db():
    """Dependency for FastAPI"""
    if AsyncSessionLocal is None:
        raise RuntimeError("Database not configured")
    
    async with AsyncSessionLocal() as session:
        yield session
