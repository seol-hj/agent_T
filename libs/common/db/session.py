"""
Database Session Management

SQLAlchemy 세션 생성 및 관리
"""

import os
from typing import Generator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base


# DATABASE_URL 환경변수에서 가져오기
# 기본값: SQLite (로컬 테스트용)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agent_t.db")


def get_engine(database_url: Optional[str] = None, echo: bool = False) -> Engine:
    """
    SQLAlchemy Engine 생성

    Args:
        database_url: 데이터베이스 URL (기본값: 환경변수 DATABASE_URL)
        echo: SQL 쿼리 로깅 활성화 (기본값: False)

    Returns:
        SQLAlchemy Engine
    """
    url = database_url or DATABASE_URL

    # SQLite 설정
    if url.startswith("sqlite"):
        engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=echo
        )

        # SQLite에서 Foreign Key 제약조건 활성화
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    # PostgreSQL 설정
    elif url.startswith("postgresql"):
        engine = create_engine(
            url,
            pool_size=10,  # 연결 풀 크기
            max_overflow=20,  # 최대 오버플로우
            pool_pre_ping=True,  # 연결 유효성 체크
            echo=echo
        )

    # 기타 DB
    else:
        engine = create_engine(url, echo=echo)

    return engine


def get_session_factory(engine: Optional[Engine] = None) -> sessionmaker:
    """
    SQLAlchemy SessionFactory 생성

    Args:
        engine: SQLAlchemy Engine (기본값: 자동 생성)

    Returns:
        SessionFactory
    """
    if engine is None:
        engine = get_engine()

    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    )


def init_db(engine: Optional[Engine] = None, drop_all: bool = False):
    """
    데이터베이스 초기화 (테이블 생성)

    Args:
        engine: SQLAlchemy Engine (기본값: 자동 생성)
        drop_all: 기존 테이블 삭제 여부 (기본값: False)
    """
    if engine is None:
        engine = get_engine()

    if drop_all:
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)


def get_db(session_factory: Optional[sessionmaker] = None) -> Generator[Session, None, None]:
    """
    데이터베이스 세션 의존성 (FastAPI용)

    Usage:
        @app.get("/experiments")
        def get_experiments(db: Session = Depends(get_db)):
            return db.query(Experiment).all()

    Args:
        session_factory: SessionFactory (기본값: 자동 생성)

    Yields:
        SQLAlchemy Session
    """
    if session_factory is None:
        session_factory = get_session_factory()

    db = session_factory()
    try:
        yield db
    finally:
        db.close()


# Global SessionFactory (앱 시작 시 한 번만 생성)
_global_session_factory: Optional[sessionmaker] = None


def setup_database(database_url: Optional[str] = None, echo: bool = False):
    """
    앱 시작 시 데이터베이스 설정

    Args:
        database_url: 데이터베이스 URL
        echo: SQL 쿼리 로깅
    """
    global _global_session_factory

    engine = get_engine(database_url=database_url, echo=echo)
    _global_session_factory = get_session_factory(engine)

    # 테이블 생성 (이미 존재하면 무시)
    init_db(engine=engine, drop_all=False)


def get_global_db() -> Generator[Session, None, None]:
    """
    Global SessionFactory를 사용한 세션 생성

    setup_database() 호출 후 사용
    """
    if _global_session_factory is None:
        raise RuntimeError("Database not initialized. Call setup_database() first.")

    db = _global_session_factory()
    try:
        yield db
    finally:
        db.close()
