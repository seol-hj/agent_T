"""
Session Management 테스트
"""

import pytest
import os

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common.db.session import (
    get_engine,
    get_session_factory,
    init_db,
    setup_database,
)
from common.db.models import Base, Experiment


def test_get_engine_sqlite():
    """SQLite 엔진 생성 테스트"""
    engine = get_engine(database_url="sqlite:///:memory:")
    assert engine is not None
    assert str(engine.url).startswith("sqlite")


def test_get_engine_postgresql():
    """PostgreSQL 엔진 생성 테스트 (연결 테스트는 제외)"""
    engine = get_engine(database_url="postgresql://user:pass@localhost:5432/testdb")
    assert engine is not None
    assert str(engine.url).startswith("postgresql")


def test_get_session_factory():
    """SessionFactory 생성 테스트"""
    engine = get_engine(database_url="sqlite:///:memory:")
    session_factory = get_session_factory(engine)
    assert session_factory is not None

    # 세션 생성 테스트
    session = session_factory()
    assert session is not None
    session.close()


def test_init_db():
    """DB 초기화 테스트"""
    engine = get_engine(database_url="sqlite:///:memory:")

    # 테이블 생성
    init_db(engine=engine, drop_all=False)

    # 테이블 존재 확인
    inspector = engine.dialect.get_inspector(engine)
    table_names = inspector.get_table_names()

    expected_tables = [
        "experiments",
        "user_requests",
        "experiment_specs",
        "scenarios",
        "network_artifacts",
        "demand_artifacts",
        "simulation_runs",
        "analysis_results",
        "reports",
        "agent_logs",
        "model_versions",
        "prompt_versions",
        "rag_documents",
    ]

    for table in expected_tables:
        assert table in table_names


def test_init_db_drop_all():
    """DB 초기화 (drop_all) 테스트"""
    engine = get_engine(database_url="sqlite:///:memory:")

    # 첫 번째 초기화
    init_db(engine=engine, drop_all=False)

    # 데이터 삽입
    session_factory = get_session_factory(engine)
    session = session_factory()
    exp = Experiment(id="exp_001", status="pending")
    session.add(exp)
    session.commit()
    session.close()

    # drop_all=True로 재초기화
    init_db(engine=engine, drop_all=True)

    # 데이터가 삭제되었는지 확인
    session = session_factory()
    count = session.query(Experiment).count()
    assert count == 0
    session.close()


def test_setup_database():
    """setup_database 테스트"""
    # 환경변수 설정 (테스트용)
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"

    setup_database(echo=False)

    # 테이블 생성 확인
    from common.db.session import _global_session_factory
    assert _global_session_factory is not None

    # 세션 생성 테스트
    session = _global_session_factory()
    assert session is not None
    session.close()
